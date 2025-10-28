---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa Scaling Configuration Examples"
---

This guide has a set of example configurations for content clusters using flat or grouped data distribution.
Data is distributed over nodes and groups
using a Vespa's [distribution algorithm](../reference/services-content.html#distribution).
See [Scaling Vespa](sizing-search.html) for when to use grouped or flat data distribution.
These examples illustrate common deployment patterns.
In all examples, the number of stateless [container](../jdisc/) nodes is fixed.
The examples are [services.xml](../reference/services-content.html) deployed using
[Application Packages](../application-packages.html).

Refer to the [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA) sample application for how to get started from a deployable multinode starting point.
The examples below are trimmed down for readability in the `admin` and `container` sections.
See the [appendix](#appendix-hosts-xml) for *hosts.xml* to use when testing deployments.

Also read [changing topology](/en/elasticity.html#changing-topology) and
[topology and resizing](https://cloud.vespa.ai/en/topology-and-resizing)
is intro documents before continuing.

## Flat Distribution

Flat (single group) distribution with [min-redundancy](../reference/services-content.html#min-redundancy)=3.
Data is distributed and partitioned over 9 nodes and there are 3 replicas of each document, stored on 3 different nodes.
Queries are dispatched in parallel to all nodes.
In case of a node failure, the remaining nodes will index (make ready)
and activate the *not ready* (stored) copies to restore full search coverage.

```
{% highlight xml%}


























        3













{% endhighlight %}
```

## Grouped Distribution

When using grouped distribution in an indexed content cluster, the following restrictions apply:
* There can only be a single level of leaf groups under the top group
* Each leaf group must have the same number of nodes
* The number of leaf groups must be a factor of the *redundancy*
* The [distribution partitions](../reference/services-content.html#distribution)
  must be specified such that the redundancy per group is equal

With a low number of nodes per group, it's important to remember that a node failure
will cause the data to be re-distributed to the remaining nodes
and their memory footprint and disk usage will grow
when those nodes start activating the documents originally activated on the failed node.
E.g. with 2 nodes per group, the remaining healthy node will start activating all the content,
which will cause a 2x memory and disk footprint compared with the ideal state.

The [min-node-ratio-per-group](../reference/services-content.html#min-node-ratio-per-group)
controls the data distribution behavior inside a group in cases of node failures.
This sets a lower bound on the ratio of nodes within groups
that must be online and accepting feed and query traffic,
before the entire group is automatically taken out of service from both feed and search/serving.
Once number of nodes in the group have been restored, and ideal state has been achieved,
the group will be automatically set in service.

## 9 nodes, 3 groups with 3 nodes per group

This example has 3 groups and each group index all the documents over the 3 nodes in the group.
With 3 groups there are 3 replicas in total of each document, and each replica is indexed and active.
Losing a node does not reduce search coverage.

```
{% highlight xml%}


























        3




















{% endhighlight %}
```

## 9 nodes, 9 groups with 1 node per group

This example has 9 groups and each group index all the documents on a single node.
With 9 groups there are 9 replicas in total of each document, and each replica is indexed and active.
Losing a node does not reduce search coverage.
With a single node, indexing throughput is limited by the single node performance,
as all data needs to go all nodes.

```
{% highlight xml%}


























        9
































{% endhighlight %}
```

## Serving Availability Tuning

When using flat distribution,
*soft failing nodes* is a challenge for serving with high availability and low latency.
Soft failing nodes are nodes which answers health checks from
[cluster controllers](../content/content-nodes.html)
and search container dispatch health checks,
but still experiences issues which impacts serving latency
(e.g. cpu frequency throttling due to thermal heating, memory corruptions and so forth).
In a cluster with a flat distribution,
the slowest node determines the latency,
as the query request is dispatched to all content nodes in parallel.
The probability of a soft failing node increases with the number of nodes used to distribute the data over.

Use [adaptive coverage timeout](../reference/services-content.html#coverage)
to prevent slow soft failing nodes to impact availability.
This allows the dispatcher to stop waiting for the slowest node(s).
See also [graceful search degradation](../graceful-degradation.html).

Grouped distributions are less impacted by soft failing nodes in general,
as queries are dispatched to one group at a time using a
[dispatch policy](../reference/services-content.html#dispatch-policy).
The *adaptive* policy takes group latency into account
when deciding which group the query request should be routed to.

## Changing Group Configuration

It is easy to change the group topology without service disruption,
with a few caveats - read more in [elasticity](../elasticity.html#changing-topology).

## Appendix: hosts.xml

```
{% highlight xml%}


        node0


        node1


        node2


        node3


        node4


        node5


        node6


        node7


        node8


{% endhighlight %}
```
