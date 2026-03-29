"""
Consolidate ALL DM directory data sources into a single master directory.
Sources:
  1. GIS Server - DM_Personnel (3,654 records)
  2. GIS Server - AP_Govt_Structure (470 records)
  3. GitHub - ap-district-key-posts / Google Sheets (2,182 records)
  4. GitHub - eOffice.dashboard.ap (446 officers)
  5. GitHub - Ministers-e-Office (25 ministers)
  6. Local Excel contact files (1,357 records)
  7. GitHub - DM-Personnel-Directory (reference hierarchy)

Output: Consolidated master CSV + JSON in district_key_posts_export/
Date: 2026-03-29
"""

import json
import csv
import os
import re
from collections import Counter, defaultdict

BASE = os.path.join(os.path.dirname(__file__), "district_key_posts_export")

# Canonical district names (28 official)
CANONICAL_DISTRICTS = {
    "alluri sitha ramaraju": "Alluri Sitha Ramaraju",
    "alluri sitharama raju": "Alluri Sitha Ramaraju",
    "alluri sitarama raju": "Alluri Sitha Ramaraju",
    "asr": "Alluri Sitha Ramaraju",
    "anakapalli": "Anakapalli",
    "anantapuramu": "Anantapuramu",
    "anantapur": "Anantapuramu",
    "ananthapuramu": "Anantapuramu",
    "annamayya": "Annamayya",
    "bapatla": "Bapatla",
    "chittoor": "Chittoor",
    "dr br ambedkar konaseema": "Dr BR Ambedkar Konaseema",
    "dr. b.r. ambedkar konaseema": "Dr BR Ambedkar Konaseema",
    "dr.b.r.ambedkar konaseema": "Dr BR Ambedkar Konaseema",
    "konaseema": "Dr BR Ambedkar Konaseema",
    "east godavari": "East Godavari",
    "eluru": "Eluru",
    "guntur": "Guntur",
    "kadapa": "Kadapa",
    "ysr kadapa": "Kadapa",
    "y.s.r. kadapa": "Kadapa",
    "y.s.r.kadapa": "Kadapa",
    "kakinada": "Kakinada",
    "krishna": "Krishna",
    "kurnool": "Kurnool",
    "markapuram": "Markapuram",
    "ntr": "NTR",
    "nandyal": "Nandyal",
    "nandyala": "Nandyal",
    "spsr nellore": "SPSR Nellore",
    "s.p.s. nellore": "SPSR Nellore",
    "nellore": "SPSR Nellore",
    "sri potti sriramulu nellore": "SPSR Nellore",
    "palnadu": "Palnadu",
    "parvathipuram manyam": "Parvathipuram Manyam",
    "polavaram": "Polavaram",
    "prakasam": "Prakasam",
    "srikakulam": "Srikakulam",
    "sri sathya sai": "Sri Sathya Sai",
    "sri satya sai": "Sri Sathya Sai",
    "tirupati": "Tirupati",
    "visakhapatnam": "Visakhapatnam",
    "vishakapatnam": "Visakhapatnam",
    "vizianagaram": "Vizianagaram",
    "west godavari": "West Godavari",
    # Additional variants found in data
    "anantapuram": "Anantapuramu",
    "ananthapuram": "Anantapuramu",
    "viskahpatnam": "Visakhapatnam",
    "vishakhapatnam": "Visakhapatnam",
    "yr": "Kadapa",
    "ysr": "Kadapa",
    "y.s.r": "Kadapa",
    "kona seema": "Dr BR Ambedkar Konaseema",
    "state level": "",
}


def normalize_district(name):
    if not name:
        return ""
    key = re.sub(r'[^\w\s]', '', name.lower()).strip()
    key = re.sub(r'\s+', ' ', key)
    return CANONICAL_DISTRICTS.get(key, name.strip())


def normalize_name(name):
    if not name:
        return ""
    name = str(name).strip()
    # Remove excessive whitespace
    name = re.sub(r'\s+', ' ', name)
    # Title case if all caps
    if name == name.upper() and len(name) > 3:
        name = name.title()
    return name


def clean_phone(phone):
    if not phone:
        return ""
    phone = str(phone).strip()
    phone = re.sub(r'[^\d+]', '', phone)
    if phone.startswith('91') and len(phone) == 12:
        phone = phone[2:]
    if phone.startswith('+91'):
        phone = phone[3:]
    return phone if len(phone) >= 7 else ""


def load_json(filename):
    path = os.path.join(BASE, filename)
    if not os.path.exists(path):
        print(f"  WARNING: {filename} not found")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get('features', data.get('data', [data]))
    return data


