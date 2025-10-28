---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa Benchmarking"
---

Benchmarking a Vespa application is essential to get an idea of
how well the test configuration performs.
Thus, benchmarking is an essential part of sizing a search cluster itself.
Benchmarking a cluster can answer the following questions:
* What throughput and latency to expect from a search node?
* Which resource is the bottleneck in the system?

These in turn indirectly answers other questions such as how many nodes are needed,
and if it will help to upgrade disk or CPU.
Thus, benchmarking will help in finding the optimal Vespa configuration,
using all resources optimally, which in turn lowers costs.

A good rule is to benchmark whenever the workload changes.
Benchmarking should also be done when adding new features to queries.

Having an understanding of the query mix and SLA will help to set the test parameters.
Before benchmarking, consider:
* What is the expected query mix?
  Having a representative query mix to test with is essential in order to get valid results.
  Splitting up in different types of queries
  is also a useful way to get an idea of which query classes are resource intensive.
* What is the expected SLA, both in terms of latency and query throughput?
* How important is real-time behavior? What is the rate of incoming documents, if any?
* Timeout, in a benchmarking scenario, is it ok for requests to time out? Default
  [timeout](/en/reference/query-language-reference.html#timeout) is 500 ms, and
  [softtimeout](/en/reference/query-api-reference.html#ranking.softtimeout.enable) is enabled.
  If the full cost of all queries are to be considered:
  + Disable soft timeout with execution parameter
    - by a [query profile](../query-profiles.html)
    - by appending: `&ranking.softtimeout.enable=false` to with the
      [vespa-fbench](#vespa-fbench) `-a` option
  + Set timeout to e.g. 5 seconds
    - Note that `timeout` in YQL takes precedence
    - Replace timeout in YQL or use the execution parameter
      [timeout](/en/reference/query-api-reference.html#timeout) as above.

If benchmarking using Vespa Cloud, see [Vespa Cloud Benchmarking](https://cloud.vespa.ai/en/benchmarking).

## vespa-fbench

Vespa provides a query load generator tool,
[vespa-fbench](/en/operations/tools.html#vespa-fbench),
to run queries and generate statistics - much like a traditional web server load generator.
It allows running any number of *clients*
(i.e. the more clients, the higher load), for any length of time,
and adjust the client response time before issuing the next query.
It outputs the throughput, max, min, and average latency,
as well as the 25, 50, 75, 90, 95, 99 and 99.9 latency percentiles.
This provides quite accurate information of how well the system manages the workload.
**Disclaimer:** *vespa-fbench* is a tool to drive load for benchmarking and tuning.
It is not a tool for finding the maximum load
or latencies in a production setting.
This is due to the way it is implemented: It is run with `-n` number of clients per run.
It is good for testing, as proton can be observed at different levels of concurrency.
In the real world, the number of clients and query arrival will follow a different distribution,
and impact 95p / 99p latency percentiles.

### Prepare queries

vespa-fbench uses *query files* for GET and POST queries -
see the [reference](/en/operations/tools.html#vespa-fbench) - examples:
*HTTP GET* requests:

```
/search/?yql=select%20%2A%20from%20sources%20%2A%20where%20true
```
*HTTP POST* requests format:

```
/search/
{"yql" : "select * from sources * where true"}
```

### Run queries

A typical vespa-fbench command looks like:

```
$ vespa-fbench -n 8 -q queries.txt -s 300 -c 0 myhost.mydomain.com 8080
```

This starts 8 clients, using requests read from `queries.txt`.
The `-s` parameter indicates that the benchmark will run for 300 seconds.
The `-c` parameter, states that each client thread should wait for 0 milliseconds between each query.
The last two parameters are container hostname and port.
Multiple hosts and ports can be provided,
and the clients will be uniformly distributed to query the containers round-robin.

A more complex example, using docker, hitting a Vespa Cloud endpoint:

```
$ docker run -v /Users/myself/tmp:/testfiles \
      -w /testfiles --entrypoint '' vespaengine/vespa \
      /opt/vespa/bin/vespa-fbench \
          -C data-plane-public-cert.pem -K data-plane-private-key.pem -T /etc/ssl/certs/ca-bundle.crt \
          -n 10 -q queries.txt -o result.txt -s 300 -c 0 \
          myapp.mytenant.aws-us-east-1c.z.vespa-app.cloud 443
```

When using a query file with HTTP POST requests (`-P` option) one also need
to pass the *Content-Type* header using the `-H` header option.

```
  $ docker run -v /Users/myself/tmp:/testfiles \
        -w /testfiles --entrypoint '' vespaengine/vespa \
        /opt/vespa/bin/vespa-fbench \
            -C data-plane-public-cert.pem -K data-plane-private-key.pem -T /etc/ssl/certs/ca-bundle.crt \
            -n 10 -P -H "Content-Type: application/json" -q queries_post.txt -o output.txt -s 300 -c 0 \
            myapp.mytenant.aws-us-east-1c.z.vespa-app.cloud 443
```

### Post Processing

After each run, a summary is written to stdout (and possibly an output file from each client) - example:

```
***************** Benchmark Summary *****************
clients:                      30
ran for:                    1800 seconds
cycle time:                    0 ms
lower response limit:          0 bytes
skipped requests:              0
failed requests:               0
successful requests:    12169514
cycles not held:        12169514
minimum response time:      0.82 ms
maximum response time:   3010.53 ms
average response time:      4.44 ms
25 percentile:              3.00 ms
50 percentile:              4.00 ms
75 percentile:              6.00 ms
90 percentile:              7.00 ms
95 percentile:              8.00 ms
99 percentile:             11.00 ms
actual query rate:       6753.90 Q/s
utilization:               99.93 %
```

Take note of the number of *failed requests*,
as a high number here can indicate that the system is overloaded,
or that the queries are invalid.
* In some modes of operation, vespa-fbench waits before sending the next query.
  "utilization" represents the time that vespa-fbench is sending queries and waiting for responses.
  For example, a 'system utilization' of 50%
  means that vespa-fbench is stress testing the system 50% of the time,
  and is doing nothing the remaining 50% of the time
* vespa-fbench latency results include network latency between the client and the Vespa instance.
  Measure and subtract network latency to obtain the true vespa query latency.

## Benchmark

Strategy: find optimal *requestthreads* number,
then find capacity by increasing number of parallel test clients:

1. Test with single client (n=1), single thread to find a *latency baseline*.
   For each test run, increase [threads](../reference/services-content.html#requestthreads):

   ```
   <content id="search" version="1.0">
     <engine>
       <proton>
         <tuning>
           <searchnode>
               <requestthreads>
                   <persearch>1</persearch>
               </requestthreads>
   ```

   use 1, 2, 4, 8, ... threads and measure query latency (vespa-fbench output)
   and CPU utilization ([metric](#metrics) - below).
   Note: after deploying the thread config change,
   [proton](../proton.html) must be restarted for new thread setting to take effect
   (look for ONLINE):

   ```
   $ vespa-stop-services && vespa-start-services && sleep 60 && vespa-proton-cmd --local getProtonStatus
      ...
     "matchengine","OK","state=ONLINE",""
     "documentdb:search","OK","state=ONLINE configstate=OK",""
   ```
2. use #threads sweet spot, then increase number of clients, observe latency and CPU.

### Metrics

The *container* nodes expose the
[/metrics/v2/values](../operations/metrics.html) interface -
use this to dump metrics during benchmarks.
Example - output all metrics from content node:

```
$ curl http://localhost:8080/metrics/v2/values | \
  jq '.nodes[] | select(.role=="content/mysearchcluster/0/0") | .node.metrics[].values'
```

Output CPU util:

```
$ curl http://localhost:8080/metrics/v2/values | \
  jq '.nodes[] | select(.role=="content/mysearchcluster/0/0") | .node.metrics[].values."cpu.util"'
```
