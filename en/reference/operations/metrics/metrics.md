---
# Copyright Vespa.ai. All rights reserved.
title: "Metrics Reference"
redirect_from:
  - en/reference/metrics-reference.html
---

# Metrics reference documentation

## Metric types

Each metric have one of the types documented [here](metric-units.html).

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

* [Vespa Metric Set Reference](vespa-metric-set.html)
* [Default Metric Set Reference](default-metric-set.html)
* [Metric Units Reference](metric-units.html)
* [Container Metrics Reference](container.html)
* [Distributor Metrics Reference](distributor.html)
* [Searchnode Metrics Reference](searchnode.html)
* [Storage Metrics Reference](storage.html)
* [Configserver Metrics Reference](configserver.html)
* [Logd Metrics Reference](logd.html)
* [Node Admin Metrics Reference](nodeadmin.html)
* [Slobrok Metrics Reference](slobrok.html)
* [Clustercontroller Metrics Reference](clustercontroller.html)
* [Sentinel Metrics Reference](sentinel.html)
