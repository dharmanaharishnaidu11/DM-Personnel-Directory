#!/usr/bin/env python3
"""
DM Personnel Feature Service — Create & Publish (NDMA-Aligned)
Creates a hosted feature layer in ArcGIS Enterprise Portal for the
Disaster Management Personnel Directory — 8 Sectors, 25 Categories,
16 ESFs per NDMA DM Act 2005 / NDMP 2019.

Author: APSDMA GIS Cell
Date:   2026-02-16
"""

import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PORTAL_URL = "https://apsdmagis.ap.gov.in/gisportal"
SERVER_URL = "https://apsdmagis.ap.gov.in/gisserver"

# Load credentials
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(SCRIPT_DIR, "..", "apsdma_credentials.json")

try:
    with open(CREDS_PATH, "r") as f:
        creds = json.load(f)
    PORTAL_USER = creds["arcgis_infrastructure"]["portal"]["username"]
    PORTAL_PASS = creds["arcgis_infrastructure"]["portal"]["password"]
except Exception as e:
    print(f"Warning: Could not load credentials: {e}")
    PORTAL_USER = "portaladmin"
    PORTAL_PASS = ""

SERVICE_NAME = "DM_Personnel"
FOLDER_NAME = "APSDMADepartments2025"

# ---------------------------------------------------------------------------
# AP Districts & Mandals for coded-value domains
# ---------------------------------------------------------------------------
AP_DISTRICTS = [
    "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya",
    "Bapatla", "Chittoor", "Dr.B.R.Ambedkar Konaseema", "East Godavari",
    "Eluru", "Guntur", "Kakinada", "Krishna", "Kurnool",
    "Markapuram", "Nandyal", "NTR", "Palnadu",
    "Parvathipuram Manyam", "Polavaram", "Prakasam",
    "Sri Potti Sriramulu Nellore", "Sri Sathya Sai", "Srikakulam",
    "Tirupati", "Visakhapatnam", "Vizianagaram", "West Godavari",
    "Y.S.R.Kadapa",
]

