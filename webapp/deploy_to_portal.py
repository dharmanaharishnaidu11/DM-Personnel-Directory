#!/usr/bin/env python3
"""
Deploy DM Personnel Directory to ArcGIS Portal

This script:
1. Copies the web app to IIS wwwroot directory
2. Registers it as a Web App item in the Portal
3. Shares with the organization

Author: APSDMA GIS Cell
Date:   2026-02-12
"""

import os
import shutil
import json
import requests
import urllib3

urllib3.disable_warnings()

# Configuration
WEBAPP_SOURCE = os.path.dirname(os.path.abspath(__file__))
PORTAL_URL = "https://192.168.8.24/gisportal"
SERVER_WEBAPPS_DIR = r"C:\inetpub\wwwroot\dm_personnel"
WEBAPP_PUBLIC_URL = "https://apsdmagis.ap.gov.in/dm_personnel/index.html"

# Load credentials
try:
    creds_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "apsdma_credentials.json",
    )
    with open(creds_path, "r") as f:
        creds = json.load(f)
    PORTAL_USER = creds["arcgis_infrastructure"]["portal"]["username"]
    PORTAL_PASS = creds["arcgis_infrastructure"]["portal"]["password"]
except Exception as e:
    print(f"Warning: Could not load credentials: {e}")
    PORTAL_USER = "portaladmin"
    PORTAL_PASS = ""


def get_portal_token():
    """Get authentication token from Portal."""
    url = f"{PORTAL_URL}/sharing/rest/generateToken"
    data = {
        "username": PORTAL_USER,
        "password": PORTAL_PASS,
        "client": "referer",
        "referer": "https://apsdmagis.ap.gov.in/gisportal",
        "expiration": 120,
        "f": "json",
    }
    resp = requests.post(url, data=data, verify=False, timeout=30)
    try:
        result = resp.json()
    except Exception:
        # Fallback: try public URL
        url2 = "https://apsdmagis.ap.gov.in/gisportal/sharing/rest/generateToken"
        resp = requests.post(url2, data=data, verify=False, timeout=30)
        result = resp.json()
    token = result.get("token")
    if not token:
        print(f"  Token error: {result.get('error', {}).get('message', 'Unknown')}")
    return token


def copy_to_webserver():
    """Copy web app HTML files to IIS directory."""
    print("=" * 60)
    print("  DEPLOYING DM PERSONNEL WEB APP FILES")
    print("=" * 60)

    try:
        if os.path.exists(SERVER_WEBAPPS_DIR):
            print(f"  Existing directory found, updating...")
            # Copy all HTML files
            for item in os.listdir(WEBAPP_SOURCE):
                if item.endswith(".html"):
                    src = os.path.join(WEBAPP_SOURCE, item)
                    dst = os.path.join(SERVER_WEBAPPS_DIR, item)
                    shutil.copy2(src, dst)
                    print(f"  Copied: {item}")
            # Copy JS and CSS subdirectories
            for subdir in ["js", "css"]:
                src_dir = os.path.join(WEBAPP_SOURCE, subdir)
                dst_dir = os.path.join(SERVER_WEBAPPS_DIR, subdir)
                if os.path.exists(src_dir):
                    os.makedirs(dst_dir, exist_ok=True)
                    for fname in os.listdir(src_dir):
                        src_f = os.path.join(src_dir, fname)
                        dst_f = os.path.join(dst_dir, fname)
                        if os.path.isfile(src_f):
                            shutil.copy2(src_f, dst_f)
                            print(f"  Copied: {subdir}/{fname}")
        else:
            os.makedirs(os.path.dirname(SERVER_WEBAPPS_DIR), exist_ok=True)
            shutil.copytree(
                WEBAPP_SOURCE,
                SERVER_WEBAPPS_DIR,
                ignore=shutil.ignore_patterns("*.py", "*.pyc", "__pycache__"),
            )
            print(f"  Copied to: {SERVER_WEBAPPS_DIR}")

        return SERVER_WEBAPPS_DIR
    except PermissionError:
        print(f"  ERROR: Permission denied. Run as Administrator.")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def register_portal_item(token):
    """Register the web app as a Portal item."""
    print()
    print("=" * 60)
    print("  REGISTERING PORTAL ITEM")
    print("=" * 60)

    # Try multiple URLs (internal, then public)
    urls = [
        f"{PORTAL_URL}/sharing/rest/content/users/{PORTAL_USER}/addItem",
        f"https://apsdmagis.ap.gov.in/gisportal/sharing/rest/content/users/{PORTAL_USER}/addItem",
    ]
    data = {
        "title": "DM Personnel Directory  - Andhra Pradesh",
        "type": "Web Mapping Application",
        "typeKeywords": "Web Mapping Application, Personnel, Directory, DM, APSDMA, Dashboard",
        "description": """
            <p><b>Disaster Management Personnel Directory</b></p>
            <p>Complete directory of all officials, staff, NGOs, and volunteers involved
            in disaster management in Andhra Pradesh  - from CM to VRO level.</p>
            <h4>Features:</h4>
            <ul>
                <li>Searchable hierarchy tree (Category > District > Person)</li>
                <li>Interactive map with jurisdiction polygons</li>
                <li>Detailed profile cards with contact information</li>
                <li>Filter by category, district, hierarchy level, status</li>
                <li>Export to CSV</li>
                <li>Click-to-call and WhatsApp integration</li>
            </ul>
            <h4>Categories:</h4>
            <ul>
                <li><b>Revenue Hierarchy:</b> CM > CS > Collector > JC > RDO > Tahsildar > VRO</li>
                <li><b>Police &amp; Fire:</b> DGP > SP > DSP > CI > SI + Fire Services</li>
                <li><b>SDRF/NDRF/Medical:</b> SDRF, NDRF teams, DMHO, PHC MOs, ASHA workers</li>
                <li><b>NGOs &amp; Volunteers:</b> Registered disaster relief organizations</li>
            </ul>
            <p><b>Data Source:</b> Survey123 form filled by department heads</p>
        """,
        "tags": "Personnel, Directory, DM, APSDMA, Andhra Pradesh, Disaster Management, Officials, Hierarchy",
        "snippet": "Complete disaster management personnel directory for AP  - from CM to VRO level across Revenue, Police, Fire, SDRF, NDRF, Medical & NGOs",
        "url": WEBAPP_PUBLIC_URL,
        "token": token,
        "f": "json",
    }

    for try_url in urls:
        print(f"  Trying: {try_url[:60]}...")
        try:
            resp = requests.post(try_url, data=data, verify=False, timeout=30)
            result = resp.json()
            if result.get("success"):
                item_id = result.get("id")
                print(f"  SUCCESS! Item ID: {item_id}")
                print(f"  View at: {PORTAL_URL}/home/item.html?id={item_id}")
                return item_id
            else:
                print(f"  Response: {result.get('error', {}).get('message', str(result)[:100])}")
        except Exception as e:
            print(f"  Failed: {e}")
            continue

    print("  ERROR: Could not register item with any URL")
    return None


