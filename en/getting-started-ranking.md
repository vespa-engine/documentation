---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Getting started with ranking"
redirect_from:
- /documentation/getting-started-ranking.html
---

Learn how [ranking](ranking.html) works in Vespa by using the open [query API](query-api.html) of
[vespa-documentation-search](https://github.com/vespa-cloud/vespa-documentation-search).
In this article, find a set of queries invoking different `rank-profiles`, which is the ranking definition.

Ranking is the user-defined computation that scores documents to a query,
here configured in [doc.sd](https://github.com/vespa-cloud/vespa-documentation-search/blob/main/src/main/application/schemas/doc.sd),
also see [schema documentation](schemas.html).
This schema has a set of (contrived) ranking functions, to help learn Vespa ranking.



## Ranking using document features only
Let's start with something simple: _Irrespective of the query, score all documents by the number of in-links to it_.
That is, for any query, return the documents with most in-links first in the result set:

<pre style="display:none" data-test="exec" data-test-assert-contains="attribute(inlinks).count">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20true&ranking=inlinks'
</pre>

{% include query.html content=
"[select * from doc where true;&ranking=inlinks](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20true&ranking=inlinks)"%}

The score, named `relevance` in query results, is the size of the `inlinks` attribute array in the document,
as configured in the `expression`:
```
rank-profile inlinks {
    first-phase {
        expression: attribute(inlinks).count
    }
    summary-features {
        attribute(inlinks).count
    }
}
```


Count the number of entries in `inlinks` in the result and compare with `relevance` - it will be the same.
Observe that the ranking expression does not use any features from the query,
it only uses `attribute(inlinks).count`,
which is a [document feature](reference/rank-features.html#document-features).



## Observing values used in ranking
When developing ranking expressions, it is useful to observe the input values.
Output the input values using [summary-features](reference/schema-reference.html#summary-features).
In this experiment, we will use another rank function, still counting in-links but scoring older documents lower:

<p><!-- depends on mathjax -->
    $$ num\_inlinks * {decay\_const}^{doc\_age\_seconds/3600} $$
</p>

Note:
* use of the `now` [ranking feature](reference/rank-features.html)
* use `pow`, a mathematical function in [ranking expressions](reference/ranking-expressions.html)
* use of constants and functions to write better code

<pre style="display:none" data-test="exec" data-test-assert-contains="summaryfeatures">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20true&ranking=inlinks'
</pre>

{% include query.html content=
"[select * from doc where true&ranking=inlinks_age](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20true&ranking=inlinks_age)"%}

```
rank-profile inlinks_age {
    first-phase {
        expression: rank_score
    }
    summary-features {
        attribute(inlinks).count
        attribute(last_updated)
        now
        doc_age_seconds
        age_decay
        num_inlinks
        rank_score
    }
    constants {
        decay_const: 0.9
    }
    function doc_age_seconds() {
        expression: now - attribute(last_updated)
    }
    function age_decay() {
        expression: pow(decay_const, doc_age_seconds/3600)
    }
    function num_inlinks() {
        expression: attribute(inlinks).count
    }
    function rank_score() {
        expression: num_inlinks * age_decay
    }
}
```
In the query results, here we observe a document with 27 in-links, 9703 seconds old, get at relevance at 20.32
(the age of documents will vary with query time):
```
"relevance": 20.325190122213748,
...
"summaryfeatures": {
    "attribute(inlinks).count": 27.0,
    "attribute(last_updated)": 1.615971522E9,
    "now": 1.615981225E9,
    "rankingExpression(age_decay)": 0.7527848193412499,
    "rankingExpression(doc_age_seconds)": 9703.0,
    "rankingExpression(num_inlinks)": 27.0,
    "rankingExpression(rank_score)": 20.325190122213748,
}
```
Using `summary-features` makes it easy to validate and develop the ranking expression.

<!-- ToDo: also use https://docs.vespa.ai/en/reference/schema-reference.html#match-features -->



## Ranking with query features
Let's assume we want to find similar documents, and we define document similarity as having the same number of words.
From most perspectives, this is a poor similarity function, better functions are described later.

The documents have a `term_count` field - so let's add a `ranking.features.query` for term count as well:

<pre style="display:none" data-test="exec" data-test-assert-contains="query(q_term_count)">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20true&ranking=term_count_similarity&ranking.features.query(q_term_count)=1000'
</pre>

{% include query.html content=
"[select * from doc where true;&ranking=term_count_similarity&ranking.features.query(q_term_count)=1000](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20true&ranking=term_count_similarity&ranking.features.query(q_term_count)=1000)"%}

<p><!-- depends on mathjax -->
    $$ 1 - \frac{fabs(attribute(term\_count) - query(q\_term\_count))}{1 + attribute(term\_count) + query(q\_term\_count)} $$
</p>

```
rank-profile term_count_similarity {
    first-phase {
        expression {
            1 -
            fabs(    attribute(term_count) - query(q_term_count) ) /
                (1 + attribute(term_count) + query(q_term_count) )
        }
    }
    summary-features {
        attribute(term_count)
        query(q_term_count)
    }
}
```
This rank function will score documents [0-1>, closer to 1 is more similar:
```
"relevance": 0.9985029940119761,
...    
"summaryfeatures": {
    "attribute(term_count)": 1003.0,
    "query(q_term_count)": 1000.0,
}
```
The key learning here is how to transfer ranking features in the query.
Use different names for more query features.



## Ranking with a query tensor
Another similarity function can be overlap in in-links.
We will map the inlinks [weightedset](reference/schema-reference.html#type:weightedset) into a
[tensor](reference/schema-reference.html#type:tensor),
query with a tensor of same type and create a scalar using a tensor product as the rank score.
We use a [mapped](reference/tensor.html#general-literal-form) query tensor,
where the document name is the address in the tensor, using a value of 1 for each in-link:
```
{% raw %}{{links:/en/query-profiles.html}:1,
 {links:/en/page-templates.html}:1,
 {links:/en/overview.html}:1}{% endraw %}
```

{% include important.html content="Vespa cannot know the query tensor type from looking at it -
it must be configured using a [query profile type](ranking-expressions-features.html#query-feature-types).
Below, we use `queryProfile=links` in the query.
Explore the [configuration](https://github.com/vespa-cloud/vespa-documentation-search/tree/main/src/main/application/search/query-profiles):"%}

```
└── query-profiles
    ├── links.xml
    └── types
        └── links.xml
```
The query profile `default` is assumed if not set in the query.
If your application has only _one_ query profile, you can call it `default.xml` and it is always invoked.

As the in-link data is represented in a weightedset,
we use the [tensorFromWeightedSet](reference/rank-features.html#document-features)
rank feature to transform it into a tensor named _links_:
```
rank-profile inlink_similarity {
    first-phase {
        expression: sum(tensorFromWeightedSet(attribute(inlinks), links) * query(links))
    }
    summary-features {
        query(links)
        tensorFromWeightedSet(attribute(inlinks), links)
    }
}
```

<pre style="display:none" data-test="exec" data-test-assert-contains="tensor&lt;float&gt;(links{})">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20true&queryProfile=links&ranking=inlink_similarity&ranking.features.query(links)=%7B%7Blinks%3A%2Fen%2Fquery-profiles.html%7D%3A1%2C%7Blinks%3A%2Fen%2Fpage-templates.html%7D%3A1%2C%7Blinks%3A%2Fen%2Foverview.html%7D%3A1%7D'
</pre>

{% include query.html content=
"[select * from doc where true&queryProfile=links&ranking=inlink_similarity&ranking.features.query(links)={{inlinks:/en/query-profiles.html}:1,{inlinks:/en/page-templates.html}:1,{inlinks:/en/overview.html}:1}](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20true&queryProfile=links&ranking=inlink_similarity&ranking.features.query(links)=%7B%7Blinks%3A%2Fen%2Fquery-profiles.html%7D%3A1%2C%7Blinks%3A%2Fen%2Fpage-templates.html%7D%3A1%2C%7Blinks%3A%2Fen%2Foverview.html%7D%3A1%7D)"%}

Inspect relevance and summary-features:

```
"relevance": 2.0
...
"summaryfeatures": {
  "query(links)": {
    "type": "tensor<float>(links{})",
    "cells": [
      { "address": { "links": "/en/query-profiles.html" }, "value": 1 },
      { "address": { "links": "/en/page-templates.html" }, "value": 1 },
      { "address": { "links": "/en/overview.html" },       "value": 1 } ]
  },
  "tensorFromWeightedSet(attribute(inlinks),links)": {
    "type": "tensor(links{})",
    "cells": [
      { "address": { "links": "/en/page-templates.html" },             "value": 1 },
      { "address": { "links": "/en/jdisc/container-components.html" }, "value": 1 },
      { "address": { "links": "/en/query-profiles.html" },             "value": 1 } ]
  }
}
```

Here, the tensors have one dimension, so they are vectors - 
the sum of the tensor product is hence the doc product.
As all values are 1, all products are 1 and the sum is 2:

<table class="table" style="width: auto">
<thead>
  <tr><th>document</th>
      <th>query</th>
      <th>value</th></tr>
</thead>
<tbody>
  <tr><td>/en/jdisc/container-components.html</td><td></td><td>0</td></tr>
  <tr><td></td><td>/en/overview.html</td><td>0</td></tr>
  <tr><td>/en/page-templates.html</td><td>/en/page-templates.html</td><td>1</td></tr>
  <tr><td>/en/query-profiles.html</td><td>/en/query-profiles.html</td><td>1</td></tr>
</tbody>
</table>

Change values in the query tensor to see difference in rank score, setting different weights for links.

Summary: The problem of comparing two lists of links is transformed into a numerical problem
of multiplying two occurrence vectors, summing co-occurrences and ranking by this sum:
```
sum(tensorFromWeightedSet(attribute(inlinks), links) * query(links))
```

Notes:
* Query tensors can grow large.
  Applications will normally create the tensor in code using a [Searcher](searcher-development.html),
  also see [example](ranking-expressions-features.html#query-feature-types).
* Here the document tensor is created from a weighted set -
  a better way would be to store this in a tensor in the document to avoid the transformation.



## Retrieval and ranking
So far in this guide, we have run the ranking function over _all_ documents.
This is a valid use case for many applications.
However, ranking documents is generally CPU-expensive,
optimizing by reducing the candidate set will increase performance.
Example query using text matching,
dumping [calculated rank features](https://docs.vespa.ai/en/reference/query-api-reference.html#ranking.listFeatures):

<pre style="display:none" data-test="exec" data-test-assert-contains="attributeMatch(inlinks)">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20title%20contains%20%22document%22&ranking.listFeatures'
</pre>

{% include query.html content=
"[select * from doc where title contains \"document\"&ranking.listFeatures](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20title%20contains%20%22document%22&ranking.listFeatures)"%}

See the **long** list of rank features calculated per result.
However, the query filters on documents with "ranking" in the title,
so the features are only calculated for the small set of matching documents.

Running a filter like this is _document retrieval_. Another good example is web search -
the user query terms are used to _retrieve_ the candidate set cheaply (from billions of documents),
then one or more _ranking functions_ are applied to the much smaller candidate set to generate the ranked top-ten.
Another way to look at it is:
* In the retrieval (recall) phase, _find all relevant documents_
* In the ranking phase, _show only relevant documents_.

Still, the candidate set after retrieval can be big, a query can hit all documents.
Ranking all candidates is not possible in many applications.

Splitting the ranking into two phases is another optimization -
use an inexpensive ranking expression to sort out the least promising candidates
before spending most resources on the highest ranking candidates.
In short, use increasingly more power per document as the candidate set shrinks:

<img src="/assets/img/retrieval-ranking.svg" width="584" height="auto" alt="Retrieval and ranking]"/>

Let's try the same query again, with a two-phase rank-profile that also does an explicit rank score cutoff:

<pre style="display:none" data-test="exec" data-test-assert-contains="attribute(inlinks).count">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20title%20contains%20%22document%22&ranking=inlinks_twophase'
</pre>

{% include query.html content=
"[select * from doc where title contains \"document\"&ranking=inlinks_twophase](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20title%20contains%20%22document%22&ranking=inlinks_twophase)"%}

```
rank-profile inlinks_twophase inherits inlinks_age {
    first-phase {
        keep-rank-count       : 50
        rank-score-drop-limit : 10
        expression            : num_inlinks
    }
    second-phase {
        expression            : rank_score
    }
}
```

Note how using rank-profile `inherits` is a smart way to define functions once,
then use in multiple rank-profiles.
Read more about [schema inheritance](schemas.html#schema-inheritance).
Here, `num_inlinks` and `rank_score` are defined in a rank profile we used earlier:

```
    function num_inlinks() {
        expression: attribute(inlinks).count
    }
```

In the results, observe that no document has a _rankingExpression(num_inlinks)_ less than or equal to 10.0,
meaning all such documents were purged in the first ranking phase due to the `rank-score-drop-limit`.
Normally, the `rank-score-drop-limit` is not used, as the `keep-rank-count` is most important.
Read more in the [reference](reference/schema-reference.html#rank-score-drop-limit).

For a dynamic limit, pass a ranking feature like `query(threshold)`
and use an `if` statement to check if the score is above the threshold or not -
if below, assign -1 (something lower than the `rank-score-drop-limit`) and have it dropped.
Read more in [ranking expressions](ranking-expressions-features.html#the-if-function-and-string-equality-tests).

Two-phased ranking is a performance optimization - this guide is about functionality,
so the rest of the examples will only be using one ranking phase.
Read more in [first-phase](reference/schema-reference.html#firstphase-rank).



## Retrieval: AND, OR, weakAnd
This guide will not go deep in query operators in the retrieval phase,
see [query-api](query-api.html) for details.

<pre style="display:none" data-test="exec" data-test-assert-contains="semantic-qa-retrieval.html">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20(default%20contains%20%22vespa%22%20AND%20default%20contains%20%22documents%22%20AND%20default%20contains%20%22about%22%20AND%20default%20contains%20%22ranking%22%20AND%20default%20contains%20%22and%22%20AND%20default%20contains%20%22retrieval%22)'
</pre>
<pre style="display:none" data-test="exec" data-test-assert-contains="semantic-qa-retrieval.html">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20(default%20contains%20%22vespa%22%20OR%20default%20contains%20%22documents%22%20OR%20default%20contains%20%22about%22%20OR%20default%20contains%20%22ranking%22%20OR%20default%20contains%20%22and%22%20OR%20default%20contains%20%22retrieval%22)'
</pre>
Consider a query like _"vespa documents about ranking and retrieval"_.
A query AND-ing these terms hits less than 3% of the document corpus,
missing some of the documents about ranking and retrieval:

{% include query.html content=
"[select * from doc where (default contains \"vespa\" AND default contains \"documents\" AND default contains \"about\" AND default contains \"ranking\" AND default contains \"and\" AND default contains \"retrieval\")](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20(default%20contains%20%22vespa%22%20AND%20default%20contains%20%22documents%22%20AND%20default%20contains%20%22about%22%20AND%20default%20contains%20%22ranking%22%20AND%20default%20contains%20%22and%22%20AND%20default%20contains%20%22retrieval%22))"%}

Alternatively, OR-ing the terms hits more than 95% of the documents,
unable to filter out irrelevant documents in the retrieval phase:

{% include query.html content=
"[select * from doc where (default contains \"vespa\" OR default contains \"documents\" OR default contains \"about\" OR default contains \"ranking\" OR default contains \"and\" OR default contains \"retrieval\")](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20(default%20contains%20%22vespa%22%20OR%20default%20contains%20%22documents%22%20OR%20default%20contains%20%22about%22%20OR%20default%20contains%20%22ranking%22%20OR%20default%20contains%20%22and%22%20OR%20default%20contains%20%22retrieval%22))"%}

Using a "weak AND" can address the problems of too few (AND) or too many (OR) hits in the retrieval phase.
Think of it as an _optimized OR_, where the least relevant candidates are discarded from further evaluation.
To find the least relevant candidates, a simple scoring function is used:

    rank_score = sum_n(term(n).significance * term(n).weight)

As the point of [weakAnd](reference/query-language-reference.html#weakand) is to early discard the worst candidates,
_totalCount_ is an approximation:

<pre style="display:none" data-test="exec" data-test-assert-contains="semantic-qa-retrieval.html">
curl -s 'https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20%5B%7B%22scoreThreshold%22%3A0%2C%22targetHits%22%3A10%7D%5D%0AweakAnd(default%20contains%20%22vespa%22,default%20contains%20%22documents%22,default%20contains%20%22about%22,default%20contains%20%22ranking%22,default%20contains%20%22and%22,default%20contains%20%22retrieval%22)'
</pre>

{% include query.html content=
"[select * from doc where {scoreThreshold: 0, targetHits: 10}weakAnd(default contains \"vespa\", default contains \"documents\", default contains \"about\", default contains \"ranking\", default contains \"and\", default contains \"retrieval\")](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20%5B%7B%22scoreThreshold%22%3A0%2C%22targetHits%22%3A10%7D%5D%0AweakAnd(default%20contains%20%22vespa%22,default%20contains%20%22documents%22,default%20contains%20%22about%22,default%20contains%20%22ranking%22,default%20contains%20%22and%22,default%20contains%20%22retrieval%22))"%}

Note that this blurs the distinction between filtering (retrieval) and ranking a little -
here the `weakAnd` does <span style="text-decoration: underline">both</span> filtering and ranking
to optimize the number of candidates for the later rank phases.
The default rank-profile is used:
```
rank-profile documentation inherits default {
    inputs {
        query(titleWeight): 2.0
        query(contentsWeight): 1.0
    }
    first-phase {
        expression: query(titleWeight) * bm25(title) + query(contentsWeight) * bm25(content)
    }
}
```
Observe we are here using text matching rank features,
which fits well with weakAnd's scoring function that also uses text matching features.

Read more in [using weakAnd with Vespa](using-wand-with-vespa.html).

<!--
ToDo, next steps:
* look at retrieval, start easy with AND, then OR
* OR degenerates quickly to _all_ documents, so describe WAND in layman terms
* describe when rank features are calculated to illustrate importance of recall phase
* from here, POST YQL for better readability
* explain, tracing ...
-->

## Next steps
* Read more about custom re-ranking of the final result set in
  [reranking in searcher](reranking-in-searcher.html).
