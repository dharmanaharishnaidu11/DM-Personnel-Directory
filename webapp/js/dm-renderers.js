/* ==========================================================================
   DM Personnel Directory — ArcGIS Renderers (per View Mode)
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.renderers = (function() {

    function _marker(color, size) {
        return {
            type: "simple-marker", style: "circle",
            color: color, size: size || 8,
            outline: { color: [255, 255, 255], width: 1.5 }
        };
    }

    /** Department View: color by department group (10 colors) */
    function sectorRenderer() {
        var infos = [];
        Object.keys(DMP.CATEGORIES).forEach(function(catName) {
            var sectorKey = DMP.CATEGORIES[catName].sector;
            var sectorColor = DMP.SECTORS[sectorKey].color;
            infos.push({
                value: catName,
                symbol: _marker(sectorColor, 8),
                label: catName
            });
        });
        return {
            type: "unique-value",
            field: "category",
            defaultSymbol: _marker([120, 120, 120], 6),
            uniqueValueInfos: infos
        };
    }

    /** Department View: color by individual state department (40 colors) */
    function categoryRenderer() {
        var infos = Object.keys(DMP.CATEGORIES).map(function(catName) {
            return {
                value: catName,
                symbol: _marker(DMP.CATEGORIES[catName].color, 8),
                label: catName
            };
        });
        return {
            type: "unique-value",
            field: "category",
            defaultSymbol: _marker([120, 120, 120], 6),
            uniqueValueInfos: infos
        };
    }

    /** Chain of Command: color by hierarchy level (graduated) */
    function hierarchyRenderer() {
        var levelColors = {
            1: [26, 54, 93],      // dark navy
            2: [44, 82, 130],     // medium navy
            3: [49, 130, 206],    // blue
            4: [99, 179, 237],    // light blue
            5: [144, 205, 244],   // lighter
            6: [190, 227, 248]    // lightest
        };
        var infos = [1, 2, 3, 4, 5, 6].map(function(lv) {
            return {
                value: lv,
                symbol: _marker(levelColors[lv], 6 + (7 - lv) * 1.5),
                label: "Level " + lv + " — " + DMP.HIERARCHY[lv].generic
            };
        });
        return {
            type: "unique-value",
            field: "hierarchy_level",
            defaultSymbol: _marker([180, 180, 180], 6),
            uniqueValueInfos: infos
        };
    }

    /** Disaster Duty: color by duty status */
    function disasterDutyRenderer() {
        var infos = Object.keys(DMP.DUTY_STATUS).map(function(st) {
            return {
                value: st,
                symbol: _marker(DMP.DUTY_STATUS[st].color, 9),
                label: st
            };
        });
        return {
            type: "unique-value",
            field: "disaster_duty_status",
            defaultSymbol: _marker([200, 200, 200], 5),
            uniqueValueInfos: infos
        };
    }

    /** DM Role: color by dm_role */
    function dmRoleRenderer() {
        var infos = Object.keys(DMP.DM_ROLES).filter(function(r) { return r !== "None"; }).map(function(role) {
            return {
                value: role,
                symbol: _marker(DMP.DM_ROLES[role].color, 9),
                label: role
            };
        });
        return {
            type: "unique-value",
            field: "dm_role",
            defaultSymbol: _marker([180, 180, 180], 6),
            uniqueValueInfos: infos
        };
    }

    /** Get renderer for a view mode */
    function getRendererForMode(mode) {
        switch (mode) {
            case "department": return sectorRenderer();
            case "geographic": return categoryRenderer();
            case "command":    return hierarchyRenderer();
            case "disaster":   return disasterDutyRenderer();
            default:           return sectorRenderer();
        }
    }

    /** Build legend HTML for a view mode */
    function buildLegendHTML(mode) {
        var html = "";
        switch (mode) {
            case "department":
                html = '<h4>Department Groups</h4>';
                DMP.getSortedSectorKeys().forEach(function(sk) {
                    var s = DMP.SECTORS[sk];
                    html += '<div class="legend-item"><span class="ldot" style="background:rgb(' + s.color.join(",") + ')"></span> ' + s.label + '</div>';
                });
                break;
            case "geographic":
                html = '<h4>State Departments</h4>';
                var bySector = DMP.getCategoriesBySector();
                DMP.getSortedSectorKeys().forEach(function(sk) {
                    var s = DMP.SECTORS[sk];
                    html += '<div class="legend-section"><b style="font-size:10px;color:#718096;">' + s.label + '</b></div>';
                    bySector[sk].forEach(function(catName) {
                        var c = DMP.CATEGORIES[catName].color;
                        html += '<div class="legend-item"><span class="ldot" style="background:rgb(' + c.join(",") + ')"></span> ' + catName + '</div>';
                    });
                });
                break;
            case "command":
                html = '<h4>Hierarchy Level</h4>';
                for (var lv = 1; lv <= 6; lv++) {
                    var h = DMP.HIERARCHY[lv];
                    html += '<div class="legend-item"><span class="ldot" style="background:rgb(' + [26 + lv * 25, 54 + lv * 25, 93 + lv * 25].join(",") + ')"></span> L' + lv + ' \u2014 ' + h.generic + '</div>';
                }
                break;
            case "disaster":
                html = '<h4>Disaster Duty Status</h4>';
                Object.keys(DMP.DUTY_STATUS).forEach(function(st) {
                    var c = DMP.DUTY_STATUS[st].color;
                    html += '<div class="legend-item"><span class="ldot" style="background:rgb(' + c.join(",") + ')"></span> ' + st + '</div>';
                });
                html += '<div class="legend-item"><span class="ldot" style="background:rgb(200,200,200)"></span> No Active Duty</div>';
                break;
        }
        return html;
    }

    return {
        sectorRenderer: sectorRenderer,
        categoryRenderer: categoryRenderer,
        hierarchyRenderer: hierarchyRenderer,
        disasterDutyRenderer: disasterDutyRenderer,
        dmRoleRenderer: dmRoleRenderer,
        getRendererForMode: getRendererForMode,
        buildLegendHTML: buildLegendHTML
    };
})();
