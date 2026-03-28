#!/usr/bin/env python3
"""
DM Personnel Directory — Sync Pipeline
ArcGIS Hosted Feature Service → PostgreSQL (personnel schema)

- Pulls all records from DM_Personnel/FeatureServer/0
- Normalizes district names to canonical 28
- Maps category → dept_code
- Looks up district_lgd from admin.ap_districts_28
- UPSERTs into personnel.persons
- Logs to personnel.sync_log

Schedule: every 30 minutes via Windows Task Scheduler
"""

import os
import sys
import json
import time
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

# Disable SSL warnings
import urllib3
urllib3.disable_warnings()

# ── Config ──
DB_HOST = "192.168.9.35"
DB_PORT = 5432
DB_NAME = "apsdma_2026"
DB_USER = "sde"
DB_PASS = "apsdma#123"

PORTAL_URL = "https://192.168.8.24/gisportal"
FEATURE_URL = "https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/DM_Personnel/FeatureServer/0"
TOKEN_URL = f"{PORTAL_URL}/sharing/rest/generateToken"
PORTAL_USER = "portaladmin"
PORTAL_PASS = "9494501235Nn@"

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "dm_personnel_sync.log")),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("dm_personnel_sync")

# ── Import department mapping from setup module ──
sys.path.insert(0, os.path.dirname(__file__))
from dm_personnel_db_setup import CATEGORY_TO_CODE, NDMA_TO_AP, migrate_category, get_dept_code

# ══════════════════════════════════════════════════════════════════
# District normalization (from sync_common patterns)
# ══════════════════════════════════════════════════════════════════
DISTRICT_CANONICAL = [
    "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya",
    "Bapatla", "Chittoor", "Dr.B.R.Ambedkar Konaseema", "East Godavari",
    "Eluru", "Guntur", "Kakinada", "Krishna", "Kurnool", "Markapuram",
    "Nandyal", "NTR", "Palnadu", "Parvathipuram Manyam", "Polavaram",
    "Prakasam", "Sri Potti Sriramulu Nellore", "Sri Sathya Sai",
    "Srikakulam", "Tirupati", "Visakhapatnam", "Vizianagaram",
    "West Godavari", "Y.S.R.Kadapa"
]

_DISTRICT_ALIASES = {
    "anantapur": "Ananthapuramu",
    "ananthapuram": "Ananthapuramu",
    "anantapuramu": "Ananthapuramu",
    "ananthapur": "Ananthapuramu",
    "konaseema": "Dr.B.R.Ambedkar Konaseema",
    "dr. b.r. ambedkar konaseema": "Dr.B.R.Ambedkar Konaseema",
    "dr b r ambedkar konaseema": "Dr.B.R.Ambedkar Konaseema",
    "ambedkar konaseema": "Dr.B.R.Ambedkar Konaseema",
    "nellore": "Sri Potti Sriramulu Nellore",
    "spsr nellore": "Sri Potti Sriramulu Nellore",
    "sri potti sriramulu nellore": "Sri Potti Sriramulu Nellore",
    "sri satya sai": "Sri Sathya Sai",
    "sri sathya sai": "Sri Sathya Sai",
    "ysr kadapa": "Y.S.R.Kadapa",
    "kadapa": "Y.S.R.Kadapa",
    "cuddapah": "Y.S.R.Kadapa",
    "y.s.r. kadapa": "Y.S.R.Kadapa",
    "y.s.r.kadapa": "Y.S.R.Kadapa",
    "parvathipuram": "Parvathipuram Manyam",
    "manyam": "Parvathipuram Manyam",
    "alluri": "Alluri Sitharama Raju",
    "alluri sitarama raju": "Alluri Sitharama Raju",
    "asr": "Alluri Sitharama Raju",
    "vishakapatnam": "Visakhapatnam",
    "vishakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
}

# Build lowercase lookup from canonical
for d in DISTRICT_CANONICAL:
    _DISTRICT_ALIASES[d.lower()] = d


