---
title: vespa
render_with_liquid: false
---

## vespa

The command-line tool for Vespa.ai

### Synopsis

The command-line tool for Vespa.ai.

Use it on Vespa instances running locally, remotely or in Vespa Cloud.

To get started, see the following quick start guides:

- Local Vespa instance: [https://docs.vespa.ai/en/vespa-quick-start.html](https://docs.vespa.ai/en/vespa-quick-start.html)
- Vespa Cloud: [https://cloud.vespa.ai/en/getting-started](https://cloud.vespa.ai/en/getting-started)

The complete Vespa documentation is available at https://docs.vespa.ai.

For detailed description of flags and configuration, see 'vespa help config'.


```
vespa [flags]
```

### Options

```
  -a, --application string   The application to use (cloud only). Format "tenant.application.instance" - instance is optional
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -h, --help                 help for vespa
  -i, --instance string      The instance of the application to use (cloud only)
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa activate](vespa_activate.html)	 - Activate (deploy) a previously prepared application package
* [vespa auth](vespa_auth.html)	 - Manage Vespa Cloud credentials
* [vespa clone](vespa_clone.html)	 - Create files and directory structure from a Vespa sample application
* [vespa config](vespa_config.html)	 - Manage persistent values for global flags
* [vespa curl](vespa_curl.html)	 - Access Vespa directly using curl
* [vespa deploy](vespa_deploy.html)	 - Deploy (prepare and activate) an application package
* [vespa destroy](vespa_destroy.html)	 - Remove a deployed Vespa application and its data
* [vespa document](vespa_document.html)	 - Issue a single document operation to Vespa
* [vespa feed](vespa_feed.html)	 - Feed multiple document operations to Vespa
* [vespa fetch](vespa_fetch.html)	 - Download a deployed application package
* [vespa inspect](vespa_inspect.html)	 - Provides insight
* [vespa log](vespa_log.html)	 - Show the Vespa log
* [vespa prepare](vespa_prepare.html)	 - Prepare an application package for activation
* [vespa prod](vespa_prod.html)	 - Deploy an application package to production in Vespa Cloud
* [vespa query](vespa_query.html)	 - Issue a query to Vespa
* [vespa status](vespa_status.html)	 - Show Vespa endpoints and status
* [vespa test](vespa_test.html)	 - Run a test suite, or a single test
* [vespa version](vespa_version.html)	 - Show current CLI version and check for updates
* [vespa visit](vespa_visit.html)	 - Retrieve and print all documents from Vespa

