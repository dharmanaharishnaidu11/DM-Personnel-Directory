#!/usr/bin/env python3
"""
Add new fields to the existing DM_Personnel Feature Service.
- DM Role fields (nodal officer, SPOC, etc.)
- Disaster duty assignment fields
- Extended contact fields (office phone, fax, residence, etc.)
- Employee identification fields

Author: APSDMA GIS Cell
Date:   2026-02-12
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


# New fields to add
NEW_FIELDS = [
    # ── DM Role fields ──
    {"name": "dm_role",               "type": "esriFieldTypeString",  "alias": "DM Role",                       "length": 100, "nullable": True, "editable": True},
    {"name": "dm_role_active",        "type": "esriFieldTypeString",  "alias": "DM Role Active?",               "length": 10,  "nullable": True, "editable": True},
    {"name": "dm_role_order_no",      "type": "esriFieldTypeString",  "alias": "DM Role - GO/Order No.",        "length": 200, "nullable": True, "editable": True},
    {"name": "dm_role_since",         "type": "esriFieldTypeDate",    "alias": "DM Role Assigned Since",        "length": 0,   "nullable": True, "editable": True},

    # ── Disaster Duty Assignment ──
    {"name": "disaster_name",         "type": "esriFieldTypeString",  "alias": "Assigned Disaster/Event",       "length": 200, "nullable": True, "editable": True},
    {"name": "disaster_type",         "type": "esriFieldTypeString",  "alias": "Disaster Type",                 "length": 50,  "nullable": True, "editable": True},
    {"name": "disaster_duty",         "type": "esriFieldTypeString",  "alias": "Duty Assigned",                 "length": 300, "nullable": True, "editable": True},
    {"name": "disaster_duty_location","type": "esriFieldTypeString",  "alias": "Duty Location",                 "length": 200, "nullable": True, "editable": True},
    {"name": "disaster_duty_status",  "type": "esriFieldTypeString",  "alias": "Duty Status",                   "length": 20,  "nullable": True, "editable": True},
    {"name": "disaster_duty_start",   "type": "esriFieldTypeDate",    "alias": "Duty Start Date",               "length": 0,   "nullable": True, "editable": True},
    {"name": "disaster_duty_end",     "type": "esriFieldTypeDate",    "alias": "Duty End Date",                 "length": 0,   "nullable": True, "editable": True},
    {"name": "disaster_shift",        "type": "esriFieldTypeString",  "alias": "Shift / Roster",                "length": 50,  "nullable": True, "editable": True},
    {"name": "disaster_team",         "type": "esriFieldTypeString",  "alias": "Team / Group Name",             "length": 100, "nullable": True, "editable": True},

    # ── Extended Contact Info ──
    {"name": "office_phone",          "type": "esriFieldTypeString",  "alias": "Office Phone (Landline)",       "length": 20,  "nullable": True, "editable": True},
    {"name": "office_phone_ext",      "type": "esriFieldTypeString",  "alias": "Office Phone Extension",        "length": 10,  "nullable": True, "editable": True},
    {"name": "fax_number",            "type": "esriFieldTypeString",  "alias": "Fax Number",                    "length": 20,  "nullable": True, "editable": True},
    {"name": "residence_phone",       "type": "esriFieldTypeString",  "alias": "Residence Phone",               "length": 15,  "nullable": True, "editable": True},
    {"name": "residence_address",     "type": "esriFieldTypeString",  "alias": "Residence Address",             "length": 500, "nullable": True, "editable": True},
    {"name": "intercom_number",       "type": "esriFieldTypeString",  "alias": "Intercom / PBX Number",         "length": 20,  "nullable": True, "editable": True},
    {"name": "ham_radio_callsign",    "type": "esriFieldTypeString",  "alias": "HAM Radio Callsign",            "length": 20,  "nullable": True, "editable": True},

    # ── Employee Identification ──
    {"name": "employee_id",           "type": "esriFieldTypeString",  "alias": "Employee / CFMS ID",            "length": 50,  "nullable": True, "editable": True},
    {"name": "designation_code",      "type": "esriFieldTypeString",  "alias": "Designation Code (HOD Code)",   "length": 20,  "nullable": True, "editable": True},
]


def get_token():
    # Use HTTPS internal URL to avoid redirect issues
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
        # Fallback: try public URL with HTTPS
        url2 = f"https://apsdmagis.ap.gov.in/gisportal/sharing/rest/generateToken"
        resp = requests.post(url2, data=data, verify=False, timeout=30)
        result = resp.json()
    token = result.get("token")
    if not token:
        raise RuntimeError(f"Token failed: {result}")
    return token


def add_fields(token):
    """Add new fields to the existing feature service."""
    admin_url = f"{INTERNAL_SERVER}/rest/admin/services/{SERVICE_PATH}/0/addToDefinition"

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
            for f in NEW_FIELDS
        ]
    }

    data = {
        "addToDefinition": json.dumps(payload),
        "token": token,
        "f": "json",
    }

    print(f"  Adding {len(NEW_FIELDS)} new fields...")
    resp = requests.post(admin_url, data=data, verify=False, timeout=120)
    result = resp.json()

    if result.get("success"):
        print(f"  [OK] {len(NEW_FIELDS)} fields added successfully")
        return True
    else:
        print(f"  [WARN] Response: {result}")
        # Some fields may already exist — try one by one
        if "already exists" in str(result):
            print("  Trying fields individually...")
            added = 0
            for f in NEW_FIELDS:
                single = {"fields": [{
                    "name": f["name"], "type": f["type"], "alias": f["alias"],
                    "sqlType": "sqlTypeOther", "nullable": True, "editable": True,
                    **({"length": f["length"]} if f.get("length", 0) > 0 else {}),
                }]}
                d = {"addToDefinition": json.dumps(single), "token": token, "f": "json"}
                r = requests.post(admin_url, data=d, verify=False, timeout=30)
                res = r.json()
                if res.get("success"):
                    print(f"    + {f['name']}")
                    added += 1
                else:
                    print(f"    - {f['name']} (already exists or error)")
            print(f"  [OK] Added {added} new fields")
        return False


def main():
    print()
    print("=" * 70)
    print("  ADD NEW FIELDS TO DM_PERSONNEL FEATURE SERVICE")
    print("=" * 70)
    print(f"  New fields: {len(NEW_FIELDS)}")
    print(f"  Categories: DM Role (4), Disaster Duty (9), Contacts (7), ID (2)")
    print()

    token = get_token()
    print("  [OK] Token obtained")
    print()

    add_fields(token)

    print()
    print("  Fields added:")
    print("  " + "-" * 60)
    for f in NEW_FIELDS:
        print(f"    {f['alias']:40s}  ({f['name']})")
    print()


if __name__ == "__main__":
    main()
