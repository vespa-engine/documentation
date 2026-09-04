---
title: vespa skills list
render_with_liquid: false
---

## vespa skills list

List available Vespa AI-assistant skills

```
vespa skills list [flags]
```

### Options

```
  -f, --force   Ignore cache and force downloading the latest skills from GitHub
  -h, --help    help for list
```

### Options inherited from parent commands

```
  -a, --application string   The application to use. Format "tenant.application.instance" - instance is optional (tenant required for cloud targets)
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa skills](vespa_skills.html)	 - Manage Vespa AI-assistant skills

