---
title: vespa skills install
render_with_liquid: false
---

## vespa skills install

Install Vespa AI-assistant skills

### Synopsis

Install Vespa AI-assistant skills for one or more agent harnesses.

Skills are downloaded from https://github.com/vespa-engine/skills and
copied into the directory the chosen harness(es) discover automatically. Run
'vespa skills list' to see available skills.

If no skill names are given, all available skills are installed. If
--harness or --local/--global are not given and the terminal is interactive,
you will be prompted to choose.

```
vespa skills install [skill]... [flags]
```

### Examples

```
$ vespa skills install
$ vespa skills install schema-authoring app-package
$ vespa skills install --harness claude,codex --local
```

### Options

```
  -f, --force             Ignore cache when downloading, and overwrite already-installed skills
  -g, --global            Install for all projects, in the user's home directory
      --harness strings   Agent harness(es) to install for (claude, codex, antigravity, cursor). Can be repeated or comma-separated
  -h, --help              help for install
  -l, --local             Install for the current project only
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

