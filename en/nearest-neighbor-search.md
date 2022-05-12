---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Nearest Neighbor Search"
redirect_from:
- /documentation/nearest-neighbor-search.html
---

Searching for the nearest neighbors of a data point in high dimensional vector space is a 
fundamental problem for many real-time serving applications.

Many real-world applications require query-time constrained vector search. 
For example, real-time recommender systems using [vector search for candidate retrieval](tutorials/news-5-recommendation.html) 
need to filter recommendations by hard constraints like regional availability or age group suitability. 
Likewise, search systems using vector search need to support filtering.
For example, typical e-commerce search interfaces allow users to navigate and filter search results using result facets. 

## Using Vespa's nearest neighbor search

The following sections demonstrates how to use the [Vespa nearestNeighbor](reference/query-language-reference.html#nearestneighbor)
query operator. See also the [practical nearest neighbor search guide](nearest-neighbor-search-guide.html)
for many query example. 

These examples use exact nearest neighbor search with perfect accuracy,
but which is computationally expensive for large document volumes since 
the distance metric must be calculated for every document that matches
the boolean query filters.

Exact nearest neighbor search scales close to linearly with number of threads used per query.  
Using multiple threads per search, can be used to make exact search run with acceptable serving latency. 
Using more threads per search to reduce latency is still costly, but the results are exact without any accuracy loss. 

See how to use approximate nearest neighbor search with `HNSW` in
the [Approximate Nearest Neighbor Search](approximate-nn-hnsw.html) document.


<pre>
schema product {

    document product {

        field title type string {
            indexing: summary | index
        }

        field in_stock type bool {
            indexing: summary | attribute
        }

        field price type int {
            indexing: summary | attribute
        }

        field popularity type float {
            indexing: summary | attribute
        }

        field image_sift_encoding type tensor&lt;float&gt;(d0[128]) {
            indexing: summary | attribute
            attribute {
                distance-metric: euclidean
            }
        }

        field bert_embedding type tensor&lt;float&gt;(d0[384]) {
            indexing: summary | attribute
            attribute {
                distance-metric: angular
            }
        }
    }

    rank-profile semantic_similarity {
        inputs {
          query(query_embedding) tensor&lt;float&gt;(d0[384])
        }
        first-phase {
          expression: closeness(field, bert_embedding)
        }
    }

    rank-profile image_similarity {
        inputs {
          query(sift_embedding) tensor&lt;float&gt;(d0[128]])
        }
        first-phase {
          expression: closeness(field, image_sift_embedding)
        }
    }
}
</pre>

The `product` document schema is made up of six fields.
Fields like `title`, `in_stock`, `price` and `popularity` are self-explanatory but the
fields of [tensor](tensor-user-guide.html) type needs more explanation. 

