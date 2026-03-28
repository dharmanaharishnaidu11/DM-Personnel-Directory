/* ==========================================================================
   ARCHIVED — NDMA Categorisation (Pre-Feb 2026)
   ==========================================================================
   This file preserves the original NDMA-based categorisation that was used
   before the webapp was restructured to follow AP State Government's own
   40 State Department structure from codes.ap.gov.in.

   Contents archived:
   - 8 NDMA Sectors
   - 25 NDMA-aligned Categories
   - 16 Emergency Support Functions (ESFs) from NDMP 2019
   - NDMA-specific hierarchy labels per category
   - NDMA-to-AP migration mapping

   NOT IN USE — for reference only.
   ========================================================================== */

// ── 8 NDMA Sectors (original) ──
var NDMA_SECTORS = {
    executive_admin:   { label: "Executive & Revenue Admin",     icon: "account_balance",      color: [49, 130, 206],  order: 1 },
    law_enforcement:   { label: "Law Enforcement & Security",    icon: "shield",               color: [229, 62, 62],   order: 2 },
    fire_rescue:       { label: "Fire & Rescue Forces",          icon: "local_fire_department", color: [255, 152, 0],   order: 3 },
    health_medical:    { label: "Health & Medical",              icon: "local_hospital",        color: [56, 161, 105],  order: 4 },
    infrastructure:    { label: "Infrastructure & Utilities",    icon: "engineering",           color: [128, 90, 213],  order: 5 },
    rural_social:      { label: "Rural & Social Services",       icon: "people",                color: [38, 166, 154],  order: 6 },
    youth_voluntary:   { label: "Youth & Voluntary Sector",      icon: "volunteer_activism",    color: [214, 158, 46],  order: 7 },
    info_coordination: { label: "Information & Coordination",    icon: "campaign",              color: [233, 30, 99],   order: 8 }
};

// ── 25 NDMA-aligned Categories (original) ──
var NDMA_CATEGORIES = {
    "Revenue & District Administration": { sector: "executive_admin", color: [49, 130, 206],  abbr: "REV" },
    "Civil Defence":                     { sector: "executive_admin", color: [66, 153, 225],  abbr: "CD" },
    "Home Guards":                       { sector: "executive_admin", color: [99, 179, 237],  abbr: "HG" },
    "Police":                            { sector: "law_enforcement", color: [229, 62, 62],   abbr: "POL" },
    "Armed Forces":                      { sector: "law_enforcement", color: [197, 48, 48],   abbr: "AF" },
    "Fire & Emergency Services":         { sector: "fire_rescue",     color: [255, 152, 0],   abbr: "FIRE" },
    "SDRF":                              { sector: "fire_rescue",     color: [255, 183, 77],  abbr: "SDRF" },
    "NDRF":                              { sector: "fire_rescue",     color: [255, 112, 67],  abbr: "NDRF" },
    "Medical & Public Health":           { sector: "health_medical",  color: [56, 161, 105],  abbr: "MED" },
    "Veterinary & Animal Husbandry":     { sector: "health_medical",  color: [72, 187, 120],  abbr: "VET" },
    "Irrigation & Water Resources":      { sector: "infrastructure",  color: [128, 90, 213],  abbr: "IRR" },
    "Public Works / R&B":                { sector: "infrastructure",  color: [139, 92, 246],  abbr: "PWD" },
    "Power / Electricity":               { sector: "infrastructure",  color: [167, 139, 250], abbr: "PWR" },
    "Telecom & Communications":          { sector: "infrastructure",  color: [109, 40, 217],  abbr: "TEL" },
    "Transport":                         { sector: "infrastructure",  color: [91, 33, 182],   abbr: "TRN" },
    "Municipal & Urban Development":     { sector: "infrastructure",  color: [124, 58, 237],  abbr: "MUN" },
    "Panchayat Raj & Rural Development": { sector: "rural_social",    color: [38, 166, 154],  abbr: "PR" },
    "Food & Civil Supplies":             { sector: "rural_social",    color: [0, 150, 136],   abbr: "FCS" },
    "Education":                         { sector: "rural_social",    color: [0, 137, 123],   abbr: "EDU" },
    "Agriculture & Fisheries":           { sector: "rural_social",    color: [77, 182, 172],  abbr: "AGR" },
    "NCC / Youth Organizations":         { sector: "youth_voluntary", color: [214, 158, 46],  abbr: "NCC" },
    "NGOs & Volunteer Organizations":    { sector: "youth_voluntary", color: [236, 201, 75],  abbr: "NGO" },
    "Private Sector / CSR":              { sector: "youth_voluntary", color: [183, 121, 31],  abbr: "CSR" },
    "Media & Public Information":        { sector: "info_coordination", color: [233, 30, 99],  abbr: "MED" },
    "APSDMA / DM Coordination":          { sector: "info_coordination", color: [194, 24, 91],  abbr: "DM" }
};

