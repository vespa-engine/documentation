---
# Copyright Vespa.ai. All rights reserved.
title: "Content Cluster Elasticity"
redirect_from:
- /en/elastic-vespa.html
---

Vespa clusters can be grown and shrunk while serving queries and writes.
Documents in content clusters are automatically redistributed on changes to maintain an even distribution
with minimal data movement.
To resize, just change the [nodes](reference/services-content.html#nodes)
and redeploy the application - no restarts needed.

![A cluster growing in two dimensions](/assets/img/elastic-grow.svg)

Documents are managed by Vespa in chunks called [buckets](#buckets).
The size and number of buckets are completely managed by Vespa and there is never any
need to manually control sharding.

The elasticity mechanism is also used to recover from a node loss:
New replicas of documents are created automatically on other nodes to maintain
the configured redundancy.
Failed nodes is therefore not a problem that requires immediate attention -
clusters will self-heal from node failures as long as there are sufficient resources.

![A cluster with a node failure](/assets/img/elastic-fail.svg)

When you want to remove nodes from a content cluster, you can have the system migrate data
off them in an orderly fashion prior to removal. This is done by marking nodes as *retired*.
This is useful to remove nodes that should be retired, but also to migrate a cluster to entirely new nodes
while online: Add the new nodes, mark the old nodes retired, wait for the data to be redistributed
and remove the old nodes.

The auto-elasticity is configured for a normal fail-safe operation,
but there are tradeoffs like recovery speed and resource usage.
Learn more in [procedures](/en/operations-selfhosted/admin-procedures.html#content-cluster-configuration).

## Adding nodes

To add or remove nodes from a content cluster, just `nodes`
tag of the [content](reference/services-content.html) cluster in
[services.xml](reference/services.html)
and [redeploy](application-packages.html#deploy).
Read more in [procedures](/en/operations-selfhosted/admin-procedures.html).

When adding a new node, a new *ideal state* is calculated for all buckets.
The buckets mapped to the new node are moved, the superfluous are removed.
See redistribution example - add a new node to the system, with redundancy n=2:

![Bucket migration as a node is added to the cluster](/assets/img/add-node-move-buckets.svg)

The distribution algorithm generates a random node sequence for each bucket.
In this example with n=2, replicas map to the two nodes sorted first.
The illustration shows how placement onto two nodes changes as a third node is added.
The new node takes over as primary for the buckets where it got sorted first,
and as secondary for the buckets where it got sorted second.
This ensures minimal data movement when nodes come and go, and allows capacity to be changed easily.

No buckets are moved between the existing nodes when a new node is added.
Based on the pseudo-random sequences, some buckets change from primary to secondary, or are removed.
Multiple nodes can be added in the same deployment.

## Removing nodes

Whether a node fails or is *retired*, the same redistribution happens.
If the node is retired, replicas are generated on the other nodes
and the node stays up, but with no active replicas.
Example of redistribution after node failure, n=2:

![Bucket migration as a node is removed from the cluster](/assets/img/lose-node-move-buckets.svg)

Here, node 2 fails. This node held the active replicas of bucket 2 and 6.
Once the node fails the secondary replicas are set active.
If they were already in a *ready* state, they start serving queries immediately,
otherwise they will index replicas,
see [searchable-copies](reference/services-content.html#searchable-copies).
All buckets that no longer have secondary replicas
are merged to the remaining nodes according to the ideal state.

## Grouped distribution

Nodes in content clusters can be placed in [groups](reference/services-content.html#group).
A group of nodes in a content cluster will have one or more complete replicas of the entire document corpus.

![A cluster changes from using one to many groups](/assets/img/query-groups.svg)

This is useful in the cases listed below:

| Cluster upgrade | With multiple groups it becomes safe to take out a full group for upgrade instead of just one node at a time. [Read more](/en/operations-selfhosted/live-upgrade.html). |
| Query throughput | Applications with high query rates and/or high static query cost can use groups to scale to higher query rates since Vespa will automatically send a query to just a single group. [Read more](performance/sizing-search.html). |
| Topology | By using groups you can control replica placement over network switches or racks to ensure there is redundancy at the switch and rack level. |

Tuning group sizes and node resources enables applications to easily find the latency/cost sweet spot,
the elasticity operations are automatic and queries and writes work as usual with no downtime.

## Changing topology

A Vespa elasticity feature is the ability to change topology (i.e. grouped distribution) without service disruption.
This is a live change, and will auto-redistribute documents to the new topology.

Also read [topology change](/en/operations-selfhosted/admin-procedures.html#topology-change)
if running Vespa self-hosted - the below steps are general for all hosting options.

### Replicas

When changing topology, pay attention to the [min-redundancy](/en/reference/services-content.html#min-redundancy) setting -
this setting configures a *minimum* number of replicas in a cluster,
the *actual* number is topology dependent - example:

A flat cluster with min-redundancy n=2 and 15 nodes is changed into a grouped cluster with 3 groups with 5 nodes each
(total node count and n is kept unchanged).
In this case, the actual redundancy will be 3 after the change,
as each of the 3 groups will have at least 1 replica for full query coverage.
The practical consequence is that disk and memory requirements per node *increases* due to the change to topology.
It is therefore important to calculate the actual replica count before reconfiguring topology.

### Query coverage

Changing topology might cause query coverage loss in the transition, unless steps taken in the right order.
If full coverage is not important, just make the change and wait for document redistribution to complete.

To keep full query coverage, make sure not to change both group size and number of groups at the same time:

1. To add nodes for more data, or to have less data per node, increase group size.
   E.g., in a 2-group cluster with 8 nodes per group, add 4 nodes for a 25% capacity increase with 10 nodes per group.
2. If the goal is to add query capacity, add one or more groups, with the same node count as existing group(s).
   A flat cluster is the same as one group - if the flat cluster has 8 nodes,
   change to a grouped cluster with 2 groups of 8 nodes per group.
   This will add an empty group, which is put in query serving once populated.

In short, if the end-state means both changing number of groups and node count per group,
do this as separate steps, as a combination of the above.
Between each step, wait for document redistribution to complete using the `merge_bucket.pending` metric -
see [example](https://cloud.vespa.ai/en/index-bootstrap).

## Buckets

To manage documents, Vespa groups them in *buckets*,
using hashing or hints in the [document id](documents.html).

A document Put or Update is sent to all replicas of the bucket with the document.
If bucket replicas are out of sync, a bucket merge operation is run to re-sync the bucket.
A bucket contains [tombstones](/en/operations-selfhosted/admin-procedures.html#data-retention-vs-size)
of recently removed documents.

Buckets are split when they grow too large, and joined when they shrink.
This is a key feature for high performance in small to large instances,
and eliminates need for downtime or manual operations when scaling.
Buckets are purely a content management concept, and data is not stored or
indexed in separate buckets, nor does queries relate to buckets in any way.
Read more in [buckets](content/buckets.html).

## Ideal state distribution algorithm

The [ideal state distribution algorithm](content/idealstate.html)
uses a variant of the [CRUSH algorithm](https://ceph.com/assets/pdfs/weil-crush-sc06.pdf)
to decide bucket placement.
It makes a minimal number of documents move when nodes are added or removed.
Central to the algorithm is the assignment of a node sequence to each bucket:

![Assignment of a node sequence to each bucket](/assets/img/bucket-node-sequence.svg)

Steps to assign a bucket to a set of nodes:

1. Seed a random generator with the bucket ID to generate a pseudo-random sequence of numbers.
   Using the bucket ID as seed will then always generate the same sequence for the bucket.
2. Nodes are ordered by [distribution-key](reference/services-content.html#node),
   assign the random number in that order.
   E.g. a node with distribution-key 0 will get the first random number, node 1 the second.
3. Sort the node list by the random number.
4. Select nodes in descending random number order -
   above, node 1, 3 and 0 will store bucket 0x3c000000000000a0 with n=3 (redundancy).
   For n=2, node 1 and 3 will store the bucket.
   This specification of where to place a bucket is called the bucket's *ideal state*.

Repeat this for all buckets in the system.

## Consistency

Consistency is maintained at bucket level.
Content nodes calculate local checksums based on the bucket contents,
and the distributors compare checksums across the bucket replicas.
A *bucket merge* is issued to resolve inconsistency, when detected.
While there are inconsistent bucket replicas, operations are routed to the "best" replica.

As buckets are split and joined, it is possible for replicas of a bucket to be split at different levels.
A node may have been down while its buckets have been split or joined.
This is called *inconsistent bucket splitting*.
Bucket checksums can not be compared across buckets with different split levels.
Consequently, content nodes do not know whether all documents exist in enough replicas in this state.
Due to this, inconsistent splitting is one of the highest maintenance priorities.
After all buckets are split or joined back to the same level,
the content nodes can verify that all the replicas are consistent and fix any detected issues with a merge.
[Read more](content/consistency.html).

## Further reading
* [content nodes](content/content-nodes.html)
* [proton](proton.html) - see *ready* state
