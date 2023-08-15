---
title: vespa completion zsh
render_with_liquid: false
---

## vespa completion zsh

Generate the autocompletion script for zsh

### Synopsis

Generate the autocompletion script for the zsh shell.

If shell completion is not already enabled in your environment you will need
to enable it.  You can execute the following once:

	echo "autoload -U compinit; compinit" >> ~/.zshrc

To load completions in your current shell session:

	source <(vespa completion zsh)

To load completions for every new session, execute once:

#### Linux:

	vespa completion zsh > "${fpath[1]}/_vespa"

#### macOS:

	vespa completion zsh > $(brew --prefix)/share/zsh/site-functions/_vespa

You will need to start a new shell for this setup to take effect.


```
vespa completion zsh [flags]
```

### Options

```
  -h, --help              help for zsh
      --no-descriptions   disable completion descriptions
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

* [vespa completion](vespa_completion.html)	 - Generate the autocompletion script for the specified shell

