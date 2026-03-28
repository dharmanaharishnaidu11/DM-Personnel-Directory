/* ==========================================================================
   DM Personnel Directory — Map Setup & Layer Management
   Admin boundary overlays from NP_Admin FeatureServer — latest 28-district
   boundaries, 688 mandals, 18K villages, assembly/parliament constituencies,
   revenue divisions, municipal/gram panchayat boundaries from VM2 DB.
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.map = (function() {

    var _map = null;
    var _view = null;
    var _adminLayers = {};    // keyed by ADMIN_LAYERS key name
    var _personnelLayer = null;
    var _personnelLayerView = null;
    var _highlightHandle = null;

    // ══════════════════════════════════════════════════════════════════
    // Layer definitions — renderer, visibility, labels, draw order
    // ══════════════════════════════════════════════════════════════════

    var LAYER_DEFS = {
        india_states: {
            title: "India States",
            visible: false, order: 0,
            fill: [0,0,0,0], outline: [150,150,150,0.3], width: 1.5
        },
        state: {
            title: "AP State Boundary",
            visible: true, order: 1,
            fill: [0,0,0,0], outline: [26,54,93,0.8], width: 2.5
        },
        district: {
            title: "Districts (28)",
            visible: true, order: 2,
            fill: [49,130,206,0.04], outline: [49,130,206,0.7], width: 1.8,
            labelField: "district_name",
            labelColor: [26,54,93,0.85],
            labelSize: 9, labelWeight: "bold",
            labelMinScale: 3000000, labelMaxScale: 300000
        },
        revenue_division: {
            title: "Revenue Divisions (82)",
            visible: false, order: 3,
            fill: [0,0,0,0], outline: [139,92,246,0.5], width: 1.2,
            dash: true,
            labelField: "revenue_di",
            labelColor: [100,60,180,0.7],
            labelSize: 8, labelWeight: "normal",
            labelMinScale: 1500000, labelMaxScale: 100000
        },
        parliament: {
            title: "Parliament (25)",
            visible: false, order: 4,
            fill: [0,0,0,0], outline: [192,57,43,0.4], width: 1.5,
            dash: true
        },
        assembly: {
            title: "Assembly (175)",
            visible: false, order: 5,
            fill: [0,0,0,0], outline: [230,126,34,0.4], width: 1.0,
            dash: true,
            labelField: "assembly_n",
            labelColor: [180,100,20,0.7],
            labelSize: 7, labelWeight: "normal",
            labelMinScale: 800000, labelMaxScale: 50000
        },
        mandal: {
            title: "Mandals (688)",
            visible: false, order: 6,
            fill: [0,0,0,0], outline: [120,120,120,0.5], width: 0.8,
            labelField: "mandal_name",
            labelColor: [80,80,80,0.8],
            labelSize: 8, labelWeight: "normal",
            labelMinScale: 500000, labelMaxScale: 50000
        },
        municipal: {
            title: "Municipal/ULB (112)",
            visible: false, order: 7,
            fill: [255,140,0,0.06], outline: [255,140,0,0.6], width: 1.2,
            labelField: "tn_name",
            labelColor: [200,100,0,0.8],
            labelSize: 8, labelWeight: "bold",
            labelMinScale: 600000, labelMaxScale: 20000
        },
        municipal_2025: {
            title: "New ULBs 2025 (7)",
            visible: false, order: 8,
            fill: [255,80,0,0.08], outline: [255,80,0,0.7], width: 1.5,
            labelField: "ulb_name",
            labelColor: [220,60,0,0.8],
            labelSize: 8, labelWeight: "bold",
            labelMinScale: 600000, labelMaxScale: 20000
        },
        gram_panchayat: {
            title: "Gram Panchayats (14,216)",
            visible: false, order: 9,
            fill: [0,0,0,0], outline: [38,166,154,0.35], width: 0.5,
            labelField: "pname",
            labelColor: [30,130,120,0.7],
            labelSize: 7, labelWeight: "normal",
            labelMinScale: 200000, labelMaxScale: 10000
        },
        village: {
            title: "Villages (18,392)",
            visible: false, order: 10,
            fill: [0,0,0,0], outline: [180,180,180,0.4], width: 0.5
        },
        settlement: {
            title: "Settlements (372)",
            visible: false, order: 11,
            fill: [108,92,231,0.04], outline: [108,92,231,0.4], width: 0.7
        },
        ward: {
            title: "Ward Boundaries (2,532)",
            visible: false, order: 12,
            fill: [0,0,0,0], outline: [52,152,219,0.4], width: 0.5
        },
        ward_secretariat: {
            title: "Ward Secretariats (973)",
            visible: false, order: 13,
            fill: [0,0,0,0], outline: [46,204,113,0.4], width: 0.6
        },
        // ── Point layers ──
        district_hqs: {
            title: "District HQs (28)",
            visible: false, order: 14,
            isPoint: true,
            pointColor: [26,54,93], pointSize: 10,
            labelField: "headquater",
            labelColor: [26,54,93,0.9],
            labelSize: 9, labelWeight: "bold",
            labelMinScale: 5000000, labelMaxScale: 0
        },
        mandal_hqs: {
            title: "Mandal HQs (688)",
            visible: false, order: 15,
            isPoint: true,
            pointColor: [99,99,99], pointSize: 5,
            labelField: "mandal",
            labelColor: [80,80,80,0.7],
            labelSize: 7, labelWeight: "normal",
            labelMinScale: 500000, labelMaxScale: 20000
        }
    };

    // ── Build renderer from layer def ──
    function _makeRenderer(def) {
        if (def.isPoint) {
            return {
                type: "simple",
                symbol: {
                    type: "simple-marker", style: "circle",
                    color: def.pointColor, size: def.pointSize,
                    outline: { color: [255,255,255], width: 1.5 }
                }
            };
        }
        var sym = {
            type: "simple-fill",
            color: def.fill,
            outline: { color: def.outline, width: def.width }
        };
        if (def.dash) {
            sym.outline.style = "dash";
        }
        return { type: "simple", symbol: sym };
    }

    // ── Build labeling info from layer def ──
    function _makeLabelInfo(def) {
        if (!def.labelField) return undefined;
        return [{
            labelExpression: "[" + def.labelField + "]",
            labelPlacement: "always-horizontal",
            symbol: {
                type: "text",
                color: def.labelColor || [50,50,50,0.8],
                haloColor: [255,255,255,0.9],
                haloSize: 1.5,
                font: {
                    size: def.labelSize || 8,
                    weight: def.labelWeight || "normal",
                    family: "Inter, sans-serif"
                }
            },
            minScale: def.labelMinScale || 0,
            maxScale: def.labelMaxScale || 0
        }];
    }

    // ══════════════════════════════════════════════════════════════════
    // Init
    // ══════════════════════════════════════════════════════════════════

    function init(callback) {
        require([
            "esri/Map",
            "esri/views/MapView",
            "esri/layers/FeatureLayer",
            "esri/layers/TileLayer",
            "esri/widgets/BasemapToggle",
            "esri/Basemap",
            "esri/identity/IdentityManager",
            "esri/config"
        ], function(Map, MapView, FeatureLayer, TileLayer, BasemapToggle, Basemap, IdentityManager, esriConfig) {

            esriConfig.portalUrl = DMP.config.PORTAL_URL;
            esriConfig.request.trustedServers.push("apsdmagis.ap.gov.in");

            var osmBasemap = new Basemap({
                baseLayers: [
                    new TileLayer({
                        urlTemplate: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                        copyright: "OpenStreetMap contributors"
                    })
                ],
                title: "OpenStreetMap",
                id: "osm"
            });

            DMP.auth.generateToken().then(function() {
                DMP.auth.registerWithIdentityManager(IdentityManager);
                DMP.auth.startAutoRefresh();
                _buildMap(Map, MapView, FeatureLayer, BasemapToggle, osmBasemap, callback);
            }).catch(function(err) {
                console.warn("[DMP] Auth failed, trying without:", err);
                _buildMap(Map, MapView, FeatureLayer, BasemapToggle, osmBasemap, callback);
            });
        });
    }

    function _buildMap(Map, MapView, FeatureLayer, BasemapToggle, osmBasemap, callback) {
        var baseUrl = DMP.config.ADMIN_BASE_URL;
        var ids = DMP.config.ADMIN_LAYERS;

        // ── Create all admin boundary layers sorted by draw order ──
        var sortedKeys = Object.keys(LAYER_DEFS).sort(function(a, b) {
            return LAYER_DEFS[a].order - LAYER_DEFS[b].order;
        });

        var mapLayers = [];
        sortedKeys.forEach(function(key) {
            if (ids[key] === undefined) return;  // skip if not in config
            var def = LAYER_DEFS[key];
            var layerOpts = {
                url: baseUrl + "/" + ids[key],
                title: def.title,
                visible: def.visible,
                renderer: _makeRenderer(def),
                popupEnabled: false,
                legendEnabled: false
            };
            var labelInfo = _makeLabelInfo(def);
            if (labelInfo) layerOpts.labelingInfo = labelInfo;

            _adminLayers[key] = new FeatureLayer(layerOpts);
            mapLayers.push(_adminLayers[key]);
        });

        // ── Personnel layer (on top of all boundaries) ──
        _personnelLayer = new FeatureLayer({
            url: DMP.config.PERSONNEL_URL,
            title: "DM Personnel",
            outFields: ["*"],
            popupEnabled: false,
            renderer: DMP.renderers.sectorRenderer()
        });
        mapLayers.push(_personnelLayer);

        _map = new Map({
            basemap: "gray-vector",
            layers: mapLayers
        });

        _view = new MapView({
            container: "viewDiv",
            map: _map,
            center: DMP.config.AP_CENTER,
            zoom: DMP.config.AP_ZOOM,
            constraints: { minZoom: DMP.config.MIN_ZOOM, maxZoom: DMP.config.MAX_ZOOM },
            popup: { autoOpenEnabled: false }
        });

        _view.ui.add(new BasemapToggle({ view: _view, nextBasemap: osmBasemap }), "bottom-right");

        // ── Zoom-dependent auto-visibility ──
        _view.watch("zoom", function(zoom) {
            // Mandals: auto-show at zoom 10+
            if (_adminLayers.mandal) {
                if (zoom >= 10) {
                    _adminLayers.mandal.visible = true;
                } else {
                    var distFilter = (document.getElementById("filter-district") || {}).value;
                    if (!distFilter) _adminLayers.mandal.visible = false;
                }
            }
            // Villages: auto-show at zoom 13+
            if (_adminLayers.village) {
                _adminLayers.village.visible = zoom >= 13;
            }
            // Gram panchayats: auto-show at zoom 12+
            if (_adminLayers.gram_panchayat && _adminLayers.gram_panchayat._userToggled !== true) {
                _adminLayers.gram_panchayat.visible = zoom >= 12;
            }
            // Ward boundaries: auto-show at zoom 14+
            if (_adminLayers.ward && _adminLayers.ward._userToggled !== true) {
                _adminLayers.ward.visible = zoom >= 14;
            }
        });

        // Get layer view for highlighting personnel
        _view.whenLayerView(_personnelLayer).then(function(lv) {
            _personnelLayerView = lv;
        });

        _view.when(function() {
            if (callback) callback();
        });
    }

    // ══════════════════════════════════════════════════════════════════
    // Public API
    // ══════════════════════════════════════════════════════════════════

    function loadPersonnel(callback) {
        var query = _personnelLayer.createQuery();
        query.where = "1=1";
        query.outFields = ["*"];
        query.returnGeometry = true;
        query.orderByFields = ["hierarchy_level ASC", "district_name ASC", "person_name ASC"];
        query.num = DMP.config.MAX_RECORDS;

        _personnelLayer.queryFeatures(query).then(function(result) {
            var personnel = result.features.map(function(f) {
                return Object.assign({ oid: f.attributes.OBJECTID, geometry: f.geometry }, f.attributes);
            });
            callback(null, personnel);
        }).catch(function(err) {
            callback(err, []);
        });
    }

    function setRenderer(renderer) {
        if (_personnelLayer) _personnelLayer.renderer = renderer;
    }

    function setDefinitionExpression(where) {
        if (_personnelLayer) _personnelLayer.definitionExpression = where;
    }

    function zoomTo(geometry) {
        if (_view && geometry) {
            _view.goTo({ target: geometry, zoom: 12 }, { duration: 800 });
        }
    }

    function highlight(oid) {
        if (_highlightHandle) _highlightHandle.remove();
        if (_personnelLayerView) {
            _highlightHandle = _personnelLayerView.highlight(oid);
        }
    }

    function clearHighlight() {
        if (_highlightHandle) _highlightHandle.remove();
        _highlightHandle = null;
    }

    function onClick(handler) {
        if (!_view) return;
        _view.on("click", function(event) {
            _view.hitTest(event, { include: _personnelLayer }).then(function(response) {
                if (response.results.length > 0) {
                    var oid = response.results[0].graphic.attributes.OBJECTID;
                    handler(oid);
                }
            });
        });
    }

    function showMandals(visible) {
        if (_adminLayers.mandal) _adminLayers.mandal.visible = visible;
    }

    function setAdminBoundaryVisibility(level, visible) {
        if (_adminLayers[level]) {
            _adminLayers[level].visible = visible;
            _adminLayers[level]._userToggled = true;
        }
    }

    /** Get all admin layer keys and their current visibility (for UI toggles) */
    function getAdminLayerList() {
        var list = [];
        Object.keys(LAYER_DEFS).sort(function(a, b) {
            return LAYER_DEFS[a].order - LAYER_DEFS[b].order;
        }).forEach(function(key) {
            if (_adminLayers[key]) {
                list.push({
                    key: key,
                    title: LAYER_DEFS[key].title,
                    visible: _adminLayers[key].visible,
                    isPoint: !!LAYER_DEFS[key].isPoint
                });
            }
        });
        return list;
    }

    function zoomToDistrictExtent(districtName, mandalName, personnel) {
        if (!_view || !personnel) return;

        var matching = personnel.filter(function(p) {
            if (p.district_name !== districtName) return false;
            if (mandalName && p.mandal_name !== mandalName) return false;
            return p.geometry && p.geometry.longitude && p.geometry.latitude;
        });

        if (matching.length === 0) {
            matching = personnel.filter(function(p) {
                return p.district_name === districtName && p.geometry;
            });
        }

        if (matching.length === 0) return;

        if (matching.length === 1) {
            _view.goTo({ target: matching[0].geometry, zoom: mandalName ? 13 : 11 }, { duration: 800 });
        } else {
            var xMin = Infinity, yMin = Infinity, xMax = -Infinity, yMax = -Infinity;
            matching.forEach(function(p) {
                var g = p.geometry;
                var x = g.longitude || g.x;
                var y = g.latitude || g.y;
                if (x < xMin) xMin = x;
                if (y < yMin) yMin = y;
                if (x > xMax) xMax = x;
                if (y > yMax) yMax = y;
            });
            var pad = mandalName ? 0.05 : 0.15;
            _view.goTo({
                target: {
                    type: "extent",
                    xmin: xMin - pad, ymin: yMin - pad,
                    xmax: xMax + pad, ymax: yMax + pad,
                    spatialReference: { wkid: 4326 }
                }
            }, { duration: 800 });
        }

        setAdminBoundaryVisibility("district", true);
        if (districtName && !mandalName) setAdminBoundaryVisibility("mandal", true);
        if (mandalName) {
            setAdminBoundaryVisibility("mandal", true);
            setAdminBoundaryVisibility("village", true);
        }
    }

    function getView() { return _view; }
    function getPersonnelLayer() { return _personnelLayer; }

    return {
        init: init,
        loadPersonnel: loadPersonnel,
        setRenderer: setRenderer,
        setDefinitionExpression: setDefinitionExpression,
        zoomTo: zoomTo,
        highlight: highlight,
        clearHighlight: clearHighlight,
        onClick: onClick,
        showMandals: showMandals,
        setAdminBoundaryVisibility: setAdminBoundaryVisibility,
        getAdminLayerList: getAdminLayerList,
        zoomToDistrictExtent: zoomToDistrictExtent,
        getView: getView,
        getPersonnelLayer: getPersonnelLayer
    };
})();
