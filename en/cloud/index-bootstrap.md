---
# Copyright Vespa.ai. All rights reserved.
title: Index bootstrap
category: cloud
---

When bootstrapping an index, one must consider node resource configuration and number of nodes.
The strategy is to iterate:

![Growing a Vespa cluster in steps](/assets/img/index-bootstrap.svg)

1. Feed smaller chunks of data
2. Evaluate
3. Deploy new node counts / node resource configuration
4. Wait for data migration to complete
5. Evaluate

While doing this, ensure the cluster is **never more than 50% full** -
this gives headroom to later increase/shrink the index
and change schema configuration easily using automatic reindexing.
It is easy to downscale resources after the bootstrap,
and it saves a lot of time keeping the clusters within limits - hence max 50%.

Review the [Vespa Overview](/en/overview.html) to understand
the different between *container* and *content* clusters before continuing.

## Preparations

The content node resource configuration should not have ranges for index bootstrap,
as autoscaling will interfere with the evaluation in this step.
This is a good starting point, **make sure there are no ranges like [2,3]**:

```
{% highlight xml %}



{% endhighlight %}
```

To evaluate how full the content cluster is, use [metrics](monitoring) from content nodes - example:

```
$ curl \
  --cert data-plane-public-cert.pem \
  --key  data-plane-private-key.pem \
  https://vespacloud-docsearch.vespa-team.aws-us-east-1c.z.vespa-app.cloud/prometheus/v1/values | \
  egrep 'disk.util|mem.util' | egrep 'clusterId="content/'
```

Once able to get the metrics above, you are ready to bootstrap the index.

## Bootstrap

| Step | Description |
| --- | --- |
| **1% feed** | The purpose of this step is to feed a tiny chunk of the corpus to:   1. Estimate the memory and disk resource configuration. 2. Estimate the number of nodes required for the 10% step.   Feed a small data set, using `vespa feed` as in [getting started](https://cloud.vespa.ai/en/getting-started). Observe the util metrics, stop no later than 50% memory/disk util. The resource configuration should be modified so disk is in the 50-80% range of memory. Example: if memory util is 50%, disk util should be 30-45%. The reasoning is that memory is a more expensive component than disk, better over-allocate on disk and just track memory usage.  Look at memory util. Say the 1% feed caused a 15% memory util - this means that the 10% feed will take 150%, or 3X more than the 50% max. There are two options, either increase memory/disk or add more nodes. A good rule of thumb at this stage is that the final 100% feed could fit on 4 or more nodes, and there is a 2-node minimum for redundancy. The default configuration at the start of this document is quite small, so a 3X at this stage means triple the disk and memory, and add more nodes in later steps.  Deploy changes (if needed). Whenever node count increases or resource configuration is modified, new nodes are added, and data is migrated to new nodes. Example: growing from 2 to 3 nodes means each of the 2 current nodes will migrate 33% of their data to the new node. Read more in [elasticity](/en/elasticity.html). It saves time to let the cluster finish data migration before feeding more data. In this step it will be fast as the data volume is small, but nevertheless check the [vds.idealstate.merge_bucket.pending.average](/en/reference/distributor-metrics-reference.html#vds_idealstate_merge_bucket_pending) metric. Wait for 0 for all nodes - this means data migration is completed:   ``` $ curl \   --cert ~/.vespa/mytenant.myapp.default/data-plane-public-cert.pem \   --key  ~/.vespa/mytenant.myapp.default/data-plane-private-key.pem \   https://vespacloud-docsearch.vespa-team.aws-us-east-1c.z.vespa-app.cloud/prometheus/v1/values?consumer=Vespa | \   egrep 'vds_idealstate_merge_bucket_pending_average' ```   At this point, you can validate that both memory and disk util is less than 5%, so the 10% feed will fit. |
| **10% feed** | Feed the 10% corpus, still observing util metrics.  As the content cluster capacity is increased, it is normal to eventually be CPU bound in the container or content cluster. Grep for `cpu_util` in metrics (like in the example above) to evaluate.  A 10% feed is a great baseline for the full capacity requirements. Fine tune the resource config and number of hosts as needed. If you deploy changes, wait for the `vds.idealstate.merge_bucket.pending.average` metric to go to zero again. This now takes longer time as nodes are configured larger, it normally completes within a few hours.  Again validate memory and disk util is less than 5% before the full feed. |
| **100% feed** | Feed the full data set, observing the metrics. You should be able to estimate timing by extrapolation, this is linear at this scale. At feed completion, observe the util metrics for the final fine-tuning.  A great exercise at this point is to add a node then reduce a node, and take the time to completion (`vds.idealstate.merge_bucket.pending.average` to 0). This is useful information when the application is in production, as you know the time to add or shrink capacity in advance.  It can be a good idea to reduce node count to get the memory util closer to 70% at this step, to optimize for cost. However, do not spend too much time optimizing in this step, next step is normally [sizing for query load](/en/performance/sizing-search.html). This will again possibly alter resource configuration and node counts / topology, but now you have a good grasp at how to easily bootstrap the index for these experiments. |

## Troubleshooting

Make sure you are able to feed and access documents as the example in [preparations](#preparations).
Read [security guide](/en/cloud/security/guide.html) for cert/key usage.

Feeding too much will cause a
[feed blocked](/en/operations/feed-block.html) state.
Add a node to the full content cluster in services.xml, and wait for data migration to complete -
i.e. wait for the `vds.idealstate.merge_bucket.pending.average` metric to go to zero.
It is better to add a node than increasing node resources, as data migration is quicker.

## Further reading
* [Reads and Writes](/en/reads-and-writes.html)
* [Vespa Feed Sizing Guide](/en/performance/sizing-feeding.html)
* [Vespa Cloud Benchmarking](https://cloud.vespa.ai/en/benchmarking)
* [Monitoring](https://cloud.vespa.ai/en/monitoring)
