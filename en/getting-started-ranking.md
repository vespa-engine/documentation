---
# Copyright Verizon Media. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Getting started with ranking"
---

Learn how [ranking](ranking.html) works in Vespa by using the open [query API](query-api.html) of
[vespa-documentation-search](https://github.com/vespa-engine/sample-apps/tree/master/vespa-cloud/vespa-documentation-search).

Ranking is the user-defined computation that scores documents to a query,
here configured in the schema [doc.sd](https://github.com/vespa-engine/sample-apps/blob/master/vespa-cloud/vespa-documentation-search/src/main/application/schemas/doc.sd),
also see [schema documentation](schemas.html).
This schema has a set of (contrived) ranking functions, to help learn Vespa ranking.

In this article, find a set of queries invoking different `rank-profiles`, which is the ranking definition.


## Ranking using document features only
Let's start with something simple: _Irrespective of the query, score documents by the number of in-links to it_.
That is, for any query, return the documents with most in-links first in the result set:

[https://doc-search.vespa.oath.cloud/search/?yql=select * from sources * where sddocname contains "doc";&ranking=inlinks](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20sources%20*%20where%20sddocname%20contains%20%22doc%22%3B&ranking=inlinks)

The score, named `relevance` in query results, is the size of the `inlinks` attribute array in the document:
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
Observe that the ranking function does not use any features from the query.



## Observing values used in ranking
When developing an application, it is useful to observe the input values to ranking.
Use [summary-features](reference/schema-reference.html#summary-features)
to output values in search results.

In this experiment, we will use another rank function, still counting in-links but scoring older documents lower:

<br/>
<p><!-- depends on mathjax -->
    $$ num\_inlinks * {decay\_const}^{doc\_age\_seconds/3600} $$
</p>

Also new is:
* use of the `now` [ranking feature](reference/rank-features.html)
* use of constants and functions to write better code

[https://doc-search.vespa.oath.cloud/search/?yql=select * from sources * where sddocname contains "doc";&ranking=inlinks_age](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20sources%20*%20where%20sddocname%20contains%20%22doc%22%3B&ranking=inlinks_age)
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
In the query results, observe a document with 27 in-links, 9703 seconds old, get at relevance at 20.32:
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
Using `summary-features` makes it easy to validate and develop the rank expression.



## Two-phased ranking, rank-profile inheritance
See [first-phase](reference/schema-reference.html#firstphase-rank).
The purpose of two-phased ranking is to use a cheap rank function to eliminate most candidates
using little resources in the first phase -
then use a precise, resource intensive function in the second phase.

[https://doc-search.vespa.oath.cloud/search/?yql=select * from sources * where sddocname contains "doc";&ranking=inlinks_twophase](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20sources%20*%20where%20sddocname%20contains%20%22doc%22%3B&ranking=inlinks_twophase)

Note how using rank-profile `inheritance` is a smart way to define functions once, then use in multiple rank-profiles:
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

In the results, observer that no document has a _rankingExpression(num_inlinks) < 10.0_,
meaning all such documents were purged in the first ranking phase due to the `rank-score-drop-limit`.

Two-phased ranking is a performance optimization - this guide is about functionality,
so the rest of the examples will only be using first-phase ranking.



## Ranking with query features
Let's assume we want to find similar documents, and we define document similarity as having the same number of words.
From most perspectives a poor similarity function, better functions are described later.

The documents have a `term_count` field - so let's add a `ranking.features.query` for term count as well:

[https://doc-search.vespa.oath.cloud/search/?yql=select * from sources * where sddocname contains "doc";&ranking=term_count_similarity&ranking.features.query(q_term_count)=1000](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20sources%20*%20where%20sddocname%20contains%20%22doc%22%3B&ranking=term_count_similarity&ranking.features.query(q_term_count)=1000)

<br/>
<p><!-- depends on mathjax -->
    $$ 1 - \frac{fabs(attribute(term\_count) - query(q\_term\_count))}{1 + attribute(term\_count) + query(q\_term\_count)} $$
</p>



```
rank-profile term_count_similarity {
    first-phase {
        expression: 1 - fabs(attribute(term_count) - query(q_term_count)) / (1 + attribute(term_count) + query(q_term_count))
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
The key learning here is how to transfer ranking values, or ranking features in the query.
Use different names for more query features.



## Ranking with a query tensor
Another similarity function can be overlap in in-links.
We will map the inlinks [weightedset](reference/schema-reference.html#type:weightedset) into a
[tensor](reference/schema-reference.html#type:tensor),
query with a tensor of same type and create a scalar using a tensor product as the rank score.
We use a [mapped](reference/tensor.html#general-literal-form) query tensor:
```
{% raw %}{{links:/en/query-profiles.html}:1,{links:/en/query-profiles.html}:1,{links:/en/query-profiles.html}:1}{% endraw %}
```
**Important:** Vespa cannot know the query tensor type from looking at it -
it must be configured using a [query profile type](ranking-expressions-features.html#query-feature-types).
Below, we use `queryProfile=links` in the query.
Explore the [configuration](https://github.com/vespa-engine/sample-apps/tree/master/vespa-cloud/vespa-documentation-search/src/main/application/search/query-profiles):
```
└── query-profiles
    ├── links.xml
    └── types
        └── links.xml
```
Pro tip: The query profile `default` is assumed if not set in the query.
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

[https://doc-search.vespa.oath.cloud/search/?yql=select * from sources * where sddocname contains "doc";&queryProfile=links&ranking=inlink_similarity&ranking.features.query(links)={% raw %}{{inlinks:/en/query-profiles.html}:1,{inlinks:/en/page-templates.html}:1,{inlinks:/en/overview.html}:1}{% endraw %}](https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20sources%20*%20where%20sddocname%20contains%20%22doc%22%3B&queryProfile=links&ranking=inlink_similarity&ranking.features.query(links)=%7B%7Blinks%3A%2Fen%2Fquery-profiles.html%7D%3A1%2C%7Blinks%3A%2Fen%2Fpage-templates.html%7D%3A1%2C%7Blinks%3A%2Fen%2Foverview.html%7D%3A1%7D)

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

Here, the tensors have one dimension and are hence vectors - the sum of the tensor product is hence the doc product.
As all values are 1, all products are 1 and the sum is 2:

<table border="2" cellpadding="6" rules="groups" frame="hsides">
<thead>
  <tr><th scope="col" class="left">document</th>
      <th scope="col" class="left">query</th>
      <th scope="col" class="left">value</th></tr>
</thead>
<tbody>
  <tr><td>/en/jdisc/container-components.html</td><td></td><td>0</td></tr>
  <tr><td></td><td>/en/overview.html</td><td>0</td></tr>
  <tr><td>/en/page-templates.html</td><td>/en/page-templates.html</td><td>1</td></tr>
  <tr><td>/en/query-profiles.html</td><td>/en/query-profiles.html</td><td>1</td></tr>
</tbody>
</table>
<br/>

Change values in query tensor to see difference in rank score, setting different weights for links.

Summary: The problem of comparing two lists of links is transformed into a numerical problem
of multiplying two occurrence vectors,  summing co-occurences and ranking by this sum:
```
sum(tensorFromWeightedSet(attribute(inlinks), links) * query(links))
```

Notes:
* Query tensors can grow large. Applications can create the tensor in code using a _Searcher_,
  see [example](ranking-expressions-features.html#query-feature-types).
