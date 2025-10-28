---
# Copyright Vespa.ai. All rights reserved.
title: "Accelerated OR search using the WAND algorithm"
---

This document describes how to use the Weak And algorithm for accelerated OR like search.

The WAND algorithm is described in detail in
[Efficient Query Evaluation using a Two-Level Retrieval Process (PDF)](https://www.researchgate.net/profile/David-Carmel-3/publication/221613425_Efficient_query_evaluation_using_a_two-level_retrieval_process/links/02bfe50e6854500153000000/Efficient-query-evaluation-using-a-two-level-retrieval-process.pdf) by Andrei Z. Broder et al.:

> We have determined that our algorithm significantly reduces the total number of full evaluations by more than 90%,
> almost without any loss in precision or recall.
> At the heart of our approach there is an efficient implementation of a new Boolean construct called WAND or Weak AND
> that might be of independent interest

Vespa has two different implementations of the WAND dynamic pruning algorithm.
Both implementations attempt to retrieve the best top-k scoring documents
without exhaustive scoring all documents which matches any of the terms in the query.

Consider a query example ***is cdg airport in main paris*?** from the
[MS Marco Passage Ranking](https://github.com/microsoft/MSMARCO-Passage-Ranking) query set.
If we run this query over the 8.8M passage documents using OR
we retrieve and rank *7,926,256* documents out of *8,841,823* documents.
That is in other words [ranking](ranking.html) 89% of the total corpus size.
It's close to brute force evaluating all documents (100%).

If we instead change to the boolean retrieval logic to AND,
we only retrieve 2 documents and fail to retrieve the relevant document(s).

The WAND algorithm tries to address this problem by starting the search for candidate documents using OR,
limiting the number of documents that are ranked, saving both latency and resource usage (cost)
while still returning the same or almost the same top-k results as the brute force OR.
For the example, using WAND with *K* or *targetHits* to 1000, only 196,900 documents are fully ranked.
That is a huge improvement over the exhaustive OR search which retrieves and ranks *7,926,256* documents
and at the same time retrieving the same results as the exhaustive OR search.

So what is the catch? Why not use WAND algorithm all the time?
The catch is that the inner wand scoring function can only be a linear sum of the ranking contribution
from each of the query terms,
and one cannot override the score calculation (with a [ranking expression](ranking.html)).
The inner scoring function of both WAND implementations in Vespa cannot be overridden
like the ranking expression controlled by the `first-phase` ranking expression in a rank profile.
Users can only control the weight of the terms or generally features in the query and in the document.
The weights can be adjusted and both WAND implementations in Vespa
attempt to calculate the top-k documents with the highest maximum inner dot product.
WAND could be looked at as performing the maximum inner product search in a sparse vector space,
without brute force calculating it all over all candidates exhaustively.

Vespa has two query operators which implements the WAND algorithm; `weakAnd` and `wand`.
These two query operators have different characteristics:
* `weakAnd` is designed for single valued indexed string fields
  (or fieldset combining multiple indexed string fields).
  `weakAnd` integrates with linguistic processing (tokenization and stemming).
  It uses the per-term inverted document frequency and query term weight in the inner scoring
  but does not use document term frequency in the scoring.
* The `wand` query operator which does not integrate with linguistic processing
  like tokenization, stemming and normalization
  and the user (you) must specify the query features and their weight and the document features and their weight.
  The features do not need to be string, and it is recommended to map from string to numeric types.
  For example the pre-trained language model [BERT](https://en.wikipedia.org/wiki/BERT_(language_model))
  uses a fixed vocabulary of about 30K tokens and text snippets are tokenized into a set of token ids.
  We can then represent the document as a bag of BERT token ids (e.g. using weightedset<int> data type)
  where each token id has a weight which is computed during document processing,
  e.g. using [DeepCT or HDCT](https://github.com/AdeDZY/DeepCT) weighting.
  Similar approaches exist for other high dimensional sparse vector spaces
  which do not relate to text matching but where one wants to efficiently perform a maximum inner dot product search.

If you are in doubt whether you can use WAND algorithm to accelerate retrieval,
you can evaluate using a query set and perform the query exhaustive using brute force OR
and compare the top-k results returned when using the approximative WAND.
If top-k as measured by Recall@K is high, you could save compute resources (and get lower latency) by using WAND.

In the following sections we discuss these two WAND implementations in detail.

## weakAnd

The [weakAnd query operator](reference/query-language-reference.html#weakand)
accepts terms searching over multiple fields and also logical conjunctions using OR/AND.
It's designed to retrieve over indexed string fields and fieldsets (single-valued or multivalued)
and integrates fully with linguistic processing like tokenization and stemming.

When using weakAnd via [YQL](query-language.html)
or a [Searcher plugin](searcher-development.html),
specify the target for minimum number of hits the operator should produce per content node involved in the query.

The effect of tuning `targetHits` may not be intuitive.
To ensure that you get the best hits possible with a weakAnd,
set the target number somewhat higher than the number of hits returned to the user;
setting it 10 times higher should be more than enough.

The reason for increasing the target number is that weakAnd uses a ranking function internally (inner product)
and the hits which are evaluated by the weakAnd scorer is also evaluated by the `first-phase` ranking expression.

Anything similar to classic vector ranking should correlate well with weakAnd inner product scoring,
e.g. `nativeFieldMatch` or `bm25` ranking features.

Note that because weakAnd relies on feedback identifying which hits are used for first phase ranking
to increase its threshold for what's considered a good hit,
the special [unranked rank profile](reference/schema-reference.html#rank-profile)
(which turns off ranking completely) may cause weakAnd queries to become slower than using a real rank profile.

The query example expressed in YQL:

```
select * from passages where (
    default contains "is" OR default contains "cdg" OR
    default contains "airport" OR default contains "in" OR default contains "main" OR
    default contains "paris"
)
```

Alternatively using a combination of YQL and user query language

```
{
    "yql": "select * from passages where userQuery()",
    "query": "is cdg airport in main paris?",
    "type": "any"
}
```

Where type *any* means OR.

Using the weakAnd query operator, the query is:

```
select * from passages where (
    {targetHits: 200}
        weakAnd(
            default contains "is", default contains "cdg", default contains "airport",
            default contains "in", default contains "main", default contains "paris"
    )
)
```

We specify that the [target number of hits (top k)](reference/query-language-reference.html#targethits)
should be 200 (Default 100),
and this number is used per content node if the content is distributed over more than one node.

### weakAnd inner scoring

The weakAnd query operator uses the following ranking features when calculating the inner score dot product:
* [term(n).significance](reference/rank-features.html#term(n).significance)
* [term(n).weight](reference/rank-features.html#term(n).weight)

Note that the number of times the term occurs in the document is not used in the inner scoring.

Both term significance and weight features could be overridden in the query using
[annotations](reference/query-language-reference.html#annotations).
If the term significance is not overridden with the query,
the significance is calculated from the indexed corpus using a formula loosely based on
[Inverse Document Frequency](https://en.wikipedia.org/wiki/Tf%E2%80%93idf).

Documents that could not potentially compete with any of the hits already in heap (size targetHits) of top hits are skipped,
while the weakAnd implementation still exposes the hits which were evaluated to the first phase ranking function,
and not only the top k hits.
When configured to use multiple threads per search,
each thread maintains a top-k scoring heap but communicates score thresholds.

Often times, for the performance reasons listed above, it is preferable to use weakAnd instead of OR.
To enable this behavior, set the query property
[weakAnd.replace](reference/query-api-reference.html#weakand.replace) to true.

## wand

The [wand query operator](reference/query-language-reference.html#wand)
works over a single [weightedset field](reference/schema-reference.html#weightedset)
which can be both string or numeric (int/long) - the weight is always int.

Weighted sets of string must be configured with
`match:word` or `match:exact` -
see [match documentation](reference/schema-reference.html#match).
There is no linguistic processing of strings for string features when using the wand query operator.

Below is an example passage document type where we pre-process the text using a BERT tokenizer
and map text to bert token ids and assign a weight to each unique token id.

```
document passage {
    field text type string {
        indexing: summary | index
    }
    field deep_ct_tokens type weightedset<int> {
        indexing: summary |attribute
        attribute:fast-search
    }
}
```

We can process text and tokenize the text with a BERT tokenizer and set the weight per token id:

```
{
    "put": "id:msmarco:passage::8433854",
    "fields": {
        "text": "Charles de Gaulle airport (CDG) is the main international airport for Paris",
        "deep_ct_tokens": {
            "2248": 12,
            "1996": 5,
            "3729": 9,
            "2003": 8,
            "2798": 1,
            "2139": 1,
            "1006": 3,
            "1007": 1,
            "2290": 5,
            "28724": 6,
            "3000": 3,
            "2005": 5,
            "2364": 1,
            "3199": 15
        }
    }
}
```

The wand query operator allows full control over both query side weights and document side weights,
and it is guaranteed that it will find the top k best hits ranked by the inner dot product
between the sparse query vector and the sparse document vector.

The Vespa [rank query operator](reference/query-language-reference.html#rank)
can be used to create a query tree,
where a bag of features is used in the wand for efficient retrieval with normal lexical query terms
to produce matching ranking features like bm25 for the configurable first phase/second-phase ranking.

The example below uses the `rank` operator to also produce normal text matching features
for those top-k documents which are retrieved by the inner product search performed by the wand operator.
The userQuery() does not impact recall,
but creates "normal" ranking features for first-phase or second-phase ranking.
Similar at query time we can use the same type of text to feature mapping
(in this case all query terms have weight 1):

```
{
    "yql":"select * from passages where rank(
        ({targetHits: 25}
            wand(deep_ct_tokens, @tokens)),
            userQuery())",
    "tokens": "{2003: 1, 3729: 1, 2290: 1, 3199: 1, 1999: 1, 2364: 1, 3000: 1}",
    "query": "is cdg airport in main paris?",
    "type": "any",
    "ranking.profile": "deep_bm25"
}
```

With the rank profile *deep_bm25* defined as:

```
rank-profile deep {
    first-phase {
        expression: rawScore(deep_ct_tokens) + bm25(text)
    }
    summary-features {
        bm25(text)
        rawScore(deep_ct_tokens)
    }
}
```

The [rawScore](reference/rank-features.html#rawScore(field)) ranking feature
is the inner dot product calculated by the wand query operator.
For the 25 documents (per node) with the highest inner product score
there is also a bm25(text) score which we combine with the inner product score.
Note that the bm25 is **only** calculated for the top-k hits returned by the wand.

In this example, the inner product score is 41, and the bm25 of the text is 35.003.