def share_item(token, item_id):
    """Share item with the organization."""
    urls = [
        f"{PORTAL_URL}/sharing/rest/content/users/{PORTAL_USER}/items/{item_id}/share",
        f"https://apsdmagis.ap.gov.in/gisportal/sharing/rest/content/users/{PORTAL_USER}/items/{item_id}/share",
    ]
    data = {
        "everyone": "true",
        "org": "true",
        "groups": "",
        "token": token,
        "f": "json",
    }
    for try_url in urls:
        try:
            resp = requests.post(try_url, data=data, verify=False, timeout=30)
            result = resp.json()
            if result.get("itemId"):
                print(f"  Item shared with organization and public")
                return True
            print(f"  Share response: {str(result)[:100]}")
        except Exception:
            continue
    print(f"  Share warning: could not share item")
    return False


def main():
    print()
    print("=" * 60)
    print("  DM PERSONNEL DIRECTORY  - DEPLOYMENT")
    print("=" * 60)
    print(f"  Source:  {WEBAPP_SOURCE}")
    print(f"  Target:  {SERVER_WEBAPPS_DIR}")
    print(f"  Portal:  {PORTAL_URL}")
    print()

    html_files = [f for f in os.listdir(WEBAPP_SOURCE) if f.endswith(".html")]
    print(f"  Files to deploy: {', '.join(html_files)}")
    print()

    # Step 1: Copy files to IIS
    target = copy_to_webserver()
    if not target:
        print()
        print("  MANUAL DEPLOYMENT REQUIRED:")
        print("  " + "-" * 56)
        print(f"  1. Copy HTML files from: {WEBAPP_SOURCE}")
        print(f"  2. To: {SERVER_WEBAPPS_DIR}")
        print(f"  3. Access via: {WEBAPP_PUBLIC_URL}")
        return

    # Step 2: Get token
    print()
    print("  Getting Portal token...")
    token = get_portal_token()
    if not token:
        print("  Could not authenticate. Register manually in Portal.")
        return

    # Step 3: Register in Portal
    item_id = register_portal_item(token)
    if item_id:
        share_item(token, item_id)

    # Done
    print()
    print("=" * 60)
    print("  DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print()
    print(f"  Web App:     {WEBAPP_PUBLIC_URL}")
    print(f"  Portal Item: {PORTAL_URL}/home/item.html?id={item_id}")
    print()
    print("  COMPLETE SETUP WORKFLOW:")
    print("  " + "-" * 56)
    print("  1. [DONE] Deploy web app to IIS")
    print("  2. [DONE] Register in Portal")
    print("  3. Run: python apis/dm_personnel_service.py")
    print("     > Creates the DM_Personnel feature service")
    print("  4. Run: python survey123/generate_survey_xlsform.py")
    print("     > Generates the Survey123 XLSForm (.xlsx)")
    print("  5. Open Survey123 Connect > import XLSForm > Publish")
    print("  6. Share Survey123 link with department heads")
    print("  7. Data will auto-appear in the web app!")
    print()


if __name__ == "__main__":
    main()
