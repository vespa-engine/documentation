---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Storage Metrics"
---

| Name | Unit | Description |
| --- | --- | --- |
| vds.datastored.alldisks.buckets | bucket | Number of buckets managed |
| vds.datastored.alldisks.docs | document | Number of documents stored |
| vds.datastored.alldisks.bytes | byte | Number of bytes stored |
| vds.datastored.alldisks.activebuckets | bucket | Number of active buckets on the node |
| vds.datastored.alldisks.readybuckets | bucket | Number of ready buckets on the node |
| vds.visitor.allthreads.averagevisitorlifetime | millisecond | Average lifetime of a visitor |
| vds.visitor.allthreads.averagequeuewait | millisecond | Average time an operation spends in input queue. |
| vds.visitor.allthreads.queuesize | operation | Size of input message queue. |
| vds.visitor.allthreads.completed | operation | Number of visitors completed |
| vds.visitor.allthreads.created | operation | Number of visitors created. |
| vds.visitor.allthreads.failed | operation | Number of visitors failed |
| vds.visitor.allthreads.averagemessagesendtime | millisecond | Average time it takes for messages to be sent to their target (and be replied to) |
| vds.visitor.allthreads.averageprocessingtime | millisecond | Average time used to process visitor requests |
| vds.visitor.allthreads.aborted | instance | Number of visitors aborted. |
| vds.visitor.allthreads.averagevisitorcreationtime | millisecond | Average time spent creating a visitor instance |
| vds.visitor.allthreads.destination_failure_replies | instance | Number of failure replies received from the visitor destination |
| vds.filestor.queuesize | operation | Size of input message queue. |
| vds.filestor.averagequeuewait | millisecond | Average time an operation spends in input queue. |
| vds.filestor.active_operations.size | operation | Number of concurrent active operations |
| vds.filestor.active_operations.latency | millisecond | Latency (in ms) for completed operations |
| vds.filestor.throttle_window_size | operation | Current size of async operation throttler window size |
| vds.filestor.throttle_waiting_threads | thread | Number of threads waiting to acquire a throttle token |
| vds.filestor.throttle_active_tokens | instance | Current number of active throttle tokens |
| vds.filestor.allthreads.mergemetadatareadlatency | millisecond | Time spent in a merge step to check metadata of current node to see what data it has. |
| vds.filestor.allthreads.mergedatareadlatency | millisecond | Time spent in a merge step to read data other nodes need. |
| vds.filestor.allthreads.mergedatawritelatency | millisecond | Time spent in a merge step to write data needed to current node. |
| vds.filestor.allthreads.mergeavgdatareceivedneeded | byte | Amount of data transferred from previous node in chain that we needed to apply locally. |
| vds.filestor.allthreads.mergebuckets.count | request | Number of requests processed. |
| vds.filestor.allthreads.mergebuckets.failed | request | Number of failed requests. |
| vds.filestor.allthreads.mergebuckets.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.mergelatencytotal | millisecond | Latency of total merge operation, from master node receives it, until merge is complete and master node replies. |
| vds.filestor.allthreads.merge_put_latency | millisecond | Latency of individual puts that are part of merge operations |
| vds.filestor.allthreads.merge_remove_latency | millisecond | Latency of individual removes that are part of merge operations |
| vds.filestor.allstripes.throttled_rpc_direct_dispatches | instance | Number of times an RPC thread could not directly dispatch an async operation directly to Proton because it was disallowed by the throttle policy |
| vds.filestor.allstripes.throttled_persistence_thread_polls | instance | Number of times a persistence thread could not immediately dispatch a queued async operation because it was disallowed by the throttle policy |
| vds.filestor.allstripes.timeouts_waiting_for_throttle_token | instance | Number of times a persistence thread timed out waiting for an available throttle policy token |
| vds.filestor.allstripes.averagequeuewait | millisecond | Average time an operation spends in input queue. |
| vds.filestor.allthreads.put.count | operation | Number of requests processed. |
| vds.filestor.allthreads.put.failed | operation | Number of failed requests. |
| vds.filestor.allthreads.put.test_and_set_failed | operation | Number of operations that were skipped due to a test-and-set condition not met |
| vds.filestor.allthreads.put.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.put.request_size | byte | Size of requests, in bytes |
| vds.filestor.allthreads.remove.count | operation | Number of requests processed. |
| vds.filestor.allthreads.remove.failed | operation | Number of failed requests. |
| vds.filestor.allthreads.remove.test_and_set_failed | operation | Number of operations that were skipped due to a test-and-set condition not met |
| vds.filestor.allthreads.remove.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.remove.request_size | byte | Size of requests, in bytes |
| vds.filestor.allthreads.remove.not_found | request | Number of requests that could not be completed due to source document not found. |
| vds.filestor.allthreads.get.count | operation | Number of requests processed. |
| vds.filestor.allthreads.get.failed | operation | Number of failed requests. |
| vds.filestor.allthreads.get.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.get.request_size | byte | Size of requests, in bytes |
| vds.filestor.allthreads.get.not_found | request | Number of requests that could not be completed due to source document not found. |
| vds.filestor.allthreads.update.count | request | Number of requests processed. |
| vds.filestor.allthreads.update.failed | request | Number of failed requests. |
| vds.filestor.allthreads.update.test_and_set_failed | request | Number of requests that were skipped due to a test-and-set condition not met |
| vds.filestor.allthreads.update.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.update.request_size | byte | Size of requests, in bytes |
| vds.filestor.allthreads.update.latency_read | millisecond | Latency of the source read in the request. |
| vds.filestor.allthreads.update.not_found | request | Number of requests that could not be completed due to source document not found. |
| vds.filestor.allthreads.createiterator.count | request | Number of requests processed. |
| vds.filestor.allthreads.createiterator.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.createiterator.failed | request | Number of failed requests. |
| vds.filestor.allthreads.visit.count | request | Number of requests processed. |
| vds.filestor.allthreads.visit.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.visit.docs | document | Number of entries read per iterate call |
| vds.filestor.allthreads.visit.failed | request | Number of failed requests. |
| vds.filestor.allthreads.remove_location.count | request | Number of requests processed. |
| vds.filestor.allthreads.remove_location.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.remove_location.failed | request | Number of failed requests. |
| vds.filestor.allthreads.splitbuckets.count | request | Number of requests processed. |
| vds.filestor.allthreads.splitbuckets.failed | request | Number of failed requests. |
| vds.filestor.allthreads.splitbuckets.latency | request | Latency of successful requests. |
| vds.filestor.allthreads.joinbuckets.count | request | Number of requests processed. |
| vds.filestor.allthreads.joinbuckets.failed | request | Number of failed requests. |
| vds.filestor.allthreads.joinbuckets.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.deletebuckets.count | request | Number of requests processed. |
| vds.filestor.allthreads.deletebuckets.failed | request | Number of failed requests. |
| vds.filestor.allthreads.deletebuckets.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.remove_by_gid.count | request | Number of requests processed. |
| vds.filestor.allthreads.remove_by_gid.failed | request | Number of failed requests. |
| vds.filestor.allthreads.remove_by_gid.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.setbucketstates.count | request | Number of requests processed. |
| vds.filestor.allthreads.setbucketstates.failed | request | Number of failed requests. |
| vds.filestor.allthreads.setbucketstates.latency | millisecond | Latency of successful requests. |
| vds.mergethrottler.averagequeuewaitingtime | millisecond | Time merges spent in the throttler queue |
| vds.mergethrottler.queuesize | instance | Length of merge queue |
| vds.mergethrottler.active_window_size | instance | Number of merges active within the pending window size |
| vds.mergethrottler.estimated_merge_memory_usage | byte | An estimated upper bound of the memory usage (in bytes) of the merges currently in the active window |
| vds.mergethrottler.bounced_due_to_back_pressure | instance | Number of merges bounced due to resource exhaustion back-pressure |
| vds.mergethrottler.locallyexecutedmerges.ok | instance | The number of successful merges for 'locallyexecutedmerges' |
| vds.mergethrottler.locallyexecutedmerges.failures.aborted | operation | The number of merges that failed because the storage node was (most likely) shutting down |
| vds.mergethrottler.locallyexecutedmerges.failures.bucketnotfound | operation | The number of operations that failed because the bucket did not exist |
| vds.mergethrottler.locallyexecutedmerges.failures.busy | operation | The number of merges that failed because the storage node was busy |
| vds.mergethrottler.locallyexecutedmerges.failures.exists | operation | The number of merges that were rejected due to a merge operation for their bucket already being processed |
| vds.mergethrottler.locallyexecutedmerges.failures.notready | operation | The number of merges discarded because distributor was not ready |
| vds.mergethrottler.locallyexecutedmerges.failures.other | operation | The number of other failures |
| vds.mergethrottler.locallyexecutedmerges.failures.rejected | operation | The number of merges that were rejected |
| vds.mergethrottler.locallyexecutedmerges.failures.timeout | operation | The number of merges that failed because they timed out towards storage |
| vds.mergethrottler.locallyexecutedmerges.failures.total | operation | Sum of all failures |
| vds.mergethrottler.locallyexecutedmerges.failures.wrongdistribution | operation | The number of merges that were discarded (flushed) because they were initiated at an older cluster state than the current |
| vds.mergethrottler.mergechains.ok | operation | The number of successful merges for 'mergechains' |
| vds.mergethrottler.mergechains.failures.busy | operation | The number of merges that failed because the storage node was busy |
| vds.mergethrottler.mergechains.failures.total | operation | Sum of all failures |
| vds.mergethrottler.mergechains.failures.exists | operation | The number of merges that were rejected due to a merge operation for their bucket already being processed |
| vds.mergethrottler.mergechains.failures.notready | operation | The number of merges discarded because distributor was not ready |
| vds.mergethrottler.mergechains.failures.other | operation | The number of other failures |
| vds.mergethrottler.mergechains.failures.rejected | operation | The number of merges that were rejected |
| vds.mergethrottler.mergechains.failures.timeout | operation | The number of merges that failed because they timed out towards storage |
| vds.mergethrottler.mergechains.failures.wrongdistribution | operation | The number of merges that were discarded (flushed) because they were initiated at an older cluster state than the current |
| vds.server.network.tls-handshakes-failed | operation | Number of client or server connection attempts that failed during TLS handshaking |
| vds.server.network.peer-authorization-failures | failure | Number of TLS connection attempts failed due to bad or missing peer certificate credentials |
| vds.server.network.client.tls-connections-established | connection | Number of secure mTLS connections established |
| vds.server.network.server.tls-connections-established | connection | Number of secure mTLS connections established |
| vds.server.network.client.insecure-connections-established | connection | Number of insecure (plaintext) connections established |
| vds.server.network.server.insecure-connections-established | connection | Number of insecure (plaintext) connections established |
| vds.server.network.tls-connections-broken | connection | Number of TLS connections broken due to failures during frame encoding or decoding |
| vds.server.network.failed-tls-config-reloads | failure | Number of times background reloading of TLS config has failed |
| vds.bouncer.unavailable_node_aborts | operation | Number of operations that were aborted due to the node (or target bucket space) being unavailable |
| vds.changedbucketownershiphandler.avg_abort_processing_time | millisecond | Average time spent aborting operations for changed buckets |
| vds.changedbucketownershiphandler.external_load_ops_aborted | operation | Number of outdated external load operations aborted |
| vds.changedbucketownershiphandler.ideal_state_ops_aborted | operation | Number of outdated ideal state operations aborted |
| vds.communication.bucket_space_mapping_failures | operation | Number of messages that could not be resolved to a known bucket space |
| vds.communication.convertfailures | operation | Number of messages that failed to get converted to storage API messages |
| vds.communication.exceptionmessageprocesstime | millisecond | Time transport thread uses to process a single message that fails with an exception thrown into communication manager |
| vds.communication.messageprocesstime | millisecond | Time transport thread uses to process a single message |
| vds.communication.messagequeue | item | Size of input message queue. |
| vds.communication.sendcommandlatency | millisecond | Average ms used to send commands to MBUS |
| vds.communication.sendreplylatency | millisecond | Average ms used to send replies to MBUS |
| vds.communication.toolittlememory | operation | Number of messages failed due to too little memory available |
| vds.datastored.bucket_space.active_buckets | bucket | Number of active buckets in the bucket space |
| vds.datastored.bucket_space.bucket_db.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| vds.datastored.bucket_space.bucket_db.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| vds.datastored.bucket_space.bucket_db.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| vds.datastored.bucket_space.bucket_db.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| vds.datastored.bucket_space.buckets_total | bucket | Total number buckets present in the bucket space (ready + not ready) |
| vds.datastored.bucket_space.entries | document | Number of entries (documents + tombstones) stored in the bucket space |
| vds.datastored.bucket_space.bytes | byte | Bytes stored across all documents in the bucket space |
| vds.datastored.bucket_space.docs | document | Documents stored in the bucket space |
| vds.datastored.bucket_space.ready_buckets | bucket | Number of ready buckets in the bucket space |
| vds.datastored.fullbucketinfolatency | millisecond | Amount of time spent to process a full bucket info request |
| vds.datastored.fullbucketinforeqsize | node | Amount of distributors answered at once in full bucket info requests. |
| vds.datastored.simplebucketinforeqsize | bucket | Amount of buckets returned in simple bucket info requests |
| vds.filestor.allthreads.applybucketdiff.count | request | Number of requests processed. |
| vds.filestor.allthreads.applybucketdiff.failed | request | Number of failed requests. |
| vds.filestor.allthreads.applybucketdiff.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.applybucketdiffreply | request | Number of applybucketdiff replies that have been processed. |
| vds.filestor.allthreads.bucketfixed | bucket | Number of times bucket has been fixed because of corruption |
| vds.filestor.allthreads.bucketverified.count | request | Number of requests processed. |
| vds.filestor.allthreads.bucketverified.failed | request | Number of failed requests. |
| vds.filestor.allthreads.bucketverified.latency | request | Latency of successful requests. |
| vds.filestor.allthreads.bytesmerged | byte | Total number of bytes merged into this node. |
| vds.filestor.allthreads.createbuckets.count | request | Number of requests processed. |
| vds.filestor.allthreads.createbuckets.failed | request | Number of failed requests. |
| vds.filestor.allthreads.createbuckets.latency | request | Latency of successful requests. |
| vds.filestor.allthreads.failedoperations | operation | Number of operations throwing exceptions. |
| vds.filestor.allthreads.getbucketdiff.count | request | Number of requests processed. |
| vds.filestor.allthreads.getbucketdiff.failed | request | Number of failed requests. |
| vds.filestor.allthreads.getbucketdiff.latency | request | Latency of successful requests. |
| vds.filestor.allthreads.getbucketdiffreply | request | Number of getbucketdiff replies that have been processed. |
| vds.filestor.allthreads.internaljoin.count | request | Number of requests processed. |
| vds.filestor.allthreads.internaljoin.failed | request | Number of failed requests. |
| vds.filestor.allthreads.internaljoin.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.movedbuckets.count | request | Number of requests processed. |
| vds.filestor.allthreads.movedbuckets.failed | request | Number of failed requests. |
| vds.filestor.allthreads.movedbuckets.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.operations | operation | Number of operations processed. |
| vds.filestor.allthreads.readbucketinfo.count | request | Number of requests processed. |
| vds.filestor.allthreads.readbucketinfo.failed | request | Number of failed requests. |
| vds.filestor.allthreads.readbucketinfo.latency | request | Latency of successful requests. |
| vds.filestor.allthreads.readbucketlist.count | request | Number of requests processed. |
| vds.filestor.allthreads.readbucketlist.failed | request | Number of failed requests. |
| vds.filestor.allthreads.readbucketlist.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.recheckbucketinfo.count | request | Number of requests processed. |
| vds.filestor.allthreads.recheckbucketinfo.failed | request | Number of failed requests. |
| vds.filestor.allthreads.recheckbucketinfo.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.revert.count | request | Number of requests processed. |
| vds.filestor.allthreads.revert.failed | request | Number of failed requests. |
| vds.filestor.allthreads.revert.latency | millisecond | Latency of successful requests. |
| vds.filestor.allthreads.revert.not_found | request | Number of requests that could not be completed due to source document not found. |
| vds.filestor.allthreads.stat_bucket.count | request | Number of requests processed. |
| vds.filestor.allthreads.stat_bucket.failed | request | Number of failed requests. |
| vds.filestor.allthreads.stat_bucket.latency | request | Latency of successful requests. |
| vds.filestor.bucket_db_init_latency | millisecond | Time taken (in ms) to initialize bucket databases with information from the persistence provider |
| vds.filestor.directoryevents | operation | Number of directory events received. |
| vds.filestor.diskevents | operation | Number of disk events received. |
| vds.filestor.partitionevents | operation | Number of partition events received. |
| vds.filestor.pendingmerge | bucket | Number of buckets currently being merged. |
| vds.filestor.waitingforlockrate | operation | Amount of times a filestor thread has needed to wait for lock to take next message in queue. |
| vds.mergethrottler.mergechains.failures.aborted | operation | The number of merges that failed because the storage node was (most likely) shutting down |
| vds.mergethrottler.mergechains.failures.bucketnotfound | operation | The number of operations that failed because the bucket did not exist |
| vds.server.memoryusage | byte | Amount of memory used by the storage subsystem |
| vds.server.memoryusage_visiting | byte | Message use from visiting |
| vds.server.message_memory_use.highpri | byte | Message use from high priority storage messages |
| vds.server.message_memory_use.lowpri | byte | Message use from low priority storage messages |
| vds.server.message_memory_use.normalpri | byte | Message use from normal priority storage messages |
| vds.server.message_memory_use.total | byte | Message use from storage messages |
| vds.server.message_memory_use.veryhighpri | byte | Message use from very high priority storage messages |
| vds.state_manager.invoke_state_listeners_latency | millisecond | Time spent (in ms) propagating state changes to internal state listeners |
| vds.visitor.cv_queueevictedwaittime | millisecond | Milliseconds waiting in create visitor queue, for visitors that was evicted from queue due to higher priority visitors coming |
| vds.visitor.cv_queuefull | operation | Number of create visitor messages failed as queue is full |
| vds.visitor.cv_queuesize | item | Size of create visitor queue |
| vds.visitor.cv_queuetimeoutwaittime | millisecond | Milliseconds waiting in create visitor queue, for visitors that timed out while in the visitor queue |
| vds.visitor.cv_queuewaittime | millisecond | Milliseconds waiting in create visitor queue, for visitors that was added to visitor queue but scheduled later |
| vds.visitor.cv_skipqueue | operation | Number of times we could skip queue as we had free visitor spots |
| vds.server.network.rpc-capability-checks-failed | failure | Number of RPC operations that failed due to one or more missing capabilities |
| vds.server.network.status-capability-checks-failed | failure | Number of status page operations that failed due to one or more missing capabilities |
| vds.server.fnet.num-connections | connection | Total number of connection objects |
