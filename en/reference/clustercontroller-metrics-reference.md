---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "ClusterController Metrics"
---

| Name | Unit | Description |
| --- | --- | --- |
| cluster-controller.down.count | node | Number of content nodes down |
| cluster-controller.initializing.count | node | Number of content nodes initializing |
| cluster-controller.maintenance.count | node | Number of content nodes in maintenance |
| cluster-controller.retired.count | node | Number of content nodes that are retired |
| cluster-controller.stopping.count | node | Number of content nodes currently stopping |
| cluster-controller.up.count | node | Number of content nodes up |
| cluster-controller.cluster-state-change.count | node | Number of nodes changing state |
| cluster-controller.nodes-not-converged | node | Number of nodes not converging to the latest cluster state version |
| cluster-controller.stored-document-count | document | Total number of unique documents stored in the cluster |
| cluster-controller.stored-document-bytes | byte | Combined byte size of all unique documents stored in the cluster (not including replication) |
| cluster-controller.cluster-buckets-out-of-sync-ratio | fraction | Ratio of buckets in the cluster currently in need of syncing |
| cluster-controller.busy-tick-time-ms | millisecond | Time busy |
| cluster-controller.idle-tick-time-ms | millisecond | Time idle |
| cluster-controller.work-ms | millisecond | Time used for actual work |
| cluster-controller.is-master | binary | 1 if this cluster controller is currently the master, or 0 if not |
| cluster-controller.remote-task-queue.size | operation | Number of remote tasks queued |
| cluster-controller.node-event.count | operation | Number of node events |
| cluster-controller.resource_usage.nodes_above_limit | node | The number of content nodes above resource limit, blocking feed |
| cluster-controller.resource_usage.max_memory_utilization | fraction | Current memory utilisation, for content node with the highest value |
| cluster-controller.resource_usage.max_disk_utilization | fraction | Current disk space utilisation, for content node with the highest value |
| cluster-controller.resource_usage.memory_limit | fraction | Memory space limit as a fraction of available memory |
| cluster-controller.resource_usage.disk_limit | fraction | Disk space limit as a fraction of available disk space |
| reindexing.progress | fraction | Re-indexing progress |
