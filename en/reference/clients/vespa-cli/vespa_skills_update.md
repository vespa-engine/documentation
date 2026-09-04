---
title: vespa skills update
render_with_liquid: false
---

## vespa skills update

Update previously installed Vespa AI-assistant skills

### Synopsis

Update previously installed Vespa AI-assistant skills to the latest version.

This replays whichever harness(es) and scope were used by a previous 'vespa
skills install', without prompting again. Run 'vespa skills install' first
if you haven't installed any skills yet.

If no skill names are given, every installed skill is checked for updates.

```
vespa skills update [skill]... [flags]
```

### Examples

```
$ vespa skills update
$ vespa skills update schema-authoring
```

### Options

```
  -g, --global   Only update globally installed skills
  -h, --help     help for update
  -l, --local    Only update skills installed in the current project
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

