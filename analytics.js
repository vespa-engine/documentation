// Copyright Vespa.ai. All rights reserved.

// Cookie consent (Osano) and Google Tag Manager.
// Mintlify loads every .js file in the content directory on every page, so this runs site-wide.
// Order matters: consent defaults, then Osano, then GTM - same as _includes/htmlhead.html on the Jekyll site.
(function () {
    // TODO: replace with the docs-specific Osano config once it exists
    var OSANO_SRC = "https://cmp.osano.com/6gFOfdLuNB/06819a9e-81bf-4078-896b-32c0db4cfcb9/osano.js";
    var GTM_ID = "GTM-WM6MPVZP";

    // Don't track local development (mint dev).
    // TODO: before merging, also skip Mintlify preview deployments - only run on docs.vespa.ai
    var host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1" || host === "0.0.0.0" || host === "[::1]" || host.endsWith(".local")) {
        return;
    }

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
    function loadScript(src) {
        var s = document.createElement("script");
        s.src = src;
        s.async = false;
        document.head.appendChild(s);
    }

    loadScript(OSANO_SRC);

    // Skip GTM for internal users
    if (!document.cookie.split(';').some(function (cookie) { return cookie.trim().startsWith('vespa_internal=1'); })) {
        window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
        loadScript("https://www.googletagmanager.com/gtm.js?id=" + GTM_ID);
    }

    // "Cookie Preferences" footer link (docs.json): any link to #cookie-preferences opens the Osano drawer.
    // Capture phase so this runs before the Next.js link handler navigates
    document.addEventListener("click", function (e) {
        var link = e.target.closest && e.target.closest('a[href$="#cookie-preferences"]');
        if (!link || !window.Osano || !window.Osano.cm) return;
        e.preventDefault();
        window.Osano.cm.showDrawer('osano-cm-dom-info-dialog-open');
    }, true);
})();
