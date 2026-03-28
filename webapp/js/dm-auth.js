/* ==========================================================================
   DM Personnel Directory — Portal Authentication
   ========================================================================== */

window.DMP = window.DMP || {};

DMP.auth = (function() {
    var _token = null;
    var _expires = 0;
    var _refreshTimer = null;

    function generateToken() {
        var url = DMP.config.PORTAL_URL + "/sharing/rest/generateToken";
        var params = new URLSearchParams({
            username: "portaladmin",
            password: "9494501235Nn@",
            client: "referer",
            referer: window.location.origin || "https://apsdmagis.ap.gov.in",
            expiration: 120,
            f: "json"
        });

        return fetch(url, { method: "POST", body: params })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.token) {
                    _token = data.token;
                    _expires = data.expires || (Date.now() + 7200000);
                    return _token;
                }
                throw new Error("Token generation failed: " + JSON.stringify(data));
            });
    }

    function registerWithIdentityManager(IdentityManager) {
        if (!_token) return;
        IdentityManager.registerToken({ server: DMP.config.SERVER_URL.replace("/rest/services", ""), token: _token });
        IdentityManager.registerToken({ server: DMP.config.PORTAL_URL, token: _token });
    }

    function getToken() { return _token; }

    function startAutoRefresh() {
        if (_refreshTimer) clearInterval(_refreshTimer);
        _refreshTimer = setInterval(function() {
            generateToken().then(function() {
                console.log("[DMP] Token refreshed");
            }).catch(function(err) {
                console.error("[DMP] Token refresh failed:", err);
            });
        }, DMP.config.TOKEN_REFRESH_MS);
    }

    return {
        generateToken: generateToken,
        registerWithIdentityManager: registerWithIdentityManager,
        getToken: getToken,
        startAutoRefresh: startAutoRefresh
    };
})();
