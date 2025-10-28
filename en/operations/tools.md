---
# Copyright Vespa.ai. All rights reserved.
title: "Tools"
---

This is the command-line tools reference for various Vespa use cases.

## vespa-analyze-onnx-model

Loads an ONNX-model to analyze memory usage and infer/probe output types based on input types.

Synopsis: `vespa-analyze-onnx-model <onnx-model> [options...]`

Example (refer to [ONNX](/en/onnx.html) for more examples):

```
$ vespa-analyze-onnx-model Network.onnx
```

| Option | Description |
| --- | --- |
| --probe-types | Use onnx model to infer/probe output types based on input types |

## vespa-fbench
*vespa-fbench* is used for benchmarking the capacity of a Vespa system.
Refer to [vespa-benchmarking](/en/performance/vespa-benchmarking.html)
for usage and examples.

Multiple hostnames and ports can be used,
to distribute load round-robin to clients.

Synopsis: `vespa-fbench [options] <hostname> <port>`

Example:

```
$ vespa-fbench -n 10 -q query%03d.txt -s 300 -c 0 -o output%03d.txt -xy test.domain.com 8080
```

| Option | Description |
| --- | --- |
| -H *header* | append extra header to each get request. |
| -A *assign authority* | hostname:port. Overrides Host: header sent. |
| -a *str* | append string to each query |
| -n *numClients* | Run vespa-fbench with *numClients* clients in parallel. If not specified, vespa-fbench will use a default value of *10* clients. |
| -c *cycleTime* | each client will make a request each <num> milliseconds [1000] ('-1' -> cycle time should be twice the response time) |
| -l *limit* | minimum response size for successful requests [0] |
| -i *ignoreCount* | do not log the <num> first results. -1 means no logging [0] |
| -s *seconds* | run the test for <num> seconds. -1 means forever [60] |
| -q *queryFilePattern* | pattern defining input query files, e.g. *query%03d.txt* (the pattern is used with sprintf to generate filenames). Unless using POST, a query file has one query per line, each line starting with `/search/`:  ``` /search/?yql=select%20%2A%20from%20sources%20%2A%20where%20true ``` |
| -P | use POST for requests instead of GET. Two lines per query, format:  ``` /search/ {"yql" : "select * from sources * where true"} ```  Any line starting with "/" will be taken as a URL path, with the following lines taken as the content (these lines can NOT start with "/"). The default content type is *"Content-Type: application/json"*; see *-H*. |
| -o *outputFilePattern* | save query results to output files with the given pattern (default is not saving.) |
| -r *restartLimit* | number of times to re-use each query file. -1 means no limit [-1] |
| -m *maxLineSize* | max line size in input query files [8192]. Can not be less than the minimum [1024]. |
| -p *seconds* | Print summary every <num> seconds. Only available when installing vespa-fbench from test branch, |
| -k | Enable HTTP keep-alive. |
| -d | Base64 decode POST request content |
| -x | write benchmark data reporting to output file:  | NumHits | Number of hits returned | | NumFastHits | Number of actual document hits returned | | TotalHitCount | Total number of hits for query | | QueryHits | Hits as specified in query | | QueryOffset | Offset as specified in query | | NumErrors | Number of error hits returned | | NumGroupHits | Number of grouping hits returned | | SearchTime | Time used for searching. Entire query time for one phase search, first phase for two-phase search | | AttributeFetchTime | Time used for attribute fetching, or 0 for one phase search | | FillTime | Time used for summary fetching, or 0 for one phase search | |
| -y | write data on coverage to output file (must be used with -x).  | DocsSearched | Total number of documents in nodes searched | | NodesSearched | Total number of search nodes which were used | | FullCoverage | 1 if true, 0 if false | |
| -z | Use single query file to be distributed between clients. |
| -T *file* | CA certificate file to verify peer against. Use to benchmark https enabled port. (e.g *-T /etc/ssl/certs/ca-bundle.crt*) |
| -C *file* | Client certificate file name |
| -K *file* | Client private key file name |
| -D | Use TLS configuration from environment if T/C/K is not used |