# ---------------------------------------------------------------------------
# Feature service field definitions
# ---------------------------------------------------------------------------
FIELDS = [
    # ── Core identity ──
    {"name": "person_name",          "type": "esriFieldTypeString",  "length": 200, "alias": "Full Name",              "nullable": False},
    {"name": "designation",          "type": "esriFieldTypeString",  "length": 150, "alias": "Designation",            "nullable": False},
    {"name": "department",           "type": "esriFieldTypeString",  "length": 100, "alias": "Department",             "nullable": False},
    {"name": "sub_department",       "type": "esriFieldTypeString",  "length": 100, "alias": "Sub-Department / Unit",  "nullable": True},
    {"name": "category",             "type": "esriFieldTypeString",  "length": 60,  "alias": "Category",               "nullable": False},
    {"name": "hierarchy_level",      "type": "esriFieldTypeInteger", "length": 0,   "alias": "Hierarchy Level (1-6)",   "nullable": False},
    {"name": "rank_designation",     "type": "esriFieldTypeString",  "length": 100, "alias": "Rank (Military/Para)",   "nullable": True},
    {"name": "employee_id",          "type": "esriFieldTypeString",  "length": 50,  "alias": "Employee / CFMS ID",     "nullable": True},
    {"name": "designation_code",     "type": "esriFieldTypeString",  "length": 20,  "alias": "Designation Code",       "nullable": True},

    # ── Reporting chain ──
    {"name": "reports_to_name",      "type": "esriFieldTypeString",  "length": 200, "alias": "Reports To (Name)",      "nullable": True},
    {"name": "reports_to_designation","type": "esriFieldTypeString",  "length": 150, "alias": "Reports To (Designation)","nullable": True},
    {"name": "reports_to_id",        "type": "esriFieldTypeString",  "length": 50,  "alias": "Reports To (Emp ID)",    "nullable": True},

    # ── ESF assignments ──
    {"name": "esf_assignments",      "type": "esriFieldTypeString",  "length": 200, "alias": "ESF Assignments",        "nullable": True},
    {"name": "esf_primary",          "type": "esriFieldTypeInteger", "length": 0,   "alias": "Primary ESF (1-16)",     "nullable": True},

    # ── Contact info ──
    {"name": "phone_primary",        "type": "esriFieldTypeString",  "length": 15,  "alias": "Primary Phone",          "nullable": True},
    {"name": "phone_alternate",      "type": "esriFieldTypeString",  "length": 15,  "alias": "Alternate Phone",        "nullable": True},
    {"name": "whatsapp_number",      "type": "esriFieldTypeString",  "length": 15,  "alias": "WhatsApp Number",        "nullable": True},
    {"name": "office_phone",         "type": "esriFieldTypeString",  "length": 20,  "alias": "Office Phone (Landline)","nullable": True},
    {"name": "office_phone_ext",     "type": "esriFieldTypeString",  "length": 10,  "alias": "Office Phone Extension", "nullable": True},
    {"name": "intercom_number",      "type": "esriFieldTypeString",  "length": 20,  "alias": "Intercom / PBX Number",  "nullable": True},
    {"name": "fax_number",           "type": "esriFieldTypeString",  "length": 20,  "alias": "Fax Number",             "nullable": True},
    {"name": "residence_phone",      "type": "esriFieldTypeString",  "length": 15,  "alias": "Residence Phone",        "nullable": True},
    {"name": "ham_radio_callsign",   "type": "esriFieldTypeString",  "length": 20,  "alias": "HAM Radio Callsign",     "nullable": True},
    {"name": "email",                "type": "esriFieldTypeString",  "length": 100, "alias": "Official Email",         "nullable": True},
    {"name": "residence_address",    "type": "esriFieldTypeString",  "length": 500, "alias": "Residence Address",      "nullable": True},

    # ── Posting / jurisdiction ──
    {"name": "district_name",        "type": "esriFieldTypeString",  "length": 100, "alias": "District",               "nullable": True},
    {"name": "mandal_name",          "type": "esriFieldTypeString",  "length": 100, "alias": "Mandal",                 "nullable": True},
    {"name": "village_name",         "type": "esriFieldTypeString",  "length": 100, "alias": "Village/Ward",           "nullable": True},
    {"name": "jurisdiction_type",    "type": "esriFieldTypeString",  "length": 20,  "alias": "Jurisdiction Level",     "nullable": False},
    {"name": "office_address",       "type": "esriFieldTypeString",  "length": 500, "alias": "Office Address",         "nullable": True},
    {"name": "status",               "type": "esriFieldTypeString",  "length": 20,  "alias": "Current Status",         "nullable": False},
    {"name": "date_of_posting",      "type": "esriFieldTypeDate",    "length": 0,   "alias": "Date of Posting",        "nullable": True},

    # ── DM Role ──
    {"name": "dm_role",              "type": "esriFieldTypeString",  "length": 100, "alias": "DM Role",                "nullable": True},
    {"name": "dm_role_active",       "type": "esriFieldTypeString",  "length": 10,  "alias": "DM Role Active?",        "nullable": True},
    {"name": "dm_role_order_no",     "type": "esriFieldTypeString",  "length": 200, "alias": "DM Role GO/Order No.",   "nullable": True},
    {"name": "dm_role_since",        "type": "esriFieldTypeDate",    "length": 0,   "alias": "DM Role Since",          "nullable": True},

    # ── Disaster duty ──
    {"name": "disaster_name",        "type": "esriFieldTypeString",  "length": 200, "alias": "Disaster/Event Name",    "nullable": True},
    {"name": "disaster_type",        "type": "esriFieldTypeString",  "length": 50,  "alias": "Disaster Type",          "nullable": True},
    {"name": "disaster_duty",        "type": "esriFieldTypeString",  "length": 300, "alias": "Duty Assigned",          "nullable": True},
    {"name": "disaster_duty_location","type": "esriFieldTypeString", "length": 200, "alias": "Duty Location",          "nullable": True},
    {"name": "disaster_duty_status", "type": "esriFieldTypeString",  "length": 20,  "alias": "Duty Status",            "nullable": True},
    {"name": "disaster_duty_start",  "type": "esriFieldTypeDate",    "length": 0,   "alias": "Duty Start Date",        "nullable": True},
    {"name": "disaster_duty_end",    "type": "esriFieldTypeDate",    "length": 0,   "alias": "Duty End Date",          "nullable": True},
    {"name": "disaster_shift",       "type": "esriFieldTypeString",  "length": 50,  "alias": "Shift / Roster",         "nullable": True},
    {"name": "disaster_team",        "type": "esriFieldTypeString",  "length": 100, "alias": "Team / Group Name",      "nullable": True},

    # ── Capabilities & resources ──
    {"name": "blood_group",          "type": "esriFieldTypeString",  "length": 5,   "alias": "Blood Group",            "nullable": True},
    {"name": "languages_spoken",     "type": "esriFieldTypeString",  "length": 200, "alias": "Languages Spoken",       "nullable": True},
    {"name": "training_certifications","type": "esriFieldTypeString", "length": 500, "alias": "DM Training/Certs",     "nullable": True},
    {"name": "equipment_resources",  "type": "esriFieldTypeString",  "length": 500, "alias": "Equipment/Resources",    "nullable": True},
    {"name": "availability_24x7",    "type": "esriFieldTypeString",  "length": 5,   "alias": "24x7 Availability",      "nullable": True},

    # ── NGO / specialization ──
    {"name": "specialization",       "type": "esriFieldTypeString",  "length": 200, "alias": "Specialization / Role",  "nullable": True},
    {"name": "ngo_org_name",         "type": "esriFieldTypeString",  "length": 200, "alias": "NGO/Organization Name",  "nullable": True},

    # ── Metadata ──
    {"name": "photo_url",            "type": "esriFieldTypeString",  "length": 500, "alias": "Photo URL",              "nullable": True},
    {"name": "remarks",              "type": "esriFieldTypeString",  "length": 500, "alias": "Remarks",                "nullable": True},
    {"name": "date_of_entry",        "type": "esriFieldTypeDate",    "length": 0,   "alias": "Date of Entry",          "nullable": True},
    {"name": "entered_by",           "type": "esriFieldTypeString",  "length": 100, "alias": "Entered By",             "nullable": True},
]