The `image_sift_encoding` tensor field is used to store the
[scale-invariant feature transform (SIFT)](https://en.wikipedia.org/wiki/Scale-invariant_feature_transform)
encoding of a product catalog image.

The tensor definition specifies a first-order dense tensor and has exactly 128 dimensions. 
The &lt;float&gt; defines [tensor value type](tensor-user-guide.html#cell-value-types).
When searching for nearest neighbors in the SIFT embedding vector space, one use
[euclidean](reference/schema-reference.html#distance-metric) as `distance-metric`.


The `bert_embedding` field is used to store a dense vectorized embedding representation 
of the product and which use [angular](reference/schema-reference.html#distance-metric) 
as `distance-metric`. See [Dense Retrieval using bi-encoders over
 Transformer models](https://blog.vespa.ai/pretrained-transformer-language-models-for-search-part-2/)

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
          expression: closeness(field, bert_embedding)
        }
    }

    rank-profile image_similarity {
        inputs {
          query(sift_embedding) tensor&lt;float&gt;(d0[128]])
        }
        first-phase {
          expression: closeness(field, image_sift_embedding)
        }
    }
</pre>
The `rank-profile` also specifies the query input tensor names. The query input tensors
must be of the same dimensionality as the document vector and the same dimension name. 

Skipping the query tensor definition will cause a query time error:</p>
<pre>
Expected a tensor value of 'query(sift_embedding)' but has [...]
</pre>

The `closeness(field, image_sift_encoding)` is a [rank-feature](reference/rank-features.html) calculated
by the [nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator. 
The `closeness()` rank feature calculates a score in the range [0, 1], where 0 is infinite distance,
and 1 is zero distance. This is convenient because Vespa sorts hits by decreasing relevancy score,
and one usually want the closest hits to be ranked highest.

The `first-phase` is part of Vespa's <a href="phased-ranking.html">phased ranking</a> support. In this example
the `closeness` feature is re-used and documents are not re-ordered. 

Phased ranking or multi-stage document ranking, enables re-ranking of the top-k best scoring hits as ranked or
or retrieved from the previous ranking phase. The computed ranking score is rendered as `relevance` in
the default [Vespa JSON result format](reference/default-result-format.html). If the `relevance` field
of the hit becomes 0.0 one usually have forgotten to specify the correct ranking profile.


## Indexing product data
After deploying the application package with the document schema, one
can [index](reads-and-writes.html) the product data using the
[Vespa JSON feed format](reference/document-json-format.html).

In the example below there are two documents, 
the tensor fields are using [indexed tensor short form](reference/tensor.html#indexed-short-form).
<pre>
[
  {
    "put": "id:shopping:product::998211",
    "fields": {
      "title": "Linen Blend Wide Leg Trousers",
      "in_stock": true,
      "price": 2999,
      "popularity": 0.342,
      "image_sift_encoding": {
        "values": [
          0.9147281579191466,
          0.5453696694173961,
          0.7529545687063771,
          ..
         ]
      },
      "bert_embedding": {
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
      "title": "Loose-fit White Pens",
      "in_stock": false,
      "price": 9999,
      "popularity": 0.538,
      "image_sift_encoding": {
        "values": [
          0.9785931815169806,
          0.5697209315543527,
          0.5352198004501647,
          ..
        ]
      },
      "bert_embedding": {
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

The above json data can be fed to Vespa using any of the
[Vespa feeding apis](reads-and-writes.html#api-and-utilities).
Vespa only supports real time indexing so there is no explicit batch support,
documents become searchable as they are fed to the system.

## Querying product data
To query the data one uses the
[nearestNeighbor](reference/query-language-reference.html#nearestneighbor) query operator.
The operator expects two arguments; the document tensor field which is searched and the input query tensor name.

The `targetHits` query annotation specifies the the number of results that one wants to expose to `first-phase`
ranking. `targetHits` is a required parameter and the query will fail if not specified.
The `targetHits` is a lower bound per node,  and with exact search more hits are exposed to `first-phase` ranking.

The query tensor is sent as a query ranking feature
and the query tensor name is referenced in second argument of the query operator.

<h4>Related Products using Image Similarity</h4>
<p>
  In this example, the <em>nearestNeighbor</em> query operator
  is used to recommend similar products based on image similarity.
  For a given image (e.g. a product image shown in the product search result page) one can find
  products which have a similar product image.
</p>
<p>
  The search for nearest neighbors in the SIFT embedding space is limited to products
  where <em>in_stock</em> is <em>true</em>.
  The overall query is specified using
  the <a href="query-language.html">YQL query language</a>
  and the <a href="query-api.html#http">query api request</a> becomes:
</p>
<pre>
{
    "yql": "select title, price from sources products where ({targetHits: 10}nearestNeighbor(image_sift_encoding,query_vector_sift)) and in_stock = true",
    "input.query(query_vector_sift)": [
        0.22507139604882176,
        0.11696498718517367,
        0.9418422036734729,
        ...
    ],
    "ranking.profile": "image-similarity",
    "hits": 10
}
</pre>
<p>
  The YQL query uses logical conjunction <em>and</em> so that the nearest neighbor search is restricted
  to documents where <em>in_stock</em> is true.
  The <a href="reference/query-language-reference.html#targethits">targetHits</a> is the desired number of neighbors
  which is exposed to the first-phase ranking function declared in the image-similarity ranking profile.
</p>
<p>
  The total number of hits which is ranked by the ranking profile
  depends on the query filters and how fast the nearest neighbor search algorithm converges.
  The operator might expose more than 10 hits to the <em>first-phase</em> ranking expression.
  Since there is filtering on <em>in_stock</em>,
  the query might return zero results in the case where the entire product catalog is out of stock.
</p>
<p>
  The <em>ranking.profile</em> parameter controls the <em>rank-profile</em> we described earlier,
  which simply ranks documents based on how similar they are in the SIFT vector encoding space.
</p>
<p>
  Finally, the <em>hits</em> parameter controls how many hits are returned in the response.
  If the documents are partitioned over multiple content nodes the <em>targetHits</em> is per node,
  so with e.g. 10 nodes we get at least 100 nearest neighbors fully evaluated
  using the <em>first-phase</em> ranking function.
</p>
<p>
  In this example, the <em>first-phase</em> expression is the <em>closeness</em> score
  as calculated by the <em>nearestNeighbor</em> operator.
  One could re-order hits by changing the first-phase ranking function,
  and the following would <em>re-rank</em> the nearest neighbors which are in stock using the price:
</p>
<pre>
rank-profile image-similarity-price {
    first-phase {
        expression: if(isNan(attribute(price)) == 1,0.0, attribute(price))
    }
}
</pre>
<p>
  Here the <em>closeness</em> score calculated by the <em>nearestNeighbor</em> query operator is ignored,
  documents are instead re-ranked by <em>price</em>.
</p>

<h4>Related Products using BERT Embedding Similarity</h4>
<p>
  As an alternative to using product image similarity to find related items one could
  also use the textual BERT embedding representation from the product:
</p>
<pre>
rank-profile similarity-using-bert {
    first-phase {
        expression: closeness(field, bert_embedding)
    }
}
</pre>

<h4>Related Products using a hybrid combination</h4>
<p>
It is also possible to combine the two methods for retrieving related products. 
In this example one use a single query request using disjunction (OR)
logical operator to retrieve products which are close in either vector space.
The ranking function uses weighted linear combination of the <em>closeness</em> scores
produced by two <em>nearestNeighbor</em> query operators:
</p>
<pre>
rank-profile hybrid-similarity {
    first-phase {
        expression: {
            query(bert_weight)*closeness(field, bert_embedding) +
            (1 - query(bert_weight))*closeness(field, image_sift_encoding)
        }
    }
}
</pre>
<p>
  The search request need to pass both query embedding tensors.
  The query use logical disjunction (OR) to combine the two <em>nearestNeighbor</em> query operators.
  The search request becomes:
</p>
<pre>
{
    "yql": "select title, price from sources products where (({targetHits: 10}nearestNeighbor(title_bert_embedding,query_vector_bert))
    or ({targetHits: 10}nearestNeighbor(image_sift_encoding,query_vector_sift))) and in_stock = true",
    "hits": 10,
    "ranking.features.query(query_vector_sift)": [
        0.5158057404746615,
        0.6441591144976925,
        0.24075880767944935,
        ...
    ],
    "ranking.features.query(query_vector_bert)": [
        0.708719978302217,
        0.4800850502044147,
        0.03310770782193717,
        ...
    ],
    "ranking.features.query(bert_weight)": 0.1,
    "ranking.profile": "hybrid-similarity"
}
</pre>


<h3 id="programmatic-usage">Using Nearest Neighbor from a Searcher Component</h3>
<p>
  As with all query operators in Vespa, one can also build the query tree programmatically
  in a custom <a href="searcher-development.html">Searcher component</a>.
</p>
<p>
  In the example below,
  one execute the incoming query and fetch the tensor of the top ranking hit
  ranked by whatever rank-profile was specified in the search request.
  The <em>image_sift_encoding</em> tensor from the top ranking hit is read and used as the input
  for the <em>nearestNeighbor</em> query operator
  to find related products (using the rank profile described in earlier sections).
</p>
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
        Tensor sift_encoding = (Tensor) bestHit.getField("image_sift_encoding");
        Query relatedQuery = new Query();
        relatedQuery.getRanking().setProfile("image-similarity");
        relatedQuery.getRanking().getFeatures().put("query(query_vector_sift)", sift_encoding);
        NearestNeighborItem nn = new NearestNeighborItem("image_sift_encoding",  "query_vector_sift");
        nn.setTargetNumHits(10);
        relatedQuery.getModel().getQueryTree().setRoot(nn);
        return execution.search(relatedQuery);
    }
}
{% endhighlight %}</pre>


<h3 id="hamming-binary">Using binary embeddings with hamming distance</h3>
<p>
  If one for example has a 128 bit binary embedding (hash),
  one can pack 128 bits into a 16 dimensional dense tensor using int8 cell precision:
</p>
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
<p>
  Hamming distance over binary vectors is implemented with xor and pop count cpu instructions, 
  so it is highly efficient. In the example there is also multi-threaded search,
  which can also be used for previous examples for exact brute force nearest neighbor search to 
  reduce serving latency.
  See the <a href="https://blog.vespa.ai/billion-scale-knn-part-two/">Billion Scale vector search</a> 
  blog post for an detailed introduction to using binary vectors and hamming distance search.  
</p>