Default output:

| connection reuse count | Indicates how many times HTTP connections were reused to issue another request. Note that this number will only be displayed if the -k switch (enable HTTP keep-alive) is used. |
| clients | Echo of the -n parameter. |
| cycle time | Echo of the -c parameter. |
| lower response limit | Echo of the -l parameter. |
| skipped requests | Number of requests that was skipped by vespa-fbench. vespa-fbench will typically skip a request if the line containing the query url exceeds a pre-defined limit. Skipped requests will have minimal impact on the statistical results. |
| failed requests | The number of failed requests. A request will be marked as failed if en error occurred while reading the result or if the result contained fewer bytes than 'lower response limit'. |
| successful requests | Number of successful requests. Each performed request is counted as either successful or failed. Skipped requests (see above) are not performed and therefore not counted. |
| cycles not held | Number of cycles not held. The cycle time is specified with the -c parameter. It defines how often a client should perform a new request. However, a client may not perform another request before the result from the previous request has been obtained. Whenever a client is unable to initiate a new request 'on time' due to not being finished with the previous request, this value will be increased. |
| minimum response time | The minimum response time. The response time is measured as the time period from just before the request is sent to the server, till the result is obtained from the server. |
| maximum response time | The maximum response time. The response time is measured as the time period from just before the request is sent to the server, till the result is obtained from the server. |
| average response time | The average response time. The response time is measured as the time period from just before the request is sent to the server, till the result is obtained from the server. |
| X percentile | The X percentile of the response time samples; a value selected such that X percent of the response time samples are below this value. In order to calculate percentiles, a histogram of response times is maintained for each client at runtime and merged after the test run ends. If a percentile value exceeds the upper bound of this histogram, it will be approximated (and thus less accurate) and marked with '(approx)'. |
| actual query rate | The average number of queries per second; QPS. |
| utilization | The percentage of time used waiting for the server to complete (successful) requests. Note that if a request fails, the utilization will drop since the client has 'wasted' the time spent on the failed request. |
| zero hit queries | The number of queries that gave zero hits in Vespa |

## vespa-makefsa

Use *vespa-makefsa* to compile a list of phrases into a *finite state automation* (FSA) file.
FSA files are used in [query phrasing and rewriting](/en/query-rewriting.html).

If input file is not specified, standard input is used.

Synopsis: `vespa-makefsa [-h] [-b] [-B] [-e] [-n] [-s bytes] [-z bytes] [-t] [-p] [-i] [-S serial] [-v] [-V] [input_file] output_file`

| Option | Description |
| --- | --- |
| -h | Help text |
| -b | Use binary input format with Base64 encoded info |
| -B | Use binary input format with raw |
| -e | Use text input format with no info (default) |
| -n | Use text input format with (unsigned) numerical info |
| -s bytes | Data size for numerical info: 1,2 or 4(default) |
| -z bytes | Data size for binary info (-B) (0 means NUL terminated) |
| -t | Use text input format |
| -p | Build automaton with perfect hash |
| -i | Ignore info string, regardless of input format |
| -S serial | Serial number |
| -v | Verbose |
| -V | Display version |

## vespa-query-profile-dump-tool

Dumps all resolved query profile properties for a set of dimension values

Synopsis:`vespa-query-profile-dump-tool dump [query-profile] [dir]? [parameters]?`

Examples:

```
dump default                           # dumps the 'default' profile non-variant values in the current dir

dump default x=x1&y=y1                 # dumps the 'default' profile resolved with dimensions values x=x1 and y=y1 in the current dir

dump default myapppackage              # dumps the 'default' profile non-variant values in myapppackage/search/query-profiles

dump default dev/myprofiles x=x1&y=y1  # dumps the 'default' profile resolved with dimensions values x=x1 and y=y1 in dev/myprofiles
```

| Option | Description |
| --- | --- |
| query-profile | Name of the query profile to dump the values of |
| dir | Path to an application package or query profile directory. Default: current dir |
| parameters | HTTP request encoded dimension keys used during resolving. Default: none |
