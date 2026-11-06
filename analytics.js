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
        // Mintlify navigates client-side and re-renders the sidebar and footer, which removes the link.
        // Put it back whenever that happens; the check is cheap since the link is usually still in place
        new MutationObserver(function () {
            if (!cookiePreferences.isConnected || cookiePreferences.parentElement === document.body) placeCookiePreferences();
        }).observe(document.body, { childList: true, subtree: true });
        window.matchMedia("(min-width: 1024px)").addEventListener("change", placeCookiePreferences);
    });

    // Skip GTM for internal users
    if (!document.cookie.split(';').some(function (cookie) { return cookie.trim() === 'vespa_internal=1'; })) {
        window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
        loadScript("https://www.googletagmanager.com/gtm.js?id=" + GTM_ID);
    }

    // "Cookie preferences" link. Styles in custom.css.
    var cookiePreferences = document.createElement("button");
    cookiePreferences.id = "vespa-cookie-preferences";
    cookiePreferences.type = "button";
    cookiePreferences.textContent = "Cookie preferences";
    cookiePreferences.addEventListener("click", function () {
        window.Osano.cm.showDrawer('osano-cm-dom-info-dialog-open');
    });

    function placeCookiePreferences() {
        // Sidebar on desktop, page footer on mobile (a fixed link would cover the "Ask a question" bar),
        // the homepage footer (index.mdx), or fixed to the screen on pages with none of these
        var sidebar = document.getElementById("sidebar");
        var parent = sidebar && getComputedStyle(sidebar).display !== "none" ? sidebar
            : document.getElementById("vespa-cookie-preferences-slot") || document.getElementById("footer") || document.body;
        if (cookiePreferences.parentElement !== parent) parent.appendChild(cookiePreferences);
    }
})();
