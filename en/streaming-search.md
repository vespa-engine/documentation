---
# Copyright Vespa.ai. All rights reserved.
title: "Streaming Search"
---

Search engines make queries fast by creating indexes over the stored data.
While the indexes cost extra resources to build and maintain, this is usually
a good tradeoff because they make queries so much cheaper. However, this
does not hold for use cases where the data is split into many small subsets
where each query just searches one (or a few) of these subsets, the canonical
example being *personal indexes* where a user only searches their own data.

For such use cases, Vespa provides *streaming search*
- a mode where only the raw data of the documents is
[stored](proton.html#document-store) and searches are implemented
by streaming - no indexes required. In addition, attributes
are also only stored on disk so that the only data needed in memory is
45 bytes per document, meaning that streaming mode lets you store billions of documents
on each node.

This is especially important in personal data applications using vector embeddings,
which otherwise require a lot of memory and require ANN to perform well,
which is often unsuited for searching personal data as they don't surface
all the most relevant documents.

Streaming mode is suitable when subsets are *on average* small compared
to the entire corpus. Vespa delivers low query latency also for the occasional large
subset (say, users with huge amounts of data) by automatically sharding such data groups
over multiple content nodes, searched in parallel.

Note: Using both streaming and indexed mode in the same cluster is discouraged.
The resource usage and performance characteristics for the two modes are
very different and it might be very hard to operate and get good performance for
such a system.

## Differences in streaming search

Streaming search uses the same implementation of most features in Vespa, including matching,
ranking, grouping and sorting, and mostly supports the same features.
A [schema](schemas.html) used in
[indexed mode](reference/services-content.html#document)
can in most cases be used in streaming search without any changes.
The following differences however apply:
* Streaming search does not use the [linguistics](linguistics.html) module while feeding documents.
  Instead, the string fields of each streamed document are
  [tokenized](linguistics.html#tokenization) and
  [normalized](linguistics.html#normalization) on the fly as part of performing a search.
  Query terms are [normalized](linguistics.html#normalization) in the same way.
  [Stemming](linguistics.html#stemming) is not supported for streaming search.
* Since there are no indexes, the content nodes do not collect term statistics and average field length statistics.
  + Term significance should be provided by a [global significance model](significance.html#global-significance-model),
    if [text matching features](reference/rank-features.html) that benefit from it are used.
    This includes among others *[bm25](reference/bm25.html)*,
    *nativeRank*, *nativeFieldMatch*, *nativeProximity* and *fieldMatch*.
  + If using *bm25*, adjust the
    [averageFieldLength](reference/rank-feature-configuration.html#properties)
    configuration for a more precise *bm25* score.
* Even without any indexes, fields must be specified as
  [index](reference/schema-reference.html#index) or
  [attribute](reference/schema-reference.html#attribute) to make them available for
  matching, ranking, grouping and sorting.
  The associated default [match](reference/schema-reference.html#match) setting for a field
  is equivalent to [indexed mode](reference/services-content.html#document).
* Streaming search supports a wider range of matching options (such as substring and prefix), and
  these can be specified either at query time or at configuration time.
  See [matching options](#matching-options-in-streaming-search) for details.
* [HNSW](reference/schema-reference.html#index-hnsw) indexes are not supported in streaming search.
  This means a [nearest neighbor search](nearest-neighbor-search.html#using-nearest-neighbor-search)
  is always *exact* when used in streaming search.
  The following parameters for adjusting *approximate* nearest neighbor search thus have no effect:
  + [post-filter-threshold](reference/schema-reference.html#post-filter-threshold)
  + [approximate-threshold](reference/schema-reference.html#approximate-threshold)
  + [filter-first-threshold](reference/schema-reference.html#filter-first-threshold)
  + [filter-first-exploration](reference/schema-reference.html#filter-first-exploration)
  + [exploration-slack](reference/schema-reference.html#exploration-slack)
  + [target-hits-max-adjustment-factor](reference/schema-reference.html#target-hits-max-adjustment-factor)
* [Parent/child relationships](parent-child.html) are not supported in streaming search.
  Using such functionality will fail [deployment](glossary.html#deployment).
* [Predicate fields](predicate-fields.html) are not supported in streaming search.
  They can exist as summary only fields in the document, but they are not searchable.
* [URI-fields](reference/schema-reference.html#uri) are not supported in streaming search.
  They are handled as regular string fields, and do not support the uri search functionality.
* [firstPhaseRank](reference/rank-features#firstPhaseRank) rank feature always returns the default value in streaming search.

## Using streaming search

These are the steps required to use streaming search:

1. Set indexing mode to [streaming](reference/services-content.html#document):

   ```
   <content id="mycluster" version="1.0">
       <documents>
           <document type="myType" mode="streaming" />
   ```
2. Use
   [document IDs](documents.html) which contains a *group* value specifying
   the small subset the document belongs to (usually a userid). These have the form
   `id:myNamespace:myType:g=myUserid:myLocalid`
   and when represented as paths in [document/v1](document-v1-api-guide.html) requests,
   `document/v1/myNamespace/myType/group/myUserId/myLocalId`
3. Specify the subset to search using the query parameter
   [streaming.groupname](reference/query-api-reference.html#streaming.groupname).

See the [vector streaming search sample application](https://github.com/vespa-engine/sample-apps/tree/master/vector-streaming-search)
for a complete example.

## Enabling indexing statements in streaming search

{% include important.html content='Since Vespa 8.287, this section can be disregarded -
it is not necessary to add `<document-processing/>` tags.
The configuration is identical to using indexed mode.' %}

Indexing statements are - as the name indicates - mostly used for indexing,
and so they are not executed by default with streaming search.

However, sometimes it is convenient to run indexing statements also when using streaming, for example to
use the `embed` function to turn text into an embedding vector, as in

```
indexing: input myTextField | embed | attribute
```

Indexing statements are run by a document processor, so to enable them with streaming,
enable document processing enabled on a container cluster and point to it as the one to do
indexing processing from the content cluster:

```
<services version="1.0">
    <container id="myContainers" version="1.0">
        ...
        <document-processing/>
        ...
    </container>

    <content id="mail" version="1.0">
        ...
        <documents>
            <document type="myType" mode="streaming" />
            <document-processing chain="indexing" cluster="myContainers" />
        </documents>
        ...
    </content>
</services>
```

## Matching options in streaming search

Streaming search offers more flexibility in matching text fields: Match settings
can be specified at query time on any text field, and fields marked with `indexing: index`
supports [suffix](reference/schema-reference.html#suffix) and
[substring](reference/schema-reference.html#substring) matching.

To specify match settings at query time in YQL:

```
select * from sources * where artist contains ({prefix:true}"col")
select * from sources * where artist contains ({substring:true}"old")
select * from sources * where artist contains ({suffix:true}"play")
```

To specify a default match setting for a field in the schema:

```
field artist type string {
    indexing: summary | index
    match: substring
}
```

## Streaming search grouping extension

[Grouping](grouping.html) works as normal with streaming search but offers two additional features,
explained here.

### Grouping over all documents

Since streaming search "looks at" all documents matching the group name/selection
regardless of the query, it is possible to group over all those documents and not just the ones
matching the query. This is done by using `where(true)` in the grouping expression:

```
all( where(true) all(group(myfield) each(output(count()))) )
```

When doing this, relevancy is not calculated for groups, as only matched hits have relevance.

### The docidnsspecific function

The `docidnsspecific` function returns the docid without namespace.

```
all( group(docidnsspecific()) each(output(count())) )
```

## Resource usage with streaming search
**Memory**: Streaming search requires 45 bytes of memory per document regardless of the document content.
**Disk**: Streaming search requires disk space to store the raw document data in compressed form.
The size is dependent on the actual data but can be extrapolated linearly with the number of documents.

## Query tuning in streaming search

Streaming search is a [visit](visiting.html) operation.
Parallelism is configured using [persistence-threads](reference/services-content.html#persistence-threads):

```
<persistence-threads count='8'/>
<visitors thread-count='8'/>
```

On [Vespa Cloud](https://cloud.vespa.ai/),
this number is set automatically to match the number of VCPUs set in
[resources](https://cloud.vespa.ai/en/reference/services#resources).
If you cannot get lower latency by increasing VCPUs, it means your streaming searches have become
IO bound.

### Tuning document store: Direct IO and cache

For better control of memory usage, use direct IO for reads when
[document store cache](reference/services-content.html#summary)
is enabled -
this makes the OS buffer cache size smaller and more predictable performance.
The document store cache will cache recent entries and increase performance for users or groups doing repeated accesses.
This sets aside 1 GB for document store cache.

```
<engine>
  <proton>
    <tuning>
      <searchnode>
        <summary>
          <io>
            <write>directio</write>
            <read>directio</read>
          </io>
          <store>
            <cache>
              <maxsize>1073741824</maxsize>
            </cache>
```
