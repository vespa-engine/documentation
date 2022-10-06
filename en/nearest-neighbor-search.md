---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Nearest Neighbor Search"
redirect_from:
- /documentation/nearest-neighbor-search.html
---

Searching for the nearest neighbors of a data point in high dimensional vector space is a 
fundamental problem for many real-world applications.

Many real-world applications require query-time constrained vector search. 
For example, real-time recommender systems using [vector search for candidate retrieval](tutorials/news-5-recommendation.html) 
need to filter recommendations by hard constraints like regional availability or age group suitability. 
Likewise, search systems using vector search need to support filtering.
For example, typical e-commerce search interfaces allow users to navigate and filter search results using result facets. 

## Using Vespa's nearest neighbor search

The following sections demonstrates how to use the Vespa [nearestNeighbor](reference/query-language-reference.html#nearestneighbor)
query operator. To learn how Vespa can create the vectors for you, see [embedding](embedding.html).

See also the [practical nearest neighbor search guide](nearest-neighbor-search-guide.html)
for many query examples.
These examples use exact nearest neighbor search with perfect accuracy,
but which is computationally expensive for large document volumes since 
the distance metric must be calculated for every document that matches
the boolean query filters.

Exact nearest neighbor search scales close to linearly 
with [number of threads used per query](performance/practical-search-performance-guide.html#multithreaded-search-and-ranking).
Using multiple threads per search, can be used to make 
exact nearest neighbor search run with acceptable serving latency. 
Using more threads per search to reduce latency is still costly for larger vector volumes 
or high query throughput applications, as the number of distance calculations
involved in the query does not change by changing number of threads performing the search. 

A cost-efficient approach is to instead of exact search, using **approximate** search.
See how to use **approximate** nearest neighbor search with `HNSW` in
the [Approximate Nearest Neighbor Search](approximate-nn-hnsw.html) document.

The following Vespa [document schema](schemas.html) is used to illustrate Vespa's support for 
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

        field image_embedding type tensor&lt;float&gt;(d0[512]) {
            indexing: summary | attribute
            attribute {
                distance-metric: angular 
            }
        }

        field text_embedding type tensor&lt;float&gt;(d0[384]) {
            indexing: summary | attribute
            attribute {
                distance-metric: innerproduct
            }
        }
    }

    rank-profile semantic_similarity {
        inputs {
          query(query_embedding) tensor&lt;float&gt;(d0[384])
        }
        first-phase {
          expression: closeness(field, text_embedding)
        }
    }

    rank-profile image_similarity {
        inputs {
          query(image_query_embedding) tensor&lt;float&gt;(d0[512]])
        }
        first-phase {
          expression: closeness(field, image_embedding)
        }
    }
}
</pre>

The `product` document schema has 4 fields. Fields like `popularity` are self-explanatory but the
fields of [tensor](tensor-user-guide.html) type needs more explanation. 

