---
# Copyright Vespa.ai. All rights reserved.
title: "Reads and writes"
---

This guide covers the aspects of accessing [documents](documents.html) in Vespa.
Documents are stored in *content* clusters.
Writes (PUT, UPDATE, DELETE) and reads (GET) pass through a *container* cluster.
Find a more detailed flow at the end of this article.

![Vespa Overview](/assets/img/vespa-overview.svg)

Highlights:
* Vespa's indexing structures are built for high-rate field updates.
  Refer to the [feed sizing guide](performance/sizing-feeding.html) for write performance,
  in particular [partial updates](partial-updates.html) for partial updates.
* Vespa supports [parent/child](parent-child.html) for de-normalized data.
  This can be used to simplify the code to update application data,
  as one write will update all children documents.
* Applications can add custom feed [document processors](document-processing.html)
  and multiple container clusters - see [indexing](indexing.html) for details.
* Writes in Vespa are *consistent* in a stable cluster, but Vespa will prioritize availability over consistency when
  there is a conflict.
  See the [elasticity](elasticity.html#consistency) documentation
  and the [Vespa consistency model](content/consistency.html).
  It is recommended to use the same client instance for updating a given document when possible -
  for data consistency, but also
  [performance](performance/sizing-feeding.html#concurrent-mutations) (see *concurrent mutations*).
  Read more on write operation [ordering](content/content-nodes.html#ordering).
  For performance, group field updates to the same document into
  [one update operation](performance/sizing-feeding.html#client-roundtrips).
* Applications can [auto-expire documents](documents.html#document-expiry).
  This feature also blocks PUTs to documents that are already expired -
  see [indexing](/en/operations-selfhosted/routing.html#document-selection) and
  [document selection](reference/services-content.html#documents).
  This is a common problem when feeding test data with timestamps,
  and the writes a silently dropped.

Also see [troubleshooting](/en/operations-selfhosted/admin-procedures.html#troubleshooting).

## Operations

| Operation | Description |
| --- | --- |
| Get | Get a document by ID. |
| Put | Write a document by ID - a document is overwritten if a document with the same document ID exists.  Puts can have [conditions](document-v1-api-guide.html#conditional-writes) for test-and-set use cases. Conditions can be combined with [create if nonexistent](document-v1-api-guide.html#create-if-nonexistent), which causes the condition to be ignored if the document does not already exist. |
| Remove | Remove a document by ID. If the document to be removed is not found, it is not considered a failure. Read more about [data-retention](/en/operations-selfhosted/admin-procedures.html#data-retention-vs-size). Also see [batch deletes](operations/batch-delete.html).  Removes can have [conditions](document-v1-api-guide.html#conditional-writes) for test-and-set use cases.  A removed document is written as a tombstone, and later garbage collected - see [removed-db / prune / age](reference/services-content.html#removed-db-prune-age). Vespa does not retain, nor return, the document data of removed documents. |
| Update | Also referred to as [partial updates](partial-updates.html), as it updates one or more fields of a document by ID - the [document v1 API](document-v1-api-guide.html#put) can be used to perform [updates in the JSON Document format](reference/document-json-format.html#update). If the document to update is not found, it is not considered a failure.  Updates support [create if nonexistent](document-v1-api-guide.html#create-if-nonexistent) (upsert).  Updates can have [conditions](document-v1-api-guide.html#conditional-writes) for test-and-set use cases.  All data structures ([attribute](attributes.html), [index](proton.html#index) and [summary](document-summaries.html)) are updatable. Note that only *assign* and *remove* are idempotent - message re-sending can apply updates more than once. Use *conditional writes* for stronger consistency.   |  |  | | --- | --- | | **All field types** | * [assign](reference/document-json-format.html#assign) (may also be used to clear fields) | | **Numeric field types** | * [increment](reference/document-json-format.html#arithmetic).   Also see [auto-generate weightedset keys](reference/schema-reference.html#weightedset) * [decrement](reference/document-json-format.html#arithmetic) * [multiply](reference/document-json-format.html#arithmetic) * [divide](reference/document-json-format.html#arithmetic) | | **Composite types** | * [add](reference/document-json-format.html#add)   For *array* and *weighted set*.   To put into a *map*,   see the [assign](reference/document-json-format.html#assign) section * [remove](reference/document-json-format.html#composite-remove) * [match](reference/document-json-format.html#match)   Pick element from collection, then apply given operation to matched element * [accessing elements within a composite field using fieldpaths](reference/document-json-format.html#fieldpath) | | **Tensor types** | * [modify](reference/document-json-format.html#tensor-modify)   Modify individual cells in a tensor - can replace, add or multiply cell values * [add](reference/document-json-format.html#tensor-add)   Add cells to mapped or mixed tensors * [remove](reference/document-json-format.html#tensor-remove)   Remove cells from mapped or mixed tensors | |

## API and utilities

Also see the [JSON Document format](reference/document-json-format.html):

| API / util | Description |
| --- | --- |
| [Vespa CLI](vespa-cli.html) | Command-line tool to `get`, `put`, `remove`, `update`, `feed`, `visit`. |
| [/document/v1/](reference/document-v1-api-reference.html) | API for `get`, `put`, `remove`, `update`, `visit`. |
| [Java Document API](document-api-guide.html) | Provides direct read-and write access to Vespa documents using Vespa's internal communication layer. Use this when accessing documents from Java components in Vespa such as [searchers](searcher-development.html) and [document processors](document-processing.html). See the [Document](https://github.com/vespa-engine/vespa/blob/master/document/src/main/java/com/yahoo/document/Document.java) class. |
| [pyvespa](https://vespa-engine.github.io/pyvespa/reads-writes.html) | Python client library for reading and writing documents to Vespa. Provides convenient methods for feeding, querying, and visiting documents. Expect less performance than Vespa CLI and vespa-feed-client for heavy batch feed operations. |

Advanced / debugging tools:
* [vespa-feed-client](vespa-feed-client.html):
  Java library and command line client for feeding document operations
  using [/document/v1/](reference/document-v1-api-reference.html).
* [vespa-feeder](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-feeder)
  is a utility for feeding over the [Message Bus](/en/operations-selfhosted/routing.html).
* [vespa-get](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-get) gets single documents
  over the [Message Bus](/en/operations-selfhosted/routing.html).
* [vespa-visit](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-visit) gets multiple documents
  over the [Message Bus](/en/operations-selfhosted/routing.html).

## Feed flow

Use the [Vespa CLI](vespa-cli.html), [vespa-feed-client](vespa-feed-client.html), [pyvespa python client](https://vespa-engine.github.io/pyvespa/reads-writes.html)
or [/document/v1/ API](reference/document-v1-api-reference.html) to read and write documents:

![Feed with feed client](/assets/img/elastic-feed-container.svg)

Alternatively, use [vespa-feeder](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-feeder) to feed files
or the [Java Document API](document-api-guide.html).

![Feed with vespafeeder](/assets/img/elastic-feed-vespafeeder.svg)

[Indexing](/en/operations-selfhosted/routing.html#routing-for-indexing)
and/or [document processing](document-processing.html)
is a chain of processors that manipulate documents before they are stored.
Document processors can be user defined.
When using indexed search, the final step in the chain prepares documents for indexing.

The [Document API](document-api-guide.html) forwards requests to distributors on content nodes.
For more information, read about [content nodes](content/content-nodes.html)
and the [search core](proton.html).

## Further reading
* [Visiting](visiting.html)
* [/document/v1/ API guide](document-v1-api-guide.html)
* [/document/v1/ API reference](reference/document-v1-api-reference.html)
