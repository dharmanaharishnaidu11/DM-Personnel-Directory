"""
Import AP District Key Posts data into DM Personnel Feature Service.
Source: district_key_posts_export/_ALL_DISTRICTS.json
Target: https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/DM_Personnel/FeatureServer/0
Date: 2026-03-28
"""

import json
import os
import urllib.request
import urllib.parse
import ssl
import re
import time
from datetime import datetime

# --- Config ---
API_BASE = "https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/DM_Personnel/FeatureServer/0"
PORTAL_URL = "https://apsdmagis.ap.gov.in/gisportal"
USERNAME = "portaladmin"
PASSWORD = "9494501235Nn@"

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "district_key_posts_export")
INPUT_FILE = os.path.join(EXPORT_DIR, "_ALL_DISTRICTS.json")

BATCH_SIZE = 100  # ArcGIS addFeatures batch limit

# District HQ coordinates (lat, lon) for point geometry
DISTRICT_HQ = {
    "Alluri Sitha Ramaraju": (17.6868, 81.7875),  # Paderu approx
    "Anakapalli": (17.6910, 83.0037),
    "Anantapuramu": (14.6819, 77.6006),
    "Annamayya": (14.6833, 78.7333),  # Rayachoti
    "Bapatla": (15.9048, 80.4670),
    "Chittoor": (13.2172, 79.1003),
    "Dr BR Ambedkar Konaseema": (16.5769, 81.8259),  # Amalapuram
    "East Godavari": (17.0005, 81.7799),  # Rajahmundry
    "Eluru": (16.7107, 81.0952),
    "Guntur": (16.3067, 80.4365),
    "Kadapa": (14.4673, 78.8242),
    "Kakinada": (16.9891, 82.2475),
    "Krishna": (16.1740, 81.1350),  # Machilipatnam
    "Kurnool": (15.8281, 78.0373),
    "Markapuram": (15.7354, 79.2700),
    "NTR": (16.5062, 80.6480),  # Vijayawada
    "Nandyal": (15.4786, 78.4836),
    "Palnadu": (16.2360, 79.7040),  # Narasaraopet
    "Parvathipuram Manyam": (18.7668, 83.4256),
    "Polavaram": (17.2473, 81.6432),
    "Prakasam": (15.5057, 80.0499),  # Ongole
    "SPSR Nellore": (14.4426, 79.9865),
    "Sri Sathya Sai": (14.1700, 77.6100),  # Puttaparthi
    "Srikakulam": (18.2949, 83.8935),
    "Tirupati": (13.6288, 79.4192),
    "Visakhapatnam": (17.6868, 83.2185),
    "Vizianagaram": (18.1067, 83.3956),
    "West Godavari": (16.7590, 81.6800),  # Bhimavaram
}

# Map key posts department names -> DM Personnel 'category' (AP 40-dept codes)
DEPT_TO_CATEGORY = {
    "Revenue": "Revenue",
    "Home (Law & Order)": "Home",
    "Health": "Health",
    "Education": "Education",
    "Agriculture, Animal Husbandry & Cooperation": "Agriculture",
    "Panchayat Raj": "PR & RD",
    "Municipal Administration": "Municipal Admin",
    "Engineering Depts": "Infrastructure",
    "Energy": "Energy",
    "Civil Supplies": "Civil Supplies",
    "Revenue Generating Depts": "Commercial Taxes",
    "Welfare Dept": "Social Welfare",
    "Youth, Tourism, Sports & Culture": "Youth & Sports",
    "Other Departments": "General Admin",
    "ITDA": "Tribal Welfare",
}

# Map key posts department -> DM Personnel 'department' field
DEPT_TO_DEPARTMENT = {
    "Revenue": "Revenue",
    "Home (Law & Order)": "Home",
    "Health": "HM & FW",
    "Education": "Education",
    "Agriculture, Animal Husbandry & Cooperation": "Agriculture",
    "Panchayat Raj": "PR & RD",
    "Municipal Administration": "Municipal Admin",
    "Engineering Depts": "Infrastructure",
    "Energy": "Energy",
    "Civil Supplies": "Civil Supplies",
    "Revenue Generating Depts": "Commercial Taxes",
    "Welfare Dept": "Social Welfare",
    "Youth, Tourism, Sports & Culture": "Youth & Sports",
    "Other Departments": "General Admin",
    "ITDA": "Tribal Welfare",
}

