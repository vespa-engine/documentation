---
# Copyright Vespa.ai. All rights reserved.
title: "Simple Query Language Reference"
---

The *simple query language* allows application end users
to issue more complex queries than a list of tokens.
It is a heuristic, non-structured language,
which attempts to do something probably-useful with any input given.
It is combined with the structured [YQL](../query-language.html)
by using the [userQuery](query-language-reference.html#userquery) operator.

### Simple Query Syntax

```
Query      ::= Expr ( SPACE Expr )*
Expr       ::= Term | Prefix? '(' SimpleTerm+ ')'
Term       ::= Prefix? Field? CoreTerm Weight?
SimpleTerm ::= Field? CoreTerm Weight?
Prefix     ::= '+' | '-'
Field      ::= ID ':'                              /* A valid field name or alias */
Weight     ::= '!'+ | '!' NUM                      /* NUM is a percentage. */
CoreTerm   ::= WORD | Phrase | NumTerm | PrefixTerm | SubstringTerm | SuffixTerm | SameElement
Phrase     ::= '"' WORD+ '"'
NumTerm    ::= NUM | '<' NUM | '>' NUM | '[' NUM? ';' NUM? ';' HITLIMIT? ']'
                                                   /* NUM is any numeric type including floating point */
                                                   /* HITLIMIT is a optional count of many hits you want as minimum from this range */
PrefixTerm    ::= WORD '*'
SubstringTerm ::= '*' WORD '*'
SuffixTerm    ::= '*' WORD
SameElement   ::= '{' Field CoreTerm ( SPACE Field CoreTerm )* '}'
```

### Prefix searching

Prefix matching is only available for attributes.
A prefix search term (e.g. 'car*') behaves like a pattern match on the
given field: Documents that have a field value beginning with the
given prefix are matched and returned (or not returned if the '-' syntax is
used). A prefix search term does not add or change the ranking of the
documents in the result set.

### Term weight

The weight is either one or more ! characters, or a ! followed by an
integer. The integer is a fixed point scaling number with decimal
factor 100, i.e. it can be regarded as a percentage. When using
repeated ! characters, the weight is increased with 50 (from a default
value of 100) for each !. A weight expression may also be applied to a phrase.

A term weight is used to modify the relative importance of the terms
in your query. The term score is only one part of the overall rank
calculation, but by adding weight to the most important terms, you can
ensure that they contribute more. For more details on rank
calculation, see [Ranking guide](../ranking.html).

### Numerical terms

`[x;y]` matches any number between *x* and
*y*, including the endpoints *x* and
*y*. Note that `>number` is the same as
`[number+1;]` and `<number` is the same
as `[;number-1]`.

A few examples using numerical terms:

```
perl size:<100
```

This query will get all documents with the word “perl” and
with size less than 100Kb.

```
chess kasparov -karpov date:[19990101;19991231]
```

This query will get all documents last modified in 1999 containing
*chess* and *kasparov*, but not *karpov*.

#### Advanced range search

In order to quickly fetch the best documents given a simple range you can do
that efficiently using capped range search. For it to be efficient it requires that
you use [fast-search](schema-reference.html#attribute) on the attribute
used for range search.

It is fast because it will start only scan enough terms in the dictionary
to satisfy the number of documents requested. A positive number will start from the
left of your range and work its way right. A negative number will start from right and go left.

```
date:[0;21000101;10]
```

Will give you the at least 10 first documents since the birth of Jesus.

```
date:[0;21000101;-10]
```

Will give you the at least 10 last documents since the birth of Jesus.

### Grouping in the simple query language

There is only one level of parentheses supported; any use of
additional parentheses within the expression will be ignored. In
addition, note that the terms within should not be prefixed with + or -.

When the parentheses are prefixed by a + (can be excluded
for `all` type, because expressions are + by default), the
search requires that at least one of the included terms is present in
the document. This effectively gives you a way of having alternative
terms expressing the same intent, while requiring that the concept is
covered in the document.

When the parentheses are prefixed by a -, the search excludes all
documents that include all the terms, but allows documents that only
use some of the terms in the expression. It is a bit more difficult to
find good use for this syntax; it could for instance be used to remove
documents that compare two different products, while still allowing
documents only discussing one of them.

## Search in URLs

Create a URL-field in the index by creating a field of type
[uri](schema-reference.html#uri) -
refer to this for how to build queries.
The indexer will report an ERROR in the log for invalid URLs. Notes:
* Note however that finding documents matching a full URL does not
  behave like exact matching in i.e. string fields, but more like substring matching.
  A search for `myurlfield:http://www.mydomain.com/` will match documents
  where *myurlfield* is set to both *http://www.mydomain.com/*,
  *http://www.mydomain.com/test*, and *http://redirect.com/?goto=http://www.mydomain.com/*
* Hostname searches have an anchoring mechanism to limit which URLs match.
  By default, queries are anchored in the end,
  which means that a search for `mydomain.com` will match `www.mydomain.com`,
  but not `mydomain.com.au`.
  Adding a ^ (caret) to the start will turn on anchoring at the start,
  meaning that the query will only return exact matches.
  Adding a `*` at the end will turn off anchoring at the end.
  The query `^mydomain.com*` will match `mydomain.com.au`,
  but not `www.mydomain.com`.

## Field Path Syntax

Streaming search supports the [field path](document-field-path.html)
syntax of the [document selection language](document-select-language.html) when searching structs and maps.
Special for the map type is the ability to select a subset of
map entries to search using the `mymap{"foo"}`  syntax.

See the [field path](document-field-path.html) documentation
for use-cases of the map data type.

In the result output, a map is represented in the same way as in the Document XML:

```
<field name="mymap">
    <item><key>foo</key><value>bar</value></item>
    <item><key>fuz</key><value>baz</value></item>
</field>
```

## Removing syntax characters from queries

It will sometimes be more robust to remove characters which are used
in the query syntax from a user's search terms. An example could be
URLs containing parentheses. Comma ("," ASCII 0x2C) may be
used as a safe replacement character in these cases.

```
(x url:http://site.com/a)b) y
```

The URL `http://site.com/a)b` in this example could be quoted as following:

```
(x url:http://site.com/a,b) y
```

## Examples

The *simple* query language syntax accepts any input string and makes the most of it.
A basic query consists of words separated by spaces (encoded as %20). In addition,
* A phrase can be searched by enclosing it in quotes, like
  `"match exactly this"`
* Phrases and words may be preceded by -, meaning documents *must not* contain this
* Phrases and words may be preceded by +, meaning documents
  *must* contain this, currently only in use for subtype `any`
* Groups of words and phrases may be grouped using parenthesis, like
  `-(do not match if all of these words matches)`
* Each word or phrase may be preceded by an index or attribute name and a colon,
  like `indexname:word`, to match in that index.
  If the index name is omitted the index named *default* is searched.

Any *noise* (characters not in indexes or attributes, and with no query language meaning)
is ignored, all query strings are valid.
The exception is queries which have no meaningful interpretation.
An example is `-a`, which one would expect to return
all documents *not* containing *a*.
Vespa, however, will return the error message *Null query*.
All the following examples are of type *all*.

Get all documents with the term *word*,
having *microsoft* but not *bug* in the title:

```
word title:microsoft -title:bug
```

Search for all documents having the phrase "*to be or not to be*",
but excluding those having *shakespeare* in the title:

```
"to be or not to be" -title:shakespeare
```

Get all documents with the word *Christmas* in the title that
were last modified Christmas Day 2009:

```
title:Christmas date:20091225
```

Get documents on US Foreign politics, excluding those matching both
rival presidential candidates:

```
"us foreign politics" -(clinton trump)
```

Get documents on US Foreign politics, including only those matching at
least one of the rival presidential candidates:

```
"us foreign politics" (clinton trump)
```