def normalize_district(name):
    """Normalize district name to canonical 28-district name."""
    if not name or name.strip() in ("", "State Level"):
        return None
    name = name.strip()
    # Exact match
    if name in DISTRICT_CANONICAL:
        return name
    # Alias lookup
    key = name.lower().strip().replace("  ", " ")
    if key in _DISTRICT_ALIASES:
        return _DISTRICT_ALIASES[key]
    # Fuzzy: check substring
    for canonical in DISTRICT_CANONICAL:
        if key in canonical.lower() or canonical.lower() in key:
            return canonical
    return name  # return as-is if no match


# ══════════════════════════════════════════════════════════════════
# ArcGIS API
# ══════════════════════════════════════════════════════════════════
def get_token():
    data = {
        "username": PORTAL_USER, "password": PORTAL_PASS,
        "client": "referer", "referer": "https://apsdmagis.ap.gov.in",
        "expiration": 120, "f": "json"
    }
    r = requests.post(TOKEN_URL, data=data, verify=False, timeout=30)
    return r.json().get("token")


def fetch_all_records(token):
    """Fetch all records from DM_Personnel feature service."""
    all_features = []
    offset = 0
    batch_size = 2000

    while True:
        url = (
            f"{FEATURE_URL}/query?where=1%3D1&outFields=*&returnGeometry=true"
            f"&resultRecordCount={batch_size}&resultOffset={offset}"
            f"&orderByFields=objectid+ASC&f=json&token={token}"
        )
        r = requests.get(url, verify=False, timeout=60)
        data = r.json()
        features = data.get("features", [])
        if not features:
            break
        all_features.extend(features)
        log.info(f"  Fetched {len(features)} records (offset={offset}, total={len(all_features)})")
        if not data.get("exceededTransferLimit"):
            break
        offset += batch_size

    return all_features


# ══════════════════════════════════════════════════════════════════
# Sync Logic
# ══════════════════════════════════════════════════════════════════
def epoch_to_date(epoch_ms):
    """Convert ArcGIS epoch milliseconds to Python date."""
    if not epoch_ms:
        return None
    try:
        return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).date()
    except (ValueError, OSError, OverflowError):
        return None


