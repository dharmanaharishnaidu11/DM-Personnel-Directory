#!/usr/bin/env python3
"""
DM Personnel Directory — Database Setup
Creates personnel schema, seeds 40 departments + 93 HODs.
Run once, idempotent (safe to re-run).
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values

DB_HOST = "192.168.9.35"
DB_PORT = 5432
DB_NAME = "apsdma_2026"
DB_USER = "sde"
DB_PASS = "apsdma#123"

# ══════════════════════════════════════════════════════════════════
# 10 Sectors
# ══════════════════════════════════════════════════════════════════
SECTORS = {
    "core_governance":  {"label": "Core Governance & Administration",       "order": 1},
    "finance_planning": {"label": "Finance & Planning",                     "order": 2},
    "revenue_dm":       {"label": "Revenue & Disaster Management",          "order": 3},
    "home_security":    {"label": "Home, Law & Security",                   "order": 4},
    "health_medical":   {"label": "Health, Medical & Family Welfare",       "order": 5},
    "education_skills": {"label": "Education & Skill Development",          "order": 6},
    "agriculture_env":  {"label": "Agriculture, Environment & Water",       "order": 7},
    "infrastructure":   {"label": "Infrastructure, Industry & Urban Dev",   "order": 8},
    "rural_panchayat":  {"label": "Panchayat Raj & Rural Development",      "order": 9},
    "social_welfare":   {"label": "Social Welfare & Empowerment",           "order": 10},
}

# ══════════════════════════════════════════════════════════════════
# 40 AP State Departments (from codes.ap.gov.in)
# ══════════════════════════════════════════════════════════════════
AP_DEPARTMENTS = [
    # (dept_code, dept_name, sector_key, abbr)
    # Core Governance (7)
    ("CAB01", "Chief Ministers Office",          "core_governance",  "CAB"),
    ("CSO01", "Chief Secretarys Office",         "core_governance",  "CSO"),
    ("GAD01", "General Administration",          "core_governance",  "GAD"),
    ("GAD07", "Governors Secretariat",           "core_governance",  "RJB"),
    ("GAD16", "Chief Electoral Officer",         "core_governance",  "CEO"),
    ("LEG01", "Legislature",                     "core_governance",  "LEG"),
    ("RTG01", "Real Time Governance",            "core_governance",  "RTG"),
    # Finance (3)
    ("FIN01", "Finance",                         "finance_planning", "FIN"),
    ("PLG01", "Planning",                        "finance_planning", "PLG"),
    ("PBE01", "Public Enterprises",              "finance_planning", "PBE"),
    # Revenue & DM (2)
    ("REV01", "Revenue",                         "revenue_dm",       "REV"),
    ("RDM01", "Disaster Management",             "revenue_dm",       "RDM"),
    # Home (2)
    ("HOM01", "Home",                            "home_security",    "HOM"),
    ("LAW01", "Law",                             "home_security",    "LAW"),
    # Health (1)
    ("HMF01", "Health, Medical & Family Welfare","health_medical",   "HMF"),
    # Education (3)
    ("EHE01", "Human Resources (Higher Education)",   "education_skills", "EHE"),
    ("ESE01", "Human Resources (School Education)",   "education_skills", "ESE"),
    ("SEI01", "Dept of Skills Development and Training","education_skills","SEI"),
    # Agriculture (4)
    ("AGC01", "Agriculture and Marketing",       "agriculture_env",  "AGC"),
    ("AHF01", "Animal Husbandry, Dairy Dev and Fisheries","agriculture_env","AHF"),
    ("EFS01", "Environment, Forest, Science and Technology","agriculture_env","EFS"),
    ("ICD01", "Water Resources",                 "agriculture_env",  "ICD"),
    # Infrastructure (9)
    ("ENE01", "Energy",                          "infrastructure",   "ENE"),
    ("TRB01", "Transport, Roads and Buildings",  "infrastructure",   "TRB"),
    ("MAU01", "Municipal Administration and Urban Development","infrastructure","MAU"),
    ("HOU01", "Housing",                         "infrastructure",   "HOU"),
    ("INC01", "Industries and Commerce",         "infrastructure",   "INC"),
    ("INI01", "Infrastructure and Investment",   "infrastructure",   "INI"),
    ("ITC01", "IT, Electronics and Communications","infrastructure", "ITC"),
    ("FCS01", "Consumer Affairs, Food and Civil Supplies","infrastructure","FCS"),
    ("LAE01", "Labour and Employment",           "infrastructure",   "LAE"),
    # Panchayat Raj (2)
    ("PRR01", "Panchayat Raj and Rural Development","rural_panchayat","PRR"),
    ("GWS01", "Gram/Ward Volunteers and Village/Ward Secretariats","rural_panchayat","GWS"),
    # Social Welfare (7)
    ("SOW01", "Social Welfare",                  "social_welfare",   "SOW"),
    ("BCW01", "Backward Classes Welfare",        "social_welfare",   "BCW"),
    ("MNW01", "Minorities Welfare",              "social_welfare",   "MNW"),
    ("TBW01", "Dept of Tribal Welfare",          "social_welfare",   "TBW"),
    ("EWS01", "Dept of Economically Weaker Sections Welfare","social_welfare","EWS"),
    ("WDC01", "Women, Children, Disabled and Senior Citizens","social_welfare","WDC"),
    ("YTC01", "Youth Advancement, Tourism and Culture","social_welfare","YTC"),
]

# ══════════════════════════════════════════════════════════════════
# 93 HODs per department code
# ══════════════════════════════════════════════════════════════════
AP_HODS = {
    "AGC01": ["Agriculture", "Horticulture", "Sericulture", "Marketing", "Cooperation and Cooperative Societies"],
    "AHF01": ["Animal Husbandry", "Fisheries"],
    "BCW01": ["BC Welfare"],
    "EFS01": ["Forest (PCCF)"],
    "EHE01": ["Collegiate Education", "State Archives", "Oriental Manuscripts", "National Cadet Corps"],
    "ENE01": ["Electrical Safety"],
    "ESE01": ["School Education", "Intermediate Education", "Publication", "Adult Education", "Public Libraries"],
    "FCS01": ["Civil Supplies", "Legal Metrology"],
    "FIN01": ["Treasuries & Accounts", "State Audit", "Government Life Insurance", "Pay and Accounts Office", "Works Accounts", "AP State Directorate of Revenue Intelligence"],
    "GAD01": ["Information and Public Relations", "Anti Corruption Bureau", "Protocol", "Vigilance and Enforcement", "AP Bhavan New Delhi", "Translations", "Special Enforcement Bureau"],
    "GWS01": ["Gram Volunteers / Ward Volunteers"],
    "HMF01": ["Medical Education", "Public Health", "Family Welfare", "IPM & Food Safety", "Ayush", "Drugs Control", "Directorate of Secondary Health"],
    "HOM01": ["Police (DGP)", "Prisons & Correctional Services", "Printing and Stationery", "Fire Services", "Sainik Welfare", "Special Protection Force", "EAGLE Anti-Narcotics", "Prosecutions"],
    "ICD01": ["CADA", "Ground Water", "Water Resources (E-in-C)", "Resettlement and Rehabilitation"],
    "INC01": ["Industries, Commerce and Export Promotion", "Handlooms & Textiles", "Mines and Geology", "Sugar and Cane"],
    "INI01": ["State Ports"],
    "ITC01": ["Electronics Delivery Services"],
    "LAE01": ["Labour", "Factories", "Insurance Medical Services", "Boilers"],
    "MAU01": ["Municipal Administration", "Town and Country Planning", "Public Health Engineering"],
    "MNW01": ["AP State Minorities Commission", "Minorities Welfare"],
    "PLG01": ["Economics and Statistics"],
    "PRR01": ["Panchayati Raj", "Panchayati Raj Engineering", "Rural Development", "Rural Water Supply Engineering"],
    "REV01": ["Revenue (CCLA)", "Commercial Taxes", "Prohibition and Excise", "Survey Settlements and Land Records", "Endowment", "Registration and Stamps"],
    "SEI01": ["Technical Education", "Employment and Training"],
    "SOW01": ["Social Welfare"],
    "TBW01": ["Tribal Welfare", "Tribal Welfare Engineering"],
    "TRB01": ["Roads and Buildings (E-in-C)", "Transport", "Public Transport Department"],
    "WDC01": ["Women Development and Child Welfare", "Differently Abled, Senior Citizens & Transgender", "Juvenile Welfare & Correctional Services"],
    "YTC01": ["Youth Services", "Archaeology and Museums"],
}

# Category name → dept_code mapping
CATEGORY_TO_CODE = {d[1]: d[0] for d in AP_DEPARTMENTS}

# Legacy NDMA → AP department name
NDMA_TO_AP = {
    "Revenue & District Administration": "Revenue",
    "Police": "Home",
    "Fire & Emergency Services": "Home",
    "Medical & Public Health": "Health, Medical & Family Welfare",
    "SDRF": "Home",
    "NDRF": "Home",
    "Civil Defence": "Home",
    "Home Guards": "Home",
    "Armed Forces": "Home",
    "Irrigation & Water Resources": "Water Resources",
    "Municipal & Urban Development": "Municipal Administration and Urban Development",
    "Power / Electricity": "Energy",
    "Transport": "Transport, Roads and Buildings",
    "Public Works / R&B": "Transport, Roads and Buildings",
    "Telecom & Communications": "IT, Electronics and Communications",
    "Panchayat Raj & Rural Development": "Panchayat Raj and Rural Development",
    "Food & Civil Supplies": "Consumer Affairs, Food and Civil Supplies",
    "Education": "Human Resources (School Education)",
    "Agriculture & Fisheries": "Agriculture and Marketing",
    "Veterinary & Animal Husbandry": "Animal Husbandry, Dairy Dev and Fisheries",
    "NCC / Youth Organizations": "Youth Advancement, Tourism and Culture",
    "NGOs & Volunteer Organizations": "Disaster Management",
    "Private Sector / CSR": "Industries and Commerce",
    "Media & Public Information": "General Administration",
    "APSDMA / DM Coordination": "Disaster Management",
}


def migrate_category(cat):
    """Map any category name → canonical AP department name."""
    if not cat:
        return "General Administration"
    if cat in CATEGORY_TO_CODE:
        return cat
    if cat in NDMA_TO_AP:
        return NDMA_TO_AP[cat]
    # Fuzzy: check if input is substring of a known name or vice versa
    cat_lower = cat.lower()
    for name in CATEGORY_TO_CODE:
        if cat_lower in name.lower() or name.lower() in cat_lower:
            return name
    return "General Administration"


def get_dept_code(category_name):
    """Get dept_code for a category name."""
    canonical = migrate_category(category_name)
    return CATEGORY_TO_CODE.get(canonical)


def setup():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    conn.autocommit = False
    cur = conn.cursor()

    print("=" * 60)
    print("  DM PERSONNEL — DATABASE SETUP")
    print("=" * 60)

    # 1. Run schema migration SQL
    sql_path = os.path.join(os.path.dirname(__file__), "dm_personnel_schema_migration.sql")
    print(f"\n[1] Running schema migration: {sql_path}")
    with open(sql_path, "r") as f:
        sql = f.read()
    cur.execute(sql)
    conn.commit()
    print("    Schema created OK")

    # 2. Seed departments
    print(f"\n[2] Seeding {len(AP_DEPARTMENTS)} departments...")
    for dept_code, dept_name, sector_key, abbr in AP_DEPARTMENTS:
        sec = SECTORS[sector_key]
        cur.execute("""
            INSERT INTO personnel.departments (dept_code, dept_name, sector_key, sector_label, sector_order, abbr)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (dept_code) DO UPDATE SET
                dept_name = EXCLUDED.dept_name,
                sector_key = EXCLUDED.sector_key,
                sector_label = EXCLUDED.sector_label,
                sector_order = EXCLUDED.sector_order,
                abbr = EXCLUDED.abbr
        """, (dept_code, dept_name, sector_key, sec["label"], sec["order"], abbr))
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM personnel.departments")
    print(f"    Departments: {cur.fetchone()[0]}")

    # 3. Seed HODs
    hod_count = 0
    for dept_code, hods in AP_HODS.items():
        for i, hod_name in enumerate(hods):
            cur.execute("""
                INSERT INTO personnel.hods (hod_name, dept_code, display_order)
                VALUES (%s, %s, %s)
                ON CONFLICT (dept_code, hod_name) DO UPDATE SET
                    display_order = EXCLUDED.display_order
            """, (hod_name, dept_code, i + 1))
            hod_count += 1
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM personnel.hods")
    print(f"\n[3] HODs seeded: {cur.fetchone()[0]}")

    # 4. Verify
    print(f"\n[4] Verification:")
    cur.execute("SELECT COUNT(*) FROM personnel.departments WHERE is_active")
    print(f"    Active departments: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM personnel.hods WHERE is_active")
    print(f"    Active HODs: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM personnel.persons")
    print(f"    Persons: {cur.fetchone()[0]} (will be populated by sync)")

    # Show tree summary
    print(f"\n[5] Department tree:")
    cur.execute("""
        SELECT d.sector_label, d.dept_name, d.abbr, COUNT(h.id) AS hod_count
        FROM personnel.departments d
        LEFT JOIN personnel.hods h ON h.dept_code = d.dept_code
        GROUP BY d.sector_order, d.sector_label, d.dept_name, d.abbr
        ORDER BY d.sector_order, d.dept_name
    """)
    last_sector = None
    for row in cur.fetchall():
        if row[0] != last_sector:
            last_sector = row[0]
            print(f"\n    [{last_sector}]")
        print(f"      [{row[2]}] {row[1]} ({row[3]} HODs)")

    conn.close()
    print(f"\n{'=' * 60}")
    print("  SETUP COMPLETE")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    setup()
