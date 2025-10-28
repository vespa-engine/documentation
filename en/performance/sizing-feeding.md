---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa Feed Sizing Guide"
---

Vespa is optimized to sustain a high feed load while serving -
also during planned and unplanned changes to the instance.
This guide provides an overview of how to optimize feed performance and also understand bottlenecks.

The [reads and writes](../reads-and-writes.html) guide has an overview of the Vespa architecture and relevant
APIs for feeding and searching. One key takeaway is that Vespa is split into two main service types:
* Stateless container cluster(s)
* Stateful content cluster(s)

The stateless container cluster is responsible for processing all document operations to Vespa.
The stateful content cluster is responsible for writing and syncing all document operations (persisting state and managing data structures).

Generally, Vespa cannot sustain a higher write rate than the underlying storage can handle (MB/s and IOPS). To understand
resource utilization it is critical that resource usage like CPU, memory, disk and network are monitored. Only this way can
a system be sized correctly and bottlenecks identified.

## Stateless container cluster

The processing of all document operations to Vespa are routed through the stateless *container* cluster.
Processing includes both Vespa processing like [linguistic processing](../linguistics.html)
and custom [document processing](../document-processing.html). The
stateless container cluster is also responsible for [embedding](../embedding.html) inference. Embedding
inference can be compute-resource intensive, depending on number of *embed* calls and the size of the embedding model.
See [embedding performance](../embedding.html#embedder-performance).

The stateless cluster is compute (CPU/GPU util) bound and processing rates should scale linearly with the number of nodes and the number of V-CPU's in the cluster as
long as the client can deliver enough operations over the network.

See [multiple container clusters](/en/operations-selfhosted/routing.html#multiple-container-clusters)
for how to separate search and write to different container clusters. Isolated container clusters
are useful for high load scenarios where the container cluster is compute bound and where there is concurrent search and write load
and where we want to avoid write operations to impact search queries due to compute-related resource contention.

The stateless container cluster is implemented in Java (JVM), ensure enough memory allocated for heap to avoid excessive JVM garbage collection.
See [stateless container tuning](container-tuning.html) for tuning options. The default max heap size is 1.5GB in self-hosted deployments
unless overridden.

## Stateful content cluster
**All feed operations** to Vespa are **written and synced** to the [transaction log](../proton.html#transaction-log) on
the content node(s). This include both writing new documents and updating existing documents.
The Vespa transaction log is a write-ahead log (WAL) that ensures durability of the data. A reply is only sent back to the client
when the operation is written successfully to the transaction log and applied (visible in search/get).

The write pattern is append and sequential (not random) IO. Note that Vespa cannot sustain a higher write rate than
the underlying storage can handle. Feeding might be impacted severely if the content nodes are using network attached storage
where the sync operation (for durability) has a much higher cost than on local attached storage (e.g. SSD).
See [sync-transactionlog](../reference/services-content.html#sync-transactionlog).

### Document store

Documents are written to the [document store](../proton.html#document-store) in all
[indexing modes](../reference/services-content.html#document) -
this is where the copy of the document is persisted.

Adding new documents to the document store is append-only with a sequential IO pattern.
Writing a new version of a document (PUT a document that already exists) is the same as for a
document id that does not exist. The in-memory mapping from
document id to summary data file position is updated to point to the latest version in both cases. The
summary files are [defragmented](../proton.html#defragmentation) to remove old versions of documents.

### Attribute store

Fields that are defined with the [attribute](../attributes.html) property are in-memory fields that
supports in-place updates with higher [partial update](../partial-updates.html) throughput than fields that are indexed
with `index` property (avoiding read-apply-write pattern).
The attribute store is a memory-only data structure that is regularly persisted to disk in the [attribute store](../proton.html#attributes).

```
schema ticker {
    document ticker {
        field volume type int {
            indexing: summary | attribute
        }
    }
}
```

See [partial updates](../partial-updates.html) for details.

#### Redundancy settings

To achieve memory-only updates (plus transaction log writing),
make sure all attributes to update are [ready](../proton.html#sub-databases),
meaning the content node has loaded the attribute field into memory:
* One way to ensure this is to set
  [searchable copies](../reference/services-content.html#searchable-copies) equal to
  [redundancy](../reference/services-content.html#redundancy) -
  i.e. all nodes that has a replica of the document has loaded it as searchable
* Another way is by setting
  [fast-access](../reference/schema-reference.html#attribute) on each attribute to update

### Index

Changes to index fields are written to the [document store](#document-store)
and the [index](../proton.html#index).
Note that an UPDATE operation requires a read-modify-write to the document store and limits throughput.
Refer to [partial updates](../partial-updates.html) for more details.

```
schema music {
    document music {
        field artist type string {
            indexing: summary | index
        }
    }
}
```

### Content Node Thread pools

Several thread pools are involved when handling write operations on a content node.
These are summarized in the following table. Not all mutating operations can be handled in parallel and tracking
these metrics can help identify bottlenecks. For example, if you notice that feed throughput is not increasing beyond
a certain CPU utilization, it might be that one of the thread pools is saturated.
Metrics are available for each thread pool, see
[searchnode metrics](../reference/vespa-set-metrics-reference.html#searchnode-metrics)
for details.

To analyse performance and bottlenecks, the most relevant metrics are *.utilization* and *.queuesize*.
In addition, *.saturation* is relevant for the [field writer](#field-writer-executor) thread pool.
See [bottlenecks](#bottlenecks) for details.

| Thread pool | Description |
| --- | --- |
| master | Updates the [document metastore](../attributes.html#document-meta-store), prepares tasks to the [index](#index-thread) and [summary](#summary-thread) threads, and splits a write operation into a set of tasks to update individual [attributes](../proton.html#attributes), executed by the threads in the [field writer](#field-writer-executor). | |  |
| Threads | 1 |
| Instances | One instance per document database. |
| Metric prefix | *content.proton.documentdb.threading_service.master.* |
| index | Manages writing of index fields in the [memory index](../proton.html#index). It splits a write operation into a set of tasks to update individual index fields, executed by the threads in the [field writer](#field-writer-executor). | |
| Threads | 1 |
| Instances | One instance per document database. |
| Metric prefix | *content.proton.documentdb.threading_service.index.* |
| summary | Writes documents to the [document store](../proton.html#document-store). | |
| Threads | 1 |
| Instances | One instance per document database. |
| Metric prefix | *content.proton.documentdb.threading_service.summary.* |
| field writer | The threads in this thread pool are used to invert index fields, write changes to the memory index, and write changes to attributes. Index fields and attribute fields across all document databases are randomly assigned to one of the threads in this thread pool. A field that is costly to write or update might become the bottleneck during feeding. | |
| Threads | Many, controlled by [feeding concurrency](../reference/services-content.html#feeding). |
| Instances | One instance shared between all document databases. |
| Metric prefix | *content.proton.executor.field_writer.* |
| shared | The threads in this thread pool are among other used to compress and de-compress documents in the [document store](../proton.html#document-store), merge files as part of [disk index fusion](../proton.html#disk-index-fusion), and prepare for inserting a vector into a [HNSW index](../reference/schema-reference.html#index-hnsw). | |
| Threads | Many, controlled by [feeding concurrency](../reference/services-content.html#feeding). |
| Instances | One instance shared between all document databases. |
| Metric prefix | *content.proton.executor.shared.* |

## Multivalue attribute

[Multivalued attributes](../reference/schema-reference.html#field) are
*weightedset*, *array of struct/map*, *map of struct/map* and *tensor*.
The attributes have different characteristics, which affects write performance.
Generally, updates to multivalue fields are more expensive as the field size grows:

| Attribute | Description |
| --- | --- |
| weightedset | Memory-only operation when updating: read full set, update, write back. Make the update as inexpensive as possible using numeric types instead of strings, where possible Example: a weighted set of string with many (1000+) elements. Adding an element to the set means an enum store lookup/add and add/sort of the attribute multivalue map - details in [attributes](../attributes.html). Use a numeric type instead to speed this up - this has no string comparisons. |
| array/map of struct/map | Update to array of struct/map and map of struct/map requires a read from the [document store](../proton.html#document-store) and will reduce update rate - see [#10892](https://github.com/vespa-engine/vespa/issues/10892). |
| tensor | Updating tensor cell values is a memory-only operation: copy tensor, update, write back. For large tensors, this implicates reading and writing a large chunk of memory for single cell updates. |

## Parent/child

[Parent documents](../parent-child.html) are global, i.e. has a replica on all nodes.
Writing to fields in parent documents often simplify logic,
compared to the de-normalized case where all
(child) documents are updated.
Write performance depends on the average number of child documents vs number of nodes in the cluster - examples:
* 10-node cluster, avg number of children=100, redundancy=2:
  A parent write means 10 writes, compared to 200 writes, or 20x better
* 50-node cluster, avg number of children=10, redundancy=2:
  A parent write means 50 writes, compared to 20 writes, or 2.5x worse

Hence, the more children, the better performance effect for parent writes.

## Conditional updates

A conditional update looks like:

```
{
    "update" : "id:namespace:myDoc::1",
    "condition" : "myDoc.myField == \"abc\"",
    "fields" : { "myTimestamp" : { "assign" : 1570187817 } }
}
```

If the [document store](../proton.html#document-store)
is accessed when evaluating the condition, performance drops significantly because you get random access instead of
just appending to the persisted data structures.
Conditions should be evaluated using attribute values for high performance -
in the example above, *myField* should be an attribute.

Note: If the condition uses struct or map, values are read from the document store:

```
    "condition" : "myDoc.myMap{1} == 3"
```

This is true even though all struct fields are defined as attribute.
Improvements to this is tracked in
[#10892](https://github.com/vespa-engine/vespa/issues/10892).

## Client roundtrips

Consider the difference when sending two fields assignments to the same document:

```
{
    "update" : "id:namespace:doctype::1",
    "fields" : {
        "myMap{1}" : { "assign" : { "timestamp" : 1570187817 } }
        "myMap{2}" : { "assign" : { "timestamp" : 1570187818 } }
    }
}
```

vs.

```
{
    "update" : "id:namespace:doctype::1",
    "fields" : {
        "myMap{1}" : { "assign" : { "timestamp" : 1570187817 } }
    }
}
{
    "update" : "id:namespace:doctype::1",
    "fields" : {
        "myMap{2}" : { "assign" : { "timestamp" : 1570187818 } }
    }
}
```

In the first case, *one* update operation is sent from
[vespa feed](../vespa-cli.html) -
in the latter, the client will send the second update operation *after* receiving an ack for the first.
When updating multiple fields, put the updates in as few operations as possible.
See [ordering details](../content/content-nodes.html#ordering).

## Feed vs. search

A content node normally has a fixed set of resources (CPU, memory, disk).
Configure the CPU allocation for feeding vs. searching in
[concurrency](../reference/services-content.html#feeding) -
value from 0 to 1.0 - a higher value means more CPU resources for feeding.

In addition, you can also control priority of feed versus search, or rather how nice feeding shall be.
Since a process needs root privileges for increasing feed, we have opted to reduce priority (be nice)
of feeding. This is controlled by a [niceness](../reference/services-content.html#feeding-niceness)
number from 0 to 1.0 - higher value will favor search over feed. 0 is default.

## Feed testing

When testing for feeding capacity:

1. Use [vespa feed](../vespa-cli.html).
2. Test using one content node to find its capacity and where the bottlenecks are (resource utilization metrics) and Vespa metrics
3. Test feeding performance by adding feeder instances.
   Make sure network and CPU (content and container node) usage increases, until saturation.
4. See troubleshooting at end to make sure there are no errors.

Other scenarios: Feed testing for capacity for sustained load in a system in steady state,
during state changes, during query load.

## Troubleshooting

{% include note.html content="Use the
[monitoring sample app](/en/operations-selfhosted/monitoring.html#monitoring-with-grafana)
to set up a sample system, with a document/query feed and dashboards, to familiarize with metrics." %}

|  |  |
| --- | --- |
| Metrics | Use [metrics](../reference/vespa-set-metrics-reference.html#storage-metrics) from content nodes and look at queues - queue wait time and queue size (all metrics in milliseconds):   ``` vds.filestor.averagequeuewait.sum vds.filestor.queuesize ```   Check content node metrics across all nodes to see if there are any outliers. Also check latency metrics per operation type:   ``` vds.filestor.allthreads.put.latency vds.filestor.allthreads.update.latency vds.filestor.allthreads.remove.latency ``` |
| Bottlenecks | One of the [threads](#content-node-thread-pools) used to handle write operations might become the bottleneck during feeding. Look at the *.utilization* metrics for all thread pools:   ``` content.proton.documentdb.threading_service.master.utilization content.proton.documentdb.threading_service.index.utilization content.proton.documentdb.threading_service.summary.utilization content.proton.executor.field_writer.utilization content.proton.executor.shared.utilization ```   If utilization is high for [field writer](#field-writer-executor) or [shared](#shared-executor), adjust [feeding concurrency](../reference/services-content.html#feeding) to allow more CPU cores to be used for feeding.  For the field writer also look at the *.saturation* metric:   ``` content.proton.executor.field_writer.saturation ```   If this is close to 1.0 and higher than *.utilization* it indicates that one of its worker threads is a bottleneck. The reason can be that this particular thread is handling a large index or attribute field that is naturally expensive to write and update. Use the [custom component state API](../proton.html#custom-component-state-api) to find which index and attribute fields are assigned to which thread (identified by *executor_id*), and look at the detailed statistics of the field writer to find which thread is the actual bottleneck:   ``` state/v1/custom/component/documentdb/mydoctype/subdb/ready/index state/v1/custom/component/documentdb/mydoctype/subdb/ready/attributewriter state/v1/custom/component/threadpools/field_writer ``` |
| Failure rates | Inspect these metrics for failures during load testing:   ``` vds.distributor.updates.latency vds.distributor.updates.ok vds.distributor.updates.failures.total vds.distributor.puts.latency vds.distributor.puts.ok vds.distributor.puts.failures.total vds.distributor.removes.latency vds.distributor.removes.ok vds.distributor.removes.failures.total ``` |
| Blocked feeding | This metric should be 0 - refer to [feed block](../operations/feed-block.html):   ``` content.proton.resource_usage.feeding_blocked ``` |
| Concurrent mutations | Multiple clients updating the same document concurrently will stall writes:   ``` vds.distributor.updates.failures.concurrent_mutations ```  Mutating client operations towards a given document ID are sequenced on the [distributors](../content/content-nodes.html#distributor). If an operation is already active towards a document, a subsequently arriving one will be bounced back to the client with a transient failure code. Usually this happens when users send feed from multiple clients concurrently without synchronisation. Note that feed operations sent by a single client are sequenced client-side, so this should not be observed with a single client only. Bounced operations are never sent on to the backends and should not cause elevated latencies there, although the client will observe higher latencies due to automatic retries with back-off. |
| Wrong distribution | ``` vds.distributor.updates.failures.wrongdistributor ```  Indicates that clients keep sending to the wrong distributor. Normally this happens infrequently (but is *does* happen on client startup or distributor state transitions), as clients update and cache all state required to route directly to the correct distributor (Vespa uses a deterministic CRUSH-based algorithmic distribution). Some potential reasons for this:  1. Clients are being constantly re-created with no cached state. 2. The system is in some kind of flux where the underlying state keeps changing constantly. 3. The client distribution policy has received so many errors    that it throws away its cached state to start with a clean slate to    e.g. avoid the case where it only has cached information for the bad side of a network partition. 4. The system has somehow failed to converge to a shared cluster state,    causing parts of the cluster to have a different idea of the correct state than others. |
| Cluster out of sync | *update_puts/gets* indicate "two-phase" updates:   ``` vds.distributor.update_puts.latency vds.distributor.update_puts.ok vds.distributor.update_gets.latency vds.distributor.update_gets.ok vds.distributor.update_gets.failures.total vds.distributor.update_gets.failures.notfound ```   If replicas are out of sync, updates cannot be applied directly on the replica nodes as they risk ending up with diverging state. In this case, Vespa performs an explicit read-consolidate-write (write repair) operation on the distributors. This is usually a lot slower than the regular update path because it doesn't happen in parallel. It also happens in the write-path of other operations, so risks blocking these if the updates are expensive in terms of CPU.  Replicas being out of sync is by definition not the expected steady state of the system. For example, replica divergence can happen if one or more replica nodes are unable to process or persist operations. Track (pending) merges:   ``` vds.idealstate.buckets vds.idealstate.merge_bucket.pending vds.idealstate.merge_bucket.done_ok vds.idealstate.merge_bucket.done_failed ``` |
