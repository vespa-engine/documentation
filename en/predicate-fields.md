---
# Copyright Vespa.ai. All rights reserved.
title: "Predicate Fields"
---

*[Predicate](reference/schema-reference.html#predicate) fields*
provides a way to match queries to a set of *boolean constraints* given in the document.
The typical use case is to have a set of boolean constraints representing advertisements,
specifying their target groups.
Then we query the system with a set of impressions, i.e. specific values for a given user,
to find out which ads can be shown to this user.
When configuring predicate fields there are some trade-offs between index size and query performance.
Predicate fields are not supported in
[streaming search](streaming-search.html#differences-in-streaming-search).

Predicate fields are good for solving problems where practitioners have used Percolator Queries.

## Boolean Constraints

A boolean constraint (predicate) specifies a target area for queries to land in.
Its attributes may be simple true/false criteria,
subsets of sets to match, or ranges of values.

### Predicates

A predicate is a specification of a boolean constraint in the form of a boolean expression.
For example, the predicate `gender in [Female] and age in [20..30] and pos in [1..4]`
can specify that an ad requires target users to be women between 20 and 30 years of age,
and that the ad must be placed in one of the top four positions.
The valid expressions are described by the following grammar:

```
predicate   = disjunction <EOF> ;
disjunction = conjunction [ 'or' disjunction ] ;
conjunction = ( leaf  | [ 'not' ], '(', disjunction, ')' ) [ 'and' conjunction ] ;
leaf        = value, [ 'not' ], 'in', ( value | multivalue | range )
            | 'true'
            | 'false' ;

value       = alphanum { alphanum } | string ;
multivalue  = '[' value, { ',', value } ']' ;
range       = '[' [ integer ] '..' [ integer ] ']' ;

alphanum    = alpha | digit | '_';
string      = '\'', { stdchars_1 | escape_1 }, '\''
            | '"', { stdchars_2 | escape_2 }, '"' ;

integer     = [ '-' | '+' ], ( posdigit, { digit } | '0' );

alpha       = ? ASCII characters in the range a-z and A-Z ? ;
digit       = '0' | posdigit ;
posdigit    = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' ;
stdchars_1  = ? All unicode chars except '\\' and '\'' ? ;
stdchars_2  = ? All unicode chars except '\\' and '"' ? ;
escape_1    = '\\', ( '\\' | 't' | 'n' | 'f' | 'r' | '\'' | 'x', hexdigit, hexdigit )
escape_2    = '\\', ( '\\' | 't' | 'n' | 'f' | 'r' | '"' | 'x', hexdigit, hexdigit )
hexdigit    = digit | 'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'A' | 'B' | 'C' | 'D' | 'E' | 'F' ;
```

### Attributes

The variables in predicates are known as *attributes*. There are two types of attributes:
* **Regular attributes**. Regular attributes take string values.
  Specify in the predicate that a regular attribute must have one value of multiple alternatives.
  E.g. `hobby in [Music, Hiking]` evaluates true if hobby is assigned to either
  `Music` or `Hiking` (or both).
* **Range attributes**. Range attributes take integer values
  and may only be used in range expressions.
  A range expression specifies either a lower bound, an upper bound or both:
  1. `age in [10..]` - age must be 10 or higher
  2. `age in [..10]` - age must be 10 or lower
  3. `age in [10..15]` - age must be between 10 and 15, inclusive

### Predicate Samples

The subset expression evaluates to true if the regular attribute is assigned
to any of the values listed in the brackets:

```
hobby in [Music, Hiking, Biking]
```

The range expression evaluates to true if the range attribute is in the specified range
(boundaries are inclusive):

```
age in [20..29]
```

It's also possible to specify only the lower or upper bound for a range expression:

```
age in [..29]
```

Use the `or` operator to create disjunctions:

```
age in [..29] or hobby in [Music, Biking]
```

Similarly, use the `and` operator to create conjunctions:

```
age in [20..29] and hobby in [Music]
```

Parenthesis can be used to create more complex predicates:

```
(age in [20..29] and gender in [Male]) or (age in [30..39] and gender in [Female])
```

The subset and range expression can be negated using the `not` operator:

```
age not in [20..29] and hobby not in [Music]
```
```
not age in [20..29] and not hobby in [Music]
```

The `not` operator can also be combined with parenthesis:

```
not (age in [20..29] or hobby in [Music])
```

Attributes and values containing non-alphanumeric letters must be surrounded with quotes:

```
"profile.gender" in ['Male', "Female"]
```

If a string surrounded with double-quotes contains a double-quote, escape it with backslash.
Same rule applies for single quotes in single-quoted strings.
Double quotes in single-quoted strings and single quotes in double-quoted string shall not be escaped.

```
"single'quote" in ["double\"quote", 'double"quote', 'single\'quote']
```

Set the predicate to the value `true` to make it always a match.
Setting the predicate to `false` will ensure that it's never a match.

```
true
```
```
false
```

## Queries

A boolean query represents a set of concrete values for attributes,
which may fall within the target area drawn up by one or more sets of boolean constraints.
Queries are specified by two lists of attributes with values.
One list holds regular attributes, each with one or more discrete values,
while the other list holds range attributes with a single value each.

### Search Using YQL+

Boolean queries are made using the `predicate` function of YQL+.
The predicate function takes three parameters: The predicate field,
a map of regular attribute key/value pairs, and a map of range attribute key/value pairs.

```
select * from sources * where predicate(predicate_field, {"gender":"Female", "gender":"Male", hobby":"Hiking"}, {"age":20L, "pos":2L})
```

One can use empty maps when specifying attributes:

```
select * from sources * where predicate(predicate_field, {}, {"age":20L})
```

When specifying multiple values for the same key, it is possible to use an array as the value:

```
select * from sources * where predicate(predicate_field,{"gender":["Female","Male"], "hobby":"Hiking"}, {"age":20L})
```

### Subqueries

For efficiency reasons it is possible to specify multiple queries at
once. This is done by providing a bitmap with each term, where the
bitmap represents which (out of 64) subqueries the term is a part
of. A typical use case for this is when we want to find ads for
multiple positions on a page. Then the user profile information will
be part of every subquery while the ad placement varies. Remember that
all subqueries are used every time, which means that empty subqueries
also can get matches.

#### Specifying Subqueries in YQL

Subqueries are specified as maps where the key is a string
representation of either a hex number or a list of bit numbers, and
the value is a map of attribute key/value pairs. The two queries below demonstrates the
two different methods of mapping attributes to subqueries.

```
select * from sources * where predicate(predicate_field, {"0x3":{"gender":"Female"}, "0x1":{"hobby":["music","hiking"]}}, {"0x2":{"age":23L}})
```
```
select * from sources * where predicate(predicate_field, {"[0,1]":{"gender":"Female"}, "[0]":{"hobby":["music","hiking"]}}, {"[1]":{"age":23L}})
```

The queries above is constructed from the following two queries:

```
select * from sources * where predicate(predicate_field, {"gender":"Female", "hobby":["music","hiking"]},{})
select * from sources * where predicate(predicate_field, {"gender":"Female"}, {"age":23L})
```

Note that the subquery bit numbers use zero-based numbering, e.g. first subquery has index `0`.
Highest valid subquery has index `63`.
Any value `0x1`-`0xFFFFFFFFFFFFFFFF` is a valid subquery bitmap.

{% include note.html content="When no subquery mapping is specified, the attribute is applied to all subqueries."%}

#### Identifying Subqueries in Results

When using subqueries you need to add the `subqueries`
summary feature to your schema. For each hit, the subqueries
are reported in two different summary features, one for the lower 32
bits, named `lsb`, and one for the upper 32 bits,
named `msb`.

See the [predicate search example](https://github.com/vespa-engine/sample-apps/tree/master/examples/predicate-fields) for how to configure a custom *searcher*, *services.xml*
and the *schema*
required to retrieve the subquery bitmap of each hit.

#### Predicate Example

A typical use case for the subquery feature is when we want to find ads for
multiple positions on a page. The user profile information will
be identical for every subquery while the ad placement varies. The following example uses 3 different attributes;
`age`, `gender` and `pos`. The 2 former attributes represents the user profile,
while the `pos` attribute determines the ad placement.
Assume the following 3 documents are indexed:

```
[
   {
      "fields" : {
         "target" : "age in [20..30] and gender in [Female, Male] and pos in [1]"
      },
      "put" : "id:test:ad::1"
   },
   {
      "fields" : {
         "target" : "gender in [Male] and pos in [1, 2]"
      },
      "put" : "id:test:ad::2"
   },
   {
      "fields" : {
         "target" : "age in [20..] and gender in [Female, Male] and pos in [2]"
      },
      "put" : "id:test:ad::3"
   }
]
```

Find all ads that target males at age 25 for ad placement 1 and 2.
To do that, create a query consisting of two subqueries, one for placement 1 and the other for placement 2:

```
select * from sources * where predicate(target, {"[0,1]":{"gender":"Male"}, "[0]":{"pos": "1"}, "[1]":{"pos": "2"}}, {"[0,1]":{"age":25L}})
```

Note that each subquery has a separate value for `pos`, while the `gender` and `age` values are common for both subqueries.

The query will return 3 hits, one for each document. Each document will have a *summary feature* with the subquery bitmap (64-bit).
This is assuming that the `SubqueriesSearcher` from the sample app is used. If not so, each document will have two summary features,
one for the lower 32-bit and one for the upper 32-bit of the subquery bitmap.
* The document with id `id:test:ad::1` will have subquery bitmap of
  `0x1`; the lowest bit set to 1 as the document is a hit for subquery #1.
* The document with id `id:test:ad::2` is a hit for both subqueries and has the two lowest bits set to 1,
  giving `0x3` as subquery bitmap.
* Following the same principle, the subquery bitmap of `id:test:ad::3` is `0x2`.

## Configuration

Note: Using predicate fields is complex and tuning the configuration for performance requires
insight in the underlying algorithms.

A field of type predicate requires an index definition
with a mandatory parameter, `arity`, a value which trades index size
for query complexity. See [Index Size](#index-size) for more
details. Fields of type predicate also accept three other optional parameters:
`lower-bound`, `upper-bound` and `dense-posting-list-threshold`.
These properties are helpful in optimizing query performance and index size. The two former parameters
sets the lower and upper bounds on values of range attributes. The latter value determines how the boolean index
is structured, trading index size for potentially better query performance.

To feed a predicate, put it in a field of type
[predicate](reference/schema-reference.html#predicate) as a string -
refer to the [JSON reference](reference/document-json-format.html#predicate).

### Schema

The following schema example sets up an attribute predicate field
including the mandatory arity parameter.

```
schema example {
    document example {

        field predicate_field type predicate {
            indexing: attribute
            index {
                arity: 2  # mandatory
                lower-bound: 3
                upper-bound: 200
                dense-posting-list-threshold: 0.25
            }
        }

    }

    # For subquery reporting:
    rank-profile default {
        summary-features: subqueries(predicate_field).lsb subqueries(predicate_field).msb
    }
}
```

### Upper and Lower Bounds

The `upper-bound` and `lower-bound` parameters
specify the range of values that the boolean expressions are expected
to operate on. Queries with values outside this range are
rejected. The index is optimized based on the bounds, so if the bounds
are changed, the index needs to be rebuilt.

### Dense Posting List Threshold

The `dense-posting-list-threshold` parameter is a threshold that impacts how the
boolean index is structured in memory. The boolean index consists of several sparse data structures
(B-tree based posting lists). The largest posting lists are also stored in a dense vector based structure.
The dense posting lists are faster for searching, but may increase the overall index size significantly.
Only posting lists with relative size above the threshold are stored in the dense format
(for a corpus of 1mill documents and threshold=0.5, all posting lists of size >500k will be stored as vector).
The optimal value depends on corpus characteristics and will lay somewhere between 0.15 - 0.50.
A too low threshold will have large, negative impact on both query performance and index size,
while a too large threshold may slightly decrease the query performance.

The default value is 0.40. Valid range is (0, 1].

### Index Size

When using range attributes, the attributes are expanded to a set of
attributes for sub-ranges that together covers the entire range. The
granularity of the sub-ranges are controlled by the parameter
`arity`. A low arity will make smaller indexes, but
require more terms in the queries. Conversely, a high arity makes for
large indexes but fewer query terms.

Also impacting index size is the size of intervals that are accepted
in the boolean constraints. A typical case is intervals with infinite
endpoints, i.e. match every number greater than *x*. Using 2^63
as infinity makes the intervals large, and impacts index size. A lower
max-value reduces the index size. The max-values can be easily
controlled with the `upper-bound`
and `lower-bound` parameters.

The `dense-posting-list-threshold` parameter has an inverse impact on the index size.
Increasing the threshold is beneficial if a smaller index size is preferred over query performance.

The following figure shows how the number of terms for a single
document grows with increasing arity and range limit.

google.load('visualization', '1', {packages: ['corechart']});

function drawVisualization() {
// Create and populate the data table.
let data = google.visualization.arrayToDataTable([
[ 'Bound (2^k)', 'Arity 2', 'Arity 4', 'Arity 8', 'Arity 16', 'Arity 32', 'Arity 64', 'Arity 128'],
[ 10 , 12, 18, 20, 30, 43, 27, 12 ],
[ 11 , 13, 19, 22, 34, 44, 43, 20 ],
[ 12 , 14, 21, 26, 42, 46, 75, 36 ],
[ 13 , 15, 22, 27, 43, 50, 76, 68 ],
[ 14 , 16, 24, 29, 45, 58, 78, 132 ],
[ 15 , 17, 25, 33, 49, 74, 82, 133 ],
[ 16 , 18, 27, 34, 57, 75, 90, 135 ],
[ 17 , 19, 28, 36, 58, 77, 106, 139 ],
[ 18 , 20, 30, 40, 60, 81, 138, 147 ],
[ 19 , 21, 31, 41, 64, 89, 139, 163 ],
[ 20 , 22, 33, 43, 72, 105, 141, 195 ],
[ 21 , 23, 34, 47, 73, 106, 145, 259 ],
[ 22 , 24, 36, 48, 75, 108, 153, 260 ],
[ 23 , 25, 37, 50, 79, 112, 169, 262 ],
[ 24 , 26, 39, 54, 87, 120, 201, 266 ],
[ 25 , 27, 40, 55, 88, 136, 202, 274 ],
[ 26 , 28, 42, 57, 90, 137, 204, 290 ],
[ 27 , 29, 43, 61, 94, 139, 208, 322 ],
[ 28 , 30, 45, 62, 102, 143, 216, 386 ],
[ 29 , 31, 46, 64, 103, 151, 232, 387 ],
[ 30 , 32, 48, 68, 105, 167, 264, 389 ],
[ 31 , 33, 49, 69, 109, 168, 265, 393 ],
[ 32 , 34, 51, 71, 117, 170, 267, 401 ],
[ 33 , 35, 52, 75, 118, 174, 271, 417 ],
[ 34 , 36, 54, 76, 120, 182, 279, 449 ],
[ 35 , 37, 55, 78, 124, 198, 295, 513 ],
[ 36 , 38, 57, 82, 132, 199, 327, 514 ],
[ 37 , 39, 58, 83, 133, 201, 328, 516 ],
[ 38 , 40, 60, 85, 135, 205, 330, 520 ],
[ 39 , 41, 61, 89, 139, 213, 334, 528 ],
[ 40 , 42, 63, 90, 147, 229, 342, 544 ],
[ 41 , 43, 64, 92, 148, 230, 358, 576 ],
[ 42 , 44, 66, 96, 150, 232, 390, 640 ],
[ 43 , 45, 67, 97, 154, 236, 391, 641 ],
[ 44 , 46, 69, 99, 162, 244, 393, 643 ],
[ 45 , 47, 70, 103, 163, 260, 397, 647 ],
[ 46 , 48, 72, 104, 165, 261, 405, 655 ],
[ 47 , 49, 73, 106, 169, 263, 421, 671 ],
[ 48 , 50, 75, 110, 177, 267, 453, 703 ],
[ 49 , 51, 76, 111, 178, 275, 454, 767 ],
[ 50 , 52, 78, 113, 180, 291, 456, 768 ],
[ 51 , 53, 79, 117, 184, 292, 460, 770 ],
[ 52 , 54, 81, 118, 192, 294, 468, 774 ],
[ 53 , 55, 82, 120, 193, 298, 484, 782 ],
[ 54 , 56, 84, 124, 195, 306, 516, 798 ],
[ 55 , 57, 85, 125, 199, 322, 517, 830 ],
[ 56 , 58, 87, 127, 207, 323, 519, 894 ],
[ 57 , 59, 88, 131, 208, 325, 523, 895 ],
[ 58 , 60, 90, 132, 210, 329, 531, 897 ],
[ 59 , 61, 91, 134, 214, 337, 547, 901 ],
[ 60 , 62, 93, 138, 222, 353, 579, 909 ],
[ 61 , 63, 94, 139, 223, 354, 580, 925 ],
[ 62 , 64, 96, 141, 225, 356, 582, 957 ],
[ 63 , 65, 97, 145, 229, 360, 586, 1021 ]
]);
// Create and draw the visualization.
new google.visualization.LineChart(document.getElementById('visualization')).
draw(data, {curveType: "none",
title: 'Index size vs. range limit and arity',
width: 700, height: 600,
vAxis: {title: 'Term count', maxValue: 10},
hAxis: {title: 'Range limit, 2^k'}}
);
}
google.setOnLoadCallback(drawVisualization);

Index size vs. range limit and arityArity 2Arity 4Arity 8Arity 16Arity 32Arity 64Arity 128203040506003006009001,200Range limit, 2^kTerm count

259
