/* ==========================================================================
   DM Personnel Directory — Filters, Stats, Search
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.filters = (function() {

    var _allPersonnel = [];
    var _filteredPersonnel = [];
    var _onFilterChange = null;
    var _searchTimeout = null;

    function init(onFilterChange) {
        _onFilterChange = onFilterChange;
        _populateDropdowns();
        _bindEvents();
    }

    function setPersonnel(all) {
        _allPersonnel = all;
        _filteredPersonnel = all.slice();
    }

    function _populateDropdowns() {
        // Sector dropdown
        var sectorSelect = document.getElementById("filter-sector");
        if (sectorSelect) {
            DMP.getSortedSectorKeys().forEach(function(sk) {
                var opt = document.createElement("option");
                opt.value = sk;
                opt.textContent = DMP.SECTORS[sk].label;
                sectorSelect.appendChild(opt);
            });
        }

        // Category dropdown (populated dynamically when sector changes)
        _populateCategories();

        // District dropdown
        var districtSelect = document.getElementById("filter-district");
        if (districtSelect) {
            DMP.AP_DISTRICTS.forEach(function(d) {
                var opt = document.createElement("option");
                opt.value = d; opt.textContent = d;
                districtSelect.appendChild(opt);
            });
        }

        // Level dropdown
        var levelSelect = document.getElementById("filter-level");
        if (levelSelect) {
            for (var i = 1; i <= 6; i++) {
                var opt = document.createElement("option");
                opt.value = i;
                opt.textContent = "L" + i + " \u2014 " + DMP.HIERARCHY[i].generic;
                levelSelect.appendChild(opt);
            }
        }

        // Status dropdown
        var statusSelect = document.getElementById("filter-status");
        if (statusSelect) {
            DMP.STATUS_VALUES.forEach(function(s) {
                var opt = document.createElement("option");
                opt.value = s; opt.textContent = s;
                statusSelect.appendChild(opt);
            });
        }
    }

    function _populateCategories(sectorKey) {
        var catSelect = document.getElementById("filter-category");
        if (!catSelect) return;

        // Clear existing options except first
        while (catSelect.options.length > 1) catSelect.remove(1);

        var cats = sectorKey
            ? Object.keys(DMP.CATEGORIES).filter(function(c) { return DMP.CATEGORIES[c].sector === sectorKey; })
            : Object.keys(DMP.CATEGORIES);

        cats.sort().forEach(function(c) {
            var opt = document.createElement("option");
            opt.value = c; opt.textContent = c;
            catSelect.appendChild(opt);
        });
    }

    function _bindEvents() {
        // Sector change: repopulate category dropdown
        var sectorSelect = document.getElementById("filter-sector");
        if (sectorSelect) {
            sectorSelect.addEventListener("change", function() {
                _populateCategories(this.value || null);
                document.getElementById("filter-category").value = "";
                _apply();
            });
        }

        // All filter dropdowns
        ["filter-category", "filter-district", "filter-level", "filter-status"].forEach(function(id) {
            var el = document.getElementById(id);
            if (el) el.addEventListener("change", _apply);
        });

        // Search with debounce (filterbar search-box)
        var searchBox = document.getElementById("search-box");
        if (searchBox) {
            searchBox.addEventListener("input", function() {
                // Sync sidebar search
                var sidebar = document.getElementById("sidebar-search");
                if (sidebar && sidebar.value !== this.value) sidebar.value = this.value;
                clearTimeout(_searchTimeout);
                _searchTimeout = setTimeout(_apply, 300);
            });
        }

        // Sidebar search (primary, always visible)
        var sidebarSearch = document.getElementById("sidebar-search");
        if (sidebarSearch) {
            sidebarSearch.addEventListener("input", function() {
                // Sync filterbar search
                if (searchBox && searchBox.value !== this.value) searchBox.value = this.value;
                clearTimeout(_searchTimeout);
                _searchTimeout = setTimeout(_apply, 300);
            });
        }

        // Reset
        var resetBtn = document.getElementById("btn-reset");
        if (resetBtn) {
            resetBtn.addEventListener("click", function() {
                ["filter-sector", "filter-category", "filter-district", "filter-level", "filter-status"].forEach(function(id) {
                    var el = document.getElementById(id);
                    if (el) el.value = "";
                });
                var sb = document.getElementById("search-box");
                if (sb) sb.value = "";
                var ss = document.getElementById("sidebar-search");
                if (ss) ss.value = "";
                _populateCategories(null);
                _apply();
            });
        }

        // Export
        var exportBtn = document.getElementById("btn-export");
        if (exportBtn) {
            exportBtn.addEventListener("click", function() {
                DMP.exportCSV(_filteredPersonnel);
            });
        }
    }

    function _apply() {
        var sector = (document.getElementById("filter-sector") || {}).value || "";
        var cat    = (document.getElementById("filter-category") || {}).value || "";
        var dist   = (document.getElementById("filter-district") || {}).value || "";
        var level  = (document.getElementById("filter-level") || {}).value || "";
        var status = (document.getElementById("filter-status") || {}).value || "";
        var search = ((document.getElementById("sidebar-search") || document.getElementById("search-box") || {}).value || "").toLowerCase().trim();

        _filteredPersonnel = _allPersonnel.filter(function(p) {
            // Sector filter
            if (sector) {
                var pSector = DMP.getSector(p.category);
                if (pSector !== sector) return false;
            }
            // Category filter
            if (cat && p.category !== cat) return false;
            // District filter
            if (dist && p.district_name !== dist) return false;
            // Level filter
            if (level && String(p.hierarchy_level) !== level) return false;
            // Status filter
            if (status && p.status !== status) return false;
            // Search — across all meaningful fields
            if (search) {
                var hay = [p.person_name, p.designation, p.department, p.sub_department,
                           p.phone_primary, p.phone_alternate, p.office_phone,
                           p.district_name, p.mandal_name, p.village_name,
                           p.ngo_org_name, p.email, p.category, p.dm_role,
                           p.disaster_name, p.employee_id, p.remarks,
                           p.reports_to_name, p.reports_to_designation,
                           p.rank_designation, p.jurisdiction_type]
                    .filter(Boolean).join(" ").toLowerCase();
                if (hay.indexOf(search) === -1) return false;
            }
            return true;
        });

        _updateStats();
        if (_onFilterChange) _onFilterChange(_filteredPersonnel);
    }

    function _updateStats() {
        var total = _filteredPersonnel.length;
        var active = _filteredPersonnel.filter(function(p) { return p.status === "Active"; }).length;
        var onDuty = _filteredPersonnel.filter(function(p) {
            return p.disaster_duty_status && (p.disaster_duty_status === "On Duty" || p.disaster_duty_status === "Assigned");
        }).length;
        var districts = {};
        _filteredPersonnel.forEach(function(p) { if (p.district_name) districts[p.district_name] = true; });
        var distCount = Object.keys(districts).length;

        var statsEl = document.getElementById("stats-bar");
        if (statsEl) {
            statsEl.innerHTML =
                '<span>Total: <b>' + total + '</b></span>' +
                '<span>Active: <b>' + active + '</b></span>' +
                (onDuty > 0 ? '<span style="color:#ff6b6b;">On Duty: <b>' + onDuty + '</b></span>' : '') +
                '<span>Districts: <b>' + distCount + '</b>/28</span>';
        }

        var treeCount = document.getElementById("tree-count");
        if (treeCount) treeCount.textContent = total;
    }

    /** Build where clause for map definition expression */
    function getWhereClause() {
        var parts = [];
        var sector = (document.getElementById("filter-sector") || {}).value || "";
        var cat    = (document.getElementById("filter-category") || {}).value || "";
        var dist   = (document.getElementById("filter-district") || {}).value || "";
        var level  = (document.getElementById("filter-level") || {}).value || "";
        var status = (document.getElementById("filter-status") || {}).value || "";

        if (cat) {
            parts.push("category = '" + cat.replace(/'/g, "''") + "'");
        } else if (sector) {
            // Build IN clause for all categories in this sector
            var sectorCats = Object.keys(DMP.CATEGORIES).filter(function(c) {
                return DMP.CATEGORIES[c].sector === sector;
            });
            if (sectorCats.length) {
                parts.push("category IN ('" + sectorCats.join("','") + "')");
            }
        }
        if (dist) parts.push("district_name = '" + dist.replace(/'/g, "''") + "'");
        if (level) parts.push("hierarchy_level = " + level);
        if (status) parts.push("status = '" + status.replace(/'/g, "''") + "'");

        return parts.length ? parts.join(" AND ") : "1=1";
    }

    function getFiltered() { return _filteredPersonnel; }

    return {
        init: init,
        setPersonnel: setPersonnel,
        getFiltered: getFiltered,
        getWhereClause: getWhereClause,
        apply: _apply
    };
})();
