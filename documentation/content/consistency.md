---
# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa consistency model"
---

Vespa offers configurable data redundancy with eventual consistency across replicas.
It's designed for high efficiency under workloads where eventual consistency is an
acceptable tradeoff. This document aims to go into some detail on what these tradeoffs
are, and what you, as a user, can expect.

<!-- TODO more doc links, explain replica vs bucket?, ... -->

### Write durability and consistency

When a client receives a successful [write](../writing-to-vespa.html) response,
the operation has been written to the OS. The replication level is configurable.
Operations are by default written on _all_ replicas before sending a response.

On each replica node, operations are persisted to a write-ahead log before
being applied. The system will automatically recover after a crash by replaying
logged operations. The transaction log is synced to disk at OS-specific intervals, which
is typically 30 seconds. This means that if _all_ replicas go down at the same time,
it is possible to lose the most recent non-synced data.

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

When using a [Get](../document-api.html#get) or [Visit](visiting.html) operation, the client will never observe a partially
updated document. For these read operations, writes behave as if they are atomic.

Searches may observe partial updates, as updates are not atomic across index
structures. This can only happen _after_ a write has started, but _before_ it's
complete. Once a write is complete, all index updates are visible.

Searches may observe transient loss of coverage when nodes go down. Vespa will
restore coverage automatically when this happens. How fast this happens depends
on the configured [searchable-copies](../reference/services-content.html#searchable-copies) value.

If replicas diverge during a Get, Vespa performs a read-repair. This fetches the
requested document from all divergent replicas. The client then receives the
version with the newest timestamp.

If replicas diverge during a Visit, the operation will by default wait until the
replicas are back in sync. You can configure the operation to immediately use the
replica with the most documents.

Visits return the current state of the document set. They do not have snapshot isolation.

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
"win" and become visible. This version may be a remove (tombstone).

If a test-and-set operation updates at least one replica, it will eventually
become visible on the other replicas.

The reconciliation operation is referred to as a "merge" in the rest of the Vespa
documentation.

### Network partitions

Vespa is dependent on a centralized (but fault tolerant) node health checker
and coordinator.

A network partition may take place between the coordinator and a subset of nodes.
Operations to nodes in this subset aren't guaranteed to succeed until the
partition heals.
As a consequence, Vespa is not guaranteed to be strongly available (i.e. the 'A' in
[CAP](https://en.wikipedia.org/wiki/CAP_theorem "CAP theorem")).

In _practice_, the best-effort semantics of Vespa have proven to be both
robust and highly available.
