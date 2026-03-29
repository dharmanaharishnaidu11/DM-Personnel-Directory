"""
Export DM_Personnel and AP_Govt_Structure feature services from APSDMA GIS Portal.
"""
import urllib.request
import urllib.parse
import json
import os
import ssl

# Disable SSL verification for internal GIS server
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

OUT_DIR = r"d:\APSDMA_MASTER_DATA\07_DATABASES\09_GO_Doccuments\district_key_posts_export"

# --- Step 1: Get Token ---
print("=" * 60)
print("Step 1: Generating token...")
token_url = "https://apsdmagis.ap.gov.in/gisportal/sharing/rest/generateToken"
token_params = urllib.parse.urlencode({
    "username": "portaladmin",
    "password": "9494501235Nn@",
    "client": "referer",
    "referer": "https://apsdmagis.ap.gov.in",
    "expiration": 120,
    "f": "json"
}).encode("utf-8")

req = urllib.request.Request(token_url, data=token_params)
req.add_header("Referer", "https://apsdmagis.ap.gov.in")
resp = urllib.request.urlopen(req, context=ctx)
token_json = json.loads(resp.read().decode("utf-8"))

if "token" not in token_json:
    print(f"ERROR: Token generation failed: {token_json}")
    raise SystemExit(1)

TOKEN = token_json["token"]
print(f"Token obtained (expires in 120 min): {TOKEN[:20]}...")


def query_all_records(service_url, token, return_geometry=True):
    """Query all records from a feature service, handling pagination."""
    all_features = []
    result_offset = 0
    batch_size = 2000
    fields_info = None

    while True:
        params = urllib.parse.urlencode({
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true" if return_geometry else "false",
            "resultRecordCount": batch_size,
            "resultOffset": result_offset,
            "f": "json",
            "token": token
        }).encode("utf-8")

        req = urllib.request.Request(service_url, data=params)
        req.add_header("Referer", "https://apsdmagis.ap.gov.in")
        resp = urllib.request.urlopen(req, context=ctx)
        data = json.loads(resp.read().decode("utf-8"))

        if "error" in data:
            print(f"  ERROR: {data['error']}")
            break

        if fields_info is None and "fields" in data:
            fields_info = data["fields"]

        features = data.get("features", [])
        all_features.extend(features)
        print(f"  Fetched {len(features)} records (total so far: {len(all_features)})")

        if len(features) < batch_size:
            break
        result_offset += batch_size

    # Build a complete response object
    result = {"features": all_features}
    if fields_info:
        result["fields"] = fields_info
    if "geometryType" in data:
        result["geometryType"] = data["geometryType"]
    if "spatialReference" in data:
        result["spatialReference"] = data["spatialReference"]

    return result


def print_summary(name, data):
    """Print summary statistics for a feature service dump."""
    features = data.get("features", [])
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {name}")
    print(f"{'=' * 60}")
    print(f"Total records: {len(features)}")

    if not features:
        return

    # Collect all attribute keys
    all_keys = set()
    for f in features:
        all_keys.update(f.get("attributes", {}).keys())
    print(f"Fields: {len(all_keys)}")
    print(f"Field names: {sorted(all_keys)}")

    attrs = [f.get("attributes", {}) for f in features]

    # District breakdown
    dist_fields = [k for k in all_keys if "district" in k.lower()]
    for df in dist_fields:
        vals = [a.get(df) for a in attrs if a.get(df)]
        unique = sorted(set(vals))
        print(f"\nUnique {df}: {len(unique)}")
        for v in unique:
            count = sum(1 for a in attrs if a.get(df) == v)
            print(f"  {v}: {count}")

    # Department breakdown
    dept_fields = [k for k in all_keys if "dept" in k.lower() or "department" in k.lower()]
    for df in dept_fields:
        vals = [a.get(df) for a in attrs if a.get(df)]
        unique = sorted(set(vals))
        print(f"\nUnique {df}: {len(unique)}")
        for v in unique[:30]:
            count = sum(1 for a in attrs if a.get(df) == v)
            print(f"  {v}: {count}")
        if len(unique) > 30:
            print(f"  ... and {len(unique) - 30} more")

    # Entered_by breakdown
    eb_fields = [k for k in all_keys if "entered" in k.lower() or "created" in k.lower() or "editor" in k.lower()]
    for ef in eb_fields:
        vals = [a.get(ef) for a in attrs if a.get(ef)]
        unique = sorted(set(str(v) for v in vals))
        print(f"\nUnique {ef}: {len(unique)}")
        for v in unique[:20]:
            count = sum(1 for a in attrs if str(a.get(ef, "")) == v)
            print(f"  {v}: {count}")

    # Status breakdown
    status_fields = [k for k in all_keys if "status" in k.lower()]
    for sf in status_fields:
        vals = [a.get(sf) for a in attrs if a.get(sf)]
        unique = sorted(set(str(v) for v in vals))
        print(f"\nUnique {sf}: {len(unique)}")
        for v in unique:
            count = sum(1 for a in attrs if str(a.get(sf, "")) == v)
            print(f"  {v}: {count}")

    # Designation breakdown (useful for personnel)
    desig_fields = [k for k in all_keys if "designat" in k.lower() or "post" in k.lower() or "role" in k.lower()]
    for df in desig_fields:
        vals = [a.get(df) for a in attrs if a.get(df)]
        unique = sorted(set(str(v) for v in vals))
        print(f"\nUnique {df}: {len(unique)}")
        for v in unique[:30]:
            count = sum(1 for a in attrs if str(a.get(df, "")) == v)
            print(f"  {v}: {count}")
        if len(unique) > 30:
            print(f"  ... and {len(unique) - 30} more")


# --- Step 2: DM_Personnel ---
print("\n" + "=" * 60)
print("Step 2: Querying DM_Personnel...")
dm_url = "https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/DM_Personnel/FeatureServer/0/query"
dm_data = query_all_records(dm_url, TOKEN, return_geometry=True)

dm_path = os.path.join(OUT_DIR, "gis_dm_personnel_dump.json")
with open(dm_path, "w", encoding="utf-8") as f:
    json.dump(dm_data, f, indent=2, ensure_ascii=False)
print(f"Saved to: {dm_path}")

# --- Step 3: AP_Govt_Structure ---
print("\n" + "=" * 60)
print("Step 3: Querying AP_Govt_Structure...")
govt_url = "https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/AP_Govt_Structure/FeatureServer/0/query"
govt_data = query_all_records(govt_url, TOKEN, return_geometry=False)

govt_path = os.path.join(OUT_DIR, "gis_ap_govt_structure_dump.json")
with open(govt_path, "w", encoding="utf-8") as f:
    json.dump(govt_data, f, indent=2, ensure_ascii=False)
print(f"Saved to: {govt_path}")

# --- Step 4: Summaries ---
print_summary("DM_Personnel", dm_data)
print_summary("AP_Govt_Structure", govt_data)

print("\n" + "=" * 60)
print("DONE. Both services exported successfully.")
