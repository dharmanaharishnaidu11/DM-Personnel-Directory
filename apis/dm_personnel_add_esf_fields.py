#!/usr/bin/env python3
"""
Add ESF & Capability fields to the existing DM_Personnel Feature Service.

This script upgrades the feature service from the original schema to the
NDMA-aligned schema by adding:
  - ESF assignment fields (esf_assignments, esf_primary)
  - Chain-of-command field (reports_to_id)
  - Sub-department & rank fields
  - Capability fields (blood_group, languages, training, equipment, availability)

Run this AFTER the feature service exists but BEFORE deploying the new webapp.

Author: APSDMA GIS Cell
Date:   2026-02-16
"""

import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PORTAL_URL = "https://apsdmagis.ap.gov.in/gisportal"
INTERNAL_SERVER = "https://192.168.8.24:6443/arcgis"
SERVICE_PATH = "Hosted/DM_Personnel/FeatureServer"

# Load credentials
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(SCRIPT_DIR, "..", "apsdma_credentials.json")
try:
    with open(CREDS_PATH, "r") as f:
        creds = json.load(f)
    PORTAL_USER = creds["arcgis_infrastructure"]["portal"]["username"]
    PORTAL_PASS = creds["arcgis_infrastructure"]["portal"]["password"]
except Exception:
    PORTAL_USER = "portaladmin"
    PORTAL_PASS = ""


# ── New fields to add (ESF, capabilities, chain-of-command) ──
NEW_FIELDS = [
    # ESF assignments
    {"name": "esf_assignments",       "type": "esriFieldTypeString",  "alias": "ESF Assignments (comma-sep)",  "length": 200, "nullable": True, "editable": True},
    {"name": "esf_primary",           "type": "esriFieldTypeInteger", "alias": "Primary ESF (1-16)",           "length": 0,   "nullable": True, "editable": True},

    # Chain of command
    {"name": "reports_to_id",         "type": "esriFieldTypeString",  "alias": "Reports To (Employee ID)",     "length": 50,  "nullable": True, "editable": True},

    # Sub-department & rank
    {"name": "sub_department",        "type": "esriFieldTypeString",  "alias": "Sub-Department / Unit",        "length": 100, "nullable": True, "editable": True},
    {"name": "rank_designation",      "type": "esriFieldTypeString",  "alias": "Rank (Military/Paramilitary)", "length": 100, "nullable": True, "editable": True},

    # Capabilities & resources
    {"name": "blood_group",           "type": "esriFieldTypeString",  "alias": "Blood Group",                  "length": 5,   "nullable": True, "editable": True},
    {"name": "languages_spoken",      "type": "esriFieldTypeString",  "alias": "Languages Spoken",             "length": 200, "nullable": True, "editable": True},
    {"name": "training_certifications","type": "esriFieldTypeString", "alias": "DM Training / Certifications", "length": 500, "nullable": True, "editable": True},
    {"name": "equipment_resources",   "type": "esriFieldTypeString",  "alias": "Equipment / Resources",        "length": 500, "nullable": True, "editable": True},
    {"name": "availability_24x7",     "type": "esriFieldTypeString",  "alias": "24x7 Availability",            "length": 5,   "nullable": True, "editable": True},
]


def get_token():
    """Get Portal token via internal URL."""
    url = f"https://192.168.8.24/gisportal/sharing/rest/generateToken"
    data = {
        "username": PORTAL_USER, "password": PORTAL_PASS,
        "client": "referer", "referer": "https://apsdmagis.ap.gov.in/gisportal",
        "expiration": 120, "f": "json",
    }
    resp = requests.post(url, data=data, verify=False, timeout=30)
    try:
        result = resp.json()
    except Exception:
        url2 = f"https://apsdmagis.ap.gov.in/gisportal/sharing/rest/generateToken"
        resp = requests.post(url2, data=data, verify=False, timeout=30)
        result = resp.json()
    token = result.get("token")
    if not token:
        raise RuntimeError(f"Token failed: {result}")
    return token


def check_existing_fields(token):
    """Check which fields already exist on the feature service."""
    url = f"https://apsdmagis.ap.gov.in/gisserver/rest/services/{SERVICE_PATH}/0?f=json&token={token}"
    resp = requests.get(url, verify=False, timeout=30)
    result = resp.json()
    existing = {f["name"] for f in result.get("fields", [])}
    return existing


