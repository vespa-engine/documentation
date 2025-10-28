---
# Copyright Vespa.ai. All rights reserved.
title: "/metrics/v2 API reference"
---

The *application metrics API* is available on each *node* at
the metrics proxy port, default *http://host:19092/metrics/v2/values*.
A container service on the same node as the metrics proxy might forward */metrics/v2/values*
on its own port, normally 8080.
*/metrics/v2/values* is an aggregation of the application instance nodes */metrics/v1/values*.
Refer to [monitoring](/en/operations-selfhosted/monitoring.html)
for an overview of nodes, services and metrics APIs.

## HTTP requests

| HTTP request | metrics/v2 operation | Description |
| --- | --- | --- |
| GET |  | |
|  | Application metrics | ``` /metrics/v2/values ```   See [monitoring](/en/operations-selfhosted/monitoring.html#metrics-v2-values) for examples. |

## Request parameters

| Parameter | Type | Description |
| --- | --- | --- |
| consumer | String | Specify response [consumer](services-admin.html#consumer), i.e. set of metrics. See [metrics/v1](metrics-v1.html#consumer) for details. |

## HTTP status codes

Non-exhaustive list of status codes:

| Code | Description |
| --- | --- |
| 200 | OK. |

## Response format

Responses are in JSON format, with the following fields:

| Element | Parent | Type | Description |
| --- | --- | --- | --- |
| nodes |  | Array | Root element for /metrics/v2/values. Returns an array of node objects with metrics |
| hostname | nodes | String | Node hostname. |
| role | nodes | String | Node role. |
| services | nodes | Array | Array of service objects, the are services running on the node. The `service` object is defined in [/metrics/v1/values](metrics-v1.html#metrics-v1-values). |
