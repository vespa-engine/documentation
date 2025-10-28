---
# Copyright Vespa.ai. All rights reserved.
title: Monitoring
category: cloud
---

![Sample Vespa Console dashboard](/assets/img/grafana-metrics.png)

The Vespa Cloud Console has dashboards for insight into performance metrics,
use the "monitoring" tab for the zone deployment.

These metrics can also be pulled into external monitoring tools using the Prometheus metrics API.

## Prometheus metrics API

Prometheus metrics are found at `$ENDPOINT/prometheus/v1/values`:

```
$ curl -s --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
  'https://vespacloud-docsearch.vespa-team.aws-us-east-1c.z.vespa-app.cloud/prometheus/v1/values'
```

The metrics can be fed into e.g. your Grafana Cloud or self-hosted Grafana instance.
See the [Vespa metrics documentation](/en/monitoring.html) for more information.

## Using Grafana

This section explains how to set up Grafana to consume Vespa metrics using the Prometheus API.

### 1. Prometheus configuration

Prometheus is configured using `prometheus.yml`, find sample config in
[prometheus](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/monitoring/album-recommendation-monitoring/prometheus).
See `prometheus-cloud.yml`,
which is designed to be easy to set up with any Vespa Cloud instance.
Replace `<Endpoint>` and `<SERVICE_NAME>` with the endpoint
for the application and the service name, respectively.
In addition, the path to the private key and public cert
that is used for the data plane to the endpoint need to be provided -
refer to [security](/en/cloud/security/guide.html).
Then, configure the Prometheus instance to use this configuration file.
The Prometheus instance will now start retrieving the metrics from Vespa Cloud.
If the Prometheus instance is used for multiple services,
append the target configuration for Vespa to scrape_configs.

### 2. Grafana configuration

Use the
[provisioning folder](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/monitoring/album-recommendation-monitoring/grafana/provisioning)
as a baseline for further configuration.

In the provisioning folder there are a few different files that all help for configuring Grafana locally.
These work as good examples of default configurations,
but the most important is the file named `Vespa-Engine-Advanced-Metrics-External.json`.
This is a default dashboard, based upon the metrics the Vespa team use to monitor performance.

Click the + button on the side and go to import.
Upload the file to the Grafana instance.
This should automatically load in the dashboard for usage.
For now, it will not display any data as no data sources are configured yet.

### 3. Grafana Data Source

The Prometheus data source has to be added to the Grafana instance for the visualisation.
Click the cog on the left and then "Data Sources".
Click "Add data source" and choose Prometheus from the list.
Add the URL for the Prometheus instance with appropriate bindings for connecting.
The configuration for the bindings will depend on how the Prometheus instance is hosted.
Once the configuration details have been entered,
click Save & Test at the bottom and ensure that Grafana says "Data source is working".

To verify the data flow,
navigate back to the Vespa Metrics dashboard by clicking the dashboard symbol on the left (4 blocks)
and clicking manage and then click Vespa Metrics.
Data should now appear in the Grafana dashboard.
If no data shows up, edit one of the data sets and ensure that it has the right data source selected.
The name of the data source the dashboard is expecting might be different from what your data source is named.
If there is still no data appearing,
it either means that the Vespa instance is not being used
or that some part of the configuration is wrong.

## Using AWS Cloudwatch