# ---------------------------------------------------------------------------
# 25 NDMA-Aligned Categories (8 Sectors — sector derived client-side)
# ---------------------------------------------------------------------------
CATEGORIES_25 = [
    # Sector: Executive & Revenue Admin
    "Revenue & District Administration",
    "Civil Defence",
    "Home Guards",
    # Sector: Law Enforcement & Security
    "Police",
    "Armed Forces",
    # Sector: Fire & Rescue Forces
    "Fire & Emergency Services",
    "SDRF",
    "NDRF",
    # Sector: Health & Medical
    "Medical & Public Health",
    "Veterinary & Animal Husbandry",
    # Sector: Infrastructure & Utilities
    "Irrigation & Water Resources",
    "Public Works / R&B",
    "Power / Electricity",
    "Telecom & Communications",
    "Transport",
    "Municipal & Urban Development",
    # Sector: Rural & Social Services
    "Panchayat Raj & Rural Development",
    "Food & Civil Supplies",
    "Education",
    "Agriculture & Fisheries",
    # Sector: Youth & Voluntary Sector
    "NCC / Youth Organizations",
    "NGOs & Volunteer Organizations",
    "Private Sector / CSR",
    # Sector: Information & Coordination
    "Media & Public Information",
    "APSDMA / DM Coordination",
]

