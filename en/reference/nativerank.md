---
# Copyright Vespa.ai. All rights reserved.
title: "nativeRank Reference"
---

The *nativeRank* feature produces a reasonable text ranking score which is
computed at an acceptable performance,
and is a good candidate for [first phase](../phased-ranking.html) ranking.
The *nativeRank* feature is a linear combination of the normalized scores
computed by the features *nativeFieldMatch*, *nativeProximity*,
and *nativeAttributeMatch*.
All these features are described in detail below.
See the [configuration properties](#configuration-properties)
section for how to configure the features.

## nativeFieldMatch

The *nativeFieldMatch* feature captures how well query
terms match searched index fields by looking at the number of times a
term occurs in a field and how early in the field it occurs. The
significance and weight of the terms are also taken into account such
that unusual terms give a higher rank contribution than common ones.

The score for *nativeFieldMatch* is calculated as follows:

nativeFieldMatch
=

∑
i
n

termSignificance
i
×

termWeight
i

∑
j
m

fieldWeight
j

firstOccImp
j
×

firstOccBoost

i
j
+

1
-

firstOccImp
j
×

numOccBoost

i
j

∑
i
n

termSignificance
i
×

termWeight
i

∑
j
m

fieldWeight
j
×

fmMaxTable
j
\[ nativeFieldMatch = \frac{\sum_i^ntermSignificance_i \times termWeight_i\sum_j^mfieldWeight_j(firstOccImp_j \times firstOccBoost_{ij} + (1 - firstOccImp_j) \times numOccBoost_{ij})}{\sum_i^ntermSignificance_i \times termWeight_i\sum_j^mfieldWeight_j \times fmMaxTable_j} \]

where *n* is the number of query terms searched in index fields,
*m* is the number of fields searched by query term *i*,
*firstOccImpj* is the *firstOccurrenceImportance*
for field *j*, and *firstOccBoostij*,
*numOccBoostij* and *fmMaxTablej* are given below.

firstOccBoost

i
j
=

firstOccurrenceTable
j

firstOcc

i
j
×

tableSize
j

max

6

fieldLength
j
\[ firstOccBoost_{ij} = firstOccurrenceTable_j[\frac{firstOcc_{ij} \times tableSize_j}{max(6,fieldLength_j)}] \]

where *firstOccurrenceTablej* is the boost table configured for field *j*,
typically an expdecay function (see the [boost tables](#boost-tables) section below),
*firstOccij* is the first occurrence of query term *i* in field *j*,
and *tableSizej* is the size of the boost table.

numOccBoost

i
j
=

occurrenceCountTable
j

numOccs

i
j
×

tableSize
j

max

6

fieldLength
j
\[ numOccBoost_{ij} = occurrenceCountTable_j[\frac{numOccs_{ij} \times tableSize_j}{max(6,fieldLength_j)}] \]

where *occurrenceCountTablej* is the boost table configured for field *j*,
typically a loggrowth function (see the [boost tables](#boost-tables) section below),
*numOccsij* is the number of occurrences of query term *i* in field *j*,
and *tableSizej* is the size of the boost table.

fmMaxTable
j
=

firstOccImp
j
×
max

firstOccurrenceTable
j
+

1
-

firstOccImp
j
×
max

occurrenceCountTable
j
\[ fmMaxTable_j = firstOccImp_j \times max(firstOccurrenceTable_j) + (1 - firstOccImp_j) \times max(occurrenceCountTable_j) \]

where *max(boostTablej)* is the max value in that table.
*fmMaxTablej* is 1 if table normalization is turned off
(see the property *nativeRank.useTableNormalization* in the
[configuration properties](#configuration-properties) section).

The default behavior for *nativeFieldMatch* is to consider all query terms searching in all index fields
when calculating the score.
The calculation can be limited to a specified set of index fields as follows:

`nativeFieldMatch(f1, f2)`

In this case only query terms searching in index fields *f1* and *f2* are considered.

## nativeProximity

The *nativeProximity* feature captures how near the matched query terms occur
in searched index fields by looking at the word distance between query terms in query term pairs.
Two query terms that are close to each other should give a higher score than two terms that are far from each other.

The score for *nativeProximity* is calculated as follows:

nativeProximity
=

∑
j
m

fieldWeight
j

∑

a
b

termPairWeight

a
b

proxImp
j
×

proxTable
j

dist

a
b
-
1
+

1
-

proxImp
j
×

revProxTable
j

dist

b
a
-
1

∑
j
m

fieldWeight
j

∑

a
b

termPairWeight

a
b
×

pMaxTable
j
\[ nativeProximity = \frac{\sum_j^mfieldWeight_j\sum_{ab}termPairWeight_{ab}(proxImp_j \times proxTable_j[dist_{ab} - 1] + (1 - proxImp_j) \times revProxTable_j[dist_{ba} - 1])}{\sum_j^mfieldWeight_j\sum_{ab}termPairWeight_{ab} \times pMaxTable_j} \]

where *m* is the number of index fields,
*ab* is a term pair searched for in field *j*,
*proxImpj* is the *proximityImportance* for field *j*,
*proxTablej* is the forward proximity boost table for field *j*,
*distab* is the minimum distance between occurrences of query terms *a*
and *b* in field *j*,
(*a* occurs before *b*),
*revProxTablej* is the reverse proximity boost table for field *j*,
*distba* is the minimum distance between occurrences of query terms
*b* and *a* in field *j* (*b* occurs before *a*),
and *termPairWeightab* and *pMaxTablej* are given below.

For each field *j* we consider all query terms searched in this field and generate a set of term pairs.
The *slidingWindowSize* parameter determines how many pairs that are generated.
With a sliding window of size 3 over the terms *a b c d*,
we first consider the terms *a b c*, then the terms *b c d*,
and finally the terms *c d*.
The following pairs are generated: *ab*, *ac*, *bc*, *bd*, and *cd*.

termPairWeight

a
b
=

connectedness

a
b
×

termSignificance
a
×

termWeight
a
+

termSignificance
b
×

termWeight
b
\[ termPairWeight_{ab} = connectedness_{ab} \times (termSignificance_a \times termWeight_a + termSignificance_b \times termWeight_b) \]

connectedness

a
c
=

min

connectedness

a
b

connectedness

b
c

d
i
s

t

a
c
\[ connectedness_{ac} = \frac{min(connectedness_{ab}, connectedness_{bc})}{dist_{ac}} \]

where *distac* is the distance between term *a* and *c* in the query.

pMaxTable
j
=

proxImp
j
×
max

proxTable
j
+

1
-

proxImp
j
×
max

revProxTable
j
\[ pMaxTable_j = proxImp_j \times max(proxTable_j) + (1 - proxImp_j) \times max(revProxTable_j) \]

where *max(boostTablej)* is the max value in that table.
*pMaxTablej* is 1 if table normalization is turned off
(see the property *nativeRank.useTableNormalization* in the
[configuration properties](#configuration-properties) section).

The default behavior for *nativeProximity* is to consider all index fields and all query terms
pairs searching in these fields when calculating the score.
The calculation can be limited to a specified set of index fields as follows:

`nativeProximity(f1, f2)`

In this case only query term pairs searching in index fields *f1* and *f2* are considered.

For multi-value fields, setting [element-gap](schema-reference.html#rank-element-gap) for the field in the rank profile enables distance calculation between adjacent elements.

## nativeAttributeMatch

The *nativeAttributeMatch* feature captures how well query terms match searched attribute fields,
and is calculated as follows:

nativeAttributeMatch
=

∑
i
n

termWeight
i
×

attributeWeight
j
×
sign

w

i
j
×

weightTable
j

abs

w

i
j

∑
i
n

termWeight
i
×

attributeWeight
j
×
max

weightTable
j
\[ nativeAttributeMatch = \frac{\sum_i^ntermWeight_i \times attributeWeight_j \times sign(w_{ij}) \times weightTable_j[abs(w_{ij})]}{\sum_i^ntermWeight_i \times attributeWeight_j \times max(weightTable_j)} \]

where *n* is the number of query terms searched in attribute fields,
*weightTablej* is the boost table for attribute *j*,
*max(weightTablej)* is the max value in that table
(1 if table normalization is turned off),
*sign(wij)* is the sign of *wij*.
*wij* is dependent on the attribute type:
* **Weighted set**: equals the weight associated with the key
  (represented by query term *i*) in attribute *j*.
* **Array**: equals the number of occurrences of query
  term *i* in attribute *j*.
* **Single**: equals 1.

The default behavior for *nativeAttributeMatch* is to consider all query terms
searching in all attribute fields when calculating the score.
The calculation can be limited to a specified set of attribute fields as follows:

`nativeAttributeMatch(a1, a2)`

In this case only query terms searching in attribute fields *a1* and *a2* are considered.

## nativeRank

The *nativeRank* feature is just a linear combination of the three other features,
and is calculated as follows:

nativeRank
=

f
m
w
×
nativeFieldMatch
+
p
w
×
nativeProximity
+
a
m
w
×
nativeAttributeMatch

f
m
w
+
p
w
+
a
m
w
\[ nativeRank = \frac{fmw \times nativeFieldMatch + pw \times nativeProximity + amw \times nativeAttributeMatch}{fmw + pw + amw} \]

where *fmw* is the *fieldMatchWeight*,
*pw* is the *proximityWeight*,
and *amw* is
the *attributeMatchWeight*.

The default behavior when calculating the native rank score
is to consider all query terms searching in all defined index fields and attribute fields.
In many cases though only a subset of these fields are of interest in the rank score calculation.
You can set up *nativeRank* for a subset of fields
by specifying the field names in the parameter list as follows:

```
first-phase {
    expression: nativeRank(title,body,tags)
}
```

In this case we have two index fields (*title* and *body*)
and one attribute field (*tags*),
and the *nativeRank* feature is calculated based on the
features *nativeFieldMatch(title,body)*, *nativeProximity(title,body)*,
and *nativeAttributeMatch(tags)*.
Note that the CPU cost of calculating the native rank score is also reduced when specifying a subset of the fields.

## Variables

This is a list of the common variables used in the formulas above:

| Variable | Description |
| --- | --- |
| *attributeWeightj* | The weight of attribute field *j*. See the [schema reference](schema-reference.html#weight) for how to set this weight. The default value is 100. |
| *connectednessab* | The connectedness between query terms *a* and *b*. |
| *fieldLengthj* | The length of field *j* in number of words. |
| *fieldWeightj* | The weight of index field *j*. See the [schema reference](schema-reference.html#weight) for how to set this weight. The default value is 100. |
| *termSignificancei* | The significance of query term *i*. |
| *termWeighti* | The weight of query term *i*. |

## Configuration properties

This is a comprehensive list of all the configuration properties to all native rank features:

| Feature | Parameter | Default | Description |
| --- | --- | --- | --- |
| `nativeFieldMatch` | `averageFieldLength` | The actual length of the field in the given document. | When set this replaces the true field length in the nativeFieldMatch formula for all documents. |
||  |  |  |  |
| --- | --- | --- | --- |
| `nativeFieldMatch` | `firstOccurrenceTable` | expdecay(8000,12.50) | The default table used when calculating boost for the first occurrence in a field. |
| `nativeFieldMatch` | `firstOccurrenceTable.fieldName` | The value of `firstOccurrenceTable` | The table used when calculating boost for the first occurrence in the given field. |
| `nativeFieldMatch` | `occurrenceCountTable` | loggrowth(1500,4000,19) | The default table used when calculating boost for the number of occurrences in a field. |
| `nativeFieldMatch` | `occurrenceCountTable.fieldName` | The value of `occurrenceCountTable` | The table used when calculating boost for the number of occurrences in the given field. |
| `nativeFieldMatch` | `firstOccurrenceImportance` | 0.5 | The default importance value used for weighting the boosts for first occurrence and number of occurrences in a field. This value should be in the interval [0, 1]. |
| `nativeFieldMatch` | `firstOccurrenceImportance.fieldName` | The value of `firstOccurrenceImportance` | The importance value used for the given field. |
| `nativeProximity` | `proximityTable` | expdecay(500,3) | The default table used when calculating forward proximity boost in a field. |
| `nativeProximity` | `proximityTable.fieldName` | The value of `proximityTable` | The table used when calculating forward proximity boost in the given field. |
| `nativeProximity` | `reverseProximityTable` | expdecay(400,3) | The default table used when calculating reverse proximity boost in a field. |
| `nativeProximity` | `reverseProximityTable.fieldName` | The value of `reverseProximityTable` | The table used when calculating reverse proximity boost in the given field. |
| `nativeProximity` | `proximityImportance` | 0.5 | The default importance value used for weighting the boosts for forward and reverse proximity in a field. This value should be in the interval [0, 1]. |
| `nativeProximity` | `proximityImportance.fieldName` | The value of `proximityImportance` | The importance value used for the given field. |
| `nativeProximity` | `slidingWindowSize` | 4 | The size of the sliding window used when generating term pairs. |
| {% include deprecated.html content="The elementGap rank property is deprecated and will be removed in Vespa 9."%} | | | |
| `nativeProximity` | `elementGap.fieldName` | infinity | The gap between positions in adjacent elements in multi-value fields. Use the [element-gap](schema-reference.html#rank-element-gap) rank setting instead. |
| `nativeAttributeMatch` | `weightTable` | linear(1,0) | The default table used when calculating boost for matching in an attribute field. |
| `nativeAttributeMatch` | `weightTable.attributeName` | The value of `weightTable` | The table used when calculating boost for matching in the given attribute. |
| `nativeRank` | `fieldMatchWeight` | 100.0 | How much to weight the score from *nativeFieldMatch*. |
| `nativeRank` | `proximityWeight` | 25.0 | How much to weight the score from *nativeProximity*. If table normalization is turned off the default value is 100.0. |
| `nativeRank` | `attributeMatchWeight` | 100.0 | How much to weight the score from *nativeAttributeMatch*. |
| `nativeRank` | `useTableNormalization` | true | Whether we should use table normalization for the native rank features. Set this property to *false* to turn off table normalization |

For example, to override the *occurrenceCountTable*
and *reverseProximityTable* for the index field *content*,
add the following to the rank profile in the sd file:

```
rank-properties {
    nativeFieldMatch.occurrenceCountTable.content: "linear(0,0)"
    nativeProximity.reverseProximityTable.content: "linear(0,0)"
}
```

See the [search definitions](schema-reference.html#rank-properties) reference
for more information on rank-properties.

### Boost tables

The following boost tables are supported by the native rank features:

| Name | Function | Description |
| --- | --- | --- |
| expdecay(w,t) | `w * exp(-x/t)` | Represents an exponential decay function where *w* is the weight controlling the amplitude and *t* is the tune parameter controlling the slope. |
| loggrowth(w,t,s) | `w * log(1 + (x/s)) + t` | Represents a logarithmic growth function where *w* is the weight controlling the amplitude, *t* is the tune parameter controlling the offset, and *s* is a scale parameter controlling the sensitivity to the variable *x* |
| linear(w,t) | `w * x + t` | Represents a linear function where *w* controls the slope and *t* controls the offset. |

The parameters *w*, *t*, and *s* are floating point numbers,
the same as the content of the tables.
The default table size is 256 with x in the interval [0,255].
You can override this default size by specifying an optional last parameter to the table name.
For instance, if you use *linear(1.5,0,512)* you get a table with size 512
populated with the result of evaluating the function *1.5*x + 0* for all x in the interval [0,511].

### Rank types

Four predefined rank types are supported by *nativeRank*:
*about* (default), *identity*, *tags*, and *empty*.
Each type is associated with a set of boost tables that are used by the native rank features.
See the [rank type](rank-types.html) document for detailed information on these type.

When setting up the sd file, either use one of the predefined rank types for a field,
or explicitly specify the boost tables to use for that field as a set of rank-properties.
If you don't specify anything you get the boost tables associated with the *about* type.
The *about* boost tables for *nativeFieldMatch* and *nativeProximity*
are already optimized for textual match,
while the boost table for *nativeAttributeMatch* is data dependent
and must be optimized for each use case.

## nativeRank limitations

The nativeRank feature is a pure text match scoring feature.
In particular, it does not take the following concepts into account for documents that match a query:
* Static rank or any other relevancy contribution that is based on a numeric value.
  Use the *attribute* feature in a ranking expression to get this concept into the final relevancy score.
* Geographical location of a match correlated to a location associated with the query.
  Use the *distance* or *closeness* feature in a ranking expression to take this into account.
* The age of the matching documents.
  Use the *freshness* feature in a ranking expression to take this into account.
