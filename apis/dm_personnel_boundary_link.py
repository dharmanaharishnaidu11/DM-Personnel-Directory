#!/usr/bin/env python3
"""
DM Personnel — Boundary Linkage
Spatially joins each person's GPS point to admin boundaries:
  - District (28) + LGD code + area
  - Mandal (688) + LGD code + revenue division
  - Village (18,392) + LGD code
  - Assembly constituency (175) + type
  - Parliament constituency (25)
  - Municipal/ULB boundary (112)
  - Gram Panchayat (14,216)

Also fixes mandal_name for persons who have GPS but no mandal via spatial lookup.

Run after sync_dm_personnel.py or standalone.
"""

import psycopg2
import logging
import sys

DB_HOST = "192.168.9.35"
DB_PORT = 5432
DB_NAME = "apsdma_2026"
DB_USER = "sde"
DB_PASS = "apsdma#123"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler()])
log = logging.getLogger("boundary_link")


def run():
    log.info("=" * 60)
    log.info("  DM PERSONNEL — BOUNDARY LINKAGE")
    log.info("=" * 60)

    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()

    # 1. Add new columns if they don't exist
    log.info("\n[1] Adding boundary columns to personnel.persons...")
    new_columns = [
        # District attributes
        ("district_area_sqm",       "DOUBLE PRECISION"),
        # Mandal attributes
        ("mandal_name_spatial",     "VARCHAR(100)"),
        ("mandal_lgd_spatial",      "INTEGER"),
        ("revenue_division",        "VARCHAR(100)"),
        # Village attributes
        ("village_name_spatial",    "VARCHAR(100)"),
        ("village_lgd",             "VARCHAR(20)"),
        # Assembly
        ("assembly_constituency",   "VARCHAR(100)"),
        ("assembly_const_no",       "VARCHAR(10)"),
        ("assembly_type",           "VARCHAR(10)"),
        # Parliament
        ("parliament_constituency", "VARCHAR(100)"),
        ("parliament_const_no",     "VARCHAR(10)"),
        # Municipal/ULB
        ("ulb_name",                "VARCHAR(100)"),
        ("ulb_code",                "VARCHAR(20)"),
        # Gram Panchayat
        ("gram_panchayat",          "VARCHAR(100)"),
        # Linkage metadata
        ("boundary_linked_at",      "TIMESTAMPTZ"),
    ]

    for col_name, col_type in new_columns:
        cur.execute(f"""
            DO $$ BEGIN
                ALTER TABLE personnel.persons ADD COLUMN IF NOT EXISTS {col_name} {col_type};
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """)
    conn.commit()
    log.info(f"    {len(new_columns)} boundary columns ensured")

    # Count persons with geometry
    cur.execute("SELECT COUNT(*) FROM personnel.persons WHERE geom IS NOT NULL")
    total_with_geom = cur.fetchone()[0]
    log.info(f"    Persons with GPS: {total_with_geom}")

    # 2. District spatial join
    log.info("\n[2] Linking districts (spatial join)...")
    cur.execute("""
        UPDATE personnel.persons p
        SET
            district_name = COALESCE(d.district_name, p.district_name),
            district_lgd = COALESCE(d.district_lgd::INTEGER, p.district_lgd),
            district_area_sqm = d.shape_area
        FROM admin.ap_districts_28 d
        WHERE p.geom IS NOT NULL
          AND ST_Within(p.geom, d.geom)
    """)
    district_linked = cur.rowcount
    conn.commit()
    log.info(f"    District linked: {district_linked} / {total_with_geom}")

    # 3. Mandal spatial join
    log.info("\n[3] Linking mandals (spatial join)...")
    cur.execute("""
        UPDATE personnel.persons p
        SET
            mandal_name_spatial = m.mandal_name,
            mandal_lgd_spatial = m.mandal_lgd,
            revenue_division = m.revenue_division,
            mandal_name = COALESCE(NULLIF(p.mandal_name, ''), m.mandal_name),
            mandal_lgd = COALESCE(p.mandal_lgd, m.mandal_lgd)
        FROM admin.ap_mandals_688 m
        WHERE p.geom IS NOT NULL
          AND ST_Within(p.geom, m.geom)
    """)
    mandal_linked = cur.rowcount
    conn.commit()
    log.info(f"    Mandal linked: {mandal_linked} / {total_with_geom}")

    # 4. Village spatial join
    log.info("\n[4] Linking villages (spatial join)...")
    cur.execute("""
        UPDATE personnel.persons p
        SET
            village_name_spatial = v.village,
            village_lgd = v.lgd_code_v,
            village_name = COALESCE(NULLIF(p.village_name, ''), v.village)
        FROM admin.ap_villages v
        WHERE p.geom IS NOT NULL
          AND ST_Within(p.geom, v.geom)
    """)
    village_linked = cur.rowcount
    conn.commit()
    log.info(f"    Village linked: {village_linked} / {total_with_geom}")

    # 5. Assembly constituency spatial join
    log.info("\n[5] Linking assembly constituencies...")
    cur.execute("""
        UPDATE personnel.persons p
        SET
            assembly_constituency = a.assembly_n,
            assembly_const_no = a.const_no,
            assembly_type = a.type
        FROM admin.ap_assembly a
        WHERE p.geom IS NOT NULL
          AND ST_Within(p.geom, a.geom)
    """)
    assembly_linked = cur.rowcount
    conn.commit()
    log.info(f"    Assembly linked: {assembly_linked} / {total_with_geom}")

    # 6. Parliament constituency spatial join
    log.info("\n[6] Linking parliament constituencies...")
    cur.execute("""
        UPDATE personnel.persons p
        SET
            parliament_constituency = pa.parliament,
            parliament_const_no = pa.parliament_no
        FROM admin.ap_parliament pa
        WHERE p.geom IS NOT NULL
          AND ST_Within(p.geom, pa.geom)
    """)
    parliament_linked = cur.rowcount
    conn.commit()
    log.info(f"    Parliament linked: {parliament_linked} / {total_with_geom}")

    # 7. Municipal/ULB spatial join
    log.info("\n[7] Linking municipal/ULB boundaries...")
    cur.execute("""
        UPDATE personnel.persons p
        SET
            ulb_name = u.tn_name,
            ulb_code = u.ulb_code
        FROM admin.ap_municipal_boundaries u
        WHERE p.geom IS NOT NULL
          AND ST_Within(p.geom, u.geom)
    """)
    ulb_linked = cur.rowcount
    conn.commit()
    log.info(f"    ULB linked: {ulb_linked} / {total_with_geom}")

    # 8. Gram Panchayat spatial join
    log.info("\n[8] Linking gram panchayats...")
    cur.execute("""
        UPDATE personnel.persons p
        SET
            gram_panchayat = gp.pname
        FROM admin.gram_panchayats gp
        WHERE p.geom IS NOT NULL
          AND ST_Within(p.geom, gp.geom)
    """)
    gp_linked = cur.rowcount
    conn.commit()
    log.info(f"    Gram Panchayat linked: {gp_linked} / {total_with_geom}")

    # 9. Mark linkage timestamp
    cur.execute("UPDATE personnel.persons SET boundary_linked_at = NOW() WHERE geom IS NOT NULL")
    conn.commit()

    # 10. Summary
    log.info("\n" + "=" * 60)
    log.info("  BOUNDARY LINKAGE SUMMARY")
    log.info("=" * 60)
    log.info(f"  Total persons with GPS : {total_with_geom}")
    log.info(f"  District linked        : {district_linked}")
    log.info(f"  Mandal linked          : {mandal_linked}")
    log.info(f"  Village linked         : {village_linked}")
    log.info(f"  Assembly linked        : {assembly_linked}")
    log.info(f"  Parliament linked      : {parliament_linked}")
    log.info(f"  Municipal/ULB linked   : {ulb_linked}")
    log.info(f"  Gram Panchayat linked  : {gp_linked}")

    # Show sample enriched record
    log.info("\n  SAMPLE ENRICHED RECORD:")
    cur.execute("""
        SELECT person_name, designation, district_name, district_lgd,
               mandal_name, revenue_division, village_name,
               assembly_constituency, parliament_constituency,
               ulb_name, gram_panchayat
        FROM personnel.persons
        WHERE mandal_name IS NOT NULL AND assembly_constituency IS NOT NULL
        LIMIT 3
    """)
    for row in cur.fetchall():
        log.info(f"    {row[0]} | {row[1]}")
        log.info(f"      District: {row[2]} (LGD {row[3]})")
        log.info(f"      Mandal: {row[4]} | RD: {row[5]}")
        log.info(f"      Village: {row[6]}")
        log.info(f"      Assembly: {row[7]} | Parliament: {row[8]}")
        log.info(f"      ULB: {row[9]} | GP: {row[10]}")
        log.info("")

    # District-wise completeness
    log.info("  DISTRICT-WISE BOUNDARY COMPLETENESS:")
    cur.execute("""
        SELECT
            COALESCE(district_name, '(State Level)') AS dist,
            COUNT(*) AS total,
            COUNT(mandal_name) AS has_mandal,
            COUNT(assembly_constituency) AS has_assembly,
            COUNT(parliament_constituency) AS has_parliament,
            COUNT(revenue_division) AS has_rd,
            COUNT(gram_panchayat) AS has_gp
        FROM personnel.persons
        GROUP BY district_name
        ORDER BY district_name NULLS LAST
    """)
    log.info(f"    {'District':35s} {'Total':>5s} {'Mandal':>7s} {'Assembly':>9s} {'Parl':>5s} {'RD':>4s} {'GP':>4s}")
    log.info(f"    {'-'*35} {'-'*5} {'-'*7} {'-'*9} {'-'*5} {'-'*4} {'-'*4}")
    for row in cur.fetchall():
        log.info(f"    {row[0]:35s} {row[1]:5d} {row[2]:7d} {row[3]:9d} {row[4]:5d} {row[5]:4d} {row[6]:4d}")

    conn.close()
    log.info("\n" + "=" * 60)
    log.info("  DONE")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
