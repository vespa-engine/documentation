---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa Query Language - YQL"
---

Vespa accepts unstructured human input and structured queries for application logic separately,
then combines them into a single data structure for executing.
Human input is parsed heuristically, see [Query API input](query-api.html#input).
Application logic is expressed in YQL, use this guide for examples -
also see the [YQL reference](reference/query-language-reference.html).

## Live query examples

The following are live YQL examples:
---

Selection: Select all documents from the `doc` source.
This is the easiest way to count all documents in a source:

select * from doc where true
---

Filtering: Find all documents with `ranking` in the `title` field:

select * from doc where title contains "ranking"
---

Filtering: Find all documents with `ranking` in the `default` [fieldset](schemas.html#fieldset).

select * from doc where default contains "ranking"
---

Ordering: Order by number of terms in the document, descending.

select * from doc where true order by term_count desc
---

Pagination: Select all documents, return hits 6-15.

select * from doc where true limit 15 offset 5
---

Grouping:
* Select all documents from the `doc` source.
* Group by term count in buckets of 100, display average term count per bucket.
* Note on `limit 0`: This returns zero regular hits, only the grouping result.

select * from doc where true limit 0 |
all(
group( fixedwidth(term_count,100) )
each( output( avg(term_count) ) )
)

Find more [grouping examples](grouping.html).
---

Numeric: Select documents with attribute "last_updated" > 1646167144:

select * from doc where last_updated > 1646167144

Numeric: Select documents with integer in field - works both for single-value fields and multivalue,
like array<int>:

select * from doc where term_count = 257
---

Phrase: Select documents with the phrase "question answering":

select * from doc where default contains phrase("question","answering")
---

Timeout: Time out query execution after 100 ms, returning hits found before timing out -
see [ranking.softtimeout.enable](reference/query-api-reference.html#ranking.softtimeout.enable):

select * from doc where true timeout 100
---

Regular expressions: Select documents matching the regular expression
in the `namespace` [attribute](attributes.html) field:

select * from doc where namespace matches "op.*"
---

### Command-line queries

Use the [Vespa CLI](vespa-cli.html) to run a query from the command-line:

```
$ vespa query 'select * from doc where true'
```

To use any HTTP client, use `-v` to generate the encoded YQL string:

```
$ vespa query -v 'select * from doc where true'

curl http://127.0.0.1:8080/search/\?timeout=10s\&yql=select+%2A+from+doc+where+true
```

Run the query:

```
$ curl http://127.0.0.1:8080/search/\?timeout=10s\&yql=select+%2A+from+doc+where+true
```

Alternatively, set the query as the `yql` parameter in a POST:

```
$ curl --data-urlencode 'yql=select * from doc where true' \
  http://127.0.0.1:8080/search/
```

## Query examples

Boolean:

```
$ vespa query 'select * from doc where is_public = true'
```

Map:

```
$ vespa query 'select * from doc where my_map contains sameElement(key contains "Coldplay", value > 10)'

#
# Schema definition for my_map:
#
field my_map type map<string, int> {
    indexing: summary
    struct-field key   { indexing: attribute }
    struct-field value { indexing: attribute }
}
```

Escapes - see the [FAQ](faq.html#how-does-backslash-escapes-work):

```
#
# The artist field is:
#   "artist": "Meta..ica"
#

$ vespa query -v 'select * from music where artist matches "M.ta\\.\\.ica"'
```
