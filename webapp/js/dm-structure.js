/* ==========================================================================
   DM Personnel Directory — Interactive Structure Editor
   Visual org chart builder: 10 Sectors → 40 Departments → 93 HODs
   Uses vis-network for interactive graph visualization
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.structure = (function() {
    "use strict";

    var _network = null;
    var _nodes = null;   // vis.DataSet
    var _edges = null;   // vis.DataSet
    var _container = null;
    var _initialized = false;
    var _selectedNodeId = null;
    var _selectedEdgeId = null;
    var _currentColorScheme = "sector";

    // ══════════════════════════════════════════════════════════════════
    // Edge type definitions — each has a distinct visual style
    // ══════════════════════════════════════════════════════════════════
    var EDGE_TYPES = {
        governance: {
            label: "Governs",
            desc: "Root governance relationship (State → Sector)",
            color: "#0c2340", width: 3, dashes: false,
            arrows: { to: { enabled: true, scaleFactor: 1.2 } }
        },
        contains: {
            label: "Contains",
            desc: "Parent-child containment (Sector → Department)",
            color: "#5f6b7a", width: 2, dashes: false,
            arrows: { to: { enabled: true, scaleFactor: 0.8 } }
        },
        sub_dept: {
            label: "Sub-Department",
            desc: "HOD under a State Department",
            color: "#8896a6", width: 1.5, dashes: [5, 5],
            arrows: { to: { enabled: true, scaleFactor: 0.6 } }
        },
        coordinates: {
            label: "Coordinates With",
            desc: "Horizontal coordination between departments",
            color: "#FF9933", width: 2, dashes: [3, 3],
            arrows: { to: { enabled: true }, from: { enabled: true } }
        },
        district_branch: {
            label: "District Branch",
            desc: "Department's district-level office",
            color: "#3182ce", width: 1.5, dashes: [8, 3, 2, 3],
            arrows: { to: { enabled: true, scaleFactor: 0.8 } }
        },
        reports_to: {
            label: "Reports To",
            desc: "Vertical reporting chain",
            color: "#e53e3e", width: 2.5, dashes: false,
            arrows: { to: { enabled: true, type: "arrow", scaleFactor: 1 } }
        },
        oversees: {
            label: "Oversees",
            desc: "Oversight / supervisory relationship",
            color: "#38a169", width: 1.5, dashes: [6, 3],
            arrows: { to: { enabled: true, scaleFactor: 0.8 } }
        },
        advisory: {
            label: "Advisory",
            desc: "Advisory / consultative relationship",
            color: "#805ad5", width: 1, dashes: [2, 4],
            arrows: { to: { enabled: true, scaleFactor: 0.5 } }
        }
    };

    // ══════════════════════════════════════════════════════════════════
    // Initialization
    // ══════════════════════════════════════════════════════════════════

    function init(containerId) {
        _container = document.getElementById(containerId);
        if (!_container) { console.error("[Structure] Container not found:", containerId); return; }
        _container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#5f6b7a;"><div class="spinner"></div>&nbsp; Loading vis-network library...</div>';
        _loadVisJS(function() {
            console.log("[Structure] vis-network loaded, vis.Network:", typeof (window.vis && window.vis.Network));
            // Allow browser to reflow/paint the container before building graph
            setTimeout(function() {
                try {
                    _buildGraph();
                    _setupControls();
                    _buildLegend();
                    _initialized = true;
                    console.log("[Structure] Initialized OK —", _nodes.length, "nodes,", _edges.length, "edges");
                } catch (err) {
                    console.error("[Structure] Build error:", err);
                    _container.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#5f6b7a;padding:24px;text-align:center;"><div style="font-size:32px;margin-bottom:8px;">&#9888;</div><b>Error building structure</b><br><small style="color:#e53e3e;">' + (err.message || err) + '</small><br><br><small>Check browser console (F12) for details</small></div>';
                }
            }, 150);
        });
    }

    function _loadVisJS(callback) {
        if (window.vis && window.vis.Network && window.vis.DataSet) return callback();
        // ArcGIS JS API loads Dojo AMD loader which defines window.define.
        // vis-network UMD wrapper sees define.amd and registers as AMD module
        // instead of assigning to window.vis. Fix: fetch as text, hide define,
        // then eval so UMD falls through to browser-global assignment.
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "js/vis-network.min.js", true);
        xhr.onload = function() {
            if (xhr.status !== 200) { _loadVisCDN(callback); return; }
            _evalVisCode(xhr.responseText);
            if (window.vis && window.vis.Network && window.vis.DataSet) {
                callback();
            } else {
                console.warn("[Structure] Local vis-network did not set globals, trying CDN");
                _loadVisCDN(callback);
            }
        };
        xhr.onerror = function() { _loadVisCDN(callback); };
        xhr.send();
    }

    function _evalVisCode(code) {
        var savedDefine = window.define;
        try {
            window.define = undefined;
            (new Function(code)).call(window);
        } catch (e) {
            console.error("[Structure] vis-network eval error:", e);
        } finally {
            window.define = savedDefine;
        }
    }

    function _loadVisCDN(callback) {
        var xhr2 = new XMLHttpRequest();
        xhr2.open("GET", "https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js", true);
        xhr2.onload = function() {
            if (xhr2.status !== 200) {
                _container.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#5f6b7a;"><div style="font-size:32px;margin-bottom:8px;">&#9888;</div><b>Could not load vis-network</b><br><small>Check internet connection</small></div>';
                return;
            }
            _evalVisCode(xhr2.responseText);
            if (window.vis && window.vis.Network && window.vis.DataSet) {
                callback();
            } else {
                _container.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#5f6b7a;"><div style="font-size:32px;margin-bottom:8px;">&#9888;</div><b>vis-network loaded but globals not set</b><br><small>Check console (F12) for details</small></div>';
            }
        };
        xhr2.onerror = function() {
            _container.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#5f6b7a;"><div style="font-size:32px;margin-bottom:8px;">&#9888;</div><b>Could not load vis-network</b><br><small>Check internet connection</small></div>';
        };
        xhr2.send();
    }

    // ══════════════════════════════════════════════════════════════════
    // Build the initial graph from DMP config
    // ══════════════════════════════════════════════════════════════════

    function _buildGraph() {
        var nodesArr = [];
        var edgesArr = [];

        // ── Root node ──
        nodesArr.push({
            id: "root",
            label: "AP State\nGovernment",
            level: 0,
            nodeType: "root",
            shape: "box",
            color: { background: "#0c2340", border: "#071528", highlight: { background: "#1a3a5c", border: "#0c2340" } },
            font: { color: "#fff", size: 16, bold: { color: "#fff" }, face: "Inter, sans-serif" },
            shadow: { enabled: true, size: 8 },
            margin: 14,
            widthConstraint: { minimum: 140 }
        });

        // ── 10 Sector nodes ──
        var sectorKeys = DMP.getSortedSectorKeys();
        sectorKeys.forEach(function(sk) {
            var sec = DMP.SECTORS[sk];
            var c = sec.color;
            var bg = "rgb(" + c.join(",") + ")";
            nodesArr.push({
                id: "sec_" + sk,
                label: sec.label,
                level: 1,
                nodeType: "sector",
                sectorKey: sk,
                shape: "box",
                color: { background: bg, border: bg, highlight: { background: bg, border: "#000" } },
                font: { color: "#fff", size: 11, bold: { color: "#fff" }, face: "Inter, sans-serif" },
                shadow: { enabled: true, size: 5 },
                margin: 10,
                widthConstraint: { minimum: 120, maximum: 200 }
            });
            edgesArr.push({
                from: "root", to: "sec_" + sk,
                edgeType: "governance",
                color: { color: "#0c2340", opacity: 0.7 },
                width: 2.5,
                arrows: { to: { enabled: true, scaleFactor: 0.8 } },
                smooth: { type: "cubicBezier" }
            });
        });

        // ── 40 Department nodes ──
        Object.keys(DMP.CATEGORIES).forEach(function(catName) {
            var cat = DMP.CATEGORIES[catName];
            var sk = cat.sector;
            var sColor = DMP.getSectorColor(sk);
            var bg = "rgba(" + sColor[0] + "," + sColor[1] + "," + sColor[2] + ",0.12)";
            var border = "rgb(" + sColor.join(",") + ")";
            var hlBg = "rgba(" + sColor[0] + "," + sColor[1] + "," + sColor[2] + ",0.3)";

            nodesArr.push({
                id: "dept_" + cat.code,
                label: "[" + cat.abbr + "] " + catName,
                level: 2,
                nodeType: "department",
                deptCode: cat.code,
                sectorKey: sk,
                catName: catName,
                shape: "box",
                color: { background: bg, border: border, highlight: { background: hlBg, border: border } },
                font: { size: 10, face: "Inter, sans-serif", color: "#1a2332" },
                shadow: { enabled: true, size: 3 },
                margin: 7,
                widthConstraint: { minimum: 100, maximum: 220 }
            });
            edgesArr.push({
                from: "sec_" + sk, to: "dept_" + cat.code,
                edgeType: "contains",
                color: { color: border, opacity: 0.5 },
                width: 1.5,
                arrows: { to: { enabled: true, scaleFactor: 0.5 } },
                smooth: { type: "cubicBezier" }
            });

            // ── HOD nodes under each department ──
            var hods = DMP.AP_HODS[cat.code] || [];
            hods.forEach(function(hodName, idx) {
                var hodId = "hod_" + cat.code + "_" + idx;
                nodesArr.push({
                    id: hodId,
                    label: hodName,
                    level: 3,
                    nodeType: "hod",
                    deptCode: cat.code,
                    sectorKey: sk,
                    hodName: hodName,
                    shape: "ellipse",
                    color: { background: "#f5f7fa", border: border, highlight: { background: "#e8ecf0", border: border } },
                    font: { size: 9, color: "#1a2332", face: "Inter, sans-serif" },
                    margin: 5
                });
                edgesArr.push({
                    from: "dept_" + cat.code, to: hodId,
                    edgeType: "sub_dept",
                    color: { color: "#8896a6", opacity: 0.4 },
                    width: 1,
                    dashes: [4, 4],
                    arrows: { to: { enabled: true, scaleFactor: 0.4 } },
                    smooth: { type: "cubicBezier" }
                });
            });
        });

        _nodes = new window.vis.DataSet(nodesArr);
        _edges = new window.vis.DataSet(edgesArr);

        var options = {
            layout: {
                hierarchical: {
                    enabled: true,
                    direction: "UD",
                    sortMethod: "directed",
                    levelSeparation: 150,
                    nodeSpacing: 200,
                    treeSpacing: 300,
                    blockShifting: true,
                    edgeMinimization: true,
                    parentCentralization: true
                }
            },
            physics: { enabled: false },
            interaction: {
                navigationButtons: true,
                keyboard: { enabled: true, bindToWindow: false },
                multiselect: true,
                hover: true,
                tooltipDelay: 300,
                zoomView: true,
                dragView: true,
                dragNodes: true
            },
            nodes: {
                borderWidth: 2,
                borderWidthSelected: 3,
                chosen: true
            },
            edges: {
                smooth: { type: "cubicBezier", forceDirection: "vertical" },
                chosen: true
            }
        };

        _network = new window.vis.Network(_container, { nodes: _nodes, edges: _edges }, options);

        // ── Event handlers ──
        _network.on("selectNode", function(params) {
            if (params.nodes.length > 0) {
                _selectedNodeId = params.nodes[0];
                _selectedEdgeId = null;
                _showNodeProps(_selectedNodeId);
            }
        });

        _network.on("selectEdge", function(params) {
            if (params.edges.length > 0 && params.nodes.length === 0) {
                _selectedEdgeId = params.edges[0];
                _selectedNodeId = null;
                _showEdgeProps(_selectedEdgeId);
            }
        });

        _network.on("deselectNode", function() {
            _selectedNodeId = null;
            _clearProps();
        });

        _network.on("deselectEdge", function() {
            _selectedEdgeId = null;
            _clearProps();
        });

        _network.on("doubleClick", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                _network.focus(nodeId, { scale: 1.5, animation: { duration: 500, easingFunction: "easeOutQuad" } });
            }
        });

        // Fit view after layout settles
        setTimeout(function() {
            _network.fit({ animation: { duration: 600, easingFunction: "easeOutQuad" } });
        }, 400);
    }

    // ══════════════════════════════════════════════════════════════════
    // Controls setup
    // ══════════════════════════════════════════════════════════════════

    function _setupControls() {
        // Layout direction
        _on("struct-layout", "change", function() { _changeLayout(this.value); });

        // Color scheme
        _on("struct-color-scheme", "change", function() { _applyColorScheme(this.value); });

        // Visibility toggles
        ["sectors", "departments", "hods"].forEach(function(type) {
            _on("struct-show-" + type, "change", function() {
                _toggleVisibility(type, this.checked);
            });
        });

        // Focus dropdowns
        var focusSec = document.getElementById("struct-focus-sector");
        var focusDept = document.getElementById("struct-focus-dept");
        if (focusSec) {
            DMP.getSortedSectorKeys().forEach(function(sk) {
                focusSec.appendChild(new Option(DMP.SECTORS[sk].label, sk));
            });
            focusSec.addEventListener("change", function() {
                if (this.value) _focusSector(this.value);
                else _network.fit({ animation: { duration: 400 } });
            });
        }
        if (focusDept) {
            var catsBySector = DMP.getCategoriesBySector();
            DMP.getSortedSectorKeys().forEach(function(sk) {
                var grp = document.createElement("optgroup");
                grp.label = DMP.SECTORS[sk].label;
                (catsBySector[sk] || []).sort().forEach(function(catName) {
                    var cat = DMP.CATEGORIES[catName];
                    grp.appendChild(new Option("[" + cat.abbr + "] " + catName, cat.code));
                });
                focusDept.appendChild(grp);
            });
            focusDept.addEventListener("change", function() {
                if (this.value) _focusDepartment(this.value);
                else _network.fit({ animation: { duration: 400 } });
            });
        }

        // Fit button
        _on("struct-fit", "click", function() {
            _network.fit({ animation: { duration: 500, easingFunction: "easeOutQuad" } });
        });

        // Add node
        _on("struct-add-node", "click", _addNode);

        // Add connection
        _on("struct-add-conn", "click", _addConnection);

        // Delete
        _on("struct-delete", "click", _deleteSelected);

        // Export
        _on("struct-export", "click", _exportJSON);

        // Populate all dropdowns
        _refreshDropdowns();
    }

    function _on(id, evt, fn) {
        var el = document.getElementById(id);
        if (el) el.addEventListener(evt, fn);
    }

    // ══════════════════════════════════════════════════════════════════
    // Dropdown population
    // ══════════════════════════════════════════════════════════════════

    function _refreshDropdowns() {
        _populateNodeDropdown("struct-conn-from", "From...");
        _populateNodeDropdown("struct-conn-to", "To...");
        _populateNodeDropdown("struct-node-parent", "No parent (root level)");

        // Edge type dropdown
        var typeSel = document.getElementById("struct-conn-type");
        if (typeSel) {
            typeSel.innerHTML = '<option value="">Connection type...</option>';
            Object.keys(EDGE_TYPES).forEach(function(et) {
                typeSel.appendChild(new Option(EDGE_TYPES[et].label + " — " + EDGE_TYPES[et].desc, et));
            });
        }
    }

    function _populateNodeDropdown(selId, placeholder) {
        var sel = document.getElementById(selId);
        if (!sel) return;
        sel.innerHTML = '<option value="">' + (placeholder || "Select...") + '</option>';

        var allNodes = _nodes.get();
        // Group by type
        var groups = { root: [], sector: [], department: [], hod: [] };
        allNodes.forEach(function(n) {
            var t = n.nodeType || "other";
            if (!groups[t]) groups[t] = [];
            groups[t].push(n);
        });

        var order = [
            { key: "root", label: "Root" },
            { key: "sector", label: "Sectors (10)" },
            { key: "department", label: "Departments (40)" },
            { key: "hod", label: "HODs (93)" }
        ];

        order.forEach(function(g) {
            var items = groups[g.key] || [];
            if (!items.length) return;
            var grp = document.createElement("optgroup");
            grp.label = g.label;
            items.sort(function(a, b) { return (a.label || "").localeCompare(b.label || ""); });
            items.forEach(function(n) {
                var label = (n.label || "").replace(/\n/g, " ");
                grp.appendChild(new Option(label, n.id));
            });
            sel.appendChild(grp);
        });

        // Custom nodes
        var customs = allNodes.filter(function(n) { return !groups[n.nodeType]; });
        if (customs.length) {
            var cGrp = document.createElement("optgroup");
            cGrp.label = "Custom Nodes";
            customs.forEach(function(n) {
                cGrp.appendChild(new Option((n.label || "").replace(/\n/g, " "), n.id));
            });
            sel.appendChild(cGrp);
        }
    }

    // ══════════════════════════════════════════════════════════════════
    // Layout changes
    // ══════════════════════════════════════════════════════════════════

    function _changeLayout(dir) {
        if (!_network) return;
        if (dir === "physics") {
            _network.setOptions({
                layout: { hierarchical: { enabled: false } },
                physics: { enabled: true, solver: "forceAtlas2Based",
                    forceAtlas2Based: { gravitationalConstant: -80, centralGravity: 0.01, springLength: 150 },
                    stabilization: { iterations: 200 }
                }
            });
        } else {
            _network.setOptions({
                layout: {
                    hierarchical: {
                        enabled: true,
                        direction: dir,
                        sortMethod: "directed",
                        levelSeparation: dir === "LR" ? 250 : 150,
                        nodeSpacing: 200,
                        treeSpacing: 300
                    }
                },
                physics: { enabled: false }
            });
        }
        setTimeout(function() { _network.fit({ animation: { duration: 500 } }); }, 600);
    }

    // ══════════════════════════════════════════════════════════════════
    // Color schemes
    // ══════════════════════════════════════════════════════════════════

    function _applyColorScheme(scheme) {
        _currentColorScheme = scheme;
        var updates = [];

        _nodes.forEach(function(n) {
            if (n.nodeType === "root") return; // root always stays dark

            var newColor;
            switch (scheme) {
                case "sector":
                    newColor = _getColorBySector(n);
                    break;
                case "level":
                    newColor = _getColorByLevel(n);
                    break;
                case "type":
                    newColor = _getColorByType(n);
                    break;
                default:
                    newColor = _getColorBySector(n);
            }
            if (newColor) updates.push({ id: n.id, color: newColor });
        });

        if (updates.length) _nodes.update(updates);
    }

    function _getColorBySector(n) {
        var sk = n.sectorKey;
        if (!sk) return null;
        var sColor = DMP.getSectorColor(sk);
        var bg, border;

        if (n.nodeType === "sector") {
            bg = "rgb(" + sColor.join(",") + ")";
            return { background: bg, border: bg, highlight: { background: bg, border: "#000" } };
        }
        if (n.nodeType === "department") {
            bg = "rgba(" + sColor[0] + "," + sColor[1] + "," + sColor[2] + ",0.12)";
            border = "rgb(" + sColor.join(",") + ")";
            return { background: bg, border: border, highlight: { background: "rgba(" + sColor[0] + "," + sColor[1] + "," + sColor[2] + ",0.3)", border: border } };
        }
        if (n.nodeType === "hod") {
            border = "rgb(" + sColor.join(",") + ")";
            return { background: "#f5f7fa", border: border, highlight: { background: "#e8ecf0", border: border } };
        }
        return null;
    }

    function _getColorByLevel(n) {
        var level = n.level || 0;
        var colors = [
            { bg: "#0c2340", border: "#071528", font: "#fff" },  // L0
            { bg: "#1a3a5c", border: "#0c2340", font: "#fff" },  // L1
            { bg: "#3182ce", border: "#2b6cb0", font: "#fff" },  // L2
            { bg: "#63b3ed", border: "#4299e1", font: "#1a2332" } // L3
        ];
        var c = colors[Math.min(level, 3)];
        return { background: c.bg, border: c.border, highlight: { background: c.bg, border: "#000" } };
    }

    function _getColorByType(n) {
        var typeColors = {
            root:       { bg: "#0c2340", border: "#071528" },
            sector:     { bg: "#e53e3e", border: "#c53030" },
            department: { bg: "#3182ce", border: "#2b6cb0" },
            hod:        { bg: "#38a169", border: "#2f855a" },
            district:   { bg: "#FF9933", border: "#e07800" },
            custom:     { bg: "#805ad5", border: "#6b46c1" }
        };
        var c = typeColors[n.nodeType] || typeColors.custom;
        return { background: c.bg, border: c.border, highlight: { background: c.bg, border: "#000" } };
    }

    // ══════════════════════════════════════════════════════════════════
    // Visibility toggles
    // ══════════════════════════════════════════════════════════════════

    function _toggleVisibility(type, visible) {
        var typeMap = { sectors: "sector", departments: "department", hods: "hod" };
        var nodeType = typeMap[type];
        if (!nodeType) return;

        var updates = [];
        _nodes.forEach(function(n) {
            if (n.nodeType === nodeType) {
                updates.push({ id: n.id, hidden: !visible });
            }
        });
        _nodes.update(updates);
    }

    // ══════════════════════════════════════════════════════════════════
    // Focus / navigation
    // ══════════════════════════════════════════════════════════════════

    function _focusSector(sectorKey) {
        var nodeId = "sec_" + sectorKey;
        var ids = [nodeId];
        _edges.forEach(function(e) {
            if (e.from === nodeId) {
                ids.push(e.to);
                // Also add HODs under each department
                _edges.forEach(function(e2) {
                    if (e2.from === e.to) ids.push(e2.to);
                });
            }
        });
        _network.selectNodes(ids);
        _network.focus(nodeId, { scale: 0.6, animation: { duration: 500, easingFunction: "easeOutQuad" } });
    }

    function _focusDepartment(deptCode) {
        var nodeId = "dept_" + deptCode;
        var ids = [nodeId];
        _edges.forEach(function(e) {
            if (e.from === nodeId) ids.push(e.to);
            if (e.to === nodeId) ids.push(e.from);
        });
        _network.selectNodes(ids);
        _network.focus(nodeId, { scale: 1.2, animation: { duration: 500, easingFunction: "easeOutQuad" } });
    }

    // ══════════════════════════════════════════════════════════════════
    // Add Node
    // ══════════════════════════════════════════════════════════════════

    function _addNode() {
        var name = (document.getElementById("struct-node-name").value || "").trim();
        var type = (document.getElementById("struct-node-type") || {}).value || "custom";
        var parent = (document.getElementById("struct-node-parent") || {}).value;

        if (!name) return _alert("Enter a node name");

        var id = type + "_c_" + Date.now();
        var nodeConfig = { id: id, label: name, nodeType: type, shadow: { enabled: true, size: 3 }, margin: 7 };

        // Inherit sector from parent if possible
        var parentNode = parent ? _nodes.get(parent) : null;
        var sectorKey = parentNode ? parentNode.sectorKey : null;

        switch (type) {
            case "department":
                var sColor = sectorKey ? DMP.getSectorColor(sectorKey) : [120, 120, 120];
                var border = "rgb(" + sColor.join(",") + ")";
                Object.assign(nodeConfig, {
                    shape: "box", level: 2,
                    color: { background: "rgba(" + sColor[0] + "," + sColor[1] + "," + sColor[2] + ",0.12)", border: border },
                    font: { size: 10, color: "#1a2332" },
                    sectorKey: sectorKey,
                    widthConstraint: { minimum: 100, maximum: 220 }
                });
                break;
            case "hod":
                var sColor2 = sectorKey ? DMP.getSectorColor(sectorKey) : [136, 150, 166];
                Object.assign(nodeConfig, {
                    shape: "ellipse", level: 3,
                    color: { background: "#f5f7fa", border: "rgb(" + sColor2.join(",") + ")" },
                    font: { size: 9, color: "#1a2332" },
                    sectorKey: sectorKey
                });
                break;
            case "district":
                Object.assign(nodeConfig, {
                    shape: "diamond", level: 3,
                    color: { background: "#ebf8ff", border: "#3182ce" },
                    font: { size: 10, color: "#1a2332" },
                    sectorKey: sectorKey
                });
                break;
            case "person":
                Object.assign(nodeConfig, {
                    shape: "dot", size: 16, level: 4,
                    color: { background: "#e8ecf0", border: "#5f6b7a" },
                    font: { size: 9, color: "#1a2332" }
                });
                break;
            default:
                Object.assign(nodeConfig, {
                    shape: "box", level: 2,
                    color: { background: "#fff", border: "#dfe3e8" },
                    font: { size: 10, color: "#1a2332" }
                });
        }

        _nodes.add(nodeConfig);

        // Connect to parent
        if (parent) {
            var edgeType = type === "hod" ? "sub_dept" : "contains";
            var et = EDGE_TYPES[edgeType];
            _edges.add({
                from: parent, to: id,
                edgeType: edgeType,
                color: { color: et.color, opacity: 0.5 },
                width: et.width,
                dashes: et.dashes || false,
                arrows: et.arrows,
                smooth: { type: "cubicBezier" }
            });
        }

        _network.focus(id, { scale: 1, animation: { duration: 500 } });
        _refreshDropdowns();

        // Clear inputs
        document.getElementById("struct-node-name").value = "";
    }

    // ══════════════════════════════════════════════════════════════════
    // Add Connection
    // ══════════════════════════════════════════════════════════════════

    function _addConnection() {
        var from = (document.getElementById("struct-conn-from") || {}).value;
        var to = (document.getElementById("struct-conn-to") || {}).value;
        var type = (document.getElementById("struct-conn-type") || {}).value;

        if (!from || !to || !type) return _alert("Select From, To, and Connection Type");
        if (from === to) return _alert("Cannot connect a node to itself");

        var et = EDGE_TYPES[type];
        if (!et) return _alert("Invalid connection type");

        _edges.add({
            from: from, to: to,
            edgeType: type,
            color: { color: et.color },
            width: et.width,
            dashes: et.dashes || false,
            arrows: et.arrows,
            label: et.label,
            font: { size: 8, color: et.color, strokeWidth: 2, strokeColor: "#fff", face: "Inter, sans-serif" }
        });

        // Select the new edge
        _network.selectNodes([from, to]);
    }

    // ══════════════════════════════════════════════════════════════════
    // Delete selected
    // ══════════════════════════════════════════════════════════════════

    function _deleteSelected() {
        var sel = _network.getSelection();
        if (sel.nodes.length === 0 && sel.edges.length === 0) return _alert("Select a node or connection first");

        if (sel.nodes.length > 0) {
            // Delete nodes and their connected edges
            sel.nodes.forEach(function(nid) {
                if (nid === "root") return; // protect root
                var connected = _network.getConnectedEdges(nid);
                _edges.remove(connected);
            });
            var toRemove = sel.nodes.filter(function(nid) { return nid !== "root"; });
            _nodes.remove(toRemove);
        }

        if (sel.edges.length > 0) {
            _edges.remove(sel.edges);
        }

        _clearProps();
        _refreshDropdowns();
    }

    // ══════════════════════════════════════════════════════════════════
    // Properties panel
    // ══════════════════════════════════════════════════════════════════

    function _showNodeProps(nodeId) {
        var node = _nodes.get(nodeId);
        if (!node) return;

        var panel = document.getElementById("struct-props-content");
        if (!panel) return;

        // Connected nodes
        var connectedIds = _network.getConnectedNodes(nodeId);
        var incoming = [], outgoing = [];
        _edges.forEach(function(e) {
            if (e.to === nodeId) {
                var fn = _nodes.get(e.from);
                incoming.push({ label: fn ? (fn.label || "").replace(/\n/g, " ") : e.from, type: e.edgeType || "?" });
            }
            if (e.from === nodeId) {
                var tn = _nodes.get(e.to);
                outgoing.push({ label: tn ? (tn.label || "").replace(/\n/g, " ") : e.to, type: e.edgeType || "?" });
            }
        });

        var html = '<div class="sp-section"><h4>Node Properties</h4></div>';
        html += _spRow("Name", _esc((node.label || "").replace(/\n/g, " ")));
        html += _spRow("Type", '<span class="sp-type-badge sp-type-' + (node.nodeType || "custom") + '">' + (node.nodeType || "custom") + '</span>');
        html += _spRow("Level", node.level !== undefined ? node.level : "—");
        html += _spRow("Shape", node.shape || "—");
        if (node.sectorKey && DMP.SECTORS[node.sectorKey]) {
            html += _spRow("Sector", DMP.SECTORS[node.sectorKey].label);
        }
        if (node.deptCode) {
            html += _spRow("Dept Code", node.deptCode);
        }

        if (incoming.length) {
            html += '<div class="sp-section"><h4>Incoming (' + incoming.length + ')</h4></div>';
            incoming.forEach(function(c) {
                html += '<div class="sp-conn-item"><span class="sp-conn-type">' + c.type + '</span> ' + _esc(c.label) + '</div>';
            });
        }
        if (outgoing.length) {
            html += '<div class="sp-section"><h4>Outgoing (' + outgoing.length + ')</h4></div>';
            outgoing.forEach(function(c) {
                html += '<div class="sp-conn-item"><span class="sp-conn-type">' + c.type + '</span> ' + _esc(c.label) + '</div>';
            });
        }

        panel.innerHTML = html;
    }

    function _showEdgeProps(edgeId) {
        var edge = _edges.get(edgeId);
        if (!edge) return;

        var panel = document.getElementById("struct-props-content");
        if (!panel) return;

        var fromNode = _nodes.get(edge.from);
        var toNode = _nodes.get(edge.to);
        var et = EDGE_TYPES[edge.edgeType];

        var html = '<div class="sp-section"><h4>Connection Properties</h4></div>';
        html += _spRow("Type", '<span class="sp-conn-type-badge" style="background:' + (et ? et.color : "#999") + '">' + (et ? et.label : edge.edgeType || "?") + '</span>');
        html += _spRow("From", _esc(fromNode ? (fromNode.label || "").replace(/\n/g, " ") : edge.from));
        html += _spRow("To", _esc(toNode ? (toNode.label || "").replace(/\n/g, " ") : edge.to));
        if (et) html += _spRow("Description", et.desc);

        panel.innerHTML = html;
    }

    function _clearProps() {
        var panel = document.getElementById("struct-props-content");
        if (panel) {
            panel.innerHTML = '<div class="sp-empty"><div class="sp-empty-icon">&#128065;</div>Click a node or connection<br>to view its properties<br><br><small>Double-click to zoom in</small></div>';
        }
    }

    function _spRow(label, value) {
        return '<div class="sp-row"><span class="sp-label">' + label + '</span><span class="sp-value">' + value + '</span></div>';
    }

    // ══════════════════════════════════════════════════════════════════
    // Legend
    // ══════════════════════════════════════════════════════════════════

    function _buildLegend() {
        var el = document.getElementById("struct-legend");
        if (!el) return;

        var html = '';
        Object.keys(EDGE_TYPES).forEach(function(key) {
            var et = EDGE_TYPES[key];
            var dashStyle = et.dashes ? "stroke-dasharray:" + (Array.isArray(et.dashes) ? et.dashes.join(",") : "4,4") : "";
            html += '<div class="sl-item">' +
                '<svg width="40" height="12" style="flex-shrink:0;">' +
                '<line x1="0" y1="6" x2="30" y2="6" stroke="' + et.color + '" stroke-width="' + Math.min(et.width, 3) + '" ' + dashStyle + '/>' +
                '<polygon points="32,6 26,2 26,10" fill="' + et.color + '"/>' +
                '</svg>' +
                '<span class="sl-label">' + et.label + '</span></div>';
        });
        el.innerHTML = html;
    }

    // ══════════════════════════════════════════════════════════════════
    // Export
    // ══════════════════════════════════════════════════════════════════

    function _exportJSON() {
        var data = {
            nodes: _nodes.get(),
            edges: _edges.get(),
            exportedAt: new Date().toISOString(),
            source: "APSDMA DM Personnel Structure Editor"
        };
        var blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = "ap_structure_" + new Date().toISOString().slice(0, 10) + ".json";
        a.click();
        URL.revokeObjectURL(url);
    }

    // ══════════════════════════════════════════════════════════════════
    // Helpers
    // ══════════════════════════════════════════════════════════════════

    function _esc(s) {
        if (!s) return "";
        return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    function _alert(msg) {
        // Use a non-blocking notification
        var el = document.getElementById("struct-alert");
        if (el) {
            el.textContent = msg;
            el.style.display = "block";
            setTimeout(function() { el.style.display = "none"; }, 3000);
        } else {
            alert(msg);
        }
    }

    // ══════════════════════════════════════════════════════════════════
    // Public API
    // ══════════════════════════════════════════════════════════════════

    function show() {
        if (!_initialized) {
            // Delay init to ensure container has layout dimensions after display:flex
            setTimeout(function() { init("structure-canvas"); }, 50);
        } else if (_network) {
            setTimeout(function() {
                _network.redraw();
                _network.fit({ animation: { duration: 400 } });
            }, 100);
        }
    }

    function hide() { /* nothing needed */ }

    return {
        init: init,
        show: show,
        hide: hide,
        EDGE_TYPES: EDGE_TYPES
    };
})();
