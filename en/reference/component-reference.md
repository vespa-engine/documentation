---
# Copyright Vespa.ai. All rights reserved.
title: "Component Reference"
category: oss,cloud
redirect_from:
- /en/jdisc/component-versioning.html
---

A component is any Java class whose lifetime is controlled by the container,
see the [Developer Guide](../developer-guide.html) for an introduction.
Components are specified and configured in services.xml and can have other components, and config
(represented by generated "Config" classes) [injected](../jdisc/injecting-components.html)
at construction time, and in turn be injected into other components.

Whenever a component or a resource your component depends on is changed by a redeployment,
your component is reconstructed. Once all changed components are reconstructed, new requests
are atomically switched to use the new set and the old ones are destructed.

If you have multiple constructors in your component, annotate the one to use for injection by
`@com.yahoo.component.annotation.Inject`.

Identifiable components must implement `com.yahoo.component.Component`, and components that need to
destruct resources at removal must subclass `com.yahoo.component.AbstractComponent`
and implement `deconstruct()`.

See the [example](../operations/metrics.html#example-qa)
for common questions about component uniqueness / lifetime.

## Component Types

Vespa defined various component types (superclasses) for common tasks:

| Component type | Description |
| --- | --- |
| Request handler | [Request handlers](../jdisc/developing-request-handlers.html) allow applications to implement arbitrary HTTP APIs. A request handler accepts a request and returns a response. Custom request handlers are subclasses of [ThreadedHttpRequestHandler](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/container/jdisc/ThreadedHttpRequestHandler.html). |
| Processor | The [processing framework](../jdisc/processing.html) can be used to create general composable synchronous request-response systems. Searchers and search chains are an instantiation (through subclasses) of this general framework for a specific domain. Processors are invoked synchronously and the response is a tree of arbitrary data elements. Custom output formats can be defined by adding [renderers](#renderers). |
| Renderer | Renderers convert a Response (or query Result) into a serialized form sent over the network. Renderers are subclasses of [com.yahoo.processing.rendering.Renderer](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/processing/rendering/Renderer.java). |
| Searcher | Searchers processes Queries and their Results. Since they are synchronous, they can issue multiple queries serially or in parallel to e.g. implement federation or decorate queries with information fetched from a content cluster. Searchers are composed into *search chains* defined in services.xml. A query request selects a particular search chain which implements the logic of that query. [Read more](../searcher-development.html). |
| Document processor | Document processors processes incoming document operations. Similar to Searchers and Processors they can be composed in chains, but document processors are asynchronous. [Read more](../document-processing.html). |
| Binding | A binding matches a request URI to the correct [filter chain](#filter) or [request handler](#request-handlers), and route outgoing requests to the correct [client](#client). For instance, the binding *http://*/** would match any HTTP request, while *http://*/processing* would only match that specific path. If several bindings match, the most specific one is chosen.   |  |  | | --- | --- | | Server binding | A server binding is a rule for matching incoming requests to the correct request handler, basically the JDisc building block for implementing RESTful APIs. | | Client binding | A client binding is a pattern which is used to match requests originating inside the container, e.g. when doing federation, to a client provider. That is, it is a rule which determines what code should handle a given outgoing request. | |
| Filter | A filter is a lightweight request checker. It may set some specific request property, or it may do security checking and simply block requests missing some mandatory property or header. |
| Client | Clients, or client providers, are implementations of clients for different protocols, or special rules for given protocols. When a JDisc application acts as a client, e.g. fetches a web page from another host, it is a client provider that handles the transaction. Bindings are used, as with request handlers and filters, to choose the correct client, matching protocol, server, etc., and then hands off the request to the client provider. There is no problem in using arbitrary other types of clients for external services in processors and request handlers. |

## Component configurations

This illustrates a typical component configuration set up by the Vespa container:
![Vespa container component configuration](/assets/img/container-components.svg)

The network layer associates a Request with a *response handler*
and routes it to the correct type of [request handler](#request-handlers)
(typically based on URI binding patterns).

If an application needs lightweight request-response processing
using decomposition by a series of chained logical units,
the [processing framework](../jdisc/processing.html)
is the correct family of components to use.
The request will be routed from ProcessingHandler through one or more chains of
[Processor](#processors) instances.
The exact format of the output is customizable using a [Renderer](#renderers).

If doing queries, SearchHandler will create a Query object,
route that to the pertinent chain of [Searcher](#searchers) instances,
and associate the returned Result with the correct [Renderer](#renderers) instance
for optional customization of the output format.

The DocumentProcessingHandler is usually invoked from messagebus,
and used for feeding documents into an index or storage.
The incoming data is used to build a Document object,
and this is then feed through a chain of [DocumentProcessor](#document-processors) instances.

If building an application with custom HTTP APIs, for instance arbitrary REST APIs,
the easiest way is building a custom [RequestHandler](#request-handlers).
This gets the Request, which is basically a set of key-value pairs,
and returns a stream of arbitrary data back to the network.

## Injectable Components

These components are available from Vespa for [injection](../jdisc/injecting-components.html)
into applications in various contexts:

| Component | Description |
| --- | --- |
| Always available | |
| --- | --- |
| [AthenzIdentityProvider](https://github.com/vespa-engine/vespa/blob/master/container-disc/src/main/java/com/yahoo/container/jdisc/athenz/AthenzIdentityProvider.java) | Provides the application's Athenz-identity and gives access to identity/role certificate and tokens. |
| [BertBaseEmbedder](https://github.com/vespa-engine/vespa/blob/master/model-integration/src/main/java/ai/vespa/embedding/BertBaseEmbedder.java) | A BERT-Base compatible embedder, see [BertBase embedder](../embedding.html#bert-embedder). |
| [ConfigInstance](https://github.com/vespa-engine/vespa/blob/master/config-lib/src/main/java/com/yahoo/config/ConfigInstance.java) | Configuration is injected into components as `ConfigInstance` components - see [configuring components](../configuring-components.html). |
| [Executor](https://docs.oracle.com/javase/7/docs/api/java/util/concurrent/Executor.html) | Default threadpool for processing requests in threaded request handler |
| [Linguistics](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/Linguistics.java) | Inject a Linguistics component like [SimpleLinguistics](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/simple/SimpleLinguistics.java) or provide a custom implementation - see [linguistics](../linguistics.html). |
| [Metric](https://github.com/vespa-engine/vespa/blob/master/jdisc_core/src/main/java/com/yahoo/jdisc/Metric.java) | Jdisc core interface for metrics. Required by all subclasses of ThreadedRequestHandler. |
| [MetricReceiver](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/metrics/simple/MetricReceiver.java) | Use to emit metrics from a component. Find an example in the [metrics](../operations/metrics.html#metrics-from-custom-components) guide. |
| [ModelsEvaluator](https://github.com/vespa-engine/vespa/blob/master/model-evaluation/src/main/java/ai/vespa/models/evaluation/ModelsEvaluator.java) | Evaluates machine-learned models added to Vespa applications and available as config form. |
| [SentencePieceEmbedder](https://github.com/vespa-engine/vespa/blob/master/linguistics-components/src/main/java/com/yahoo/language/sentencepiece/SentencePieceEmbedder.java) | A native Java implementation of SentencePiece, see [SentencePiece embedder](embedding-reference.html#sentencepiece-embedder). |
| [VespaCurator](https://github.com/vespa-engine/vespa/blob/master/zkfacade/src/main/java/com/yahoo/vespa/curator/api/VespaCurator.java) | A client for ZooKeeper. For use in container clusters that have ZooKeeper enabled. See [using ZooKeeper](../using-zookeeper.html). |
| [VipStatus](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/container/handler/VipStatus.java) | Use this to gain control over the service status (up/down) to be emitted from this container. |
| [WordPieceEmbedder](https://github.com/vespa-engine/vespa/blob/master/linguistics-components/src/main/java/com/yahoo/language/wordpiece/WordPieceEmbedder.java) | An implementation of the WordPiece embedder, usually used with BERT models. Refer to [WordPiece embedder](embedding-reference.html#wordpiece-embedder). |
| [SystemInfo](https://github.com/vespa-engine/vespa/blob/master/hosted-zone-api/src/main/java/ai/vespa/cloud/SystemInfo.java) | Vespa Cloud: Provides information about the environment the component is running in. [Read more](/en/jdisc/container-components.html#the-systeminfo-injectable-component). |
| Available in containers having `search` | |
| [DocumentAccess](https://github.com/vespa-engine/vespa/blob/master/documentapi/src/main/java/com/yahoo/documentapi/DocumentAccess.java) | To use the [Document API](../document-api-guide.html). |
| [ExecutionFactory](https://github.com/vespa-engine/vespa/blob/master/container-search/src/main/java/com/yahoo/search/searchchain/ExecutionFactory.java) | To execute new queries from code. [Read more](../developing-web-services.html#queries). |
| [Map<String, Model>](https://github.com/vespa-engine/vespa/blob/master/model-evaluation/src/main/java/ai/vespa/models/evaluation/Model.java) | Use to inject a set of Models, see [Stateless Model Evaluation](../stateless-model-evaluation.html). |
| Available in containers having `document-api` or `document-processing` | |
| [DocumentAccess](https://github.com/vespa-engine/vespa/blob/master/documentapi/src/main/java/com/yahoo/documentapi/DocumentAccess.java) | To use the [Document API](../document-api-guide.html). |

## Component Versioning

Components as well as many other artifacts in the container can be versioned.
This document explains the format and semantics of these versions and how they are referred.

### Format

Versions are on the form:

```
version ::=    major [ "." minor [ "." micro [ "." qualifier ]]]
```

Where `major`, `minor`, and `micro` are integers
and `qualifier` is any string.

A version is appended to an id separated by a colon.
In cases where a file is created for each component version,
the colon is replaced by a dash in the file name.

### Ordering

Versions are ordered first by major, then minor, then micro and then
by doing a lexical ordering on the qualifier.
This means that `a:1 < a:1.0 < a:1.0.0 < a:1.1 < a:1.1.0 < a:2`

### Referencing a versioned Component

Whenever component is referenced by id (in code or configuration),
a fully or partially specified version may be included in the reference
by using the form `id:versionSpecification`.
Such references are resolved using the following rules:
* An id without any version specification resolves to the highest
  version not having a qualifier.
* A partially or full version specification resolves to the highest
  version not having a qualifier which matches the specification.
* Versions with qualifiers are matched only by exact match.

Example: Given a component with id `a` having these versions: `[1.1, 1.2, 1.2, 1.3.test, 2.0]`
* The reference `a` will resolve to `a:2.0`
* The reference `a:1` will resolve to `a:1.2`
* The only way to resolve to the "test" qualified version
  is by using the exact reference `a:1.3.test`
* These references will not resolve: `a:1.3`, `a:3`, `1.2.3`

### Merging specifications for chained Components

In some cases, there is a need for merging multiple references into one.
An example is inheritance of chains of version references,
where multiple inherited chains may reference the same component.

Two version references are said to be *compatible* if one is a prefix of the other.
In this case the most specific version is used.
If they are not compatible they are *conflicting*. Example:

```
<search>
    <searcher id="Searcher:2.3" class="com.yahoo.search.example.Searcher" bundle="the name in <artifactId> in your pom.xml" />
    <searcher id="Searcher:2.4" class="com.yahoo.search.example.Searcher" bundle="the name in <artifactId> in your pom.xml" />
    <chain id="parenta">
        <searcher id="Searcher:2"> bundle="the name in <artifactId> in your pom.xml" </searcher>
    </chain>
    <chain id="parentb">
        <searcher id="Searcher:2.3"> bundle="the name in <artifactId> in your pom.xml" </searcher>
    </chain>
    <chain id="parentc">
        <searcher id="Searcher:2.4"> bundle="the name in <artifactId> in your pom.xml" </searcher>
    </chain>

    <!-- This chain will get Searcher:2.3 -->
    <chain id="childa" inherits="parenta parentb" />

    <!-- Error, as Searcher:2.3 and Searcher:2.4 are conflicting -->
    <chain id="childb" inherits="parentb parentc" />
</search>
```
