---
# Copyright Vespa.ai. All rights reserved.
title: "Metrics"
redirect_from:
- /en/reference/metrics.html
---

Metrics for all nodes is aggregated using
*[/metrics/v2/values](../reference/metrics-v2.html#metrics-v2-values)* or
*[/prometheus/v1/values](../reference/prometheus-v1.html#prometheus-v1-values)*.
Values from these endpoints reflect the 1 minute activity immediately before the request.

Example getting a metric value from using the prometheus endpoint:

```
$ curl -s http://ENDPOINT/prometheus/v1/values/?consumer=vespa | \
  grep "vds.idealstate.merge_bucket.pending.average" | egrep -v 'HELP|TYPE'
```

{% include important.html content='Make sure to use [consumer=vespa](../reference/metrics-v1.html#consumer)
to list all metrics.' %}

Example getting a metric value using */metrics/v2/values*:

```
$ curl ENDPOINT/metrics/v2/values | \
  jq -r -c '
    .nodes[] |
    .hostname as $h |
    .services[].metrics[] |
    select(.values."content.proton.documentdb.documents.total.last") |
    [$h, .dimensions.documenttype, .values."content.proton.documentdb.documents.total.last"] |
    @tsv'

node9.vespanet	music	0
node8.vespanet	music	0
```

## Aggregating metrics

Metrics in Vespa are generated from services running on the individual nodes, and in many cases
have many recordings per metric, from within each node, with unique tag / dimension combinations.
These recordings need to be put together to contribute to the overall picture of how the system
is behaving. If this is done the right way you will be able to “zoom out” to get the bigger
picture, or to “zoom in” to see how things behave in more detail. This is very useful when
looking into possible production issues. Unfortunately it is easy to combine metrics the wrong
way, resulting in potentially significantly distorted graphs.

For each of the values (suffixes) available for the different metrics here is how we recommend
that you aggregate them to get the best use of them. The guidelines should be used both for
aggregations over time (multiple snapshot intervals) and over tag combinations.

| Suffix Name | Aggregation |
| --- | --- |
| `max` | Use the highest value available `MAX(max)`. |
| `min` | Use the lowest value available `MIN(min)`. |
| `sum` | Use the sum of all values `SUM(sum)`. |
| `count` | Use the sum of all values `SUM(count)`. |
| `average` | To generate an average value you want to do `SUM(sum) / SUM(count)` where you generate the graph. Don’t use the `average` suffix itself if you have the `sum` and `count` suffixes available. Using this will easily lead to computing averages of averages, which will easily become very distorted and noisy. |
| `last` | Avoid this except for metrics you expect to be stable, such as amount of memory available on a node, etc. This value is the last from a metrics snapshot period, hence basically a single value picked from all values during the snapshot period. Typically, very noisy for volatile metrics. It does not make sense to aggregate on this value at all, but if you must then choose a value with the same combination of tags over time. |
| `95percentile` | This value cannot be aggregated in a way that gives a mathematically correct value. But where you have to either compute the average value for the most realistic value, `AVERAGE(95percentile)`, or max if the goal is to better identify outliers, `MAX(95percentile)`. Regardless, this value is best used when considered at the most granular level, with all tag values specified. |
| `99percentile` | Same as for the `95percentile` suffix. |

## Metric-sets

Node metrics in */metrics/v1/values* are listed per service,
with a set of system metrics - example:

```
{% highlight json %}
{
    "services": [
        {
            "name": "vespa.container",
            "timestamp": 1662120754,
            "status": {
                "code": "up",
                "description": "Data collected successfully"
            },
            "metrics": [
                {
                    "values": {
                        "memory_virt": 3683172352,
                        "memory_rss": 1425416192,
                        "cpu": 2.0234722784298,
                        "cpu_util": 0.202347227843
                    },
                    "dimensions": {
                        "metrictype": "system",
                        "instance": "container",
                        "clustername": "default",
                        "vespaVersion": "8.46.19"
                    }
                },
                {
                    "values": {},
                    "dimensions": {
                        "clustername": "default",
                        "instance": "container",
                        "vespaVersion": "8.46.19"
                    }
                }
            ]
        },
{% endhighlight %}
```

The `default` metric-set is added to the system metric-set,
unless a [consumer](../reference/metrics-v1.html#consumer) request parameter
specifies a different built-in or custom metric set -
see [metric list](../reference/default-set-metrics-reference.html).

The `Vespa` metric-set has a richer set of metrics, see
[metric list](../reference/vespa-set-metrics-reference.html).

The *consumer* request parameter can also be used in
[/metrics/v2/values](../reference/metrics-v2.html) and
[/prometheus/v1/values](../reference/prometheus-v1.html).

Example minimal metric-set; system metric-set + a specific metric:

```
{% highlight xml%}








{% endhighlight %}
```

Example default metric-set and more; system metric-set + default metric-set + a built-in metric:

```
{% highlight xml%}









{% endhighlight %}
```

## Metrics names

The names of metrics emitted by Vespa typically follow this naming scheme:
`<prefix>.<service>.<component>.<suffix>`. The separator (`.` here) may differ for
different metrics integrations. Similarly, the `<prefix>` string may differ depending on your configuration.
Further some metrics have several levels of `component` names. Each metric will have a number of values associated
with them, one for each `suffix` provided by the metric. Typical suffixes include `sum`, `count` and
`max`.

## Container Metrics

Metrics from the container with description and unit can be found in the
[container metrics reference](/en/reference/container-metrics-reference.html).
The most commonly used metrics are mentioned below.

### Generic Container Metrics

These metrics are output for the server as a whole, e.g. related to resources.
Some metrics indicate memory usage, such as `mem.heap.*`, `mem.native.*`, `mem.direct.*`.
Other metrics are related to the JVM garbage collection, `jdisc.gc.count` and `jdisc.gc.ms`.

### Thread Pool Metrics

Metrics for the container thread pools.
The `jdisc.thread_pool.*` metrics have a dimension `threadpool` with thread pool name,
e.g. *default-pool* for the container's default thread pool.
See [Container Tuning](/en/performance/container-tuning.html) for details.

### HTTP Specific Metrics

These are metrics specific for HTTP.
Those metrics that are specific to a connector will have a dimension containing the TCP listen port.

Refer to [Container Metrics](/en/reference/container-metrics-reference.html)
for metrics on HTTP status response codes,
`http.status.*` or more detailed requests related to the handling of requests, `jdisc.http.*`.
Other relevant metrics include `serverNumConnections`,
`serverNumOpenConnections`,
`serverBytesReceived` and
`serverBytesSent`.

### Query Specific Metrics

For metrics related to queries please start with the `queries` and `query_latency`,
the `handled.requests` and `handled.latency`
or the `httpapi_*` metrics for more insights.

### Feed Specific Metrics

For metrics related to feeding into Vespa,
we recommend using the `feed.operations` and `feed.latency` metrics.

## Available metrics

Each of the services running in a Vespa installation maintains and reports a number of metrics.

Metrics from the container services are the most commonly used, and are listed in
[Container Metrics](../reference/container-metrics-reference.html).
You will find the metrics available there, with description and unit.

## Metrics from custom components

Add custom metrics from components like [Searchers](../searcher-development.html) and
[Document processors](../document-processing.html):

1. Add a [MetricReceiver](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/metrics/simple/MetricReceiver.html) instance to the constructor of the component -
   it is [injected](../jdisc/injecting-components.html) by the Container.
2. Declare [Gauge](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/metrics/simple/Gauge.html)
   and [Counter](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/metrics/simple/Counter.html) metrics using the *declare*-methods on the *MetricReceiver*.
   Optionally set arbitrary metric dimensions to default values at declaration time - refer to the javadoc for details.
3. Each time there is some data to measure, invoke the
   [sample](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/metrics/simple/Gauge.html#sample(double)) method on gauges or the
   [add](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/metrics/simple/Counter.html#add()) method on counters.
   The gauges and counters declared are inherently thread-safe.
   When sampling data, any dimensions can optionally be set.
4. Add a [consumer](../reference/services-admin.html#consumer) in *services.xml*
   for the metrics to be emitted in the metric APIs, like in the previous section.

Find a full example in the
[album-recommendation-java](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation-java) sample application.

{% include note.html content="Metrics with no value do now show in the metric APIs -
in the example above, make at least one query to set the metric value." %}

### Example / QA

I have two different libraries that are running as components with their own threads within the vespa container.
We are injecting MetricReceiver to each library.
After injecting the receiver we store the reference to this receiver in a container-wide object
so that they can be used inside these libraries
(the libraries each have several classes and such, so it is not possible to inject the receiver every time,
and we need to use the stored reference). Questions:

1. **Q:** Is the MetricReceiver object unique within the container?
   That is, if I am injecting the receiver to two different components, is always the same object getting injected?
   **A:** Yes, you get the same object.
2. **Q:** How long does an object remain valid?
   Does the same object remain valid for the life of the container
   (meaning from container booting up to the point of restart/shutdown) or can the object change?
   I ask this because we store the reference to the receiver at a common place
   so that it can be used to emit metrics elsewhere in the library where we can’t inject it,
   so I am wondering how frequently we need to update this reference.
   **A:** It remains valid for the lifetime of the component to which it got injected.
   Therefore, if you share component references through some other mean than direct or indirect injection
   you may end up with invalid references.
   A "container-wide object" sounds like trouble.
   You should have it injected into all the components that needs it instead.
   Or, if you feel that will be too fine-grained,
   create one large object which gets these things injected,
   and then have that injected into all components that need the common stuff.
