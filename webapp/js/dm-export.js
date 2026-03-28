/* ==========================================================================
   DM Personnel Directory — CSV Export
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.exportCSV = function(personnel) {
    var headers = [
        "Name", "Designation", "Rank", "Department", "Sub-Department", "Category", "Sector",
        "Level", "Employee ID", "Designation Code",
        "District", "Mandal", "Village", "Jurisdiction Type", "Status", "Posted Since",
        "DM Role", "DM Role Active", "DM Order No.", "DM Role Since",
        "Disaster Name", "Disaster Type", "Disaster Duty", "Duty Status", "Duty Location",
        "Duty Start", "Duty End", "Shift", "Team",
        "Personal Mobile", "Alt Mobile", "WhatsApp", "Office Phone", "Ext", "Intercom",
        "Fax", "Residence Phone", "HAM Radio", "Email",
        "Office Address", "Residence Address",
        "Reports To", "Reports To ID",
        "Blood Group", "Languages", "Training/Certs", "Equipment/Resources", "Available 24x7",
        "NGO/Org Name", "Specialization", "Remarks"
    ];

    var rows = personnel.map(function(p) {
        var sectorKey = DMP.getSector(p.category);
        var sectorLabel = sectorKey ? DMP.SECTORS[sectorKey].label : "";
        var reportsTo = [p.reports_to_name, p.reports_to_designation].filter(Boolean).join(" - ");
        var fmtDate = function(d) { return d ? new Date(d).toLocaleDateString("en-IN") : ""; };

        return [
            p.person_name, p.designation, p.rank_designation, p.department, p.sub_department,
            p.category, sectorLabel,
            p.hierarchy_level, p.employee_id, p.designation_code,
            p.district_name, p.mandal_name, p.village_name, p.jurisdiction_type, p.status, fmtDate(p.date_of_posting),
            p.dm_role, p.dm_role_active, p.dm_role_order_no, fmtDate(p.dm_role_since),
            p.disaster_name, p.disaster_type, p.disaster_duty, p.disaster_duty_status, p.disaster_duty_location,
            fmtDate(p.disaster_duty_start), fmtDate(p.disaster_duty_end), p.disaster_shift, p.disaster_team,
            p.phone_primary, p.phone_alternate, p.whatsapp_number, p.office_phone, p.office_phone_ext,
            p.intercom_number, p.fax_number, p.residence_phone, p.ham_radio_callsign, p.email,
            p.office_address, p.residence_address,
            reportsTo, p.reports_to_id,
            p.blood_group, p.languages_spoken, p.training_certifications, p.equipment_resources, p.availability_24x7,
            p.ngo_org_name, p.specialization, p.remarks
        ].map(function(v) { return '"' + ((v || "").toString().replace(/"/g, '""')) + '"'; });
    });

    var csv = [headers.join(",")].concat(rows.map(function(r) { return r.join(","); })).join("\n");
    var blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "DM_Personnel_" + new Date().toISOString().slice(0, 10) + ".csv";
    a.click();
    URL.revokeObjectURL(url);
};
