---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root. 
title: "Approximate Nearest Neighbor Search using HNSW Index"
keywords: "ann, approximate nearest neighbor"
redirect_from:
- /documentation/approximate-nn-hnsw.html
---

For an introduction to nearest neighbor search, see [nearest neighbor search](nearest-neighbor-search.html) documentation, 
for practical usage of Vespa's nearest neighbor search, see [nearest neighbor search - a practical guide](nearest-neighbor-search-guide.html),
and to have Vespa create vectors for you, see [embedding](embedding.html).
This document describes how to speed up searches for nearest neighbors by adding a
[HNSW index](reference/schema-reference.html#index-hnsw) to the
tensor field.

Vespa implements a modified version of the Hierarchical Navigable Small World (HNSW) graph algorithm [paper](https://arxiv.org/abs/1603.09320).
The implementation in Vespa supports:

* **Filtering** - The search for nearest neighbors can be constrained by query filters
as the nearest neighbor search in Vespa is expressed as a query operator.
The [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator can be combined with other filters or query terms using the [Vespa query language](query-language.html).
See many query examples in the [practical guide](nearest-neighbor-search-guide.html#combining-approximate-nearest-neighbor-search-with-query-filters).

* **Multi-vector Indexing** - Since Vespa 8.144.19 multiple vectors per document can be indexed.
In this case documents are retrieved by the closest vector in each document compared to the query vector.
See the [Multi-vector indexing sample application](https://github.com/vespa-engine/sample-apps/tree/master/multi-vector-indexing)
for examples.
For use cases and implementation details see the following blog post:
[Revolutionizing semantic search with multi-vector HNSW indexing in Vespa](https://blog.vespa.ai/semantic-search-with-multi-vector-indexing/#implementation)

* **Real Time Indexing** - CRUD (Create, Add, Update, Remove) vectors in the index with low latency and high throughput.

* **Mutable HNSW Graph** - No query or indexing overhead from searching multiple <em>HNSW</em> graphs. In Vespa, there is one graph per tensor field per content node.
No segmented or partitioned graph where a query against a content node need to scan multiple HNSW graphs.

* **Multithreaded Indexing** - The costly part when performing real time changes to the *HNSW* graph
is distance calculations while searching the graph layers to find which links to change.
These distance calculations are performed by multiple indexing threads.

## Using Vespa's approximate nearest neighbor search
The query examples in [nearest neighbor search](nearest-neighbor-search.html) uses exact search, which has perfect accuracy.
However, this is computationally expensive for large document volumes
as distances are calculated for every document which matches the query filters.

To enable fast approximate matching, the tensor field definition
needs an `index` directive. A Vespa [document schema](schemas.html) can declare multiple tensor fields with `HNSW` enabled.

<pre>
field image_embeddings type tensor&lt;float&gt;(i{},x[512]) {
  indexing: summary | attribute | index
  attribute {
    distance-metric: angular
  }
  index {
    hnsw {
      max-links-per-node: 16
      neighbors-to-explore-at-insert: 100
    }
  }
}

field text_embedding type tensor&lt;float&gt;(x[384]) {
  indexing: summary | attribute | index
  attribute {
    distance-metric: prenormalized-angular
  }
  index {
    hnsw {
      max-links-per-node: 24
      neighbors-to-explore-at-insert: 200
    }
  }
}
</pre>

In the schema snippet above, fast approximate search is enabled by building an `HNSW` index for the
`image_embeddings` and the `text_embedding` tensor fields.
`image_embeddings` indexes multiple vectors per document,
while `text_embedding` indexes one vector per document.

The two vector fields use different [distance-metric](reference/schema-reference.html#distance-metric)
and `HNSW` index settings:

* `max-links-per-node` - a higher value increases recall accuracy, but also memory usage, indexing and search cost.
* `neighbors-to-explore-at-insert` - a higher value increases recall accuracy, but also indexing cost.

Choosing the value of these parameters affects both accuracy, search performance, memory usage and indexing performance.
See [Billion-scale vector search with Vespa - part two](https://blog.vespa.ai/billion-scale-knn-part-two/)
for a detailed description of these tradeoffs. See [HNSW index reference](reference/schema-reference.html#index-hnsw) 
for details on the index parameters. 

### Indexing throughput 
![Real-time indexing throughput](https://blog.vespa.ai/assets/2022-01-27-billion-scale-knn-part-two/throughput.png)

The `HNSW` settings impacts indexing throughput. Higher values of `max-links-per-node` and `neighbors-to-explore-at-insert`
reduces indexing throughput. Example from [Billion-scale vector search with Vespa - part two](https://blog.vespa.ai/billion-scale-knn-part-two/).

### Memory usage
Higher value of `max-links-per-node` impacts memory usage, higher values means higher memory usage:

![Memory footprint](https://blog.vespa.ai/assets/2022-01-27-billion-scale-knn-part-two/memory.png)

### Accuracy 

![Accuracy](https://blog.vespa.ai/assets/2022-01-27-billion-scale-knn-part-two/ann.png)

Higher `max-links-per-node` and `neighbors-to-explore-at-insert` improves the quality of the graph and
recall accuracy. The lower combination reaches about 70% recall@10, while the higher combination reaches
about 92% recall@10. The improvement in accuracy needs to be weighted against the impact on indexing performance and
memory usage. 

## Using approximate nearest neighbor search 

With an *HNSW* index enabled on the tensor field one can choose between approximate
or exact (brute-force) search by using the [approximate query annotation](reference/query-language-reference.html#approximate)

<pre>
{
  "yql": "select * from doc where {targetHits: 100, approximate:false}nearestNeighbor(image_embeddings,query_image_embedding)",
  "hits": 10
  "input.query(query_image_embedding)": [0.21,0.12,....],
  "ranking.profile": "image_similarity" 
}
</pre>
By default, `approximate` is true when searching a tensor field with `HNSW` index enabled.
The `approximate` parameter allows quantifying the accuracy loss of using approximate search. 
The loss can be calculated by performing an exact neighbor search using `approximate:false` and 
compare the retrieved documents with `approximate:true` and calculate the overlap@k metric.

Note that exact searches over a large vector volume require adjustment of the
[query timeout](reference/query-api-reference.html#timeout).
The default [query timeout](reference/query-api-reference.html#timeout) is 500ms,
which will be too low for an exact search over many vectors.

In addition to [targetHits](reference/query-language-reference.html#targethits), 
there is a [hnsw.exploreAdditionalHits](reference/query-language-reference.html#hnsw-exploreadditionalhits) parameter
which controls how many extra nodes in the graph (in addition to `targetHits`)
that are explored during the graph search. This parameter is used to tune accuracy quality versus query performance. 

## Combining approximate nearest neighbor search with filters 
The [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator can be combined with other
query filters using the [Vespa query language](reference/query-language-reference.html) and its query operators.
There are two high-level strategies for combining query filters with approximate nearest neighbor search:
* [pre-filtering](https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/#pre-filtering-strategy) (the default)
* [post-filtering](https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/#post-filtering-strategy)

These strategies can be configured in a rank profile using
[approximate-threshold](reference/schema-reference.html#approximate-threshold) and
[post-filter-threshold](reference/schema-reference.html#post-filter-threshold).
See
[Controlling the filtering behavior with approximate nearest neighbor search](https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/#controlling-the-filtering-behavior-with-approximate-nearest-neighbor-search)
for more details.

Note that when using `pre-filtering` the following query operators are not included when evaluating the filter part of the query:
* [geoLocation](reference/query-language-reference.html#geolocation)
* [predicate](reference/query-language-reference.html#predicate)

These are instead evaluated after the approximate nearest neighbors are retrieved, more like a `post-filter`.
This might cause the search to expose fewer hits to ranking than the wanted `targetHits`.

Since Vespa 8.78.45 the `pre-filter` can be evaluated using
[multiple threads per query](performance/practical-search-performance-guide.html#multithreaded-search-and-ranking).
This can be used to reduce query latency for larger vector datasets where the cost of evaluating the `pre-filter` is significant.
Note that searching the `HNSW` index is always single-threaded per query.
Multithreaded evaluation when using `post-filtering` has always been supported,
but this is less relevant as the `HNSW` index search first reduces the document candidate set based on `targetHits`.

## Nearest Neighbor Search Considerations

* **targetHits**:
The [targetHits](reference/query-language-reference.html#targethits)
specifies how many hits one wants to expose to [ranking](ranking.html) *per content node*.
Nearest neighbor search is typically used as an efficient retriever in a [phased ranking](phased-ranking.html)
pipeline. See [performance sizing](performance/sizing-search.html). 

* **Pagination**:
Pagination uses the standard [hits](reference/query-api-reference.html#hits) 
and [offset](reference/query-api-reference.html#offset) query api parameters. 
There is no caching of results in between pagination requests,
so a query for a higher `offset` will cause the search to be performed over again.
This aspect is no different from [sparse search](using-wand-with-vespa.html) not using nearest neighbor query operator.  

* **Total hit count is not accurate**:
Technically, all vectors in the searchable index are neighbors. There is no strict boundary between a match 
and no match. Both exact (`approximate:false`) and approximate (`approximate:true`) usages
of the [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator
does not produce an accurate `totalCount`.
This is the same behavior as with sparse dynamic pruning search algorithms like
[weakAnd](reference/query-language-reference.html#weakand) and [wand](reference/query-language-reference.html#wand). 
  
* **Grouping** counts are not accurate:
Grouping counts from [grouping](grouping.html) are not accurate when using [nearestNeighbor](reference/query-language-reference.html#nearestneighbor)
search. This is the same behavior as with other dynamic pruning search algorithms like
[weakAnd](reference/query-language-reference.html#weakand) and
[wand](reference/query-language-reference.html#wand). 
See the [Result diversification](https://blog.vespa.ai/result-diversification-with-vespa/) 
blog post on how grouping can be combined with nearest neighbor search. 


## Scaling Approximate Nearest Neighbor Search

### Memory 
Vespa tensor fields are [in-memory](attributes.html) data structures and so is the `HNSW` graph data structure.
For large vector datasets the primary memory resource usage relates to the raw vector field memory usage.

Using lower tensor cell type precision can reduce memory footprint significantly, for example using `bfloat16` 
instead of `float` saves close to 50% memory usage without significant accuracy loss. 

Vespa [tensor cell value types](performance/feature-tuning.html#cell-value-types) include:

* `int8` - 1 byte per value. Used to represent binary vectors, for example 64 bits can be represented using 8 `int8` values.
* `bfloat16` - 2 bytes per value. See [bfloat16 floating-point format](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format).
* `float` - 4 bytes per value. Standard float.
* `double` - 8 bytes per value. Standard double.


### Search latency and document volume

The `HNSW` greedy search algorithm is sublinear (close to log(N) where N is the number of vectors in the graph).
This has interesting properties when attempting to add more
nodes horizontally using [flat data distribution](performance/sizing-search.html#data-distribution).
Even if the document volume per node is reduced by a factor of 10, the search latency is only reduced by 50%. 
Still, flat scaling helps scale document volume, and increasing indexing throughput as vectors are partitioned
randomly over a set of nodes. 

Pure vector search applications (without filtering, or re-ranking) should attempt to scale up document volume by using 
larger instance type and maximize the number of vectors per node. To scale with query throughput,
use [grouped data distribution](performance/sizing-search.html#data-distribution) to replicate content. 

Note that strongly sublinear search is not necessarily true if the application
uses nearest neighbor search for candidate retrieval in a <a href="phased-ranking.html">multi-phase ranking</a> pipeline, 
or combines nearest neighbor search with filters. 



## HNSW Operations 
Changing the [distance-metric](reference/schema-reference.html#distance-metric)
for a tensor field with `hnsw` index requires [restarting](reference/schema-reference.html#changes-that-require-restart-but-not-re-feed),
but not re-indexing (re-feed vectors). Similar, changing the `max-links-per-node` and
`neighbors-to-explore-at-insert` construction parameters requires re-starting. 
