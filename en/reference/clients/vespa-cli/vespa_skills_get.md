---
title: vespa skills get
render_with_liquid: false
---

## vespa skills get

Get the skills of a deployed application

### Synopsis

Get the skills of a deployed application.

Applications can serve skills documenting themselves to agents, such as their
schemas, at /skills/v1/. This prints the document at the given path below it,
or the list of the application's skills if no path is given. The path may also
be given in full, as documents link to each other.

Unlike the other skills commands, this gets the skills of your application,
not the general Vespa skills from GitHub.

```
vespa skills get [path] [flags]
```

### Examples

```
$ vespa skills get
$ vespa skills get schemas
$ vespa skills get schemas/music
$ vespa skills get /skills/v1/schemas/music/
```

### Options

```
  -h, --help       help for get
  -v, --verbose    Print the equivalent curl command
  -w, --wait int   Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
```

### Options inherited from parent commands

```
  -a, --application string   The application to use. Format "tenant.application.instance" - instance is optional (tenant required for cloud targets)
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use
      --progress             Show live deployment progress in interactive terminals (default true)
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa skills](vespa_skills.html)	 - Manage Vespa AI-assistant skills

