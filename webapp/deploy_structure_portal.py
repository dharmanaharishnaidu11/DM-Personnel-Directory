#!/usr/bin/env python3
"""
Deploy AP Government Structure Validation Portal to ArcGIS Portal

This script:
1. Copies structure_portal.html to IIS wwwroot directory
2. Registers it as a Web App item in the Portal
3. Shares with the organization

Author: APSDMA GIS Cell
Date:   2026-02-20
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
WEBAPP_PUBLIC_URL = "https://apsdmagis.ap.gov.in/dm_personnel/structure_portal.html"

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
        url2 = "https://apsdmagis.ap.gov.in/gisportal/sharing/rest/generateToken"
        resp = requests.post(url2, data=data, verify=False, timeout=30)
        result = resp.json()
    token = result.get("token")
    if not token:
        print(f"  Token error: {result.get('error', {}).get('message', 'Unknown')}")
    return token


def copy_to_webserver():
    """Copy structure_portal.html to IIS directory."""
    print("=" * 60)
    print("  DEPLOYING STRUCTURE PORTAL")
    print("=" * 60)

    src_file = os.path.join(WEBAPP_SOURCE, "structure_portal.html")
    if not os.path.exists(src_file):
        print(f"  ERROR: Source file not found: {src_file}")
        return None

    try:
        os.makedirs(SERVER_WEBAPPS_DIR, exist_ok=True)
        dst_file = os.path.join(SERVER_WEBAPPS_DIR, "structure_portal.html")
        shutil.copy2(src_file, dst_file)
        print(f"  Copied: structure_portal.html")
        print(f"  Target: {dst_file}")
        return dst_file
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

    urls = [
        f"{PORTAL_URL}/sharing/rest/content/users/{PORTAL_USER}/addItem",
        f"https://apsdmagis.ap.gov.in/gisportal/sharing/rest/content/users/{PORTAL_USER}/addItem",
    ]
    data = {
        "title": "AP Government Structure - Validation Portal",
        "type": "Web Mapping Application",
        "typeKeywords": "Web Mapping Application, Government, Structure, Validation, APSDMA, Portal",
        "description": """
            <p><b>AP Government Structure Validation Portal</b></p>
            <p>Interactive portal for departments to review and validate the government
            hierarchy structure data. Includes department tree with minister/secretary/HOD chains,
            correction submission, validation tracking, and export capabilities.</p>
            <h4>Features:</h4>
            <ul>
                <li>Collapsible department hierarchy tree (CM > Minister > Secretary > Dept > HODs/AOs)</li>
                <li>One-click department validation</li>
                <li>Correction submission form with review workflow</li>
                <li>Validation status dashboard with progress tracking</li>
                <li>CSV export for structure data, corrections, and summary</li>
            </ul>
            <h4>Data Coverage:</h4>
            <ul>
                <li>40 State Departments</li>
                <li>96 Heads of Department (HODs)</li>
                <li>238 Autonomous Organisations</li>
                <li>30 State Units</li>
                <li>Complete Minister > Secretary > HOD officer chains</li>
            </ul>
            <p><b>Source:</b> AP HRMS Code Book & Secretaries/HoD Lists (Dec 2025)</p>
        """,
        "tags": "Government, Structure, Validation, Departments, HOD, APSDMA, Andhra Pradesh",
        "snippet": "AP Government Structure Validation Portal - 40 departments, HODs, AOs with validation and correction workflow",
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
                print(
                    f"  Response: {result.get('error', {}).get('message', str(result)[:100])}"
                )
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
    print("  AP GOVT STRUCTURE VALIDATION PORTAL - DEPLOYMENT")
    print("=" * 60)
    print(f"  Source:  {WEBAPP_SOURCE}")
    print(f"  Target:  {SERVER_WEBAPPS_DIR}")
    print(f"  Portal:  {PORTAL_URL}")
    print()

    # Step 1: Copy files to IIS
    target = copy_to_webserver()
    if not target:
        print()
        print("  MANUAL DEPLOYMENT REQUIRED:")
        print("  " + "-" * 56)
        print(f"  1. Copy structure_portal.html from: {WEBAPP_SOURCE}")
        print(f"  2. To: {SERVER_WEBAPPS_DIR}")
        print(f"  3. Access via: {WEBAPP_PUBLIC_URL}")
        return

    # Step 2: Get token
    print()
    print("  Getting Portal token...")
    token = get_portal_token()
    if not token:
        print("  Could not authenticate. Register manually in Portal.")
        print(f"  File is deployed at: {WEBAPP_PUBLIC_URL}")
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
    if item_id:
        print(f"  Portal Item: {PORTAL_URL}/home/item.html?id={item_id}")
    print()
    print("  NEXT STEPS:")
    print("  " + "-" * 56)
    print("  1. Run: python apis/govt_structure_service.py")
    print("     > Creates the 2 Feature Services + seeds ~500 records")
    print("  2. Open: " + WEBAPP_PUBLIC_URL)
    print("  3. Login: CMO_Peshi / 202620252023")
    print("  4. Share link with departments for validation!")
    print()


if __name__ == "__main__":
    main()
