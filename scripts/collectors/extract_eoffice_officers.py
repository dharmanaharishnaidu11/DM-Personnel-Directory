"""
Extract unique officers from kranthi0209/eOffice.dashboard.ap GitHub repo.
Combines data from aggregate reports + individual officer JSON files.
"""
import json
import urllib.request
import time
import sys

REPO = "kranthi0209/eOffice.dashboard.ap"
BASE_RAW = f"https://raw.githubusercontent.com/{REPO}/main"
API_BASE = f"https://api.github.com/repos/{REPO}"

def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Python"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                print(f"  FAILED: {url} -> {e}")
                return None

def main():
    # 1. Get file tree
    print("Fetching repo file tree...")
    tree_data = fetch_json(f"{API_BASE}/git/trees/main?recursive=1")
    if not tree_data or "tree" not in tree_data:
        print("ERROR: Could not fetch repo tree")
        sys.exit(1)

    all_files = [item["path"] for item in tree_data["tree"]]
    json_files = [f for f in all_files if f.endswith(".json")]
    print(f"  Found {len(json_files)} JSON files in repo")

    # Identify aggregate reports vs individual officer files
    aggregate_reports = [f for f in json_files if "Report" in f or "Employee" in f]
    individual_files = [f for f in json_files if f not in aggregate_reports
                        and f != "settings.json" and not f.startswith(".")]

    print(f"  Aggregate reports: {aggregate_reports}")
    print(f"  Individual officer files: {len(individual_files)}")

    # 2. Fetch aggregate reports (these have Employee, Office_Type, Cadre_Type)
    officers = {}  # key: employee name -> record

    for report_file in aggregate_reports:
        print(f"\nFetching aggregate: {report_file}...")
        data = fetch_json(f"{BASE_RAW}/{report_file}")
        if not data:
            continue
        print(f"  {len(data)} records")

        for rec in data:
            name = rec.get("Employee", "").strip()
            if not name:
                continue

            cadre = rec.get("Cadre_Type") or ""
            office_type = rec.get("Office_Type") or ""

            # Use name as key; keep the record with most info
            if name not in officers:
                officers[name] = {
                    "person_name": name,
                    "designation": cadre.strip() if cadre else office_type.strip(),
                    "department": "",
                    "cadre_type": cadre.strip() if cadre else "",
                    "office_type": office_type.strip(),
                    "login_id": "",
                    "source": "eOffice.dashboard.ap"
                }
            else:
                # Update with richer data if available
                existing = officers[name]
                if cadre and not existing["cadre_type"]:
                    existing["cadre_type"] = cadre.strip()
                    existing["designation"] = cadre.strip()
                if office_type and not existing["office_type"]:
                    existing["office_type"] = office_type.strip()

    print(f"\nUnique officers from aggregate reports: {len(officers)}")

    # 3. Fetch individual officer files for department + post details
    print(f"\nFetching {len(individual_files)} individual officer files...")
    fetched = 0
    for i, fname in enumerate(individual_files):
        data = fetch_json(f"{BASE_RAW}/{fname}")
        if not data or not isinstance(data, list) or len(data) == 0:
            continue

        fetched += 1
        # Get first record for officer info
        rec = data[0]
        name = rec.get("holder", "").strip()
        if not name:
            continue

        post_name = str(rec.get("post_name", "") or "").strip()
        dept = str(rec.get("Dept", "") or "").strip()
        post_id = str(rec.get("holderPostId", "") or "").strip()

        # Collect all unique departments this officer appears in
        depts = set()
        posts = set()
        for r in data:
            d = str(r.get("Dept", "") or "").strip()
            p = str(r.get("post_name", "") or "").strip()
            if d: depts.add(d)
            if p: posts.add(p)

        # Use the most common department
        dept_str = "; ".join(sorted(depts)) if len(depts) <= 3 else dept
        post_str = post_name  # Use first record's post

        if name in officers:
            # Enrich existing record
            if dept_str and not officers[name]["department"]:
                officers[name]["department"] = dept_str
            if post_str and (not officers[name]["designation"] or officers[name]["designation"] == officers[name].get("office_type", "")):
                officers[name]["designation"] = post_str
            if post_id and not officers[name]["login_id"]:
                officers[name]["login_id"] = post_id
        else:
            officers[name] = {
                "person_name": name,
                "designation": post_str,
                "department": dept_str,
                "cadre_type": "",
                "office_type": "",
                "login_id": post_id,
                "source": "eOffice.dashboard.ap"
            }

        if (i + 1) % 25 == 0:
            print(f"  Processed {i+1}/{len(individual_files)} files...")

    print(f"  Fetched {fetched} individual files successfully")
    print(f"  Total unique officers: {len(officers)}")

    # 4. Clean up and format output
    output = []
    for name in sorted(officers.keys()):
        rec = officers[name]
        output.append({
            "person_name": rec["person_name"],
            "designation": rec["designation"],
            "department": rec["department"],
            "cadre_type": rec["cadre_type"],
            "office_type": rec.get("office_type", ""),
            "login_id": rec.get("login_id", ""),
            "source": rec["source"]
        })

    # 5. Save
    out_path = r"d:\APSDMA_MASTER_DATA\07_DATABASES\09_GO_Doccuments\district_key_posts_export\github_eoffice_officers.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(output)} officers to:\n  {out_path}")

    # Summary stats
    with_dept = sum(1 for r in output if r["department"])
    with_cadre = sum(1 for r in output if r["cadre_type"])
    with_login = sum(1 for r in output if r["login_id"])
    print(f"\n  With department: {with_dept}")
    print(f"  With cadre_type: {with_cadre}")
    print(f"  With login_id:   {with_login}")

    # Show a few samples
    print("\nSample records:")
    for r in output[:5]:
        print(f"  {r['person_name']} | {r['designation']} | {r['department'][:50]}")

if __name__ == "__main__":
    main()
