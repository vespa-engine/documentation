---
title: vespa skills
render_with_liquid: false
---

## vespa skills

Manage Vespa AI-assistant skills

### Synopsis

Manage Vespa AI-assistant skills.

Skills teach AI coding assistants how to work with Vespa: schema authoring,
application packages, queries, feeding and more. Skills are downloaded from
https://github.com/vespa-engine/skills and installed for one or more
agent harnesses: Claude Code, Codex, Cursor and Antigravity CLI.

```
vespa skills [flags]
```

### Options

```
  -h, --help   help for skills
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

* [vespa](vespa.html)	 - The command-line tool for Vespa.ai
* [vespa skills install](vespa_skills_install.html)	 - Install Vespa AI-assistant skills
* [vespa skills list](vespa_skills_list.html)	 - List available Vespa AI-assistant skills
* [vespa skills update](vespa_skills_update.html)	 - Update previously installed Vespa AI-assistant skills

