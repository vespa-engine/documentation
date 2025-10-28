---
# Copyright Vespa.ai. All rights reserved.
title: "Glossary"
---

 /* temp style while developing */
li {
margin-top: 20px;
}
li > ul > li {
margin-top: 0;
}
.subpage p {
margin-block-end: 0;
}

This is a glossary of both Vespa-specific terminology, and general terms useful in this context.
---
* **Application**

  The unit of deployment and management.
  It can contain any number of clusters and schemas etc., but all deployed together.
  The files defining the application is called [Application Package](application-packages.html).
* **Attribute**

  An attribute is a field with properties other than an indexed field.
  Attribute fields have flexible match modes, including exact match, prefix match, and case-sensitive matching.
  Attributes enable high sustained update rates by writing directly to memory without disk access.
  Features like Grouping, Sorting, and [Parent/Child](#parent-child) use attributes.
* **Boolean Search**

  Use [Predicate fields](predicate-fields.html)
  to match queries to a set of boolean constraints in documents.
  The typical use case is to have a set of boolean constraints
  representing advertisements, specifying their target groups.
  Example: `hobby in [Music, Hiking] and age in [20..30]`.
* **Cluster**

  A set of homogenous nodes which all perform the same task.
  Vespa has two types: Container clusters are stateless, and content clusters store and process the data.
* **Component**

  Components extend a base class from the Container code module;
  some are [Chained](components/chained-components.html) for execution.
  The component types are:
  + [Processors](jdisc/processing.html#processors)
  + [Searchers](#searcher)
  + [Document Processors](#document-processor)
  + [Search Result Renderers](result-rendering.html)
  + [Provider Components](jdisc/injecting-components.html#special-components)
* **Configuration Server**

  The configuration server hosts most of the control plane of Vespa,
  where application packages are deployed to - often shortened to "config server".
  Config servers are deployed as one or in a cluster - see [overview](overview.html).
  The config server serves configuration for all Vespa processes,
  and is normally the first cluster started.
* **Container**

  Vespa's Java container, hosting all application components as well as the stateless logic of Vespa itself.
  Read more in [Container](jdisc/index.html).
  Not to be confused with [Docker Containers](#docker).
* **Content Node**

  Content nodes are stateful and holds the document and index data -
  see [content nodes](/en/content/content-nodes.html).
  These nodes implement Vespa's [elasticity](elasticity.html)
  for seamless data migration and scaling.
* **Control Plane**

  The deploy-commands are Vespa's control plane.
  The control plane is often secured with other credentials than the [data plane](#data-plane).
  Often low throughput and used by automation like GitHub Actions to deploy new versions
  of application packages.
* **Data Plane**

  Document and Query APIs make the Vespa Data plane.
  Also see [control plane](#control-plane).
  Often high throughout / low latency, as this is user-serving.
* **Deploy**

  `deploy` is a control-plane command to upload and activate a new version of an
  [application package](#application).
* **Deployment**

  A deployment is a running Vespa application,
  created by using [deploy](#deploy).
* **Diversity**

  Result diversity means having diverse results in the result set.
  As an example, not return the n highest ranking results, but eliminate similar hits, e.g. from the same domain.
  Refer to [diversity](/en/reference/schema-reference.html#diversity) and
  [grouping](/en/grouping.html) for features to eliminate similar hits or group them together.
* **Docker**

  Vespa is available as a container image from
  [hub.docker.com](https://hub.docker.com/r/vespaengine/vespa).
  Products to run this image include Docker, Podman and runC,
  and it enables users to run Vespa in a well-defined environment on multiple platforms.
  Read more in [Docker Containers](/en/operations-selfhosted/docker-containers.html).
* **Document**

  Vespa models data as documents.
  A document has a string identifier, set by the application, unique across all documents.
  A document is a set of key-value pairs.
  A document has a [Schema](#schema).
  Read more in [Documents](documents.html).
* **Document frequency (normalized)**

  The *document frequency* of a term captures how often the term occurs in the document corpus
  relative to the total number of documents.
  For ranking purposes this value is always normalized so that it is in the range [0, 1].
  For example, if a term occurs in 600 out of 1000 documents, its normalized document
  frequency will be \(600/1000 = 0.6\).

  From an information retrieval perspective, the normalized document frequency gives a measure
  of how common (or rare) a term is. Query terms that occur rarely (thus having a low document
  frequency) are usually expected to be more *relevant* to the query, since they are
  more specific. On the other end, very common terms (with high document frequency) are often
  considered to be "stopwords" (such as "the", "an" etc.), and are expected to have a low
  contribution to query relevance. This is directly related to
  [inverse document frequency](https://en.wikipedia.org/wiki/Tf%E2%80%93idf#Inverse_document_frequency),
  which is used by classic text ranking algorithms such as [tf-idf](https://en.wikipedia.org/wiki/Tf%E2%80%93idf)
  and [BM25](reference/bm25.html).
* **Document summary**

  A [document summary](document-summaries.html)
  is the information that is shown for each document in a query result.
  What information to include is determined by a document summary class:
  A named set of fields with config on which information they should contain.
  When Vespa stores a document, it is written to the [document store](proton.html#document-store)
  and used to generate summaries.
  The document store is scanned when using [streaming search](streaming-search.html).
* **Document Processor**

  Document processing is a framework to create chains of configurable [Components](#component)
  that read and modify document operations.
  A Document Processor uses `getFieldValue()` and `setFieldValue()` to process fields,
  alternatively using generated code from [Concrete Documents](concrete-documents.html).
* **Document Type**

  The data type part of a [Schema](#schema) - a collection of fields.
* **Elasticity**

  Vespa's clusters are elastic - a user can add or remove nodes on running applications without service disruption.
  For the stateful content nodes, this causes data sync between nodes for uniform distribution,
  with minimal data re-distribution. Read more in [Elasticity](elasticity.html).
* **Enclave**

  Vespa Cloud Enclave is a feature to run your Vespa application in Vespa Cloud in your own AWS or GCP account,
  see the [Enclave documentation](https://cloud.vespa.ai/en/enclave/).
* **Embedding**

  A common technique in modern big data serving applications is to map the subject data - say, text or images -
  to points in an abstract vector space and then do computation in that vector space.
  For example, retrieve similar data by finding nearby points in the vector space,
  or using the vectors as input to a neural net.
  This mapping is usually referred to as *embedding*,
  and Vespa provides [built-in support](embedding.html) for this.
* **Estimated hit ratio**

  When Vespa plans how a query should be evaluated in the most efficient way
  possible, one of the most important pieces of information is how many *hits*
  different parts of the query will produce. The estimated hit ratio is a normalized
  number in the range [0, 1] that states the proportion of documents that is expected
  to match a given part of the query.

  For example, a query with an `AND` operator over multiple terms will benefit
  by having the query planner place the term with the *lowest* estimated hit
  ratio *first* in the AND's evaluation order. This is because that term will be
  the cheapest to evaluate (least number of candidate documents to iterate over), and all
  other terms can be excluded as a possible match if it doesn't match.
* **Federation**

  The [Container](#container) allows multiple sources of data
  to be [federated](federation.html) to a common search service.
  The sources of data may be both search clusters, or external services,
  backed by Vespa or any other kind of service.
  The container may be used as a pure federation platform
  by setting up a system consisting solely of container nodes federating to external services.
* **Field**

  Documents have [Fields](schemas.html#field).
  A field has a type, and a field contained in a document can be written to, read from and queried.
  A field can also be generated (i.e. a synthetic field) -
  in this case, the field definition is outside the document - [example](/en/indexing.html#date-indexing).
  A field can be singlevalue, like a string, or multivalue, like an array of strings.
* **Fieldset**

  The term *fieldset* has two meanings in Vespa:
  + A collection of fields that are queried together - configured in the [schema](/en/schemas.html#fieldset):

    ```
    fieldset myset {
        fields: artist, title, album
    }
    ```
  + A collection of fields to return for a GET or VISIT operation, see the [guide](/en/documents.html#fieldsets):

    ```
    $ vespa visit --field-set restaurant:name,rating
    ```
* **Garbage Collection**

  Use a [Document Selection](reference/services-content.html#document.selection)
  to [auto-expire](documents.html#document-expiry) documents by time or any other criterion.
* **Grouping**

  Vespa Grouping is a list processing language which describes how the query hits should be grouped,
  aggregated and presented in result sets.
  A grouping statement takes the list of all matches to a query as input and groups/aggregates it,
  possibly in multiple nested and parallel ways to produce the output.
  [Read more](grouping.html).
* **Handler**

  Also called *Request Handler*.
  A handler is a [Component](#component) used to build API endpoints on the [Container](#container).
  Find documentation at [developing request handlers](/en/jdisc/developing-request-handlers.html),
  and [example use](https://github.com/vespa-engine/sample-apps/tree/master/model-inference/src/main/java/ai/vespa/example).
* **Indexing**

  The process of creating index structures.
  This includes routing document writes to indexing processors,
  processing (indexing) documents and writing the documents to content clusters.
  Settings like [streaming search](#streaming-search) do not create indices to optimize resource usage.
* **Instance**
  *Instance* is always "default" in Vespa.ai
  (i.e. there is only one) -
  managed services like [Vespa Cloud](https://cloud.vespa.ai/) support multiple,
  [read more](https://cloud.vespa.ai/en/tenant-apps-instances).
  An instance is a deployment of an application for a given purpose, like production serving -
  multiple instances of an application can be used to support more use cases like integration testing.
* **Namespace**

  A segment of [Document IDs](#document)
  which helps you generate unique ids also if you have multiple sources of unique values.
  Namespace can be used to [Visit](#visit) a subspace of the corpus.
* **Nearest neighbor search**

  [Nearest neighbor search](nearest-neighbor-search.html),
  or [vector search](vector-search.html),
  is a technique used to find the closest data points to a given query point in a high-dimensional vector space -
  see [distance metric](nearest-neighbor-search.html#distance-metrics-for-nearest-neighbor-search).
  It can be exact or approximate.
  This is supported in Vespa using the
  [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator.
* **Node**

  A Node is a host / container instance running one or more [Services](#service).
  The mapping from logical to actual name is configured in [hosts.xml](reference/hosts.html).
* **Parent / Child**

  Using document references, documents can have [parent/child](parent-child.html) relationships.
  Use this to join data by importing fields from parent documents.
  Parent documents are replicated to all nodes in the cluster.
* **Partial Update**

  A partial update is an update to one or more fields in a document.
  It also includes updating all index structures,
  so the effect of the partial update is immediately observable in queries.
  Partial updates do not require the full document,
  and enables a high write throughput with memory-only operations.
  [Read more](partial-updates.html).
* **Posting List**

  A posting list is a fundamental data structure in information retrieval and search engines.
  It is used in inverted indexes to store the occurrences of a term in a collection of documents.
  [Read more](/en/performance/feature-tuning.html#posting-lists).
* **Quantization**

  Quantization is the process of constraining an input
  from a continuous or otherwise large set of values (such as the real numbers)
  to a discrete set (such as the integers).
  It is a way to reduce memory and CPU usage for [tensor operations](#tensor)
  in [nearest neighbor search](#nearest-neighbor-search),
  to improve throughput or latencies.
* **Query**

  Use the [Query API](query-api.html) to query the corpus.
  Queries are written in [YQL](reference/query-language-reference.html),
  or can be created programmatically in a [Searcher](#searcher).
  Configure query execution in a [Query Profile](query-profiles.html).
* **Ranking**

  Ranking is where Vespa does computing, or inference over documents.
  The computations to be done are expressed in functions called
  [Ranking Expressions](ranking-expressions-features.html#ranking-expressions),
  bundled into [Rank Profiles](ranking.html#rank-profiles) defined in a [Schema](#schema).
  These can range from simple math expressions combining some rank features,
  to tensor expressions or large machine-learned models.
  Ranking can be single- or [multiphased](phased-ranking.html).
* **Schema**

  A description of a particular type of data and how to process/rank it.
  See the [Schema guide](schemas.html).
* **Searcher**

  A searcher is a [Component](#component) - usually deployed as part of an OSGi bundle.
  All Searchers must implement a single method `search(query)`.
  Developers implement application query logic in Searchers -
  [read more](/en/searcher-development.html).
* **Semantic search**

  Semantic search denotes search with meaning,
  as distinguished from lexical search where the search engine looks for literal matches of the query words.
  Read [Revolutionizing Semantic Search with Multi-Vector HNSW Indexing](https://blog.vespa.ai/semantic-search-with-multi-vector-indexing/)
  for more details on semantic search, pointers to resources, and how to implement it.
* **Service**

  A Service runs in a [Cluster](#cluster) of container or content nodes,
  configured in [services.xml](reference/services.html).
* **Streaming search**

  [Streaming search](streaming-search.html) is querying fields that do not have an index structure.
  The indexing cost is minimal as no index is generated.
  A query is hence a scan over all data, and normally slower than using index structures.
  Streaming search is used for applications like personal search, where the searched data volume is small.
  It can be a powerful option to drastically limit memory use in nearest-neighbor applications
  where the possible neighbor set it orders of magnitude smaller than the total.
* **Tenant**

  An organizational unit that owns [applications](#application).
  In Vespa.ai APIs, *tenant* and *application* are always "default",
  and a Vespa system has exactly one tenant
  and one application.
  In managed services like [Vespa Cloud](https://cloud.vespa.ai/),
  multiple tenants and applications is supported -
  [read more](https://cloud.vespa.ai/en/tenant-apps-instances).
* **Tensor**

  A [Tensor](tensor-user-guide.html) is a data structure which generalizes scalars, vectors and matrices
  to any number of dimensions:
  A scalar is a tensor of rank 0, a vector is a tensor of rank 1, a matrix is a tensor of rank 2.
  Tensors consist of a set of scalar valued cells, with each cell having a unique address.
  A cell's address is specified by its index or label in all the dimensions of that tensor.
  The number of dimensions in a tensor is the rank of the tensor,
  each dimension can be either mapped or indexed.
* **Visit**

  [Visit](visiting.html) is a feature to efficiently get or process a set of / all documents,
  identified by a [Document Selection Expression](reference/document-select-language.html).
  Visit iterates over all, or a set of, buckets and sends documents to a (set of) targets.