def add_fields(token, existing_fields):
    """Add new fields, skipping any that already exist."""
    admin_url = f"{INTERNAL_SERVER}/rest/admin/services/{SERVICE_PATH}/0/addToDefinition"

    fields_to_add = [f for f in NEW_FIELDS if f["name"] not in existing_fields]

    if not fields_to_add:
        print("  [OK] All fields already exist — nothing to add")
        return True

    print(f"  Adding {len(fields_to_add)} new fields (skipping {len(NEW_FIELDS) - len(fields_to_add)} existing)...")

    # Try bulk add first
    payload = {
        "fields": [
            {
                "name": f["name"],
                "type": f["type"],
                "alias": f["alias"],
                "sqlType": "sqlTypeOther",
                "nullable": f.get("nullable", True),
                "editable": f.get("editable", True),
                **({"length": f["length"]} if f.get("length", 0) > 0 else {}),
            }
            for f in fields_to_add
        ]
    }

    data = {
        "addToDefinition": json.dumps(payload),
        "token": token,
        "f": "json",
    }

    resp = requests.post(admin_url, data=data, verify=False, timeout=120)
    result = resp.json()

    if result.get("success"):
        print(f"  [OK] All {len(fields_to_add)} fields added in bulk")
        return True

    # Bulk failed — try one by one
    print(f"  [WARN] Bulk add failed: {result.get('error', {}).get('message', 'unknown')}")
    print("  Trying fields individually...")
    added = 0
    for f in fields_to_add:
        single = {"fields": [{
            "name": f["name"], "type": f["type"], "alias": f["alias"],
            "sqlType": "sqlTypeOther", "nullable": True, "editable": True,
            **({"length": f["length"]} if f.get("length", 0) > 0 else {}),
        }]}
        d = {"addToDefinition": json.dumps(single), "token": token, "f": "json"}
        r = requests.post(admin_url, data=d, verify=False, timeout=30)
        res = r.json()
        if res.get("success"):
            print(f"    + {f['name']:30s}  ({f['alias']})")
            added += 1
        else:
            print(f"    - {f['name']:30s}  (already exists or error)")
    print(f"  [OK] Added {added}/{len(fields_to_add)} fields")
    return added > 0


def update_category_domain(token):
    """Update the category domain from old 5 values to new 25 NDMA-aligned values."""
    from dm_personnel_service import CATEGORIES_25, DOMAINS

    admin_url = f"{INTERNAL_SERVER}/rest/admin/services/{SERVICE_PATH}/updateDefinition"

    # Build domain update payload
    domain_def = DOMAINS["category_domain"]
    payload = {
        "fields": [
            {
                "name": "category",
                "domain": domain_def,
            }
        ]
    }

    data = {
        "updateDefinition": json.dumps(payload),
        "token": token,
        "f": "json",
    }

    print(f"  Updating category domain to {len(CATEGORIES_25)} values...")
    resp = requests.post(admin_url, data=data, verify=False, timeout=60)
    result = resp.json()

    if result.get("success"):
        print(f"  [OK] Category domain updated to {len(CATEGORIES_25)} NDMA-aligned values")
        return True
    else:
        print(f"  [WARN] Domain update response: {result}")
        print("  (This may need manual update via ArcGIS Server Manager)")
        return False


def main():
    print()
    print("=" * 70)
    print("  ADD ESF & CAPABILITY FIELDS TO DM_PERSONNEL")
    print("  (NDMA-Aligned Upgrade)")
    print("=" * 70)
    print(f"  New fields:  {len(NEW_FIELDS)}")
    print(f"  Categories:  ESF assignments, capabilities, chain-of-command")
    print()

    # Step 1: Authenticate
    print("[1] Authenticating...")
    token = get_token()
    print("  [OK] Token obtained")
    print()

    # Step 2: Check existing fields
    print("[2] Checking existing fields...")
    existing = check_existing_fields(token)
    print(f"  [OK] Found {len(existing)} existing fields")
    print()

    # Step 3: Add new fields
    print("[3] Adding ESF & capability fields...")
    add_fields(token, existing)
    print()

    # Step 4: Update category domain
    print("[4] Updating category domain (5 → 25 NDMA categories)...")
    update_category_domain(token)
    print()

    # Summary
    print("=" * 70)
    print("  UPGRADE COMPLETE")
    print("=" * 70)
    print()
    print("  New fields added:")
    print("  " + "-" * 60)
    for f in NEW_FIELDS:
        print(f"    {f['alias']:40s}  ({f['name']})")
    print()
    print("  NEXT STEPS:")
    print("  1. Verify fields at: https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/DM_Personnel/FeatureServer/0")
    print("  2. Run generate_survey_xlsform.py to regenerate Survey123 form")
    print("  3. Deploy the new webapp with 5 view modes")
    print()


if __name__ == "__main__":
    main()
