---
# Copyright Vespa.ai. All rights reserved.
title: "Rank Feature Configuration"
---

For some [rank features](rank-features.html),
it is possible to set configuration variables for how the features are calculated.
For features that are per field or attribute,
the variables are set separately per field/attribute.

## Properties

Rank Features configuration properties are set by adding the following to the rank profile:

```
rank-properties {
    <featurename>.<configuration-property>: <value>
}
```

Where *<featurename>* is the name of a feature class (feature name up to the first dot),
*<configuration-property>* is a property from the list below,
appropriate for the feature, and *<value>* is either a number of a quoted string. Example:

```
rank-profile my-profile inherits default {
  rank-properties {
    fieldMatch(title).maxAlternativeSegmentations: 10
    fieldMatch(title).maxOccurrences: 5
    bm25(title).k1: 1.5
    bm25(title).b: 0.85
    bm25(title).averageFieldLength: 200
    elementwise(bm25(content),x,float).k1: 1.4
    elementwise(bm25(content),x,float).b: 0.87
    elementwise(bm25(content),x,float).averageElementLength: 50
    elementSimilarity(tags).output.sumWeightSquared: "sum((0.35*p+0.15*o+0.30*q+0.20*f)*w^2)"
    elementSimilarity(tags).output.avgWeightSquared: "avg((0.35*p+0.15*o+0.30*q+0.20*f)*w^2)"
    elementSimilarity(tags).output.sumWeight: "sum(w)"
  }
}
```

For features missing from the list of properties below a rank property can be set with
another syntax, e.g. setting *averageFieldLength* for *my_field* for
the *nativeFieldMatch* feature can be done as:

```
  nativeFieldMatch.averageFieldLength.my_field: 512
```

Rank profiles are inherited like other content of rank profiles.

## List of properties

An incomplete list of rank properties by the feature they apply to.

