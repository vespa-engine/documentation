---
# Copyright Vespa.ai. All rights reserved.
title: "Content node recovery"
category: oss
redirect_from:
- /en/operations/content-node-recovery.html
---

In exceptional cases, one or more content nodes may end up with corrupted data causing it to fail to restart.
Possible reasons are
* the application configuring a higher memory or disk limit
  such that the node is allowed to accept more data than it can manage,
* hardware failure, or
* a bug in Vespa.

Normally a corrupted node can just be wiped of all data or removed from the cluster, but
when this happens simultaneously to multiple nodes, or redundancy 1 is used, it may be necessary to recover
the node(s) to avoid data loss. This documents explains the procedure.

## Recovery steps

On each of the nodes needing recovery:

1. [Stop services](/en/operations-selfhosted/admin-procedures.html#vespa-start-stop-restart) on the node if running.
2. Repair the node:
   * If the node cannot start due to needing more memory than available:
     Increase the memory available to the node, or if not possible stop all non-essential processes on the node
     using `vespa-sentinel-cmd list`
     and `vespa-sentinel-cmd stop [name]`,
     and (if necessary) start only the content node process using `vespa-sentinel-cmd start searchnode`.
     When the node is successfully started, issue delete operations or increase the cluster size to reduce the
     amount of data on the node if necessary.
   * If the node cannot start due to needing more disk than available:
     Increase the disk available to the node, or if not possible delete non-essential data such as logs and cached packages.
     When the node is successfully started, issue delete operations or increase the cluster size to reduce the
     amount of data on the node if necessary.
   * If the node cannot start for any other reason, repair the data manually as needed.
     This procedure will depend on the specific nature of the data corruption.- [Start services](/en/operations-selfhosted/admin-procedures.html#vespa-start-stop-restart) on the node.
   - Verify that the node is fully up before doing the next node -
     metrics/interfaces to be used to evaluate if the next node can be stopped:
     * Check if a node is up using
       [/state/v1/health](/en/reference/state-v1.html#state-v1-health).
     * Check the `vds.idealstate.merge_bucket.pending.average` metric on content nodes.
       When 0, all buckets are in sync - see [example](/en/operations/metrics.html).
