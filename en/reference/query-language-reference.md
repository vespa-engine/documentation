---
# Copyright Vespa.ai. All rights reserved.
title: "YQL Query Language Reference"
---

Vespa accepts unstructured human input and structured queries for application logic separately,
then combines them into a single data structure for executing.
Human input is parsed heuristically, while application queries are formulated in YQL.

{% include note.html content='See the [Query Language Guide](../query-language.html)
for query examples'%}

A query URL looks like:

```
http://myhost.mydomain.com:8080/search/?yql=select%20%2A%20from%20sources%20%2A%20where%20text%20contains%20%22blues%22
```

In other words, `yql` contains:

```
select * from sources * where text contains "blues"
```

This [matches](schema-reference.html#match) all documents
where the field named *text* contains the word *blues*.

Quote `"` and backslash `\` characters in text values must be escaped by a backslash,
also see [how does backslash escapes work](../faq.html#how-does-backslash-escapes-work).

{% include important.html content='There is no way to query for a field that is not set
/ equals `null` or `NaN`.
Work around using a "magic" value (like MAXINT) that is not normally used in the documents.'%}

## select
*select* is the list of [summary fields](../schemas.html#indexing) requested
(a field with the `summary` index attribute).
Vespa will hide other fields in the matching documents.

```
select price,isbn from sources * where title contains "madonna"
```

The above explicitly requests the fields "price" and "isbn" (from all sources).
To request all fields, use an asterisk as field selection:

```
select * from sources * where title contains "madonna"
```

## from sources
*from sources* specifies which content
[sources](query-api-reference.html#model.sources) to query. Example:

```
select * from music where title contains "madonna"
```

queries all document types in the *music* content cluster or federation source. Query in:

| all sources | `select … from sources * where …` |
| a set of sources | `select … from sources source1, source2 where …` |
| a single source | `select … from source1 where …` |

In other words, *sources* is used for querying some/all sources.
If only a single source is queried, the *sources* keyword is dropped.
To restrict the query to only one schema (aka document type) use the
[model.restrict](query-api-reference.html#model.restrict) URL parameter.
Also see [federation](../federation.html).

## where

The `where` clause is a tree of operators:

| numeric | The following numeric operators are available: `= < > <= >= range(field, lower bound, upper bound)`.   ``` where 500 >= price ```  ``` where range(fieldname, 0, 5000000000L) ```   Numbers must be in the signed 32-bit range. Input 64-bit signed numbers using `L` as suffix.  For the `range` operator, one can also use the strings `Infinity` or `-Infinity`:   ``` where (range(year, 2000, Infinity)) ```  | Annotation | Effect | | --- | --- | | [bounds](#bounds) | Range: open or closed interval. | | [hitLimit](#hitlimit) | Used for *capped range search*. The `range()` query operator with `hitLimit` can be used to efficiently implement top-k selection for ranking a subset of the documents in the index. See [example and use cases](../performance/practical-search-performance-guide.html#advanced-range-search-with-hitlimit). |   The [weightedset](schema-reference.html#weightedset) field does not support filtering on weight. Solve this using the [map](schema-reference.html#map) type and [sameElement](#sameelement) query operator - see [example](../query-language.html#map). |
| boolean | The boolean operator is: `=`   ``` where alive = true ``` |
| contains | The right-hand side argument of the contains operator is either a string literal, or a function, like `phrase`.  `contains` is the basic building block for text matching. The kind of [matching](schema-reference.html#match) to be done depends on the field settings in the schema.   ``` where title contains "madonna" ```  | Annotation | Effect | | --- | --- | | [stem](#stem) | By default, the string literal is [tokenized](../linguistics.html#tokenization) to match the field(s) searched. Explicitly control tokenization by using [stem](#stem):  ``` where title contains ({stem: false}"madonna") ``` |   The matched field must be an [indexed field or attribute](../schemas.html#indexing).  Fields inside structs are referenced using dot notation - e.g `mystruct.mystructfield`. |
| and | `and` accepts other `and` statements, `or` statements, [userQuery](#userquery), logically inverted statements - and contains statements as arguments:   ``` where title contains "madonna" and title contains "saint" ``` |
| or | `or` accepts other `or` statements, `and` statements, [userQuery](#userquery) - and contains statements as arguments:   ``` where title contains "madonna" or title contains "saint" ``` |
| not | Use the `!` operator to match document that does *not* satisfy some condition:   ``` where title contains "madonna" and !(title contains "saint") ``` |
| phrase | Phrases are expressed as a function:   ``` where text contains phrase("st", "louis", "blues") ``` |
| near | `near()` matches if all argument terms occur close to each other in the same document.   | Annotation | Effect | | --- | --- | | [distance](#distance) | Tune closeness using `distance`. |   For multi-value fields, setting [element-gap](schema-reference.html#rank-element-gap) for the field in the rank profile enables distance calculation between adjacent elements. |
| onear | `onear()` (ordered near) is like `near()`, but also requires the terms in the document having the same order as given in the function (i.e. it is a phrase allowing other words interleaved). With distance 1, `onear()` has the same semantics as `phrase()`.   | Annotation | Effect | | --- | --- | | [distance](#distance) | Tune closeness using `distance`. |   For multi-value fields, setting [element-gap](schema-reference.html#rank-element-gap) for the field in the rank profile enables distance calculation between adjacent elements. |
| sameElement | *sameElement()* is an operator that requires the terms to match within the same struct element in an array or a map field. Example:   ``` struct person {     field first_name    type string {}     field last_name     type string {}     field year_of_birth type int {} }  field persons type array<person> {     indexing: summary     struct-field first_name    { indexing: attribute }     struct-field last_name     { indexing: attribute }     struct-field year_of_birth { indexing: attribute } } field identities type map<string, person> {     indexing: summary     struct-field key                 { indexing: attribute }     struct-field value.first_name    { indexing: attribute }     struct-field value.last_name     { indexing: attribute }     struct-field value.year_of_birth { indexing: attribute } } ```   With normal *AND* the query `persons.first_name AND persons.last_name` will normally not give you what you want. It will match if a document has a *persons* element with a matching *first_name* *AND* any element with a matching *last_name*. So you will get a lot of false positives since there is nothing limiting them to the same element. However, that is what *sameElement* ensures. Note that *sameElement* uses *AND* to connect the operands. To use *OR*, use multiple sameElement operators using logical OR.   ``` where persons contains sameElement(first_name contains 'Joe', last_name contains 'Smith', year_of_birth < 1940) ```   The above returns all documents containing Joe Smith born before 1940 in the *persons* array.  Searching in a map is similar to searching in an array of struct. The difference is that you have an extra synthetic struct with the field members *key* and *value*. The above example with the *identities* map looks like this:   ``` where identities contains sameElement(key contains 'father', value.first_name contains 'Joe', value.last_name contains 'Smith', value.year_of_birth < 1940) ```   The above returns all documents that have tagged Joe Smith born before 1940 as a 'father'. The importance here is using the indirection of *key* and *value* to address the keys and the values of the map. |
| equiv | If two terms in the same field should give exactly the same behavior when matched, the `equiv()` operator behaves like a special case of `or`.   ``` where fieldName contains equiv("A","B") ```   In many cases, the OR operator will give the same results as an EQUIV. The matching logic is exactly the same, and an OR does not have the limitations that EQUIV does (below). The difference is in how matches are visible to ranking functions. All words that are children of an OR count for ranking. When using an EQUIV however, it looks like a single word:   * Counts as only +1 for queryTermCount * Counts as 1 word for completeness measures * Proximity will not discriminate different words inside the EQUIV * Connectivity can be set between the entire EQUIV and the word before and after * Items inside the EQUIV are not directly visible to ranking features,   so weight and connectivity on those will have no effect   Limitations on how `equiv` can be used in a query:   * `equiv` may not appear inside a phrase * It may only contain `TermItem` and `PhraseItem` instances.   Operators like `and` cannot be placed inside `equiv` * `PhraseItems` inside `equiv` will rank like as if they have size 1   Learn how to use [equiv](../query-rewriting.html#equiv). |
| uri | Used to search for urls indexed using the [uri field type](schema-reference.html#uri).   ``` where myUrlField contains uri("vespa.ai/foo") ```   Various subfields are supported to search components of the URL, see the field type definition.   | Annotation | Effect | | --- | --- | | [startAnchor](#startanchor) | Anchor uri.hostname at start. | | [endAnchor](#endanchor) | Anchor uri.hostname at end. | |
| fuzzy | [Levenshtein](https://en.wikipedia.org/wiki/Levenshtein_distance) edit distance search within a string [attribute](schema-reference.html#attribute).   ``` where myStringAttribute contains ({prefixLength:1, maxEditDistance:2}fuzzy("parantesis")) ```   Annotations below are configuring `fuzzy`:   | Annotation | Effect | | --- | --- | | [maxEditDistance](#maxeditdistance) | An inclusive upper bound of edit distance between query and string attribute (default is 2). | | [prefixLength](#prefixlength) | Number of characters that are considered frozen, so the fuzzy match will be performed only with the suffix left. Default is 0 (i.e. `fuzzy` will match across whole query) | | [prefix](#prefix) | If `true`, a string is considered a match when it's possible to transform a *prefix* of the candidate string to the query string using at most `maxEditDistance` edits. See [fuzzy prefix match](../text-matching.html#fuzzy-prefix-match). Default is `false`, which means that the entire string is considered. |   Find an example in [text matching](../text-matching.html#fuzzy-match). {% include important.html content="Only string [attribute](schema-reference.html#attribute) fields in [documents](services-content.html#document) are supported (single, array or weightedset). Matching is optimized internally when `maxEditDistance` is 1 or 2. Setting [prefixLength](#prefixlength) greater than 0 narrows the match for the [fast-search](schema-reference.html#attribute), greatly reducing the number of terms that must be considered."%} |
| matches | Regular expression match is supported using [posix extended syntax](https://en.wikibooks.org/wiki/Regular_Expressions/POSIX_Extended_Regular_Expressions), with the limitation that it is **case-insensitive**.  Example matching both `madonna`, `madona` and with any number of `n`s:   ``` where attribute_field matches "mado[n]+a" ```   Find more examples in the [text matching](../text-matching.html#regular-expression-match) guide. {% include important.html content="Only [attribute](schema-reference.html#attribute) fields in [documents](services-content.html#document) is supported. It is not optimized for performance. Having a prefix using the `^` will be faster than not having one. Additionally, fields that serve as both attributes and indexes are not compatible. "%} |
| userInput | *userInput()* is a robust way of mixing user input and a formal query. The argument is an unprocessed text string from a user or LLM, which is parsed into query items as controlled by annotations:   ``` yql=select * from sources * where userInput('some text') ```   The argument can be given as a reference using "@parameterName":   ``` yql=select * from sources * where userInput(@text)&text=some text ```   Both of these will result in the query   ``` select * from sources * where weakAnd(default contains "some", default contains "text") ```   The default behavior may be overridden by annotations:   ``` yql=select * from sources * where ({grammar.syntax:'none',grammar.tokenization:'linguistics',grammar.composite:'near',distance:3}userInput('some text')) ```  | Annotation | Effect | | --- | --- | | [grammar](#grammar) | How to parse the user input. For any value of `grammar` other than `raw` or `segment`, only the following annotations are applied:   * [defaultIndex](#defaultindex) * [targetHits](#targethits) (for weakAnd)* [distance](#distance) (for near/oNear)* [ranked](#ranked) * [filter](#filter) * [stem](#stem) * [normalizeCase](#normalizecase) * [accentDrop](#accentdrop) * [usePositionData](#usepositiondata)   E.g. if annotating `userInput` with `phrase`, a `filter` annotation will have effect, but not `language`.  See [isYqlDefault](query-api-reference.html#model.type.isYqlDefault) on setting a default grammar in a request/query profile. | | [defaultIndex](#defaultindex) | Same as [model.defaultIndex](query-api-reference.html#model.defaultindex) in the query API - [example using a fieldset](/en/query-api.html#using-a-fieldset). | | [language](#language) | Language setting for the linguistics treatment of this userInput() call. | | [allowEmpty](#allowempty) | Whether to allow empty input for query parsing and search terms. |   In addition, other annotations, like [stem](#stem) or [ranked](#ranked), will take effect as normal.  More examples can be found in the [query API](../query-api.html#input-examples) guide. |
| userQuery | *userQuery()* reads from [model.queryString](query-api-reference.html#model.querystring) and parses the query using [simple query language](simple-query-language-reference.html). If set, [model.filter](query-api-reference.html#model.filter) is combined with *model.queryString* before the parsing.  The user query is first parsed, then the resulting tree is inserted into the corresponding place in the YQL query tree. Example:   ``` $ vespa query 'select * from sources * where vendor contains "brick and mortar" AND price < 50 AND userQuery()' \   query="abc def -ghi" \   type=all ```   This evaluates to a query where:   * the numeric field *price* must be less than 50 * *vendor* must match *brick and mortar* * the default index must contain the two terms *abc* and *def*,   *and not* contain *ghi*.   Use [model.defaultIndex](query-api-reference.html#model.defaultindex) to specify a field or fieldset if not using *default* - see [example](/en/query-api.html#using-a-fieldset). |
| rank | The first, and only the first, argument of the *rank()* function determines whether a document is a match, but all arguments are used for calculating rank features. The `rank` operator is useful for boosting documents based on the presence of certain terms without impacting matching or retrieval logic.   ``` where rank(a contains "A", b contains "B", c contains "C") ```   It's also useful in hybrid search use cases. See [blog post](https://blog.vespa.ai/redefining-hybrid-search-possibilities-with-vespa/) for usage examples. For example, retrieve using the [nearestNeighbor](#nearestneighbor) query operator as the first argument and have matching features calculated for the other arguments.   ``` where rank(nearestNeighbor(field, queryVector), a contains "A", b contains "B", c contains "C") ``` |
| in | The *in* operator is used to match a set of values in an integer or string field. A document is considered a match when at least one of the values matches the content of the field. This is an optimized shorthand for multiple OR conditions, and is similar to the IN operator in SQL. Available since {% include version.html version="8.293.15" %}. Example:   ``` where integer_field in (10, 20, 30) where string_field in ('germany', 'france', 'norway') ```  Where `string_field` is a field with `match:word`. There is no [linguistic](/en/linguistics.html) processing like tokenization or stemming of the string values used in the *in* operator except lowercasing. See string [match](schema-reference.html#match).  ``` field string_field type string {     indexing: summary | index # or attribute     match: word     rank:filter     attribute: fast-search # if attribute   } ```   Using the *in* operator against string fields with `match:text` will cause recall issues because the field contents will be tokenized during indexing while the *in* operator does not tokenize the values.  The argument before *in* is the name of the field or [fieldset](schema-reference.html#fieldset) to search. The argument after *in* is a comma-separated list of values, enclosed in parentheses. String values must be single or double-quoted if passed inline in YQL  For multi-value fields (like arrays), the *in* operator works by checking if any element in the array matches any of the values in the set. This is similar to SQL's IN operator but more streamlined for array comparisons. Example:   ``` where integer_array_field in (10, 20, 30) ```   If integer_array_field = [5, 10, 15], it will match because 10 is in the array. Similarly, if integer_array_field = [20, 25, 30], it will match because both 20 and 30 are in the array.  For faster query parsing use [parameter substitution](#parameter-substitution) to submit the values as an additional request parameter. Quoting of string values are optional. Example:   ``` where integer_field in (@integer_values)&integer_values=10,20,30 where string_field in (@string_values)&string_values=germany,france,norway ```   The *in* operator acts as a single term in the query tree, and does not provide any match information for text ranking features.  For a discussion of usage and examples refer to:   * [multivalue query operators](../multivalue-query-operators.html#in-example) * [multi-lookup set filtering](../performance/feature-tuning.html#multi-lookup-set-filtering) * [in operator system test](https://github.com/vespa-engine/system-test/tree/master/tests/search/in_operator)  | Field type | Singlevalue or [multivalue](../schemas.html#multivalue-field) [attribute or index field](../schemas.html#indexing) with basic type [byte](schema-reference.html#byte), [int](schema-reference.html#int), [long](schema-reference.html#long) or [string](schema-reference.html#string). String fields must have `match:word` or `match:exact`. | | Query model | A set of values/tokens. | | Matching | Documents where the field contains at least one of the values in the query. | | Ranking | None. | | Java Query Item | [NumericInItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/NumericInItem.html) and [StringInItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/StringInItem.html). |   {% include important.html content="When using the *in* operator with an attribute field, set [fast-search](../attributes.html#fast-search) and [rank: filter](schema-reference.html#filter) for best possible performance. Always use `match:word` for string fields." %} |
| dotProduct | *dotProduct* calculates the dot product between the weighted set in the query and a weighted set field in the document as its rank score contribution:   ``` where dotProduct(description, {"a":1, "b":2}) ```   The result is stored as a [raw score](../multivalue-query-operators.html#raw-scores-and-query-item-labeling).  A normal use case is a collection of weighted tokens produced by an algorithm, to match against a corpus containing weighted tokens produced by another algorithm in order to implement personalized content exploration. See example usage of *dotProduct* in [practical performance guide](../performance/practical-search-performance-guide.html#multi-valued-query-operators).  Refer to [multivalue query operators](../multivalue-query-operators.html) for a discussion of usage and examples.  Keys must be single or double-quoted if passed inline in YQL - alternatively, use [parameter substitution](#parameter-substitution) to submit the weighted set with a simple format for faster query parsing - example: `where dotProduct(description, @myterms)`.   | Field type | Weighted set attribute with fast-search. Note: Also supported for regular attribute or index fields, but then with much weaker performance). | | Query model | Weighted set with {token, weight} pairs | | Matching | Documents where the weighted set field contains at least one of the tokens in the query. | | Ranking | Dot product score between the weights of the matched query tokens and field tokens. This score is available using [rawScore](rank-features.html#rawScore(field)) or [itemRawScore](rank-features.html#itemRawScore(label)) rank features. | | Java Query Item | [DotProductItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/DotProductItem.html) | |
| weightedSet | When using *weightedSet* to search a field, all tokens present in the searched field will be matched against the weighted set in the query. This means that using a weighted set to search a single-value attribute field will have similar semantics to using a normal term to search a weighted set field. The low-level matching information resulting from matching a document with a weighted set in the query will contain the weights of all the matched tokens in descending order. Each matched weight will be represented as a standard occurrence on position 0 in element 0.   ``` where weightedSet(description, {"a":1, "b":2}) ```   *weightedSet* has similar semantics to [equiv](#equiv), as it acts as a single term in the query. However, the restriction dictating that it contains a collection of weighted tokens directly enables specific back-end optimizations that improves performance for large sets of tokens compared to using the generic [equiv](#equiv) or [or](#or) operators.  Keys must be single or double-quoted if passed inline in YQL - alternatively, use [parameter substitution](#parameter-substitution) to submit the weighted set with a simple format for faster query parsing - example: `where weightedSet(description, @myterms)`.   | Field type | Singlevalue or [multivalue](../schemas.html#field) attribute or index field. (Note: Most use cases operates on a single value field). | | Query model | Weighted set with {token, weight} pairs. | | Matching | Documents where the field contains at least one of the tokens in the query. For filtering use cases we recommend using the [in operator](#in) instead, as it is simpler to use and has slightly better performance. | | Ranking | The operator will act as a single term in the back-end. The query term weight is the weight assigned to the operator itself and the match weight is the largest weight among matching tokens from the weighted set. This operator does not produce a raw score. Due to better ranking and performance we recommend using [dotProduct](#dotproduct) instead. | | Java Query Item | [WeightedSetItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/WeightedSetItem.html) | |
| wand | `wand` can be used to search for documents where weighted tokens in a field matches a subset of weighted tokens in the query. At the same time, it internally calculates the dot product between token weights in the query and the field. `wand` is guaranteed to return the top-k hits according to its internal dot product rank score. It is an operator that scales adaptively from [or](#or) to [and](#and).  Note that total hit count becomes inaccurate when using wand.  `wand` optimizes the performance of using multiple threads per search in the backend, and is also called *Parallel Wand*.  `wand` also allows numeric arguments, then the search argument is an array of arrays of length two. In each pair, the first number is the search term, the second its weight:  ``` where wand(description, [[11,1], [37,2]]) ```   Keys must be single or double-quoted if passed inline in YQL - alternatively, use [parameter substitution](#parameter-substitution) to submit the weighted set with a simple format for faster query parsing - example: `where wand(description, @myterms)`.   | Annotation | Effect | | --- | --- | | [scoreThreshold](#scorethreshold) | Minimum rank score for hits to include. | | [targetHits](#targethits) | Wanted number of hits exposed to the real first-phase ranking function per content node. |  ``` where ({scoreThreshold: 0.13, targetHits: 7}wand(description, {"a":1, "b":2})) ```   Refer to [using wand](../using-wand-with-vespa.html) for introduction to the WAND algorithm and example usage of *wand* in [practical performance guide](../performance/practical-search-performance-guide.html#multi-valued-query-operators).   | Field type | Weighted set attribute with fast-search. Note: Also supported for regular attribute or index fields, but then with much weaker performance). | | Query model | Weighted set with {token, weight} pairs. | | Matching | Documents where the weighted set field contains at least one of the tokens in the query and where the internal dot product score for this document, is larger than the worst among the current top-k best hits. This means that more than top-k documents are matched and returned for ranking. It also means that many documents are skipped, even they match several tokens in the query because the dot product score is too low. This skipping makes *wand* faster than [dotProduct](#dotproduct) in some cases. | | Ranking | Dot product score between the weights of the matched query tokens and field tokens. This score is available using [rawScore](rank-features.html#rawScore(field)) or [itemRawScore](rank-features.html#itemRawScore(label)) rank features. Note that the top-k best hits are only guaranteed to be returned when using this internal score as the final ranking expression. | | Java Query Item | [WandItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/WandItem.html) | |
| weakAnd | `weakAnd` is sometimes called *Vespa Wand*. Unlike [wand](#wand), it accepts arbitrary word matches (across arbitrary fields) as arguments. Only a limited number of documents are returned for ranking (default is 100), but it does not guarantee to return the best k hits. This function can be seen as an optimized [or](#or):   ``` where weakAnd(a contains "A", b contains "B") ```  | Annotation | Effect | | --- | --- | | [targetHits](#targethits) | Wanted number of hits exposed to the real first-phase ranking function per content node. |  ``` where ({targetHits: 7}weakAnd(a contains "A", b contains "B")) ```   Unlike [wand](#wand), `weakAnd` can be used to search across several fields of various types, but it does NOT guarantee to return the top-k best number of hits. It can however be combined with any ranking expression. Keep in mind that this expression should correlate with its simple internal ranking score that uses query term weight and inverse document frequency for matching terms.  Refer to [using wand](../using-wand-with-vespa.html) for a usage and examples.   | Field type | Multiple fields of all types (both attribute and index). | | Query model | Arbitrary number of query items searching across different fields. | | Matching | Documents that matches at least one of the tokens in the query and where the internal operator score for this document is larger than the worst among the current top-k best hits. As with [wand](#wand), this means that typically more than top-k documents are matched and a lot of documents are skipped. | | Ranking | Internal ranking score based on query term weight and inverse document frequency for matching terms to find the top-k hits. This score is currently not available to the ranking framework. Matching terms are exposed to the ranking framework (same as when using [and](#and) or [or](#or)), so an arbitrary ranking expression can be used in combination with this operator. Note that the ranking expression used should correlate with this internal ranking score. [bm25](rank-features.html#bm25), [nativeFieldMatch](rank-features.html#nativeFieldMatch) and [nativeDotProduct](rank-features.html#nativeDotProduct(field)) rank features are good starting points. | | Java Query Item | [WeakAndItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/WeakAndItem.html) | |
| geoLocation | `geoLocation` matches a [position](schema-reference.html#position) inside a geographical circle, specified as latitude, longitude, and a maximum distance (radius). See also [geoBoundingBox](#geoboundingbox). Example:   ``` where geoLocation(myfieldname, 63.5, 10.5, "200 km") ```   In this example we search for documents near 63.5° north, 10.5° east, and within a 200 km radius. So a document with a "myfieldname" position in Trondheim, Norway at N63°25'47;E10°23'36 would match. The first parameter is the name of the attribute field. The second parameter is the latitude (positive for north, negative for south). The third parameter is the longitude (positive for east, negative for west). The fourth parameter must be a string specifying the radius and its units, where the supported units/suffixes include "km", "m" (abbr. for meters), "miles", "mi" (abbr. for miles), "deg" (abbr. for degrees) and "d" (contextual abbr. for degrees). The "deg" / "d" unit / suffix gives radius the same units as latitude. Any negative number for radius (e.g. "-1 m") is interpreted as an "infinite" radius, letting any geographical position at all match the geoLocation operator.  The position attribute in the schema could look like:   ``` field myfieldname type position {     indexing: attribute | summary } ```   Arrays of positions are also possible:   ``` field myfieldname type array<position> {     indexing: attribute } ```  | Annotation | Effect | | --- | --- | | [label](#label) | Label for referring to this term during ranking. |   Properties:   | Field type | position attribute (single-valued or array). | | Query parameters | Field name, latitude, longitude, radius. | | Matching | Returns documents inside the given geo circle. | | Ranking | Use `closeness(myfieldname)`, or `distance(myfieldname)` in ranking calculations. See [closeness](rank-features.html#closeness(name)) and [distance](rank-features.html#distance(name)) documentation. | | Java Query Item | [GeoLocationItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/GeoLocationItem.html) | |
| geoBoundingBox | `geoBoundingBox` requires a [position](schema-reference.html#position) to be inside a geographical rectangle; specified as 4 numbers (in degrees). The 4 numbers must be in a specific order: south-western corner (minimum latitude, minimum longitude) followed by north-eastern corner (maximum latitude, maximum longitude). Examples:   ``` where geoBoundingBox(myfieldname, 63.25, 10.01, 63.45, 10.61) where geoBoundingBox(myfieldname, -23.12, -43.85, -22.59, -42.89) ```   In the first example we search for documents inside a rectangular map view around Trondheim, Norway. So a document with a "myfieldname" position at [63°25'50"N 10°23'42"E](https://www.google.com/maps/place/63%C2%B025'50.0%22N+10%C2%B023'42.0%22E) would match. The second example surrounds [Rio de Janeiro](https://www.google.com/maps/place/22%C2%B059'13.0%22S+43%C2%B012'10.0%22W), Brazil.  * The first parameter is the name of the attribute field. * The 2nd parameter is the minimum (southern) latitude (positive for north, negative for south). * The 3rd parameter is the minimum (western) longitude (positive for east, negative for west). * The 4th parameter is the maximum (northern) latitude (positive for north, negative for south). * The 5th parameter is the maximum (eastern) longitude (positive for east, negative for west).  See the [geoLocation](#geolocation) operator for more details about positions. Note that there is no ranking contribution from this operator; if you want to get the distance to the center of the box, you need an additional `geoLocation` item with that point.  Properties:   | Field type | position attribute (single-valued or array). | | Query parameters | Field name, southern, western, northern, eastern limits. | | Matching | Returns documents inside the given geo bounding box. | | Ranking | None. | | Java Query Item | [GeoLocationItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/GeoLocationItem.html) | |
| nearestNeighbor | `nearestNeighbor` matches the top-k nearest neighbors in a multidimensional vector space. Points in the vector space are specified as [tensors](../tensor-user-guide.html) with one indexed dimension, where the size of that dimension is equal to the dimensionality of the vector space.  The document vectors are stored in a [tensor field attribute](schema-reference.html#tensor), and the query vector is sent with the query request. The following tensor field types are supported:   * Single vector per document: Tensor type with one indexed dimension.   Example: `tensor<float>(x[3])` * Multiple vectors per document: Tensor type with one or more mapped dimensions and one indexed dimension.   Examples: `tensor<float>(m{},x[3])`, `tensor<float>(m{},n{},x[3])`   Euclidean distance is used as the default [distance metric](schema-reference.html#distance-metric) and the exact nearest neighbors are returned. When storing multiple vectors per document, the vector that is closest to the query vector is used when calculating the distance between the document and the query. If an [HNSW index](schema-reference.html#index-hnsw) is specified on the tensor field, the approximate nearest neighbors are returned. Example:   ``` where ({targetHits: 10}nearestNeighbor(doc_vector, query_vector))&input.query(query_vector)=[3,5,7]&ranking=semantic ```   In this example we search for the top 10 nearest neighbors in a 3-dimensional vector space. *targetHits* specifies the top-k nearest neighbors to expose to a user defined `semantic` [rank profile](../ranking.html). The [targetHits](#targethits) annotation is required. The first parameter of *nearestNeighbor* is the name of the tensor field attribute containing the document vectors (*doc_vector*).  The second parameter is the name of the tensor sent with the query request (*query_vector*). Specifying *query_vector* as the name means the query request must set this tensor as *input.query(query_vector)* - see the [reference](query-api-reference.html#ranking.features). The tensor type of the **input query vector must be defined** in the rank profile:   ``` rank-profile semantic {     inputs {         query(query_vector) tensor<float>(x[3])     }     first-phase: closeness(field, doc_vector) } ```   Also see [defining query feature types](../ranking-expressions-features.html#query-feature-types). Failure to define the query input tensor in the schema will fail the request:   ```   Expected 'query(query_vector)' to be a tensor, but it is the string '[3,5,7]' ```   The document tensor field attribute is defined as follows:   ``` field doc_vector type tensor<float>(x[3]) {     indexing: attribute | summary } ```   The above example does not define HNSW `index` and the search for neighbors will be exact.  See [Nearest Neighbor Search](../nearest-neighbor-search.html), [Approximate Nearest Neighbor Search using HNSW Index](../approximate-nn-hnsw.html) and [Nearest Neighbor Search Guide](../nearest-neighbor-search-guide.html) for more detailed examples.   | Annotation | Effect | | --- | --- | | [targetHits](#targethits) | This annotation is required, and specifies the number of hits nearestNeighbor should expose to [ranking](../ranking.html). Note that more or less hits might actually be produced. *targetHits* is per node involved in the query. | | [approximate](#approximate) | The optional `approximate` annotation may be set to `false` to not use an approximate [HNSW index](schema-reference.html#index-hnsw). This is especially useful to compare exact and approximate results in order to perform tuning of HNSW parameters. This annotation is default `true` when an HNSW index is specified, otherwise it is always `false`. Setting this to `false` might trigger [graceful query degradation](../graceful-degradation.html). Adjust [timeout](#timeout) as needed. | | [hnsw.exploreAdditionalHits](#hnsw-exploreadditionalhits) | Tune how many extra nodes in the HNSW graph (in addition to `targetHits`) that should be explored before selecting the best hits. Default is `0`. Increasing this parameter increases the accuracy of the approximate search, at the cost of more distance computations. | | [label](#label) | Use to mark the query operator with a label that can be referred to from the ranking expression in the rank profile. See the [closeness](rank-features.html#closeness(dimension,name)) and [distance](rank-features.html#distance(dimension,name)) rank features. Useful when having multiple `nearestNeighbor` operators in the same query, e.g., when the schema has multiple vector fields. See [nearest neighbor search guide](../nearest-neighbor-search-guide.html#multiple-nearest-neighbor-search-operators-in-the-same-query) for usage example. | | [distanceThreshold](#distancethreshold) | Use to filter out hits with a higher distance than a threshold. See [nearest neighbor search guide](../nearest-neighbor-search-guide.html#strict-filters-and-distant-neighbors) for usage example. |   Properties:   | Field type | Tensor attribute with one indexed dimension of size N or with one or more mapped dimensions and one indexed dimension of size N. | | Query model | Tensor with one indexed dimension of size N. | | Matching | Returns documents where the distance (according to the [distance metric](schema-reference.html#distance-metric) used) between the document tensor and the query tensor is less than the greatest distance among the current top-k best hits. This means that typically more than top-k documents are matched and returned for ranking. This is similar to the behavior of [wand](#wand). When an [HNSW index](schema-reference.html#index-hnsw) is used, the top-k best hits are calculated before regular matching happens, taking the rest of the query filters into account. | | Ranking | Calculates a closeness score that is defined as `1 / (1 + d)`, where `d` is the distance between the document tensor and query tensor. This score is available using [rawScore](rank-features.html#rawScore(field)), [itemRawScore](rank-features.html#itemRawScore(label)), or [closeness](rank-features.html#closeness(dimension,name)) rank features. The raw distance is available using the [distance](rank-features.html#distance(dimension,name)) rank feature. | | Java Query Item | [NearestNeighborItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/NearestNeighborItem.html) | |
| nonEmpty | *nonEmpty* takes as its only argument an arbitrary search expression. It will then perform a set of checks on that expression. If all the checks pass, the result is the same expression, otherwise the query will fail. The checks are as follows:   1. No empty search term 2. No empty operators, like phrases without terms 3. No null markers (NullItem) from e.g. failed query parsing  ``` yql=select * from sources * where bar contains "a" and nonEmpty(bar contains "bar" and foo contains @foo)&foo= ```   Note how "foo" is empty in this case, which will force the query to fail. If "foo" contained a searchable term, the query would not have failed. |
| predicate | *predicate()* specifies a predicate query - see [predicate fields](../predicate-fields.html). It takes three arguments: the predicate field to search, a map of attributes, and a map of range attributes:   ``` where predicate(predicate_field,{"gender":"Female"},{"age":20L}) ```   Due to a quirk in YQL-parsing, one cannot specify an empty map, use the number 0 instead.   ``` where predicate(predicate_field,0,{"age":20L}) ``` |
| true | Matches all documents of any type. Care must be taken when using this since processing all documents as matches is expensive. At minimum, consider restricting to only one schema where you know the corpus isn't too big, see the [model.restrict](query-api-reference.html#model.restrict) URL parameter. |
| false | Does not match any document at all. Not useful in itself, but could potentially be used as a placeholder in the query tree. |

## order by

Sort using `order by`.
Add `asc` or `desc` after the name of an
[attribute](../attributes.html) to set sort order -
ascending order is default. Add another sorting attributes to get a secondary sort, that will be a tiebreaker for the
primary ordering attribute. This is typically used to get a predictable ordering when the primary ordering attribute
has the same value for multiple documents.

```
where title contains "madonna" order by price asc, releasedate desc
```

Sorting function, locale and strength are defined using the annotations "function", "locale" and "strength", as in:

```
where title contains "madonna" order by {function: "uca", locale: "en_US", strength: "IDENTICAL"}other desc, {function: "lowercase"}something
```

{% include note.html content="[match-phase](schema-reference.html#match-phase)
is enabled when sorting - refer to the [sorting reference](sorting.html)."%}

The [rank profile](../ranking.html) determines the rank score each document will get.
Results are ordered by that value by default, but `order by` overrides that ordering.
Vespa does not optimize away the rank score computation in this case, it is still executed, even if the model score is thrown away. Use the built-in rank-profile *unranked* for optimal performance of sorting queries.

To do a primary ordering on the rank score, and a secondary sort on an attribute, use `'[relevance]'` as the first order by attribute.
See [Special sorting attributes](sorting.html#special-sorting-attributes) for more details.

| Annotation | Effect |
| --- | --- |
| [function](#function) | Sort function, default UCA. |
| [locale](#locale) | Locale identifier for the [UCA sort function](#function). |
| [strength](#strength) | Strength setting for the [UCA sort function](#function). |

## limit / offset

To specify a slice / limit the number of hits returned / do pagination,
use `limit` and/or `offset`. This can also be controlled by using
[native execution parameters](query-api-reference.html#native-execution-parameters).

{% include important.html content='Values set in YQL takes precedence over
[hits/offset](query-api-reference.html#hits).
Values for hits/offset in query profiles are also overridden by YQL,
e.g., `limit 100` overrides `<field name="hits" overridable="false">50</field>`.' %}

Limited by [maxHits](query-api-reference.html#hits) (default 400)
and [maxOffset](query-api-reference.html#offset) (default 1000) -
these can be configured in a [queryProfile](../query-profiles.html).

Example: This returns two hits (if there are sufficiently many hits matching the query),
skipping the 29 first documents

```
where title contains "madonna" limit 31 offset 29
```

## timeout

Set query timeout in milliseconds using `timeout`. This can also be controlled by using the native
execution parameter [timeout](query-api-reference.html#timeout). YQL specified values takes precedence.:

```
where title contains "madonna" timeout 70
```

Only literal numbers are valid, i.e. setting another unit is not supported.

{% include note.html content='The value is in milliseconds,
whereas the native execution parameter [timeout](query-api-reference.html#timeout) is in seconds' %}

## Parameter substitution

Use parameter substitution to separate the YQL string from user input values.
E.g., the [userInput(value)](#userinput) query operator
supports parameter substitution for the `value` parameter:

```
... where userInput(@userinput)&userinput=free+text
```

The query operators [field in (value)](#in),
[dotProduct(field, value)](#dotproduct),
[weightedSet(field, value)](#weightedset) and [wand(field, value)](#wand)
support parameter substitution for the `value` parameter.

The `value` string can be passed in one of the following forms
(quotes can be skipped unless the keys contain `,` or `:`.):
* List: `value, ...`.
  For the [in](#in) operator only.
* Array: `[[key, value], ...]`.
  For [dotproduct](#dotproduct), [weightedset](#weightedset) and [wand](#wand).
* Map: `{key: value, ...}`.
  For [dotproduct](#dotproduct), [weightedset](#weightedset) and [wand](#wand).

See the [query API guide](/en/query-api.html#parameter-substitution) for examples.

## Annotations

Terms and phrases can be annotated to manipulate the behavior.
Add an annotation using `{}`:

```
where text contains ({distance: 5}near("a", "b")) and text contains ({distance:2}near("c", "d"))
```

Note that the annotation is enclosed by parentheses to scope the annotation to the operator.

All annotations are supported by the string arguments to functions like
and phrase() and near() and also the string argument to the "contains" operator.
Some annotations are also supported by the functions which are handled like leaf nodes internally in the query tree:
phrase(), near(), onear(), range(), equiv(), dotProduct(), weightedSet(), weakAnd(), wand() and nearestNeighbor().

Refer to [SelectTestCase.java](https://github.com/vespa-engine/vespa/blob/master/container-search/src/test/java/com/yahoo/select/SelectTestCase.java) for sample usage.

| Annotation | Default | Values | Description |
| --- | --- | --- | --- |
| accentDrop | true | boolean | Remove accents from this term if it is the setting for this field. Refer to [linguistics](../linguistics.html#normalization). |
| allowEmpty | false | boolean | Whether to allow empty input for query parsing and query terms in [userInput](#userinput). If `true`, a NullItem instance is inserted in the proper place in the query tree. If `false`, the query will fail if the user provided input can not be parsed or is empty. |
| andSegmenting |  | true|false | Force phrase or AND operator if re-segmenting (e.g. in stemming) this term results in multiple terms. Default is choosing from language settings. |
| annotations |  | map | Map of `string: string`. Custom annotations. No special semantics inside the YQL layer. Example:   ``` annotations : {cox: "another"} ``` |
| approximate |  | boolean | Used in [nearestNeighbor](#nearestneighbor). The optional *approximate* annotation may be set to `false` to disallow usage of an approximate [HNSW index](schema-reference.html#index-hnsw). This is especially useful to compare exact and approximate results in order to perform tuning of other parameters. This annotation is default `true` when an HNSW index is specified, otherwise it is always `false`. |
| ascending |  | boolean | Ascending hit order. Used by [hitLimit](#hitlimit). |
| bounds | `closed` | enum | A [numeric](#numeric) interval is by default a closed interval. If the lower bound is exclusive, set to `leftOpen`. If the upper bound is exclusive, set to `rightOpen`. If both bounds are exclusive, set the annotation to `open`. Example:   ``` where ({bounds:"rightOpen"}range(year, 2000, 2018)) ``` |
| connectivity |  | map | Map of `id: int, weight: double` of explicit connectivity between this item and the item with the given [id](#id) - see [text matching and ranking](../nativerank.html#weight-significance-and-connectedness). Example:   ``` connectivity: {id: 4, weight: 0.8} ``` |
| descending |  | boolean | Descending hit order. Used by [hitLimit](#hitlimit). |
| defaultIndex | `default` | Any searchable field in the schema. | Used by [userInput](#userinput). Same as [model.defaultIndex](query-api-reference.html#model.defaultindex) in the query API. If [grammar](#grammar) is set to `raw` or `segment`, this will be the field searched. |
| distance | 2 | int | The *distance*-annotation sets the maximum position difference to count as a match, see [near](#near) / [onear](#onear). The default distance is 2, meaning match if the words have up to one separating word.   ``` where text contains ({distance: 5}near("a", "b")) ``` |
| distanceThreshold | +infinity | double | Used in [nearestNeighbor](#nearestneighbor). The `distanceThreshold` annotation may be used to filter away hits with a higher distance than the given threshold from the results. Note that one will never get more hits with `distanceThreshold` than you would get without it - to get more hits, increase [targetHits](#targethits), too. The units for the threshold depends on the [distance metric](schema-reference.html#distance-metric) used. |
| endAnchor | true | boolean | The `hostname` subfield of [uri](#uri) supports anchoring to the start and/or end of the hostname, controlled by the `startAnchor` and `endAnchor` annotations. Anchoring to the end is on by default while anchoring to the start is not. Hence   ``` where myUrlField.hostname contains uri("vespa.ai") ```   will match *vespa.ai* and *docs.vespa.ai*, while   ``` where myUrlField.hostname contains ({startAnchor: true}uri("vespa.ai")) ```   will only match vespa.ai. |
| filter | false | boolean | Regard this term as a "filter" term and not a term from the end user. Terms that are annotated with "filter:true" are not bolded. See also [model.filter](query-api-reference.html#model.filter). Bolding of terms is controlled by [schema:bolding](schema-reference.html#bolding). |
| function |  |  | Default sort function for strings is `uca`. Field sort specification can be configured in the [schema](schema-reference.html#sorting), values in the query overrides the schema settings.  Numeric fields are numerically sorted.   | Function | Description | | --- | --- | | `uca` | This sorting is based on the [icu](https://icu.unicode.org/) library that follows the [Universal Collation Algorithm](https://unicode.org/reports/tr10/). The specifications of [locale](https://unicode-org.github.io/icu-docs/apidoc/dev/icu4j/com/ibm/icu/util/ULocale.html) and [strength](https://unicode-org.github.io/icu-docs/apidoc/dev/icu4j/com/ibm/icu/text/Collator.html) are identical to how [icu](https://icu.unicode.org/) specifies them.  Both [locale](#locale) and [strength](#strength) are optional, however `strength` requires `locale`.  The [locale](#locale) query annotation will override locale-setting in the [schema](schema-reference.html#sorting). If `locale` is missing from both, the `lowercase` function will be used by default. | | `lowercase` | This improves the sorting by first lowercasing and normalising the strings before sorting. This is slightly more correct and might be enough for the use case. It is not that much more costly than `raw` sort, and less expensive than `uca`. | | `raw` | Raw byteorder is a simple and fast ordering based on memcmp of utf8 for strings and correct sort order compliant binary rep for other fields is done. However, that is not correct for anything except computers, looking only at the binary representation. | |
| grammar | `weakAnd` | `raw`, `segment` and all values accepted for the [model.type](query-api-reference.html#model.type) argument in the query API. | How to parse [userInput](#userinput). `raw` will treat the user input as a string to be matched without any processing, `segment` will do a first pass through the linguistic libraries, while the rest of the values will treat the string as a query to be parsed. The individual model.type settings can also be set, using `grammar.composite`, `grammar.tokenization`, and `grammar.syntax`, refer to the [model.type](query-api-reference.html#model.type) documentation.  See also [userInput examples](../query-api.html#input-examples). |
| hitLimit |  | int | [Numeric](#numeric) operations support `hitLimit`. This is used for *capped range search*. An alternative to using negative and positive values for hitLimit is always using a positive number of hits (as a negative number of hits does not make much sense) and combine this with either of the [ascending](#ascending) and [descending](#descending) annotations (but not both). Example: `{hitLimit: 38, descending: true}` would be equivalent to setting it to -38, i.e. only populate with 38 hits and start from upper boundary, i.e. descending order.  Note that `hitLimit` will limit the number of documents that are considered. This is a powerful optimisation that must be used with care, particularly in combination with other filters. The set of documents to be considered will be limited upfront by only selecting the N best according to the range query and the hitLimit annotation, for further query evaluation.  `hitLimit` is not exact, but "at least". In addition, it will only kick in if the attribute has [fast-search](schema-reference.html#attribute). It will look up the upper or lower bound in the range in the dictionary and scan in ascending or descending order and select entries until it has satisfied hitLimit. You will get all documents for all the dictionary entries selected.  See the [practical-search-performance-guide](../performance/practical-search-performance-guide.html#advanced-range-search-with-hitlimit) for an example. |
| hnsw.exploreAdditionalHits |  |  | Used in [nearestNeighbor](#nearestneighbor). When using an [HNSW index](schema-reference.html#index-hnsw), the optional `hnsw.exploreAdditionalHits` annotation can be used to tune how many extra nodes in the graph (in addition to `targetHits`) should be explored before selecting the best hits. Using a greater number here gives better quality, but worse performance. |
| id |  | int | Unique ID used for e.g. [connectivity](#connectivity). |
| implicitTransforms | true | boolean | Implicit term transformations (field defaults). If `implicitTransforms` is true, the settings for the field in the schema will be honored in term transforms, e.g. if the field has stemming, this term will be stemmed. If `implicitTransforms` is false, the search backend will receive the term exactly as written in the initial YQL expression. This is in other words a top level switch to turn off all other [stemming](../linguistics.html#stemming), accent removal, Unicode [normalizations](../linguistics.html#normalization) and so on. |
| label |  | string | Used by [geoLocation](#geolocation) and [nearestNeighbor](#nearestneighbor).  Label for referring to this term/operator during ranking. |
| language |  | RFC 3066 language code | Language setting for the linguistics handling of [userInput](#userinput), also see [model.language](query-api-reference.html#model.language) in the query API reference. |
| locale |  |  | Used by the [UCA sort function](#function). An identifier following [unicode locale identifiers](https://www.unicode.org/reports/tr35/#Unicode_Language_and_Locale_Identifiers), e.g. `en_US`. |
| maxEditDistance | 2 | int | Used in [fuzzy](#fuzzy). An inclusive upper bound of edit distance between query and string attribute. |
| nfkc | true | boolean | NFKC [normalization](../linguistics.html#normalization). |
| normalizeCase | true | boolean | Normalize casing of this term if it is the setting for this field. |
| origin |  | map | Map of `original: string, offset: int, length: int`. The (sub-)string which produced this term. Default unset. Example:   ``` origin: {original: "abc", offset: 1, length: 2} ``` |
| prefix | false | boolean | Do [prefix matching](schema-reference.html#prefix) for this term, e.g. search for "word*". |
| substring | false | boolean | Do substring matching for this word if available in the index. ("Search for "*word*".") Only supported for [streaming search](../streaming-search.html). |
| prefixLength | 0 | int | Used in [fuzzy](#fuzzy). Number of characters that are considered frozen, so the fuzzy match will be performed with the suffix left. |
| ranked | true | boolean | Include this term for ranking calculation. Setting ranked to false can speed up query evaluation. Read more about [schema reference](schema-reference.html#rank). [Example](../ranking-expressions-features.html#dumping-rank-features-for-specific-documents) |
| scoreThreshold |  | double | A threshold in [wand](#wand) for the minimum score of hits to include as matches. |
| significance |  | double | Significance value for text ranking features - see [text matching and ranking](../nativerank.html#weight-significance-and-connectedness). |
| startAnchor | false | boolean | See [endAnchor](#endanchor). |
| stem | true | boolean | Stem this term if it is the setting for this field. |
| strength | `PRIMARY` | * `PRIMARY` * `SECONDARY` * `TERTIARY` * `QUATERNARY` * `IDENTICAL` | Used by the [UCA sort function](#function). Default is `PRIMARY`, which only sorts on primary differentiating characteristics; this means that letters in uppercase/lowercase or with differences in accents only are considered equal. |
| suffix | false | boolean | Do *suffix matching* for this term, e.g. search for "*word". |
| targetHits | 100 | int | Used by [wand](#wand) and [weakAnd](#weakand), where the default is 100.  It is also used with [nearestNeighbor](#nearestneighbor), where it has no default - it must always be set, see examples in [nearest neighbor search](../nearest-neighbor-search.html).  It sets the wanted number of hits exposed to the real first-phase ranking function per content node. If additional second phase ranking with rerank-count is used, do not set `targetHits` less than the configured rank-profile's [rerank-count](schema-reference.html#secondphase-rerank-count). |
| usePositionData | true | boolean | Use term position data for text ranking features such as [nativeRank](../nativerank.html). This is *term* position, not to be confused with [geo searches](../geo-search.html). Setting "usePositionData:false" can improve query performance. |
| weight | 100 | int | Term weight, used in some text ranking features - see [text matching and ranking](../nativerank.html#weight-significance-and-connectedness).   ``` where title contains ({weight:200}"heads") ``` |

### Annotations of sub-expressions

Consider the following query:

```
select * from sources * where ({stem: false}(foo contains "a" and bar contains "b")) or foo contains ({stem: false}"c")
```

The "stem" annotation controls whether a given term should be stemmed if its
field is configured as a stemmed field (default is "true").
The "AND" operator itself has no internal API for whether its operands should be stemmed or not,
but we can still annotate as such,
because when the value of a given annotation is determined,
the expression tree is followed from the term in question and up through its ancestors.
Traversing the tree stops when a value is found (or there is nothing more to traverse).
In other words, none of the terms in this example will be stemmed.

How annotations behave may be easier to understand of expressing a boolean query in the style of an S-expression:

```
(AND term1 term2 (OR term3 term4) (OR term5 (AND term6 term7)))
```

The annotation scopes would then be as follows, i.e. annotations on
which elements will be checked when determining the settings for a given term:

| term1 | term1 itself, and the first AND |
| term2 | term2 itself, and the first AND |
| term3 | term3 itself, the first OR and the first AND |
| term4 | term4 itself, the first OR and the first AND |
| term5 | term5 itself, the second OR and the first AND |
| term6 | term6 itself, the second AND, the second OR and the first AND |
| term7 | term7 itself, the second AND, the second OR and the first AND |

## Query properties

Use YQL variable syntax to initialize words in phrases and as single terms.
This removes the need for caring about quoting a term in YQL, as well as URL quoting.
The term will be used *exactly* as it is in the URL.
As an example, look at a query with a YQL argument, and the properties
*animal* and *syntaxExample*:

```
yql=select * from sources * where foo contains @animal and foo contains phrase(@animal, @syntaxExample, @animal)&animal=panda&syntaxExample=syntactic
```

This YQL expression will then access the query properties *animal* and
*syntaxExample* and evaluate to:

```
select * from sources * where (foo contains "panda" AND foo contains phrase("panda", "syntactic", "panda"))
```

## YQL in query profiles

YQL requires quoting to be included in a URL.
Since YQL is well suited to application logic, while not being intended for end users,
a solution to this is storing the application's YQL queries into different
[query profiles](../query-profiles.html).
To add a default query profile, add *search/query-profiles/default.xml* to the
[application package](../application-packages.html):

```
<query-profile id="default">
    <field name="yql">select * from sources * where default contains "latest" or userQuery()</field>
</query-profile>
```

This will add *latest* as an *OR term* to all queries not having an explicit query profile parameter.
The important thing to note is how it is not necessary to URL-quote anything in the query profiles files.
They operate independently of the HTTP parsing as such.

## Query rewriting in Searchers

Searchers which modifies the textual YQL statement (not recommended)
should be annotated with `@Before("ExternalYql")`.
Searchers modifying query tree produced from an input YQL statement
should annotate with `@After("ExternalYql")`.

## Grouping

Group / aggregate results by adding a grouping expression after a `|` -
[read more](../grouping.html).

```
select * from sources * where sddocname contains 'purchase' | all(group(customer) each(output(sum(price))))
```
