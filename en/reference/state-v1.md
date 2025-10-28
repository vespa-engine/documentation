---
# Copyright Vespa.ai. All rights reserved.
title: "/state/v1 API reference"
redirect_from:
- /en/reference/state-config-inspect.html
---

Every service exposes the `/state/v1` API - use [vespa-model-inspect](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect) to find ports,
see the [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
sample application for practical examples.
Besides the endpoints listed below, a service might have additional endpoints specific to that service -
this is the case for [Proton](/en/proton.html#state-v1-api).

## HTTP requests

| HTTP request | state/v1 operation | Description |
| --- | --- | --- |
| GET |  | |
|  | Service config generation | ``` /state/v1/config ```   In the response, [config](#config) has a mandatory [generation](#generation) and one or more <service> elements:   * sentinel * container * distributor * logd * slobroks * servicelayer * proton   Note: Other configuration elements can also be added as a service. A <service> has a mandatory [generation](#generation). An optional [message](#message) can be returned. Example:   ``` {% highlight json %} {     "config": {         "generation": 11,         "slobroks": {             "generation": 11,             "message": "ok"         }     } } {% endhighlight %} ``` |
|  | Service version | ``` /state/v1/version ```   Returns a mandatory service [version](#version). Example:   ``` {% highlight json %} {     "version" : "8.43.64" } {% endhighlight %} ``` |
|  | Service health | ``` /state/v1/health ```   Returns the service status, with [time](#time), [status](#status) and [metrics](#metrics). Metrics contains `requestsPerSecond` and `latencySeconds`, see [StateHandler](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/container/jdisc/state/StateHandler.java).  Example:   ``` {% highlight json %} {     "time": 1661863544346,     "status": {         "code": "up"     },     "metrics": {         "snapshot": {             "from": 1661863483.422,             "to": 1661863543.38         },         "values": [             {                 "name": "requestsPerSecond",                 "values": {                     "count": 30,                     "rate": 0.5                 }             },             {                 "name": "latencySeconds",                 "values": {                     "average": 0.001,                     "sum": 0,                     "count": 0,                     "last": 0.001,                     "max": 0.001,                     "min": 0.001,                     "rate": 0                 }             }         ]     } } {% endhighlight %} ``` |
|  | Service metrics | ``` /state/v1/metrics ```   Same as `/state/v1/health`, but with a full metrics set.  A metric has a [name](#name) and [values](#values), and can have a [description](#description) and a set of [dimensions](#dimensions):   ``` {% highlight json %} {     "name": "content.proton.documentdb.matching.rank_profile.query_setup_time",     "description": "Average time (sec) spent setting up and tearing down queries",     "values": {         "average": 0,         "sum": 0,         "count": 0,         "rate": 0,         "min": 0,         "max": 0,         "last": 0     },     "dimensions": {         "documenttype": "music",         "rankProfile": "default"     } } {% endhighlight %} ``` |
|  | Service metric histograms | ``` /state/v1/metrics/histograms ```   See [histograms](/en/operations-selfhosted/monitoring.html#histograms) for usage. The histograms are implemented using [HdrHistogram](http://hdrhistogram.org/), and the CSV result is what that library generates. |

## HTTP status codes

Non-exhaustive list of status codes:

| Code | Description |
| --- | --- |
| 200 | OK. |

## Response format

Responses are in JSON format, with the following fields:

| Element | Parent | Type | Description |
| --- | --- | --- | --- |
| config |  | Object | Root element for /state/v1/config. |
| generation | config | Number | The generation number is the number for the config that is active in the application. |
| message | config | String | An info or error message. |
| version |  | String | Vespa version. |
| time |  | Number | Epoch in microseconds. |
| status |  | Object |  |
| code | status | String | Service status code - one of:  * up * down * initializing   Containers with the [query API](../query-api.html) enabled return `initializing` while waiting for content nodes to start, see [example](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA). `up` means that the service is fully up. Assume status `down` if no response. Refer to [StateMonitor](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/container/jdisc/state/StateMonitor.java) for implementation. |
| message | status | String | Message is optional - it is normally empty if the service is up, while it is set to a textual reason for why it is unavailable, if so. |
| metrics |  | Object | Snapshot of metric values. |
| snapshot | metrics | Object | Time period for metrics snapshot. |
| from | snapshot | Number | Epoch in seconds, with microseconds fraction. |
| to | snapshot | Number | Epoch in seconds, with microseconds fraction. |
| values | metrics | Array | Array of metric objects. |
| name | values | String | Metric name. |
| description | values | String | Textual description of the metric. |
| dimensions | values | Object | Set of dimension name/value pairs. |
| values | values | Object | Set of metric values. |
| average | values | Number | Average metric value, typically *sum* divided by *count*. |
| sum | values | Number | Sum of metric values in snapshot. |
| count | values | Number | Number of times metric has been set. For instance in a metric counting number of operations done, it will give the number of operations added for that snapshot period. For a value metric, for instance latency of operations, the count will give how many times latencies have been added to the metric. |
| last | values | Number | Last metric value. |
| max | values | Number | Max metric value in snapshot. |
| min | values | Number | Min metric value in snapshot. |
| rate | values | Number | Metric rate: *count* divided by *snapshot interval*. |
