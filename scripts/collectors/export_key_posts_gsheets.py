"""
Export AP District Key Posts data from Google Sheets API.
Source: https://kranthi0209.github.io/ap-district-key-posts/
Date: 2026-03-28
"""

import json
import csv
import os
import urllib.request
import urllib.parse
import ssl
import time

API_URL = "https://script.google.com/macros/s/AKfycbw8hUNLBqYi_3CHjcviIkIYe0ycvKnfUYkhsc9iqHW66Z6q9KkNyc9uqbAp9g0mupWM/exec"

OUT_DIR = os.path.join(os.path.dirname(__file__), "district_key_posts_export")

# District name mapping (district_id -> friendly name)
DISTRICT_NAMES = {
    "D01": "Alluri Sitha Ramaraju", "D02": "Anakapalli", "D03": "Anantapuramu",
    "D04": "Annamayya", "D05": "Bapatla", "D06": "Chittoor",
    "D07": "East Godavari", "D08": "Eluru", "D09": "Guntur",
    "D10": "Kadapa", "D11": "Kakinada", "D12": "Dr BR Ambedkar Konaseema",
    "D13": "Krishna", "D14": "Kurnool", "D15": "Parvathipuram Manyam",
    "D16": "Markapuram", "D17": "Nandyal", "D18": "SPSR Nellore",
    "D19": "NTR", "D20": "Palnadu", "D21": "Polavaram",
    "D22": "Prakasam", "D23": "Srikakulam", "D24": "Sri Sathya Sai",
    "D25": "Tirupati", "D26": "Visakhapatnam", "D27": "Vizianagaram",
    "D28": "West Godavari",
}


def fetch_json(url):
    """Fetch JSON from URL, following redirects."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "APSDMA-Export/1.0"})
    # Google Apps Script redirects; need to follow
    for _ in range(5):
        resp = urllib.request.urlopen(req, context=ctx, timeout=30)
        if resp.status in (301, 302, 307, 308):
            url = resp.headers["Location"]
            req = urllib.request.Request(url, headers={"User-Agent": "APSDMA-Export/1.0"})
        else:
            break
    return json.loads(resp.read().decode("utf-8"))


def export():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Output: {OUT_DIR}\n")

    # 1. Fetch summary
    print("Fetching summary...")
    try:
        summary = fetch_json(f"{API_URL}?action=getSummary")
        with open(os.path.join(OUT_DIR, "_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"  Summary: {len(summary) if isinstance(summary, list) else 'OK'}\n")
    except Exception as e:
        print(f"  Summary failed: {e}\n")
        summary = None

    # 2. Get actual sheet names from summary, then fetch each district
    all_records = []
    all_columns = set()

    if isinstance(summary, dict) and "summaries" in summary:
        sheets = summary["summaries"]
    else:
        sheets = []
        print("  WARNING: No summary data, cannot determine sheet names!")

    for entry in sheets:
        did = entry["district_id"]
        sheet_name = entry["sheet_name"]
        dname = DISTRICT_NAMES.get(did, did)
        total = entry.get("total", "?")
        gen = entry.get("gen_saved", 0)
        ei = entry.get("ei_saved", 0)

        print(f"  [{did}] {dname} (sheet={sheet_name}, {total} posts, {gen} gen, {ei} E&I)...",
              end=" ", flush=True)
        try:
            url = f"{API_URL}?action=getSheet&sheet={urllib.parse.quote(sheet_name)}"
            data = fetch_json(url)

            if isinstance(data, dict) and "data" in data:
                rows = data["data"]
            elif isinstance(data, list):
                rows = data
            else:
                rows = []

            # Add district info to each row
            for row in rows:
                row["_district_id"] = did
                row["_district_name"] = dname
                row["_sheet_name"] = sheet_name
                all_columns.update(row.keys())

            # Save per-district JSON
            with open(os.path.join(OUT_DIR, f"{did}_{dname.replace(' ', '_')}.json"),
                       "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

            all_records.extend(rows)
            print(f"{len(rows)} records")

        except Exception as e:
            print(f"ERROR: {e}")

        time.sleep(0.5)  # be polite to Google

    # 3. Save combined JSON
    combined_json = os.path.join(OUT_DIR, "_ALL_DISTRICTS.json")
    with open(combined_json, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)

    # 4. Save combined CSV
    if all_records:
        # Order columns sensibly
        priority = ["_district_id", "_district_name", "post_id", "department",
                     "post_name", "officer_name", "cfms_id", "contact",
                     "working_from", "native_district", "reg_fac", "is_vacant",
                     "no_post", "efficiency", "integrity", "general_saved",
                     "ei_saved", "last_updated"]
        cols = [c for c in priority if c in all_columns]
        cols += sorted(all_columns - set(cols))

        combined_csv = os.path.join(OUT_DIR, "_ALL_DISTRICTS.csv")
        with open(combined_csv, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(all_records)

    print(f"\n{'='*50}")
    print(f"Total: {len(all_records)} records from {len(sheets)} districts")
    print(f"JSON:  {combined_json}")
    if all_records:
        print(f"CSV:   {combined_csv}")
    print(f"{'='*50}")


if __name__ == "__main__":
    export()
