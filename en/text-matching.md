---
# Copyright Vespa.ai. All rights reserved.
title: "Text Matching"
redirect_from:
- /en/text-matching-ranking.html
---

This guide demonstrates tokenization, linguistic processing and matching over [string](reference/schema-reference.html#string)
fields in Vespa. The guide features examples based on the [quick start](vespa-quick-start.html).

Refer to the [ranking](ranking.html) introduction for ranking,
and review the different [match modes](reference/schema-reference.html#match) that Vespa supports per field.
See the [text search](tutorials/text-search.html) and
[text search through ML](tutorials/text-search-ml.html) tutorials.
Finally, refer to [linguistics](linguistics.html) for linguistic processing in Vespa.

Using [query tracing](#query-trace) is useful when debugging text matching.

## Index and attribute

Vespa string fields can have a mix of settings specified per field,
such as the [indexing](reference/schema-reference.html#indexing) and
[match modes](reference/schema-reference.html#match).
* The *index* for free-text search with default match mode *text*, integrating with linguistic
  processing such as [tokenization and stemming](linguistics.html).
* The *attribute* indexing is used for
  database-style of string matching without linguistic processing and where the exact string contents are matched.

Free-text search is normally solved using a string field in *index* mode:

```
field album type string {
    indexing: summary | index
}
```

If both index and attribute are configured for string-type fields, Vespa will search and match against the
index with default match `text`. When the field is both index and attribute, the index
aspect is used for matching. (The attribute could still be useful in general, for grouping and sorting.)
To get multiple match modes on a single source field you could define a synthetic field outside the document block:

```
schema music {

  document music {

    field album type string {
      indexing: summary | index
    }

  }

  field album_as_attribute type string {
    indexing: input album | attribute
  }

}
```

If you want substring matching for indexed search, consider using [n-gram matching](#n-gram-match).

Below, find details on transformations to the text for text indexing and search using the quick start
sample application as an example.

The *album* field has [index](reference/schema-reference.html#indexing) mode.
For text fields, this enables transformations of the string field to increase query recall.

The following is useful for dumping the resulting text tokens after indexing, to understand the transformations. This
coupled with [query tracing](#query-trace) can help us understand why a document field doesn't match or match a query.

Add another [document summary](document-summaries.html)
to [schemas/music.sd](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation/app/schemas/music.sd) that contains an extra summary field
using [tokens](reference/schema-reference.html#tokens)
with the [source](reference/schema-reference.html#source)
set to the proper index field:

```
document-summary my-debug-summary {
    summary album { }
    summary album_tokens {
        source: album
        tokens
    }
    from-disk
}

fieldset default {
    fields: artist, album
}
```

Redeploy the application to enable the new document summary:

```
$ vespa deploy --wait 300
```

Show original content of album field:

```
$ vespa query "select * from music where true" summary=my-debug-summary | \
  jq -c '.root.children[].fields.album'
"Liebe ist für alle da"
"A Head Full of Dreams"
"Hardwired...To Self-Destruct"
"When We All Fall Asleep, Where Do We Go?"
"Love Is Here To Stay"
```

Show tokens used for indexing the album field:

```
$ vespa query "select * from music where true" summary=my-debug-summary | \
  jq -c '.root.children[].fields.album_tokens'
["lieb","ist","fur","all","da"]
["a","head","full","of","dream"]
["hardwire","to","self","destruct"]
["when","we","all","fall","asleep","where","do","we","go"]
["love","is","here","to","stay"]
```

Observe the [linguistic transformations](linguistics.html) to the data before indexed:

| Transformation | Type |
| --- | --- |
| Hardwired...To → hardwire to | Tokenization - split terms on non-characters, here "..." |
| Head → head | Lowercasing |
| für → fur | Normalizing |
| dreams → dream | Stemming |

Then, change from *index* to [attribute](reference/schema-reference.html#indexing)
in [schemas/music.sd](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation/app/schemas/music.sd) (and remove all bm25 settings):

```
@@ -13,8 +13,7 @@
         }

         field album type string {
-            indexing: summary | index
-            index: enable-bm25
+            indexing: summary | attribute
         }

         field year type int {
@@ -51,7 +50,7 @@
             query(user_profile) tensor<float>(cat{})
         }
         first-phase {
-            expression: bm25(album) + 0.25 * sum(query(user_profile) * attribute(category_scores))
+            expression: 0.25 * sum(query(user_profile) * attribute(category_scores))
         }
     }
```

Run the tutorial again using the new schema, stop after feeding.
Show tokens used for indexing the album field:

```
$ vespa query "select * from music where true" summary=my-debug-summary | \
  jq -c '.root.children[].fields.album_tokens'
["a head full of dreams"]
["love is here to stay"]
["when we all fall asleep, where do we go?"]
["liebe ist für alle da"]
["hardwired...to self-destruct"]
```

The most important observation is that the strings are added *as-is* for attributes and matching considers the full value, including whitespace (no tokenization).

The only transformation is lowercasing, both query terms and attribute data are lowercased before matching unless the `match`
setting for the field has been set to `cased`.
Read more about the attribute [word match mode](reference/schema-reference.html#match).

## Prefix match

Use the [prefix](/en/reference/query-language-reference.html#prefix) annotation
to match string prefixes in attributes of type string:

```
field album type string {
    indexing: summary | attribute
}
```

Note that regular *index* fields does not support prefix matching.

```
$ vespa query 'select * from music where album contains ({prefix: true}"a hea")'
```

The [search-suggestions](https://github.com/vespa-engine/sample-apps/tree/master/incremental-search/search-suggestions) sample application uses prefix search, see README for a design discussion.

To prefix-match individual terms in a string,
use an attribute with array of strings in addition to the index string field, e.g.:

```
schema company {
    document company {
        field company_name_string type string {
            indexing: index | summary
        }
    }
    field company_name_array type array<string> {
        indexing: input company_name_string | trim | split " +" | attribute | summary
    }
}
```

Use the [indexing-language](reference/indexing-language-reference.html) to split the string, as shown above.
Adding "Goldman" and "Sachs" will match query terms like "Gold" and "Sach".

## Fuzzy match

Use [fuzzy](reference/query-language-reference.html#fuzzy) matching
to match in string attributes with configurable edit distance. Field configuration:

```
field album type string {
    indexing:  summary | attribute
    attribute: fast-search
}
```
```
$ vespa query 'select * from music where album contains ({maxEditDistance: 1}fuzzy("A Head Full of Dreems"))'
```

Fuzzy matching is great for misspellings.
See use of *prefixLength* and *fast-search* in the [reference](reference/query-language-reference.html#fuzzy).

Character [normalization](/en/linguistics.html#normalization) is not performed for fuzzy matches.

### Fuzzy prefix match

By default, `fuzzy` matches *full* strings against the query. For use-cases such as
type-ahead search this means a user query such as "Ahead Full" will fail to match the document string
"A Head Full of Dreams", both when using fuzzy matching (too many characters missing) as well
as regular, *non-fuzzy* prefix matching (prefixes do not exactly match).

Adding `prefix:true` enables *fuzzy prefix* semantics. If a string has a *prefix*
that can match the query string within the specified maximum number of edits, it will be considered a match.

```
$ vespa query 'select * from music where album contains ({maxEditDistance: 1, prefix: true}fuzzy("Ahead Full"))'
```

This query will match strings such as "A Head Full of Dreams", "A Head Full of Clouds", "Ahead Full Steam" etc.

Exact prefix locking (`prefixLength:n`) can be used alongside fuzzy prefix matching to constrain the
candidate set to strings that have prefix that *exactly* matches *n* characters of the query. Fuzzy prefix
matching then applies to the remainder (suffix) of the candidate string. This greatly speeds up dictionary scans
since only a subset of the dictionary needs to be considered.

{% include important.html content="Fuzzy prefix matching often matches many more documents than non-prefix
fuzzy matching. For instance, a query such as `{maxEditDistance:2,prefix:true}fuzzy(\"XY\")` will
end up matching *every* document, since *all possible strings* can have their prefix transformed to \"XY\"
with at most 2 edits. This is the case for all fuzzy prefix queries where the length of the query string is equal to,
or lower than, `maxEditDistance`. This should be taken into consideration when constructing queries
based on user input."%}

## Regular expression match

Using [regular expressions](reference/query-language-reference.html#matches)
is supported in attributes.
There are however no optimizing data structures for query speed,
it runs the expression over all attribute values.

```
field album type string {
    indexing:  summary | attribute
}
```

Example, matching from start of string:

```
$ vespa query 'select * from music where album matches "^a head fu[l]+ of dreams"'
```

A substring search:

```
$ vespa query 'select * from music where album matches "head"'
```

Character [normalization](/en/linguistics.html#normalization) is not performed for regular expression matches.

## N-Gram match

N-gram matching splits text into subword tokens ("grams") of the specified N size.
This is useful with CJK languages which does not use space, as well as for substring matching
in text indexes.

Vespa will by default combine the grams it creates from a text in queries into an AND item,
requiring all of them to match. This can be overridden by sending the query parameter `gram.match`,
which can be set to the name of any composite query item:
`all` (default), `any`, `weakAnd`, `phrase`, `near`, or `onear`.

```
Example: Input text "滿腦子的夢想" with these settings

    field album type string {
        indexing: {
            "zh-hant" | set_language;
            summary | index
        }
        match {
            gram
            gram-size: 2
        }
    }

Produces the tokens 子的 夢想 滿腦 的夢 腦子

Any query which contains at least two tokens frmo this text will therefore be matched.
```

## Example use case
*What is the best way to index short word-length documents,
like names of all locations/towns in the world, such that they:*
* *Are robust to misspelling in user queries eg: "Amsterdam" --> "amstredam"*
* *Are cross-lingual for search, e.g.: "America" --> "美國"*

To make this multilingual,
use an [array<string>](reference/schema-reference.html#array) field to store all the alternatives.
One can also translate to a canonical single language used in indexing at query time,
but in cases with very short documents, opt for doing it indexing time.

Alternatives for matching with spell checking:

1. Make the field an attribute and use [fuzzy matching](#fuzzy-match).
2. Make the field an index with [gram matching](#n-gram-match).
3. Having an array of alternatives anyway, just stuff all the misspellings to match into it.
   Consider using a [weighted set](reference/schema-reference.html#weightedset) instead
   to weight them by closeness to the original.

3. will give the cheapest queries and exact control over misspelled matching,
but a larger index, more work for the developer, and adjusting spell correction becomes more complicated.
1. will be most expensive, but maybe also most convenient
There are currently no rank signals giving you the match quality.
2. Is in between, and will probably work best when incorporating ranking signals that use proximity
(such as e.g. [nativeRank](nativerank.html) but not [bm25](reference/bm25.html)).

Read [Simplify Search with Multilingual Embedding Models](https://blog.vespa.ai/simplify-search-with-multilingual-embeddings) for semantic matching and ranking.

## Query Trace

Adding [trace.level=2](reference/query-api-reference.html#trace.level)
gives insight when testing queries - example attribute lowercasing
(observe that queries with "Liebe" and "liebe" give the same result):

```
$ vespa config set target local
$ vespa query 'select * from music where album contains "Liebe ist für alle da"' \
  ranking=rank_albums \
  trace.level=2
```

Also try query tracing to see how query parsing changes with *index* and *attribute* indexing modes.

## Appendix: Match Configuration Debugging

Inspect generated configuration to understand or validate the match configuration.
Run this to find the value of the -i argument used below:

```
$ docker exec vespa sh -c vespa-configproxy-cmd | grep IndexingProcessor

  vespa.configdefinition.ilscripts,default/docprocchains/chain/indexing/component/com.yahoo.docprocs.indexing.IndexingProcessor, ...
```

Start over, deploy with the indexing settings below and feed data.
Note the difference for the *artist* (with exact matching) and *album* fields:

```
field artist type string {
    indexing: summary | index
    match   : exact
}
field album type string {
    indexing: summary | index
}

$ docker exec vespa sh -c 'vespa-get-config \
  -n vespa.configdefinition.ilscripts \
  -i default/docprocchains/chain/indexing/component/com.yahoo.docprocs.indexing.IndexingProcessor'

maxtermoccurrences 100
fieldmatchmaxlength 1000000
ilscript[0].doctype "music"
ilscript[0].docfield[0] "artist"
ilscript[0].docfield[1] "album"
ilscript[0].docfield[2] "year"
ilscript[0].docfield[3] "category_scores"
ilscript[0].content[0] "clear_state | guard { input artist | exact | summary artist | index artist; }"
ilscript[0].content[1] "clear_state | guard { input album | tokenize normalize stem:"BEST" | summary album | index album; }"
ilscript[0].content[2] "clear_state | guard { input year | summary year | attribute year; }"
ilscript[0].content[3] "clear_state | guard { input category_scores | summary category_scores | attribute category_scores; }"
```