def epoch_to_datetime(epoch_ms):
    if not epoch_ms:
        return None
    try:
        return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def sync():
    log.info("=" * 60)
    log.info("  DM PERSONNEL SYNC — START")
    log.info("=" * 60)
    started = datetime.now(timezone.utc)

    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()

    # Start sync log
    cur.execute(
        "INSERT INTO personnel.sync_log (sync_type, started_at) VALUES ('arcgis_to_pg', %s) RETURNING id",
        (started,)
    )
    sync_id = cur.fetchone()[0]
    conn.commit()

    try:
        # 1. Get token
        log.info("[1] Authenticating...")
        token = get_token()
        if not token:
            raise Exception("Failed to get portal token")

        # 2. Fetch all records
        log.info("[2] Fetching records from ArcGIS FS...")
        features = fetch_all_records(token)
        log.info(f"    Total fetched: {len(features)}")

        # 3. Load district LGD lookup
        cur.execute("SELECT district_name, district_lgd FROM admin.ap_districts_28")
        district_lgd = {row[0]: row[1] for row in cur.fetchall()}

        # 4. Load mandal lookup (district_name, mandal_name) → mandal_lgd
        cur.execute("SELECT district_name, mandal_name, mandal_lgd FROM admin.ap_mandals_688 WHERE mandal_name IS NOT NULL")
        mandal_lgd = {}
        for row in cur.fetchall():
            key = (row[0], row[1].lower() if row[1] else "")
            mandal_lgd[key] = row[2]

        # 5. Process and upsert
        log.info("[3] Processing and upserting...")
        inserted = 0
        updated = 0
        normalized = 0

        for feat in features:
            a = feat["attributes"]
            geom = feat.get("geometry")

            # Normalize district
            raw_district = a.get("district_name") or ""
            norm_district = normalize_district(raw_district)
            if norm_district and norm_district != raw_district and raw_district != "State Level":
                normalized += 1

            # Get dept_code from category
            category = a.get("category") or ""
            dept_code = get_dept_code(category)

            # Lookup LGD codes
            d_lgd = district_lgd.get(norm_district) if norm_district else None
            m_name = a.get("mandal_name") or ""
            m_lgd = None
            if norm_district and m_name:
                m_lgd = mandal_lgd.get((norm_district, m_name.lower()))

            # Build geometry WKT
            geom_wkt = None
            if geom and geom.get("x") and geom.get("y"):
                geom_wkt = f"SRID=4326;POINT({geom['x']} {geom['y']})"

            # Jurisdiction
            jtype = a.get("jurisdiction_type") or ""
            if not jtype:
                level = a.get("hierarchy_level") or 6
                if level <= 2:
                    jtype = "State"
                elif level == 3:
                    jtype = "District"
                elif level == 4:
                    jtype = "Division"
                elif level == 5:
                    jtype = "Mandal"
                else:
                    jtype = "Village"

            oid = a.get("objectid")
            gid = a.get("globalid")

            cur.execute("""
                INSERT INTO personnel.persons (
                    person_name, designation, employee_id, date_of_birth,
                    dept_code, sub_department, category, hierarchy_level,
                    district_name, district_lgd, mandal_name, mandal_lgd,
                    village_name, jurisdiction_type, office_address,
                    reports_to_name, reports_to_designation,
                    parent_department, posting_type, rank_designation,
                    status, date_of_posting,
                    phone_primary, phone_alternate, whatsapp_number, email,
                    office_phone, office_phone_ext, intercom_number, fax_number,
                    residence_phone, ham_radio_callsign, residence_address,
                    esf_primary, esf_assignments,
                    dm_role, dm_role_active, dm_role_order_no, dm_role_since,
                    disaster_name, disaster_type, disaster_duty, disaster_duty_location,
                    disaster_duty_status, disaster_duty_start, disaster_duty_end,
                    disaster_shift, disaster_team,
                    blood_group, languages_spoken, training_certifications,
                    equipment_resources, availability_24x7,
                    ngo_org_name, specialization,
                    geom, photo_url, remarks,
                    arcgis_objectid, arcgis_globalid,
                    entered_by, date_of_entry, sync_updated_at
                ) VALUES (
                    %(person_name)s, %(designation)s, %(employee_id)s, %(date_of_birth)s,
                    %(dept_code)s, %(sub_department)s, %(category)s, %(hierarchy_level)s,
                    %(district_name)s, %(district_lgd)s, %(mandal_name)s, %(mandal_lgd)s,
                    %(village_name)s, %(jurisdiction_type)s, %(office_address)s,
                    %(reports_to_name)s, %(reports_to_designation)s,
                    %(parent_department)s, %(posting_type)s, %(rank_designation)s,
                    %(status)s, %(date_of_posting)s,
                    %(phone_primary)s, %(phone_alternate)s, %(whatsapp_number)s, %(email)s,
                    %(office_phone)s, %(office_phone_ext)s, %(intercom_number)s, %(fax_number)s,
                    %(residence_phone)s, %(ham_radio_callsign)s, %(residence_address)s,
                    %(esf_primary)s, %(esf_assignments)s,
                    %(dm_role)s, %(dm_role_active)s, %(dm_role_order_no)s, %(dm_role_since)s,
                    %(disaster_name)s, %(disaster_type)s, %(disaster_duty)s, %(disaster_duty_location)s,
                    %(disaster_duty_status)s, %(disaster_duty_start)s, %(disaster_duty_end)s,
                    %(disaster_shift)s, %(disaster_team)s,
                    %(blood_group)s, %(languages_spoken)s, %(training_certifications)s,
                    %(equipment_resources)s, %(availability_24x7)s,
                    %(ngo_org_name)s, %(specialization)s,
                    ST_GeomFromEWKT(%(geom)s), %(photo_url)s, %(remarks)s,
                    %(arcgis_objectid)s, %(arcgis_globalid)s,
                    %(entered_by)s, %(date_of_entry)s, NOW()
                )
                ON CONFLICT (arcgis_objectid) DO UPDATE SET
                    person_name = EXCLUDED.person_name,
                    designation = EXCLUDED.designation,
                    employee_id = EXCLUDED.employee_id,
                    date_of_birth = EXCLUDED.date_of_birth,
                    dept_code = EXCLUDED.dept_code,
                    sub_department = EXCLUDED.sub_department,
                    category = EXCLUDED.category,
                    hierarchy_level = EXCLUDED.hierarchy_level,
                    district_name = EXCLUDED.district_name,
                    district_lgd = EXCLUDED.district_lgd,
                    mandal_name = EXCLUDED.mandal_name,
                    mandal_lgd = EXCLUDED.mandal_lgd,
                    village_name = EXCLUDED.village_name,
                    jurisdiction_type = EXCLUDED.jurisdiction_type,
                    office_address = EXCLUDED.office_address,
                    reports_to_name = EXCLUDED.reports_to_name,
                    reports_to_designation = EXCLUDED.reports_to_designation,
                    parent_department = EXCLUDED.parent_department,
                    posting_type = EXCLUDED.posting_type,
                    rank_designation = EXCLUDED.rank_designation,
                    status = EXCLUDED.status,
                    date_of_posting = EXCLUDED.date_of_posting,
                    phone_primary = EXCLUDED.phone_primary,
                    phone_alternate = EXCLUDED.phone_alternate,
                    whatsapp_number = EXCLUDED.whatsapp_number,
                    email = EXCLUDED.email,
                    office_phone = EXCLUDED.office_phone,
                    office_phone_ext = EXCLUDED.office_phone_ext,
                    intercom_number = EXCLUDED.intercom_number,
                    fax_number = EXCLUDED.fax_number,
                    residence_phone = EXCLUDED.residence_phone,
                    ham_radio_callsign = EXCLUDED.ham_radio_callsign,
                    residence_address = EXCLUDED.residence_address,
                    dm_role = EXCLUDED.dm_role,
                    dm_role_active = EXCLUDED.dm_role_active,
                    dm_role_order_no = EXCLUDED.dm_role_order_no,
                    dm_role_since = EXCLUDED.dm_role_since,
                    geom = EXCLUDED.geom,
                    remarks = EXCLUDED.remarks,
                    entered_by = EXCLUDED.entered_by,
                    sync_updated_at = NOW()
            """, {
                "person_name": a.get("person_name"),
                "designation": a.get("designation") or "Not Specified",
                "employee_id": a.get("employee_id"),
                "date_of_birth": epoch_to_date(a.get("date_of_birth")),
                "dept_code": dept_code,
                "sub_department": a.get("sub_department"),
                "category": category,
                "hierarchy_level": a.get("hierarchy_level") or 6,
                "district_name": norm_district,
                "district_lgd": d_lgd,
                "mandal_name": a.get("mandal_name") if a.get("mandal_name") else None,
                "mandal_lgd": m_lgd,
                "village_name": a.get("village_name"),
                "jurisdiction_type": jtype,
                "office_address": a.get("office_address"),
                "reports_to_name": a.get("reports_to_name"),
                "reports_to_designation": a.get("reports_to_designation"),
                "parent_department": a.get("parent_department"),
                "posting_type": a.get("posting_type"),
                "rank_designation": a.get("rank_designation"),
                "status": a.get("status") or "Active",
                "date_of_posting": epoch_to_date(a.get("date_of_posting")),
                "phone_primary": a.get("phone_primary"),
                "phone_alternate": a.get("phone_alternate"),
                "whatsapp_number": a.get("whatsapp_number"),
                "email": a.get("email"),
                "office_phone": a.get("office_phone"),
                "office_phone_ext": a.get("office_phone_ext"),
                "intercom_number": a.get("intercom_number"),
                "fax_number": a.get("fax_number"),
                "residence_phone": a.get("residence_phone"),
                "ham_radio_callsign": a.get("ham_radio_callsign"),
                "residence_address": a.get("residence_address"),
                "esf_primary": a.get("esf_primary"),
                "esf_assignments": a.get("esf_assignments"),
                "dm_role": a.get("dm_role") if a.get("dm_role") else None,
                "dm_role_active": a.get("dm_role_active"),
                "dm_role_order_no": a.get("dm_role_order_no"),
                "dm_role_since": epoch_to_date(a.get("dm_role_since")),
                "disaster_name": a.get("disaster_name"),
                "disaster_type": a.get("disaster_type"),
                "disaster_duty": a.get("disaster_duty"),
                "disaster_duty_location": a.get("disaster_duty_location"),
                "disaster_duty_status": a.get("disaster_duty_status"),
                "disaster_duty_start": epoch_to_date(a.get("disaster_duty_start")),
                "disaster_duty_end": epoch_to_date(a.get("disaster_duty_end")),
                "disaster_shift": a.get("disaster_shift"),
                "disaster_team": a.get("disaster_team"),
                "blood_group": a.get("blood_group"),
                "languages_spoken": a.get("languages_spoken"),
                "training_certifications": a.get("training_certifications"),
                "equipment_resources": a.get("equipment_resources"),
                "availability_24x7": a.get("availability_24x7"),
                "ngo_org_name": a.get("ngo_org_name"),
                "specialization": a.get("specialization"),
                "geom": geom_wkt,
                "photo_url": a.get("photo_url"),
                "remarks": a.get("remarks"),
                "arcgis_objectid": oid,
                "arcgis_globalid": gid,
                "entered_by": a.get("entered_by"),
                "date_of_entry": epoch_to_datetime(a.get("date_of_entry")),
            })

        conn.commit()

        # Count results
        cur.execute("SELECT COUNT(*) FROM personnel.persons")
        total_in_db = cur.fetchone()[0]

        # Update sync log
        cur.execute("""
            UPDATE personnel.sync_log SET
                finished_at = NOW(), records_fetched = %s,
                records_inserted = %s, records_updated = %s,
                records_normalized = %s, status = 'success'
            WHERE id = %s
        """, (len(features), total_in_db, 0, normalized, sync_id))
        conn.commit()

        log.info(f"\n[4] SYNC COMPLETE:")
        log.info(f"    Fetched:    {len(features)}")
        log.info(f"    In DB:      {total_in_db}")
        log.info(f"    Normalized: {normalized} district names fixed")

        # Quick summary
        cur.execute("""
            SELECT district_name, COUNT(*)
            FROM personnel.persons
            WHERE district_name IS NOT NULL
            GROUP BY district_name ORDER BY district_name
        """)
        log.info(f"\n[5] District distribution:")
        for row in cur.fetchall():
            log.info(f"    {row[0]:35s}: {row[1]}")

        cur.execute("SELECT COUNT(*) FROM personnel.persons WHERE district_name IS NULL")
        log.info(f"    {'(State Level / NULL)':35s}: {cur.fetchone()[0]}")

        cur.execute("""
            SELECT dept_code, COUNT(*)
            FROM personnel.persons
            WHERE dept_code IS NOT NULL
            GROUP BY dept_code ORDER BY COUNT(*) DESC LIMIT 10
        """)
        log.info(f"\n[6] Top departments (by dept_code):")
        for row in cur.fetchall():
            log.info(f"    {row[0]}: {row[1]}")

        unmapped = 0
        cur.execute("SELECT COUNT(*) FROM personnel.persons WHERE dept_code IS NULL")
        unmapped = cur.fetchone()[0]
        log.info(f"    Unmapped (no dept_code): {unmapped}")

    except Exception as e:
        log.error(f"SYNC ERROR: {e}", exc_info=True)
        cur.execute(
            "UPDATE personnel.sync_log SET finished_at=NOW(), status='error', errors=%s WHERE id=%s",
            (str(e), sync_id)
        )
        conn.commit()
    finally:
        conn.close()

    log.info("=" * 60)


if __name__ == "__main__":
    sync()
