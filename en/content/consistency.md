---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa Consistency Model"
redirect_from:
- /documentation/content/consistency.html
---

Vespa offers configurable data redundancy with eventual consistency across replicas.
It's designed for high efficiency under workloads where eventual consistency is an
acceptable tradeoff. This document aims to go into some detail on what these tradeoffs
are, and what you, as a user, can expect.

<!-- TODO more doc links, explain replica vs bucket?, ... -->

### Vespa and CAP

Vespa may be considered a limited subset of AP under the [CAP theorem](https://en.wikipedia.org/wiki/CAP_theorem).

Under CAP, there is a fundamental limitation of whether any distributed system can offer
guarantees on consistency (C) or availability (A) in scenarios where nodes are partitioned (P)
from each other. Since there is no escaping that partitions can and will happen, we talk
either of systems that are _either_ CP or AP.

Consistency (C) in CAP implies that reads and writes are strongly consistent, i.e. the system offers
_linearizability_.
Weaker forms such as causal consistency or "read your writes" consistency is _not_ sufficient.
As mentioned initially, Vespa is an eventually consistent data store and therefore does not offer
this property. In practice, Consistency requires the use of a majority consensus algorithm, which
Vespa does not currently use.

Availability (A) in CAP implies that _all requests_ receive a non-error response regardless of how
the network may be partitioned. Vespa is dependent on a centralized (but fault tolerant) node health
checker and coordinator. A network partition may take place between the coordinator and a subset of nodes.
Operations to nodes in this subset aren't guaranteed to succeed until the partition heals.
As a consequence, Vespa is not _guaranteed_ to be strongly available,
so we treat this as a "limited subset" of AP (though this is not technically part of the CAP definition).

In _practice_, the best-effort semantics of Vespa have proven to be both robust and
highly available in common datacenter networks.

### Write durability and consistency

When a client receives a successful [write](../reads-and-writes.html) response,
the operation has been written and synced to disk. The replication level is configurable.
Operations are by default written on _all_ available replica nodes before sending a response.
"Available" here means being Up in the [cluster state](content-nodes.html#cluster-state),
which is determined by the fault-tolerant, centralized Cluster Controller service.
If a cluster has a total of 3 nodes, 2 of these are available and the replication factor
is 3, writes will be ACKed to the client if both the available nodes ACK the operation.

On each replica node, operations are persisted to a write-ahead log before
being applied. The system will automatically recover after a crash by replaying
logged operations. Writes are guaranteed to be synced to durable storage prior
to sending a successful response to the client, so acknowledged writes are retained even
in the face of sudden power loss.

If a client receives a failure response for a write operation, the operation may or may not have taken
place on a subset of the replicas. If not all replicas could be written to,
they are considered divergent (out of sync). The system detects and reconciles
divergent replicas. This happens without any required user intervention.

Each document write assigns a new wall-clock timestamp to the resulting document
version. As a consequence, configure servers with NTP to keep clock drift as small
as possible. Large clock drifts may result in timestamp collisions or unexpected
operation orderings.

Vespa has support for conditional writes for individual documents through
test-and-set operations. Multi-document transactions are not supported.

After a successful response, changes to the search indexes are immediately
visible by default.

### Read consistency

Reads are consistent on a best-effort basis and are not guaranteed to be linearizable.

When using a [Get](../reference/document-v1-api-reference.html#get) or [Visit](../visiting.html) operation,
the client will never observe a partially updated document.
For these read operations, writes behave as if they are atomic.

Searches may observe partial updates, as updates are not atomic across index
structures. This can only happen _after_ a write has started, but _before_ it's
complete. Once a write is complete, all index updates are visible.

Searches may observe transient loss of coverage when nodes go down. Vespa will
restore coverage automatically when this happens. How fast this happens depends
on the configured [searchable-copies](../reference/services-content.html#searchable-copies) value.

If replicas diverge during a Get, Vespa performs a read-repair. This fetches the
requested document from all divergent replicas. The client then receives the
version with the newest timestamp.

If replicas diverge during a Visit, the behavior is slightly different between
the Document V1 API and [vespa-visit](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-visit):

  * Document V1 will prefer immediately visiting the replica that contains the
    most documents. This means it's possible for a subset of documents in a bucket
    to not be returned.
  * `vespa-visit` will by default retry visiting the bucket until it is in sync.
    This may take a long time if large parts of the system are out of sync.

The rationale for this difference in behavior is that Document V1 is usually
called in a real-time request context, whereas `vespa-visit` is usually called
in a background/batch processing context.

Visitor operations iterate over the document corpus in an implementation-specific
order. Any given document is returned in the state it was in at the time the visitor
iterated over the data bucket containing the document. This means there is <em>no
snapshot isolation</em>—a document mutation happening concurrently with a visitor
may or may not be reflected in the returned document set, depending on whether
the mutation happened before or after iteration of the bucket containing the document.

### Replica reconciliation

Reconciliation is the act of bringing divergent replicas back into sync. This
usually happens after a node restarts or fails. It will also happen after
network partitions.

Unlike several other eventually consistent databases, Vespa doesn't use
distributed replica operation logs. Instead, reconciling replicas involves
exchanging sets of timestamped documents. Reconciliation is complete once
the union set of documents is present on all replicas. Metadata is checksummed
to determine whether replicas are in sync with each other.

When reconciling replicas, the newest available version of a document will
"win" and become visible. This version may be a remove (tombstone). Tombstones
are replicated in the same way as regular documents.

Reconciliation happens the document level, not at the field level. I.e. there
is no merging of individual fields across different versions.

If a test-and-set operation updates at least one replica, it will eventually
become visible on the other replicas.

The reconciliation operation is referred to as a "merge" in the rest of the Vespa
documentation.

Tombstone entries have a configurable time-to-live before they are compacted away.
Nodes that have been partitioned away from the network for a longer period of time
than this TTL should ideally have their indexes removed before being allowed back into the cluster.
If not, there is a risk of resurrecting previously removed documents.
Vespa does not currently detect or handle this scenario automatically.

See the documentation on [data-retention-vs-size](/en/operations-selfhosted/admin-procedures.html#data-retention-vs-size).

### Q/A

#### How does Vespa perform read-repair for Get-operations, and how many replicas are consulted?

When the distributor process that is responsible for a particular data bucket receives
a Get operation, it checks its locally cached replica metadata state for inconsistencies.

If all replicas have consistent metadata, the operation is routed to a single replica—preferably
located on the same host as the distributor, if present. This is the normal case when
the bucket replicas are in sync.

If there is at least one replica metadata mismatch, the distributor automatically initiates
a read-repair process:

 1. The distributor splits the bucket replicas into subsets based on their metadata,
    where all replicas in each subset have the same metadata. It then sends a lightweight
    metadata-only Get to one replica in each subset. The core assumption is that all
    these replicas have the same set of document versions, and that it suffices to
    consult one replica in the set. If a metadata read fails, the distributor will
    automatically fail over to another replica in the subset.
 2. It then sends one full Get to a node in the replica set that returned the _highest_
    timestamp.

This means that if you have 100 replicas and 1 has different metadata from the remaining
99, only 2 nodes in total will be initially queried, and only 1 will receive the actual
(full) Get read.

Similar algorithms are used by other operations that may trigger read/write-repair.

#### Since Vespa performs read-repair when inconsistencies are detected, does this mean replies are strongly consistent?

Unfortunately not. Vespa does not offer any cross-document transactions, so in
this case strong consistency implies single-object _linearizability_ (as opposed to
_strict serializability_ across multiple objects). Linearizability requires the ability
to reach a majority consensus amongst a particular known and stable configuration of
replicas (side note: replica sets can be reconfigured in strongly consistent algorithms
like Raft and Paxos, but such a reconfiguration must also be threaded through the
consensus machinery).

The active replica set for a given data bucket (and thus the documents it logically
contains) is ephemeral and dynamic based on the nodes that are currently available in
the cluster (as seen from the cluster controller). This precludes having a stable set
of replicas that can be used for reaching majority decisions.

See also [Vespa and CAP](#vespa-and-cap).

#### In what kind of scenario might Vespa return a stale version of a document?

Stale document versions may be returned when all replicas containing the most recent
document version have become unavailable.

Example scenario (for simplicity—but without loss of generality—assuming redundancy 1) in
a cluster with two nodes {A, B}:

 1. Document X is stored in a replica on node A with timestamp 100.
 2. Node A goes down; node B takes over ownership.
 3. A write request is received for document X; it is stored on node B with timestamp
    200 and ACKed to the client.
 4. Node B goes down.
 5. Node A comes back up.
 6. A read request arrives for document X. The only visible replica is on node A, which
    ends up serving the request.
 7. The document version at timestamp 100 is returned to the client.

Since the write at `t=200` _happens-after_ the write at `t=100`, returning the version at
`t=100` violates linearizability.

