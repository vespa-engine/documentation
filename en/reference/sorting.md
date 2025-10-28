---
# Copyright Vespa.ai. All rights reserved.
title: "Sorting Reference"
---

A sorting specification in a query consists of one or more
sorting expressions. Each sorting expression is an optional sort order
followed by an attribute name or a function over an attribute.
Multiple expressions are separated by a single SPACE character.

Using more than one sort expression will give you multilevel
sorting. In this case, the most significant expression is the
first, while subsequent expressions detail sorting within groups
of equal values for the previous expression.

```
Sorting       ::= SortExpr ( ' ' SortExpr )*
SortExpr      ::= [SortOrder] ( SortObject | MissingExpr )
MissingExpr   ::= MISSING '(' SortObject ',' MissingPolicy ')'
MissingPolicy ::= FIRST |
                  LAST |
                  AS ',' MissingValue
SortObject    ::= SortAttribute | Function
Function      ::= LOWERCASE '(' SortAttribute ')' |
                  RAW '(' SortAttribute ')' |
                  UCA '(' SortAttribute [ ',' Locale [ ',' Strength] ] ')'
MISSING       ::= 'missing'
FIRST         ::= 'first'
LAST          ::= 'last'
AS            ::= 'as'
LOWERCASE     ::= 'lowercase'
UCA           ::= 'uca'
RAW           ::= 'raw'
Locale        ::= An identifier following unicode locale identifiers, fx 'en_US'.
Strength      :: 'PRIMARY' | 'SECONDARY' | 'TERTIARY' | 'QUATERNARY' | 'IDENTICAL'
SortOrder     ::= '+' | '-'
SortAttribute ::= ID | ID.key | ID.value            /* A valid attribute name, with key/value appended for maps */
MissingValue  ::= QuotedString | Token
Token         ::= TokenChar*
TokenChar     ::= any non Delimiter
QuotedString  ::= '"' ( StringChar | '\' QuotedChar )* '"'
StringChar    ::= any non QuotedChar
Delimiter     ::= ' ' | ',' | '(' | ')' | QuotedChar
QuotedChar    ::= '\' | '"'
```

See [Geo search](../geo-search.html) for sorting by distance.
Refer to [YQL Vespa reference](query-language-reference.html#order-by) for how to set sorting parameters in YQL.

## Sort order

`+` denotes ascending sorting order,
while `-` gives descending order.
Ascending order is defined as lowest values first for numerical attributes.
Strings are sorted according to the sort function chosen.
Descending order is the reverse of ascending order.

Note: `+` in query URLs must be encoded as %2B -
for consistency, `-` can be encoded as %2D.

### Default sort order

If `+`/`-` is omitted, the default is used,
either the system-wide default of `+`
or any override in [schema](schema-reference.html#sorting).
Default sort order is `+` or ascending,
except for `[rank]` or the special builtin `[relevance]`,
which has `-` or descending.

## Sort attribute

The sorting attribute in a sort expression is the name of an
attribute in the index. Attribute names will often be the same
as field names. In the schema, an attribute is
indicated by the indexing language fragment for a field having
an [attribute](schema-reference.html#attribute)
statement.

When sorting on attributes, it is recommended to use the built-in *unranked* rank-profile.
This allows the search kernel to execute the query significantly faster than execution the ranking framework for many hits
and then finally ignore this score and sort by the specified sorting specification.

### Multivalue sort attribute

When sorting on a multivalue attribute ([map](schema-reference.html#map),
[array](schema-reference.html#array), or [weightedset](schema-reference.html#weightedset)) one of
the values for the document is selected to be used for
sorting. Ascending sort order uses the lowest value while descending
sort order uses the highest value. See the [missing policies](#missing) section for how a document without values in the attribute is treated.

## Sort function

Refer to [function](query-language-reference.html#function).

## Special sorting attributes

Three special attributes are available for sorting in addition to the index specific attributes:

| [relevance] | The document's relevance score for this query. This is the same as the default ordering when no sort specification is given ([rank] is a legacy alias for the same thing). |
| [source] | The document's source name. This is only relevant when querying multiple sources. |
| [docid] | The document's identification in the search backend. This will typically give you the documents in indexing order. **Keep in mind that this id is unique only to the backend node**. The same document might have different id on a different node. The same way a different document might have the same id on another node. This is just intended as a cheap way of getting an almost stable sort order. |

These special attributes are most useful as secondary sort expressions in a multilevel sort.
This will allow you to sort groups of equal values for the primary expression
in either relevancy or indexing order.
Without this additional sort expression, the order within each equal group is not deterministic.
{% include important.html content='
In [YQL, using order by](query-language-reference.html#order-by), the special sorting
attributes must be enclosed in quotes.
'%}

## Missing policies

A document might not have a value in the attribute. One of the following missing policies will then be applied:

| Policy | Example | Description |
| --- | --- | --- |
| default | `+attr` | If the sort order is ascending and the attribute is single-valued then the document is sorted before any documents with values in the attribute. If the attribute is multi-valued or the sort order is descending then the document is sorted after any documents with values in the attribute. |
| first | `+missing(attr,first)` | The document is sorted before any documents with values in the attribute. |
| last | `+missing(attr,last)` | The document is sorted after any documents with values in the attribute. |
| as | `+missing(attr,as,42)` | The document is sorted as if it had the missing value specified in the [sorting specification](#sortspec). If the missing value cannot be converted to the attribute data type then an error is reported (query is aborted for indexed search, parts of the sort spec is ignored for streaming search). |

Note that missing policies can be combined with other functions ,e.g.
`+missing(lowercase(attr),as,"nothing here")`.

## Limitations

### Attribute only

It is only possible to sort on [attributes](../attributes.html).
Trying to sort on an [index or summary field](../schemas.html#indexing),
without an associated attribute, will not work.

Also note that [match-phase](schema-reference.html#match-phase) is enabled when sorting.

### Optimization causing incorrect total hit count

When sorting on a single-value numeric attribute with [fast-search](../attributes.html#fast-search)
Vespa will by default activate an optimization which makes delivering sorted results much faster,
but with inaccurate total-hit count.
To disable this optimization,
set the query parameter `sorting.degrading` to false
(in the request or a [query profile](../query-profiles.html)).
See the [reference](query-api-reference.html#sorting.degrading) for details.

## Examples

Sort by surname in ascending order:

```
+surname
```

Sort by surname in ascending order after lowercasing the surname:

```
+lowercase(surname)
```

Sort by surname in ascending English US locale collation order.

```
+uca(surname,en_US)
```

Sort by surname in ascending Norwegian 'Bokmål' locale collation order:

```
+uca(surname,nb_NO)
```

Sort by surname in ascending Norwegian 'Bokmål' locale collation order,
but more attributes of a character are used to distinguish.
Now it is case-sensitive and 'aa' and 'å' are different:

```
+uca(surname,nb_NO,TERTIARY)
```

Sort by surname, with the youngest ones first when the names are equal:

```
+surname -yearofbirth
```

Sort in ascending order yearofbirth groups,
and sort by relevancy within each group of equal values
with the highest relevance first:

```
+yearofbirth -[relevance]
```