# Hierarchy level assignment based on post name patterns
def get_hierarchy_level(post_name):
    post_lower = post_name.lower()
    # Level 3: District heads
    if any(x in post_lower for x in [
        "joint collector", "superintendent of police",
        "commissioner of police", "district collector",
        "chief executive officer, zilla",
    ]):
        return 3
    # Level 4: Sub-district / senior officers
    if any(x in post_lower for x in [
        "sub collector", "revenue divisional officer",
        "addl superintendent", "superintending engineer",
        "adcp", "metropolitan commissioner",
        "vice chairman",
        "po itda",
        "joint commissioner",
    ]):
        return 4
    # Level 5: District-level department heads
    return 5


def parse_js_date(date_str):
    """Parse JS date string to epoch milliseconds."""
    if not date_str or date_str in ('', 'null', 'undefined'):
        return None
    # Format: "Fri Sep 05 2025 00:00:00 GMT+0530 (India Standard Time)"
    m = re.search(r'(\w{3})\s+(\w{3})\s+(\d{1,2})\s+(\d{4})', str(date_str))
    if m:
        months = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
                  'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
        _, mon_str, day, year = m.groups()
        mon = months.get(mon_str, 1)
        dt = datetime(int(year), mon, int(day))
        return int(dt.timestamp() * 1000)
    # Try ISO format
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


def get_token():
    """Get ArcGIS Portal token."""
    ctx = ssl.create_default_context()
    params = urllib.parse.urlencode({
        'username': USERNAME,
        'password': PASSWORD,
        'client': 'referer',
        'referer': 'https://apsdmagis.ap.gov.in',
        'expiration': '120',
        'f': 'json'
    }).encode()
    req = urllib.request.Request(f"{PORTAL_URL}/sharing/rest/generateToken", data=params)
    resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    data = json.loads(resp.read())
    if 'token' not in data:
        raise Exception(f"Token error: {data}")
    return data['token']


def add_features(features, token):
    """Add features to Feature Service in batches."""
    ctx = ssl.create_default_context()
    total_added = 0
    total_failed = 0

    for i in range(0, len(features), BATCH_SIZE):
        batch = features[i:i + BATCH_SIZE]
        params = urllib.parse.urlencode({
            'features': json.dumps(batch),
            'f': 'json',
            'token': token
        }).encode()
        req = urllib.request.Request(f"{API_BASE}/addFeatures", data=params)
        resp = urllib.request.urlopen(req, context=ctx, timeout=60)
        result = json.loads(resp.read())

        if 'addResults' in result:
            ok = sum(1 for r in result['addResults'] if r.get('success'))
            fail = sum(1 for r in result['addResults'] if not r.get('success'))
            total_added += ok
            total_failed += fail
            if fail:
                errors = [r.get('error', {}).get('description', '')
                          for r in result['addResults'] if not r.get('success')]
                print(f"    Batch {i//BATCH_SIZE + 1}: {ok} added, {fail} failed: {errors[:3]}")
            else:
                print(f"    Batch {i//BATCH_SIZE + 1}: {ok} added")
        else:
            print(f"    Batch {i//BATCH_SIZE + 1}: ERROR - {str(result)[:200]}")
            total_failed += len(batch)

        time.sleep(0.3)

    return total_added, total_failed


