---
# Copyright Vespa.ai. All rights reserved.
title: "Grouping Reference"
---

Read the [Vespa grouping guide](../grouping.html) first, for examples and an introduction to grouping -
this is the Vespa grouping reference.

Also note that using a [multivalued](../schemas.html#field) attribute
(such as an array of doubles) in a grouping expression affects performance.
Such operations can hit a memory bandwidth bottleneck,
particularly if the set of hits to be processed is large, as more data is evaluated.

## Group

Group query results using a custom expression (using the `group` clause):
* A numerical constant
* A document [attribute](../attributes.html)
* A function over another expression (`xorbit`, `md5`, `cat`,
  `xor`, `and`, `or`, `add`, `sub`,
  `mul`, `div`, `mod`) or any other [expression](#expressions)
* The datatype of an expression is resolved using best-effort, similarly to how common
  programming languages does to resolve arithmetics of different data typed operands
* The results of any expression are either scalar or single dimension arrays
  + `add(<array>)` adds all elements together to produce a scalar
  + `add(<arrayA>, <arrayB>)` adds each element together producing a new
    array whose size is `max(|<arrayA>|, |<arrayB>|)`

Groups can contain subgroups (by using `each` and `group` operations),
and may be nested to any level.

Multiple sub-groupings or outputs can be created under the same group level, using multiple parallel `each`
or `all` clauses, and each one may be labelled using [as(mylabel)](#labels).

When grouping results, *groups* that contain *outputs*,
*group lists* and *hit lists* are generated.
Group lists contain subgroups, and hit lists contain hits that are part of the owning group.

The identity of a group is held by its *id*.
Scalar identities such as long, double and string, are directly available from the *id*,
whereas range identities used for bucket aggregation are separated into the sub-nodes *from* and *to*.
Refer to the [result format reference](default-result-format.html).

### Multivalue attributes

A [multivalue](../schemas.html#field) attribute is a
[weighted set](schema-reference.html#weightedset),
[array](schema-reference.html#array) or
[map](schema-reference.html#map).
Most grouping functions will just handle the elements of
multivalued attributes separately, as if they were all individual values in separate documents.
If you are grouping over array of struct or maps, scoping will be used to preserve structure.
Each entry in the array/map will be treated as a separate sub-document.
The following syntax can be used when grouping on *map* attribute fields.

Group on map keys:

```
all( group(mymap.key) each(output(count())) )
```

Group on map keys then on map values:

```
all( group(mymap.key) each( group(mymap.value) each(output(count())) ))
```

Group on values for key *my_key*:

```
all( group(my_map{"my_key"}) each(output(count())) )
```

Group on struct field *my_field* referenced in map element *my_key*:

```
all( group(my_map{"my_key"}.my_field) each(output(count())) )
```

The key can either be specified directly (above) or indirectly via a key source attribute.
The key is retrieved from the key source attribute for each document.
Note that the key source attribute must be single value and have the same data type as the key type of the map:

```
all( group(my_map{attribute(my_key_source)}) each(output(count())) )
```

Group on array of integers field:

```
all( group(my_array) each(output(count())) )
```

Group on struct field *my_field* in the *my_array* array of structs:

```
all( group(my_array.my_field) each(output(count())) )
```

[Tensors](schema-reference.html#tensor) can not be used in grouping.

## Filtering groups

When grouping on multivalue attributes, it may be useful to filter the groups so
that only some specific values are collected. This can be done by adding a
filter. The `filter` clause expects a filter *predicate*:
* [regex("regular expression", input-expression)](#regex-filter)
* [range(min-limit, max-limit, input-expression)](#range-filter)
* [range(min-limit, max-limit, input-expression, bool, bool)](#range-filter)
* [not *predicate*](#logical-predicates-filter)
* [*predicate* and *predicate*](#logical-predicates-filter)
* [*predicate* or *predicate*](#logical-predicates-filter)

### Regex filter

Use a regular expression to match the input, and include only
documents that match in the grouping. The input will usually be the
same -expression as in the "group" clause.
Example:

```
all( group(my_array) filter(regex("foo.*", my_array)) ...)
```

Here,
each value in *my_array* is considered, but only the values that start
with a "foo" prefix are collected in groups; All others are ignored.
See [example](/en/grouping.html#structured-grouping).

### Range filter

Use a `range` filter to match documents where a field value is between a lower and an upper bound. Example:

```
all( group(some_field) filter(range(1990, 2012, year)) ...)
```

Here, the lower bound is *inclusive* (year ≥ 1990) and the upper bound is *exclusive* (year < 2012).
Use optional bools at the end to control if the lower and upper bounds are inclusive respectively.
The first bool sets the lower bound inclusive, and the second sets upper bound inclusive.

```
all( group(some_field) filter(range(1990, 2012, year, true, true)) ...)
```

Here, both lower and upper bound are inclusive.

### Logical predicates

Use `not` to negate another filter expression. It takes a single
sub-filter and matches when the sub-filter does not. Example:

```
all( group(my_field) filter( not regex("bar.*", my_other_field)) ...)
```

Use `or` to perform a logical disjunction across two
sub-filters. The combined filter matches if any of the sub-filters evaluate to
true. Example:

```
all( group(my_field) filter( regex("bar.*", my_field) or regex("baz.*", my_third_field) ) ...)
```

Use `and` to perform a logical conjunction across two
sub-filters. The combined filter matches only if all of the sub-filters evaluate
to true. Example:

```
all( group(my_field) filter( regex("bar.*", my_other_field) and regex("baz.*", my_third_field) ) ...)
```

These logical predicates can be nested to create complex filter conditions.
Filter expressions follow *conventional precedence*
rules: `not` is evaluated before `and`,
and `and` is evaluated before `or`. Operators of the same
precedence are evaluated left-to-right. Use parentheses `(...)` to
force a different grouping when needed.
Example:

```
all(
    group(my_field)
    filter( (regex("bar.*", some_field) or regex("baz.*", other_field)) and not regex(".*foo", some_field))
    each(...)
)
```

## Order / max

Each level of grouping may specify how to order its groups (using `order`):
* Ordering can be done using any of the available aggregates
* Multi-level grouping allows strict ordering where primary aggregates may be equal
* Ordering is either ascending or descending, specified per level of ordering
* Groups are sorted using [locale aware sorting](#uca)

Limit the number of groups returned for each level using `max`,
returning only first *n* groups as specified by `order`:
* `order` changes ordering of groups after a merge operation for the following
  aggregators: `count`, `avg` and  `sum`
* `order` **will not** change ordering of groups after a merge operation
  when `max` or `min` is used
* Default order, `-max(relevance())`, **does not** require use of
  [precision](#precision)

## Continuations

Pagination of grouping results are managed by `continuations`.
These are opaque objects that can be combined and re-submitted using the `continuations` annotation
on the grouping step of the query to move to the previous or next page in a result list.

All root groups contain a single *this* continuation per `select`.
That continuation represents the current view, and if submitted as the sole continuation,
it will reproduce the exact same result as the one that contained it.

There are zero or one *prev*/*next* continuation per group- and hit list.
Submit any number of these to retrieve the next/previous pages of the corresponding lists

Any number of continuations can be combined in a query, but the first must always be the *this*-continuation.
E.g. one may simultaneously move both to the next page of one list, and the previous page of another.

{% include note.html content="If more than one continuation object are provided for the same group- or hit-list,
the one given last is the one that takes effect.
This is because continuations are processed in the order given,
and they replace whatever continuations they collide with."%}

If working programmatically with grouping, find the
[Continuation](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/grouping/Continuation.html)
objects within
[RootGroup](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/grouping/result/RootGroup.html),
[GroupList](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/grouping/result/GroupList.html) and
[HitList](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/grouping/result/HitList.html)
result objects. These can then be added back into the continuation list of the
[GroupingRequest](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/grouping/GroupingRequest.html)
to paginate.

Refer to the [grouping guide](../grouping.html#pagination) for an example.

## Labels

Lists created using the `each` keyword can be assigned a label
using the construct `each(...) as(mylabel)`.
The outputs created by that each clause will be identified by this label.

## Aliases

Grouping expressions can be tagged with an *alias*.
An alias allows the expression to be reused without having to repeat the expression verbatim.

```
all(group(a) alias(myalias, count()) each(output($myalias)))
```

is equivalent to

```
all(group(a) each(output(count())))
```

.

```
all(group(a) order($myalias=count()) each(output($myalias)))
```

is equivalent to

```
all(group(a) order(count()) each(output(count())))
```

.

## Precision

The number of intermediate groups returned from each content node
during expression evaluation to give the container node more data to consider
when selecting the groups that are to be evaluated further:
`each(...) precision(1000)`
A higher number costs more bandwidth, but leads to higher accuracy in some cases.

## Query parameters

The following *query parameters* are relevant for grouping.
See the [Query API Reference](query-api-reference.html#parameters) for description.
* [select](query-api-reference.html#select)
* [groupingSessionCache](query-api-reference.html#groupingsessioncache)
* [grouping.defaultMaxGroups](query-api-reference.html#grouping.defaultmaxgroups)
* [grouping.defaultMaxHits](query-api-reference.html#grouping.defaultmaxhits)
* [grouping.globalMaxGroups](query-api-reference.html#grouping.globalmaxgroups)
* [grouping.defaultPrecisionFactor](query-api-reference.html#grouping.defaultprecisionfactor)

## Grouping Session Cache

{% include important.html content="The grouping session cache is **only useful if** the grouping expression
uses default ordering.
The **drawback** is that when `max` is specified in the grouping expression,
it might cause inaccuracies in aggregated values such as `count`.
It is recommended testing whether this is an issue or not,
and if so, adjust the `precision` parameter to still get correct counts."%}

The session cache stores intermediate grouping results in the content nodes when using multi-level grouping expressions,
in order to speed up grouping at a potential loss of accuracy. This causes the query and grouping expression to be run only once.

When having multi-level grouping expressions, the search query is normally re-run for each level.
The drawback of this is, with an expensive ranking function, the query will take more time than strictly necessary.

## Aggregators

Each level of grouping specifies a set of aggregates to collect for all documents
that belong to that group (using the `output` operation):
* The documents in a group, retrieved using a specified summary class
* The count of documents in a group
* The sum, average, min, max, xor or standard deviation of an expression
* Multiple quantiles of an expressions value

When all arguments are numeric, the result type is resolved by looking at the argument types.
If all arguments are longs, the result is a long.
If at least one argument is a double, the result is a double.

When using `order`, aggregators can also be used in expressions in order to get increased control over group sorting.
This does not work with expressions that takes attributes as an argument, unless the expression is enclosed within an aggregator.

Using sum, max on a multivalued attribute:
Doing an operation such as `output(sum(myarray))` will run the sum over each element value in each document.
The result is the sum of sums of values.
Similarly `max(myarray)` will yield the maximal element over all elements in all documents, and so on.

Compute quantiles by listing the desired quantile values (comma-separated) in brackets, followed by a comma and the expression (e.g., a field):

```
all( group(city) each(output(quantiles([0.5], delivery_days) as(median_delivery_days) ) ) )
```

to compute the median, or

```
all( group(city) each(output(quantiles([0.5, 0.9], delivery_days))) )
```

This computes the median (p50) and 90th percentile (p90) time to delivery in days per city. Note that quantiles are computed using [KLL Sketch](https://datasketches.apache.org/docs/KLL/KLLSketch.html), so they are approximate.

Multivalue fields such as maps, arrays can be used for grouping.
However, using aggregation functions such as sum() on such fields can give misleading results.
Assume a map from strings to integers (`map<string, int>`),
where the strings are some sort of key to use for grouping.
The following expression will provide the sum of the values for all keys:

```
all( group(mymap.key) each(output(sum(mymap.value))) )
```

and not the sum of the values within each key, as one would expect.
It is still, however, possible to run the following expression to get the sum of values within a specific key:

```
all( group("my_group") each(output(sum(mymap{"foo"}))) )
```

Refer to the system test for
[grouping on struct and map types](https://github.com/vespa-engine/system-test/blob/master/tests/search/struct_and_map_types/struct_and_map_grouping.rb)
for more examples.

|  |  |  |  |
| --- | --- | --- | --- |
| Group list aggregators | | | |
| Name | Description | Arguments | Result |
| count | Counts the number of unique groups (as produced by `group`). Note that `count` operates independently of `max` and that this count is an estimate using HyperLogLog++ which is an algorithm for the count-distinct problem | None | Long |
| Group aggregators | | | |
| Name | Description | Arguments | Result |
| count | Increments a long counter every time it is invoked | None | Long |
| sum | Sums the argument over all selected documents | Numeric | Numeric |
| avg | Computes the average over all selected documents | Numeric | Numeric |
| min | Keeps the minimum value of selected documents | Numeric | Numeric |
| max | Keeps the maximum value of selected documents | Numeric | Numeric |
| xor | XOR the values (their least significant 64 bits) of all selected documents | Any | Long |
| stddev | Computes the population standard deviation over all selected documents | Numeric | Double |
| quantiles | Computes one or multiple quantiles of the values of an expression. Quantiles must be a number between 0 and 1 inclusive. | [Numeric+], Expr | [{"quantile":Double,"value":Double}+] |
| Hit aggregators | | | |
| Name | Description | Arguments | Result |
| summary | Produces a summary of the requested [summary class](/en/reference/schema-reference.html#document-summary) | Name of summary class | Summary |

## Expressions

|  |  |  |  |
| --- | --- | --- | --- |
| Arithmetic expressions | | | |
| Name | Description | Arguments | Result |
| add | Add the arguments together | Numeric+ | Numeric |
| + | Add left and right argument | Numeric, Numeric | Numeric |
| mul | Multiply the arguments together | Numeric+ | Numeric |
| * | Multiply left and right argument | Numeric, Numeric | Numeric |
| sub | Subtract second argument from first, third from result, etc | Numeric+ | Numeric |
| - | Subtract right argument from left | Numeric, Numeric | Numeric |
| div | Divide first argument by second, result by third, etc | Numeric+ | Numeric |
| / | Divide left argument by right | Numeric, Numeric | Numeric |
| mod | Modulo first argument by second, result by third, etc | Numeric+ | Numeric |
| % | Modulo left argument by right | Numeric, Numeric | Numeric |
| neg | Negate argument | Numeric | Numeric |
| - | Negate right argument | Numeric | Numeric |
| Bitwise expressions | | | |
| Name | Description | Arguments | Result |
| and | AND the arguments in order | Long+ | Long |
| or | OR the arguments in order | Long+ | Long |
| xor | XOR the arguments in order | Long+ | Long |
| String expressions | | | |
| Name | Description | Arguments | Result |
| strlen | Count the number of bytes in argument | String | Long |
| strcat | Concatenate arguments in order | String+ | String |
| Type conversion expressions | | | |
| Name | Description | Arguments | Result |
| todouble | Convert argument to double | Any | Double |
| tolong | Convert argument to long | Any | Long |
| tostring | Convert argument to string | Any | String |
| toraw | Convert argument to raw | Any | Raw |
| Raw data expressions | | | |
| Name | Description | Arguments | Result |
| cat | Cat the binary representation of the arguments together | Any+ | Raw |
| md5 | Does an MD5 over the binary representation of the argument, and keeps the lowest 'width' bits | Any, Numeric(width) | Raw |
| xorbit | Does an XOR of 'width' bits over the binary representation of the argument. Width is rounded up to a multiple of 8 | Any, Numeric(width) | Raw |
| Accessor expressions | | | |
| Name | Description | Arguments | Result |
| relevance | Return the computed rank of a document | None | Double |
| <attribute-name> | Return the value of the named attribute | None | Any |
| array.at | Array element access. The expression `array.at(myarray, idx)` returns one value per document by evaluating the `idx` expression and using it as an index into the array. The expression can then be used to build bigger expressions such as `output(sum(array.at(myarray, 0)))` which will sum the first element in the array of each document.  * The `idx` expression is capped to `[0, size(myarray)-1]` * If > array size, the last element is returned * If < 0, the first element is returned | Array, Numeric | Any |
| interpolatedlookup | Counts elements in a sorted array that are less than an expression, with linear interpolation if the expression is between element values. The operation `interpolatedlookup(myarray, expr)` is intended for generic graph/function lookup. The data in `myarray` should be numerical values sorted in ascending order. The operation will then scan from the start of the array to find the position where the element values become equal to (or greater than) the value of the `expr` lookup argument, and return the index of that position.  When the lookup argument's value is between two consecutive array element values, the returned position will be a linear interpolation between their respective indexes. The return value is always in the range `[0, size(myarray)-1]` of the valid index values for an array.  Assume `myarray` is a sorted array of type `array<double>` in each document: The expression `interpolatedlookup(myarray, 4.2)` is now a per-document expression that first evaluates the lookup argument, here a constant expression 4.2, and then looks at the contents of `myarray` in the document. The scan starts at the first element and proceeds until it hits an element value greater than 4.2 in the array. This means that:   * If the first element in the array is greater than 4.2, the expression returns 0 * If the first element in the array is exactly 4.2, the expression still returns 0 * If the first element in the array is 1.7 while the **second** element value is exactly 4.2,   the expression return 1.0 - the index of the second element * If **all** the elements in the array are less than 4.2,   the last valid array index `size(myarray)-1` is returned * If the 5 first elements in the array have values smaller than the lookup argument,   and the lookup argument is halfway between the fifth and sixth element,   a value of 4.5 is returned - halfway between the array indexes of the fifth and sixth elements * Similarly, if the elements in the array are `{0, 1, 2, 4, 8}`   then passing a lookup argument of "5" would return 3.25 (linear interpolation between   `indexOf(4)==3` and `indexOf(8)==4`) | Array, Numeric | Numeric |
| Bucket expressions | | | |
| Name | Description | Arguments | Result |
| fixedwidth | Maps the value of the first argument into consecutive buckets whose width equals the second argument | Any, Numeric | NumericBucketList |
| predefined | Maps the value of the first argument into the given buckets.   * Standard mathematical start and end specifiers may be used to define the width of a `bucket`.   The `(` and `)` evaluates to `[` and `>` by default. * The buckets assume the type of the start/end specifiers   (`string`, `long`, `double` or `raw`).   Values are converted to this type before being compared with these specifiers.   (e.g. `double` values are rounded to the nearest integer for buckets of type `long`). * The end specifier can be skipped. The buckets   `bucket(3)`/`bucket[3]` are the same as `bucket[3,4>`.   This is allowed for string expressions as well;   `bucket("c")` is identical to `bucket["c", "c ">`. | Any, Bucket+ | BucketList |
| Time expressions The field must be a [long](schema-reference.html#long), with second resolution (unix timestamp/epoch) - [examples](../grouping.html#time-and-date). Each of the time-functions will respect the [timezone](query-api-reference.html#timezone) query parameter. | | | |
| Name | Description | Arguments | Result |
| time.dayofmonth | Returns the day of month (1-31) for the given timestamp | Long | Long |
| time.dayofweek | Returns the day of week (0-6) for the given timestamp, Monday being 0 | Long | Long |
| time.dayofyear | Returns the day of year (0-365) for the given timestamp | Long | Long |
| time.hourofday | Returns the hour of day (0-23) for the given timestamp | Long | Long |
| time.minuteofhour | Returns the minute of hour (0-59) for the given timestamp | Long | Long |
| time.monthofyear | Returns the month of year (1-12) for the given timestamp | Long | Long |
| time.secondofminute | Returns the second of minute (0-59) for the given timestamp | Long | Long |
| time.year | Returns the full year (e.g. 2009) of the given timestamp | Long | Long |
| time.date | Returns the date (e.g. 2009-01-10) of the given timestamp | Long | Long |
| List expressions | | | |
| Name | Description | Arguments | Result |
| size | Return the number of elements in the argument if it is a list. If not return 1 | Any | Long |
| sort | Sort the elements in argument in ascending order if argument is a list If not it is a NOP | Any | Any |
| reverse | Reverse the elements in the argument if argument is a list If not it is a NOP | Any | Any |
| Other expressions | | | |
| Name | Description | Arguments | Result |
| zcurve.x | Returns the X component of the given [zcurve](https://en.wikipedia.org/wiki/Z-order_curve) encoded 2d point. All fields of type "position" have an accompanying "<fieldName>_zcurve" attribute that can be decoded using this expression, e.g. `zcurve.x(foo_zcurve)` | Long | Long |
| zcurve.y | Returns the Y component of the given zcurve encoded 2d point | Long | Long |
| uca | Converts the attribute string using [unicode collation algorithm](https://www.unicode.org/reports/tr10/). Groups are sorted using locale aware sorting, with the default and primary strength values, respectively:   ``` all( group(s) order(max(uca(s, "sv"))) each(output(count())) ) ```  ``` all( group(s) order(max(uca(s, "sv", "PRIMARY"))) each(output(count())) ) ``` | Any, Locale(String), Strength(String) | Raw |
| Single argument standard mathematical expressionsThese are the standard mathematical functions as found in the Java [Math](https://docs.oracle.com/javase/8/docs/api/java/lang/Math.html) class. | | | |
| Name | Description | Arguments | Result |
| math.exp |  | Double | Double |
| math.log |  | Double | Double |
| math.log1p |  | Double | Double |
| math.log10 |  | Double | Double |
| math.sqrt |  | Double | Double |
| math.cbrt |  | Double | Double |
| math.sin |  | Double | Double |
| math.cos |  | Double | Double |
| math.tan |  | Double | Double |
| math.asin |  | Double | Double |
| math.acos |  | Double | Double |
| math.atan |  | Double | Double |
| math.sinh |  | Double | Double |
| math.cosh |  | Double | Double |
| math.tanh |  | Double | Double |
| math.asinh |  | Double | Double |
| math.acosh |  | Double | Double |
| math.atanh |  | Double | Double |
| Dual argument standard mathematical expressions | | | |
| Name | Description | Arguments | Result |
| math.pow | Return X^Y. | Double, Double | Double |
| math.hypot | Return length of hypotenuse given X and Y sqrt(X^2 + Y^2) | Double, Double | Double |

## Filters

|  |  |  |  |
| --- | --- | --- | --- |
| String filters | | | |
| Name | Description | Arguments | Result |
| regex | Matches a field against a regular expression string. | String, Expression | Bool |
| Numeric filters | | | |
| Name | Description | Arguments | Result |
| range | Matches when a field is between a lower and upper bound. | Numeric, Numeric, Expression, Bool?, Bool? | Bool |
| Predicate filters | | | |
| Name | Description | Arguments | Result |
| and | Logical `and` between the arguments. | Filter, Filter | Bool |
| not | Logical `not` on the argument. | Filter | Bool |
| or | Logical `or` between the arguments. | Filter, Filter | Bool |

## Grouping language grammar

```
request    ::= "all(" operations ")"
group      ::= ( "all" | "each") "(" operations ")" [ "as" "(" identifier ")" ]
operations ::= [ "group" "(" exp ")" ]
               ( ( "alias" "(" identifier "," exp ")" ) |
                 ( "filter" "(" filterOp ")" ) |
                 ( "max"   "(" ( number | "inf" ) ")" ) |
                 ( "order" "(" expList | aggrList ")" ) |
                 ( "output" "(" aggrList ")" ) |
                 ( "precision" "(" number ")" ) )*
               group*
aggrList   ::= aggr ( "," aggr )*
aggr       ::= ( ( "count" "(" ")" ) |
                 ( "sum" "(" exp ")" ) |
                 ( "avg" "(" exp ")" ) |
                 ( "max" "(" exp ")" ) |
                 ( "min" "(" exp ")" ) |
                 ( "xor" "(" exp ")" ) |
                 ( "stddev" "(" exp ")" ) |
                 ( "summary" "(" [ identifier ] ")" ) )
               [ "as" "(" identifier ")" ]
expList    ::= exp ( "," exp )*
exp        ::= ( "+" | "-") ( "$" identifier [ "=" math ] ) | ( math ) | ( aggr )
filterOp   ::= "regex" "(" string "," exp ")"
math       ::= value [ ( "+" | "-" | "*" | "/" | "%" ) value ]
value      ::= ( "(" exp ")" ) |
               ( "add" "(" expList ")" ) |
               ( "and" "(" expList ")" ) |
               ( "cat" "(" expList ")" ) |
               ( "div" "(" expList ")" ) |
               ( "docidnsspecific" "(" ")" ) |
               ( "fixedwidth" "(" exp "," number ")" ) |
               ( "interpolatedlookup" "(" attributeName "," exp ")") |
               ( "math" "." (
                              (
                                "exp" | "log" | "log1p" | "log10" | "sqrt" | "cbrt" |
                                "sin" | "cos" | "tan" | "asin" | "acos" | "atan" |
                                "sinh" | "cosh" | "tanh" | "asinh" | "acosh" | "atanh"
                              ) "(" exp ")" |
                              ( "pow" | "hypot" ) "(" exp "," exp ")"
                            )) |
               ( "max" "(" expList ")" ) |
               ( "md5" "(" exp "," number "," number ")" ) |
               ( "min" "(" expList ")" ) |
               ( "mod" "(" expList ")" ) |
               ( "mul" "(" expList ")" ) |
               ( "or" "(" expList ")" ) |
               ( "predefined" "(" exp "," "(" bucket ( "," bucket )* ")" ")" ) |
               ( "reverse" "(" exp ")" ) |
               ( "relevance" "(" ")" ) |
               ( "sort" "(" exp ")" ) |
               ( "strcat" "(" expList ")" ) |
               ( "strlen" "(" exp ")" ) |
               ( "size" "(" exp")" ) |
               ( "sub" "(" expList ")" ) |
               ( "time" "." ( "date" | "year" | "monthofyear" | "dayofmonth" | "dayofyear" | "dayofweek" |
                              "hourofday" | "minuteofhour" | "secondofminute" ) "(" exp ")" ) |
               ( "todouble" "(" exp ")" ) |
               ( "tolong" "(" exp ")" ) |
               ( "tostring" "(" exp ")" ) |
               ( "toraw" "(" exp ")" ) |
               ( "uca" "(" exp "," string [ "," string ] ")" ) |
               ( "xor" "(" expList ")" ) |
               ( "xorbit" "(" exp "," number ")" ) |
               ( "zcurve" "." ( "x" | "y" ) "(" exp ")" ) |
               ( attributeName "." "at" "(" number ")") |
               ( attributeName )
bucket     ::= "bucket" ( "(" | "[" | "<" )
                        ( "-inf" | rawvalue | number | string )
                        [ "," ( "inf" | rawvalue | number | string ) ]
                        ( ")" | "]" | ">" )
rawvalue   ::= "{" ( ( string | number ) "," )* "}"
```