# Coded-value domains
DOMAINS = {
    "category_domain": {
        "type": "codedValue",
        "name": "category_domain",
        "codedValues": [{"name": c, "code": c} for c in CATEGORIES_25],
    },
    "hierarchy_level_domain": {
        "type": "codedValue",
        "name": "hierarchy_level_domain",
        "codedValues": [
            {"name": "1 - Apex / State",           "code": 1},
            {"name": "2 - Department Head",         "code": 2},
            {"name": "3 - District Head",           "code": 3},
            {"name": "4 - Sub-District / Division", "code": 4},
            {"name": "5 - Mandal / Block",          "code": 5},
            {"name": "6 - Village / Last Mile",     "code": 6},
        ],
    },
    "jurisdiction_type_domain": {
        "type": "codedValue",
        "name": "jurisdiction_type_domain",
        "codedValues": [
            {"name": "State",    "code": "State"},
            {"name": "District", "code": "District"},
            {"name": "Division", "code": "Division"},
            {"name": "Mandal",   "code": "Mandal"},
            {"name": "Village",  "code": "Village"},
        ],
    },
    "status_domain": {
        "type": "codedValue",
        "name": "status_domain",
        "codedValues": [
            {"name": "Active",      "code": "Active"},
            {"name": "On Leave",    "code": "On Leave"},
            {"name": "Transferred", "code": "Transferred"},
            {"name": "Retired",     "code": "Retired"},
            {"name": "Vacant",      "code": "Vacant"},
        ],
    },
    "esf_primary_domain": {
        "type": "codedValue",
        "name": "esf_primary_domain",
        "codedValues": [
            {"name": "ESF-1: Communication",                 "code": 1},
            {"name": "ESF-2: Public Works & Engineering",    "code": 2},
            {"name": "ESF-3: Transport",                     "code": 3},
            {"name": "ESF-4: Search & Rescue",               "code": 4},
            {"name": "ESF-5: Emergency Management / IRS",    "code": 5},
            {"name": "ESF-6: Mass Care (Shelter, Food)",     "code": 6},
            {"name": "ESF-7: Resource Support (Logistics)",  "code": 7},
            {"name": "ESF-8: Public Health & Medical",       "code": 8},
            {"name": "ESF-9: Firefighting",                  "code": 9},
            {"name": "ESF-10: Hazardous Materials (CBRN)",   "code": 10},
            {"name": "ESF-11: Agriculture & Animal Protection","code": 11},
            {"name": "ESF-12: Energy (Power, Fuel)",         "code": 12},
            {"name": "ESF-13: Law & Order / Security",       "code": 13},
            {"name": "ESF-14: Long-Term Recovery",           "code": 14},
            {"name": "ESF-15: Public Information / Media",   "code": 15},
            {"name": "ESF-16: Debris Management",            "code": 16},
        ],
    },
    "blood_group_domain": {
        "type": "codedValue",
        "name": "blood_group_domain",
        "codedValues": [
            {"name": "A+", "code": "A+"}, {"name": "A-", "code": "A-"},
            {"name": "B+", "code": "B+"}, {"name": "B-", "code": "B-"},
            {"name": "AB+","code": "AB+"},{"name": "AB-","code": "AB-"},
            {"name": "O+", "code": "O+"}, {"name": "O-", "code": "O-"},
        ],
    },
    "availability_domain": {
        "type": "codedValue",
        "name": "availability_domain",
        "codedValues": [
            {"name": "Yes", "code": "Yes"},
            {"name": "No",  "code": "No"},
        ],
    },
    "district_domain": {
        "type": "codedValue",
        "name": "district_domain",
        "codedValues": [{"name": d, "code": d} for d in AP_DISTRICTS],
    },
}

# Category → RGB color (matches dm-config.js)
CATEGORY_COLORS = {
    "Revenue & District Administration": [49, 130, 206],
    "Civil Defence":                     [66, 153, 225],
    "Home Guards":                       [99, 179, 237],
    "Police":                            [229, 62, 62],
    "Armed Forces":                      [197, 48, 48],
    "Fire & Emergency Services":         [255, 152, 0],
    "SDRF":                              [255, 183, 77],
    "NDRF":                              [255, 112, 67],
    "Medical & Public Health":           [56, 161, 105],
    "Veterinary & Animal Husbandry":     [72, 187, 120],
    "Irrigation & Water Resources":      [128, 90, 213],
    "Public Works / R&B":                [139, 92, 246],
    "Power / Electricity":               [167, 139, 250],
    "Telecom & Communications":          [109, 40, 217],
    "Transport":                         [91, 33, 182],
    "Municipal & Urban Development":     [124, 58, 237],
    "Panchayat Raj & Rural Development": [38, 166, 154],
    "Food & Civil Supplies":             [0, 150, 136],
    "Education":                         [0, 137, 123],
    "Agriculture & Fisheries":           [77, 182, 172],
    "NCC / Youth Organizations":         [214, 158, 46],
    "NGOs & Volunteer Organizations":    [236, 201, 75],
    "Private Sector / CSR":              [183, 121, 31],
    "Media & Public Information":        [233, 30, 99],
    "APSDMA / DM Coordination":          [194, 24, 91],
}


# ---------------------------------------------------------------------------
# Portal helpers
# ---------------------------------------------------------------------------

def get_token():
    """Get Portal token."""
    url = f"{PORTAL_URL}/sharing/rest/generateToken"
    data = {
        "username": PORTAL_USER,
        "password": PORTAL_PASS,
        "client": "referer",
        "referer": PORTAL_URL,
        "expiration": 120,
        "f": "json",
    }
    resp = requests.post(url, data=data, verify=False, timeout=30)
    result = resp.json()
    token = result.get("token")
    if not token:
        raise RuntimeError(f"Token generation failed: {result}")
    print(f"  [OK] Token obtained")
    return token


