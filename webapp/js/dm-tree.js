/* ==========================================================================
   DM Personnel Directory — Sidebar Tree Builders (4 View Modes)
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.tree = (function() {

    var _container = null;
    var _onSelectPerson = null;

    function init(containerId, onSelectPerson) {
        _container = document.getElementById(containerId);
        _onSelectPerson = onSelectPerson;
    }

    // ── Shared helpers ──

    function _makeNode(depth, label, count, color, childId) {
        var div = document.createElement("div");
        div.className = "tree-level tree-depth-" + depth;
        var colorHtml = "";
        if (color && depth === 0) {
            colorHtml = '<span class="sector-icon" style="background:rgb(' + color.join(",") + ')">&#9679;</span>';
        } else if (color) {
            colorHtml = '<span class="cat-dot" style="background:rgb(' + color.join(",") + ')"></span>';
        }
        div.innerHTML =
            '<div class="tree-node" data-target="' + childId + '">' +
                '<span class="expand-icon">&#9654;</span>' +
                colorHtml +
                '<span class="node-label">' + _escHtml(label) + '</span>' +
                '<span class="node-count">' + count + '</span>' +
            '</div>' +
            '<div class="tree-children" id="' + childId + '"></div>';
        return div;
    }

    function _makePersonEl(person) {
        var initials = (person.person_name || "?").split(" ").map(function(w) { return w[0]; }).join("").substring(0, 2).toUpperCase();
        var badges = "";
        if (person.hierarchy_level && person.hierarchy_level <= 3) {
            badges += '<span class="badge badge-level">L' + person.hierarchy_level + '</span>';
        }
        if (person.dm_role && person.dm_role !== "None") {
            badges += '<span class="badge badge-dm" title="' + _escHtml(person.dm_role) + '">DM</span>';
        }
        if (person.disaster_duty_status && person.disaster_duty_status !== "Relieved" && person.disaster_name) {
            badges += '<span class="badge badge-duty" title="' + _escHtml(person.disaster_duty_status + ": " + person.disaster_name) + '">DUTY</span>';
        }

        // Subtitle: designation + district (if applicable) + phone
        var desgParts = [person.designation || "\u2014"];
        if (person.district_name && person.district_name !== "State Level") {
            desgParts.push(person.district_name);
        }
        if (person.phone_primary) {
            desgParts.push(person.phone_primary);
        }
        var desgText = desgParts.join(" \u2022 ");

        var el = document.createElement("div");
        el.className = "tree-person";
        el.dataset.oid = person.oid;
        el.innerHTML =
            '<div class="person-icon">' + initials + '</div>' +
            '<div class="person-info">' +
                '<div class="person-name">' + _escHtml(person.person_name || "\u2014") + ' ' + badges + '</div>' +
                '<div class="person-desg">' + _escHtml(desgText) + '</div>' +
            '</div>';
        el.addEventListener("click", function() { if (_onSelectPerson) _onSelectPerson(person); });
        return el;
    }

    function _desigRank(d) {
        d = (d || "").toLowerCase();
        if (d === "chief minister") return 1;
        if (/deputy chief minister/.test(d)) return 2;
        if (d === "chief secretary") return 3;
        if (/director general of police/.test(d)) return 4;
        if (/governor/.test(d)) return 5;
        if (/officer on special duty/.test(d)) return 8;
        if (/minister/.test(d)) return 10;
        if (/special chief secretary/.test(d)) return 11;
        if (/principal secretary/.test(d)) return 12;
        if (/secretary/.test(d)) return 13;
        if (/collector/.test(d)) return 20;
        if (/superintendent of police|commissioner of police/.test(d)) return 21;
        return 50;
    }

    function _sortPersons(persons) {
        persons.sort(function(a, b) {
            return (a.hierarchy_level || 99) - (b.hierarchy_level || 99) ||
                   _desigRank(a.designation) - _desigRank(b.designation) ||
                   (a.person_name || "").localeCompare(b.person_name || "");
        });
    }

    function _attachToggle(container) {
        container.querySelectorAll(".tree-node").forEach(function(node) {
            node.addEventListener("click", function() {
                var targetId = this.dataset.target;
                if (!targetId) return;
                var children = document.getElementById(targetId);
                var icon = this.querySelector(".expand-icon");
                if (children) {
                    children.classList.toggle("open");
                    if (icon) icon.classList.toggle("expanded");
                }
            });
        });
    }

    function _autoExpandFirst(container) {
        var first = container.querySelector(".tree-children");
        if (first) {
            first.classList.add("open");
            var prevNode = first.previousElementSibling;
            if (prevNode) {
                var icon = prevNode.querySelector(".expand-icon");
                if (icon) icon.classList.add("expanded");
            }
        }
    }

    function _showEmpty(msg) {
        _container.innerHTML =
            '<div class="empty-state">' +
                '<div class="icon">&#128100;</div>' +
                '<h3>' + (msg || "No Personnel Found") + '</h3>' +
                '<p>Adjust filters or add data via Survey123</p>' +
            '</div>';
    }

    function _escHtml(s) {
        if (!s) return "";
        return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function _uid(prefix) {
        return prefix + "-" + Math.random().toString(36).substr(2, 8);
    }

    // ── View Mode 1: Department View ──
    // Tree: State Department (40) > HODs info > District > Person

    function buildDepartmentTree(personnel) {
        _container.innerHTML = "";
        if (!personnel.length) return _showEmpty();

        // Group by category (department) > district
        var byDept = {};
        personnel.forEach(function(p) {
            var cat = p.category || "Uncategorized";
            var dist = p.district_name || "State Level";
            if (!byDept[cat]) byDept[cat] = {};
            if (!byDept[cat][dist]) byDept[cat][dist] = [];
            byDept[cat][dist].push(p);
        });

        // Sort departments by sector order, then alphabetically within sector
        var deptNames = Object.keys(byDept);
        deptNames.sort(function(a, b) {
            var sa = DMP.CATEGORIES[a], sb = DMP.CATEGORIES[b];
            var oa = sa ? (DMP.SECTORS[sa.sector] || {}).order || 99 : 99;
            var ob = sb ? (DMP.SECTORS[sb.sector] || {}).order || 99 : 99;
            if (oa !== ob) return oa - ob;
            return a.localeCompare(b);
        });

        var lastSectorKey = null;

        deptNames.forEach(function(deptName) {
            var distData = byDept[deptName];
            var deptCount = 0;
            Object.values(distData).forEach(function(arr) { deptCount += arr.length; });
            if (deptCount === 0) return;

            var deptInfo = DMP.CATEGORIES[deptName];
            var catColor = DMP.getCategoryColor(deptName);
            var sectorKey = deptInfo ? deptInfo.sector : null;
            var sectorColor = sectorKey ? DMP.getSectorColor(sectorKey) : catColor;
            var deptLabel = deptName;
            if (deptInfo && deptInfo.abbr) deptLabel = "[" + deptInfo.abbr + "] " + deptName;

            // Insert sector group separator when sector changes
            if (sectorKey && sectorKey !== lastSectorKey) {
                lastSectorKey = sectorKey;
                var secCfg = DMP.SECTORS[sectorKey];
                if (secCfg) {
                    var sepDiv = document.createElement("div");
                    sepDiv.className = "tree-sector-sep";
                    var sepColor = "rgb(" + secCfg.color.join(",") + ")";
                    sepDiv.innerHTML = '<span class="tree-sector-dot" style="background:' + sepColor + '"></span>' +
                        '<span class="tree-sector-name">' + _escHtml(secCfg.label) + '</span>';
                    _container.appendChild(sepDiv);
                }
            }

            var deptId = _uid("d");
            var deptNode = _makeNode(0, deptLabel, deptCount, sectorColor, deptId);
            _container.appendChild(deptNode);
            var deptChildren = document.getElementById(deptId);

            // Add HODs info bar if HODs are defined for this department
            var deptCode = deptInfo ? deptInfo.code : null;
            var hodList = deptCode ? (DMP.AP_HODS[deptCode] || []) : [];
            if (hodList.length > 0) {
                var hodBar = document.createElement("div");
                hodBar.className = "hod-info-bar";
                hodBar.innerHTML = '<span class="hod-label">HODs:</span> ' +
                    hodList.map(function(h) { return '<span class="hod-tag">' + _escHtml(h) + '</span>'; }).join("");
                deptChildren.appendChild(hodBar);
            }

            // District sub-groupings
            var dists = Object.entries(distData).sort(function(a, b) {
                if (a[0] === "State Level") return -1;
                if (b[0] === "State Level") return 1;
                return a[0].localeCompare(b[0]);
            });

            dists.forEach(function(entry) {
                var dist = entry[0], persons = entry[1];
                var distId = _uid("dd");
                var distNode = _makeNode(1, dist, persons.length, null, distId);
                deptChildren.appendChild(distNode);
                var distChildren = document.getElementById(distId);

                _sortPersons(persons);
                persons.forEach(function(p) { distChildren.appendChild(_makePersonEl(p)); });
            });
        });

        _attachToggle(_container);
        _autoExpandFirst(_container);
    }

    // ── View Mode 2: Geographic View ──
    // Tree: Admin Boundary Controls > District > Mandal > Category > Person
    // Click district/mandal to zoom map and show boundaries

    function _buildAdminBoundaryPanel() {
        var panel = document.createElement("div");
        panel.className = "geo-admin-panel";

        // Build toggles dynamically from map layer list
        var layers = DMP.map.getAdminLayerList ? DMP.map.getAdminLayerList() : [];
        var html = '<div class="geo-admin-title">Admin Boundaries</div>';

        // Group: polygons then points
        var polyLayers = layers.filter(function(l) { return !l.isPoint; });
        var pointLayers = layers.filter(function(l) { return l.isPoint; });

        polyLayers.forEach(function(l) {
            var chk = l.visible ? " checked" : "";
            html += '<label class="geo-admin-toggle">' +
                '<input type="checkbox" data-layer-key="' + l.key + '"' + chk + '> ' +
                l.title + '</label>';
        });

        if (pointLayers.length) {
            html += '<div class="geo-admin-sep">Point Layers</div>';
            pointLayers.forEach(function(l) {
                var chk = l.visible ? " checked" : "";
                html += '<label class="geo-admin-toggle">' +
                    '<input type="checkbox" data-layer-key="' + l.key + '"' + chk + '> ' +
                    l.title + '</label>';
            });
        }

        panel.innerHTML = html;

        // Bind all toggle events
        panel.querySelectorAll("input[data-layer-key]").forEach(function(cb) {
            cb.addEventListener("change", function() {
                if (DMP.map.setAdminBoundaryVisibility) {
                    DMP.map.setAdminBoundaryVisibility(this.dataset.layerKey, this.checked);
                }
            });
        });

        return panel;
    }

    function buildGeographicTree(personnel) {
        _container.innerHTML = "";
        if (!personnel.length) return _showEmpty();

        // Admin boundary control panel
        _container.appendChild(_buildAdminBoundaryPanel());

        var grouped = {};
        personnel.forEach(function(p) {
            var dist = p.district_name || "State Level";
            var mandal = p.mandal_name || "(District/State HQ)";
            var cat = p.category || "Uncategorized";
            if (!grouped[dist]) grouped[dist] = {};
            if (!grouped[dist][mandal]) grouped[dist][mandal] = {};
            if (!grouped[dist][mandal][cat]) grouped[dist][mandal][cat] = [];
            grouped[dist][mandal][cat].push(p);
        });

        var sortedDists = Object.keys(grouped).sort(function(a, b) {
            if (a === "State Level") return -1;
            if (b === "State Level") return 1;
            return a.localeCompare(b);
        });

        sortedDists.forEach(function(dist) {
            var distCount = 0;
            Object.values(grouped[dist]).forEach(function(mandals) {
                Object.values(mandals).forEach(function(arr) { distCount += arr.length; });
            });

            var distId = _uid("gd");
            var distNode = _makeNode(0, dist, distCount, null, distId);
            _container.appendChild(distNode);
            var distChildren = document.getElementById(distId);

            // Add click-to-zoom on district node header
            if (dist !== "State Level") {
                var distHeader = distNode.querySelector(".tree-node");
                if (distHeader) {
                    distHeader.dataset.geoDistrict = dist;
                    distHeader.title = "Click to expand \u2022 Double-click to zoom to " + dist;
                }
            }

            Object.keys(grouped[dist]).sort(function(a, b) {
                if (a === "(District/State HQ)") return -1;
                if (b === "(District/State HQ)") return 1;
                return a.localeCompare(b);
            }).forEach(function(mandal) {
                var mandalData = grouped[dist][mandal];
                var mandalCount = 0;
                Object.values(mandalData).forEach(function(arr) { mandalCount += arr.length; });

                var mandalId = _uid("gm");
                var mandalNode = _makeNode(1, mandal, mandalCount, null, mandalId);
                distChildren.appendChild(mandalNode);
                var mandalChildren = document.getElementById(mandalId);

                // Add click-to-zoom on mandal node header
                if (mandal !== "(District/State HQ)") {
                    var mandalHeader = mandalNode.querySelector(".tree-node");
                    if (mandalHeader) {
                        mandalHeader.dataset.geoMandal = mandal;
                        mandalHeader.dataset.geoDistrict = dist;
                        mandalHeader.title = "Click to expand \u2022 Double-click to zoom to " + mandal;
                    }
                }

                Object.keys(mandalData).sort().forEach(function(cat) {
                    var persons = mandalData[cat];
                    var catColor = DMP.getCategoryColor(cat);
                    var catId = _uid("gc");
                    var catNode = _makeNode(2, cat, persons.length, catColor, catId);
                    mandalChildren.appendChild(catNode);
                    var catChildren = document.getElementById(catId);

                    _sortPersons(persons);
                    persons.forEach(function(p) { catChildren.appendChild(_makePersonEl(p)); });
                });
            });
        });

        _attachToggle(_container);
        _attachGeoZoom(_container, personnel);
        _autoExpandFirst(_container);
    }

    /** Attach double-click zoom handlers to geographic tree nodes */
    function _attachGeoZoom(container, personnel) {
        container.querySelectorAll("[data-geo-district]").forEach(function(node) {
            node.addEventListener("dblclick", function(e) {
                e.stopPropagation();
                var dist = this.dataset.geoDistrict;
                var mandal = this.dataset.geoMandal || null;
                if (DMP.map.zoomToDistrictExtent) {
                    DMP.map.zoomToDistrictExtent(dist, mandal, personnel);
                }
                // Show mandal boundaries when drilling into a district
                if (!mandal && DMP.map.setAdminBoundaryVisibility) {
                    DMP.map.setAdminBoundaryVisibility("mandal", true);
                    var cb = document.getElementById("geo-toggle-mandal");
                    if (cb) cb.checked = true;
                }
                // Show village boundaries when drilling into a mandal
                if (mandal && DMP.map.setAdminBoundaryVisibility) {
                    DMP.map.setAdminBoundaryVisibility("village", true);
                    var cb2 = document.getElementById("geo-toggle-village");
                    if (cb2) cb2.checked = true;
                }
            });
        });
    }

    // ── View Mode 3: Chain of Command View ──
    // Tree: L1 (Apex) > L2 (Dept Heads by department) > L3-L6 (by district > mandal)

    function buildCommandTree(personnel) {
        _container.innerHTML = "";
        if (!personnel.length) return _showEmpty();

        // Group by hierarchy level
        var byLevel = {};
        for (var lv = 1; lv <= 6; lv++) byLevel[lv] = [];
        personnel.forEach(function(p) {
            var level = p.hierarchy_level || 6;
            if (level < 1) level = 1;
            if (level > 6) level = 6;
            byLevel[level].push(p);
        });

        var levelColors = {
            1: [26, 54, 93], 2: [44, 82, 130], 3: [49, 130, 206],
            4: [99, 179, 237], 5: [144, 205, 244], 6: [190, 227, 248]
        };

        // ── L1: Apex State Leadership ──
        if (byLevel[1].length > 0) {
            var l1Id = _uid("coc1");
            var l1Node = _makeNode(0, "L1 \u2014 Apex / State Leadership", byLevel[1].length, levelColors[1], l1Id);
            _container.appendChild(l1Node);
            var l1Children = document.getElementById(l1Id);

            // Sub-groups: CM/Governor, CS/DGP, Ministers, Other
            var cmGov = [], ministers = [], topOfficers = [], otherL1 = [];
            byLevel[1].forEach(function(p) {
                var d = (p.designation || "").toLowerCase();
                if (/chief minister|governor/.test(d)) cmGov.push(p);
                else if (/\bminister\b/.test(d) && !/chief minister/.test(d)) ministers.push(p);
                else if (/chief secretary|director general of police|\bdgp\b/.test(d)) topOfficers.push(p);
                else otherL1.push(p);
            });

            var l1Groups = [
                { label: "Chief Minister & Governor", items: cmGov },
                { label: "Chief Secretary & DGP", items: topOfficers },
                { label: "Council of Ministers", items: ministers },
                { label: "Other Apex Officers", items: otherL1 }
            ];
            l1Groups.forEach(function(g) {
                if (!g.items.length) return;
                var gId = _uid("l1g");
                var gNode = _makeNode(1, g.label, g.items.length, null, gId);
                l1Children.appendChild(gNode);
                var gC = document.getElementById(gId);
                _sortPersons(g.items);
                g.items.forEach(function(p) { gC.appendChild(_makePersonEl(p)); });
            });
        }

        // ── L2: Department Heads & Secretaries — group by category ──
        if (byLevel[2].length > 0) {
            var l2Id = _uid("coc2");
            var l2Node = _makeNode(0, "L2 \u2014 Secretaries & Department Heads", byLevel[2].length, levelColors[2], l2Id);
            _container.appendChild(l2Node);
            var l2Children = document.getElementById(l2Id);

            var l2ByCat = {};
            byLevel[2].forEach(function(p) {
                var cat = p.category || "Uncategorized";
                if (!l2ByCat[cat]) l2ByCat[cat] = [];
                l2ByCat[cat].push(p);
            });

            Object.keys(l2ByCat).sort().forEach(function(cat) {
                var catColor = DMP.getCategoryColor(cat);
                var catId = _uid("l2c");
                var catNode = _makeNode(1, cat, l2ByCat[cat].length, catColor, catId);
                l2Children.appendChild(catNode);
                var catC = document.getElementById(catId);
                _sortPersons(l2ByCat[cat]);
                l2ByCat[cat].forEach(function(p) { catC.appendChild(_makePersonEl(p)); });
            });
        }

        // ── L3 to L6: Group by District (with Mandal sub-grouping for L5/L6) ──
        var distLevelConfigs = [
            { level: 3, label: "L3 \u2014 District Heads" },
            { level: 4, label: "L4 \u2014 Sub-District / Division" },
            { level: 5, label: "L5 \u2014 Mandal / Block Officers" },
            { level: 6, label: "L6 \u2014 Village / Field Staff" }
        ];

        distLevelConfigs.forEach(function(cfg) {
            var levelPersonnel = byLevel[cfg.level];
            if (!levelPersonnel.length) return;

            var lvId = _uid("coc" + cfg.level);
            var lvNode = _makeNode(0, cfg.label, levelPersonnel.length, levelColors[cfg.level], lvId);
            _container.appendChild(lvNode);
            var lvChildren = document.getElementById(lvId);

            // Group by district
            var byDist = {};
            levelPersonnel.forEach(function(p) {
                var dist = p.district_name || "State Level";
                if (!byDist[dist]) byDist[dist] = [];
                byDist[dist].push(p);
            });

            var sortedDists = Object.keys(byDist).sort(function(a, b) {
                if (a === "State Level") return -1;
                if (b === "State Level") return 1;
                return a.localeCompare(b);
            });

            sortedDists.forEach(function(dist) {
                var persons = byDist[dist];
                var distId = _uid("dl");
                var distNode = _makeNode(1, dist, persons.length, null, distId);
                lvChildren.appendChild(distNode);
                var distC = document.getElementById(distId);

                // For L5/L6, add mandal sub-grouping
                if (cfg.level >= 5) {
                    var byMandal = {};
                    persons.forEach(function(p) {
                        var m = p.mandal_name || "(HQ / Unassigned)";
                        if (!byMandal[m]) byMandal[m] = [];
                        byMandal[m].push(p);
                    });

                    var mandalKeys = Object.keys(byMandal).sort(function(a, b) {
                        if (a === "(HQ / Unassigned)") return -1;
                        if (b === "(HQ / Unassigned)") return 1;
                        return a.localeCompare(b);
                    });

                    mandalKeys.forEach(function(m) {
                        var mPersons = byMandal[m];
                        if (mandalKeys.length > 1 || m !== "(HQ / Unassigned)") {
                            var mId = _uid("ml");
                            var mNode = _makeNode(2, m, mPersons.length, null, mId);
                            distC.appendChild(mNode);
                            var mC = document.getElementById(mId);
                            _sortPersons(mPersons);
                            mPersons.forEach(function(p) { mC.appendChild(_makePersonEl(p)); });
                        } else {
                            _sortPersons(mPersons);
                            mPersons.forEach(function(p) { distC.appendChild(_makePersonEl(p)); });
                        }
                    });
                } else {
                    // L3/L4: Sort by category then name within district
                    persons.sort(function(a, b) {
                        return (a.category || "").localeCompare(b.category || "") ||
                               (a.person_name || "").localeCompare(b.person_name || "");
                    });
                    persons.forEach(function(p) { distC.appendChild(_makePersonEl(p)); });
                }
            });
        });

        _attachToggle(_container);
        _autoExpandFirst(_container);
    }

    // ── View Mode 4: Disaster Duty View ──
    // Tree: Disaster Name > Status > Team > Person

    function buildDisasterTree(personnel) {
        _container.innerHTML = "";

        // Filter to personnel with active disaster assignments
        var active = personnel.filter(function(p) {
            return p.disaster_name && p.disaster_duty_status && p.disaster_duty_status !== "Relieved";
        });
        var inactive = personnel.filter(function(p) {
            return !p.disaster_name || !p.disaster_duty_status || p.disaster_duty_status === "Relieved";
        });

        if (!active.length && !inactive.length) return _showEmpty();

        if (!active.length) {
            _container.innerHTML =
                '<div class="empty-state">' +
                    '<div class="icon">&#9989;</div>' +
                    '<h3>No Active Disaster Duties</h3>' +
                    '<p>' + inactive.length + ' personnel with no current assignments</p>' +
                '</div>';
            return;
        }

        // Group: disaster_name > status > team
        var grouped = {};
        active.forEach(function(p) {
            var dname = p.disaster_name;
            var status = p.disaster_duty_status || "Assigned";
            var team = p.disaster_team || "(No Team)";
            if (!grouped[dname]) grouped[dname] = {};
            if (!grouped[dname][status]) grouped[dname][status] = {};
            if (!grouped[dname][status][team]) grouped[dname][status][team] = [];
            grouped[dname][status][team].push(p);
        });

        Object.keys(grouped).sort().forEach(function(dname) {
            var disData = grouped[dname];
            var disCount = 0;
            Object.values(disData).forEach(function(statuses) {
                Object.values(statuses).forEach(function(arr) { disCount += arr.length; });
            });

            var disId = _uid("dd");
            var disNode = _makeNode(0, dname, disCount, [231, 76, 60], disId);
            _container.appendChild(disNode);
            var disChildren = document.getElementById(disId);

            var statusOrder = ["On Duty", "Assigned", "Standby", "On Leave"];
            statusOrder.forEach(function(status) {
                if (!disData[status]) return;
                var statusColor = DMP.DUTY_STATUS[status] ? DMP.DUTY_STATUS[status].color : [150, 150, 150];
                var statusCount = 0;
                Object.values(disData[status]).forEach(function(arr) { statusCount += arr.length; });

                var stId = _uid("ds");
                var stNode = _makeNode(1, status, statusCount, statusColor, stId);
                disChildren.appendChild(stNode);
                var stChildren = document.getElementById(stId);

                Object.keys(disData[status]).sort().forEach(function(team) {
                    var persons = disData[status][team];
                    if (team !== "(No Team)") {
                        var tmId = _uid("dt");
                        var tmNode = _makeNode(2, team, persons.length, null, tmId);
                        stChildren.appendChild(tmNode);
                        var tmChildren = document.getElementById(tmId);
                        _sortPersons(persons);
                        persons.forEach(function(p) { tmChildren.appendChild(_makePersonEl(p)); });
                    } else {
                        _sortPersons(persons);
                        persons.forEach(function(p) { stChildren.appendChild(_makePersonEl(p)); });
                    }
                });
            });
        });

        // Show count of inactive
        if (inactive.length) {
            var inId = _uid("di");
            var inNode = _makeNode(0, "No Active Duty", inactive.length, [180, 180, 180], inId);
            _container.appendChild(inNode);
        }

        _attachToggle(_container);
        _autoExpandFirst(_container);
    }

    /** Build tree for a given view mode */
    function build(mode, personnel) {
        switch (mode) {
            case "department": buildDepartmentTree(personnel); break;
            case "geographic": buildGeographicTree(personnel); break;
            case "command":    buildCommandTree(personnel); break;
            case "disaster":   buildDisasterTree(personnel); break;
            default:           buildDepartmentTree(personnel); break;
        }
    }

    /** Highlight a person in the tree by OID */
    function highlightPerson(oid) {
        _container.querySelectorAll(".tree-person.active").forEach(function(el) { el.classList.remove("active"); });
        var el = _container.querySelector('.tree-person[data-oid="' + oid + '"]');
        if (el) {
            el.classList.add("active");
            // Expand parents
            var parent = el.parentElement;
            while (parent && parent !== _container) {
                if (parent.classList.contains("tree-children")) {
                    parent.classList.add("open");
                    var prevSibling = parent.previousElementSibling;
                    if (prevSibling) {
                        var icon = prevSibling.querySelector(".expand-icon");
                        if (icon) icon.classList.add("expanded");
                    }
                }
                parent = parent.parentElement;
            }
            // Only scroll if the element is not visible in the tree container
            var containerRect = _container.getBoundingClientRect();
            var elRect = el.getBoundingClientRect();
            if (elRect.top < containerRect.top || elRect.bottom > containerRect.bottom) {
                el.scrollIntoView({ block: "center", behavior: "smooth" });
            }
        }
    }

    return {
        init: init,
        build: build,
        highlightPerson: highlightPerson,
        buildDepartmentTree: buildDepartmentTree,
        buildGeographicTree: buildGeographicTree,
        buildCommandTree: buildCommandTree,
        buildDisasterTree: buildDisasterTree
    };
})();
