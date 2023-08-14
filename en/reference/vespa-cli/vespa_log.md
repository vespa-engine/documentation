---
render_with_liquid: false
---

## vespa log

Show the Vespa log

### Synopsis

Show the Vespa log.

The logs shown can be limited to a relative or fixed period. All timestamps are shown in UTC.

Logs for the past hour are shown if no arguments are given.


```
vespa log [relative-period] [flags]
```

### Examples

```
$ vespa log 1h
$ vespa log --nldequote=false 10m
$ vespa log --from 2021-08-25T15:00:00Z --to 2021-08-26T02:00:00Z
$ vespa log --follow
```

### Options

```
  -f, --follow         Follow logs
  -F, --from string    Include logs since this timestamp (RFC3339 format)
  -h, --help           help for log
  -l, --level string   The maximum log level to show. Must be "error", "warning", "info" or "debug" (default "debug")
  -n, --nldequote      Dequote LF and TAB characters in log messages (default true)
  -T, --to string      Include logs until this timestamp (RFC3339 format)
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

* [vespa](vespa.html)	 - The command-line tool for Vespa.ai

