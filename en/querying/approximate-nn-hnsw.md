---
# Copyright Vespa.ai. All rights reserved. 
title: "Approximate nearest neighbor search using HNSW index"
keywords: "ann, approximate nearest neighbor"
redirect_from:
  - /en/approximate-nn-hnsw
---

This document describes how to speed up searches for nearest neighbors in vector spaces by adding
[HNSW index](../reference/schemas/schemas.html#index-hnsw) to tensor fields.
For an introduction to nearest neighbor search, see [nearest neighbor search](nearest-neighbor-search) documentation, 
for practical usage of Vespa's nearest neighbor search, see [nearest neighbor search - a practical guide](nearest-neighbor-search-guide),
and to have Vespa create vectors for you, see [embedding](../rag/embedding.html).

Vespa implements a modified version of the Hierarchical Navigable Small World (HNSW) graph algorithm [paper](https://arxiv.org/abs/1603.09320).
The implementation in Vespa supports:

* **Filtering** - The search for nearest neighbors can be constrained by query filters.
The [nearestNeighbor](../reference/querying/yql.html#nearestneighbor) query operator can be combined with other filters or query terms using the [Vespa query language](query-language.html).
See the query examples in the [practical guide](nearest-neighbor-search-guide#combining-approximate-nearest-neighbor-search-with-query-filters).

* **Multi-field vector Indexing** - A schema can include multiple indexed tensor fields and search any combination
of them in a query. This is useful to support multiple models, multiple text sources, and multi-modal search such
as indexing both a textual description and image for the same entity.

* **Multi-vector Indexing** - A single document field can contain any number of vector values by
defining it as a mixed tensor (a "map of vectors").
Documents will then be retrieved by the closest vector in each document compared to the query vector.
See the [Multi-vector indexing sample application](https://github.com/vespa-engine/sample-apps/tree/master/multi-vector-indexing)
for examples.
This is commonly used to [index documents with multiple chunks](../rag/working-with-chunks.html).
See also [this blog post](https://blog.vespa.ai/semantic-search-with-multi-vector-indexing/#implementation).

* **Real Time Indexing** - CRUD (Create, Add, Update, Remove) vectors in the index in true real time.

* **Mutable HNSW Graph** - No query or indexing overhead from searching multiple <em>HNSW</em> graphs. In Vespa, 
there is one graph per tensor field per content node. No segmented or partitioned graph where a query against 
a content node need to scan multiple HNSW graphs.

* **Multithreaded Indexing** - The costly part when performing real time changes to the *HNSW* graph
is distance calculations while searching the graph layers to find which links to change.
These distance calculations are performed by multiple indexing threads.

* **Multiple value types** - The cost driver of vector search is often storing the vectors in memory,
which is required to produce accurate results at low latency. An effective way to reduce cost is to reduce the
size of each vector value. Vespa supports double, float, bfloat16, int8 and [single-bit values](../rag/binarizing-vectors.md).
Changing from float to bfloat16 can halve cost with negligible impact on accuracy, while single-bit
values greatly reduce both memory and cpu costs, and can be effectively combined with larger vector values 
stored on disk as a paged attribute to be used for ranking.

* **Optimized HNSW lookups** - ANN searches in Vespa [support](https://blog.vespa.ai/tweaking-ann-parameters/) 
both pre-and post-filtering, beam exploration, and filtering before distance calculation ("Acorn 1").
Tuning parameters for these makes it possible to strike a good balance between performance and accuracy for any
data set. Vespa's [ANN tuning tool](https://vespa-engine.github.io/pyvespa/examples/ann-parameter-tuning-vespa-cloud.html) 
can be used to automate the process.

## Using Vespa's approximate nearest neighbor search
The query examples in [nearest neighbor search](nearest-neighbor-search) uses exact search, which has perfect accuracy.
However, this is computationally expensive for large document volumes
as distances are calculated for every document which matches the query filters.

To enable fast approximate matching, the tensor field definition
needs an `index` directive. A Vespa [document schema](../basics/schemas.html) can declare multiple tensor fields with `HNSW` enabled.

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

The two vector fields use different [distance-metric](../reference/schemas/schemas.html#distance-metric)
and `HNSW` index settings:

* `max-links-per-node` - a higher value increases recall accuracy, but also memory usage, indexing and search cost.
* `neighbors-to-explore-at-insert` - a higher value increases recall accuracy, but also indexing cost.

Choosing the value of these parameters affects both accuracy, search performance, memory usage and indexing performance.
See [Billion-scale vector search with Vespa - part two](https://blog.vespa.ai/billion-scale-knn-part-two/)
for a detailed description of these tradeoffs. See [HNSW index reference](../reference/schemas/schemas.html#index-hnsw) 
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
recall accuracy. As the search-time parameter [hnsw.exploreAdditionalHits](../reference/querying/yql.html#hnsw-exploreadditionalhits) 
is increased, the lower combination reaches about 70% recall@10, while the higher combination reaches
about 92% recall@10. The improvement in accuracy needs to be weighted against the impact on indexing performance and
memory usage. 

## Using approximate nearest neighbor search 

With an *HNSW* index enabled on the tensor field one can choose between approximate
or exact (brute-force) search by using the [approximate query annotation](../reference/querying/yql.html#approximate)

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
[query timeout](../reference/api/query.html#timeout).
The default [query timeout](../reference/api/query.html#timeout) is 500ms,
which will be too low for an exact search over many vectors.

In addition to [targetHits](../reference/querying/yql.html#targethits), 
there is a [hnsw.exploreAdditionalHits](../reference/querying/yql.html#hnsw-exploreadditionalhits) parameter
which controls how many extra nodes in the graph (in addition to `targetHits`)
that are explored during the graph search. This parameter is used to tune accuracy quality versus query performance. 

## Combining approximate nearest neighbor search with filters 
The [nearestNeighbor](../reference/querying/yql.html#nearestneighbor) query operator can be combined with other
query filters using the [Vespa query language](../reference/querying/yql.html) and its query operators.
There are two high-level strategies for combining query filters with approximate nearest neighbor search:
* [pre-filtering](https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/#pre-filtering-strategy) (the default)
* [post-filtering](https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/#post-filtering-strategy)

These strategies can be configured in a rank profile using
[approximate-threshold](../reference/schemas/schemas.html#approximate-threshold) and
[post-filter-threshold](../reference/schemas/schemas.html#post-filter-threshold).
See
[Controlling the filtering behavior with approximate nearest neighbor search](https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/#controlling-the-filtering-behavior-with-approximate-nearest-neighbor-search)
for more details.

Note that when using `pre-filtering` the following query operators are not included when evaluating the filter part of the query:
* [geoLocation](../reference/querying/yql.html#geolocation)
* [predicate](../reference/querying/yql.html#predicate)

These are instead evaluated after the approximate nearest neighbors are retrieved, more like a `post-filter`.
This might cause the search to expose fewer hits to ranking than the wanted `targetHits`.

Since {% include version.html version="8.78" %} the `pre-filter` can be evaluated using
[multiple threads per query](../performance/practical-search-performance-guide.html#multithreaded-search-and-ranking).
This can be used to reduce query latency for larger vector datasets where the cost of evaluating the `pre-filter` is significant.
Note that searching the `HNSW` index is always single-threaded per query.
Multithreaded evaluation when using `post-filtering` has always been supported,
but this is less relevant as the `HNSW` index search first reduces the document candidate set based on `targetHits`.

## Nearest Neighbor Search Considerations

* **targetHits**:
The [targetHits](../reference/querying/yql.html#targethits)
specifies how many hits one wants to expose to [ranking](../basics/ranking.html) *per content node*.
Nearest neighbor search is typically used as an efficient retriever in a [phased ranking](../ranking/phased-ranking.html)
pipeline. See [performance sizing](../performance/sizing-search.html). 

* **Pagination**:
Pagination uses the standard [hits](../reference/api/query.html#hits) 
and [offset](../reference/api/query.html#offset) query api parameters. 
There is no caching of results in between pagination requests,
so a query for a higher `offset` will cause the search to be performed over again.
This aspect is no different from [sparse search](../ranking/wand.html) not using nearest neighbor query operator.  

* **Total hit count is not accurate**:
Technically, all vectors in the searchable index are neighbors. There is no strict boundary between a match 
and no match. Both exact (`approximate:false`) and approximate (`approximate:true`) usages
of the [nearestNeighbor](../reference/querying/yql.html#nearestneighbor) query operator
does not produce an accurate `totalCount`.
This is the same behavior as with sparse dynamic pruning search algorithms like
[weakAnd](../reference/querying/yql.html#weakand) and [wand](../reference/querying/yql.html#wand). 
  
* **Grouping** counts are not accurate:
Grouping counts from [grouping](grouping.html) are not accurate when using [nearestNeighbor](../reference/querying/yql.html#nearestneighbor)
search. This is the same behavior as with other dynamic pruning search algorithms like
[weakAnd](../reference/querying/yql.html#weakand) and
[wand](../reference/querying/yql.html#wand). 
See the [Result diversification](https://blog.vespa.ai/result-diversification-with-vespa/) 
blog post on how grouping can be combined with nearest neighbor search. 


## Scaling Approximate Nearest Neighbor Search

### Memory 
Vespa tensor fields are [in-memory](../content/attributes.html) data structures and so is the `HNSW` graph data structure.
For large vector datasets the primary memory resource usage relates to the raw vector field memory usage.

Using lower tensor cell type precision can reduce memory footprint significantly, for example using `bfloat16` 
instead of `float` saves close to 50% memory usage without significant accuracy loss. 

Vespa [tensor cell value types](../performance/feature-tuning.html#cell-value-types) include:

* `int8` - 1 byte per value. Also used to represent [packed binary values](../rag/binarizing-vectors.md).
* `bfloat16` - 2 bytes per value. See [bfloat16 floating-point format](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format).
* `float` - 4 bytes per value. Standard float.
* `double` - 8 bytes per value. Standard double.


### Search latency and document volume

The `HNSW` greedy search algorithm is sublinear (close to log(N) where N is the number of vectors in the graph).
This has interesting properties when attempting to add more
nodes horizontally using [flat data distribution](../performance/sizing-search.html#data-distribution).
Even if the document volume per node is reduced by a factor of 10, the search latency is only reduced by 50%. 
Still, flat scaling helps scale document volume, and increasing indexing throughput as vectors are partitioned
randomly over a set of nodes. 

Pure vector search applications (without filtering, or re-ranking) should attempt to scale up document volume by using 
larger instance type and maximize the number of vectors per node. To scale with query throughput,
use [grouped data distribution](../performance/sizing-search.html#data-distribution) to replicate content. 

Note that strongly sublinear search is not necessarily true if the application
uses nearest neighbor search for candidate retrieval in a <a href="../phased-ranking.html">multiphase ranking</a> pipeline, 
or combines nearest neighbor search with filters.


## HNSW Operations 
Changing the [distance-metric](../reference/schemas/schemas.html#distance-metric)
for a tensor field with `hnsw` index requires [restarting](../reference/schemas/schemas.html#changes-that-require-restart-but-not-re-feed),
but not re-indexing (re-feed vectors). Similar, changing the `max-links-per-node` and
`neighbors-to-explore-at-insert` construction parameters requires re-starting. 
