---
# Copyright Vespa.ai. All rights reserved.
title: "String Segment Match"
---

The **string segment match** algorithm computes a set of metrics -
the **string segment match metrics** - intended to capture all the
information about how well a *query* string matches a
*field* string, which is useful for document ranking in search,
from the limited information usually available during matching in search engines.

The algorithm works by locating *segments*, which are local
regions in the field which contain one or more adjacent terms of the
query. All segment start points in the field are explored, and the
ones which produce the best overall segmentation are
chosen. Informally, a segmentation is good if it contains few segments
with the query matches close together. Example:

![String segment match example](/assets/img/relevance/segment-example.png)

Here two segments are found to cover the query. An alternative second
segment is also found, but is discarded because it has inferior query
term proximity. The other lone "Bush" instance is never considered
because there is no segmentation causing "Bush" to be a segment start
token (i.e. there is no lone "George").

A subset of the metrics are computed from the tokens *within*
located segments, while another subset of metrics characterizes the
number and placement of the segments themselves. This allows the
metrics to reflect the property of natural language that tokens which
are close are often part of the same meaning (typically as parts
of the same sentence) while somewhat more distant tokens are only weakly related.

Queries typically consists of multiple intended segments, where each
segment is continuous and in order, while the ordering between the
segments is of little significance (although the more important
segments tend to come first).

By matching the query in term order
to the best and fewest segments of the field, this algorithm makes use
of the available field data to discover the likely query segmentation
from the evidence. Explicit segmentation information can also be used
in the form of connectivity scores which influences the segment scores
and thus the chosen segments.

## Source information

The information used by this algorithm to calculate these metrics is
(the last three are optional):
* The position of each occurrence of a *matched* term in the query and field* The number of terms in the query and field* A number per query term indicating the weight (importance) of each query term* A number per query term indicating the relative frequency of the term* A number per adjacent query term pair indicating the linguistic connectivity between the terms

## Algorithm

The algorithm locates segments from a given start query term as follows:

```
i = the position of the first query term
j = the position of the first match of the query term at i
while (i < query.length) {
    nextJ = the first location of query term i+1 at most proximityLimit steps to the right of j
    if (nextJ not found)
        nextJ = the first location query term i+1 at most proximityLimit steps to the left backwards of j

    if (nextJ is found) { // Find next token in this segment
        i = i+1
        j = nextJ
    }
    else {
        nextJ = the first location of query term i+1 at any location to the right forwards from j
        if (nextJ not found)
            nextJ = the first location of query term i+1 at any location to the left backwards from j
        if (nextJ not found) { // Skip a non-existing query term
        	i = i+1
        }
        else { // End of segment
            return i,j as the segment end
        }
    }
}
```

So a segment is a set of terms in the field which corresponds to an adjacent subsection of query
terms where the gap between any adjacent query term in the field is at most `proximityLimit`
forwards or backwards, and where query terms not present in the field are ignored.

Let's call the field term search order used above the *semantic distance* between two field position.
So, for example
* the semantic distance between j and nextJ is n if nextJ is located n places after j and n<`proximityLimit`
* the semantic distance between j and nextJ is `proximityLimit`+n if nextJ is located n places to the *left* of j and n<`proximityLimit`

The algorithm explores tokens and segments in the semantic distance space.
The algorithm works with any definition of semantic distance.
The algorithm will record for each segment start point:
* metrics - The current best known metrics of the combined segments up to this point
* previousJ - The end j of the previous segment in the field (if any)
* i - the query term i which is the start of this segment
* semanticDistanceExplored - the distance from previousJ explored so far
* open - whether there are possibly more j's to find beyond semanticDistanceExplored

With this, we can list the high level pseudocode of the algorithm:

```
currentSegment=a segment start point at starting at i=0 (the start of the query)
while (there are open segment start points) {
    newSegment=find the next segment, at currentSegment.i with semanticDistance > currentsegment.semanticDistance
    if (no newSegment) {
        currentSegment.open = false
        continue;
    }
    SegmentStartPoint existingStartPoint=find stored segment at start point newSegment.i+1
    if (no existingStartPoint) {
        create and store a new (empty open) segment start point at newSegment.i+1
    }
    else {
        if (newSegment.score > existingStartPoint.score) {
            existingStartPoint.metrics.score = newSegment.metrics.score
            existingStartPoint.previousJ = newSegment.endJ
            existingStartPoint.semanticDistanceExplored = newSegment.semanticDistance+1
        }
    }
    currentSegment=the next open start point (in the order they are found)
}
finalMetrics=metrics of segmentStartPoint at query.length
```

