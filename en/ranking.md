---
# Copyright Vespa.ai. All rights reserved.
title: "Ranking"
---

Vespa ranks documents retrieved by a query by performing computations or inference that produces a score for each document.
The documents are sorted in descending order by this score, and highest ranking documents are returned to the user. Ranking
is useful in search and recommendation systems, where the goal is to present the most relevant results to the user.

Ranking in Vespa is configured using
declarative [ranking expressions](ranking-expressions-features.html),
These expressions vary from basic mathematical operations with [rank features](reference/rank-features.html) to
more complex [tensor expressions](tensor-examples.html) or
machine-learned models. These ranking expressions are configured in [rank profiles](#rank-profiles) within document [schemas](schemas.html).

## Retrieval versus ranking

To understand the difference between retrieval (matching) and ranking, consider the
following text-search oriented Vespa query example,
expressed in JSON POST format using Vespa's [query language](query-language.html):

```
  {
    "yql": "select * from doc where text contains \"vespa\"",
    "ranking": {
      "profile": "my-rank-profile"
    },
    "inputs": {
      "query(user_context)": [0.1, 0.2, 0.3]
    }
  }
```

The `yql` part of the query specifies the retrieval part, which retrieves documents that contain the word "vespa".
The `ranking` part specifies the ranking profile to use when **ranking** the retrieved documents.
This profile defines how to compute the score for each document retrieved by the query.

```
  rank-profile my-rank-profile inherits default {
    inputs {
      query(user_context) tensor<float>(x[3])
    }
    first-phase {
      expression: bm25(text) + sum(query(user_context) * attribute(document_context))
    }
  }
```

The `first-phase` part of the rank profile specifies the ranking expression to use when scoring
the retrieved documents. In this example, the expression is a combination of the [BM25](reference/bm25.html)
text matching feature and a dot product between the query and document context tensors using
Vespa [tensor computations](tensor-user-guide.html#ranking-with-tensors).

Since the query matched against the *text* field, Vespa can calculate text matching
rank features, such as [bm25](reference/bm25.html).

The `query(user_context)` tensor is another feature that is passed with the query request, but does
not match against any field in the document. Instead, it is used to compute a score based on the dot product
with the `document_context` attribute. This is an example of how Vespa can use additional
features in ranking, even if they do not match against any field in the document.

## Phased ranking

Rank profiles can define multiple [ranking phases](phased-ranking.html), where you can define different ranking expressions
that are applied in sequence. This is useful for separating the ranking logic into multiple steps
where the first phase is executed for all retrieved documents and the second-phase is executed for the top-scoring
documents from the first-phase. This can be used to direct more computation towards the most promising candidate documents.

```
schema myapp {

    rank-profile my-rank-profile {

        first-phase {
            expression {
                attribute(quality) * freshness(timestamp) + bm25(title)
            }
        }
        second-phase {
            expression: sum(onnx(my_onnx_model))
            rerank-count: 50
        }
        global-phase {
          expression: sum(onnx(my_larger_onnx_model))
          rerank-count: 20
      }

    }
}
```

## Machine-Learned model inference

To achieve better ranking accuracy, most organizations turn to machine learned ranking.
Vespa supports importing ML models in these formats:
* [ONNX](onnx.html), allowing importing models from popular ML frameworks like Tensorflow, PyTorch and scikit-learn.
* [XGBoost](xgboost.html)
* [LightGBM](lightgbm.html)

As these are exposed as rank features, it is possible to rank documents using a *model ensemble*, or unify
models from different frameworks in a single rank-profile.
Models are deployed in [application packages](application-packages.html) or downloaded from urls.

## Rank profiles

Ranking expressions are defined in [rank profiles](reference/schema-reference.html#rank-profile) -
either inside the schema or equivalently in their own files in the
[application package](reference/application-packages-reference.html), named
`schemas/[schema-name]/[profile-name].profile`.

One schema can have any number of rank profiles for implementing e.g. different use cases
or [bucket testing](testing.html#feature-switches-and-bucket-tests) variations.
If no profile is specified in the schema, the [default (nativeRank)](nativerank.html)
profile is used.

Rank profiles can *inherit* other profiles. This makes it possible to define complex profiles and variants
without duplication.

Queries select a rank profile using the
[ranking.profile](reference/query-api-reference.html#ranking.profile) argument
in requests or a [query profiles](query-profiles.html),
or equivalently in [Searcher](searcher-development.html) code, by

```
query.getRanking().setProfile("my-rank-profile");
```

If no profile is specified in the query, the one called `default` is used.
This profile is available also if not defined explicitly. The default rank-profile uses [nativeRank](nativerank.html)
which is a text-scoring only feature. Another built-in rank profile `unranked` is also always available.
Specifying this boosts serving performance in queries which do not need ranking because ordering is not important or
[explicit field sorting](reference/sorting.html) is used.
