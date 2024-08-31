---
title: vespa feed
render_with_liquid: false
---

## vespa feed

Feed multiple document operations to Vespa

### Synopsis

Feed multiple document operations to Vespa.

This command can be used to feed large amounts of documents to a Vespa cluster
efficiently.

The contents of json-file must be either a JSON array or JSON objects separated by
newline (JSONL).

If json-file is a single dash ('-'), documents will be read from standard input.

Once feeding completes, metrics of the feed session are printed to standard out
in a JSON format:

- feeder.operation.count: Number of operations passed to the feeder by the user,
  not counting retries.
- feeder.seconds: Total time spent feeding.
- feeder.ok.count: Number of successful operations.
- feeder.ok.rate: Number of successful operations per second.
- feeder.error.count: Number of network errors (transport layer).
- feeder.inflight.count: Number of operations currently being sent.
- http.request.count: Number of HTTP requests made, including retries.
- http.request.bytes: Number of bytes sent.
- http.request.MBps: Request throughput measured in MB/s. This is the raw
  operation throughput, and not the network throughput,
  I.e. using compression does not affect this number.
- http.exception.count: Same as feeder.error.count. Present for compatibility
  with vespa-feed-client.
- http.response.count: Number of HTTP responses received.
- http.response.bytes: Number of bytes received.
- http.response.MBps: Response throughput measured in MB/s.
- http.response.error.count: Number of non-OK HTTP responses received.
- http.response.latency.millis.min: Lowest latency of a successful operation.
- http.response.latency.millis.avg: Average latency of successful operations.
- http.response.latency.millis.max: Highest latency of a successful operation.
- http.response.code.counts: Number of responses grouped by their HTTP code.


```
vespa feed json-file [json-file]... [flags]
```

### Examples

```
$ vespa feed docs.jsonl moredocs.json
$ cat docs.jsonl | vespa feed -
```

### Options

```
      --compression string       Whether to compress the document data when sending the HTTP request. Default is "auto", which compresses large documents. Must be "auto", "gzip" or "none" (default "auto")
      --connections int          The number of connections to use (default 8)
      --deadline int             Exit if this number of seconds elapse without any successful operations. 0 to disable (default 0)
      --header strings           Add a header to all HTTP requests, on the format 'Header: Value'. This can be specified multiple times
  -h, --help                     help for feed
      --progress int             Print stats summary at given interval, in seconds. 0 to disable (default 0)
      --route string             Target Vespa route for feed operations (default "default")
      --speedtest int            Perform a network speed test using given payload, in bytes. 0 to disable (default 0)
      --speedtest-duration int   Duration of speedtest, in seconds (default 60)
      --timeout int              Individual feed operation timeout in seconds. 0 to disable (default 0)
      --trace int                Network traffic trace level in the range [0,9]. 0 to disable (default 0)
      --verbose                  Verbose mode. Print successful operations in addition to errors
  -w, --wait int                 Number of seconds to wait for service(s) to become ready. 0 to disable (default 0)
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

* [vespa](vespa.html)	 - The command-line tool for Vespa.ai

