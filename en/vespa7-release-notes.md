---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa 7 Release Notes"
---

th, td {
width: 50%;
}

These notes documents the changes between Vespa major versions 6 and 7.
As documented in [Vespa versions](https://vespa.ai/releases#versions),
major versions are used to mark breaking compatibility,
not to release significant new functionality (which instead happens on minor versions).
However, even on major versions, compatibility is broken only in two specific ways: **Changes to defaults** means that
applications may need to set some option explicitly to preserve earlier behavior, and **removal of deprecated functionality**
means that applications *which use functionality that has earlier been deprecated* need to change to keep working.

Most deprecated functionality causes warning during compilation (Java API deprecations) or deployment
(application package deprecations), however with web service APIs there is no way to emit deprecation warnings,
and we have to rely on marking these as deprecated in the documentation.

Given this, application owners need to do 3 tasks to be compatible with Vespa 7:
* Review whether [changes to defaults](#changed-defaults) requires additional settings in the application
  (**note that this is likely** on changing from 6 to 7 due to the changes to tokenization and stemming).* Make sure there are no deprecation warnings on compilation and deployment on Vespa 6.* Review the list of removed web service APIs and API parameters and make sure these are not used by clients of
      the application.

As Vespa 7 does not introduce new functionality, it is as safe and mature as the versions of Vespa 6 preceding it.
Upon release of Vespa 7, no further releases will be made of Vespa 6 for any reason.

## Changes

The following sections lists the changes on moving from Vespa 6 to Vespa 7 which must be reviewed by applications.

### Changed defaults

The following defaults have changed:

| Change | Configuration required to avoid change on Vespa 7 |
| --- | --- |
| `stemming: shortest` changed to `stemming: best` | Add [stemming: shortest](reference/schema-reference.html#stemming) to the `schema` block of all schemas. |
| Default linguistics component changed from SimpleLinguistics to OpenNlpLinguistics, including language detection using Optimaize turned on by default. | Configure `com.yahoo.language.simple.SimpleLinguistics` as a component in services.xml as described in [linguistics in Vespa](linguistics.html) |
| The default format accepted by the Java HTTP client is changed from XML to [JSON](reference/document-json-format.html) | To keep using XML:  * **Java API**: When calling `FeedClientFactory.create(sessionParams, ...)`, pass a `SessionParams`   instance which has a `FeedParams` instance which have `dataFormat` set to   `FeedParams.DataFormat.XML_UTF8` * **Command line**: Pass the `--xmloutput` option. |
| Query timeout changed from 5000 ms to 500 ms. Set the [timeout](reference/query-api-reference.html#timeout) parameter explicitly in requests or query profiles. | |
| [ranking.softtimeout.enable](reference/query-api-reference.html#ranking.softtimeout.enable) changed to default true | Set to `false` in requests or a query profile. |
| The default access log format is changed to [JSON](access-logging.html). | To keep the old proprietary format, set accesslog type=vespa in services.xml as described in [the accesslog reference](reference/services-container.html#accesslog). |
| Default return format in vespa-visit and vespa-get is changed to JSON To get XML output specify the --xmloutput method | |

### JDK version

Java components must be rebuilt with JDK 11 for the Vespa bundle-plugin to generate the
correct set of imported packages for your OSGi bundles.

### Removed Java APIs

Classes and methods that were marked as deprecated in Vespa 6 are removed.
If you get deprecation warnings for Vespa APIs when building your
application, they must be fixed before migrating to Vespa 7.

### Container Runtime Environment

The following maven artifacts are no longer provided runtime:
* commons-codec:commons-codec
* org.apache.httpcomponents:httpclient
* org.apache.httpcomponents:httpcore

If you need any of these dependencies, they must be embedded in your bundle by adding them
in scope 'compile' in pom.xml.

### Removed HTTP APIs

The following HTTP APIs are removed:

| Name | Replacement |
| --- | --- |
| Legacy HTTP apis for document feeding:  * /feed * /remove * /removelocation * /get * /visit * /document | The [/document/v1/](reference/document-v1-api-reference.html) web service API, or (for high throughput) the vespa-http-client. |

### Removed HTTP API parameters

The following HTTP API parameters are removed

| Name | Replacement |
| --- | --- |
| The `defidx` parameter in the search API | Use a custom searcher if this functionality is needed. |

### Removed command line tools

The following command line tools are removed:

| Name | Replacement |
| --- | --- |
| Vespa spooler | Custom client using the Java HTTP client |

### Removed settings from schemas

The following settings are removed from [schemas](reference/schema-reference.html):

| Name | Replacement |
| --- | --- |
| header | None. This setting doesn't have any effect |
| body | None. This setting doesn't have any effect |

### Removed constructs from services.xml

The following tags and attributes are removed from services.xml:

| Name | Replacement |
| --- | --- |
| ‘rotationScheme’ attribute in <container><accesslog> | None, rotation scheme ‘date’ will always be used |
| <container><filter> tag | <container><http><filtering> |

### Removed metrics

The following metrics are removed:

| Name | Replacement |
| --- | --- |
| free/used/totalMemoryBytes | mem.heap.free/used/total |
| http.in.bytes | serverBytesReceived |
| http.out.bytes | serverBytesSent |
| http.requests | serverNumRequests |
| http.latency | serverTotalSuccessfulResponseLatency |
| http.out.firstbytetime | serverTimeToFirstByte |
| proc.uptime | serverStartedMillis |
| proton.* | content.proton.* (note that metrics might have different structure and names in new namespace) |
| vds.filestor.spi.* | vds.filestor.alldisks.allthreads.* |

### Empty fields

Fields containing no value will not be included in responses on Vespa 7.

### Allowed characters in request URIs

Vespa 6 allowed some special characters in raw form in the query component of request URIs.
Vespa 7 requires these characters to be properly percent-encoded (RFC 2396).

| Character | Percent-encoding |
| --- | --- |
| \ | %5C |
| ^ | %5E |
| ` | %60 |
| { | %7B |
| | | %7C |
| } | %7D |

### Changes to the default JSON result format

The content of fields of type **position** in the default JSON query result format was rendered as XML
on Vespa 6 but is rendered as JSON.

Specifically, the content of a position field was rendered as a string like

`<position x="-121996000" y="37401000" latlong="N37.401000;W121.996000"/>`

but is now instead rendered as a JSON map:

```
{
  "y": 37401000,
  "x": -121996000,
  "latlong": "N37.401000;W121.996000"
}
```

### Renamed metrics

The following metrics are renamed:

| Old Name | New Name |
| --- | --- |
| 95p_query_latency | query_latency.95percentile |
| 99p_query_latency | query_latency.99percentile |
| active_queries | active_queries.average |
| athenz-tenant-cert.expiry.seconds | athenz-tenant-cert.expiry.seconds.last |
| bytes | vds.datastored.alldisks.bytes.average |
| configserver.cacheChecksumElems | configserver.cacheChecksumElems.last |
| configserver.cacheConfigElems | configserver.cacheConfigElems.last |
| configserver.delayedResponses | configserver.delayedResponses.count |
| configserver.failedRequests | configserver.failedRequests.count |
| configserver.hosts | configserver.hosts.last |
| configserver.latency | configserver.latency.average |
| configserver.requests | configserver.requests.count |
| configserver.sessionChangeErrors | configserver.sessionChangeErrors.count |
| configserver.zkAvgLatency | configserver.zkAvgLatency.last |
| configserver.zkConnections | configserver.zkConnections.last |
| configserver.zkMaxLatency | configserver.zkMaxLatency.last |
| configserver.zkOutstandingRequests | configserver.zkOutstandingRequests.last |
| configserver.zkZNodes | configserver.zkZNodes.last |
| content.cluster-controller.cluster-state-change.count | cluster-controller.cluster-state-change.count |
| content.proton.memoryusage.max | content.proton.documentdb.memory_usage.allocated_bytes.max |
| content.proton.transport.docsum.latency.average | content.proton.docsum.latency.average |
| degraded_queries | degraded_queries.rate |
| deletefailed | vds.idealstate.delete_bucket.done_failed.rate |
| deleteok | vds.idealstate.delete_bucket.done_ok.rate |
| deletepending | vds.idealstate.delete_bucket.pending.average |
| diskqueuesize | vds.filestor.alldisks.queuesize.average |
| diskqueuewait | vds.filestor.alldisks.averagequeuewait.sum.average |
| diskusage | content.proton.documentdb.disk_usage.last |
| docs | vds.datastored.alldisks.docs.average |
| document_requests | content.proton.docsum.docs.rate |
| documents_active | content.proton.documentdb.documents.active.last |
| documents_inmemory | content.proton.documentdb.index.docs_in_memory.last |
| documents_processed | documents_processed.rate |
| documents_ready | content.proton.documentdb.documents.ready.last |
| documents_removed | content.proton.documentdb.documents.removed.last |
| documents_total | content.proton.documentdb.documents.total.last |
| empty_results | empty_results.rate |
| error.backend_communication_error | error.backend_communication_error.rate |
| error.backends_oos | error.backends_oos.rate |
| error.empty_document_summaries | error.empty_document_summaries.rate |
| error.internal_server_error | error.internal_server_error.rate |
| error.invalid_query_parameter | error.invalid_query_parameter.rate |
| error.invalid_query_transformation | error.invalid_query_transformation.rate |
| error.misconfigured_server | error.misconfigured_server.rate |
| error.plugin_failure | error.plugin_failure.rate |
| error.result_with_errors | error.result_with_errors.rate |
| error.timeout | error.timeout.rate |
| error.unhandled_exception | error.unhandled_exception.rate |
| error.unspecified | error.unspecified.rate |
| failed_queries | failed_queries.rate |
| handled.requests | handled.requests.count |
| hits_per_query | hits_per_query.average |
| joinfailed | vds.idealstate.join_bucket.done_failed.rate |
| joinok | vds.idealstate.join_bucket.done_ok.rate |
| joinpending | vds.idealstate.join_bucket.pending.average |
| logd.processed.lines | logd.processed.lines.count |
| max_query_latency | query_latency.max |
| mean_query_latency | query_latency.average |
| mergefailed | vds.idealstate.merge_bucket.done_failed.rate |
| mergeok | vds.idealstate.merge_bucket.done_ok.rate |
| mergepending | vds.idealstate.merge_bucket.pending.average |
| peak_qps | peak_qps.max |
| queries | queries.rate |
| query_latency | content.proton.transport.query.latency.average |
| query_requests | content.proton.transport.query.count.rate |
| search_connections | search_connections.average |
| sentinel.uptime | sentinel.uptime.last |
| slobrok.heartbeats.failed | slobrok.heartbeats.failed.count |
| splitfailed | vds.idealstate.split_bucket.done_failed.rate |
| splitok | vds.idealstate.split_bucket.done_ok.rate |
| splitpending | vds.idealstate.split_bucket.pending.average |
| totalhits_per_query | totalhits_per_query.average |
| visit | vds.visitor.allthreads.created.sum.rate |
| visitorlifetime | vds.visitor.allthreads.averagevisitorlifetime.sum.average |
| visitorqueuewait | vds.visitor.allthreads.averagequeuewait.sum.average |

### Other changes

Vespa will not any longer implicitly load the "search" components" in containers which load the "document-api" components.
If your application depends on "search" functionality in a container specifying the `<document-api>` tag in services.xml,
make sure this container also specifies the `<search>` tag.
