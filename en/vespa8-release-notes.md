---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa 8 Release Notes"
---

This document lists the changes between Vespa major versions 7 and 8.
As documented in [Vespa versions](https://vespa.ai/releases#versions),
new functionality in Vespa is introduced in minor versions,
while major versions are used to mark releases breaking compatibility.
As Vespa 8 does not introduce any new functionality,
it is as safe and mature as the versions of Vespa 7 preceding it.
No further releases will be made of Vespa 7, except
possible critical security fixes.

## Overview

The compatibility breaking changes in Vespa 8 fall into these categories:
* [Changes to default behaviour](#changed-defaults)
* [Application package structure and settings](#application-package-changes) -
  deprecated settings and constructs in e.g. *schemas* and *services.xml* are removed.
* [Java APIs](#java-api-changes) -
  deprecated APIs are removed or revoked from Vespa's
  [public API](https://javadoc.io/doc/com.yahoo.vespa/annotations/latest/com/yahoo/api/annotations/PublicApi.html) surface.
* [Container runtime environment](#container-runtime) -
  incompatible changes to the Java build and runtime environments.
* [HTTP API changes](#removed-http-api-parameters)
* [Removed command line tools](#removed-command-line-tools)
* [Removed or renamed metrics](#removed-or-renamed-metrics)
* [Changes to the document selection language](#document-selection-exact-type-matching)
* [Security related changes](#security)
* [Operating system support](#operating-system)
* [Other changes](#other-changes), not covered by any of the above categories.

To ensure their applications are compatible with Vespa 8, application owners must:
* Review the list of [changes to defaults](#changed-defaults) and add the necessary options
  if you want to preserve behavior from Vespa 7.
* Make sure there are no deprecation warnings when compiling against Vespa 7.
* Review the [application package changes](#application-package-changes) and make sure there
  are no deployment warnings when deploying on Vespa 7.
* Review the list of [HTTP API changes](#removed-http-api-parameters) and update
  any clients of the application.
* Review the remaining sections of this document, and update the application and its environment accordingly.

Usage of deprecated Java APIs produce warnings during compilation, while *deployment warnings*
are produced for application package deprecations and most changes to the container runtime environment.
In hosted Vespa or Vespa Cloud, deployment warnings are shown in the application's console view.
However, for other types of changes, there is no way to emit deprecation warnings,
so these are only described in this document and other Vespa documentation.

The following sections lists all the changes from Vespa 7 to Vespa 8 in detail.

## Changed defaults

These changes may break clients, and impact both performance and user experience.
Applications that are in production and relies on these defaults should
make configuration changes to keep the existing behavior when upgrading to Vespa 8.
This can be done on Vespa 7, *before* upgrading -
using [bucket tests](testing.html#feature-switches-and-bucket-tests) can be useful.

The following defaults have changed:

| Change | Configuration required to avoid change on Vespa 8 |
| --- | --- |
| The default [simple query language](reference/simple-query-language-reference.html) (for end users) is changed from `all` to [weakAnd](using-wand-with-vespa.html#weakand). {% include note.html content="This might increase recall, and increase latency significantly if document corpus is large." %} | Explicitly pass [model.type](reference/query-api-reference.html#model.type)=all in queries or set this parameter in the relevant [query profiles](query-profiles.html): `<field name="model.type">all</field>`. |
| The default grammar in [YQL userInput](reference/query-language-reference.html#userinput) is changed from `all` to [weakAnd](using-wand-with-vespa.html#weakand). {% include note.html content="This might increase recall, and increase latency significantly if document corpus is large." %} | Prefix `userInput` in YQL by `{grammar: "all"}`. |
| The value of the services.xml [legacy flag v7-geo-positions](reference/default-result-format.html#geo-position-rendering) changes from true to false. | Add to services.xml: `<legacy> <v7-geo-positions>true</v7-geo-positions> </legacy>` |
| Fields of type `map` [changes JSON rendering](reference/default-result-format.html#inconsistent-map-rendering) in search results. | Add overrides in your query profile(s) for the `renderer.json.jsonMaps` parameter. |
| Fields of type `weightedset` [changes JSON rendering](reference/default-result-format.html#inconsistent-weightedset-rendering) in search results. | Add overrides in your query profile(s) for the `renderer.json.jsonWsets` parameter. |
| Expressions used as summary features, are no longer rendered wrapped in `rankingExpression()`. | Specify configuration in your rank profile as shown in [this example](reference/default-result-format.html#summary-features-wrapped-in-rankingexpression). |
| Fields of type `raw` are now presented as a base64 encoded string in summary, the same way as in json feed format. Earlier, you needed to add `raw-as-base64-in-summary` in your schema file to get this behavior. | If you have fields of type "raw" and you must have the old summary behavior for them in search results, add the line  `raw-as-base64-in-summary : false`  in your schema definition. |
| The default tensor format in responses has changed from 'long' to 'short': Tensors in query results, document API responses, and stateless model evaluation are rendered in the short form appropriate for their type (if any), documented [here](reference/document-json-format.html#tensor). | **Queries**: Pass [presentation.format.tensors](reference/query-api-reference.html#presentation.format.tensors)=long in queries, or set it parameter in the relevant [query profiles](query-profiles.html).  **Document/v1**: Pass the parameter `format.tensors=long` in requests.  **Stateless model evaluation**: Pass the parameter `format.tensors=long` in requests. |
| The default fieldset when getting or visiting documents is now `[document]` in all cases, meaning you only get those fields that are declared in the "document" block of the schema (generated fields are not included). This was already the default for the `/document/v1` API when fetching or visiting documents of a single known document type. Now it is also the default when visiting at the root level, for the command line tools `vespa-visit` and `vespa-get`, and if you use the programmatic `documentapi` from java to fetch documents. | In most cases there is no difference between `[all]` and `[document]` fieldsets - so no action is needed. If the old behavior is needed you can:  * For the command line tools, specify the fieldset as   `-l "[all]"` to include generated fields. * For `/document/v1` specify `[all]`   as the value for the `fieldSet` parameter. * If using `documentapi` from java, add the line    `params.setFieldSet("[all]");`    to modify your `VisitorParameters` value , or    `params = params.withFieldSet("[all]");`    to modify your `DocumentOperationParameters` value.  If you run document processors to generate fields and want those returned, it may be more useful to declare a fieldset with just those fields you actually want as output instead. |
| Vespa will now limit the number of groups and hits in [grouping query results](grouping.html) when `max` is not specified explicitly in grouping expressions. The default value is determined by [grouping.defaultMaxGroups](reference/query-api-reference.html#grouping.defaultmaxgroups)/ [grouping.defaultMaxHits](reference/query-api-reference.html#grouping.defaultmaxhits). The parameter [grouping.globalMaxGroups](reference/query-api-reference.html#grouping.globalmaxgroups) must now be overridden in query profiles to allow grouping expressions that may return unbounded or large results. | * [grouping.defaultMaxGroups](reference/query-api-reference.html#grouping.defaultmaxgroups)   changed from `-1` to `10`. * [grouping.defaultMaxHits](reference/query-api-reference.html#grouping.defaultmaxhits)   changed from `-1` to `10`. * [grouping.globalMaxGroups](reference/query-api-reference.html#grouping.globalmaxgroups)   changed from `-1` to `10000`. * [grouping.defaultPrecisionFactor](reference/query-api-reference.html#grouping.defaultprecisionfactor)   changed from `1.0` to `2.0`. |
| Vespa [access logs](access-logging.html) are compressed with [zstd](https://github.com/facebook/zstd). | Add a config override under `<container>` in `services.xml`:    ```       <config name="container.core.access-log">         <fileHandler>           <compressionFormat>GZIP<compressionFormat> ``` |

## Application package changes

### Removed settings from schemas

The following settings are removed from
[schema](reference/schema-reference.html):

| Name | Replacement |
| --- | --- |
| attribute: huge | None. Setting *huge* on an attribute doesn't have any effect, the code is rewritten to support it by default. |
| [compression](reference/schema-reference.html#compression) | None. Document compression is not needed, as compression is always enabled. |
| body (inside a field definition) | None. Deprecated since before Vespa 7, had no effect in Vespa 7. |
| header (inside a field definition) | None. Deprecated since before Vespa 7, had no effect in Vespa 7. |
| field type weightedset<float> | Because floating-point types are inherently imprecise they are badly suited as keys in maps and sets. If you feel the need for such data consider using something like:  ```              struct weightedfloat {                  field value type float {}                  field weight type int {}              }              field myfield type array<weightedfloat> {                  ... ``` |
| field type map<float,anything> | Using "float" as the key in a map is no longer supported, see `weightedset<float>` above. |
| field type weightedset<double> | Using "double" as the key in a set is no longer supported, see `weightedset<float>` above. |
| field type map<double,anything> | Using "double" as the key in a map is no longer supported, see `weightedset<float>` above. |
| field type weightedset<uri> | Using complex types as the key in a set is no longer supported, see `weightedset<float>` above. |
| field type map<uri,anything> | Using complex types as the key in a map is no longer supported, see `weightedset<float>` above. |
| Old syntax for array types like "string[]" | Write as `array<string>` instead. |
| Rank functions must have different names in a rank-profile | Only the last of two functions with the same name would be used. Remove or rename the first one. |
| Conflicting sorting settings are now rejected | Only keep the last of the conflicting settings. |
| A summary-field may only be added once in a document-summary block | Remove duplicates. |
| Schema and document should have the same name | Change name of the schema, so it is equal to the contained document. |

### TensorFlow import

Vespa 8 removes support for direct import of [TensorFlow models](tensorflow.html).
[ONNX](https://onnx.ai/) is now the preferred ML model format, and works both for
[ranking](onnx.html) as well as
[stateless model evaluation](stateless-model-evaluation.html).
ONNX contains tools to convert models from TensorFlow to ONNX, but Vespa will no longer provide this.

### Changed semantics in services.xml

The following elements and attributes in services.xml have new semantics:

| Name | Description |
| --- | --- |
| <nodes><redundancy> | It is now an error to configure a number of nodes (per group) that is smaller than the configured redundancy. It used to generate an application-level warning, with the redundancy implicitly reduced. Remove any <nodes> override in the non-prod environments, as the node count is automatically adjusted. |

### Removed constructs from services.xml

The following elements and attributes are removed from services.xml:

| Parent element | Removed construct | Description |
| --- | --- | --- |
| <admin> | <filedistribution> | Configuring up/download rates is not supported |
| <configserver> | Use [configservers](reference/services-admin.html#configservers) element instead |
| <config> | *namespace* attribute | The namespace must be included in the *name* attribute. |
| <myArray *operation="append">* syntax | Previously used to append items to config arrays. Use [item](reference/config-files.html#configuring-arrays) instead. |
| <container> | *jetty* attribute | Removed, had no effect on Vespa 7. |
| <nodes> jvm attributes | JVM attributes *jvmargs, allocated-memory, jvm-options, jvm-gc-options* renamed and moved to [JVM](reference/services-container.html#jvm) subelement |
| <client> | Previously used for setting up client providers. Use a [request handler](jdisc/developing-request-handlers.html) instead. |
| <handler><clientBinding> | Client bindings are no longer supported. |
| <content> | <dispatch> | Removed due to removal of *vespa-dispatch-bin*, [details.](#vespa-dispatch-bin-process-is-removed) |
| <tuning><dispatch><min-group-coverage> | Use [min-active-docs-coverage](reference/services-content.html#min-active-docs-coverage) instead. |
| <tuning><dispatch><use-local-node> | Ignored, the local node will automatically be preferred when appropriate. |
| <engine><proton><tuning><searchnode><flushstrategy><native><transactionlog><maxentries> | Use [maxsize](reference/services-content.html#flushstrategy-native-transactionlog-maxsize) instead. Vespa 7 documentation: The maximum number of entries in the [transaction log](proton.html#transaction-log) for a document type before running flush, default 1000000 (1 M). |
| <engine><proton><tuning><searchnode><summary><store><logstore><chunk><maxentries> | Use [maxsize](reference/services-content.html#summary-store-logstore-chunk-maxsize) instead. Vespa 7 documentation: Maximum number of documents in a chunk. See *summary.log.chunk.maxentries*. |
| <services> (root) | <jdisc> | Use [container](reference/services-container.html) instead. |
| <service> | Running generic services is no longer supported. |
| <clients> | Client load types are deprecated and ignored. |

### *application/* folder support removed

Application package content (*services.xml*, the *schemas/*
folder, etc.) is supposed to be put at the root level in the application
zip, such that the unzipped application package has *./services.xml*,
etc.

But it used to be that the application package content could be placed inside
an *application* directory. This support is removed on Vespa 8.

### *searchdefinitions/* folder is deprecated

Search definition schemas should now be placed in the *schemas/* folder. The old folder
will still work on Vespa 8, but causes a deprecation warning upon deployment.

## Java API changes

### Removed Java packages

| Package | Description |
| --- | --- |
| *com.yahoo.docproc.util* | Removed |
| *com.yahoo.jdisc.test* | No longer [public API](https://javadoc.io/doc/com.yahoo.vespa/annotations/latest/com/yahoo/api/annotations/PublicApi.html) |
| *com.yahoo.log.event* | No longer [public API](https://javadoc.io/doc/com.yahoo.vespa/annotations/latest/com/yahoo/api/annotations/PublicApi.html) |
| *com.yahoo.statistics* | Removed |
| *com.yahoo.vespa.curator* | No longer [public API](https://javadoc.io/doc/com.yahoo.vespa/annotations/latest/com/yahoo/api/annotations/PublicApi.html) |
| *com.yahoo.documentapi.messagebus.loadtypes* | Load types are no longer supported. Use corresponding method overloads without *LoadType* or *LoadTypeSet* parameters instead. |

### Removed Java Classes and methods

Classes and methods that were marked as deprecated in Vespa 7 are removed.
If deprecation warnings are emitted for Vespa APIs when building the application,
these must be fixed before migrating to Vespa 8. The sections below contain only the
most notable changes.

The following classes are no longer public API and have been moved to Vespa internal packages:

| Package | Class | Migration advice |
| --- | --- | --- |
| *com.yahoo.config.subscription* | All classes, except [*ConfigGetter*](https://javadoc.io/doc/com.yahoo.vespa/config/latest/com/yahoo/config/subscription/ConfigGetter.html) | Config should be [injected](configuring-components.html#use-config-in-code) to your component class constructor. |
| *com.yahoo.docproc* | *DocprocExecutor* | For unit tests, follow the steps in the [document-processing](https://github.com/vespa-engine/sample-apps/blob/master/examples/document-processing/src/test/java/ai/vespa/example/album/ProductTypeRefinerDocProcTest.java) sample app. If you need a *DocumentTypeManager* in production code, it can be directly [injected](jdisc/injecting-components.html) to your component class constructor. |
| *DocprocService* |
| *DocumentOperationWrapper* | No replacement - if needed, contact the Vespa team for advice. |
| *HandledProcessingException* |
| *ProcessingEndpoint* |
| *TransientFailureException* |
| *com.yahoo.log* | *VespaFormatter* | No replacement. |

The following methods are removed:

| Method | Migration advice |
| --- | --- |
| *com.yahoo.documentapi.DocumentAccess.createDefault()* | Container components can have a *DocumentAccess* injected via their constructor. For use outside the container, e.g. in a custom command line tool, use the new method *createForNonContainer()*. |
| *com.yahoo.log.LogSetup.getLogHandler()* | No replacement. |

### Breaking changes to Java APIs

The Javadoc of the deprecated types/members should document the replacement API.
The below list is not exhaustive - some smaller and trivial changes are not listed.

| Type(s) | Description |
| --- | --- |
| *com.yahoo.processing* | Removed use of Guava's *ListenableFuture* in type signatures. Replacement uses *CompletableFuture*. |
| *com.yahoo.search.handler.HttpSearchResponse.waitableRender()* | Removed use of Guava's *ListenableFuture* in type signature. The method is replaced with *asyncRender()*. |
| *com.yahoo.jdisc.handler* | Removed use of Guava's *ListenableFuture* in type signatures. Replacement uses *CompletableFuture* |
| *com.yahoo.searchlib.rankingexpression.rule* | Removed use of Guava collection types in type signatures. |
| *com.yahoo.search.rendering.JsonRenderer* | Removed use of Jackson types from class signature. |
| *com.yahoo.jdisc.Container* | Removed use of Guice types from class signature. |
| *com.yahoo.vdslib.VisitorStatistics* | Removed all *set/getSecondPass*-related methods. |
| *com.yahoo.documentapi* | Removed all methods taking in a *com.yahoo.documentapi.messagebus.DocumentProtocol.Priority* argument. Explicit operation priorities are deprecated and should not be set by the client. |

### Removed support for built-in XML factories

The Jdisc container has historically supported injection of built-in providers for the following XML factories:
* *javax.xml.datatype.DatatypeFactory*
* *javax.xml.parsers.DocumentBuilderFactory* and *SAXParserFactory*
* *javax.xml.stream.XMLEventFactory*, *XMLInputFactory* and *XMLOutputFactory*
* *javax.xml.transform.TransformerFactory*
* *javax.xml.validation.SchemaFactory*
* *javax.xml.xpath.XPathFactory*

These are now removed. Please check for more recent alternatives if you need this type of XML processing.

### Deprecated Java APIs

A few redundant APIs have been deprecated because they have replacements that
provide the same, or better, functionality. We advise you switch to the
replacement to reduce future maintenance cost.

| Type(s) | Replacement |
| --- | --- |
| *com.yahoo.container.jdisc.LoggingRequestHandler* | Use *com.yahoo.container.jdisc.ThreadedHttpRequestHandler* instead. |
| *com.yahoo.log.LogLevel* | Use *java.util.logging.Level* instead. |

## Container Runtime Environment

### JDK version

Vespa 8 upgrades the JDK version from 11 to 17. To ensure full compatibility, all container components
should be rebuilt with JDK 17 before being deployed on Vespa 8.

### Changes to provided maven artifacts

[Guava](https://search.maven.org/artifact/com.google.guava/guava) has been upgraded from
version 20.0 to 27.1. If you are using APIs that have been removed from the library since version 20, your
code must be updated. In most cases, it should be trivial to find replacement APIs in Java's standard library.

The following Maven artifacts are no longer provided runtime to user application plugins by the Jdisc container:

| Artifact | Notes |
| --- | --- |
| [*com.fasterxml.jackson.jaxrs:jackson-jaxrs-base*](https://search.maven.org/artifact/com.fasterxml.jackson.jaxrs/jackson-jaxrs-base) | JSON input/output handling for JAX-RS implementations, e.g. Jersey |
| [*com.fasterxml.jackson.jaxrs:jackson-jaxrs-json-provider*](https://search.maven.org/artifact/com.fasterxml.jackson.jaxrs/jackson-jaxrs-json-provider) |
| [*com.fasterxml.jackson.module:jackson-module-jaxb-annotations*](https://search.maven.org/artifact/com.fasterxml.jackson.module/jackson-module-jaxb-annotations) | Jackson data binding with JAXB annotations. |
| [*com.google.code.findbugs:jsr305*](https://search.maven.org/artifact/com.google.code.findbugs/jsr305) | Annotations in package *javax.annotation[.*]*, e.g. *Nullable* and *Nonnnull*. |
| [*com.google.inject.extensions:guice-assistedinject*](https://search.maven.org/artifact/com.google.inject.extensions/guice-assistedinject) | Guice extensions.  For component injection see [Depending on another component](jdisc/injecting-components.html#depending-on-another-component) |
| [*com.google.inject.extensions:guice-multibindings*](https://search.maven.org/artifact/com.google.inject.extensions/guice-multibindings) | Guice extensions. |
| [*javax.annotation:javax.annotation-api*](https://search.maven.org/artifact/javax.annotation/javax.annotation-api) | Annotations in package *javax.annotation[.*]*, e.g. *ManagedBean* and *Resource*. |
| [*javax.validation:validation-api*](https://search.maven.org/artifact/javax.validation/validation-api) | Javax bean validation, used by Jersey 2. |
| [*org.eclipse.jetty:**](https://search.maven.org/search?q=g:org.eclipse.jetty) | The Eclipse Jetty Project. |
| [*org.apache.felix:org.apache.felix.framework*](https://search.maven.org/artifact/org.apache.felix/org.apache.felix.framework) | Felix OSGi framework. |
| *org.apache.felix:org.apache.felix.log* | Felix OSGi framework. |
| [*org.apache.felix:org.apache.felix.main*](https://search.maven.org/artifact/org.apache.felix/org.apache.felix.main) | Felix OSGi framework. |
| [*org.bouncycastle:bcpkix-jdk15on*](https://search.maven.org/artifact/org.bouncycastle/bcpkix-jdk15on) | Bouncy Castle crypto API. |
| [*org.bouncycastle:bcprov-jdk15on*](https://search.maven.org/artifact/org.bouncycastle/bcprov-jdk15on) | Bouncy Castle crypto provider. |
| *org.glassfish.*:** | Jersey 2. All related artifacts are removed. |
| [*org.json:json*](https://search.maven.org/artifact/org.json/json) | See [vespa-engine/vespa#14762](https://github.com/vespa-engine/vespa/issues/14762) |
| [*org.javassist:javassist*](https://search.maven.org/artifact/org.javassist/javassist) | Bytecode manipulation, used by Jersey 2. |
| [*org.jvnet.mimepull:mimepull*](https://search.maven.org/artifact/org.jvnet.mimepull/mimepull) | MIME Streaming Extension, used by Jersey 2. |
| [*org.lz4:lz4-java*](https://search.maven.org/artifact/org.lz4/lz4-java) | Compression library. |

Make sure your application OSGi bundle embeds the required artifacts from the above list.
An artifact can be embedded by adding it in scope *compile* to the *dependencies* section in pom.xml.
Typically, these artifacts have until now been used in scope *provided*.
Use `mvn dependency:tree` to check whether any of the listed artifacts are directly or transitively included
as dependencies.

As always, remove any dependencies that are not required by your project. Consult the Maven documentation on
[Dependency Exclusions](https://maven.apache.org/guides/introduction/introduction-to-optional-and-excludes-dependencies.html#dependency-exclusions) for how to remove a transitively included dependency.

An example adding *org.json:json* as a compile scoped dependency:

```
<dependencies>
  ...
  <dependency>
    <groupId>org.json</groupId>
    <artifactId>json</artifactId>
    <version>20211205</version>
    <scope>compile</scope>
  </dependency>
  ...
</dependencies>
```

## Removed HTTP API parameters

The following HTTP API parameters are removed from the [query API](reference/query-api-reference.html):

| Standard API path | Parameter name | Replacement |
| --- | --- | --- |
| /search/ | *pos.ll* | add a [geoLocation](reference/query-language-reference.html#geolocation) item to the query |
| /search/ | *pos.radius* | add a [geoLocation](reference/query-language-reference.html#geolocation) item to the query |
| /search/ | *pos.attribute* | add a [geoLocation](reference/query-language-reference.html#geolocation) item to the query |
| /search/ | *pos.bb* | Support for restricting search by a bounding box, using the `pos.bb` query parameter, has been removed - add a [geoLocation](reference/query-language-reference.html#geolocation) item to the query |

## Removed command line tools

### vespa-http-client

The `vespa-http-client` command line tool is removed on Vespa 8 and is replaced by the new
[vespa-feed-client](vespa-feed-client.html). The new client uses
[HTTP/2](performance/http2.html) and the [Document v1 API](document-v1-api-guide.html).

The underlying rest API used by the vespa-http-client will still be available and supported on Vespa 8.
You can therefore continue to use an old client distributed with Vespa 7 to feed to a Vespa 8 installation.
Note that there will not be released any updates for vespa-http-client after the initial Vespa 8 release,
while fixes and security updates to the rest API implementation will continue as part of Vespa 8.
We strongly recommend that you migrate away from vespa-http-client in a timely manner.

## Removed or renamed metrics

The following metrics are renamed:

| Old Name | New name | Description |
| --- | --- | --- |
| *vds.filestor.alldisks.** | vds.filestor.* | *alldisks* has been removed from the metric name. |
| *vds.visitor.*.sum.** | vds.visitor.*.* | *sum* has been removed from the metric name. |
| *vds.filestor.*.sum.** | vds.filestor.*.* | *sum* has been removed from the metric name. |
| *vds.distributor.*.sum.** | vds.distributor.*.* | *sum* has been removed from the metric name. |

The following metrics are removed:

| Name | Description |
| --- | --- |
| *http.status.401.rate* | Use *http.status.4xx.rate* with dimension *statusCode*==401 |
| *http.status.403.rate* | Use *http.status.4xx.rate* with dimension *statusCode*==403 |
| *content.proton.documentdb.matching.query_collateral_time.** | Use *content.proton.documentdb.matching.query_setup_time.** instead |
| *content.proton.documentdb.matching.rank_profile.query_collateral_time.** | Use *content.proton.documentdb.matching.rank_profile.query_setup_time.** instead |
| *vds.visitor.allthreads.averagevisitorlifetime~~.sum~~.average* | Use .sum/.count instead |
| *vds.visitor.allthreads.averagequeuewait~~.sum~~.average* | Use .sum/.count instead |
| *vds.visitor.allthreads.queuesize~~.sum~~.average* | Use .sum/.count instead |
| *vds.visitor.allthreads.completed~~.sum~~.average* | Use .sum/.count instead |
| *vds.visitor.allthreads.averagemessagesendtime~~.sum~~.average* | Use .sum/.count instead |
| *vds.visitor.allthreads.averageprocessingtime~~.sum~~.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.queuesize.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.averagequeuewait.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.allthreads.put~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.allthreads.remove~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.allthreads.get~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.allthreads.update~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.allthreads.createiterator~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.allthreads.visit~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.allthreads.remove_location~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.filestor~~.alldisks~~.allthreads.deletebuckets~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.distributor.puts~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.distributor.removes~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.distributor.updates~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.distributor.gets~~.sum~~.latency.average* | Use .sum/.count instead |
| *vds.distributor.visitor~~.sum~~.latency.average* | Use .sum/.count instead |

## Exact matching of document types in selection language

The [document selection language](reference/document-select-language.html) now
uses *exact* matching for document types rather than *inheritance* ("is-a")
matching.

Example with two minimal document schemas:
* `document my_doc_type {}`
* `document my_extended_doc_type inherits my_doc_type {}`

Previously, the selection expression `my_doc_type` would match both a document instance of
type `my_doc_type` *and* `my_extended_doc_type`. It will now
*only* match a document of type `my_doc_type`.

## Security

### Strict mode enabled by default
*Strict mode* for request filtering in the jdisc container is enabled by default in Vespa 8.
See documentation on the [strict-mode](reference/services-http.html#filtering)
attribute in services.xml for details.

### Request headers controlling remote host/port in access log

The jdisc container will use the *X-Forwarded-For* and *X-Forwarded-Port* request headers to set the remote
host and port respectively in the access log. The following request headers will no longer be handled by default:
* y-ra
* yahooremoteip
* client-ip
* y-rp

## Operating system support for Vespa artifacts

### RPMs

The supported OS for Vespa RPMs changes from [CentOS Linux 7](https://www.centos.org/centos-linux/) to
[CentOS Stream 8](https://www.centos.org/centos-stream/) for Vespa 8. RPMs will still be built
and distributed on [Fedora Copr](https://copr.fedorainfracloud.org/coprs/g/vespa/vespa/). If you install Vespa
RPMs you will have to upgrade your OS to [CentOS Stream 8](https://www.centos.org/centos-stream/).

### OCI containers (Docker containers)

The base image used in our OCI containers changes from [docker.io/centos:7](https://hub.docker.com/_/centos)
to [quay.io/centos/centos:stream8](https://quay.io/repository/centos/centos?tab=tags) for Vespa 8. This means that
the container image is built and tested on systems running kernel version *4.18.0* (current kernel for CentOS Stream 8).
If you use Vespa's container image, you should upgrade the hosts running the containers to the same or a newer kernel version.

## Other changes

### Unknown rank profiles

Queries that specify a rank profile which does not exist in all the schemas being queried
will now fail instead of falling back to using the `default` profile.
Queries to multiple schemas must use a rank profile that exists in all of them,
which can be ensured by [inheriting](schemas.html#schema-inheritance) a common schema.

### Unknown summary classes

Queries that specify a non-existent [summary class](document-summaries.html)
will now fail, instead of being rendered empty.
Queries to multiple schemas must use a summary class that exists in all of them,
which can be ensured by [inheriting](schemas.html#schema-inheritance) a common schema.

### The "qrserver" service name

Vespa containers are in general using "container" as their service name. However, a container cluster that has
declared neither [document-processing](reference/services-docproc.html) nor
[document-api](reference/services-container.html#document-api) used to be named "qrserver".
On Vespa 8 all container clusters uses the service name "container". This affects the output of all
metrics APIs, as well as the Vespa log output.

### Container access logs

The folder for container access logs has been moved from `$VESPA_HOME/logs/vespa/qrs/` to
`$VESPA_HOME/logs/vespa/access/`.

The default compression format has changed from gzip to zstd, see [changed defaults](#changed-defaults).

### ONNX output in summary features

When defining an ONNX model output in summary features, Vespa 8 ensures that the summary feature name is `onnx`
rather than `onnxModel` as in previous version.

### Changes in rankfeatures

Vespa can calculate and return all [rank-features](reference/query-api-reference.html#ranking.listfeatures)
in the `rankfeatures` summary field. Vespa 8 contains some changes to this list:
* `now` is removed
* `bm25(field)` is added
* `matches(field)` is added

### The "storage" message bus routing policy is removed

The "storage" routing policy was removed in early Vespa 7, and clients specifying it have been forwarded to
the content routing policy for backwards compatibility. The forwarding is removed on Vespa 8 and clients needs
be updated.

Replace all usages of the "storage" policy with "content", which behaves identically.

### vespa-dispatch-bin process is removed

The dispatch functionality is moved into the Vespa Container
and the *vespa-dispatch-bin* process is removed.
As this is not a public interface,
the default was switched to **not** using vespa-dispatch-bin in Vespa-7.109.10.
The process was removed in subsequent Vespa releases:

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| [Dispatch](query-api.html) | Content cluster | dynamically allocated in 19100 - 19899 range | $VESPA_HOME/sbin/vespa-dispatch-bin | Dispatcher, communicates between container and content nodes. Can be multi-level in a hierarchy |

Rolling upgrade note: A rolling upgrade over Vespa-7.109.10 should work with no extra steps.

### YQL format
* When Vespa outputs an YQL statement, it will now not end the string by a semicolon.
  Terminating statements with semicolon continue to be optional and legal input.
* [Annotations](reference/query-language-reference.html#annotations)
  are not enclosed in `[]` brackets (still valid input).
* The annotation name is not quoted (still valid input).

Example Vespa 7 / Vespa 8:

```
where text contains ([{"distance": 5}]near("a", "b"));
where text contains ({distance: 5}near("a", "b"))
```

### Upgrade procedure

The [upgrade procedure](/en/operations-selfhosted/live-upgrade.html) has been simplified in Vespa 8
(when upgrading from Vespa 7 to Vespa 8 or between Vespa 8 versions).
When upgrading from Vespa 7.x to Vespa 7.y replace item 3
[Upgrade config servers](/en/operations-selfhosted/live-upgrade.html#upgrade-config-server)
in the [upgrade procedure](/en/operations-selfhosted/live-upgrade.html) with this procedure:
* When upgrading the config servers, the nodes of the application cannot receive config
  until they are upgraded themselves. We need to set all of them
  in standalone mode before continuing by running this command on each node:

  ```
      $ vespa-configproxy-cmd -m setmode memorycache
  ```

  Each node will automatically reattach itself when it is upgraded.
* Install the new Vespa version on the config servers and
  [restart](/en/operations-selfhosted/admin-procedures.html#vespa-start-stop-restart) them one by one.
  Wait until it is up again, look in vespa log for
  "Changing health status code from 'initializing' to 'up'"
  or use [health checks](/en/operations-selfhosted/configuration-server.html#troubleshooting).
* Redeploy and activate the application:

  ```
  $ vespa deploy
  ```