def main():
    print("=" * 70)
    print("DM DIRECTORY CONSOLIDATION")
    print("=" * 70)

    master_records = []

    # =============================================
    # SOURCE 1: GIS DM_Personnel (primary source)
    # =============================================
    print("\n[1] GIS DM_Personnel...")
    gis_data = load_json("gis_dm_personnel_dump.json")
    count = 0
    for feat in gis_data:
        attrs = feat.get('attributes', feat) if isinstance(feat, dict) else {}
        geom = feat.get('geometry', {})
        name = attrs.get('person_name', '')
        if not name or name in ('VACANT', ''):
            continue
        rec = {
            'person_name': normalize_name(name),
            'designation': attrs.get('designation', ''),
            'department': attrs.get('department', ''),
            'category': attrs.get('category', ''),
            'district': normalize_district(attrs.get('district_name', '')),
            'mandal': attrs.get('mandal_name', ''),
            'hierarchy_level': attrs.get('hierarchy_level', ''),
            'status': attrs.get('status', 'Active'),
            'phone': clean_phone(attrs.get('phone_primary', '')),
            'phone_alt': clean_phone(attrs.get('phone_alternate', '')),
            'whatsapp': clean_phone(attrs.get('whatsapp_number', '')),
            'email': attrs.get('email', '') or '',
            'employee_id': attrs.get('employee_id', '') or '',
            'posting_type': attrs.get('posting_type', '') or '',
            'rank': attrs.get('rank_designation', '') or '',
            'dm_role': attrs.get('dm_role', '') or '',
            'reports_to': attrs.get('reports_to_name', '') or '',
            'office_address': attrs.get('office_address', '') or '',
            'longitude': geom.get('x', ''),
            'latitude': geom.get('y', ''),
            'source': f"GIS_DM_Personnel ({attrs.get('entered_by', 'unknown')})",
            'source_id': attrs.get('objectid', ''),
        }
        master_records.append(rec)
        count += 1
    print(f"  Loaded: {count} records (skipped vacant/empty)")

    # =============================================
    # SOURCE 2: GIS AP_Govt_Structure
    # =============================================
    print("\n[2] GIS AP_Govt_Structure...")
    govt_data = load_json("gis_ap_govt_structure_dump.json")
    count = 0
    for feat in govt_data:
        attrs = feat.get('attributes', feat) if isinstance(feat, dict) else {}
        name = attrs.get('officer_name', '')
        if not name:
            continue
        rec = {
            'person_name': normalize_name(name),
            'designation': attrs.get('officer_designation', '') or attrs.get('name', ''),
            'department': attrs.get('dept_name', ''),
            'category': attrs.get('dept_code', ''),
            'district': '',  # State-level entries
            'mandal': '',
            'hierarchy_level': 1 if 'Secretary' in str(attrs.get('officer_designation', '')) else 2,
            'status': 'Active',
            'phone': clean_phone(attrs.get('phone', '') or attrs.get('mobile', '')),
            'phone_alt': '',
            'whatsapp': '',
            'email': attrs.get('email', '') or '',
            'employee_id': '',
            'posting_type': '',
            'rank': '',
            'dm_role': '',
            'reports_to': attrs.get('parent_name', '') or '',
            'office_address': attrs.get('office_address', '') or '',
            'longitude': '',
            'latitude': '',
            'source': 'GIS_AP_Govt_Structure',
            'source_id': attrs.get('objectid', ''),
        }
        master_records.append(rec)
        count += 1
    print(f"  Loaded: {count} records")

    # =============================================
    # SOURCE 3: Key Posts (Google Sheets export)
    # =============================================
    print("\n[3] Key Posts (Google Sheets)...")
    kp_data = load_json("_ALL_DISTRICTS.json")
    count = 0
    for r in kp_data:
        name = r.get('officer_name', '')
        if not name:
            continue
        rec = {
            'person_name': normalize_name(name),
            'designation': r.get('post_name', ''),
            'department': r.get('department_name', ''),
            'category': r.get('dept_id', ''),
            'district': normalize_district(r.get('district_name', '') or r.get('_district_name', '')),
            'mandal': '',
            'hierarchy_level': '',
            'status': 'Vacant' if r.get('is_vacant') in ('yes', True) else 'Active',
            'phone': clean_phone(r.get('contact_no', '')),
            'phone_alt': '',
            'whatsapp': '',
            'email': '',
            'employee_id': r.get('cfms_id', '') or '',
            'posting_type': r.get('reg_fac', '') or '',
            'rank': '',
            'dm_role': '',
            'reports_to': '',
            'office_address': '',
            'longitude': '',
            'latitude': '',
            'source': 'GitHub_KeyPosts_GoogleSheets',
            'source_id': r.get('post_id', ''),
        }
        master_records.append(rec)
        count += 1
    print(f"  Loaded: {count} records")

    # =============================================
    # SOURCE 4: eOffice officers
    # =============================================
    print("\n[4] eOffice officers...")
    eo_data = load_json("github_eoffice_officers.json")
    count = 0
    for r in eo_data:
        name = r.get('person_name', '')
        if not name:
            continue
        rec = {
            'person_name': normalize_name(name),
            'designation': r.get('designation', ''),
            'department': r.get('department', ''),
            'category': r.get('cadre_type', '') or r.get('office_type', ''),
            'district': '',
            'mandal': '',
            'hierarchy_level': 1,
            'status': 'Active',
            'phone': '',
            'phone_alt': '',
            'whatsapp': '',
            'email': '',
            'employee_id': r.get('login_id', '') or '',
            'posting_type': '',
            'rank': r.get('cadre_type', '') or '',
            'dm_role': '',
            'reports_to': '',
            'office_address': '',
            'longitude': '',
            'latitude': '',
            'source': 'GitHub_eOffice_Dashboard',
            'source_id': r.get('login_id', ''),
        }
        master_records.append(rec)
        count += 1
    print(f"  Loaded: {count} records")

    # =============================================
    # SOURCE 5: Ministers roster
    # =============================================
    print("\n[5] Ministers roster...")
    min_data = load_json("github_ministers_roster.json")
    count = 0
    for r in min_data:
        name = r.get('person_name', '')
        if not name:
            continue
        rec = {
            'person_name': normalize_name(name),
            'designation': r.get('designation', ''),
            'department': r.get('department', ''),
            'category': 'Council of Ministers',
            'district': '',
            'mandal': '',
            'hierarchy_level': 0,
            'status': 'Active',
            'phone': '',
            'phone_alt': '',
            'whatsapp': '',
            'email': '',
            'employee_id': r.get('login_id', '') or '',
            'posting_type': '',
            'rank': 'Minister',
            'dm_role': '',
            'reports_to': '',
            'office_address': '',
            'longitude': '',
            'latitude': '',
            'source': 'GitHub_Ministers_eOffice',
            'source_id': r.get('login_id', ''),
        }
        master_records.append(rec)
        count += 1
    print(f"  Loaded: {count} records")

    # =============================================
    # SOURCE 6: Local Excel contacts
    # =============================================
    print("\n[6] Local Excel contacts...")
    xl_data = load_json("local_excel_contacts.json")
    count = 0
    for r in xl_data:
        name = r.get('person_name', '')
        if not name:
            continue
        rec = {
            'person_name': normalize_name(name),
            'designation': r.get('designation', ''),
            'department': '',
            'category': '',
            'district': normalize_district(r.get('district', '')),
            'mandal': '',
            'hierarchy_level': '',
            'status': 'Active',
            'phone': clean_phone(r.get('phone', '')),
            'phone_alt': '',
            'whatsapp': '',
            'email': r.get('email', '') or '',
            'employee_id': '',
            'posting_type': '',
            'rank': '',
            'dm_role': '',
            'reports_to': '',
            'office_address': '',
            'longitude': '',
            'latitude': '',
            'source': f"Local_Excel ({r.get('source', '')})",
            'source_id': '',
        }
        master_records.append(rec)
        count += 1
    print(f"  Loaded: {count} records")

    # =============================================
    # STATS & OUTPUT
    # =============================================
    print(f"\n{'=' * 70}")
    print(f"TOTAL RAW RECORDS: {len(master_records)}")
    print(f"{'=' * 70}")

    # Source breakdown
    sources = Counter(r['source'].split(' (')[0] for r in master_records)
    print("\nBy source:")
    for s, c in sources.most_common():
        print(f"  {s}: {c}")

    # District breakdown
    districts = Counter(r['district'] for r in master_records if r['district'])
    print(f"\nDistricts represented: {len(districts)}")
    for d, c in sorted(districts.items()):
        print(f"  {d}: {c}")

    # Records with phone
    with_phone = sum(1 for r in master_records if r['phone'])
    with_email = sum(1 for r in master_records if r['email'])
    with_cfms = sum(1 for r in master_records if r['employee_id'])
    print(f"\nContact coverage:")
    print(f"  With phone: {with_phone}")
    print(f"  With email: {with_email}")
    print(f"  With employee/CFMS ID: {with_cfms}")

    # =============================================
    # SAVE MASTER FILES
    # =============================================
    out_dir = os.path.join(BASE, "MASTER_DIRECTORY")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Full master JSON
    master_json = os.path.join(out_dir, "AP_DM_Master_Directory.json")
    with open(master_json, 'w', encoding='utf-8') as f:
        json.dump(master_records, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {master_json}")

    # 2. Full master CSV
    fields = ['person_name', 'designation', 'department', 'category', 'district',
              'mandal', 'hierarchy_level', 'status', 'phone', 'phone_alt',
              'whatsapp', 'email', 'employee_id', 'posting_type', 'rank',
              'dm_role', 'reports_to', 'office_address', 'longitude', 'latitude',
              'source', 'source_id']
    master_csv = os.path.join(out_dir, "AP_DM_Master_Directory.csv")
    with open(master_csv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(master_records)
    print(f"Saved: {master_csv}")

    # 3. Per-district CSVs
    district_dir = os.path.join(out_dir, "by_district")
    os.makedirs(district_dir, exist_ok=True)
    by_dist = defaultdict(list)
    for r in master_records:
        d = r['district'] or 'State_Level'
        by_dist[d].append(r)
    for dist, recs in sorted(by_dist.items()):
        fname = dist.replace(' ', '_').replace('.', '') + '.csv'
        fpath = os.path.join(district_dir, fname)
        with open(fpath, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            w.writeheader()
            w.writerows(recs)
    print(f"Saved: {len(by_dist)} district CSVs to {district_dir}")

    # 4. Dedup summary - find potential duplicates (same name + district)
    seen = defaultdict(list)
    for i, r in enumerate(master_records):
        key = (r['person_name'].lower().strip(), r['district'].lower().strip())
        seen[key].append(i)
    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    dupe_file = os.path.join(out_dir, "potential_duplicates.json")
    dupe_report = []
    for (name, dist), indices in sorted(dupes.items(), key=lambda x: -len(x[1])):
        entries = []
        for idx in indices:
            r = master_records[idx]
            entries.append({
                'person_name': r['person_name'],
                'designation': r['designation'],
                'district': r['district'],
                'phone': r['phone'],
                'source': r['source'],
            })
        dupe_report.append({
            'name': name,
            'district': dist,
            'count': len(indices),
            'entries': entries,
        })
    with open(dupe_file, 'w', encoding='utf-8') as f:
        json.dump(dupe_report, f, indent=2, ensure_ascii=False)
    print(f"Saved: {dupe_file} ({len(dupe_report)} potential duplicate groups)")

    # 5. Source index
    index = {
        "generated": "2026-03-29",
        "total_records": len(master_records),
        "sources": dict(sources.most_common()),
        "districts": len(districts),
        "with_phone": with_phone,
        "with_email": with_email,
        "with_employee_id": with_cfms,
        "duplicate_groups": len(dupe_report),
        "files": {
            "master_json": "AP_DM_Master_Directory.json",
            "master_csv": "AP_DM_Master_Directory.csv",
            "by_district": "by_district/",
            "duplicates": "potential_duplicates.json",
        },
        "source_details": [
            {"name": "GIS_DM_Personnel", "url": "https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/DM_Personnel/FeatureServer/0", "type": "ArcGIS Feature Service"},
            {"name": "GIS_AP_Govt_Structure", "url": "https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/AP_Govt_Structure/FeatureServer/0", "type": "ArcGIS Feature Service"},
            {"name": "GitHub_KeyPosts", "url": "https://kranthi0209.github.io/ap-district-key-posts/", "type": "Google Sheets via Apps Script"},
            {"name": "GitHub_eOffice", "url": "https://github.com/kranthi0209/eOffice.dashboard.ap", "type": "JSON files"},
            {"name": "GitHub_Ministers", "url": "https://github.com/kranthi0209/Ministers-e-Office", "type": "JSON files"},
            {"name": "Local_Excel", "url": "d:/APSDMA_MASTER_DATA/", "type": "Excel spreadsheets"},
            {"name": "GitHub_Hierarchy", "url": "https://github.com/dharmanaharishnaidu11/DM-Personnel-Directory", "type": "Reference (191 HODs + hierarchy)"},
        ]
    }
    index_file = os.path.join(out_dir, "_INDEX.json")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"Saved: {index_file}")

    print(f"\n{'=' * 70}")
    print(f"MASTER DIRECTORY: {out_dir}")
    print(f"{'=' * 70}")

    # File sizes
    for fname in os.listdir(out_dir):
        fpath = os.path.join(out_dir, fname)
        if os.path.isfile(fpath):
            size = os.path.getsize(fpath) / 1024
            print(f"  {fname}: {size:.1f} KB")


if __name__ == '__main__':
    main()