The `metric.score` deciding which of two segmentation paths is best
is `absoluteProximity/segments^2`.
Any combination of metrics which can be calculated for a partial segmentation may be used.

Browse the
[code](https://github.com/vespa-engine/vespa/tree/master/searchlib/src/main/java/com/yahoo/searchlib/ranking/features) for details.

## Complexity

The algorithm uses a linear programming technique to avoid recomputing earlier segments.
A constant amount of data is stored per possible segment start point.
Since there are at most as many start points as there are query terms,
the memory complexity is `O(query.length)`.
As the algorithm will try all possible segment starting points (up to a limit),
and there are at most one starting point per query term,
the time complexity is `O(query.length*total number of term occurrences)`.
The average time complexity is `O(average segment length/average number of term occurrences)`.

## Metric set

The complete string segment match metrics set, computed by this algorithm, is:
* match
* proximity
* completeness
* queryCompleteness
* fieldCompleteness
* orderness
* relatedness
* earliness
* longestSequenceRatio
* segmentProximity
* unweightedProximity
* absoluteProximity
* occurrence
* absoluteOccurrence
* weightedOccurrence
* weightedAbsoluteOccurrence
* significantOccurrence
* weight
* significance
* importance
* segments
* matches
* outOfOrder
* gaps
* gapLength
* longestSequence
* head
* tail
* segmentDistance

These are documented as the features prefixed by
`fieldMatch(name)`, see the
[rank features reference](rank-features.html#field-match-features-normalized).

The metric set contains both low level, un-normalized metrics corresponding directly to a concept in
the string segment match algorithm (e.g `segments`, `gaps`), normalized basic features
(e.g. `proximity`, `queryCompleteness`), normalized metrics combining lower level
metrics into some useful part of the truth (e.g. `completeness`, `orderness`)
as well as a metric combining most of the others into one normalized value (`match`).
Applications will choose the subset of the metrics which captures the properties they determine
is important, at the granularity which is convenient.

## Configuration parameters

The algorithm has the following configuration parameters, where the three first are fundamental
parameters of the algorithm, and the others are used to normalize or combine certain features.
Configure using [rank feature configuration](rank-feature-configuration.html):

| Parameter Default Description | | |
| --- | --- | --- |
| `proximityLimit` 10 The maximum allowed gap within a segment. | | |
| `proximityTable` 1/(2^(i/2)/3) for i in 9..0 followed by 1/2^(i/2) for i in 0..10 The proximity table deciding the importance of separations of various distances, The table must have size proximityLimit*2+1, where the first half is for reverse direction distances. The table must only contain values between 0 and 1, where 1 is "perfect" and 0 is "worst". | | |
| `maxAlternativeSegmentations` 10000 The maximum number of *alternative* segmentations allowed in addition to the first one found. This will prefer to not consider iterations on segments that are far out in the field, and which starts late in the query. | | |
| `maxOccurrences` 100 The number of occurrences the number of occurrences of each word is normalized against. This should be set as the number above which additional occurrences of the term has no real significance. | | |
| `proximityCompletenessImportance` 0.9 A number between 0 and 1 which determines the importance of field completeness in relation to query completeness in the `match` and `completeness` metrics. | | |
| `relatednessImportance` 0.9 The normalized importance of relatedness used in the `match` metric. | | |
| `earlinessImportance` 0.05 The importance of the match occurring early in the query, relative to segmentProximityImportance, occurrenceImportance and proximityCompletenessImportance in the `match` metric. | | |
| `segmentProximityImportance` 0.05 The importance of multiple segments being close to each other, relative to earlinessImportance, occurrenceImportance and proximityCompletenessImportance in the `match` metric. | | |
| `occurrenceImportance` 0.05 The importance of having many occurrences of the query terms, relative to earlinessImportance, segmentProximityImportance and proximityCompletenessImportance in the `match` metric. | | |
| `fieldCompletenessImportance` 0.05 A number between 0 and 1 which determines the importance of field completeness in relation to query completeness in the `match` and `completeness` metrics. | | |
