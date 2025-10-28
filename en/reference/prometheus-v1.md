---
# Copyright Vespa.ai. All rights reserved.
title: "/prometheus/v1 API reference"
---

The *prometheus node metrics API* is available on each *node* at
the metrics proxy port, default *http://host:19092/prometheus/v1/values*.

This API has the same content as in */metrics/v1/values*,
in a [format](https://prometheus.io/docs/instrumenting/exposition_formats/) that can be
scraped by [Prometheus](https://prometheus.io/docs/introduction/overview/).

Refer to [monitoring](/en/operations-selfhosted/monitoring.html)
for an overview of nodes, services and metrics APIs.

## HTTP requests

| HTTP request | prometheus/v1 operation | Description |
| --- | --- | --- |
| GET |  | |
|  | Node metrics | ``` /prometheus/v1/values ```   See [monitoring](/en/operations-selfhosted/monitoring.html#prometheus-v1-values) for examples. |

## Request parameters

| Parameter | Type | Description |
| --- | --- | --- |
| consumer | String | Specify response [consumer](services-admin.html#consumer), i.e. set of metrics. An unknown / empty value will return the `default` metric set. Built-in (note: case-sensitive):   * `default` * `Vespa` |

## HTTP status codes

Non-exhaustive list of status codes:

| Code | Description |
| --- | --- |
| 200 | OK. |

## Response format

Responses are in Prometheus format, the values are the same as in
[/metrics/v1/values](metrics-v1.html#metrics-v1-values)
