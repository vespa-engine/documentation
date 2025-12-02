---
title: vespa inspect profile
render_with_liquid: false
---

## vespa inspect profile

Inspect profiling results

### Synopsis

Inspect profiling results previously obtained by vespa query --profile

Note: this feature is experimental and currently under development
profiling results can also be analyzed with vespa-query-analyzer (part of vespa installation)

```
vespa inspect profile [flags]
```

### Options

```
  -h, --help                  help for profile
  -f, --profile-file string   Name of the profile file to inspect (default "vespa_query_profile_result.json")
```

### Options inherited from parent commands

```
  -a, --application string   The application to use (cloud only). Format "tenant.application.instance" - instance is optional
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use (cloud only)
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa inspect](vespa_inspect.html)	 - Provides insight

