-- ============================================================================
-- DM Personnel Directory — PostgreSQL Schema
-- Schema: personnel
-- Tables: departments (40), hods (93), persons, sync_log
-- Views: v_dept_tree, v_district_summary
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS personnel;

-- ── Reference: 40 AP State Departments ──
CREATE TABLE IF NOT EXISTS personnel.departments (
    id              SERIAL PRIMARY KEY,
    dept_code       VARCHAR(10) NOT NULL UNIQUE,
    dept_name       VARCHAR(200) NOT NULL UNIQUE,
    sector_key      VARCHAR(30) NOT NULL,
    sector_label    VARCHAR(100) NOT NULL,
    sector_order    INTEGER NOT NULL,
    abbr            VARCHAR(10),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Reference: 93 HODs under departments ──
CREATE TABLE IF NOT EXISTS personnel.hods (
    id              SERIAL PRIMARY KEY,
    hod_name        VARCHAR(300) NOT NULL,
    dept_code       VARCHAR(10) NOT NULL REFERENCES personnel.departments(dept_code),
    display_order   INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(dept_code, hod_name)
);

-- ── Main: Personnel records ──
CREATE TABLE IF NOT EXISTS personnel.persons (
    id                      SERIAL PRIMARY KEY,
    -- Identity
    person_name             VARCHAR(200) NOT NULL,
    designation             VARCHAR(150) NOT NULL,
    employee_id             VARCHAR(50),
    date_of_birth           DATE,
    -- Department linkage
    dept_code               VARCHAR(10) REFERENCES personnel.departments(dept_code),
    sub_department          VARCHAR(100),
    category                VARCHAR(100),
    -- Hierarchy
    hierarchy_level         INTEGER NOT NULL CHECK (hierarchy_level BETWEEN 1 AND 6),
    -- Location (linked to admin schema by name)
    district_name           VARCHAR(100),
    district_lgd            INTEGER,
    mandal_name             VARCHAR(100),
    mandal_lgd              INTEGER,
    village_name            VARCHAR(100),
    jurisdiction_type       VARCHAR(20),
    office_address          TEXT,
    -- Reporting chain
    reports_to_id           INTEGER REFERENCES personnel.persons(id),
    reports_to_name         VARCHAR(200),
    reports_to_designation  VARCHAR(150),
    -- Posting
    parent_department       VARCHAR(200),
    posting_type            VARCHAR(50) DEFAULT 'Regular',
    rank_designation        VARCHAR(100),
    status                  VARCHAR(20) NOT NULL DEFAULT 'Active',
    date_of_posting         DATE,
    -- Contact
    phone_primary           VARCHAR(15),
    phone_alternate         VARCHAR(15),
    whatsapp_number         VARCHAR(15),
    email                   VARCHAR(100),
    office_phone            VARCHAR(20),
    office_phone_ext        VARCHAR(10),
    intercom_number         VARCHAR(20),
    fax_number              VARCHAR(20),
    residence_phone         VARCHAR(15),
    ham_radio_callsign      VARCHAR(20),
    residence_address       TEXT,
    -- ESF
    esf_primary             INTEGER,
    esf_assignments         VARCHAR(200),
    -- DM Role
    dm_role                 VARCHAR(100),
    dm_role_active          VARCHAR(10),
    dm_role_order_no        VARCHAR(200),
    dm_role_since           DATE,
    -- Disaster duty
    disaster_name           VARCHAR(200),
    disaster_type           VARCHAR(50),
    disaster_duty           VARCHAR(300),
    disaster_duty_location  VARCHAR(200),
    disaster_duty_status    VARCHAR(20),
    disaster_duty_start     DATE,
    disaster_duty_end       DATE,
    disaster_shift          VARCHAR(50),
    disaster_team           VARCHAR(100),
    -- Capabilities
    blood_group             VARCHAR(5),
    languages_spoken        VARCHAR(200),
    training_certifications TEXT,
    equipment_resources     TEXT,
    availability_24x7       VARCHAR(5),
    ngo_org_name            VARCHAR(200),
    specialization          VARCHAR(200),
    -- Spatial
    geom                    GEOMETRY(Point, 4326),
    -- Metadata
    photo_url               VARCHAR(500),
    remarks                 TEXT,
    arcgis_objectid         INTEGER UNIQUE,
    arcgis_globalid         VARCHAR(38) UNIQUE,
    entered_by              VARCHAR(100),
    date_of_entry           TIMESTAMPTZ,
    sync_updated_at         TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ── Sync log ──
CREATE TABLE IF NOT EXISTS personnel.sync_log (
    id                  SERIAL PRIMARY KEY,
    sync_type           VARCHAR(30) NOT NULL,
    started_at          TIMESTAMPTZ NOT NULL,
    finished_at         TIMESTAMPTZ,
    records_fetched     INTEGER DEFAULT 0,
    records_inserted    INTEGER DEFAULT 0,
    records_updated     INTEGER DEFAULT 0,
    records_normalized  INTEGER DEFAULT 0,
    errors              TEXT,
    status              VARCHAR(20) DEFAULT 'running'
);

-- ── Indexes ──
CREATE INDEX IF NOT EXISTS idx_persons_district ON personnel.persons(district_name);
CREATE INDEX IF NOT EXISTS idx_persons_dept ON personnel.persons(dept_code);
CREATE INDEX IF NOT EXISTS idx_persons_hierarchy ON personnel.persons(hierarchy_level);
CREATE INDEX IF NOT EXISTS idx_persons_status ON personnel.persons(status) WHERE status = 'Active';
CREATE INDEX IF NOT EXISTS idx_persons_geom ON personnel.persons USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_persons_arcgis_oid ON personnel.persons(arcgis_objectid);
CREATE INDEX IF NOT EXISTS idx_persons_name ON personnel.persons(person_name);
CREATE INDEX IF NOT EXISTS idx_persons_phone ON personnel.persons(phone_primary);

-- ── View: Department tree with counts ──
CREATE OR REPLACE VIEW personnel.v_dept_tree AS
SELECT
    d.sector_order,
    d.sector_label,
    d.sector_key,
    d.dept_code,
    d.dept_name,
    d.abbr,
    COUNT(DISTINCT p.id) AS person_count,
    COUNT(DISTINCT p.id) FILTER (WHERE p.status = 'Active') AS active_count,
    COUNT(DISTINCT p.district_name) AS district_count,
    ARRAY_AGG(DISTINCT h.hod_name ORDER BY h.hod_name) FILTER (WHERE h.hod_name IS NOT NULL) AS hods
FROM personnel.departments d
LEFT JOIN personnel.persons p ON p.dept_code = d.dept_code
LEFT JOIN personnel.hods h ON h.dept_code = d.dept_code
GROUP BY d.id, d.sector_order, d.sector_label, d.sector_key, d.dept_code, d.dept_name, d.abbr
ORDER BY d.sector_order, d.dept_name;

-- ── View: District summary ──
CREATE OR REPLACE VIEW personnel.v_district_summary AS
SELECT
    p.district_name,
    p.district_lgd,
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE p.status = 'Active') AS active,
    COUNT(*) FILTER (WHERE p.hierarchy_level <= 3) AS senior_officers,
    COUNT(DISTINCT p.dept_code) AS departments,
    COUNT(*) FILTER (WHERE p.dm_role IS NOT NULL AND p.dm_role != '') AS dm_roles,
    COUNT(*) FILTER (WHERE p.phone_primary IS NOT NULL) AS with_phone,
    COUNT(*) FILTER (WHERE p.email IS NOT NULL) AS with_email
FROM personnel.persons p
GROUP BY p.district_name, p.district_lgd
ORDER BY p.district_name;

-- ── Trigger: auto-update updated_at ──
CREATE OR REPLACE FUNCTION personnel.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_persons_updated ON personnel.persons;
CREATE TRIGGER trg_persons_updated
    BEFORE UPDATE ON personnel.persons
    FOR EACH ROW EXECUTE FUNCTION personnel.update_timestamp();