def _build_layer_def():
    """Build the layer definition for addToDefinition."""
    return {
        "layers": [
            {
                "id": 0,
                "name": "DM_Personnel",
                "type": "Feature Layer",
                "geometryType": "esriGeometryPoint",
                "description": "NDMA-aligned Disaster Management Personnel Directory — 8 Sectors, 25 Categories, 16 ESFs",
                "objectIdField": "OBJECTID",
                "globalIdField": "GlobalID",
                "hasAttachments": True,
                "supportedQueryFormats": "JSON",
                "capabilities": "Create,Delete,Query,Update,Editing",
                "allowGeometryUpdates": True,
                "hasZ": False,
                "hasM": False,
                "extent": {
                    "xmin": 76.72, "ymin": 12.41,
                    "xmax": 84.85, "ymax": 19.92,
                    "spatialReference": {"wkid": 4326}
                },
                "drawingInfo": {
                    "renderer": {
                        "type": "uniqueValue",
                        "field1": "category",
                        "defaultSymbol": {
                            "type": "esriSMS",
                            "style": "esriSMSCircle",
                            "color": [78, 78, 78, 255],
                            "size": 8,
                        },
                        "uniqueValueInfos": [
                            {"value": c, "label": c,
                             "symbol": {"type": "esriSMS", "style": "esriSMSCircle",
                                        "color": CATEGORY_COLORS.get(c, [78, 78, 78]) + [255], "size": 9}}
                            for c in CATEGORIES_25
                        ],
                    }
                },
                "fields": [
                    {"name": "OBJECTID",  "type": "esriFieldTypeOID",       "alias": "OBJECTID",  "sqlType": "sqlTypeOther"},
                    {"name": "GlobalID",  "type": "esriFieldTypeGlobalID",  "alias": "GlobalID",  "sqlType": "sqlTypeOther", "length": 38},
                ] + [
                    {
                        "name": f["name"],
                        "type": f["type"],
                        "alias": f["alias"],
                        "sqlType": "sqlTypeOther",
                        "nullable": f["nullable"],
                        "editable": True,
                        **({"length": f["length"]} if f["length"] > 0 else {}),
                    }
                    for f in FIELDS
                ],
                "types": [],
                "templates": [
                    {
                        "name": "DM Personnel",
                        "description": "",
                        "prototype": {
                            "attributes": {
                                "status": "Active",
                                "hierarchy_level": 3,
                                "jurisdiction_type": "District",
                            }
                        },
                    }
                ],
            }
        ],
    }



def create_feature_service(token):
    """Create the hosted feature service via createService REST endpoint."""
    layer_def = _build_layer_def()

    # createService endpoint
    url = f"{PORTAL_URL}/sharing/rest/content/users/{PORTAL_USER}/createService"
    data = {
        "createParameters": json.dumps({
            "name": SERVICE_NAME,
            "serviceDescription": "APSDMA Disaster Management Personnel Directory",
            "hasStaticData": False,
            "maxRecordCount": 10000,
            "supportedQueryFormats": "JSON",
            "capabilities": "Create,Delete,Query,Update,Editing",
            "description": "NDMA-aligned DM Personnel Directory — 8 Sectors, 25 Categories, 16 ESFs across all AP districts.",
            "allowGeometryUpdates": True,
            "units": "esriDecimalDegrees",
            "xssPreventionInfo": {"xssPreventionEnabled": True, "xssPreventionRule": "input", "xssInputRule": "rejectInvalid"},
        }),
        "targetType": "featureService",
        "token": token,
        "f": "json",
    }

    print("  Creating feature service...")
    resp = requests.post(url, data=data, verify=False, timeout=60)
    result = resp.json()

    if not result.get("success"):
        error = result.get("error", {})
        if "already exists" in str(error.get("message", "")):
            print(f"  [WARN] Service '{SERVICE_NAME}' already exists.")
            # Try to find the existing service
            return find_existing_service(token)
        raise RuntimeError(f"createService failed: {result}")

    item_id = result["itemId"]
    service_url = result["encodedServiceURL"]
    print(f"  [OK] Service created: {item_id}")
    print(f"       URL: {service_url}")

    # Now add the layer definition to the service
    # The returned URL may use public hostname (HTTP), but we need internal HTTPS for admin API
    admin_service_url = service_url.replace("/rest/services/", "/rest/admin/services/")
    # Force internal HTTPS endpoint for admin operations
    admin_url = admin_service_url.replace(
        "http://apsdmagis.ap.gov.in/gisserver",
        "https://192.168.8.24:6443/arcgis"
    ).replace(
        "https://apsdmagis.ap.gov.in/gisserver",
        "https://192.168.8.24:6443/arcgis"
    )
    add_url = f"{admin_url}/addToDefinition"
    add_data = {
        "addToDefinition": json.dumps(layer_def),
        "token": token,
        "f": "json",
    }

    print("  Adding layer definition...")
    resp = requests.post(add_url, data=add_data, verify=False, timeout=120)
    result = resp.json()

    if not result.get("success"):
        print(f"  [WARN] addToDefinition response: {result}")
    else:
        print(f"  [OK] Layer definition added successfully")

    return item_id, service_url