The schema defines two first-order dense tensor types (vectors):
`image_embedding` and `text_embedding`. `&lt;float&gt;` specifies the 
[tensor value type](tensor-user-guide.html#cell-value-types) and `d0` denotes the name of the dimension.

Vespa [tensor cell value types](tensor-user-guide.html#cell-value-types) include: 

* `int8` 1 byte per tensor value. Typically used to represent binary vectors, for example 64 bits can be represented using 8 `int8` values.
* `bfloat16` 2 bytes per tensor value. See [bfloat16 floating-point format](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format).
* `float` 4 bytes per tensor value. Standard float. 
* `double` 8 bytes per tensor value. Standard double

The `image_embedding` field is used to store a dense vectorized embedding representation 
of the product image and which use [angular](reference/schema-reference.html#distance-metric) 
as `distance-metric`. See for example [text to image search using CLIP with Vespa](https://blog.vespa.ai/text-image-search/).

The `text_embedding` field is used to store a dense vectorized embedding representation 
of the product and which use [innerproduct](reference/schema-reference.html#distance-metric) 
as `distance-metric`. See for example [Dense Retrieval using bi-encoders over
 Transformer models](https://blog.vespa.ai/pretrained-transformer-language-models-for-search-part-2/). 

Vespa supports five different [distance-metrics](reference/schema-reference.html#distance-metric):

* `euclidean`
* `angular`
* `innerproduct`
* `hamming`
* `geodegrees`

Lastly, one need to configure how to [rank](ranking.html) products which 
are retrieved by the nearest neighbor search:

<pre>
rank-profile semantic_similarity {
    inputs {
        query(query_embedding) tensor&lt;float&gt;(d0[384])
    }
    first-phase {
        expression: closeness(field, text_embedding)
    }
}

rank-profile image_similarity {
    inputs {
        query(image_query_embedding) tensor&lt;float&gt;(d0[512]])
    }
    first-phase {
        expression: closeness(field, image_embedding)
    }
}
</pre>

The `rank-profile` specifies the query input tensor names and types. The query input tensors
must be of the same dimensionality as the document vector and have the same dimension name. 

Skipping the query tensor definition will cause a query time error:</p>
<pre>
Expected a tensor value of 'query(query_embedding)' but has [...]
</pre>

The `closeness(field, image_embedding)` is a [rank-feature](reference/rank-features.html) calculated
by the [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator. 
The `closeness(field, tensor)` rank feature calculates a score in the range [0, 1], where 0 is infinite distance,
and 1 is zero distance. This is convenient because Vespa sorts hits by decreasing relevancy score,
and one usually want the closest hits to be ranked highest.

The `first-phase` is part of Vespa's [phased ranking](phased-ranking.html) support. In this example
the `closeness` feature is re-used and documents are not re-ordered. 

Phased ranking or multi-stage document ranking, enables re-ranking of the top-k best scoring hits as ranked
or retrieved from the previous ranking phase. The computed ranking score is rendered as `relevance` in
the default [Vespa JSON result format](reference/default-result-format.html). If the `relevance` field
of the hit becomes 0.0 one usually have forgotten to specify the correct ranking profile. 

An example of a `rank-profile` also specifying an additional [re-ranking phase](phased-ranking.html):
<pre>
rank-profile image_similarity_with_reranking {
    inputs {
        query(image_query_embedding) tensor&lt;float&gt;(d0[512]])
    }
    first-phase {
        expression: closeness(field, image_embedding)
    } 
    second-phase {
        rerank-count: 1000
        expression: closeness(field, image_embedding) * attribute(popularity)
    }
}
</pre>
In this case, hits retrieved by the nearest neighbor search operator are re-scored also using
the product's popularity as a signal. The value of the `popularity` field can be read by the
 `attribute(popularity)` rank-feature. The `second-phase` [ranking expression](ranking-expressions-features.html)
combines the popularity with the `closeness(field, image_embedding)` rank-feature using multiplication.  

## Indexing product data
After deploying the application package with the document schema, one
can [index](reads-and-writes.html) the product data using the
[Vespa JSON feed format](reference/document-json-format.html).

In the example below there are two documents, 
the vector fields are using [indexed tensor short form](reference/tensor.html#indexed-short-form).
<pre>
[
  {
    "put": "id:shopping:product::998211",
    "fields": {
      "in_stock": true,
      "popularity": 0.342,
      "image_embedding": {
        "values": [
          0.9147281579191466,
          0.5453696694173961,
          0.7529545687063771,
          ..
         ]
      },
      "text_embedding": {
        "values": [
          0.16766378547490635,
          0.3737005826272204,
          0.040492891373747675,
          ..
         ]
        }
      }
  },
  {
    "put": "id:shopping:product::97711",
    "fields": {
      "in_stock": false,
      "popularity": 0.538,
      "image_embedding": {
        "values": [
          0.9785931815169806,
          0.5697209315543527,
          0.5352198004501647,
          ..
        ]
      },
      "text_embedding": {
        "values": [
          0.03515862084651311,
          0.24585168798559187,
          0.6123057708571111,
          ..
        ]
      }
    }
  }
]
</pre>

The above JSON formatted data can be fed to Vespa using any of the
[Vespa feeding apis](reads-and-writes.html#api-and-utilities).

## Querying using nearestNeighbor query operator
To query the product dataset one uses the
[nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator.
The operator expects two arguments; the document tensor field which is searched and the input query tensor name.

The `targetHits` query annotation specifies the number of results that one wants to expose to `first-phase`
ranking per node involved in the query. `targetHits` is a required parameter and the query will fail if not specified.
The `targetHits` is a lower bound per node, and with exact search more hits than `targetHits` are exposed to `first-phase` ranking.

The query tensor is sent as a query tensor input 
and the query tensor name is referenced in the second argument of the `nearestNeighbor` operator.
In the following example, the `nearestNeighbor` operator
is used to recommend similar products based on image similarity.
For a given image (e.g. a product image shown in the product search result page) one can find
products which have a similar product image.

The search for nearest neighbors in the CLIP image embedding space is limited to products
where `in_stock` is `true`.

The overall query is specified using the [Vespa query language](query-language.html)
using the [Query API](query-api.html#http): 

<pre>
{
    "yql": "select * from product where {targetHits: 100}nearestNeighbor(image_embedding, image_query_embedding) and in_stock = true",
    "input.query(image_query_embedding)": [
        0.22507139604882176,
        0.11696498718517367,
        0.9418422036734729,
        ...
    ],
    "ranking.profile": "image_similarity",
    "hits": 10
}
</pre>

The YQL query uses logical conjunction `and` to filter the nearest neighbors 
by a constraint on the `in_stock` field. 

The [targetHits](reference/query-language-reference.html#targethits) specifies
the number of hits one want to expose to [ranking](ranking.html). The query request 
also specifies [hits](reference/query-api-reference.html#hits), which determines how
many hits are returned to the client using the [JSON result format](reference/default-result-format.html). 

The total number of hits which is ranked by the ranking profile
depends on the query filters and how fast the nearest neighbor search algorithm converges (for exact search).

The [ranking.profile](reference/query-api-reference.html#ranking.profile) parameter 
controls which profile is used. In this case, it simply ranks documents based on how close they are in the CLIP embedding space.


## Using Nearest Neighbor from a Searcher Component
As with all query operators in Vespa, one can also build the query tree programmatically
in a custom [searcher component](searcher-development.html). 

The following example executes the incoming query and fetch the tensor of the top ranking hit
ranked by whatever rank-profile was specified in the search request.

The `image_embedding` tensor from the top ranking hit is read and used as the input
for the `nearestNeighbor` query operator
to find related products (using the rank profile described in earlier sections).

<pre>{% highlight java %}
package ai.vespa.example.searcher;

import com.yahoo.prelude.query.NearestNeighborItem;
import com.yahoo.search.Query;
import com.yahoo.search.Result;
import com.yahoo.search.Searcher;
import com.yahoo.search.result.Hit;
import com.yahoo.search.searchchain.Execution;
import com.yahoo.tensor.Tensor;

public class FeedbackSearcher extends Searcher {

    @Override
    public Result search(Query query, Execution execution) {
        Result result = execution.search(query);
        if (result.getTotalHitCount() == 0)
            return result;
        execution.fill(result); // fetch the summary data of the hits if needed
        Hit bestHit = result.hits().get(0);
        Tensor clipEmbedding = (Tensor) bestHit.getField("image_embedding");

        Query relatedQuery = new Query();
        relatedQuery.getRanking().setProfile("image_similarity");
        relatedQuery.getRanking().getFeatures().put("query(image_query_embedding)", clipEmbedding);
        NearestNeighborItem nn = new NearestNeighborItem("image_embedding",  "image_query_embedding");
        nn.setTargetNumHits(10);
        relatedQuery.getModel().getQueryTree().setRoot(nn);
        return execution.search(relatedQuery);
    }
}
{% endhighlight %}</pre>

It is also possible to embed the `vectorization` components in Vespa using 
stateless [ML model evaluation](https://blog.vespa.ai/stateless-model-evaluation/). 

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
