---
# Copyright Vespa.ai. All rights reserved.
title: "Ranking Expressions and Features"
---

Read the [ranking introduction](ranking.html) first.
This guide is about [ranking expressions](reference/ranking-expressions.html)
and [rank features](reference/rank-features.html), find guides and examples below.

## Ranking expressions

Vespa uses [ranking expressions](reference/ranking-expressions.html)
to rank documents matching a query, computing a rank score per document.
A ranking expression is stored in a *rank profile*.

Ranking expressions are mathematical functions.
The function may contain anything from a single reference to a built-in feature to a machine-learned model.
Ranking expressions support the usual operators and functions,
as well as an *if* function - enabling decision trees and conditional business logic.
They support a comprehensive set of [tensor functions](reference/tensor.html),
which allows expressing machine-learned functions such as deep neural nets.
Refer to [multivalue query operators](multivalue-query-operators.html)
for details on using dot products, tensors and wand.

Ranking is most often the resource driver - this is where is application's logic is implemented.
Use [two-phase ranking](phased-ranking.html) to optimize,
using an inexpensive *first-phase* ranking to eliminate the lowest ranked candidates,
then focus the resources on a strong *second-phase* ranking.

Ranking expressions can be *handwritten* -
works well if the ranking is well-defined enough to be easily mappable into a ranking expression.
Alternatively, make the ranking expression automatically using *machine learning*.
Ranking expressions can be large, and can be imported using
[file:filename](reference/schema-reference.html#expression).

## Rank features

The primitive values used in ranking expressions
are called [rank features](reference/rank-features.html).
Rank features can be [tensors](tensor-user-guide.html),
[multivalue fields](schemas.html#field) or scalars, and one of:
* Constants set in the application package
* Values sent with the query or set in the document
* Computed by Vespa from the query and the document
  to provide information about how well the query matched the document

Vespa's [rank feature set](reference/rank-features.html)
contains a large set of low level features, as well as some higher level features.
If automated training is used, all features can often just be handed to the training algorithm
to let it choose which ones to use.
Depending on the algorithm, it can be a good idea to leave out the un-normalized features
to avoid spending learning power on having to learn to normalize these features
and determine that they really represent the same information as some of the normalized features.

Include [default rank features](https://github.com/vespa-engine/system-test/blob/master/tests/search/rankfeatures/dump.txt)
in query results by adding
[ranking.listFeatures](reference/query-api-reference.html#ranking.listfeatures) to the query.
This is useful for tasks like recording the rank feature values for automated training -
learn more in the [tutorial](tutorials/text-search-ml.html).
If more rank features than is available in the default set is wanted,
they can be added to the set in the [rank profile](reference/schema-reference.html#rank-features):

```
rank-features: feature1 feature2 …
```

It is also possible to control which features to dump - add this to the rank profile:

```
ignore-default-rank-features
```

This will make the explicitly listed rank features the only ones dumped when requesting rankfeatures in the query.

### Normalization

The rank features provided includes both features normalized to the range 0-1,
and un-normalized features like counts and positions.
Whenever possible, prefer the normalized features.
They capture the same information (and more),
but are easier to use because they can be combined more easily with other features.
In addition, try to write ranking expressions such that the combined rank score is also normalized,
for example by taking averages not sums.
The resulting normalized rank scores makes it possible to implement relevance based blending,
search assistance triggering when there are no good hits, and so on.

### Configuration

Some features, most notably the [fieldMatch](reference/rank-features.html#field-match-features-normalized) features,
have configuration parameters that enables the feature calculation to be tweaked per field for performance or relevance.
Feature configuration values are set by adding to the rank profile:

```
rank-properties {
    featureName.configurationProperty: "value"
}
```

The values are set per field, like:

```
rank-properties {
    fieldMatch(title).maxAlternativeSegmentations: 10
    fieldMatch(title).maxOccurrences: 5
    fieldMatch(description).maxOccurrences: 20
}
```

Refer to the
[rank feature configuration](reference/rank-feature-configuration.html) reference.

### Feature contribution functions

Vespa ranking features are linear.
For example, the [earliness](reference/rank-features.html#fieldMatch(name).earliness) feature
is 0 if the match is at the end of the field,
1 if the match is at the start of the field,
and 0.5 if the match is exactly in the middle of the field.
In many cases, the contribution of a feature should not be linear with its "goodness".
For example, *earliness* could decay quickly in the beginning and slowly at the end of the field.
This from the intuition that it matters more if the match is of the first or the twentieth word in the field,
but it doesn't matter as much if the match is at the thousands or thousand-and-twentieths.

To achieve this, pass the feature value through a function
which turns the line into a curve matching the intent.
This is easiest with normalized fields.
The function begins and ends in the same point, f(0)=0 and f(1)=1, but which curves in between.
To get the effect described above, a curve which starts almost flat and ends steep works - example:

```
pow(0-x,2)
```

The second number decides how pronounced the curving is.
A larger number will make changes to higher x values even more important
relative to the same change to lower x values.

### Dumping rank features for specific documents

For a training set containing judgements for certain documents,
it is useful to select those documents in the query by adding a term matching the document id,
but without impacting the values of any rank features.
To do this, add that term with [ranked](reference/query-language-reference.html#ranked) set to false:

```
select * from mydocumenttype where myidfield contains ({ranked: false}"mydocumentid" and ...)
```

### Accessing feature/function values in results

Any feature can be returned in the hit producing it by adding it to the list of
[summary-features](reference/schema-reference.html#summary-features) of the rank profile.
As all functions are features this allows the result of any computation to be accessible in results. Example:

```
rank-profile test {

    summary-features: tensor_join join_sum

    function tensor_join() {
        expression: attribute(my_tensor_field) * query(my_query_tensor)
    }

    function join_sum() {
        expression: sum(tensor_join())
    }

}
```

The results of these functions will be available in the Hits of the result as follows:

```
{% highlight java %}
import com.yahoo.search.result.FeatureData;

    FeatureData featureData = (FeatureData)hit.getField("summaryfeatures");
    Tensor tensor_join_value = featureData.getTensor("rankingExpression(tensor_join)");
    double join_sum_value = featureData.getDouble("rankingExpression(join_sum)");
{% endhighlight %}
```

Do further computation on the returned tensors,
such as e.g `Tensor larger = tensor_join_value.map((value) -> 3 * value)`.

If also leveraging [multiphase searching](searcher-development.html#multiphase-searching),
it is possible to get rank features returned in the first phase using
[match-features](reference/schema-reference.html#match-features).
This pre-populates the [matchfeatures](reference/default-result-format.html#matchfeatures) field.
The effects which can be observed in the results are the same, so this may seem like the same functionality,
but the performance trade-off is different:
* The expressions in *match-features* must be computed for all hits returned
  in the first phase, before selecting which hits to *fill*. But that also means it's
  possible to use the `matchfeatures` field to select which hits to keep and which to
  remove before calling `fill()` at all.
* The expressions in *summary-features* are not available before the *fill* phase,
  but only need to be calculated for those hits that are actually filled.

The difference is most pronounced when the corpus is divided onto many content nodes.
Consider a case with 7 content nodes, fetching 100 matches from each.
These are merged (by relevance score) into a list of 700 hits,
and the 100 with the best relevance are selected and *filled*.
If you use *match-features*, they need to be calculated for all 700 hits.
Compare with *summary-features*, where only the final 100 hits need to be considered for calculating those.

## The "if" function and string equality tests

`if` can be used for other purposes than encoding MLR trained decision trees.
One use is to choose different ranking functions for different types of documents in the same search.
Ranking expressions are able to do string equality tests,
so to choose between different ranking sub-functions based on the value of a string attribute (say, "category"),
use an expression like:

```
if (attribute(category)=="restaurant",…restaurant function, if (attribute(category)=="hotel",…hotel function, …))
```

This method is also used automatically when multiple schemas are deployed to the same cluster,
and all is included in the same query to choose the ranking expression from the correct schema for each document.

By using `if` functions, one can also implement strict tiering,
ensuring that documents having some criterion always gets a higher score than the other documents. Example:

```
if (fieldMatch(business).fieldCompleteness==1, 0.8+document.distance*0.2,
                                               if (attribute(category)=="shop", 0.6+fieldMatch(title)*0.2,
                                                                                 match*attribute(popularity)*0.6 )
```

This function puts all exact matches on business names first,
sorted by geographical distance, followed by all shops sorted by title match,
followed by everything else sorted by the overall match quality and popularity.

Also see [pin results](/en/multivalue-query-operators.html#pin-results-example)
for a comprehensive examples of using a tiered ranking function to pin queries and results.

## Using constants

Ranking expressions can refer to constants defined in a `constants` clause:

```
first-phase {
    expression: myConst1 + myConst2
}
constants {
    myConst1: 1.5
    myConst2: 2.5
    ...
}
```

Constants lists are inherited and can be overridden in sub-profiles.
This is useful to create a set of rank profiles that use the same broad ranking
but differs by constants values.

For performance, always prefer constants to query variables (see below)
whenever the constant values to use can be enumerated in a set of rank profiles.
Constants are applied to ranking expressions at configuration time,
and the resulting constant parts of expressions calculated,
which may lead to reduced execution cost, especially with tensor constants.

## Using query variables

As ranking expressions can refer to any feature by name,
one can use [query features](reference/rank-features.html#feature-list) as ranking variables.
These variables can be used for example to allow the query
to specify the degree of importance to various parts of a ranking expression,
or to quickly search large parameter spaces to find a good ranking,
by trying different values in each query.
These variables can be assigned default values in the [rank profile](reference/schema-reference.html#rank-profile)
by adding:

```
inputs {
    query(myvalue) double: 0.5
}
```

to the rank profile.
These variables can then be overridden in the query by adding:

```
input.query(myvalue)=0.1
```

to it - see the [Query API](reference/query-api-reference.html#ranking.features).

## Query feature types

The default type of all features are scalar. To use query feature *tensors* we must
[define their type in the rank profile](reference/schema-reference.html#inputs).

Without the correct tensor type, a passed query feature is handled as a string to be converted to a scalar,
which will *not give an error but will produce incorrect results*.

Tensors can be passed in requests using the [tensor literal form](reference/tensor.html#tensor-literal-form),
for example:

```
input.query(user_profile)=%7B%7Bcat%3Apop%7D%3A0.8%2C%7Bcat%3Arock%7D%3A0.2%2C%7Bcat%3Ajazz%7D%3A0.1%7D
```

However, it is usually preferable instead to create them in a [Searcher](searcher-development.html).
Set the tensor value using the
[RankFeatures](https://github.com/vespa-engine/vespa/blob/master/container-search/src/main/java/com/yahoo/search/query/ranking/RankFeatures.java) instance associated with
[Query](https://github.com/vespa-engine/vespa/blob/master/container-search/src/main/java/com/yahoo/search/Query.java) instance. This example makes a tensor with a single cell with value 500:

```
{% highlight java%}
package com.yahoo.example;

import com.yahoo.search.Query;
import com.yahoo.search.Result;
import com.yahoo.search.Searcher;
import com.yahoo.search.searchchain.Execution;
import com.yahoo.tensor.Tensor;
import com.yahoo.tensor.TensorType;

public class TensorInQuerySearcher extends Searcher {
    @Override
    public Result search(Query query, Execution execution) {
        // The Tensor type must also be in the application package as described in the above section
        query.getRanking().getFeatures().put("query(tensor_feature)",
              Tensor.Builder.of(TensorType.fromSpec("tensor(x{})")).cell().label("x", "foo").value(500).build());
        return execution.search(query);
    }
}
{% endhighlight %}
```

Refer to the [Tensor](https://javadoc.io/doc/com.yahoo.vespa/vespajlib/latest/com/yahoo/tensor/Tensor.html)
Java API for details on how to construct tensors programmatically.

## Function snippets

When using machine learned ranking, we are searching a function space
which is much more limited than the space of functions supported by ranking expressions.
We can increase the space of functions available to MLR
because the primitive features used in MLR training do not need to be primitive features in Vespa -
they can just as well be ranking expression snippets.
If there are certain mathematical combinations of features believed to be useful in an application,
these can be pre-calculated from the actual primitive features of Vespa
and given to MLR as primitives.
Such primitives can then be replaced textually by the corresponding ranking expression snippet,
before the learned expression is deployed on Vespa.

Vespa supports [expression functions](reference/schema-reference.html#function-rank).
Functions having zero arguments can be used as summary- and rank-features.
For example, the function "myfeature":

```
rank-profile myrankprofile inherits default {
    function myfeature() {
      expression: fieldMatch(title).completeness * pow(0 - fieldMatch(title).earliness, 2)
    }
}
```

becomes available as a feature as follows:

```
summary-features {
    myfeature
}
```

## Tracking relevance variations over time

Vespa comes with a few simple metrics for relevance
that enables applications to see how relevance changes over time,
either as a result of changes to how relevance is computed,
changes to query construction, changes to the content ingested,
or as a result of changing user behavior.

The relevance metrics are `relevance.at_1`,
`relevance.at_3` and `relevance.at_10`.
See [metrics](operations/metrics.html) for more information.

## Examples

If the user is underage, assign 0 to adult content
and use the average of match quality in the title field and popularity among kids.
If the user is not, use the match quality in the title field:

```
if ( query(userage) < 18,
     if ( attribute(adultness) > 0.1, 0 , (fieldMatch(title)+attribute(kidspopularity)) / 2 ),
     fieldMatch(title) )
```

Use a weighted average of the match quality in some fields,
multiplied by 1-exp of the document age:

```
( 10*fieldMatch(title) + 5*fieldMatch(description) +
  7*attributeMatch(tags).normalizedWeight ) /22 * ( 1 - age(creationtime) )
```
