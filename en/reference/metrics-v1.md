---
# Copyright Vespa.ai. All rights reserved.
title: "/metrics/v1 API reference"
---

The *node metrics API* is available on each *node* at
the metrics proxy port, default *http://host:19092/metrics/v1/values*.

Refer to [monitoring](/en/operations-selfhosted/monitoring.html)
for an overview of nodes, services and metrics APIs for self-hosted applications.

## HTTP requests

| HTTP request | metrics/v1 operation | Description |
| --- | --- | --- |
| GET |  | |
|  | Node metrics | ``` /metrics/v1/values ```   See [monitoring](/en/operations-selfhosted/monitoring.html#metrics-v1-values) for examples. |

## Request parameters

| Parameter | Type | Description |
| --- | --- | --- |
| consumer | String | Specify response [consumer](services-admin.html#consumer), i.e. set of metrics. An unknown / empty value will return the `default` metric set. Built-in:   * `default` - see [DefaultMetrics](default-set-metrics-reference.html). * `vespa` - see [VespaMetricSet](vespa-set-metrics-reference.html). |

## HTTP status codes

Non-exhaustive list of status codes:

| Code | Description |
| --- | --- |
| 200 | OK. |

## Response format

Responses are in JSON format, with the following fields:

| Element | Parent | Type | Description |
| --- | --- | --- | --- |
| services |  | Object | Root for /metrics/v1/values. Contains service objects. |
| name | services | String | Service name. |
| timestamp | services | Number | EPOCH in seconds - time of metrics fetch from service. |
| status | services | Object | Status from metrics fetch. |
| code | status | String | The status for each service is one of:  * `up` * `down` * `unknown`  `unknown` is used if the service seems to be alive, but does not report metrics. |
| description | status | String | Textual status. |
| metrics | services | Array | Array of metric objects. |
| values | metrics | Object | Set of metric-name/value pairs. |
| dimensions | metrics | Object | Set of metric dimension-name/value pairs. |
