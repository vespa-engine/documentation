---
# Copyright Vespa.ai. All rights reserved.
title: "Metrics Reference"
---

# Metrics reference documentation

## Metric types

Metrics can be of the following types:


| Type | Explanation |
|------|---|
| Binary/Unit             | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| BINARY                   | Zero or one. Zero typically indicate "false" while one indicate "true"     |
| BUCKET                   | A chunk of documents managed by a distributor service                      |
| BUFFER                   | A buffer                                                                   |
| BYTE                     | A collection of 8 bits                                                     |
| BYTE_PER_SECOND          | A unit of storage capable of holding 8 bits                                |
| CLASS                    | A instance of a Java class                                                 |
| CONNECTION               | A link used for communication between a client and a server                |
| CONTEXT_SWITCH           | A context switch                                                           |
| DEPLOYMENT               | A deployment on hosted Vespa                                                |
| DOCUMENT                 | Vespa document, a collection of fields defined in a schema file            |
| DOCUMENTID               | A unique document identifier                                               |
| DOLLAR                   | US dollar                                                                  |
| DOLLAR_PER_HOUR          | Total current cost of the cluster in $/hr                                  |
| FAILURE                  | Failures, typically for requests, operations or nodes                      |
| FILE                     | Data file stored on the disk on a node                                     |
| FRACTION                 | A value in the range [0..1]. Higher values can occur but indicate out-of-range |
| GENERATION               | Typically, generation of configuration or application package              |
| GIGABYTE                 | One billion bytes                                                          |
| HIT                      | Document that meets query filter criteria                                  |
| HIT_PER_QUERY            | Number of hits per query over a period of time                             |
| HOST                     | Bare metal computer that contain nodes                                     |
| INSTANCE                 | Typically, tenant or application                                           |
| ITEM                     | Object or unit maintained in e.g. a queue                                  |
| MILLISECOND              | Millisecond, 1/1000 of a second                                            |
| NANOSECOND               | Nanosecond, 1/1,000,000,000 of a second                                    |
| NODE                     | (Virtual) computer that is part of a Vespa cluster                         |
| OPERATION                | A clearly defined task                                                     |
| OPERATION_PER_SECOND     | Number of operations per second                                             |
| PACKET                   | Collection of data transmitted over the network as a single unit           |
| PERCENTAGE               | A number expressed as a fraction of 100, normally in [0..100]              |
| QUERY                    | A request for matching, grouping and/or scoring documents stored in Vespa  |
| QUERY_PER_SECOND         | Number of queries per second                                               |
| RECORD                   | A collection of information, typically key/value in a transaction log      |
| REQUEST                  | A request sent from a client to a server                                   |
| RESPONSE                 | A response from a server to a client                                       |
| RESTART                  | A service or node restarts                                                 |
| ROTATION                 | Routing rotation                                                           |
| SCORE                    | Relevance score for a document                                             |
| SECOND                   | Time span of 1 second                                                      |
| SECONDS_SINCE_EPOCH      | Seconds since Unix Epoch                                                   |
| SESSION                  | A set of operations in one connection or higher-level operation            |
| TASK                     | Piece of work executed by a server, e.g. background data maintenance       |
| TENANT                   | Tenant that owns zero or more applications in managed Vespa                |
| THREAD                   | Computer thread for executing tasks, operations or queries                 |
| VCPU                     | Virtual CPU                                                                |
| VERSION                  | Software or config version                                                 |
| WAKEUP                   | Computer thread wake-ups for doing some work                               |

## Metric aggregator suffixes

Metrics are collected over a time period so a metric reading must aggregate individual samples over this period.
These are specified by adding the aggregator suffix to the metric name: <code>metric.name.aggregator</code>.

The following aggregators are available:

| Aggregator name (metric suffix) | Explanation                                                         |
|---------------------------------|---------------------------------------------------------------------|
| 95percentile                    | The 95 percentile of samples in the period                          |
| 99percentile                    | The 99 percentile of samples in the period                          |
| average                         | The average of samples in the period                                |
| count                           | The count of samples in the period                                  |
| last                            | The last value sampled in the period                                |
| max                             | The max value sampled in the period                                 |
| min                             | The min value sampled in the period                                 |
| rate                            | The count of samples divided by the length of the period in seconds |
| sum                             | The sum of the sampled values in the period                         |

## Metric sets defined in Vespa

A metric set is a collection of metrics which can be referenced for convenience.
The following metric sets are defined in Vespa.

* [Vespa Metric Set Reference](vespa-set-metrics-reference.html)
* [Default Metric Set Reference](default-set-metrics-reference.html)
* [Container Metrics Reference](container-metrics-reference.html)
* [Distributor Metrics Reference](distributor-metrics-reference.html)
* [Searchnode Metrics Reference](searchnode-metrics-reference.html)
* [Storage Metrics Reference](storage-metrics-reference.html)
* [Configserver Metrics Reference](configserver-metrics-reference.html)
* [Logd Metrics Reference](logd-metrics-reference.html)
* [Node Admin Metrics Reference](nodeadmin-metrics-reference.html)
* [Slobrok Metrics Reference](slobrok-metrics-reference.html)
* [Clustercontroller Metrics Reference](clustercontroller-metrics-reference.html)
* [Sentinel Metrics Reference](sentinel-metrics-reference.html)
* [Metric Units Reference](unit-metrics-reference.html)