To pull metrics from your Vespa application into AWS Cloudwatch, refer to the
[metrics-emitter](https://github.com/vespa-engine/metrics-emitter/tree/master/cloudwatch) documentation
for how to set up an AWS Lambda.

## Alerting

The [Vespa Grafana Terraform template](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/monitoring/vespa-grafana-terraform)
provides a set of dashboards and alerts.
If you are using a different monitoring service and want to set up an equivalent alert set, you can follow this table:

| Metric name | Threshold | Dimension aggregation |
| --- | --- | --- |
| content_proton_resource_usage_disk_average | > 0.9 | max by(applicationId, clusterId, zone) |
| content_proton_resource_usage_memory_average | > 0.8 | max by(applicationId, zone, clusterId) |
| cpu_util | > 90 | max by(applicationId, zone, clusterId) |
| content_proton_resource_usage_feeding_blocked_last | >= 1 | N/A |

All metrics are from the [default metric set](/en/operations/metrics.html#metric-sets).
Metrics are using the naming scheme from the [Prometheus metrics](/en/reference/prometheus-v1.html) API.
Dimension aggregation is optional, but reduces alerting noise - e.g. in the case where an entire cluster goes bad.
It is recommended to filter all alerts on zones in the [prod environment](https://cloud.vespa.ai/en/reference/environments).

## Prometheus Metrics Sample

Below is a sample request with sample response for prometheus metrics for a minimal application on Vespa Cloud:

```
$ curl -s --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
  'https://feb749eb.a69b40ae.z.vespa-app.cloud/prometheus/v1/values'

...
jdisc_thread_pool_work_queue_size_min{threadpool="default-pool",zone="dev.aws-us-east-1c",applicationId="mytenant.myapp.default",serviceId="logserver-container",clusterId="admin/logserver",hostname="h97490a.dev.us-east-1c.aws.vespa-cloud.net",vespa_service="vespa_logserver_container",} 0.0 1733139324000
jdisc_thread_pool_work_queue_size_min{threadpool="default-handler-common",zone="dev.aws-us-east-1c",applicationId="mytenant.myapp.default",serviceId="logserver-container",clusterId="admin/logserver",hostname="h97490a.dev.us-east-1c.aws.vespa-cloud.net",vespa_service="vespa_logserver_container",} 0.0 1733139324000
# HELP content_proton_documentdb_matching_rank_profile_rerank_time_average
# TYPE content_proton_documentdb_matching_rank_profile_rerank_time_average untyped
content_proton_documentdb_matching_rank_profile_rerank_time_average{rankProfile="rank_albums",documenttype="music",zone="dev.aws-us-east-1c",applicationId="mytenant.myapp.default",serviceId="searchnode",clusterId="content/music",hostname="h104562a.dev.us-east-1c.aws.vespa-cloud.net",vespa_service="vespa_searchnode",} 0.0 1733139324000
content_proton_documentdb_matching_rank_profile_rerank_time_average{rankProfile="unranked",documenttype="music",zone="dev.aws-us-east-1c",applicationId="mytenant.myapp.default",serviceId="searchnode",clusterId="content/music",hostname="h104562a.dev.us-east-1c.aws.vespa-cloud.net",vespa_service="vespa_searchnode",} 0.0 1733139324000
content_proton_documentdb_matching_rank_profile_rerank_time_average{rankProfile="default",documenttype="music",zone="dev.aws-us-east-1c",applicationId="mytenant.myapp.default",serviceId="searchnode",clusterId="content/music",hostname="h104562a.dev.us-east-1c.aws.vespa-cloud.net",vespa_service="vespa_searchnode",} 0.0 1733139324000
...
```

Relevant labels include:
* `chain` This is the name on the search chain in the container that is used for a set of query requests.
  This is typically used to get separate metrics, such as latency and the number of queries for each chain over time.
* `documenttype` This is the name of the document type for which a set of queries are run in the content clusters.
  This is typically used to get separate content layer metrics, such as latency and the number of queries for each chain over time.
* `groupId` This is the id of the cluster group for which the metric measurement is done.
  This is typically used to get separate metrics aggregates per group in a content cluster.
  The label is most relevant for metrics from the content clusters running multiple content groups,
  see [Content Cluster Elasticity](/en/elasticity.html).
  The value is in the format group 0, group 1, group 2, etc.
* `rankProfile` This label is present for a subset of metrics from the content clusters,
  with names starting with `content_proton_documentdb_matching_rank_profile_`.
  The label is typically used in cases where you use multiple rank profiles
  and want to analyse performance differences between the different rank profiles,
  or to better understand certain types of performance issues and need to narrow down the candidate set.
* `source` This is a label applied on container metrics for classifying query failures by the content cluster
  where the failure was triggered.

How you will use labels to separate different kinds of queries depends on the observability backend you use,
but you will typically compute weighted averages for query latency and query volume,
and split graphs by the relevant labels to better understand system performance and bottlenecks.

For the container level metrics you use the `chain` label to differentiate between different query streams,
while you use the `rankProfile` label to do the same in the content level.