| Feature | Parameter | Default | Description |
| --- | --- | --- | --- |
| term | numTerms | 5 | The number of terms for which this is included in the rank features dump in the summary |
| [bm25](rank-features.html#bm25) | k1 | 1.2 | Used to limit how much a single query term can affect the score for a document. |
| b | 0.75 | Used to control the effect of the field length compared to the average field length. |
| averageFieldLength | Automatically calculated per field per content node for [indexed search](services-content.html#document), 100 for [streaming search](../streaming-search.html). | Used to set an explicit value for the average field length (in number of words). When using [streaming search](../streaming-search.html#differences-in-streaming-search), no index structures are generated, and the average field length is not automatically calculated. Instead, manually set an average field length for a more precise BM25 score. |
| [elementwise bm25](rank-features.html#elementwise-bm25) | k1 | 1.2 | Used to limit how much a single query term can affect the score for a document. |
| b | 0.75 | Used to control the effect of the element length compared to the average element length. |
| averageElementLength | Automatically calculated per field element per content node for [indexed search](services-content.html#document), 100 for [streaming search](../streaming-search.html). | Used to set an explicit value for the average element length (in number of words). When using [streaming search](../streaming-search.html#differences-in-streaming-search), no index structures are generated and the average element length is not automatically calculated. Instead, manually set an average element length for a more precise elementwise bm25 score. It should also be manually set for multi-node indexed search to get consistent scoring across the nodes. |
| fieldMatch | proximityLimit | 10 | The maximum allowed gap within a segment. |
| proximityTable | 1/(2^(i/2)/3) for i in 9..0 followed by 1/2^(i/2) for i in 0..10 | The proximity table deciding the importance of separations of various distances, The table must have size proximityLimit*2+1, where the first half is for reverse direction distances. The table must only contain values between 0 and 1, where 1 is "perfect" and 0 is "worst". |
| maxAlternativeSegmentations | 10000 | The maximum number of *alternative* segmentations allowed in addition to the first one found. This will prefer to not consider iterations on segments that are far out in the field, and which start late in the query. |
| maxOccurrences | 100 | The number of occurrences of each word is normalized against. This should be set as the number above which additional occurrences of the term have no real significance. |
| proximityCompletenessImportance | 0.9 | A number between 0 and 1 that determines the importance of field completeness in relation to query completeness in the `match` and `completeness` metrics. |
| relatednessImportance | 0.9 | The normalized importance of relatedness used in the `match` metric. |
| earlinessImportance | 0.05 | The importance of the match occurring early in the query, relative to segmentProximityImportance, occurrenceImportance and proximityCompletenessImportance in the `match` metric. |
| segmentProximityImportance | 0.05 | The importance of multiple segments being close to each other, relative to earlinessImportance, occurrenceImportance and proximityCompletenessImportance in the `match` metric. |
| occurrenceImportance | 0.05 | The importance of having many occurrences of the query terms, relative to earlinessImportance, segmentProximityImportance and proximityCompletenessImportance in the `match` metric. |
| fieldCompletenessImportance | 0.05 | A number between 0 and 1 that determines the importance of field completeness in relation to query completeness in the `match` and `completeness` metrics. |
| fieldTermMatch | numTerms | 5 | The number of terms for which this is included in the rank features dump in the summary |
| numTerms.<fieldName> | 5 | The number of terms for which this is included in the rank features dump in the summary for the specified field |
| elementCompleteness | fieldCompletenessImportance | 0.5 | Higher values favor field completeness, lower values favor query completeness. Adjusting this parameter will also affect which element is selected as the best. |
| elementSimilarity | output.default | "max( (0.35*p + 0.15*o + 0.30*q + 0.20*f) * w)" | Describes how the default output should be calculated. The value must be on the form `aggregator(expression)`. The expression is used to combine the low-level similarity measures between the query and individual elements in the field that matched the query. The aggregator will be used to aggregate the output of the expression across matched elements. The available aggregators are `max`, `avg` and `sum`. The available expression operators are `+`, `-`, `*`, `/` and `^`. Parentheses may be used to override default operator precedence. Note that you must quote the expression using `"expression"`. Terminals can be numbers or any of the following symbols:   |  |  | | --- | --- | | **p** | normalized **proximity** measure | | **o** | normalized term **ordering** measure | | **q** | normalized **query** coverage | | **f** | normalized **field** coverage | | **w** | element **weight** | |
| output.name | N/A | Define an additional feature output called `name`. The value describes how the output should be calculated and has the same syntax as the `default` output described above. Example create a new output which can be accessed as `elementSimilarity(tags).sumW`: `elementSimilarity(tags).output.sumW: "sum(w)"` |
| attributeMatch | fieldCompletenessImportance | 0.05 | A number between 0 and 1 that determines the importance of field completeness in relation to query completeness in the `match` and `completeness` metrics. |
| maxWeight | 256 | The maximal weight when calculating `attributeMatch(<name>).normalizedWeight`. Weights higher than this will not have any effect on this feature. |
| closeness | maxDistance | 9013305.0 | The maximal distance when calculating `closeness(<name>)`. Distances higher than this will not have any effect on this feature. The default is about 1000 km (1 km is about 9013.305 microdegrees). |
| scaleDistance | 45066.525 | Basic scale for distances when calculating `closeness(<name>).logscale`. The default is about 5 km. {% include deprecated.html content="use `halfResponse` instead"%} |
| halfResponse | 593861.739 | The distance that should give an output of 0.5 when calculating `closeness(<name>).logscale`. The default is about 65.89 km (must be in the range [1, maxDistance/2>). Use this parameter to fine-tune the distance range where half of the dynamics of the logscale function will be used. |
| freshness | maxAge | 3*30*24*60*60 | The maximal age in seconds when calculating `freshness(<name>)`. Ages older than this will not have any effect on this feature. The default is about 3 months. |
| halfResponse | 7*24*60*60 | The age in seconds that should give an output of 0.5 when calculating `freshness(<name>).logscale`. The default is 7 days (must be in the range [1, maxAge/2>). Use this parameter to fine-tune the age range where half of the dynamics of the logscale function will be used. |
| random | seed | Current time in microseconds | The random seed. |
| randomNormal | seed | Current time in microseconds | The random seed for randomNormal. |
| foreach | maxTerms | 16 | Specifies how many query term indices to iterate over ([0, `maxTerms`>) when using dimension `terms`. |
