/* ==========================================================================
   DM Personnel Directory — Master Configuration
   Single source of truth: AP State Departments, hierarchy, colors, URLs
   Department structure: codes.ap.gov.in (40 SDs, 93 HODs, 10 Groups)
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.config = {
    // ArcGIS Portal & Server
    PORTAL_URL: "https://apsdmagis.ap.gov.in/gisportal",
    SERVER_URL: "https://apsdmagis.ap.gov.in/gisserver/rest/services",
    PERSONNEL_URL: "https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/DM_Personnel/FeatureServer/0",
    // NP_Admin FeatureServer — latest boundaries from VM2 DB (admin schema)
    ADMIN_BASE_URL: "https://apsdmagis.ap.gov.in/gisserver/rest/services/Hosted/NP_Admin/FeatureServer",
    ADMIN_LAYERS: {
        // ── Core boundaries (always loaded) ──
        state:              14,  // ap_state (1 polygon)
        district:            7,  // ap_districts_go2025 (28)
        mandal:              8,  // ap_mandals_go2025 (688)
        village:            15,  // ap_villages (18,392)
        // ── Points ──
        district_hqs:        0,  // ap_district_hqs (28 points)
        mandal_hqs:          1,  // ap_mandal_hqs (688 points)
        // ── Political boundaries ──
        assembly:            6,  // ap_assembly (175 constituencies)
        parliament:         11,  // ap_parliament (25 constituencies)
        // ── Administrative ──
        revenue_division:   12,  // ap_revenue_divisions (82)
        municipal:           9,  // ap_municipal_boundaries (112 ULBs)
        municipal_2025:     10,  // ap_municipal_boundaries_2025 (7 new ULBs)
        // ── Rural ──
        gram_panchayat:     19,  // gram_panchayats (14,216)
        settlement:         13,  // ap_settlements (372)
        ward:               16,  // ap_ward_boundaries (2,532)
        ward_secretariat:   23,  // ward_secretariats_urban (973)
        // ── India ──
        india_states:       21   // india_states (41)
    },

    // Map defaults
    AP_CENTER: [80.0, 16.0],
    AP_ZOOM: 7,
    MIN_ZOOM: 6,
    MAX_ZOOM: 18,

    TOKEN_REFRESH_MS: 5400000,  // 90 min
    MAX_RECORDS: 10000
};

// ══════════════════════════════════════════════════════════════════════════
// 10 Department Groups
// These are logical groupings of the 40 AP State Departments for UI display
// ══════════════════════════════════════════════════════════════════════════
DMP.SECTORS = {
    core_governance: {
        label: "Core Governance & Administration",
        icon: "account_balance",
        color: [26, 54, 93],
        order: 1
    },
    finance_planning: {
        label: "Finance & Planning",
        icon: "payments",
        color: [156, 136, 51],
        order: 2
    },
    revenue_dm: {
        label: "Revenue & Disaster Management",
        icon: "gavel",
        color: [49, 130, 206],
        order: 3
    },
    home_security: {
        label: "Home, Law & Security",
        icon: "shield",
        color: [229, 62, 62],
        order: 4
    },
    health_medical: {
        label: "Health, Medical & Family Welfare",
        icon: "local_hospital",
        color: [56, 161, 105],
        order: 5
    },
    education_skills: {
        label: "Education & Skill Development",
        icon: "school",
        color: [108, 92, 231],
        order: 6
    },
    agriculture_env: {
        label: "Agriculture, Environment & Water",
        icon: "agriculture",
        color: [52, 168, 83],
        order: 7
    },
    infrastructure: {
        label: "Infrastructure, Industry & Urban Dev",
        icon: "engineering",
        color: [230, 126, 34],
        order: 8
    },
    rural_panchayat: {
        label: "Panchayat Raj & Rural Development",
        icon: "home_work",
        color: [38, 166, 154],
        order: 9
    },
    social_welfare: {
        label: "Social Welfare & Empowerment",
        icon: "people",
        color: [214, 158, 46],
        order: 10
    }
};

// ══════════════════════════════════════════════════════════════════════════
// 40 AP State Departments
// Source: codes.ap.gov.in — AP HRMS Code Book
// Each department maps to one sector group above.
// The key is the official ORG_NAME used as the `category` field value.
// ══════════════════════════════════════════════════════════════════════════
DMP.CATEGORIES = {
    // ── Core Governance & Administration (7) ──
    "Chief Ministers Office":               { sector: "core_governance",  code: "CAB01", abbr: "CAB", color: [26, 54, 93] },
    "Chief Secretarys Office":              { sector: "core_governance",  code: "CSO01", abbr: "CSO", color: [36, 64, 103] },
    "General Administration":               { sector: "core_governance",  code: "GAD01", abbr: "GAD", color: [46, 74, 113] },
    "Governors Secretariat":                { sector: "core_governance",  code: "GAD07", abbr: "RJB", color: [56, 84, 123] },
    "Chief Electoral Officer":              { sector: "core_governance",  code: "GAD16", abbr: "CEO", color: [36, 74, 123] },
    "Legislature":                          { sector: "core_governance",  code: "LEG01", abbr: "LEG", color: [66, 94, 133] },
    "Real Time Governance":                 { sector: "core_governance",  code: "RTG01", abbr: "RTG", color: [46, 84, 133] },

    // ── Finance & Planning (3) ──
    "Finance":                              { sector: "finance_planning", code: "FIN01", abbr: "FIN", color: [156, 136, 51] },
    "Planning":                             { sector: "finance_planning", code: "PLG01", abbr: "PLG", color: [166, 146, 61] },
    "Public Enterprises":                   { sector: "finance_planning", code: "PBE01", abbr: "PBE", color: [146, 126, 41] },

    // ── Revenue & Disaster Management (2) ──
    "Revenue":                              { sector: "revenue_dm",       code: "REV01", abbr: "REV", color: [49, 130, 206] },
    "Disaster Management":                  { sector: "revenue_dm",       code: "RDM01", abbr: "RDM", color: [69, 140, 216] },

    // ── Home, Law & Security (2) ──
    "Home":                                 { sector: "home_security",    code: "HOM01", abbr: "HOM", color: [229, 62, 62] },
    "Law":                                  { sector: "home_security",    code: "LAW01", abbr: "LAW", color: [209, 72, 72] },

    // ── Health, Medical & Family Welfare (1) ──
    "Health, Medical & Family Welfare":     { sector: "health_medical",   code: "HMF01", abbr: "HMF", color: [56, 161, 105] },

    // ── Education & Skill Development (3) ──
    "Human Resources (Higher Education)":   { sector: "education_skills", code: "EHE01", abbr: "EHE", color: [108, 92, 231] },
    "Human Resources (School Education)":   { sector: "education_skills", code: "ESE01", abbr: "ESE", color: [118, 102, 241] },
    "Dept of Skills Development and Training": { sector: "education_skills", code: "SEI01", abbr: "SEI", color: [98, 82, 221] },

    // ── Agriculture, Environment & Water (4) ──
    "Agriculture and Marketing":            { sector: "agriculture_env",  code: "AGC01", abbr: "AGC", color: [52, 168, 83] },
    "Animal Husbandry, Dairy Dev and Fisheries": { sector: "agriculture_env", code: "AHF01", abbr: "AHF", color: [62, 178, 93] },
    "Environment, Forest, Science and Technology": { sector: "agriculture_env", code: "EFS01", abbr: "EFS", color: [42, 158, 73] },
    "Water Resources":                      { sector: "agriculture_env",  code: "ICD01", abbr: "ICD", color: [72, 188, 103] },

    // ── Infrastructure, Industry & Urban Dev (9) ──
    "Energy":                               { sector: "infrastructure",   code: "ENE01", abbr: "ENE", color: [230, 126, 34] },
    "Transport, Roads and Buildings":       { sector: "infrastructure",   code: "TRB01", abbr: "TRB", color: [220, 136, 44] },
    "Municipal Administration and Urban Development": { sector: "infrastructure", code: "MAU01", abbr: "MAU", color: [210, 116, 24] },
    "Housing":                              { sector: "infrastructure",   code: "HOU01", abbr: "HOU", color: [240, 146, 54] },
    "Industries and Commerce":              { sector: "infrastructure",   code: "INC01", abbr: "INC", color: [200, 116, 34] },
    "Infrastructure and Investment":        { sector: "infrastructure",   code: "INI01", abbr: "INI", color: [220, 116, 44] },
    "IT, Electronics and Communications":   { sector: "infrastructure",   code: "ITC01", abbr: "ITC", color: [210, 136, 24] },
    "Consumer Affairs, Food and Civil Supplies": { sector: "infrastructure", code: "FCS01", abbr: "FCS", color: [230, 146, 54] },
    "Labour and Employment":                { sector: "infrastructure",   code: "LAE01", abbr: "LAE", color: [200, 126, 44] },

    // ── Panchayat Raj & Rural Development (2) ──
    "Panchayat Raj and Rural Development":  { sector: "rural_panchayat",  code: "PRR01", abbr: "PRR", color: [38, 166, 154] },
    "Gram/Ward Volunteers and Village/Ward Secretariats": { sector: "rural_panchayat", code: "GWS01", abbr: "GWS", color: [48, 176, 164] },

    // ── Social Welfare & Empowerment (7) ──
    "Social Welfare":                       { sector: "social_welfare",   code: "SOW01", abbr: "SOW", color: [214, 158, 46] },
    "Backward Classes Welfare":             { sector: "social_welfare",   code: "BCW01", abbr: "BCW", color: [204, 148, 36] },
    "Minorities Welfare":                   { sector: "social_welfare",   code: "MNW01", abbr: "MNW", color: [224, 168, 56] },
    "Dept of Tribal Welfare":               { sector: "social_welfare",   code: "TBW01", abbr: "TBW", color: [194, 138, 26] },
    "Dept of Economically Weaker Sections Welfare": { sector: "social_welfare", code: "EWS01", abbr: "EWS", color: [234, 178, 66] },
    "Women, Children, Disabled and Senior Citizens": { sector: "social_welfare", code: "WDC01", abbr: "WDC", color: [204, 158, 56] },
    "Youth Advancement, Tourism and Culture": { sector: "social_welfare", code: "YTC01", abbr: "YTC", color: [224, 148, 36] }
};

// ══════════════════════════════════════════════════════════════════════════
// HODs (Heads of Department) under each State Department
// Source: codes.ap.gov.in — 93 HODs mapped to parent SD via REPORT_ORG
// ══════════════════════════════════════════════════════════════════════════
DMP.AP_HODS = {
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
    "YTC01": ["Youth Services", "Archaeology and Museums"]
};

// ══════════════════════════════════════════════════════════════════════════
// Legacy category migration — maps old category names to current AP departments
// ══════════════════════════════════════════════════════════════════════════
DMP.NDMA_TO_AP = {
    "Revenue & District Administration":    "Revenue",
    "Police":                               "Home",
    "Fire & Emergency Services":            "Home",
    "Medical & Public Health":              "Health, Medical & Family Welfare",
    "SDRF":                                 "Home",
    "NDRF":                                 "Home",
    "Civil Defence":                        "Home",
    "Home Guards":                          "Home",
    "Armed Forces":                         "Home",
    "Irrigation & Water Resources":         "Water Resources",
    "Municipal & Urban Development":        "Municipal Administration and Urban Development",
    "Power / Electricity":                  "Energy",
    "Transport":                            "Transport, Roads and Buildings",
    "Public Works / R&B":                   "Transport, Roads and Buildings",
    "Telecom & Communications":             "IT, Electronics and Communications",
    "Information Technology, Electronics and Communications": "IT, Electronics and Communications",
    "Labour, Factories, Boilers and Insurance Medical Services": "Labour and Employment",
    "Panchayat Raj & Rural Development":    "Panchayat Raj and Rural Development",
    "Food & Civil Supplies":                "Consumer Affairs, Food and Civil Supplies",
    "Education":                            "Human Resources (School Education)",
    "Agriculture & Fisheries":              "Agriculture and Marketing",
    "Veterinary & Animal Husbandry":        "Animal Husbandry, Dairy Dev and Fisheries",
    "NCC / Youth Organizations":            "Youth Advancement, Tourism and Culture",
    "NGOs & Volunteer Organizations":       "Disaster Management",
    "Private Sector / CSR":                 "Industries and Commerce",
    "Media & Public Information":           "General Administration",
    "APSDMA / DM Coordination":             "Disaster Management"
};

// Also handle Secretariat API dept_name → AP category name
// (reports.ap.gov.in uses uppercase names without punctuation)
DMP.SECRETARIAT_TO_AP = {
    "AGRICULTURE AND MARKETING":                                "Agriculture and Marketing",
    "ANIMAL HUSBANDRY DAIRY DEVELOPMENT AND FISHERIES":         "Animal Husbandry, Dairy Dev and Fisheries",
    "BACKWARD CLASSES WELFARE":                                 "Backward Classes Welfare",
    "CHIEF ELECTORAL OFFICER":                                  "Chief Electoral Officer",
    "CHIEF MINISTERS OFFICE":                                   "Chief Ministers Office",
    "CHIEF SECRETARYS OFFICE":                                  "Chief Secretarys Office",
    "CONSUMER AFFAIRS FOOD AND CIVIL SUPPLIES":                 "Consumer Affairs, Food and Civil Supplies",
    "DEPARTMENT OF ECONOMICALLY WEAKER SECTIONS WELFARE":       "Dept of Economically Weaker Sections Welfare",
    "DEPARTMENT OF SKILLS DEVELOPMENT AND TRAINING":            "Dept of Skills Development and Training",
    "DEPARTMENT OF TRIBAL WELFARE":                             "Dept of Tribal Welfare",
    "DISASTER MANAGEMENT":                                      "Disaster Management",
    "ENERGY":                                                   "Energy",
    "ENVIRONMENT FOREST SCIENCE AND TECHNOLOGY":                "Environment, Forest, Science and Technology",
    "FINANCE":                                                  "Finance",
    "GENERAL ADMINISTRATION":                                   "General Administration",
    "GRAM VOLUNTEERS/WARD VOLUNTEERS AND VILLAGE SECRETARIATS/WARD SECRETARIATS": "Gram/Ward Volunteers and Village/Ward Secretariats",
    "HEALTH MEDICAL & FAMILY WELFARE":                          "Health, Medical & Family Welfare",
    "HOME":                                                     "Home",
    "HOUSING":                                                  "Housing",
    "HUMAN RESOURCES (HIGHER EDUCATION)":                       "Human Resources (Higher Education)",
    "HUMAN RESOURCES (SCHOOL EDUCATION)":                       "Human Resources (School Education)",
    "INDUSTRIES AND COMMERCE":                                  "Industries and Commerce",
    "INFORMATION TECHNOLOGY ELECTRONICS AND COMMUNICATIONS":    "IT, Electronics and Communications",
    "INFRASTRUCTURE AND INVESTMENT":                            "Infrastructure and Investment",
    "LABOUR FACTORIES BOILERS & INSURANCE MEDICAL SERVICES":    "Labour and Employment",
    "LAW":                                                      "Law",
    "LEGISLATURE":                                              "Legislature",
    "MINORITIES WELFARE":                                       "Minorities Welfare",
    "MUNICIPAL ADMINISTRATION AND URBAN DEVELOPMENT":           "Municipal Administration and Urban Development",
    "PANCHYAT RAJ AND RURAL DEVELOPMENT":                       "Panchayat Raj and Rural Development",
    "PLANNING":                                                 "Planning",
    "PUBLIC ENTERPRISES":                                       "Public Enterprises",
    "REAL TIME GOVERNANCE":                                     "Real Time Governance",
    "REVENUE":                                                  "Revenue",
    "SOCIAL WELFARE":                                           "Social Welfare",
    "TRANSPORT ROADS AND BUILDINGS":                             "Transport, Roads and Buildings",
    "WATER RESOURCES":                                          "Water Resources",
    "WOMEN CHILDREN DISABLED AND SENIOR CITIZENS":              "Women, Children, Disabled and Senior Citizens",
    "YOUTH ADVANCEMENT TOURISM AND CULTURE":                    "Youth Advancement, Tourism and Culture"
};

/** Migrate legacy category name → current AP department name */
DMP.migrateCategory = function(oldCat) {
    if (!oldCat) return "General Administration";
    // Already a valid AP department?
    if (DMP.CATEGORIES[oldCat]) return oldCat;
    // Check legacy migration
    if (DMP.NDMA_TO_AP[oldCat]) return DMP.NDMA_TO_AP[oldCat];
    // Check Secretariat uppercase
    var upper = oldCat.toUpperCase().replace(/[,.']/g, "");
    if (DMP.SECRETARIAT_TO_AP[upper]) return DMP.SECRETARIAT_TO_AP[upper];
    // Fuzzy match by containment
    var keys = Object.keys(DMP.CATEGORIES);
    for (var i = 0; i < keys.length; i++) {
        if (oldCat.toLowerCase().indexOf(keys[i].toLowerCase()) >= 0 ||
            keys[i].toLowerCase().indexOf(oldCat.toLowerCase()) >= 0) {
            return keys[i];
        }
    }
    return "General Administration";
};

// ── DM Roles (functional assignments within disaster management) ──
DMP.DM_ROLES = {
    "None":                    { color: [180, 180, 180] },
    "Nodal Officer":           { color: [230, 126, 34] },
    "SPOC":                    { color: [231, 76, 60] },
    "EOC Duty Officer":        { color: [41, 128, 185] },
    "Control Room Incharge":   { color: [142, 68, 173] },
    "DEOC Incharge":           { color: [39, 174, 96] },
    "SEOC Duty":               { color: [22, 160, 133] },
    "IRS Commander":           { color: [192, 57, 43] },
    "IRS Operations Chief":    { color: [243, 156, 18] },
    "IRS Planning Chief":      { color: [52, 152, 219] },
    "IRS Logistics Chief":     { color: [46, 204, 113] },
    "Relief Coordinator":      { color: [243, 156, 18] },
    "Evacuation Incharge":     { color: [155, 89, 182] },
    "Shelter Incharge":        { color: [52, 152, 219] },
    "Search Rescue Lead":      { color: [211, 84, 0] },
    "Medical Responder Lead":  { color: [26, 188, 156] },
    "Communication Officer":   { color: [44, 62, 80] },
    "Damage Assessment Officer": { color: [127, 140, 141] },
    "Early Warning Officer":   { color: [241, 196, 15] },
    "Flood Monitoring Officer": { color: [52, 73, 94] },
    "DDMA Chairperson":        { color: [44, 62, 80] },
    "DDMA Member Secretary":   { color: [127, 140, 141] },
    "Other DM Role":           { color: [149, 165, 166] }
};

// ── Disaster Duty Status ──
DMP.DUTY_STATUS = {
    "Assigned": { color: [230, 126, 34], label: "Assigned" },
    "On Duty":  { color: [39, 174, 96],  label: "On Duty" },
    "Standby":  { color: [52, 152, 219], label: "Standby" },
    "Relieved": { color: [149, 165, 166], label: "Relieved" },
    "On Leave": { color: [192, 57, 43],  label: "On Leave" }
};

// ── Personnel Status ──
DMP.STATUS_VALUES = ["Active", "On Leave", "Transferred", "Retired", "Vacant"];

// ── Hierarchy Levels (1-6) ──
DMP.HIERARCHY = {
    1: { generic: "Apex / State",          example: "CM, CS, DGP, Ministers, Governor" },
    2: { generic: "Department Head",       example: "Principal Secretary, Commissioner, Director" },
    3: { generic: "District Head",         example: "Collector, SP, DMHO, DEO, DFO" },
    4: { generic: "Sub-District / Division", example: "Joint Collector, RDO, DSP, Addl SP" },
    5: { generic: "Mandal / Block",        example: "Tahsildar, MPDO, CI, PHC MO" },
    6: { generic: "Village / Last Mile",   example: "VRO, SI, ANM, ASHA, Fireman, Lineman" }
};

// ── 28 AP Districts ──
DMP.AP_DISTRICTS = [
    "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya",
    "Bapatla", "Chittoor", "Dr.B.R.Ambedkar Konaseema", "East Godavari",
    "Eluru", "Guntur", "Kakinada", "Krishna",
    "Kurnool", "Markapuram", "Nandyal", "NTR",
    "Palnadu", "Parvathipuram Manyam", "Polavaram", "Prakasam",
    "Sri Potti Sriramulu Nellore", "Sri Sathya Sai", "Srikakulam",
    "Tirupati", "Visakhapatnam", "Vizianagaram", "West Godavari",
    "Y.S.R.Kadapa"
];

// ── 4 View Modes ──
DMP.VIEW_MODES = {
    department: { label: "Department",      icon: "business",      default: true },
    geographic: { label: "Geographic",      icon: "map",           default: false },
    command:    { label: "Chain of Command", icon: "account_tree", default: false },
    disaster:   { label: "Disaster Duty",   icon: "warning",       default: false }
};

// ── Helper Functions ──

/** Get sector/group key for a department name */
DMP.getSector = function(deptName) {
    var cat = DMP.CATEGORIES[deptName];
    return cat ? cat.sector : null;
};

/** Get sector/group config for a department name */
DMP.getSectorConfig = function(deptName) {
    var sectorKey = DMP.getSector(deptName);
    return sectorKey ? DMP.SECTORS[sectorKey] : null;
};

/** Get department color as [r,g,b] */
DMP.getCategoryColor = function(deptName) {
    var cat = DMP.CATEGORIES[deptName];
    return cat ? cat.color : [120, 120, 120];
};

/** Get sector/group color as [r,g,b] */
DMP.getSectorColor = function(sectorKey) {
    var sec = DMP.SECTORS[sectorKey];
    return sec ? sec.color : [120, 120, 120];
};

/** Get department ORG_CODE for a department name */
DMP.getDeptCode = function(deptName) {
    var cat = DMP.CATEGORIES[deptName];
    return cat ? cat.code : null;
};

/** Get HODs for a department ORG_CODE */
DMP.getHODs = function(deptCode) {
    return DMP.AP_HODS[deptCode] || [];
};

/** Get departments grouped by sector (sorted) */
DMP.getCategoriesBySector = function() {
    var result = {};
    var sectorOrder = Object.keys(DMP.SECTORS).sort(function(a, b) {
        return DMP.SECTORS[a].order - DMP.SECTORS[b].order;
    });
    sectorOrder.forEach(function(sk) {
        result[sk] = [];
    });
    Object.keys(DMP.CATEGORIES).forEach(function(catName) {
        var sectorKey = DMP.CATEGORIES[catName].sector;
        if (result[sectorKey]) result[sectorKey].push(catName);
    });
    return result;
};

/** Get hierarchy label for a level */
DMP.getHierarchyLabel = function(level) {
    var h = DMP.HIERARCHY[level];
    if (!h) return "Level " + level;
    return h.generic;
};

/** Get all department names as sorted array */
DMP.getCategoryNames = function() {
    return Object.keys(DMP.CATEGORIES).sort();
};

/** Get sorted sector keys */
DMP.getSortedSectorKeys = function() {
    return Object.keys(DMP.SECTORS).sort(function(a, b) {
        return DMP.SECTORS[a].order - DMP.SECTORS[b].order;
    });
};

// ── Branding ──
DMP.BRANDING = {
    GOV_NAME: "Government of Andhra Pradesh",
    AUTHORITY_NAME: "Andhra Pradesh State Disaster Management Authority",
    AUTHORITY_SHORT: "APSDMA",
    APP_TITLE: "Disaster Management Personnel Directory",
    LOGO_URL: "https://apsdmagis.ap.gov.in/gisportal/sharing/rest/content/items/9a2a82b11aaa4e99b877567efe3de99c/data",
    EMBLEM_URL: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Emblem_of_India.svg/200px-Emblem_of_India.svg.png"
};

// ── Footer Data ──
DMP.FOOTER = {
    ABOUT_TEXT: "The Andhra Pradesh State Disaster Management Authority (APSDMA) is the apex body for disaster management in the state, established under the Disaster Management Act, 2005. APSDMA coordinates all disaster preparedness, mitigation, and response activities across 28 districts.",
    ADDRESS: "APSDMA, Real Time Governance Centre (RTGC), 4th Floor, Interim Government Complex, Velagapudi, Amaravati, Andhra Pradesh - 522503",
    EMERGENCY_CONTACTS: [
        { label: "APSDMA Helpline", number: "1070" },
        { label: "National Emergency", number: "112" },
        { label: "Police", number: "100" },
        { label: "Fire", number: "101" },
        { label: "Ambulance", number: "108" },
        { label: "State EOC", number: "0863-2340104" }
    ],
    QUICK_LINKS: [
        { label: "APSDMA Portal", url: "https://apsdmagis.ap.gov.in/gisportal" },
        { label: "AP State Portal", url: "https://ap.gov.in" },
        { label: "AP Codes", url: "https://codes.ap.gov.in" },
        { label: "AP Secretariat", url: "http://www.reports.ap.gov.in/dept/" },
        { label: "IMD", url: "https://mausam.imd.gov.in" }
    ]
};

// ── About Page Content (HTML sections) ──
DMP.ABOUT = {
    OVERVIEW: '<p>The <strong>Disaster Management Personnel Directory</strong> is a GIS-enabled web application developed by the APSDMA GIS Cell to provide a comprehensive, real-time view of all disaster management personnel across Andhra Pradesh.</p>' +
        '<p>Organized by the <strong>AP State Government\u2019s official 40 State Departments</strong> (as per the AP HRMS Code Book from <a href="https://codes.ap.gov.in" target="_blank">codes.ap.gov.in</a>), the directory maps personnel across 10 department groups and 6 hierarchy levels.</p>' +
        '<p>The directory enables rapid identification and mobilization of personnel during disasters, supports chain-of-command visualization, and provides real-time situational awareness of personnel deployment across all 28 districts of Andhra Pradesh.</p>',

    ARCHITECTURE: '<p>Personnel data is organized in a two-tier hierarchy:</p>' +
        '<div class="about-highlight">' +
        '<strong>10 Department Groups</strong> \u2014 logical groupings of AP state departments<br>' +
        '<strong>40 State Departments</strong> \u2014 official AP government departments (SD codes from AP HRMS)' +
        '</div>' +
        '<table class="about-table"><thead><tr><th>Group</th><th>State Departments</th></tr></thead><tbody>' +
        '<tr><td><span class="about-dot" style="background:rgb(26,54,93)"></span> Core Governance</td><td>CM Office, CS Office, GAD, Governor, CEO, Legislature, RTG</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(156,136,51)"></span> Finance &amp; Planning</td><td>Finance, Planning, Public Enterprises</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(49,130,206)"></span> Revenue &amp; DM</td><td>Revenue, Disaster Management</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(229,62,62)"></span> Home, Law &amp; Security</td><td>Home (Police, Fire, Prisons, SPF), Law</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(56,161,105)"></span> Health &amp; Medical</td><td>Health, Medical &amp; Family Welfare</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(108,92,231)"></span> Education &amp; Skills</td><td>Higher Education, School Education, Skills Development</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(52,168,83)"></span> Agriculture &amp; Environment</td><td>Agriculture, Animal Husbandry, Forest, Water Resources</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(230,126,34)"></span> Infrastructure &amp; Industry</td><td>Energy, Transport/R&amp;B, Municipal, Housing, Industries, IT, Food/Civil Supplies, Labour</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(38,166,154)"></span> Panchayat Raj &amp; Rural Dev</td><td>Panchayat Raj, Gram/Ward Volunteers</td></tr>' +
        '<tr><td><span class="about-dot" style="background:rgb(214,158,46)"></span> Social Welfare</td><td>Social Welfare, BC Welfare, Minorities, Tribal, EWS, Women/Children, Youth/Tourism</td></tr>' +
        '</tbody></table>' +
        '<p>Department structure sourced from the <a href="https://codes.ap.gov.in" target="_blank">AP HRMS Code Book</a>. Each of the 40 State Departments has subordinate Heads of Departments (HODs) \u2014 93 in total.</p>',

    VIEW_MODES: '<p>The directory offers <strong>4 specialized view modes</strong>, each restructuring the hierarchy tree and map symbology for a specific operational need:</p>' +
        '<div class="about-view-cards">' +
        '<div class="about-view-card"><h4>Department View</h4><p><strong>Tree:</strong> Group \u2192 State Department \u2192 District \u2192 Person</p><p><strong>Use:</strong> \u201cShow all Home dept personnel across AP\u201d</p><p>Default view. Color-coded by the 10 department groups.</p></div>' +
        '<div class="about-view-card"><h4>Geographic View</h4><p><strong>Tree:</strong> District \u2192 Mandal \u2192 Department \u2192 Person</p><p><strong>Use:</strong> \u201cWho is posted in Prakasam district?\u201d</p><p>Location-first browsing with administrative boundary emphasis.</p></div>' +
        '<div class="about-view-card"><h4>Chain of Command View</h4><p><strong>Tree:</strong> L1 \u2192 L2 \u2192 L3 \u2192 ...</p><p><strong>Use:</strong> \u201cShow reporting chain from CS down through Revenue\u201d</p><p>Hierarchical reporting structure visualization.</p></div>' +
        '<div class="about-view-card"><h4>Disaster Duty View</h4><p><strong>Tree:</strong> Disaster \u2192 Status \u2192 Team \u2192 Person</p><p><strong>Use:</strong> \u201cDuring a cyclone, who is deployed where?\u201d</p><p>Active disaster assignment tracking with duty status indicators.</p></div>' +
        '</div>',

    HIERARCHY: '<p>Personnel are assigned a <strong>hierarchy level (1\u20136)</strong>:</p>' +
        '<table class="about-table about-table-sm"><thead><tr><th>Level</th><th>Generic</th><th>Revenue</th><th>Home (Police)</th><th>Health</th></tr></thead><tbody>' +
        '<tr><td>1</td><td>Apex / State</td><td>CM / CS</td><td>DGP</td><td>Director Health</td></tr>' +
        '<tr><td>2</td><td>Dept Head</td><td>CCLA / Commissioner</td><td>IG / DIG</td><td>Jt Director</td></tr>' +
        '<tr><td>3</td><td>District Head</td><td>Collector</td><td>SP</td><td>DMHO</td></tr>' +
        '<tr><td>4</td><td>Sub-District</td><td>JC / RDO</td><td>DSP</td><td>Civil Surgeon</td></tr>' +
        '<tr><td>5</td><td>Mandal/Block</td><td>Tahsildar</td><td>CI</td><td>PHC MO</td></tr>' +
        '<tr><td>6</td><td>Village/Field</td><td>VRO</td><td>SI / Constable</td><td>ANM / ASHA</td></tr>' +
        '</tbody></table>',

    HOW_IT_WORKS: '<div class="about-flow">' +
        '<div class="about-flow-step"><div class="about-flow-num">1</div><div><strong>Data Sources</strong><br>Personnel data is aggregated from AP Secretariat e-Directory, SEOC contacts, Survey123, and district websites \u2014 organized by the 40 State Departments from AP HRMS Code Book.</div></div>' +
        '<div class="about-flow-step"><div class="about-flow-num">2</div><div><strong>ArcGIS Feature Service</strong><br>Records are stored as georeferenced features in the DM_Personnel hosted feature service on ArcGIS Enterprise, with fields for identity, posting, capabilities, and disaster duty.</div></div>' +
        '<div class="about-flow-step"><div class="about-flow-num">3</div><div><strong>Web Directory &amp; Map</strong><br>This web application queries the feature service in real-time, building interactive hierarchy trees, symbology-driven maps, and detailed personnel cards.</div></div>' +
        '<div class="about-flow-step"><div class="about-flow-num">4</div><div><strong>Operational Decision Support</strong><br>During disasters, commanders use the directory to identify available personnel, track duty assignments, and visualize the chain of command on the map.</div></div>' +
        '</div>',

    REAL_WORLD: '<div class="about-scenarios">' +
        '<div class="about-scenario"><h4>Cyclone Response</h4><p>As a cyclone approaches the coast, the SEOC switches to <strong>Disaster Duty View</strong> to monitor deployed teams. Home and Revenue department personnel are filtered by coastal districts. The chain of command from District Collector down to Village Revenue Officers is visualized.</p></div>' +
        '<div class="about-scenario"><h4>Flood Operations</h4><p>During river flooding, the <strong>Geographic View</strong> shows all personnel in affected districts. The Home department\u2019s SDRF teams and Water Resources engineers are located on the map. Transport/R&amp;B staff are identified for breach repair coordination.</p></div>' +
        '<div class="about-scenario"><h4>Earthquake Coordination</h4><p>After an earthquake, the <strong>Department View</strong> helps identify Health dept personnel by district. Capabilities like training certifications help deploy the right specialists. The 24x7 availability filter ensures only contactable personnel are shown.</p></div>' +
        '</div>',

    DATA_ENTRY: '<p>Personnel records are added and updated through <strong>ArcGIS Survey123</strong> and automated data pipelines:</p>' +
        '<ul>' +
        '<li><strong>AP Secretariat e-Directory:</strong> 813 officers across 39 departments (<a href="http://www.reports.ap.gov.in/dept/" target="_blank">reports.ap.gov.in</a>)</li>' +
        '<li><strong>SEOC Contacts:</strong> Emergency duty officers from State EOC records</li>' +
        '<li><strong>Survey123 Forms:</strong> Field officers submit data via mobile-friendly forms</li>' +
        '<li><strong>District Websites:</strong> Who\u2019s Who pages from 26 district portals</li>' +
        '</ul>' +
        '<p>All data is categorized using the official AP HRMS Code Book structure with 40 State Departments and 93 Heads of Departments.</p>',

    CREDITS: '<p><strong>Developed by:</strong> APSDMA GIS Cell, Andhra Pradesh State Disaster Management Authority</p>' +
        '<p><strong>Data Sources:</strong></p>' +
        '<ul>' +
        '<li><a href="https://codes.ap.gov.in" target="_blank">AP HRMS Code Book</a> \u2014 Department structure (40 SDs, 93 HODs)</li>' +
        '<li><a href="http://www.reports.ap.gov.in/dept/" target="_blank">AP Secretariat e-Directory</a> \u2014 Secretariat officer data</li>' +
        '<li>SEOC Contact Database \u2014 Emergency duty officers</li>' +
        '</ul>' +
        '<p><strong>Technology Stack:</strong></p>' +
        '<ul>' +
        '<li>ArcGIS Enterprise 11.x (Portal, Server, Data Store)</li>' +
        '<li>ArcGIS JavaScript API 4.28</li>' +
        '<li>ArcGIS Survey123 for data collection</li>' +
        '<li>Python automation for data pipelines</li>' +
        '</ul>'
};
