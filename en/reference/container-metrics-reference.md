---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Container Metrics"
---

| Name | Unit | Description |
| --- | --- | --- |
| http.status.1xx | response | Number of responses with a 1xx status |
| http.status.2xx | response | Number of responses with a 2xx status |
| http.status.3xx | response | Number of responses with a 3xx status |
| http.status.4xx | response | Number of responses with a 4xx status |
| http.status.5xx | response | Number of responses with a 5xx status |
| application_generation | version | The currently live application config generation (aka session id) |
| in_service | binary | This will have the value 1 if the node is in service, 0 if not. |
| jdisc.gc.count | operation | Number of JVM garbage collections done |
| jdisc.gc.ms | millisecond | Time spent in JVM garbage collection |
| jdisc.jvm | version | JVM runtime version |
| cpu | thread | Container service CPU pressure |
| jdisc.memory_mappings | operation | JDISC Memory mappings |
| jdisc.open_file_descriptors | item | JDISC Open file descriptors |
| jdisc.thread_pool.unhandled_exceptions | thread | Number of exceptions thrown by tasks |
| jdisc.thread_pool.work_queue.capacity | thread | Capacity of the task queue |
| jdisc.thread_pool.work_queue.size | thread | Size of the task queue |
| jdisc.thread_pool.rejected_tasks | thread | Number of tasks rejected by the thread pool |
| jdisc.thread_pool.size | thread | Size of the thread pool |
| jdisc.thread_pool.max_allowed_size | thread | The maximum allowed number of threads in the pool |
| jdisc.thread_pool.active_threads | thread | Number of threads that are active |
| jdisc.deactivated_containers.total | item | JDISC Deactivated container instances |
| jdisc.deactivated_containers.with_retained_refs.last | item | JDISC Deactivated container nodes with retained refs |
| jdisc.application.failed_component_graphs | item | JDISC Application failed component graphs |
| jdisc.application.component_graph.creation_time_millis | millisecond | JDISC Application component graph creation time |
| jdisc.application.component_graph.reconfigurations | item | JDISC Application component graph reconfigurations |
| jdisc.singleton.is_active | item | JDISC Singleton is active |
| jdisc.singleton.activation.count | operation | JDISC Singleton activations |
| jdisc.singleton.activation.failure.count | operation | JDISC Singleton activation failures |
| jdisc.singleton.activation.millis | millisecond | JDISC Singleton activation time |
| jdisc.singleton.deactivation.count | operation | JDISC Singleton deactivations |
| jdisc.singleton.deactivation.failure.count | operation | JDISC Singleton deactivation failures |
| jdisc.singleton.deactivation.millis | millisecond | JDISC Singleton deactivation time |
| jdisc.http.ssl.handshake.failure.missing_client_cert | operation | JDISC HTTP SSL Handshake failures due to missing client certificate |
| jdisc.http.ssl.handshake.failure.expired_client_cert | operation | JDISC HTTP SSL Handshake failures due to expired client certificate |
| jdisc.http.ssl.handshake.failure.invalid_client_cert | operation | JDISC HTTP SSL Handshake failures due to invalid client certificate |
| jdisc.http.ssl.handshake.failure.incompatible_protocols | operation | JDISC HTTP SSL Handshake failures due to incompatible protocols |
| jdisc.http.ssl.handshake.failure.incompatible_chifers | operation | JDISC HTTP SSL Handshake failures due to incompatible chifers |
| jdisc.http.ssl.handshake.failure.connection_closed | operation | JDISC HTTP SSL Handshake failures due to connection closed |
| jdisc.http.ssl.handshake.failure.unknown | operation | JDISC HTTP SSL Handshake failures for unknown reason |
| jdisc.http.request.prematurely_closed | request | HTTP requests prematurely closed |
| jdisc.http.request.requests_per_connection | request | HTTP requests per connection |
| jdisc.http.request.uri_length | byte | HTTP URI length |
| jdisc.http.request.content_size | byte | HTTP request content size |
| jdisc.http.requests | request | HTTP requests |
| jdisc.http.requests.status | request | Number of requests to the built-in status handler |
| jdisc.http.filter.rule.blocked_requests | request | Number of requests blocked by filter |
| jdisc.http.filter.rule.allowed_requests | request | Number of requests allowed by filter |
| jdisc.http.filtering.request.handled | request | Number of filtering requests handled |
| jdisc.http.filtering.request.unhandled | request | Number of filtering requests unhandled |
| jdisc.http.filtering.response.handled | request | Number of filtering responses handled |
| jdisc.http.filtering.response.unhandled | request | Number of filtering responses unhandled |
| jdisc.http.handler.unhandled_exceptions | request | Number of unhandled exceptions in handler |
| jdisc.tls.capability_checks.succeeded | operation | Number of TLS capability checks succeeded |
| jdisc.tls.capability_checks.failed | operation | Number of TLS capability checks failed |
| jdisc.http.jetty.threadpool.thread.max | thread | Configured maximum number of threads |
| jdisc.http.jetty.threadpool.thread.min | thread | Configured minimum number of threads |
| jdisc.http.jetty.threadpool.thread.reserved | thread | Configured number of reserved threads or -1 for heuristic |
| jdisc.http.jetty.threadpool.thread.busy | thread | Number of threads executing internal and transient jobs |
| jdisc.http.jetty.threadpool.thread.idle | thread | Number of idle threads |
| jdisc.http.jetty.threadpool.thread.total | thread | Current number of threads |
| jdisc.http.jetty.threadpool.queue.size | thread | Current size of the job queue |
| jdisc.http.jetty.http_compliance.violation | failure | Number of HTTP compliance violations |
| serverNumOpenConnections | connection | The number of currently open connections |
| serverNumConnections | connection | The total number of connections opened |
| serverBytesReceived | byte | The number of bytes received by the server |
| serverBytesSent | byte | The number of bytes sent from the server |
| handled.requests | operation | The number of requests handled per metrics snapshot |
| handled.latency | millisecond | The time used for requests during this metrics snapshot |
| httpapi_latency | millisecond | Duration for requests to the HTTP document APIs |
| httpapi_pending | operation | Document operations pending execution |
| httpapi_num_operations | operation | Total number of document operations performed |
| httpapi_num_updates | operation | Document update operations performed |
| httpapi_num_removes | operation | Document remove operations performed |
| httpapi_num_puts | operation | Document put operations performed |
| httpapi_ops_per_sec | operation_per_second | Document operations per second |
| httpapi_succeeded | operation | Document operations that succeeded |
| httpapi_failed | operation | Document operations that failed |
| httpapi_parse_error | operation | Document operations that failed due to document parse errors |
| httpapi_condition_not_met | operation | Document operations not applied due to condition not met |
| httpapi_not_found | operation | Document operations not applied due to document not found |
| httpapi_failed_unknown | operation | Document operations failed by unknown cause |
| httpapi_failed_timeout | operation | Document operations failed by timeout |
| httpapi_failed_insufficient_storage | operation | Document operations failed by insufficient storage |
| httpapi_queued_operations | operation | Document operations queued for execution in /document/v1 API handler |
| httpapi_queued_bytes | byte | Total operation bytes queued for execution in /document/v1 API handler |
| httpapi_queued_age | second | Age in seconds of the oldest operation in the queue for /document/v1 API handler |
| httpapi_mbus_window_size | operation | The window size of Messagebus's dynamic throttle policy for /document/v1 API handler |
| mem.heap.total | byte | Total available heap memory |
| mem.heap.free | byte | Free heap memory |
| mem.heap.used | byte | Currently used heap memory |
| mem.direct.total | byte | Total available direct memory |
| mem.direct.free | byte | Currently free direct memory |
| mem.direct.used | byte | Direct memory currently used |
| mem.direct.count | byte | Number of direct memory allocations |
| mem.native.total | byte | Total available native memory |
| mem.native.free | byte | Currently free native memory |
| mem.native.used | byte | Native memory currently used |
| athenz-tenant-cert.expiry.seconds | second | Time remaining until Athenz tenant certificate expires |
| container-iam-role.expiry.seconds | second | Time remaining until IAM role expires |
| peak_qps | query_per_second | The highest number of qps for a second for this metrics snapshot |
| search_connections | connection | Number of search connections |
| feed.operations | operation | Number of document feed operations |
| feed.latency | millisecond | Feed latency |
| feed.http-requests | operation | Feed HTTP requests |
| queries | operation | Query volume |
| query_container_latency | millisecond | The query execution time consumed in the container |
| query_latency | millisecond | The overall query latency as seen by the container |
| query_timeout | millisecond | The amount of time allowed for query execution, from the client |
| failed_queries | operation | The number of failed queries |
| degraded_queries | operation | The number of degraded queries, e.g. due to some content nodes not responding in time |
| hits_per_query | hit_per_query | The number of hits returned |
| query_hit_offset | hit | The offset for hits returned |
| documents_covered | document | The combined number of documents considered during query evaluation |
| documents_total | document | The number of documents to be evaluated if all requests had been fully executed |
| documents_target_total | document | The target number of total documents to be evaluated when all data is in sync |
| jdisc.render.latency | nanosecond | The time used by the container to render responses |
| query_item_count | item | The number of query items (terms, phrases, etc.) |
| docproc.proctime | millisecond | Time spent processing document |
| docproc.documents | document | Number of processed documents |
| totalhits_per_query | hit_per_query | The total number of documents found to match queries |
| empty_results | operation | Number of queries matching no documents |
| requestsOverQuota | operation | The number of requests rejected due to exceeding quota |
| relevance.at_1 | score | The relevance of hit number 1 |
| relevance.at_3 | score | The relevance of hit number 3 |
| relevance.at_10 | score | The relevance of hit number 10 |
| error.timeout | operation | Requests that timed out |
| error.backends_oos | operation | Requests that failed due to no available backends nodes |
| error.plugin_failure | operation | Requests that failed due to plugin failure |
| error.backend_communication_error | operation | Requests that failed due to backend communication error |
| error.empty_document_summaries | operation | Requests that failed due to missing document summaries |
| error.illegal_query | operation | Requests that failed due to illegal queries |
| error.invalid_query_parameter | operation | Requests that failed due to invalid query parameters |
| error.internal_server_error | operation | Requests that failed due to internal server error |
| error.misconfigured_server | operation | Requests that failed due to misconfigured server |
| error.invalid_query_transformation | operation | Requests that failed due to invalid query transformation |
| error.results_with_errors | operation | The number of queries with error payload |
| error.unspecified | operation | Requests that failed for an unspecified reason |
| error.unhandled_exception | operation | Requests that failed due to an unhandled exception |
| serverRejectedRequests | operation | Deprecated. Use jdisc.thread_pool.rejected_tasks instead. |
| serverThreadPoolSize | thread | Deprecated. Use jdisc.thread_pool.size instead. |
| serverActiveThreads | thread | Deprecated. Use jdisc.thread_pool.active_threads instead. |
| jrt.transport.tls-certificate-verification-failures | failure | TLS certificate verification failures |
| jrt.transport.peer-authorization-failures | failure | TLS peer authorization failures |
| jrt.transport.server.tls-connections-established | connection | TLS server connections established |
| jrt.transport.client.tls-connections-established | connection | TLS client connections established |
| jrt.transport.server.unencrypted-connections-established | connection | Unencrypted server connections established |
| jrt.transport.client.unencrypted-connections-established | connection | Unencrypted client connections established |
| max_query_latency | millisecond | Deprecated. Use query_latency.max instead |
| mean_query_latency | millisecond | Deprecated. Use the expression (query_latency.sum / query_latency.count) instead |
| jdisc.http.filter.athenz.accepted_requests | request | Number of requests accepted by the AthenzAuthorization filter |
| jdisc.http.filter.athenz.rejected_requests | request | Number of requests rejected by the AthenzAuthorization filter |
| jdisc.http.filter.athenz.grid_requests | request | Number of grid requests |
| serverConnectionsOpenMax | connection | Maximum number of open connections |
| serverConnectionDurationMax | millisecond | Longest duration a connection is kept open |
| serverConnectionDurationMean | millisecond | Average duration a connection is kept open |
| serverConnectionDurationStdDev | millisecond | Standard deviation of open connection duration |
| serverNumRequests | request | Number of requests |
| serverNumSuccessfulResponses | request | Number of successful responses |
| serverNumFailedResponses | request | Number of failed responses |
| serverNumSuccessfulResponseWrites | request | Number of successful response writes |
| serverNumFailedResponseWrites | request | Number of failed response writes |
| serverTotalSuccessfulResponseLatency | millisecond | Total duration for execution of successful responses |
| serverTotalFailedResponseLatency | millisecond | Total duration for execution of failed responses |
| serverTimeToFirstByte | millisecond | Time from request has been received by the server until the first byte is returned to the client |
| serverStartedMillis | millisecond | Time since the service was started |
| embedder.latency | millisecond | Time spent creating an embedding |
| embedder.sequence_length | byte | Size of sequence produced by tokenizer |
| jvm.buffer.count | buffer | An estimate of the number of buffers in the pool |
| jvm.buffer.memory.used | byte | An estimate of the memory that the Java virtual machine is using for this buffer pool |
| jvm.buffer.total.capacity | byte | An estimate of the total capacity of the buffers in this pool |
| jvm.classes.loaded | class | The number of classes that are currently loaded in the Java virtual machine |
| jvm.classes.unloaded | class | The total number of classes unloaded since the Java virtual machine has started execution |
| jvm.gc.concurrent.phase.time | second | Time spent in concurrent phase |
| jvm.gc.live.data.size | byte | Size of long-lived heap memory pool after reclamation |
| jvm.gc.max.data.size | byte | Max size of long-lived heap memory pool |
| jvm.gc.memory.allocated | byte | Incremented for an increase in the size of the (young) heap memory pool after one GC to before the next |
| jvm.gc.memory.promoted | byte | Count of positive increases in the size of the old generation memory pool before GC to after GC |
| jvm.gc.overhead | percentage | An approximation of the percent of CPU time used by GC activities |
| jvm.gc.pause | second | Time spent in GC pause |
| jvm.memory.committed | byte | The amount of memory in bytes that is committed for the Java virtual machine to use |
| jvm.memory.max | byte | The maximum amount of memory in bytes that can be used for memory management |
| jvm.memory.usage.after.gc | percentage | The percentage of long-lived heap pool used after the last GC event |
| jvm.memory.used | byte | The amount of used memory |
| jvm.threads.daemon | thread | The current number of live daemon threads |
| jvm.threads.live | thread | The current number of live threads including both daemon and non-daemon threads |
| jvm.threads.peak | thread | The peak live thread count since the Java virtual machine started or peak was reset |
| jvm.threads.started | thread | The total number of application threads started in the JVM |
| jvm.threads.states | thread | The current number of threads (in each state) |
