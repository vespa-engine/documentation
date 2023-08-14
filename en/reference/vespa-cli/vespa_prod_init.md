---
render_with_liquid: false
---

## vespa prod init

Modify service.xml and deployment.xml for production deployment

### Synopsis

Modify service.xml and deployment.xml for production deployment.

Only basic deployment configuration is available through this command. For
advanced configuration see the relevant Vespa Cloud documentation and make
changes to deployment.xml and services.xml directly.

Reference:
https://cloud.vespa.ai/en/reference/services
https://cloud.vespa.ai/en/reference/deployment

```
vespa prod init [flags]
```

### Options

```
  -h, --help   help for init
```

### Options inherited from parent commands

```
  -a, --application string   The application to use
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone
```

### SEE ALSO

* [vespa prod](vespa_prod.html)	 - Deploy an application package to production in Vespa Cloud

