// Copyright Vespa.ai. All rights reserved.

// Cookie consent (Osano) and Google Tag Manager.
// Mintlify loads every .js file in the content directory on every page, so this runs site-wide.
// Order matters: consent defaults, then Osano, then GTM - same as _includes/htmlhead.html on the Jekyll site.
(function () {
    var OSANO_SRC = "https://cmp.osano.com/6gFOfdLuNB/06819a9e-81bf-4078-896b-32c0db4cfcb9/osano.js";
    var GTM_ID = "GTM-WM6MPVZP";

    // Production only - not on local development (mint dev), preview deployments or docs-beta
    if (window.location.hostname !== "docs.vespa.ai") return;

    if (window.__vespaAnalyticsLoaded) return;
    window.__vespaAnalyticsLoaded = true;

    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    window.gtag = window.gtag || gtag;
    gtag('consent', 'default', {
        'ad_storage': 'denied',
        'analytics_storage': 'denied',
        'ad_user_data': 'denied',
        'ad_personalization': 'denied',
        'personalization_storage': 'denied',
        'functionality_storage': 'granted',
        'security_storage': 'granted',
        'wait_for_update': 500
    });
    gtag("set", "ads_data_redaction", true);

    // Dynamically inserted scripts are async by default; async = false makes them execute in insertion order,
    // so Osano is in place before GTM runs
    function loadScript(src, onload) {
        var s = document.createElement("script");
        s.src = src;
        s.async = false;
        if (onload) s.onload = onload;
        document.head.appendChild(s);
    }

    // Shown only once Osano has loaded, so the link never does nothing
    loadScript(OSANO_SRC, function () {
        placeCookiePreferences();
        onNavigate(placeCookiePreferencesAfterRender);
        window.matchMedia("(min-width: 1024px)").addEventListener("change", placeCookiePreferences);
    });

    // Skip GTM for internal users
    if (!document.cookie.split(';').some(function (cookie) { return cookie.trim().startsWith('vespa_internal=1'); })) {
        window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
        loadScript("https://www.googletagmanager.com/gtm.js?id=" + GTM_ID);
    }

    // Mintlify navigates client-side without rerunning scripts. Not all Mintlify versions fire mintlify:navigate,
    // so also watch the History API
    function onNavigate(callback) {
        var path = location.pathname;
        function check() {
            if (location.pathname === path) return;
            path = location.pathname;
            callback();
        }
        ["pushState", "replaceState"].forEach(function (name) {
            var original = history[name];
            history[name] = function () {
                var result = original.apply(this, arguments);
                check();
                return result;
            };
        });
        window.addEventListener("popstate", check);
        window.addEventListener("mintlify:navigate", check);
    }

    // "Cookie preferences" link. Styles in custom.css.
    // The sidebar is re-rendered on navigation, which removes the link, so keep placing it until the new page settles
    function placeCookiePreferencesAfterRender() {
        var tries = 0;
        var timer = setInterval(function () {
            placeCookiePreferences();
            if (++tries >= 20) clearInterval(timer);
        }, 100);
    }

    function placeCookiePreferences() {
        var button = document.getElementById("vespa-cookie-preferences");
        if (!button) {
            button = document.createElement("button");
            button.id = "vespa-cookie-preferences";
            button.type = "button";
            button.textContent = "Cookie preferences";
            button.addEventListener("click", function () {
                window.Osano.cm.showDrawer('osano-cm-dom-info-dialog-open');
            });
        }
        // Sidebar on desktop, page footer on mobile (a fixed link would cover the "Ask a question" bar),
        // the homepage footer (index.mdx), or fixed to the screen on pages with none of these
        var sidebar = document.getElementById("sidebar");
        var parent = sidebar && getComputedStyle(sidebar).display !== "none" ? sidebar
            : document.getElementById("vespa-cookie-preferences-slot") || document.getElementById("footer") || document.body;
        if (button.parentElement !== parent) parent.appendChild(button);
    }
})();
