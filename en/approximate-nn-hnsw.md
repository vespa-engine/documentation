---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root. 
title: "Approximate Nearest Neighbor Search using HNSW Index"
redirect_from:
- /documentation/approximate-nn-hnsw.html
---

For an introduction to nearest neighbor search, see [nearest neighbor search](nearest-neighbor-search.html) documentation, 
for practical usage of Vespa's nearest neighbor search, see [nearest neighbor search - a practical guide](nearest-neighbor-search-guide.html).
This document describes how to speed up searches for nearest neighbors by adding a
[HNSW index](reference/schema-reference.html#index-hnsw) to the first-order dense tensor field.

Vespa implements a modified version of the Hierarchical Navigable Small World (HNSW) graph algorithm [paper](https://arxiv.org/abs/1603.09320) 
The implementation in Vespa supports:

* **Filtering** - The search for nearest neighbors can be constrained by query filters
as the nearest neighbor search in Vespa is expressed as a query operator.
The nearest neighbor query operator can be combined with other filters or query terms using the [Vespa query language](query-language.html).
See many examples in the [practical guide](nearest-neighbor-search-guide.html#combining-approximate-nearest-neighbor-search-with-query-filters).

* **Real Time Indexing** - Add, remove or update vectors in the index with low latency and high throughput.

* **Mutable HNSW Graph**  No query overhead from searching multiple <em>HNSW</em> graphs. In Vespa, there is one graph per field. No
segmented or partitioned graph. 

* **Multi-threaded Indexing** - The costly part when doing changes to the *HNSW* graph is distance calculations while searching the graph layers
to find which links to change. These distance calculations are performed by multiple indexing threads. 

## Using Vespa's approximate nearest neighbor search
The query examples in [nearest neighbor search](nearest-neighbor-search.html) uses exact search, which has
perfect accuracy but which is computationally expensive for large document volumes
as the distance needs to be calculated for every document which matches
the query filters. 

To enable fast approximate matching, the first-order dense tensor field definition 
needs an `index` directive. The same document type can have multiple tensor fields with *HNSW* enabled.

<pre>
field image_sift_encoding type tensor&lt;float&gt;(x[128]) {
  indexing: summary | attribute | index
  attribute {
    distance-metric: euclidean 
  }
  index {
    hnsw {
      max-links-per-node: 16
      neighbors-to-explore-at-insert: 500
    }
  }
}

field bert_embedding type tensor&lt;float&gt;(x[384]) {
  indexing: summary | attribute | index
  attribute {
    distance-metric: angular
  }
  index {
    hnsw {
      max-links-per-node: 24
      neighbors-to-explore-at-insert: 500
    }
  }
}
</pre>

In the schema snippet above, fast approximate search is enabled by building an *HNSW* index for the
*image_sift_encoding* and the *bert_embedding* tensor fields.

The two fields uses different [distance-metric](reference/schema-reference.html#distance-metric)
and `max-links-per-node` settings. 

* `max-links-per-node` impacts memory usage of the graph, accuracy and search speed. 
* `neighbors-to-explore-at-insert` impacts graph accuracy and search speed. 

Choosing the value of these parameters affects both accuracy, search speed, memory usage and indexing performance.
See [Billion-scale vector search with Vespa - part two](https://blog.vespa.ai/billion-scale-knn-part-two/)
for an detailed description of these tradeoffs. 
See [HNSW index reference](reference/schema-reference.html#index-hnsw) for details on the index parameters.

## Using fast approximate nearest neighbor search in query

With an *HNSW* index enabled on the tensor field one can choose between approximate
or exact (brute-force) search by using the [approximate query annotation](reference/query-language-reference.html#approximate)

<pre>
{
  "yql": "select * from doc where ({targetHits: 100, approximate:false}nearestNeighbor(image_sift_encoding,query_vector_sift)) and in_stock = true",
  "hits": 10
  "ranking.features.query(query_vector_sift)": [0.21,0.12,....],
  "ranking.profile": "image_similarity" 
}
</pre>

By default, `approximate` is true when searching a field with <em>HNSW</em> index enabled.
The `approximate` parameter allows quantifying the accuracy loss of using approximate search. 

The loss can be calculated by performing an exact neighbor search using `approximate:false` and 
compare the retrieved documents with `approximate:true` and calculate the overlap@k metric. 

In addition to [targetHits](reference/query-language-reference.html#targethits), 
there is a [hnsw.exploreAdditionalHits](reference/query-language-reference.html#hnsw-exploreadditionalhits) parameter
which controls how many extra nodes in the graph (in addition to `targetHits`)
that are explored during the graph search. This parameter is used to tune accuracy quality versus performance. 


## Nearest Neighbor Search Considerations

* **targetHits**
The `targetHits` specifies how many hits one wants to expose to [ranking](ranking.html) *per node*.
Nearest neighbor search is typically used as an efficient retriever in a [phased ranking](phased-ranking.html)
pipeline. See [performance sizing](performance/sizing-search.html). 

* **Pagination**
Pagination is done with the standard [hits](reference/query-api-reference.html#hits) 
and [offset](reference/query-api-reference.html#offset) query api parameters. 
There is no caching of results in between pagination requests, so a query for a higher `offset` will cause the search to be performed over again. 
This is no different from regular sparse search not using nearest neighbor query operator.  

* **Total hit count is not accurate**
Technically, all vectors in the searchable index are neighbors. There is no strict boundary between a match 
and no match. Both exact (`approximate:false`) and approximate (`approximate:true`) usages
of the [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator
does not produce an accurate `totalCount`. This is the same behavior as with other dynamic pruning search algorithms like 
[weakAnd](reference/query-language-reference.html#weakand) and
[wand](reference/query-language-reference.html#wand). 
  
* **Grouping** counts are not accurate

Grouping counts from [grouping](grouping.html) are not accurate when using [nearestNeighbor](reference/query-language-reference.html#nearestneighbor)
search. This is the same behavior as with other dynamic pruning search algorithms like 
[weakAnd](reference/query-language-reference.html#weakand) and
[wand](reference/query-language-reference.html#wand). See [Result diversification](https://blog.vespa.ai/result-diversification-with-vespa/)
blog post on how grouping can be used over hits retrieved by nearest neighbor search. 


## Scaling Approximate Nearest Neighbor Search

### Memory 
Vespa tensor fields are [in-memory](attributes.html) data structures and so is the `HNSW` graph.
For large vector datasets the primary memory resource usage relates to the the raw vector field memory usage.

Using lower tensor cell type precision can reduce memory footprint significantly, for example using `bfloat16` 
instead of `float` saves 50% memory usage without much accuracy loss. 

Vespa [tensor cell value types](tensor-user-guide.html#cell-value-types) include: 

* `int8` 1 byte per value. Used to represent binary vectors, for example 64 bits can be represented using an 8 `int8` values.
* `bfloat16` 2 bytes per value. See [bfloat16 floating-point format](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format).
* `float` 4 bytes per value. Standard float. 
* `double` 8 bytes per value. Standard double

### Search Latency and document volume

The `HNSW` greedy search algorithm is sub-linear (close to log(N)). This has interesting properties when attempting to add more
nodes horizontally using [flat data distribution](performance/sizing-search.html#data-distribution)
as even if the document volume per node is reduced by a factor of 10, the latency is only reduced by 50%.

Pure vector search applications (without filtering, or re-ranking) should attempt to scale up document volume by using a 
larger instance type and try to maximize the number of vectors per node. 

To scale with query throughput, use [grouped data distribution](performance/sizing-search.html#data-distribution).

Note that this is not necessarily true if the application
uses nearest neighbor search for candidate retrieval in a <a href="phased-ranking.html">multi-phase ranking</a> pipeline, 
or combines nearest neighbor search with filters. See <a href="performance/sizing-search.html">Sizing search</a>.

## HNSW Operations 
Changing the [distance-metric](reference/schema-reference.html#distance-metric)
for a tensor field with `hnsw` `index` requires [restarting](reference/schema-reference.html#changes-that-require-restart-but-not-re-feed), 
but not re-indexing. Similar, changing the `max-links-per-node` and
`neighbors-to-explore-at-insert` construction parameters requires re-starting. 


