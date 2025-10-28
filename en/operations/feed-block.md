---
# Copyright Vespa.ai. All rights reserved.
title: "Feed block"
---

A content cluster blocks external write operations when at least one content node has reached the
[resource limit](../reference/services-content.html#resource-limits)
of disk or memory. This is done to avoid saturating resource usage on content nodes.
The *Cluster controller* monitors the resource usage of the content nodes
and decides whether to block feeding.
Transient resource usage (see details in the metrics below) is not included in the monitored usage.
This ensures that transient resource usage is covered by the resource headroom on the content nodes,
instead of leading to feed blocked due to natural fluctuations.

{% include note.html content="When running Vespa in a Docker image on a laptop,
one can easily get `[UNKNOWN(251009) @ tcp/vespa-host:19112/default]:
ReturnCode(NO_SPACE, External feed is blocked due to resource exhaustion:
in content cluster 'example': disk on node 0 [vespa-host] is 76.7% full (the configured limit is 75.0%,
effective limit lowered to 74.0% until feed unblocked)`.
Fix this by increasing allocated storage for the Docker daemon, clean up unused volumes
or remove unused Docker images." %}

HTTP clients will see *507 Server Error: Insufficient Storage* when this happens.

When feed is blocked, write operations are rejected by *Distributors*.
All Put operations and most Update operations are rejected.
These operations are still allowed:
* Remove operations
* Update [assign](../reference/document-json-format.html#assign) operations to numeric single-value fields

To remedy, add nodes to the content cluster.
The data will [auto-redistribute](../elasticity.html), and feeding is unblocked when
all content nodes are below the limits.
For self-managed Vespa you can configure [resource-limits](../reference/services-content.html#resource-limits),
although this is not recommended. Increasing them too much might lead to OOM and content nodes being unable to start.

{% include important.html content="Always **add** nodes, do not change node capacity -
this is in practise safer and quicker.
As most Vespa applications are set up on homogeneous nodes, changing node capacity can cause a full node set swap
and more data copying than just adding more nodes of the same kind.
Copying data will in itself stress nodes, adding one node is normally the smallest and safest change."%}

These [metrics](metrics.html) are used to monitor resource usage and whether feeding is blocked:

|  |  |
| --- | --- |
| cluster-controller.resource_usage.nodes_above_limit | The number of content nodes that are above one or more resource limits. When above 0, feeding is blocked. |
| content.proton.resource_usage.disk | A number between 0 and 1, indicating how much disk (of total available) is used on the content node. Transient disk used during [disk index fusion](../proton.html#disk-index-fusion) is not included. |
| content.proton.resource_usage.memory | A number between 0 and 1, indicating how much memory (of total available) is used on the content node. Transient memory used by [memory indexes](../proton.html#memory-index-flush) is not included. |

When feeding is blocked, error messages are returned in write operation replies - example:

```
ReturnCode(NO_SPACE, External feed is blocked due to resource exhaustion:
                     in content cluster 'example': memory on node 0 [my-vespa-node-0.example.com] is 82.0% full (the configured limit is 80.0%, effective limit lowered to 79.0% until feed unblocked))
```

Note that when feeding is blocked resource usage needs to decrease below another, lower limit before getting unblocked. This is to avoid
flip-flopping between blocking and unblocking feed when being near the limit. This lower limit is 1% lower than the configured limit.

The address space used by data structures in attributes (*Multivalue Mapping*, *Enum Store*, and *Tensor Store*) can also go full and block feeding -
see [attribute data structures](../attributes.html#data-structures) for details.
This will rarely happen.
The following metric is used to monitor address space usage:

|  |  |
| --- | --- |
| content.proton.documentdb.attribute.resource_usage.address_space.max | A number between 0 and 1, indicating how much address space is used by the worst attribute data structure on the content node. |

An error is returned when the address space limit (default value is 0.90) is exceeded:

```
ReturnCode(NO_SPACE, External feed is blocked due to resource exhaustion:
                     in content cluster 'example': attribute-address-space:example.ready.a1.enum-store on node 0 [my-vespa-node-0.example.com] is 91.0% full (the configured limit is 90.0%))
```

To remedy, add nodes to the content cluster to distribute documents with attributes over more nodes.
