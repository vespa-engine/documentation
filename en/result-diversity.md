---
# Copyright Vespa.ai. All rights reserved.
title: "Result Diversity"
---

In Search and Recommendation applications, the highest-ranking documents are displayed to the user.
A document’s rank score is computed by a function over rank features.
The score is computed per document, independently of other documents’ scores
(except when using certain features in global-phase).

This greedy approach gives the best overall result when documents are sufficiently dissimilar,
but if not it might look like this:

![Result diversity example](/assets/img/diversity-1.png)

This can be improved by preferring some less similar documents even though they produce a lower individual rank score,
which can usually be done by using the value of a field to create variation - like a domain field in the example above.

Vespa has a set of features that can be used to create diversity,
this guide outlines strategies and tradeoffs to create good-looking result sets.



## Diversity
You can use the [diversity](/en/reference/schema-reference.html#diversity) element in the schema definition
to filter out non-diverse results before second-phase ranking (and during match-phase if used):

* The [attribute](/en/reference/schema-reference.html#diversity-attribute) value is the name of the attribute field
  that holds the value to diversify over (think of the domain in the example above).
* [min-groups](/en/reference/schema-reference.html#diversity-min-groups) is the minimum number of different values
  of that attribute that should be included in the result set (when available).

Example:

```
field domain type string {
    indexing: attribute | summary
}

rank-profile diverse_example {

    first-phase {
        expression: ...
    }

    diversity {
        attribute: domain
        min-groups: 10
    }

    second-phase {
        expression: ...
    }

}
```



## Grouping
Grouping is a general feature for organizing and aggregating in results, which can be used for diversification.
Grouping is specified at query time, so no rank-profile configuration is required.
For example, to get the highest ranking result per domain with grouping, use:

    all( group(domain) max(1) each( output(summary() ) ) )

With grouping, you have more accurate control over the behavior,
such as being able to specify the number of items per group.
You can also hierarchically group on multiple attributes, aggregate values etc.

The grouping result structure comes in addition to (or instead of) the regular query results,
so enabling diversity using grouping will change the rendered result structure
(unless you flatten the grouped results in a Searcher before returning).

Grouping runs on the results after second-phase ranking, and across all nodes.
Generally, this approach uses more resources compared to using the diversity element to filter out results after first-phase,
and means the second phase will be used to pick the best result also in each group (which gives better relevance at higher cost).



## Match-phase diversity
Diversity above runs over the result after first-phase ranking.

The [match-phase](/en/reference/schema-reference.html#match-phase) feature lets you increase performance
by limiting hits exposed to first-phase ranking to the highest (lowest) values of some attribute.
Adding the diversity element when using match-phase means that the diversity field attribute
is also used to produce the set of matches returned from the match-phase attribute.

```
field popularity type int {
    indexing: attribute | summary
}

field domain type string {
    indexing: attribute | summary
}

rank-profile diverse_example {

    match-phase {
        attribute: popularity
        max-hits: 100
        max-filter-coverage: 1.0
    }

    diversity {
        attribute: domain
        min-groups: 10
    }

    first-phase {
        expression: attribute(popularity)
    }
}
```



## Collapsefield
The final processing before returning a result happens in a container node -
refer to [query execution](/en/query-api.html#query-execution) for details.

Setting the [collapsefield](/en/reference/query-api-reference.html#collapsefield) parameter
lets you filter out hits which have the same value for one or more fields as a higher-ranked hit.

Using collapsefield is a cheap option when results only contains a small number of duplicates on average,
since it defers all diversification work until the end.
When there may be many duplicates, using either the diversify tag or grouping should be preferred.