def find_existing_service(token):
    """Find existing DM_Personnel service in Portal."""
    url = f"{PORTAL_URL}/sharing/rest/search"
    data = {
        "q": f'title:"{SERVICE_NAME}" type:"Feature Service" owner:{PORTAL_USER}',
        "num": 5,
        "token": token,
        "f": "json",
    }
    resp = requests.post(url, data=data, verify=False, timeout=30)
    result = resp.json()
    results = result.get("results", [])
    if results:
        item = results[0]
        print(f"  [OK] Found existing: {item['id']} - {item['url']}")
        return item["id"], item["url"]
    return None, None


def ensure_layer_definition(token, service_url, layer_def):
    """Check if layer has fields; if empty, add the layer definition."""
    # Check if layer 0 exists and has fields
    check_url = f"{service_url}/0?f=json&token={token}"
    try:
        resp = requests.get(check_url, verify=False, timeout=30)
        result = resp.json()
        fields = result.get("fields", [])
        if len(fields) > 2:  # More than just OBJECTID + GlobalID
            print(f"  [OK] Layer already has {len(fields)} fields, skipping addToDefinition")
            return True
    except Exception:
        pass  # Layer doesn't exist yet, need to add definition

    # Add the definition via internal admin URL
    admin_url = service_url.replace("/rest/services/", "/rest/admin/services/")
    admin_url = admin_url.replace(
        "http://apsdmagis.ap.gov.in/gisserver",
        "https://192.168.8.24:6443/arcgis"
    ).replace(
        "https://apsdmagis.ap.gov.in/gisserver",
        "https://192.168.8.24:6443/arcgis"
    )
    add_url = f"{admin_url}/addToDefinition"

    print(f"  Adding layer definition via: {add_url}")
    add_data = {
        "addToDefinition": json.dumps(layer_def),
        "token": token,
        "f": "json",
    }
    try:
        resp = requests.post(add_url, data=add_data, verify=False, timeout=120)
        result = resp.json()
        if result.get("success"):
            print(f"  [OK] Layer definition added successfully")
            return True
        else:
            print(f"  [WARN] addToDefinition response: {result}")
            return False
    except Exception as e:
        print(f"  [ERROR] addToDefinition failed: {e}")
        return False


