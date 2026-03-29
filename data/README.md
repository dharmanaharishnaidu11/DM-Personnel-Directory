# DM Personnel Directory — Data Sources & Consolidation

## Consolidated Master Directory

**Location**: `consolidated/`
**Generated**: 2026-03-29
**Total Records**: 7,115

| File | Description |
|------|-------------|
| `AP_DM_Master_Directory.csv` | Master CSV (22 columns, UTF-8 BOM for Excel) |
| `AP_DM_Master_Directory.json` | Master JSON |
| `by_district/` | 29 per-district CSVs (28 districts + State_Level) |
| `potential_duplicates.json` | 1,963 duplicate groups (same name + district across sources) |
| `_INDEX.json` | Generation metadata and stats |

### Columns

| Column | Description |
|--------|-------------|
| person_name | Officer name |
| designation | Post/rank title |
| department | Department name |
| category | Sector/category code |
| district | Canonical district name (28 official) |
| mandal | Mandal name (where available) |
| hierarchy_level | 0=Minister, 1=State, 2=HOD, 3=District Head, 4=Division, 5=Field |
| status | Active / Vacant / Transferred |
| phone | Primary phone (10-digit) |
| phone_alt | Alternate phone |
| whatsapp | WhatsApp number |
| email | Email address |
| employee_id | CFMS ID / Employee ID / eOffice login |
| posting_type | Regular / FAC / Attachment |
| rank | IAS / IPS / IFS / Minister etc. |
| dm_role | DM-specific role (Nodal Officer, SPOC, etc.) |
| reports_to | Reporting officer name |
| office_address | Office address |
| longitude, latitude | Point coordinates (WGS84) |
| source | Data source identifier |
| source_id | Original record ID in source |

## Data Sources (7)

### 1. GIS DM_Personnel Feature Service (3,549 records)
- **URL**: `https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/DM_Personnel/FeatureServer/0`
- **Type**: ArcGIS Hosted Feature Service
- **Coverage**: 28 districts + state level, 58 fields, point geometry
- **Entered by**: "AP 40-Dept Rebuild 2026" (1,604) + "DM Key Posts Import 2026-03-28" (2,048)
- **Sync**: `apis/sync_dm_personnel.py` (scheduled every 30 min)

### 2. GIS AP_Govt_Structure (56 records with officer names)
- **URL**: `https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/AP_Govt_Structure/FeatureServer/0`
- **Type**: ArcGIS Hosted Feature Service
- **Coverage**: 40 departments, 470 nodes (56 with officer names)

### 3. Key Posts Portal — Google Sheets (1,943 records)
- **URL**: https://kranthi0209.github.io/ap-district-key-posts/
- **Type**: Google Sheets via Google Apps Script
- **Coverage**: 28 districts, 15 departments, 372 unique posts
- **Fields**: Officer name, CFMS ID, phone, posting date, native district, Regular/FAC, Efficiency & Integrity ratings
- **API**: `https://script.google.com/macros/s/AKfycbw.../exec`
- **Admin**: ADMIN / Admin@AP2026

### 4. eOffice Dashboard (446 officers)
- **URL**: https://github.com/kranthi0209/eOffice.dashboard.ap
- **Type**: JSON files on GitHub
- **Coverage**: IAS/IPS/senior officers with designations, departments, cadre types
- **No contact info** (only eOffice login IDs)

### 5. Ministers Roster (25 ministers)
- **URL**: https://github.com/kranthi0209/Ministers-e-Office
- **Type**: JSON on GitHub
- **Coverage**: CM + 24 Ministers with department portfolios, eOffice login IDs

### 6. Local Excel Contact Files (1,096 records)
- `00_COMMAND_CENTER/SEOC_Dashboard/26 Districts contacts.xlsx` (1,006 records)
- `01_ADMINISTRATION/.../All District contacts.xlsx` (192 records)
- `01_ADMINISTRATION/.../Collecters contact list.xlsx` (26 records)
- `01_ADMINISTRATION/.../ALL Collectors, JCs, DRO, RTGS... Contact Numbers.xlsx` (133 records)

### 7. AP Government Department Hierarchy (reference)
- **File**: `AP_Government_Department_Hierarchy.md` (repo root)
- **Coverage**: 191 HODs, 40 departments, HOD-to-Village hierarchy for 34 departments
- **Source**: goir.ap.gov.in, apfinance.gov.in

## Contact Coverage

| Metric | Count | % |
|--------|-------|---|
| With phone | 6,267 | 88% |
| With email | 2,283 | 32% |
| With CFMS/employee ID | 4,385 | 62% |

## Related Repos

| Repo | Purpose |
|------|---------|
| [kranthi0209/ap-district-key-posts](https://github.com/kranthi0209/ap-district-key-posts) | District key posts data collection portal |
| [kranthi0209/eOffice.dashboard.ap](https://github.com/kranthi0209/eOffice.dashboard.ap) | eOffice KPI dashboard (IAS officers) |
| [kranthi0209/Ministers-e-Office](https://github.com/kranthi0209/Ministers-e-Office) | Ministers file-tracking dashboard |
| [kranthi0209/Ravi-Sir-Dashboard](https://github.com/kranthi0209/Ravi-Sir-Dashboard) | IAS officer personal dashboard (links hub) |
| [kranthi0209/esr-skills](https://github.com/kranthi0209/esr-skills) | ESR skills capture form (UI only, no data) |

## Refresh

To re-pull all sources and rebuild the consolidated directory:

```bash
# 1. Export from Key Posts Google Sheets
python ../07_DATABASES/09_GO_Doccuments/export_district_key_posts.py

# 2. Dump GIS Feature Services + other sources
python ../07_DATABASES/09_GO_Doccuments/import_key_posts_to_dm.py  # if needed

# 3. Consolidate all sources
python ../07_DATABASES/09_GO_Doccuments/consolidate_dm_directory.py

# 4. Sync to PostgreSQL (personnel schema)
python apis/dm_personnel_db_setup.py   # first time only
python apis/sync_dm_personnel.py       # scheduled sync
```