def build_feature(record):
    """Convert a key posts record to a DM Personnel feature."""
    district = record.get('district_name', '')
    post_name = record.get('post_name', '')
    officer_name = record.get('officer_name', '')
    dept_name = record.get('department_name', '')
    is_vacant = record.get('is_vacant') in ('yes', True, 'true')
    is_no_post = record.get('is_no_post') in ('yes', True, 'true')

    # Skip no-post entries
    if is_no_post:
        return None

    # Get coordinates
    coords = DISTRICT_HQ.get(district, (15.9129, 79.7400))  # Default: AP center

    # Determine status
    if is_vacant:
        status = "Vacant"
    else:
        status = "Active"

    # Parse native district
    native = record.get('native_dist', '')
    native_name = ""
    if native and native != 'OTHER_STATE':
        # native_dist is like "D14" -- map to name
        for dname, did_check in [
            (dn, f"D{i:02d}") for i, dn in enumerate([
                "", "Alluri Sitha Ramaraju", "Anakapalli", "Anantapuramu",
                "Annamayya", "Bapatla", "Chittoor", "East Godavari", "Eluru",
                "Guntur", "Kadapa", "Kakinada", "Dr BR Ambedkar Konaseema",
                "Krishna", "Kurnool", "Parvathipuram Manyam", "Markapuram",
                "Nandyal", "SPSR Nellore", "NTR", "Palnadu", "Polavaram",
                "Prakasam", "Srikakulam", "Sri Sathya Sai", "Tirupati",
                "Visakhapatnam", "Vizianagaram", "West Godavari"
            ], 0)
        ]:
            if did_check == native:
                native_name = dname
                break
    elif native == 'OTHER_STATE':
        native_name = "Other State"

    # Build remarks with extra info
    remarks_parts = [f"Source: DM Key Posts Portal (kranthi0209)"]
    if record.get('reg_fac'):
        remarks_parts.append(f"Posting: {record['reg_fac']}")
    if native_name:
        remarks_parts.append(f"Native: {native_name}")
    eff = record.get('efficiency')
    intg = record.get('integrity')
    if eff:
        remarks_parts.append(f"E:{eff}")
    if intg:
        remarks_parts.append(f"I:{intg}")
    remarks = " | ".join(remarks_parts)

    attributes = {
        "person_name": officer_name if officer_name else ("VACANT" if is_vacant else ""),
        "designation": post_name,
        "department": DEPT_TO_DEPARTMENT.get(dept_name, dept_name),
        "category": DEPT_TO_CATEGORY.get(dept_name, dept_name),
        "hierarchy_level": get_hierarchy_level(post_name),
        "jurisdiction_type": "District",
        "status": status,
        "district_name": district,
        "employee_id": record.get('cfms_id', '') or '',
        "phone_primary": record.get('contact_no', '') or '',
        "date_of_posting": parse_js_date(record.get('from_date', '')),
        "posting_type": record.get('reg_fac', '') or '',
        "entered_by": "DM Key Posts Import 2026-03-28",
        "date_of_entry": int(datetime.now().timestamp() * 1000),
        "remarks": remarks,
    }

    # Remove None/empty values to avoid API errors
    attributes = {k: v for k, v in attributes.items() if v is not None and v != ''}

    return {
        "attributes": attributes,
        "geometry": {
            "x": coords[1],  # longitude
            "y": coords[0],  # latitude
            "spatialReference": {"wkid": 4326}
        }
    }


def main():
    print("=" * 60)
    print("DM Key Posts -> DM Personnel Feature Service Import")
    print("=" * 60)

    # Load data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)
    print(f"\nLoaded: {len(records)} records from {INPUT_FILE}")

    # Build features
    features = []
    skipped = 0
    for r in records:
        feat = build_feature(r)
        if feat:
            features.append(feat)
        else:
            skipped += 1

    print(f"Features to import: {len(features)}")
    print(f"Skipped (no_post): {skipped}")

    if not features:
        print("Nothing to import!")
        return

    # Show sample
    print(f"\nSample feature:")
    sample = features[0]
    for k, v in sample['attributes'].items():
        print(f"  {k}: {v}")
    print(f"  geometry: ({sample['geometry']['y']:.4f}, {sample['geometry']['x']:.4f})")

    # Get token
    print(f"\nGetting token...")
    token = get_token()
    print(f"Token: {token[:30]}...")

    # Check existing count
    ctx = ssl.create_default_context()
    params = urllib.parse.urlencode({
        'where': "entered_by='DM Key Posts Import 2026-03-28'",
        'returnCountOnly': 'true',
        'f': 'json',
        'token': token
    }).encode()
    req = urllib.request.Request(f"{API_BASE}/query", data=params)
    resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    existing = json.loads(resp.read())
    existing_count = existing.get('count', 0)

    if existing_count > 0:
        print(f"\nWARNING: {existing_count} records already imported with this tag!")
        print("Delete them first or they will be duplicated.")
        ans = input("Continue anyway? (yes/no): ").strip().lower()
        if ans != 'yes':
            print("Aborted.")
            return

    # Import
    print(f"\nImporting {len(features)} features in batches of {BATCH_SIZE}...")
    added, failed = add_features(features, token)

    print(f"\n{'=' * 60}")
    print(f"DONE: {added} added, {failed} failed, {skipped} skipped")
    print(f"{'=' * 60}")

    # Verify
    params = urllib.parse.urlencode({
        'where': "entered_by='DM Key Posts Import 2026-03-28'",
        'returnCountOnly': 'true',
        'f': 'json',
        'token': token
    }).encode()
    req = urllib.request.Request(f"{API_BASE}/query", data=params)
    resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    final = json.loads(resp.read())
    print(f"Verification: {final.get('count', '?')} records with import tag in Feature Service")


if __name__ == '__main__':
    main()
