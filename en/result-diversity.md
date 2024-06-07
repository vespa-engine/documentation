---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Contributing to Vespa"
redirect_from:
- /documentation/contributing.html
---

In Search and Recommendation applications, the highest-ranking documents are displayed to the user.
A document’s rank score is computed by a function over rank features.
The score is computed per document, independently of other documents’ scores
(except when using certain features in global-phase).

This greedy approach gives the best overall result when documents are sufficiently dissimilar,
but if no it might look like this:

![Result diversity example](/assets/img/diversity-1.png)

This can be improved by preferring some less similar documents even though they produce a lower individual rank score,
which can usually be done by using the value of a field to create variation - like a domain field in the example above.

Vespa has a set of features that can be used to create diversity,
this guide outlines strategies and tradeoffs to create good-looking result sets.



## Diversity
You can use the diversity element in the schema definition to filter out non-diverse results before second-phase ranking
(and during match-phase if used):

The attribute value is the name of the attribute field that holds the value to diversify over (think of the domain in the example above)
Min-groups is the minimum number of different values of that attribute that should be included in the result set (when available).

Example:

