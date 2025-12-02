---
title: vespa completion fish
render_with_liquid: false
---

## vespa completion fish

Generate the autocompletion script for fish

### Synopsis

Generate the autocompletion script for the fish shell.

To load completions in your current shell session:

	vespa completion fish | source

To load completions for every new session, execute once:

	vespa completion fish > ~/.config/fish/completions/vespa.fish

You will need to start a new shell for this setup to take effect.


```
vespa completion fish [flags]
```

### Options

```
  -h, --help              help for fish
      --no-descriptions   disable completion descriptions
```

### Options inherited from parent commands

```
  -a, --application string   The application to use (cloud only)
  -C, --cluster string       The container cluster to use. This is only required for applications with multiple clusters
  -c, --color string         Whether to use colors in output. Must be "auto", "never", or "always" (default "auto")
  -i, --instance string      The instance of the application to use (cloud only)
  -q, --quiet                Print only errors
  -t, --target string        The target platform to use. Must be "local", "cloud", "hosted" or an URL (default "local")
  -z, --zone string          The zone to use. This defaults to a dev zone (cloud only)
```

### SEE ALSO

* [vespa completion](vespa_completion.html)	 - Generate the autocompletion script for the specified shell

