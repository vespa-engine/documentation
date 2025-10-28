---
# Copyright Vespa.ai. All rights reserved.
title: "Multivalue Query Operators"
---

This article is a followup to the [ranking introduction](ranking.html).
Some use cases in this guide are better solved using [tensors](tensor-user-guide.html).

## dotProduct and wand
*wand* (aka Parallel Wand) is a search operator that can be used for efficient top-k retrieval.
It implements the *Weak AND/Weighted AND* algorithm as described by Broder et al. in
[Efficient query evaluation using a two-level retrieval process](https://dl.acm.org/doi/10.1145/956863.956944).
See [using Wand with Vespa](using-wand-with-vespa.html) for details.
*dotProduct* is the brute force equivalent to *wand*.
They are both used to search for documents
where weighted tokens in a field matches a subset of weighted tokens in the query.
The [raw scores](#raw-scores-and-query-item-labeling) produced by
*dotProduct* are equivalent to those produced by *wand*.

The difference is that *wand* will perform local optimizations
in order to retrieve the top-k targetHits results that would be returned by inner maximum *dotproduct*.
Which one of these are most cost-efficient is complex as it depends on the size of the vocabulary (features) and:
* Number of query terms and their weight distribution
* Number of document terms and their weight distribution

It is easy to compare the two approaches. One can run benchmarks using either and compare latency and total number of hits, if on average,
total number of hits approaches the total number of documents matching the other filters in the query, it is cheaper
to use tensor dot product.

## dotProduct example

Refer to the [dotProduct](reference/query-language-reference.html#dotproduct) reference.
*dotProduct* calculates the dot product of a weighted set in the query and a weighted set in a field -
and stores the result in [raw scores](#raw-scores-and-query-item-labeling),
which is used in ranking expressions.

Use a weighted set field (use [attribute](attributes.html) with *fast-search* for higher performance)
in the document to store the tokens:

```
field features type weightedset<string> {
    indexing: summary | attribute
    attribute: fast-search
}
```

The query needs to be prepared by a custom searcher or sent
using [YQL](reference/query-language-reference.html#dotproduct).
The code below shows the relevant part.
If using multiple dot products in the same query it is a good idea to label them.
This enables us to use individual dot product scores when ranking results later.

```
Item makeDotProduct(String label, String field, Map<String, Integer> token_map) {
    DotProductItem item = new DotProductItem(field);
    item.setLabel(label);
    for (Map.Entry<String, Integer> entry : token_map.entrySet()) {
        item.addToken(entry.getKey(), entry.getValue());
    }
    return item;
}
```
*dotProduct* produces
[raw scores](#raw-scores-and-query-item-labeling)
that can be used in a ranking expression.
The simplest approach is to use the sum of all raw scores for the field containing the tokens:

```
rank-profile default {
    first-phase {
        expression: rawScore(features)
    }
}
```

For better control, label each dot product in the query and use their scores individually:

```
rank-profile default {
    first-phase {
        expression: itemRawScore(dp1) + itemRawScore(dp2)
    }
}
```

## IN operator example

Refer to the [in operator](reference/query-language-reference.html#in) reference.
The use cases for the *in* operator are for limiting the search result
to documents with specific properties that can have a large number of distinct values, like:
* We know who the user is, and want to restrict to documents
  written by one of the user's friends
* We have the topic area the user is interested in, and want to
  restrict to the top-ranked authors for this topic
* We have recorded the documents that have been clicked by users
  in the last 10 minutes, and want to search only in these

Using the *in* operator is more performant than a big OR expression:

```
select * from data where category in ('cat1', 'cat2', 'cat3')
select * from data where category = 'cat1' OR category = 'cat2' OR category = 'cat3' ...
```

See [multi-lookup set filtering](performance/feature-tuning.html#multi-lookup-set-filtering) for details.

Note that in most actual use cases,
the field we are searching in is some sort of user ID, topic ID, group ID, or document ID
and can often be modeled as a number -
usually in a field of type `long`
(or `array<long>` if multiple values are needed).
If a string field is used, it will usually also be some sort of ID;
if you have data in a string field intended for searching with the *in* operator,
then using `match: word` (default for attribute string fields) is recommended.

The following example shows how to use the *in* operator
programmatically in a [Java Searcher](searcher-development.html)
to search a category field:

```
field category type string {
    indexing: attribute | summary
    attribute: fast-search
    rank: filter
}
```

The Searcher will typically do the following:
* Create a new `StringInItem` (or `NumericInIterm`) for the field you want to use as filter.
* Find the tokens to insert into the query item.
* Combine the new `StringInItem` with the original query by using an `AndItem`.

A simple code example adding a hardcoded filter containing 10 tokens:

```
private Result hardCoded(Query query, Execution execution) {
    var filter = new StringInItem("category");
    filter.addToken("magazine1");
    filter.addToken("magazine2");
    filter.addToken("magazine3");
    filter.addToken("tv");
    filter.addToken("tabloid1");
    filter.addToken("tabloid2");
    filter.addToken("tabloid3");
    filter.addToken("tabloid4");
    filter.addToken("tabloid5");
    filter.addToken("tabloid6");
    var tree = query.getModel().getQueryTree();
    var oldRoot = tree.getRoot();
    var newRoot = new AndItem();
    newRoot.addItem(oldRoot);
    newRoot.addItem(filter);
    tree.setRoot(newRoot);
    query.trace("MyCustomFilterSearcher added hardcoded filter: ", true, 2);
    return execution.search(query);
}
```

The biggest challenge here is finding the tokens to insert;
normally the incoming search request URL might not contain all the tokens directly.
For example, the search request could contain the user id,
and a lookup (in a database or a Vespa index) would fetch the relevant categories for this user.

Refer to javadoc for more details:
[NumericInItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/NumericInItem.html) and
[StringInItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/StringInItem.html).

## Pin results example

To pin a result to a fixed position, use a tiered ranking function.
This means, define a range in ranking scores for the pinned queries, and rank the organic results below.
(It is *possible* to mix organic/pinned, to keep the example below simple, these are separate ranges)

First, define the key for the query - the key is the ID used to pin results.
How to define the key is user defined,
a simple way is to hash the query string, like:

```
$ md5 -q -s "65 inch tv set"
```

As a document can be pinned for multiple queries,
use a [weightedset](/en/reference/schema-reference.html#weightedset)
to store multiple key/position entries:

```
field pinned_query_position type weightedset<string> {
    indexing: index | summary
}
```

In this set, we will map from key to a value -
the value (*elementWeight*) will be used in a ranking profile for position.
In this example, the "organic" ranking is a closeness function:

```
rank-profile semantic_pin inherits default {
    inputs {
        query(query_embedding) tensor<float>(x[384])
    }

    function pin_topten(fieldname) {
        expression {
            if (elementCompleteness(fieldname).elementWeight > 0,
                11-elementCompleteness(fieldname).elementWeight, 0)
        }
    }

    first-phase {
        expression {
            # restrict the "organic" ranking contribution to [0-1>, add top ten contributions
            min(closeness(field, doc_embedding), 0.99999) +
            pin_topten(pinned_query_position)
        }
    }

    match-features {
        # Use match-features to easily debug ranking
        closeness(field, doc_embedding)
        elementCompleteness(pinned_query_position).elementWeight
    }
}
```

In short, we cap the organic range to 0-1, and add more to the ranking the higher the pinned position (11-pos).
Add an OR-term that adds the rank contribution from matching in the weighted set `pinned_query_position`:

```
$ vespa query 'select * from items where true
    or rank (pinned_query_position contains "af6f44472a1d3b00d40d04309067b739")' \
  ranking=semantic_pin
```

Above, a `true` statement is used for simplicity, replace this with the real query.

A sample document, with query keys and positions -
here, a document is pinned for two queries:

```
{% highlight json%}
[
    {
        "put": "id:mynamespace:items::1",
        "fields": {
            "pinned_query_position": {
                "af6f44472a1d3b00d40d04309067b739": 1,
                "fe5e6fc6358aa1c59b8838852040bfb4": 2
            }
        }
    }
]
{% endhighlight %}
```

Snippet from a sample query result:

```
{% highlight json %}
{
    "id": "id:mynamespace:items::1",
    "relevance": 10.0,
    "source": "items",
    "fields": {
        "matchfeatures": {
            "closeness(field,doc_embedding)": 0.0,
            "elementCompleteness(pinned_query_position).elementWeight": 1.0
        },
        "sddocname": "items",
        "documentid": "id:mynamespace:items::1",
        "pinned_query_position": {
            "fe5e6fc6358aa1c59b8838852040bfb4": 2,
            "af6f44472a1d3b00d40d04309067b739": 1
        }
    }
}
{% endhighlight %}
```

Observe how a pinned result for position 1 gets a 10 relevance (rank) score.

## Raw scores and query item labeling

Vespa ranking is flexible and relatively decoupled from document matching.
The output from the matching pipeline typically indicates
how the different words in the query matches a specific document
and lets the ranking framework figure out how this translates to match quality.

However, some of the more complex match operators will produce scores directly,
rather than expose underlying match information.
A good example is the *wand* operator.
During ranking, a wand will look like a single word that has no detailed match information,
but rather a numeric score attached to it.
This is called a *raw score*,
and can be included in ranking expressions using the `rawScore` feature.

The `rawScore` feature takes a field name as parameter
and gives the sum of all raw scores produced by the query for that field.
If more fine-grained control is needed
(the query contains multiple operators producing raw scores for the same field,
but we want to handle those scores separately in the ranking expression),
the `itemRawScore` feature may be used.
This feature takes a query item *label* as parameter
and gives the raw score produced by that item only.

Query item labeling is a generic mechanism that can be used to attach symbolic names to query items.
A query item is labeled by using the `setLabel` method on a query item
in the search container query API.
