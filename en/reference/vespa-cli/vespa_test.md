---
render_with_liquid: false
---

## vespa test

Run a test suite, or a single test

### Synopsis

Run a test suite, or a single test

Runs all JSON test files in the specified directory, or the single JSON test file specified.

See [https://docs.vespa.ai/en/reference/testing.html for details.](https://docs.vespa.ai/en/reference/testing.html for details.)

```
vespa test test-directory-or-file [flags]
```

### Examples

```
$ vespa test src/test/application/tests/system-test
$ vespa test src/test/application/tests/system-test/feed-and-query.json
```

### Options

```
  -h, --help       help for test
  -w, --wait int   Number of seconds to wait for a service to become ready. 0 to disable (default 0)
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

