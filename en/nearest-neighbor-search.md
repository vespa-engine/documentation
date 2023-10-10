---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Nearest Neighbor Search"
redirect_from:
- /documentation/nearest-neighbor-search.html
---

Nearest neighbor search, or vector search, is a technique used
to find the closest data points to a given query point in a high-dimensional vector space.
This is supported in Vespa using the
[nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator.
This operator can be combined with other filters or query terms using the
[Vespa query language](query-language.html),
making it easy to create hybrid solutions that combine modern vector based techniques with
[traditional information retrieval](text-matching.html).

Also try [pyvespa examples](https://pyvespa.readthedocs.io/en/latest/examples/pyvespa-examples.html#Neighbors).


## Minimal example
A nearest neighbor search has at least these components: a document vector, a query vector,
a rank profile using `closeness()` and a query with the `nearestNeighbor` operator:
<pre>
# Schema definition of the vector in documents
    document doc {

        field <span class="pre-hilite">d_vector</span> type tensor&lt;float&gt;(d[3]) {
            indexing: summary | attribute
        }

    }

# Rank profile definition in schema:
#  - using the closeness() rank feature
#  - defining the q_vector type that must match the d_vector type
    rank-profile rank_docs inherits default {
        inputs {
            query(<span class="pre-hilite">q_vector</span>) tensor&lt;float&gt;(d[3])
        }
        first-phase {
            expression: <span class="pre-hilite">closeness</span>(field, d_vector)
        }
    }

# A query with
#  - a nearestNeighbor operator with document and query vectors
#  - selecting the rank_docs rank profile
$ vespa query 'select * from docs where {targetHits: 3}<span class="pre-hilite">nearestNeighbor</span>(d_vector, q_vector)' \
  <span class="pre-hilite">ranking=rank_docs</span> \
  'input.query(q_vector)'='[1,2,3]'

# Documents with vectors
{
    "put": "id:mynamespace:music::a-head-full-of-dreams",
    "fields": {
        "d_vector": [0,1,2]
    }
}
</pre>
The `nearestNeighbor` query operator will calculate values
used by the [closeness()](reference/rank-features.html#closeness(dimension,name)) rank feature.
{% include note.html content='closeness(`field`, d_vector)
means that the closeness rank feature shall use the d_vector <span style="text-decoration: underline">field</span>.
<br/><br/>
Applications can have multiple vector fields.
These cases assign <span style="text-decoration: underline">labels</span> to the different `nearestNeighbor` operators,
so the closeness() rank feature refers to the different operators (using different fields)
See other examples of using closeness(`label`, q)
in the [nearest neighbor search guide](nearest-neighbor-search-guide.html#using-label).' %}

Read more in this guide on tensor types, distance metrics, rank profiles
and approximate nearest neighbor search.


## Vectors
A vector is represented by a [tensor](tensor-user-guide.html) with one indexed dimension.
Example [tensor type](reference/tensor.html#tensor-type-spec) representing a float vector with 384 dimensions:
<pre>
tensor&lt;float&gt;(x[384])
</pre>

Document vectors are stored in a
[tensor field](reference/schema-reference.html#tensor)
defined in the document [schema](reference/schema-reference.html).
A tensor type (dense) with one indexed dimension stores a single vector per document:
<pre>
field doc_embedding type tensor&lt;float&gt;(x[384]) {
    indexing: attribute
}
</pre>

A tensor type (mixed) with one mapped and one indexed dimension stores multiple vectors per document:
<pre>
field doc_embeddings type tensor&lt;float&gt;(m{},x[384]) {
    indexing: attribute
}
</pre>

Similarly, the type of a query vector is defined in a
[rank-profile](reference/schema-reference.html#rank-profile):
<pre>
rank-profile my_profile {
    inputs {
        query(query_embedding) tensor&lt;float&gt;(x[384])
    }
    ...
}
</pre>

This all ties together with the [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator
that expects two arguments; the document tensor field name which is searched and the input query tensor name.
The operator finds the documents that are closest to the query vector
using the [distance-metric](#distance-metrics-for-nearest-neighbor-search) defined in the tensor field.
Note that the document schema can have multiple tensor fields storing vectors,
and the query can have multiple `nearestNeighbor` operators searching different tensor fields.

Support for using the `nearestNeighbor` operator with a mixed tensor with multiple vectors per document
is available in Vespa 8.144.19.

To learn how Vespa can create the vectors for you, see [embedding](embedding.html).


## Using nearest neighbor search
The following sections demonstrates how to use the
[nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator.

These examples use **exact** nearest neighbor search with perfect accuracy,
but which is computationally expensive for large document volumes since 
the distance metric must be calculated for every document that matches
the boolean query filters.
See also the [practical nearest neighbor search guide](nearest-neighbor-search-guide.html) for more examples.

Exact nearest neighbor search scales close to linearly with
[number of threads used per query](performance/practical-search-performance-guide.html#multithreaded-search-and-ranking).
This can be used to make exact nearest neighbor search run with acceptable serving latency.
Using more threads per search to reduce latency is still costly for larger vector volumes 
or high query throughput applications, as the number of distance calculations
involved in the query does not change by changing number of threads performing the search. 

A cost-efficient approach is to use **approximate** search instead.
See how to use **approximate** nearest neighbor search with `HNSW` in
the [Approximate Nearest Neighbor Search](approximate-nn-hnsw.html) document.

The following [document schema](schemas.html) is used to illustrate Vespa's support for 
vector search, or nearest neighbor search:

<pre>
schema product {

    document product {

        field in_stock type bool {
            indexing: summary | attribute
            rank: filter
            attribute: fast-search
        }

        field popularity type float {
            indexing: summary | attribute
        }

        field text_embedding type tensor&lt;float&gt;(x[384]) {
            indexing: summary | attribute
            attribute {
                distance-metric: prenormalized-angular
            }
        }

        field image_embeddings type tensor&lt;float&gt;(i{},x[512]) {
            indexing: summary | attribute
            attribute {
                distance-metric: angular
            }
        }

    }

}
</pre>

The `product` document schema has 4 fields.
The fields of type [tensor](tensor-user-guide.html) represent vector embeddings:

- `text_embedding` - float vector with 384 dimensions.
- `image_embeddings` - multiple float vectors with 512 dimensions.

The `text_embedding` field stores a dense vectorized embedding representation
of the product description and which use [prenormalized-angular](reference/schema-reference.html#distance-metric)
as `distance-metric`. See for example
[Dense Retrieval using bi-encoders over Transformer models](https://blog.vespa.ai/pretrained-transformer-language-models-for-search-part-2/).

The `image_embeddings` field stores multiple dense vectorized embedding representations
of the product images and which use [angular](reference/schema-reference.html#distance-metric)
as `distance-metric`.
See for example [text to image search using CLIP with Vespa](https://blog.vespa.ai/text-image-search/).

### Distance metrics for nearest neighbor search
Vespa supports six different [distance-metrics](reference/schema-reference.html#distance-metric):

* `euclidean`
* `angular`
* `dotproduct`
* `prenormalized-angular`
* `hamming`
* `geodegrees`

The distance-metric is a property of the field.
This is obvious when `index` is set on the vector field,
as the distance metric is used when building the index structure.
Without `index`, no extra data structures are built for the field,
and the distance-metric setting is used when calculating the distance at query-time.
It still makes sense to have the metric as a field-property,
as the field values are often produced using a specific distance metric.

### Configure rank profiles for nearest neighbor search
Lastly, one need to configure how to [rank](ranking.html) products which 
are retrieved by the nearest neighbor search:

<pre>
rank-profile semantic_similarity {
    inputs {
        query(query_embedding) tensor&lt;float&gt;(x[384])
    }
    first-phase {
        expression: closeness(field, text_embedding)
    }
}

rank-profile image_similarity {
    inputs {
        query(image_query_embeddings) tensor&lt;float&gt;(x[512]])
    }
    first-phase {
        expression: closeness(field, image_embeddings)
    }
}
</pre>

The `rank-profile` specifies the query input tensor names and types. The query input tensors
must be of the same dimensionality as the document vector and have the same dimension name. 

Skipping the query tensor definition will cause a query time error:
```
Expected a tensor value of 'query(query_embedding)' but has [...]
```

The `closeness(field, text_embedding)` is a [rank-feature](reference/rank-features.html#closeness(dimension,name))
calculated by the [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator. 
This calculates a score in the range [0, 1], where 0 is infinite distance,
and 1 is zero distance. This is convenient because Vespa sorts hits by decreasing relevancy score,
and one usually want the closest hits to be ranked highest.

The `closeness(field, image_embeddings)` [rank-feature](reference/rank-features.html#closeness(dimension,name))
operators over a tensor field that stores multiple vectors per document.
For each document, the vector that is closest to the query vector is used in the calculation.

The `first-phase` is part of Vespa's [phased ranking](phased-ranking.html) support.
Phased ranking enables re-ranking of the top-k best scoring hits as ranked
or retrieved from the previous ranking phase. The computed ranking score is rendered as `relevance` in
the default [Vespa JSON result format](reference/default-result-format.html). If the `relevance` field
of the hit becomes 0.0 one usually have forgotten to specify the correct ranking profile. 

An example of a `rank-profile` also specifying an additional [re-ranking phase](phased-ranking.html):
<pre>
rank-profile image_similarity_with_reranking {
    inputs {
        query(image_query_embedding) tensor&lt;float&gt;(x[512]])
    }
    first-phase {
        expression: closeness(field, image_embeddings)
    } 
    second-phase {
        rerank-count: 1000
        expression: closeness(field, image_embeddings) * attribute(popularity)
    }
}
</pre>
In this case, hits retrieved by the
[nearestNeighbor](reference/query-language-reference.html#nearestneighbor)
query operator are re-scored also using
the product's popularity as a signal. The value of the `popularity` field can be read by the
 `attribute(popularity)` rank-feature. The `second-phase` [ranking expression](ranking-expressions-features.html)
combines the popularity with the `closeness(field, image_embeddings)` rank-feature using multiplication.


## Indexing product data
After deploying the application package with the document schema, one
can [index](reads-and-writes.html) the product data using the
[Vespa JSON feed format](reference/document-json-format.html).

In the example below there are two documents.
The vector embedding fields are using
[indexed tensor short form](reference/document-json-format.html#tensor)
and [mixed tensor short form](reference/document-json-format.html#tensor):
```json
[
    {
        "put": "id:shopping:product::998211",
        "fields": {
            "in_stock": true,
            "popularity": 0.342,
            "text_embedding": [
                0.16766378547490635,
                0.3737005826272204,
                0.040492891373747675,
                ..
            ],
            "image_embeddings": {
                "0": [
                    0.9147281579191466,
                    0.5453696694173961,
                    0.7529545687063771,
                    ..
                ],
                "1": [0.3737005826272204, ..]
            }
        }
    },
    {
        "put": "id:shopping:product::97711",
        "fields": {
            "in_stock": false,
            "popularity": 0.538,
            "text_embedding": [
                0.03515862084651311,
                0.24585168798559187,
                0.6123057708571111,
                ..
            ],
            "image_embeddings": {
                "0": [
                    0.9785931815169806,
                    0.5697209315543527,
                    0.5352198004501647,
                    ..
                ],
                "1": [0.24585168798559187, ..]
            }
        }
    }
]
```

The above JSON formatted data can be fed to Vespa using any of the
[Vespa feeding APIs](reads-and-writes.html#api-and-utilities).

## Querying using nearestNeighbor query operator
The [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator
is used to search the product dataset.
The operator expects two arguments; the document tensor field which is searched and the input query tensor name.

The [targetHits](reference/query-language-reference.html#targethits)
query annotation specifies the number of results to expose to `first-phase`
ranking per content node involved in the query.
`targetHits` is a required parameter and the query will fail if not specified.
The `targetHits` is a lower bound per content node,
and with exact search more hits than `targetHits` are exposed to `first-phase` ranking.

The query tensor is sent as a query input
and the query tensor name is referenced in the second argument of the `nearestNeighbor` operator.
In the following example, the `nearestNeighbor` operator
is used to recommend similar products based on image similarity.
For a given image (e.g. a product image shown in the product search result page) one can find
products which have similar product images.

Note that the nearest neighbors search is limited to products where `in_stock` is `true`.

The overall query is specified using the [Vespa query language](query-language.html)
using the [Query API](query-api.html#http): 

```json
{
    "yql": "select * from product where {targetHits: 100}nearestNeighbor(image_embeddings, image_query_embedding) and in_stock = true",
    "input.query(image_query_embedding)": [
        0.22507139604882176,
        0.11696498718517367,
        0.9418422036734729,
        ..
    ],
    "ranking.profile": "image_similarity",
    "hits": 10
}
```

The YQL query uses logical conjunction `and` to filter the `nearestNeighbor`
by a constraint on the `in_stock` field. 

The query request
also specifies [hits](reference/query-api-reference.html#hits), which determines how
many hits are returned to the client using the [JSON result format](reference/default-result-format.html). 

The total number of hits which is ranked by the ranking profile
depends on the query filters and how fast the nearest neighbor search algorithm converges (for exact search).

The [ranking.profile](reference/query-api-reference.html#ranking.profile) parameter 
controls which ranking profile is used.
In this case, it simply ranks documents based on how close they are in the CLIP embedding space.


## Using Nearest Neighbor from a Searcher Component
As with all query operators in Vespa, one can build the query tree programmatically
in a custom [searcher component](searcher-development.html). 

See the
[RetrievalModelSearcher](https://github.com/vespa-engine/sample-apps/blob/master/msmarco-ranking/src/main/java/ai/vespa/examples/searcher/RetrievalModelSearcher.java)
in the [MS Marco sample application](https://github.com/vespa-engine/sample-apps/tree/master/msmarco-ranking)
for an example of how the NearestNeighborItem is used.


## Using binary embeddings with hamming distance
The following packs a 128 bit embedding representation into a 16 dimensional dense tensor 
using `int8` tensor value precision (16 x 8 = 128 bit):
<pre>
document vector {
    field vector type tensor&lt;int8&gt;(x[16]) {
        indexing: summary | attribute
        attribute {
            distance-metric: hamming
        }
    }
}
rank-profile hamming-nn {
    num-threads-per-search: 12
    first-phase {
        expression: closeness(field,vector)
    }
}
</pre>

Hamming distance search over binary vectors is implemented with xor and pop count cpu instructions.
The rank-profile specifies 
[num-threads-per-search](reference/schema-reference.html#num-threads-per-search) to 
reduce serving latency (but not cost).

See the [Billion Scale Vector Search with Vespa](https://blog.vespa.ai/billion-scale-knn-part-two/)
blog post for a detailed introduction to using binary vectors with hamming distance.
