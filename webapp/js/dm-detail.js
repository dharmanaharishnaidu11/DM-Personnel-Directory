/* ==========================================================================
   DM Personnel Directory — Detail Panel Rendering
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.detail = (function() {

    function _esc(s) {
        if (!s) return "\u2014";
        return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function _fmtDate(d) {
        if (!d) return "\u2014";
        try { return new Date(d).toLocaleDateString("en-IN"); }
        catch (e) { return "\u2014"; }
    }

    function show(person) {
        var panel = document.getElementById("detail-panel");
        panel.classList.remove("hidden");

        // Photo
        var photoEl = document.getElementById("detail-photo");
        photoEl.innerHTML = person.photo_url
            ? '<img src="' + _esc(person.photo_url) + '" alt="' + _esc(person.person_name) + '" onerror="this.parentNode.innerHTML=\'&#128100;\'">'
            : "&#128100;";

        // Name, designation
        document.getElementById("detail-name").textContent = person.person_name || "\u2014";
        document.getElementById("detail-desg").textContent = person.designation || "\u2014";

        // Category badge
        var badge = document.getElementById("detail-badge");
        badge.textContent = person.category || "\u2014";
        var color = DMP.getCategoryColor(person.category);
        badge.style.background = "rgb(" + color.join(",") + ")";

        // Sector label
        var sectorLabel = document.getElementById("detail-sector");
        if (sectorLabel) {
            var sectorConfig = DMP.getSectorConfig(person.category);
            sectorLabel.textContent = sectorConfig ? sectorConfig.label : "";
        }

        // ── DM Role ──
        var dmSection = document.getElementById("d-dm-role-section");
        if (person.dm_role && person.dm_role !== "None") {
            dmSection.style.display = "block";
            document.getElementById("d-dm-role").textContent = person.dm_role;
            document.getElementById("d-dm-active").textContent = person.dm_role_active || "\u2014";
            document.getElementById("d-dm-order").textContent = person.dm_role_order_no || "\u2014";
            document.getElementById("d-dm-since").textContent = _fmtDate(person.dm_role_since);
        } else {
            dmSection.style.display = "none";
        }

        // ── Disaster Duty ──
        var disSection = document.getElementById("d-disaster-section");
        if (person.disaster_name && person.disaster_duty_status && person.disaster_duty_status !== "Relieved") {
            disSection.style.display = "block";
            document.getElementById("d-disaster-name").textContent = person.disaster_name || "\u2014";
            document.getElementById("d-disaster-type").textContent = person.disaster_type || "\u2014";
            document.getElementById("d-disaster-duty").textContent = person.disaster_duty || "\u2014";
            document.getElementById("d-disaster-loc").textContent = person.disaster_duty_location || "\u2014";
            document.getElementById("d-disaster-status").textContent = person.disaster_duty_status || "\u2014";
            document.getElementById("d-disaster-period").textContent =
                _fmtDate(person.disaster_duty_start) + " to " +
                (person.disaster_duty_end ? _fmtDate(person.disaster_duty_end) : "ongoing");
            document.getElementById("d-disaster-shift").textContent = person.disaster_shift || "\u2014";
            document.getElementById("d-disaster-team").textContent = person.disaster_team || "\u2014";
        } else {
            disSection.style.display = "none";
        }

        // ── Posting Details ──
        document.getElementById("d-dept").textContent = person.department || "\u2014";
        var subDeptEl = document.getElementById("d-sub-dept");
        if (subDeptEl) subDeptEl.textContent = person.sub_department || "\u2014";
        document.getElementById("d-emp-id").textContent = person.employee_id || "\u2014";
        document.getElementById("d-jurisdiction").textContent = person.jurisdiction_type
            ? person.jurisdiction_type + " (Level " + (person.hierarchy_level || "?") + ")"
            : "\u2014";
        document.getElementById("d-district").textContent = person.district_name || "\u2014";
        document.getElementById("d-mandal").textContent = person.mandal_name || "\u2014";
        document.getElementById("d-village").textContent = person.village_name || "\u2014";
        document.getElementById("d-status").textContent = person.status || "\u2014";
        document.getElementById("d-posting-date").textContent = _fmtDate(person.date_of_posting);
        document.getElementById("d-address").textContent = person.office_address || "\u2014";

        // Rank (for armed forces / paramilitary)
        var rankEl = document.getElementById("d-rank");
        if (rankEl) {
            if (person.rank_designation) {
                rankEl.parentElement.style.display = "";
                rankEl.textContent = person.rank_designation;
            } else {
                rankEl.parentElement.style.display = "none";
            }
        }

        // ── Reporting Chain ──
        var reportsTo = [person.reports_to_name, person.reports_to_designation].filter(Boolean).join(" \u2014 ");
        var reportsToEl = document.getElementById("d-reports-to");
        if (reportsTo) {
            reportsToEl.innerHTML = '<strong>' + _esc(reportsTo) + '</strong>';
        } else {
            reportsToEl.textContent = "\u2014";
        }
        // Show sub-department / org hierarchy if available
        var subDeptEl = document.getElementById("d-sub-dept");
        if (subDeptEl) {
            subDeptEl.textContent = person.sub_department || "\u2014";
        }
        // Parse chain info from remarks
        var remarksText = person.remarks || "";
        var chainMatch = remarksText.match(/Reports to:\s*(.+?)(?:\.|$)/i);
        if (chainMatch && !reportsTo) {
            reportsToEl.innerHTML = '<strong>' + _esc(chainMatch[1].trim()) + '</strong>';
        }

        // ── Contact Information ──
        document.getElementById("d-phone").innerHTML = person.phone_primary ? '<a href="tel:' + person.phone_primary + '">' + _esc(person.phone_primary) + '</a>' : "\u2014";
        document.getElementById("d-phone-alt").innerHTML = person.phone_alternate ? '<a href="tel:' + person.phone_alternate + '">' + _esc(person.phone_alternate) + '</a>' : "\u2014";
        document.getElementById("d-whatsapp").textContent = person.whatsapp_number || "\u2014";
        document.getElementById("d-office-phone").textContent =
            [person.office_phone, person.office_phone_ext ? "Ext: " + person.office_phone_ext : ""].filter(Boolean).join(" ") || "\u2014";
        document.getElementById("d-intercom").textContent = person.intercom_number || "\u2014";
        document.getElementById("d-fax").textContent = person.fax_number || "\u2014";
        document.getElementById("d-res-phone").textContent = person.residence_phone || "\u2014";
        document.getElementById("d-ham").textContent = person.ham_radio_callsign || "\u2014";
        document.getElementById("d-email").innerHTML = person.email ? '<a href="mailto:' + person.email + '">' + _esc(person.email) + '</a>' : "\u2014";
        document.getElementById("d-res-addr").textContent = person.residence_address || "\u2014";

        // ── Capabilities (new fields) ──
        var capSection = document.getElementById("d-capabilities-section");
        if (capSection) {
            var hasCap = person.blood_group || person.languages_spoken || person.training_certifications || person.equipment_resources;
            if (hasCap) {
                capSection.style.display = "block";
                var bgEl = document.getElementById("d-blood-group");
                if (bgEl) bgEl.textContent = person.blood_group || "\u2014";
                var langEl = document.getElementById("d-languages");
                if (langEl) langEl.textContent = person.languages_spoken || "\u2014";
                var trainEl = document.getElementById("d-training");
                if (trainEl) trainEl.textContent = person.training_certifications || "\u2014";
                var equipEl = document.getElementById("d-equipment");
                if (equipEl) equipEl.textContent = person.equipment_resources || "\u2014";
                var availEl = document.getElementById("d-availability");
                if (availEl) availEl.textContent = person.availability_24x7 || "\u2014";
            } else {
                capSection.style.display = "none";
            }
        }

        // ── NGO section ──
        var ngoSection = document.getElementById("d-ngo-section");
        if (ngoSection) {
            if (person.category === "NGOs & Volunteer Organizations" || person.ngo_org_name) {
                ngoSection.style.display = "block";
                document.getElementById("d-ngo").textContent = person.ngo_org_name || "\u2014";
                document.getElementById("d-spec").textContent = person.specialization || "\u2014";
            } else {
                ngoSection.style.display = "none";
            }
        }

        // ── Remarks ──
        document.getElementById("d-remarks").textContent = person.remarks || "No additional remarks";

        // ── Action buttons ──
        document.getElementById("btn-call").onclick = function() {
            if (person.phone_primary) window.open("tel:" + person.phone_primary);
        };
        document.getElementById("btn-whatsapp").onclick = function() {
            var num = person.whatsapp_number || person.phone_primary;
            if (num) window.open("https://wa.me/91" + num);
        };
    }

    function hide() {
        document.getElementById("detail-panel").classList.add("hidden");
    }

    return {
        show: show,
        hide: hide
    };
})();
