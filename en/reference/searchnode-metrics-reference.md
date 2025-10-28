---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "SearchNode Metrics"
---

| Name | Unit | Description |
| --- | --- | --- |
| content.proton.config.generation | version | The oldest config generation used by this search node |
| content.proton.documentdb.documents.total | document | The total number of documents in this documents db (ready + not-ready) |
| content.proton.documentdb.documents.ready | document | The number of ready documents in this document db |
| content.proton.documentdb.documents.active | document | The number of active / searchable documents in this document db |
| content.proton.documentdb.documents.removed | document | The number of removed documents in this document db |
| content.proton.documentdb.index.docs_in_memory | document | Number of documents in memory index |
| content.proton.documentdb.disk_usage | byte | The total disk usage (in bytes) for this document db |
| content.proton.documentdb.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| content.proton.documentdb.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| content.proton.documentdb.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| content.proton.documentdb.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| content.proton.documentdb.heart_beat_age | second | How long ago (in seconds) heart beat maintenance job was run |
| content.proton.docsum.count | request | Docsum requests handled |
| content.proton.docsum.docs | document | Total docsums returned |
| content.proton.docsum.latency | millisecond | Docsum request latency |
| content.proton.search_protocol.query.latency | second | Query request latency (seconds) |
| content.proton.search_protocol.query.request_size | byte | Query request size (network bytes) |
| content.proton.search_protocol.query.reply_size | byte | Query reply size (network bytes) |
| content.proton.search_protocol.docsum.latency | second | Docsum request latency (seconds) |
| content.proton.search_protocol.docsum.request_size | byte | Docsum request size (network bytes) |
| content.proton.search_protocol.docsum.reply_size | byte | Docsum reply size (network bytes) |
| content.proton.search_protocol.docsum.requested_documents | document | Total requested document summaries |
| content.proton.executor.proton.queuesize | task | Size of executor proton task queue |
| content.proton.executor.proton.accepted | task | Number of executor proton accepted tasks |
| content.proton.executor.proton.wakeups | wakeup | Number of times an executor proton worker thread has been woken up |
| content.proton.executor.proton.utilization | fraction | Ratio of time the executor proton worker threads has been active |
| content.proton.executor.proton.rejected | task | Number of rejected tasks |
| content.proton.executor.flush.queuesize | task | Size of executor flush task queue |
| content.proton.executor.flush.accepted | task | Number of accepted executor flush tasks |
| content.proton.executor.flush.wakeups | wakeup | Number of times an executor flush worker thread has been woken up |
| content.proton.executor.flush.utilization | fraction | Ratio of time the executor flush worker threads has been active |
| content.proton.executor.flush.rejected | task | Number of rejected tasks |
| content.proton.executor.match.queuesize | task | Size of executor match task queue |
| content.proton.executor.match.accepted | task | Number of accepted executor match tasks |
| content.proton.executor.match.wakeups | wakeup | Number of times an executor match worker thread has been woken up |
| content.proton.executor.match.utilization | fraction | Ratio of time the executor match worker threads has been active |
| content.proton.executor.match.rejected | task | Number of rejected tasks |
| content.proton.executor.docsum.queuesize | task | Size of executor docsum task queue |
| content.proton.executor.docsum.accepted | task | Number of executor accepted docsum tasks |
| content.proton.executor.docsum.wakeups | wakeup | Number of times an executor docsum worker thread has been woken up |
| content.proton.executor.docsum.utilization | fraction | Ratio of time the executor docsum worker threads has been active |
| content.proton.executor.docsum.rejected | task | Number of rejected tasks |
| content.proton.executor.shared.queuesize | task | Size of executor shared task queue |
| content.proton.executor.shared.accepted | task | Number of executor shared accepted tasks |
| content.proton.executor.shared.wakeups | wakeup | Number of times an executor shared worker thread has been woken up |
| content.proton.executor.shared.utilization | fraction | Ratio of time the executor shared worker threads has been active |
| content.proton.executor.shared.rejected | task | Number of rejected tasks |
| content.proton.executor.warmup.queuesize | task | Size of executor warmup task queue |
| content.proton.executor.warmup.accepted | task | Number of accepted executor warmup tasks |
| content.proton.executor.warmup.wakeups | wakeup | Number of times a warmup executor worker thread has been woken up |
| content.proton.executor.warmup.utilization | fraction | Ratio of time the executor warmup worker threads has been active |
| content.proton.executor.warmup.rejected | task | Number of rejected tasks |
| content.proton.executor.field_writer.queuesize | task | Size of executor field writer task queue |
| content.proton.executor.field_writer.accepted | task | Number of accepted executor field writer tasks |
| content.proton.executor.field_writer.wakeups | wakeup | Number of times an executor field writer worker thread has been woken up |
| content.proton.executor.field_writer.utilization | fraction | Ratio of time the executor fieldwriter worker threads has been active |
| content.proton.executor.field_writer.saturation | fraction | Ratio indicating the max saturation of underlying worker threads. A higher saturation than utilization indicates a bottleneck in one of the worker threads. |
| content.proton.executor.field_writer.rejected | task | Number of rejected tasks |
| content.proton.documentdb.job.total | fraction | The job load average total of all job metrics |
| content.proton.documentdb.job.attribute_flush | fraction | Flushing of attribute vector(s) to disk |
| content.proton.documentdb.job.memory_index_flush | fraction | Flushing of memory index to disk |
| content.proton.documentdb.job.disk_index_fusion | fraction | Fusion of disk indexes |
| content.proton.documentdb.job.document_store_flush | fraction | Flushing of document store to disk |
| content.proton.documentdb.job.document_store_compact | fraction | Compaction of document store on disk |
| content.proton.documentdb.job.bucket_move | fraction | Moving of buckets between 'ready' and 'notready' sub databases |
| content.proton.documentdb.job.lid_space_compact | fraction | Compaction of lid space in document meta store and attribute vectors |
| content.proton.documentdb.job.removed_documents_prune | fraction | Pruning of removed documents in 'removed' sub database |
| content.proton.documentdb.threading_service.master.queuesize | task | Size of threading service master task queue |
| content.proton.documentdb.threading_service.master.accepted | task | Number of accepted threading service master tasks |
| content.proton.documentdb.threading_service.master.wakeups | wakeup | Number of times a threading service master worker thread has been woken up |
| content.proton.documentdb.threading_service.master.utilization | fraction | Ratio of time the threading service master worker threads has been active |
| content.proton.documentdb.threading_service.master.rejected | task | Number of rejected tasks |
| content.proton.documentdb.threading_service.index.queuesize | task | Size of threading service index task queue |
| content.proton.documentdb.threading_service.index.accepted | task | Number of accepted threading service index tasks |
| content.proton.documentdb.threading_service.index.wakeups | wakeup | Number of times a threading service index worker thread has been woken up |
| content.proton.documentdb.threading_service.index.utilization | fraction | Ratio of time the threading service index worker threads has been active |
| content.proton.documentdb.threading_service.index.rejected | task | Number of rejected tasks |
| content.proton.documentdb.threading_service.summary.queuesize | task | Size of threading service summary task queue |
| content.proton.documentdb.threading_service.summary.accepted | task | Number of accepted threading service summary tasks |
| content.proton.documentdb.threading_service.summary.wakeups | wakeup | Number of times a threading service summary worker thread has been woken up |
| content.proton.documentdb.threading_service.summary.utilization | fraction | Ratio of time the threading service summary worker threads has been active |
| content.proton.documentdb.threading_service.summary.rejected | task | Number of rejected tasks |
| content.proton.documentdb.threading_service.attribute_field_writer.accepted | task | Number of accepted tasks |
| content.proton.documentdb.threading_service.attribute_field_writer.queuesize | task | Size of task queue |
| content.proton.documentdb.threading_service.attribute_field_writer.rejected | task | Number of rejected tasks |
| content.proton.documentdb.threading_service.attribute_field_writer.utilization | fraction | Ratio of time the worker threads has been active |
| content.proton.documentdb.threading_service.attribute_field_writer.wakeups | wakeup | Number of times a worker thread has been woken up |
| content.proton.documentdb.threading_service.index_field_inverter.accepted | task | Number of accepted tasks |
| content.proton.documentdb.threading_service.index_field_inverter.queuesize | task | Size of task queue |
| content.proton.documentdb.threading_service.index_field_inverter.rejected | task | Number of rejected tasks |
| content.proton.documentdb.threading_service.index_field_inverter.utilization | fraction | Ratio of time the worker threads has been active |
| content.proton.documentdb.threading_service.index_field_inverter.wakeups | wakeup | Number of times a worker thread has been woken up |
| content.proton.documentdb.threading_service.index_field_writer.accepted | task | Number of accepted tasks |
| content.proton.documentdb.threading_service.index_field_writer.queuesize | task | Size of task queue |
| content.proton.documentdb.threading_service.index_field_writer.rejected | task | Number of rejected tasks |
| content.proton.documentdb.threading_service.index_field_writer.utilization | fraction | Ratio of time the worker threads has been active |
| content.proton.documentdb.threading_service.index_field_writer.wakeups | wakeup | Number of times a worker thread has been woken up |
| content.proton.documentdb.ready.lid_space.lid_bloat_factor | fraction | The bloat factor of this lid space, indicating the total amount of holes in the allocated lid space ((lid_limit - used_lids) / lid_limit) |
| content.proton.documentdb.ready.lid_space.lid_fragmentation_factor | fraction | The fragmentation factor of this lid space, indicating the amount of holes in the currently used part of the lid space ((highest_used_lid - used_lids) / highest_used_lid) |
| content.proton.documentdb.ready.lid_space.lid_limit | documentid | The size of the allocated lid space |
| content.proton.documentdb.ready.lid_space.highest_used_lid | documentid | The highest used lid |
| content.proton.documentdb.ready.lid_space.used_lids | documentid | The number of lids used |
| content.proton.documentdb.ready.lid_space.lowest_free_lid | documentid | The lowest free local document id |
| content.proton.documentdb.notready.lid_space.lid_bloat_factor | fraction | The bloat factor of this lid space, indicating the total amount of holes in the allocated lid space ((lid_limit - used_lids) / lid_limit) |
| content.proton.documentdb.notready.lid_space.lid_fragmentation_factor | fraction | The fragmentation factor of this lid space, indicating the amount of holes in the currently used part of the lid space ((highest_used_lid - used_lids) / highest_used_lid) |
| content.proton.documentdb.notready.lid_space.lid_limit | documentid | The size of the allocated lid space |
| content.proton.documentdb.notready.lid_space.highest_used_lid | documentid | The highest used lid |
| content.proton.documentdb.notready.lid_space.used_lids | documentid | The number of lids used |
| content.proton.documentdb.notready.lid_space.lowest_free_lid | documentid | The lowest free local document id |
| content.proton.documentdb.removed.lid_space.lid_bloat_factor | fraction | The bloat factor of this lid space, indicating the total amount of holes in the allocated lid space ((lid_limit - used_lids) / lid_limit) |
| content.proton.documentdb.removed.lid_space.lid_fragmentation_factor | fraction | The fragmentation factor of this lid space, indicating the amount of holes in the currently used part of the lid space ((highest_used_lid - used_lids) / highest_used_lid) |
| content.proton.documentdb.removed.lid_space.lid_limit | documentid | The size of the allocated lid space |
| content.proton.documentdb.removed.lid_space.highest_used_lid | documentid | The highest used lid |
| content.proton.documentdb.removed.lid_space.used_lids | documentid | The number of lids used |
| content.proton.documentdb.removed.lid_space.lowest_free_lid | documentid | The lowest free local document id |
| content.proton.documentdb.bucket_move.buckets_pending | bucket | The number of buckets left to move |
| content.proton.resource_usage.disk | fraction | The relative amount of disk used by this content node (transient usage not included, value in the range [0, 1]). Same value as reported to the cluster controller |
| content.proton.resource_usage.disk_usage.total | fraction | The total relative amount of disk used by this content node (value in the range [0, 1]) |
| content.proton.resource_usage.disk_usage.total_utilization | fraction | The relative amount of disk used compared to the content node disk resource limit |
| content.proton.resource_usage.disk_usage.transient | fraction | The relative amount of transient disk used by this content node (value in the range [0, 1]) |
| content.proton.resource_usage.memory | fraction | The relative amount of memory used by this content node (transient usage not included, value in the range [0, 1]). Same value as reported to the cluster controller |
| content.proton.resource_usage.memory_usage.total | fraction | The total relative amount of memory used by this content node (value in the range [0, 1]) |
| content.proton.resource_usage.memory_usage.total_utilization | fraction | The relative amount of memory used compared to the content node memory resource limit |
| content.proton.resource_usage.memory_usage.transient | fraction | The relative amount of transient memory used by this content node (value in the range [0, 1]) |
| content.proton.resource_usage.memory_mappings | file | The number of memory mapped files |
| content.proton.resource_usage.open_file_descriptors | file | The number of open files |
| content.proton.resource_usage.feeding_blocked | binary | Whether feeding is blocked due to resource limits being reached (value is either 0 or 1) |
| content.proton.resource_usage.malloc_arena | byte | Size of malloc arena |
| content.proton.documentdb.attribute.resource_usage.address_space | fraction | The max relative address space used among components in all attribute vectors in this document db (value in the range [0, 1]) |
| content.proton.documentdb.attribute.resource_usage.feeding_blocked | binary | Whether feeding is blocked due to attribute resource limits being reached (value is either 0 or 1) |
| content.proton.documentdb.attribute.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| content.proton.documentdb.attribute.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| content.proton.documentdb.attribute.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| content.proton.documentdb.attribute.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| content.proton.resource_usage.cpu_util.setup | fraction | cpu used by system init and (re-)configuration |
| content.proton.resource_usage.cpu_util.read | fraction | cpu used by reading data from the system |
| content.proton.resource_usage.cpu_util.write | fraction | cpu used by writing data to the system |
| content.proton.resource_usage.cpu_util.compact | fraction | cpu used by internal data re-structuring |
| content.proton.resource_usage.cpu_util.other | fraction | cpu used by work not classified as a specific category |
| content.proton.transactionlog.entries | record | The current number of entries in the transaction log |
| content.proton.transactionlog.disk_usage | byte | The disk usage (in bytes) of the transaction log |
| content.proton.transactionlog.replay_time | second | The replay time (in seconds) of the transaction log during start-up |
| content.proton.documentdb.ready.document_store.disk_usage | byte | Disk space usage in bytes |
| content.proton.documentdb.ready.document_store.disk_bloat | byte | Disk space bloat in bytes |
| content.proton.documentdb.ready.document_store.max_bucket_spread | fraction | Max bucket spread in underlying files (sum(unique buckets in each chunk)/unique buckets in file) |
| content.proton.documentdb.ready.document_store.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| content.proton.documentdb.ready.document_store.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| content.proton.documentdb.ready.document_store.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| content.proton.documentdb.ready.document_store.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| content.proton.documentdb.notready.document_store.disk_usage | byte | Disk space usage in bytes |
| content.proton.documentdb.notready.document_store.disk_bloat | byte | Disk space bloat in bytes |
| content.proton.documentdb.notready.document_store.max_bucket_spread | fraction | Max bucket spread in underlying files (sum(unique buckets in each chunk)/unique buckets in file) |
| content.proton.documentdb.notready.document_store.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| content.proton.documentdb.notready.document_store.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| content.proton.documentdb.notready.document_store.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| content.proton.documentdb.notready.document_store.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| content.proton.documentdb.removed.document_store.disk_usage | byte | Disk space usage in bytes |
| content.proton.documentdb.removed.document_store.disk_bloat | byte | Disk space bloat in bytes |
| content.proton.documentdb.removed.document_store.max_bucket_spread | fraction | Max bucket spread in underlying files (sum(unique buckets in each chunk)/unique buckets in file) |
| content.proton.documentdb.removed.document_store.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| content.proton.documentdb.removed.document_store.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| content.proton.documentdb.removed.document_store.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| content.proton.documentdb.removed.document_store.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| content.proton.documentdb.ready.document_store.cache.elements | item | Number of elements in the cache |
| content.proton.documentdb.ready.document_store.cache.memory_usage | byte | Memory usage of the cache (in bytes) |
| content.proton.documentdb.ready.document_store.cache.hit_rate | fraction | Rate of hits in the cache compared to number of lookups |
| content.proton.documentdb.ready.document_store.cache.lookups | operation | Number of lookups in the cache (hits + misses) |
| content.proton.documentdb.ready.document_store.cache.invalidations | operation | Number of invalidations (erased elements) in the cache. |
| content.proton.documentdb.notready.document_store.cache.elements | item | Number of elements in the cache |
| content.proton.documentdb.notready.document_store.cache.memory_usage | byte | Memory usage of the cache (in bytes) |
| content.proton.documentdb.notready.document_store.cache.hit_rate | fraction | Rate of hits in the cache compared to number of lookups |
| content.proton.documentdb.notready.document_store.cache.lookups | operation | Number of lookups in the cache (hits + misses) |
| content.proton.documentdb.notready.document_store.cache.invalidations | operation | Number of invalidations (erased elements) in the cache. |
| content.proton.documentdb.removed.document_store.cache.elements | item | Number of elements in the cache |
| content.proton.documentdb.removed.document_store.cache.hit_rate | fraction | Rate of hits in the cache compared to number of lookups |
| content.proton.documentdb.removed.document_store.cache.invalidations | item | Number of invalidations (erased elements) in the cache. |
| content.proton.documentdb.removed.document_store.cache.lookups | operation | Number of lookups in the cache (hits + misses) |
| content.proton.documentdb.removed.document_store.cache.memory_usage | byte | Memory usage of the cache (in bytes) |
| content.proton.documentdb.ready.attribute.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| content.proton.documentdb.ready.attribute.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| content.proton.documentdb.ready.attribute.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| content.proton.documentdb.ready.attribute.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| content.proton.documentdb.ready.attribute.disk_usage | byte | Disk space usage (in bytes) of the flushed snapshot of this attribute for this document type |
| content.proton.documentdb.notready.attribute.memory_usage.allocated_bytes | byte | The number of allocated bytes |
| content.proton.documentdb.notready.attribute.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) |
| content.proton.documentdb.notready.attribute.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) |
| content.proton.documentdb.notready.attribute.memory_usage.onhold_bytes | byte | The number of bytes on hold |
| content.proton.index.cache.postinglist.elements | item | Number of elements in the cache. Contains disk index posting list files across all document types |
| content.proton.index.cache.postinglist.memory_usage | byte | Memory usage of the cache (in bytes). Contains disk index posting list files across all document types |
| content.proton.index.cache.postinglist.hit_rate | fraction | Rate of hits in the cache compared to number of lookups. Contains disk index posting list files across all document types |
| content.proton.index.cache.postinglist.lookups | operation | Number of lookups in the cache (hits + misses). Contains disk index posting list files across all document types |
| content.proton.index.cache.postinglist.invalidations | operation | Number of invalidations (erased elements) in the cache. Contains disk index posting list files across all document types |
| content.proton.index.cache.bitvector.elements | item | Number of elements in the cache. Contains disk index bitvector files across all document types |
| content.proton.index.cache.bitvector.memory_usage | byte | Memory usage of the cache (in bytes). Contains disk index bitvector files across all document types |
| content.proton.index.cache.bitvector.hit_rate | fraction | Rate of hits in the cache compared to number of lookups. Contains disk index bitvector files across all document types |
| content.proton.index.cache.bitvector.lookups | operation | Number of lookups in the cache (hits + misses). Contains disk index bitvector files across all document types |
| content.proton.index.cache.bitvector.invalidations | operation | Number of invalidations (erased elements) in the cache. Contains disk index bitvector files across all document types |
| content.proton.documentdb.index.memory_usage.allocated_bytes | byte | The number of allocated bytes for the memory index for this document type |
| content.proton.documentdb.index.memory_usage.used_bytes | byte | The number of used bytes (<= allocated_bytes) for the memory index for this document type |
| content.proton.documentdb.index.memory_usage.dead_bytes | byte | The number of dead bytes (<= used_bytes) for the memory index for this document type |
| content.proton.documentdb.index.memory_usage.onhold_bytes | byte | The number of bytes on hold for the memory index for this document type |
| content.proton.documentdb.index.disk_usage | byte | Disk space usage (in bytes) of all disk indexes for this document type |
| content.proton.documentdb.index.indexes | item | Number of disk or memory indexes |
| content.proton.documentdb.index.io.search.read_bytes | byte | Bytes read from disk index posting list and bitvector files as part of search for this document type |
| content.proton.documentdb.index.io.search.cached_read_bytes | byte | Bytes read from cached disk index posting list and bitvector files as part of search for this document type |
| content.proton.documentdb.ready.index.memory_usage.allocated_bytes | byte | The number of allocated bytes for this index field in the memory index for this document type |
| content.proton.documentdb.ready.index.disk_usage | byte | Disk space usage (in bytes) of this index field in all disk indexes for this document type |
| content.proton.documentdb.matching.queries | query | Number of queries executed |
| content.proton.documentdb.matching.soft_doomed_queries | query | Number of queries hitting the soft timeout |
| content.proton.documentdb.matching.query_latency | second | Total average latency (sec) when matching and ranking a query |
| content.proton.documentdb.matching.query_setup_time | second | Average time (sec) spent setting up and tearing down queries |
| content.proton.documentdb.matching.docs_matched | document | Number of documents matched |
| content.proton.documentdb.matching.docs_ranked | document | Number of documents ranked (first phase) |
| content.proton.documentdb.matching.docs_reranked | document | Number of documents re-ranked (second phase) |
| content.proton.documentdb.matching.rank_profile.queries | query | Number of queries executed |
| content.proton.documentdb.matching.rank_profile.soft_doomed_queries | query | Number of queries hitting the soft timeout |
| content.proton.documentdb.matching.rank_profile.soft_doom_factor | fraction | Factor used to compute soft-timeout |
| content.proton.documentdb.matching.rank_profile.query_latency | second | Total average latency (sec) when matching and ranking a query |
| content.proton.documentdb.matching.rank_profile.query_setup_time | second | Average time (sec) spent setting up and tearing down queries |
| content.proton.documentdb.matching.rank_profile.grouping_time | second | Average time (sec) spent on grouping |
| content.proton.documentdb.matching.rank_profile.rerank_time | second | Average time (sec) spent on 2nd phase ranking |
| content.proton.documentdb.matching.rank_profile.docs_matched | document | Number of documents matched |
| content.proton.documentdb.matching.rank_profile.docs_ranked | document | Number of documents ranked (first phase) |
| content.proton.documentdb.matching.rank_profile.docs_reranked | document | Number of documents re-ranked (second phase) |
| content.proton.documentdb.matching.rank_profile.limited_queries | query | Number of queries limited in match phase |
| content.proton.documentdb.matching.rank_profile.docid_partition.active_time | second | Time (sec) spent doing actual work |
| content.proton.documentdb.matching.rank_profile.docid_partition.docs_matched | document | Number of documents matched |
| content.proton.documentdb.matching.rank_profile.docid_partition.docs_ranked | document | Number of documents ranked (first phase) |
| content.proton.documentdb.matching.rank_profile.docid_partition.docs_reranked | document | Number of documents re-ranked (second phase) |
| content.proton.documentdb.matching.rank_profile.docid_partition.wait_time | second | Time (sec) spent waiting for other external threads and resources |
| content.proton.documentdb.matching.rank_profile.match_time | second | Average time (sec) for matching a query (1st phase) |
| content.proton.documentdb.feeding.commit.operations | operation | Number of operations included in a commit |
| content.proton.documentdb.feeding.commit.latency | second | Latency for commit in seconds |
| content.proton.session_cache.grouping.num_cached | session | Number of currently cached sessions |
| content.proton.session_cache.grouping.num_dropped | session | Number of dropped cached sessions |
| content.proton.session_cache.grouping.num_insert | session | Number of inserted sessions |
| content.proton.session_cache.grouping.num_pick | session | Number if picked sessions |
| content.proton.session_cache.grouping.num_timedout | session | Number of timed out sessions |
| content.proton.session_cache.search.num_cached | session | Number of currently cached sessions |
| content.proton.session_cache.search.num_dropped | session | Number of dropped cached sessions |
| content.proton.session_cache.search.num_insert | session | Number of inserted sessions |
| content.proton.session_cache.search.num_pick | session | Number if picked sessions |
| content.proton.session_cache.search.num_timedout | session | Number of timed out sessions |
| metricmanager.periodichooklatency | millisecond | Time in ms used to update a single periodic hook |
| metricmanager.resetlatency | millisecond | Time in ms used to reset all metrics. |
| metricmanager.sleeptime | millisecond | Time in ms worker thread is sleeping |
| metricmanager.snapshothooklatency | millisecond | Time in ms used to update a single snapshot hook |
| metricmanager.snapshotlatency | millisecond | Time in ms used to take a snapshot |
