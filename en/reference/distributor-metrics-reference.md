---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Distributor Metrics"
---

| Name | Unit | Description |
| --- | --- | --- |
| vds.idealstate.buckets_rechecking | bucket | The number of buckets that we are rechecking for ideal state operations |
| vds.idealstate.idealstate_diff | bucket | A number representing the current difference from the ideal state. This is a number that decreases steadily as the system is getting closer to the ideal state |
| vds.idealstate.buckets_toofewcopies | bucket | The number of buckets the distributor controls that have less than the desired redundancy |
| vds.idealstate.buckets_toomanycopies | bucket | The number of buckets the distributor controls that have more than the desired redundancy |
| vds.idealstate.buckets | bucket | The number of buckets the distributor controls |
| vds.idealstate.buckets_notrusted | bucket | The number of buckets that have no trusted copies. |
| vds.idealstate.bucket_replicas_moving_out | bucket | Bucket replicas that should be moved out, e.g. retirement case or node added to cluster that has higher ideal state priority. |
| vds.idealstate.bucket_replicas_copying_out | bucket | Bucket replicas that should be copied out, e.g. node is in ideal state but might have to provide data other nodes in a merge |
| vds.idealstate.bucket_replicas_copying_in | bucket | Bucket replicas that should be copied in, e.g. node does not have a replica for a bucket that it is in ideal state for |
| vds.idealstate.bucket_replicas_syncing | bucket | Bucket replicas that need syncing due to mismatching metadata |
| vds.idealstate.max_observed_time_since_last_gc_sec | second | Maximum time (in seconds) since GC was last successfully run for a bucket. Aggregated max value across all buckets on the distributor. |
| vds.idealstate.delete_bucket.done_ok | operation | The number of operations successfully performed |
| vds.idealstate.delete_bucket.done_failed | operation | The number of operations that failed |
| vds.idealstate.delete_bucket.pending | operation | The number of operations pending |
| vds.idealstate.delete_bucket.blocked | operation | The number of operations blocked by blocking operation starter |
| vds.idealstate.delete_bucket.throttled | operation | The number of operations throttled by throttling operation starter |
| vds.idealstate.merge_bucket.done_ok | operation | The number of operations successfully performed |
| vds.idealstate.merge_bucket.done_failed | operation | The number of operations that failed |
| vds.idealstate.merge_bucket.pending | operation | The number of operations pending |
| vds.idealstate.merge_bucket.blocked | operation | The number of operations blocked by blocking operation starter |
| vds.idealstate.merge_bucket.throttled | operation | The number of operations throttled by throttling operation starter |
| vds.idealstate.merge_bucket.source_only_copy_changed | operation | The number of merge operations where source-only copy changed |
| vds.idealstate.merge_bucket.source_only_copy_delete_blocked | operation | The number of merge operations where delete of unchanged source-only copies was blocked |
| vds.idealstate.merge_bucket.source_only_copy_delete_failed | operation | The number of merge operations where delete of unchanged source-only copies failed |
| vds.idealstate.split_bucket.done_ok | operation | The number of operations successfully performed |
| vds.idealstate.split_bucket.done_failed | operation | The number of operations that failed |
| vds.idealstate.split_bucket.pending | operation | The number of operations pending |
| vds.idealstate.split_bucket.blocked | operation | The number of operations blocked by blocking operation starter |
| vds.idealstate.split_bucket.throttled | operation | The number of operations throttled by throttling operation starter |
| vds.idealstate.join_bucket.done_ok | operation | The number of operations successfully performed |
| vds.idealstate.join_bucket.done_failed | operation | The number of operations that failed |
| vds.idealstate.join_bucket.pending | operation | The number of operations pending |
| vds.idealstate.join_bucket.blocked | operation | The number of operations blocked by blocking operation starter |
| vds.idealstate.join_bucket.throttled | operation | The number of operations throttled by throttling operation starter |
| vds.idealstate.garbage_collection.done_ok | operation | The number of operations successfully performed |
| vds.idealstate.garbage_collection.done_failed | operation | The number of operations that failed |
| vds.idealstate.garbage_collection.pending | operation | The number of operations pending |
| vds.idealstate.garbage_collection.documents_removed | document | Number of documents removed by GC operations |
| vds.idealstate.garbage_collection.blocked | operation | The number of operations blocked by blocking operation starter |
| vds.idealstate.garbage_collection.throttled | operation | The number of operations throttled by throttling operation starter |
| vds.distributor.puts.latency | millisecond | The latency of put operations |
| vds.distributor.puts.ok | operation | The number of successful put operations performed |
| vds.distributor.puts.failures.total | operation | Sum of all failures |
| vds.distributor.puts.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.puts.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.puts.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.puts.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.puts.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.puts.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.puts.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.puts.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.puts.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.puts.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.puts.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.removes.latency | millisecond | The latency of remove operations |
| vds.distributor.removes.ok | operation | The number of successful removes operations performed |
| vds.distributor.removes.failures.total | operation | Sum of all failures |
| vds.distributor.removes.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.removes.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.removes.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.removes.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.removes.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.removes.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.removes.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.removes.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.removes.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.removes.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.removes.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.updates.latency | millisecond | The latency of update operations |
| vds.distributor.updates.ok | operation | The number of successful updates operations performed |
| vds.distributor.updates.failures.total | operation | Sum of all failures |
| vds.distributor.updates.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.updates.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.updates.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.updates.diverging_timestamp_updates | operation | Number of updates that report they were performed against divergent version timestamps on different replicas |
| vds.distributor.updates.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.updates.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.updates.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.updates.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.updates.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.updates.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.updates.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.updates.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.updates.fast_path_restarts | operation | Number of safe path (write repair) updates that were restarted as fast path updates because all replicas returned documents with the same timestamp in the initial read phase |
| vds.distributor.removelocations.ok | operation | The number of successful removelocations operations performed |
| vds.distributor.removelocations.failures.total | operation | Sum of all failures |
| vds.distributor.removelocations.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.removelocations.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.removelocations.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.removelocations.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.removelocations.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.removelocations.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.removelocations.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.removelocations.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.removelocations.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.removelocations.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.removelocations.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.removelocations.latency | millisecond | The average latency of removelocations operations |
| vds.distributor.gets.latency | millisecond | The average latency of gets operations |
| vds.distributor.gets.ok | operation | The number of successful gets operations performed |
| vds.distributor.gets.failures.total | operation | Sum of all failures |
| vds.distributor.gets.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.gets.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.gets.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.gets.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.gets.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.gets.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.gets.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.gets.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.gets.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.gets.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.gets.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.visitor.latency | millisecond | The average latency of visitor operations |
| vds.distributor.visitor.ok | operation | The number of successful visitor operations performed |
| vds.distributor.visitor.failures.total | operation | Sum of all failures |
| vds.distributor.visitor.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.visitor.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.visitor.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.visitor.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.visitor.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.visitor.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.visitor.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.visitor.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.visitor.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.visitor.bytes_per_visitor | operation | The number of bytes visited on content nodes as part of a single client visitor command |
| vds.distributor.visitor.docs_per_visitor | operation | The number of documents visited on content nodes as part of a single client visitor command |
| vds.distributor.visitor.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.visitor.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.docsstored | document | Number of documents stored in all buckets controlled by this distributor |
| vds.distributor.bytesstored | byte | Number of bytes stored in all buckets controlled by this distributor |
| metricmanager.periodichooklatency | millisecond | Time in ms used to update a single periodic hook |
| metricmanager.resetlatency | millisecond | Time in ms used to reset all metrics. |
| metricmanager.sleeptime | millisecond | Time in ms worker thread is sleeping |
| metricmanager.snapshothooklatency | millisecond | Time in ms used to update a single snapshot hook |
| metricmanager.snapshotlatency | millisecond | Time in ms used to take a snapshot |
| vds.distributor.activate_cluster_state_processing_time | millisecond | Elapsed time where the distributor thread is blocked on merging pending bucket info into its bucket database upon activating a cluster state |
| vds.distributor.bucket_db.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| vds.distributor.bucket_db.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| vds.distributor.bucket_db.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| vds.distributor.bucket_db.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| vds.distributor.getbucketlists.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.getbucketlists.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.getbucketlists.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.getbucketlists.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.getbucketlists.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.getbucketlists.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.getbucketlists.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.getbucketlists.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.getbucketlists.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.getbucketlists.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.getbucketlists.failures.total | operation | Total number of failures |
| vds.distributor.getbucketlists.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.getbucketlists.latency | millisecond | The average latency of getbucketlists operations |
| vds.distributor.getbucketlists.ok | operation | The number of successful getbucketlists operations performed |
| vds.distributor.recoverymodeschedulingtime | millisecond | Time spent scheduling operations in recovery mode after receiving new cluster state |
| vds.distributor.set_cluster_state_processing_time | millisecond | Elapsed time where the distributor thread is blocked on processing its bucket database upon receiving a new cluster state |
| vds.distributor.state_transition_time | millisecond | Time it takes to complete a cluster state transition. If a state transition is preempted before completing, its elapsed time is counted as part of the total time spent for the final, completed state transition |
| vds.distributor.stats.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.stats.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.stats.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.stats.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.stats.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.stats.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.stats.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.stats.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.stats.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.stats.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.stats.failures.total | operation | The total number of failures |
| vds.distributor.stats.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.stats.latency | millisecond | The average latency of stats operations |
| vds.distributor.stats.ok | operation | The number of successful stats operations performed |
| vds.distributor.update_gets.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.update_gets.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.update_gets.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.update_gets.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.update_gets.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.update_gets.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.update_gets.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.update_gets.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.update_gets.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.update_gets.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.update_gets.failures.total | operation | The total number of failures |
| vds.distributor.update_gets.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.update_gets.latency | millisecond | The average latency of update_gets operations |
| vds.distributor.update_gets.ok | operation | The number of successful update_gets operations performed |
| vds.distributor.update_metadata_gets.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.update_metadata_gets.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.update_metadata_gets.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.update_metadata_gets.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.update_metadata_gets.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.update_metadata_gets.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.update_metadata_gets.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.update_metadata_gets.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.update_metadata_gets.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.update_metadata_gets.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.update_metadata_gets.failures.total | operation | The total number of failures |
| vds.distributor.update_metadata_gets.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.update_metadata_gets.latency | millisecond | The average latency of update_metadata_gets operations |
| vds.distributor.update_metadata_gets.ok | operation | The number of successful update_metadata_gets operations performed |
| vds.distributor.update_puts.failures.busy | operation | The number of messages from storage that failed because the storage node was busy |
| vds.distributor.update_puts.failures.concurrent_mutations | operation | The number of operations that were transiently failed due to a mutating operation already being in progress for its document ID |
| vds.distributor.update_puts.failures.inconsistent_bucket | operation | The number of operations failed due to buckets being in an inconsistent state or not found |
| vds.distributor.update_puts.failures.notconnected | operation | The number of operations discarded because there were no available storage nodes to send to |
| vds.distributor.update_puts.failures.notfound | operation | The number of operations that failed because the document did not exist |
| vds.distributor.update_puts.failures.notready | operation | The number of operations discarded because distributor was not ready |
| vds.distributor.update_puts.failures.safe_time_not_reached | operation | The number of operations that were transiently failed due to them arriving before the safe time point for bucket ownership handovers has passed |
| vds.distributor.update_puts.failures.storagefailure | operation | The number of operations that failed in storage |
| vds.distributor.update_puts.failures.test_and_set_failed | operation | The number of mutating operations that failed because they specified a test-and-set condition that did not match the existing document |
| vds.distributor.update_puts.failures.timeout | operation | The number of operations that failed because the operation timed out towards storage |
| vds.distributor.update_puts.failures.total | operation | The total number of put failures |
| vds.distributor.update_puts.failures.wrongdistributor | operation | The number of operations discarded because they were sent to the wrong distributor |
| vds.distributor.update_puts.latency | millisecond | The average latency of update_puts operations |
| vds.distributor.update_puts.ok | operation | The number of successful update_puts operations performed |
| vds.idealstate.nodes_per_merge | node | The number of nodes involved in a single merge operation. |
| vds.idealstate.set_bucket_state.blocked | operation | The number of operations blocked by blocking operation starter |
| vds.idealstate.set_bucket_state.done_failed | operation | The number of operations that failed |
| vds.idealstate.set_bucket_state.done_ok | operation | The number of operations successfully performed |
| vds.idealstate.set_bucket_state.pending | operation | The number of operations pending |
| vds.idealstate.set_bucket_state.throttled | operation | The number of operations throttled by throttling operation starter |
| vds.bouncer.clock_skew_aborts | operation | Number of client operations that were aborted due to clock skew between sender and receiver exceeding acceptable range |