def update_item_metadata(token, item_id):
    """Update item tags, description, and thumbnail."""
    url = f"{PORTAL_URL}/sharing/rest/content/users/{PORTAL_USER}/items/{item_id}/update"
    data = {
        "title": "DM Personnel Directory — Andhra Pradesh (NDMA-Aligned)",
        "tags": "Personnel, Directory, DM, APSDMA, NDMA, ESF, Hierarchy, Officials, Revenue, Police, SDRF, NDRF, Fire, Medical, Infrastructure, NGO, Survey123",
        "snippet": "NDMA-aligned disaster management personnel directory — 8 Sectors, 25 Categories, 16 ESFs across all 28 AP districts",
        "description": """<p><b>APSDMA Disaster Management Personnel Directory (NDMA-Aligned)</b></p>
<p>Comprehensive directory of all officials, staff, and organizations involved in
disaster management in Andhra Pradesh, structured per NDMA DM Act 2005, NDMP 2019,
and the 16 Emergency Support Functions (ESFs).</p>
<h4>8 Sectors &rarr; 25 Categories</h4>
<ol>
  <li><b>Executive &amp; Revenue Admin:</b> Revenue &amp; District Admin, Civil Defence, Home Guards</li>
  <li><b>Law Enforcement &amp; Security:</b> Police, Armed Forces</li>
  <li><b>Fire &amp; Rescue Forces:</b> Fire &amp; Emergency Services, SDRF, NDRF</li>
  <li><b>Health &amp; Medical:</b> Medical &amp; Public Health, Veterinary</li>
  <li><b>Infrastructure &amp; Utilities:</b> Irrigation, PWD, Power, Telecom, Transport, Municipal</li>
  <li><b>Rural &amp; Social Services:</b> Panchayat Raj, Food &amp; Civil Supplies, Education, Agriculture</li>
  <li><b>Youth &amp; Voluntary:</b> NCC, NGOs, Private Sector / CSR</li>
  <li><b>Information &amp; Coordination:</b> Media, APSDMA / DM Coordination</li>
</ol>
<h4>16 Emergency Support Functions (ESFs)</h4>
<p>Each personnel can be assigned to multiple ESFs with a primary ESF designation.</p>
<h4>5 View Modes</h4>
<ul>
  <li>Department View (Sector &rarr; Category &rarr; District)</li>
  <li>Geographic View (District &rarr; Mandal &rarr; Category)</li>
  <li>ESF View (ESF &rarr; Lead/Support &rarr; Personnel)</li>
  <li>Chain of Command (Category &rarr; Level &rarr; Personnel)</li>
  <li>Disaster Duty (Active assignments during events)</li>
</ul>
<p><b>Data Collection:</b> Survey123 forms filled by department heads</p>
<p><b>Visualization:</b> DM Personnel Web App with map, hierarchy tree &amp; 5 view modes</p>""",
        "accessInformation": "APSDMA GIS Cell",
        "licenseInfo": "Internal use only — APSDMA",
        "token": token,
        "f": "json",
    }
    resp = requests.post(url, data=data, verify=False, timeout=30)
    result = resp.json()
    if result.get("success"):
        print(f"  [OK] Metadata updated")
    else:
        print(f"  [WARN] Metadata update: {result}")


def share_with_org(token, item_id):
    """Share the feature service with the organization."""
    url = f"{PORTAL_URL}/sharing/rest/content/users/{PORTAL_USER}/items/{item_id}/share"
    data = {
        "everyone": "true",
        "org": "true",
        "groups": "",
        "token": token,
        "f": "json",
    }
    resp = requests.post(url, data=data, verify=False, timeout=30)
    result = resp.json()
    if result.get("itemId"):
        print(f"  [OK] Shared with organization and public")
    else:
        print(f"  [WARN] Share result: {result}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("=" * 70)
    print("  APSDMA DM PERSONNEL — FEATURE SERVICE PUBLISHER (NDMA-Aligned)")
    print("=" * 70)
    print(f"  Portal:     {PORTAL_URL}")
    print(f"  Service:    {SERVICE_NAME}")
    print(f"  Fields:     {len(FIELDS)}")
    print(f"  Categories: {len(CATEGORIES_25)} (8 sectors)")
    print(f"  ESFs:       16 (NDMP 2019)")
    print()

    # Step 1: Authenticate
    print("[1] Authenticating...")
    token = get_token()

    # Step 2: Create service
    print()
    print("[2] Creating Feature Service...")
    item_id, service_url = create_feature_service(token)

    if not item_id:
        print("  [ERROR] Could not create or find service. Exiting.")
        return

    # Step 2b: Ensure layer definition exists
    print()
    print("[2b] Ensuring layer definition...")
    layer_def = _build_layer_def()
    ensure_layer_definition(token, service_url, layer_def)

    # Step 3: Update metadata
    print()
    print("[3] Updating item metadata...")
    update_item_metadata(token, item_id)

    # Step 4: Share
    print()
    print("[4] Sharing with organization...")
    share_with_org(token, item_id)

    # Done
    print()
    print("=" * 70)
    print("  FEATURE SERVICE READY!")
    print("=" * 70)
    print()
    print(f"  Item ID:     {item_id}")
    print(f"  Service URL: {service_url}")
    print(f"  Portal Item: {PORTAL_URL}/home/item.html?id={item_id}")
    print(f"  REST API:    {service_url}/0")
    print()
    print("  NEXT STEPS:")
    print("  1. Run dm_personnel_add_esf_fields.py if upgrading from old schema")
    print("  2. Run generate_survey_xlsform.py to create Survey123 form (25 categories + ESFs)")
    print("  3. Open Survey123 Connect > New Survey > Link to this service")
    print("  4. Deploy the DM Personnel web app (all 5 view modes)")
    print()


if __name__ == "__main__":
    main()