// ── 16 Emergency Support Functions (NDMP 2019) ──
var NDMA_ESF = {
    1:  { name: "Communication",                  lead: "Telecom & Communications",          color: [52, 152, 219] },
    2:  { name: "Public Works & Engineering",      lead: "Public Works / R&B",                color: [46, 204, 113] },
    3:  { name: "Transport",                       lead: "Transport",                         color: [155, 89, 182] },
    4:  { name: "Search & Rescue",                 lead: "SDRF",                              color: [231, 76, 60] },
    5:  { name: "Emergency Management / IRS",      lead: "Revenue & District Administration", color: [241, 196, 15] },
    6:  { name: "Mass Care (Shelter, Food)",        lead: "Revenue & District Administration", color: [230, 126, 34] },
    7:  { name: "Resource Support (Logistics)",     lead: "Revenue & District Administration", color: [52, 73, 94] },
    8:  { name: "Public Health & Medical",          lead: "Medical & Public Health",           color: [26, 188, 156] },
    9:  { name: "Firefighting",                    lead: "Fire & Emergency Services",         color: [211, 84, 0] },
    10: { name: "Hazardous Materials (CBRN)",       lead: "Fire & Emergency Services",         color: [192, 57, 43] },
    11: { name: "Agriculture & Animal Protection",  lead: "Agriculture & Fisheries",           color: [39, 174, 96] },
    12: { name: "Energy (Power, Fuel)",             lead: "Power / Electricity",               color: [243, 156, 18] },
    13: { name: "Law & Order / Security",           lead: "Police",                            color: [142, 68, 173] },
    14: { name: "Long-Term Recovery",               lead: "Revenue & District Administration", color: [127, 140, 141] },
    15: { name: "Public Information / Media",       lead: "Media & Public Information",        color: [44, 62, 80] },
    16: { name: "Debris Management",                lead: "Municipal & Urban Development",     color: [149, 165, 166] }
};

// ── NDMA → AP State Department migration mapping ──
var NDMA_TO_AP_MAPPING = {
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
    "Telecom & Communications":             "Information Technology, Electronics and Communications",
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

// ── NDMA Hierarchy labels per category (original) ──
var NDMA_HIERARCHY_LABELS = {
    1: {
        "Revenue & District Administration": "CM / CS / Special CS",
        "Police": "DGP / Addl DGP",
        "Fire & Emergency Services": "Director Fire Services",
        "Medical & Public Health": "Director Public Health",
        "SDRF": "Commandant SDRF",
        "NDRF": "DG NDRF / Bn Commander",
        "Armed Forces": "GOC-in-C / Flag Officer",
        "Power / Electricity": "CMD / Director",
        "Irrigation & Water Resources": "Engineer-in-Chief"
    },
    2: {
        "Revenue & District Administration": "MD APSDMA / Commissioner",
        "Police": "IG / DIG",
        "Fire & Emergency Services": "Addl / Jt Director Fire",
        "Medical & Public Health": "Jt / Deputy Director Health",
        "SDRF": "2IC / Company Commander",
        "NDRF": "Company Commander",
        "Armed Forces": "Division / Brigade Commander",
        "Power / Electricity": "SE / CE",
        "Irrigation & Water Resources": "SE"
    },
    3: {
        "Revenue & District Administration": "District Collector",
        "Police": "SP / Commissioner",
        "Fire & Emergency Services": "District Fire Officer",
        "Medical & Public Health": "DMHO",
        "SDRF": "Platoon Commander",
        "NDRF": "Platoon Commander",
        "Armed Forces": "CO / Battalion Commander",
        "Power / Electricity": "EE",
        "Irrigation & Water Resources": "EE"
    }
};
