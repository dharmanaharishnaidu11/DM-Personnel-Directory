"""
Fetch AP Ministers roster from GitHub repo kranthi0209/Ministers-e-Office
and save as structured JSON.
"""
import json
import urllib.request
import ssl

URL = "https://raw.githubusercontent.com/kranthi0209/Ministers-e-Office/main/data_ids.json"
OUTPUT = r"d:\APSDMA_MASTER_DATA\07_DATABASES\09_GO_Doccuments\district_key_posts_export\github_ministers_roster.json"

# Fetch
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print(f"Fetching {URL} ...")
with urllib.request.urlopen(URL, context=ctx) as resp:
    raw = resp.read().decode("utf-8")

data = json.loads(raw)
print(f"Downloaded {len(data)} entries")

# Extract unique ministers keyed by (name, login_id)
seen = set()
records = []
for entry in data:
    name = (entry.get("employee_name") or "").strip()
    post = (entry.get("post_name") or "").strip()
    dept = (entry.get("org_unit_name") or "").strip()
    login = (entry.get("login_id") or "").strip()

    key = (name, login)
    if not name or key in seen:
        continue
    seen.add(key)

    records.append({
        "person_name": name,
        "designation": post,
        "department": dept,
        "login_id": login,
        "source": "Ministers-e-Office"
    })

records.sort(key=lambda r: r["person_name"])

print(f"Unique ministers: {len(records)}")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"Saved to {OUTPUT}")

# Print first few
for r in records[:5]:
    print(f"  {r['person_name']} | {r['designation']} | {r['department']}")
if len(records) > 5:
    print(f"  ... and {len(records)-5} more")
