---
# Copyright Vespa.ai. All rights reserved.
title: "Query API"
---

Use the Vespa Query API to query, rank and organize data. Example:

```
{% raw %}
$ vespa query "select * from music where year > 2001" \
  "ranking=rank_albums" \
  "input.query(user_profile)={{cat:pop}:0.8,{cat:rock}:0.2,{cat:jazz}:0.1}"
{% endraw %}
```

Simplified, a query has the following components:
* Input data
* Ranking and grouping specification
* Results
* Other execution parameters

This guide is an introduction to the more important elements in the API -
refer to the [Query API reference](reference/query-api-reference.html) for details.
See [query execution](#query-execution) below for data flow.

## Input

Input data is both structured data and unstructured data:

```
{% raw %}
$ vespa query "select * from music where artist contains \"coldplay\" and userInput(@q)" \
  "q=head"
{% endraw %}
```

The first line is the [YQL](query-language.html) query string,
that has both structured input (artist=coldplay)
and a reference to unstructured user input.
The user input is then given in the second line in the *q* parameter.

Separating the structured data from the unstructured reliefs the application code from
interpreting and sanitizing the input data - it is essentially a blob.
Vespa can then use heuristics to deduct the user's intention.
User input can also be expressed in the
[simple query language](reference/simple-query-language-reference.html) using
the [userQuery](reference/query-language-reference.html#userquery) operator.

Finally, input data can also be ranking query features -
here the query feature is called *user_profile*:

```
{% raw %}
$ vespa query "select * from music where artist contains \"coldplay\" and userInput(@q)" \
  "q=head" \
  "ranking=rank_albums" \
  "input.query(user_profile)={{cat:pop}:0.8,{cat:rock}:0.2,{cat:jazz}:0.1}"
{% endraw %}
```

See [query execution](#query-execution) below.

### Input examples

```
$ vespa query "select * from sources * where userInput(@animal)" \
  "animal=panda"
```

The userInput() function will access the query property "animal",
and parse the property value as a [weakAnd](reference/query-language-reference.html#grammar) query,
resulting in:

`select * from sources * where weakAnd(default contains "panda")`
---

Changing the value of "animal" without changing the rest of the expression:

```
$ vespa query "select * from sources * where userInput(@animal)" \
  "animal=panda smokey"
```

The result is:

`select * from sources * where weakAnd(default contains "panda", default contains "smokey")`
---

Combining multiple query properties, and having a more complex expression:

```
$ vespa query "select * from sources * where range(year, 1963, 2014) and (userInput(@animal) or userInput(@teddy))" \
  "animal=panda" \
  "teddy=bear roosevelt"
```

The resulting YQL expression is:

`select * from sources * where range(year, 1963, 2014) and (weakAnd(default contains "panda") or weakAnd(default contains "bear", default contains "roosevelt"))`
---

Now, consider we do not want the "teddy" field to be treated as its own query segment,
it should only be segmented with the linguistic libraries to get recall.
Do this by adding a [grammar](reference/query-language-reference.html#grammar)-annotation
to the userInput() call:

```
$ vespa query "select * from sources * where range(year, 1963, 2014) and (userInput(@animal) or ({grammar: "segment"}userInput(@teddy)))" \
  "animal=panda" \
  "teddy=bear roosevelt"
```

Then, the linguistic library will split on space, and the resulting expression is:

`select * from sources * where range(year, 1963, 2014) and (weakAnd(default contains "panda") or default contains phrase("bear", "roosevelt"))`

### Using a fieldset

Above, the userInput() is run on the *default* index, as it is not specified.
Use a [query annotation](/en/reference/query-language-reference.html#defaultindex)
to use another index:

```
$ vespa query "select * from sources * where {defaultIndex: 'myindex'}userInput(@q)" \
  q=panda
```

`myindex` is here a [field](schemas.html#field)
or [fieldset](/en/schemas.html#fieldset) in the schema.
With userQuery(), use [model.defaultIndex](/en/reference/query-api-reference.html#model.defaultindex):

```
$ vespa query "select * from music where userQuery()" \
  query=panda \
  model.defaultIndex=myindex
```

### Query Profiles

Use a [query profile](reference/query-api-reference.html#queryprofile) to store
query parameters in configuration.
This makes query strings shorter, and makes it easy to modify queries by modifying configuration only.
Use cases are setting query properties for different markets, parameters that do not change, and so on.
Query profiles can be nested, versioned and use inheritance.

### Geo Filter and Ranking

Filter by position using latitude and longitude to implement [geo search](geo-search.html).
[DistanceToPath](reference/rank-features.html#distanceToPath(name).distance) is a
[rank function](ranking.html) based on closeness.
Using ranking can often improve results instead of geo
filtering.

### Parameter substitution

Parameter substitution lets you provide query values as request parameters
instead of inserting this into the YQL string itself.
This simplifies query generation, separating the value of the string/set/array from the YQL string -
i.e. the value will not corrupt the YQL string if it contains YQL-like syntax:
* Simplify query generation, separating the value of the set/array from the YQL string.
* Speed up query parsing. Using parameter substitution accelerates string parsing.
* Reduce duplication.

In its simplest form,
use [userInput()](/en/reference/query-language-reference.html#userinput) for strings:

```
... where userInput(@user_input)&user_input=free+text
```

Lists, maps and arrays can also be used - examples:

```
# Simple example: provide a set for the IN operator
... where id in (@my_set)&my_set=10,20,30

# Same set, but use the set as a block-list (exclude items in the set)
... where !(id in (@my_set))&my_set=10,20,30

# Use a weightedSet operator
... where weightedSet(field, @my_set)&my_set={a:1,b:2}
```

It is also great to eliminate data duplication,
from Vespa 8.287 one can use parameter substitution with `embed`:

```
$ vespa query \
  'yql=select id, from product where {targetHits:10}nearestNeighbor(embedding, query_embedding) or userQuery()' \
  'input.query(query_embedding)=embed(transformer, @query)' \
  'input.query(query_tokens)=embed(tokenizer, @query)' \
  'query=running shoes for kids, white'
```

Note the use of the parameter named [query](/en/reference/query-api-reference.html#model.querystring)
used by the [userQuery()](/en/reference/query-language-reference.html#userquery) operator.
Also note the value substituted in the [embed](/en/embedding.html#embedding-a-query-text) functions.

See the [reference](/en/reference/query-language-reference.html#parameter-substitution)
for a complete list of formats.

## Ranking

[Ranking](ranking.html) specifies the computation of the query and data.
It assigns scores to documents, and returns documents ordered by score.
A [rank profile](reference/query-api-reference.html#ranking.profile)
is a specification for how to compute a document's score.
An application can have multiple rank profiles, to run different computations.
Example, a query specifies query categories and a user embedding
(from the [tensor user guide](tensor-user-guide.html#ranking-with-tensors)):

```
rank-profile product_ranking inherits default {
    inputs {
        query(q_category) tensor<float>(category{})
        query(q_embedding) tensor<float>(x[4])
    }

    function p_sales_score() {
        expression: sum(query(q_category) * attribute(sales_score))
    }

    function p_embedding_score() {
        expression: closeness(field, embedding)
    }

    first-phase {
        expression: p_sales_score() + p_embedding_score()
    }
    match-features: p_sales_score() p_embedding_score()
}
```
```
{% highlight shell %}
vespa query 'yql=select * from product where {targetHits:1}nearestNeighbor(embedding,q_embedding)' \
  'input.query(q_embedding)=[1,2,3,4]' \
  'input.query(q_category)={"Tablet Keyboard Cases":0.8, "Keyboards":0.3}' \
  'ranking=product_ranking'
{% endhighlight %}
```

{% include note.html content='In this example, `input.query(q_embedding)` is short for
`ranking.features.query(q_embedding)` -
see the [reference](reference/query-api-reference.html#ranking.features)
for tensor formats.' %}

Results can be ordered using [sorting](reference/sorting.html) instead of ranking.

The above rank profile does not do text ranking -
there are however such profiles built-in.
Text search is described in more detail in [Text Matching](text-matching.html) -
find information about normalizing, prefix search and linguistics there.

## Grouping

[Grouping](grouping.html) is a way to group documents in the result set after ranking.
Example, return max 3 albums per artist, grouped on year:

```
$ vespa query "select * from music where true limit 0 | all(group(year) each(max(3) each(output(summary())) ) )"
```

Fields used in grouping must be [attributes](attributes.html).
The grouping expression is part of the YQL query string, appended at the end.

Applications can group *all* documents (select all documents in YQL).
Using `limit 0` returns grouping results only.

## Results

All fields are returned in results by default.
To specify a subset of fields, use [document summaries](document-summaries.html).
When searching text, having a static abstract of the document in a field, or
using a [dynamic summary](reference/schema-reference.html#summary)
can both improve the visual relevance of the search, and cut bandwidth used.

The default output format is [JSON](./reference/default-result-format.html).
Write a custom [Renderer](result-rendering.html) to generate results in other formats.

Read more on [request-response](jdisc/processing.html) processing -
use this to write code to manipulate results.

## Query execution

![Query execution - from query to response](/assets/img/query-to-response.svg)

Phases:

1. **Query processing**:
   Normalizations, rewriting and enriching. Custom logic in search chains
2. **Matching, ranking and grouping/aggregation:**
   This phase dispatches the query to content nodes
3. **Result processing, rendering:** Content fetching
   and snippeting of the top global hits found in the query phase

The above is a simplification - if the query also specifies [result grouping](grouping.html),
the query phase might involve multiple phases or round-trips between the container and content nodes.
See [life of a query](performance/sizing-search.html#life-of-a-query-in-vespa)
for a deeper dive into query execution details.

Use [trace.explainlevel](reference/query-api-reference.html#trace.explainlevel) to analyze the query plan.
Use these hints to modify the query plan:
* Use [ranked: false](reference/query-language-reference.html#ranked) query annotations
  to speed up evaluation
* Use [capped range search](reference/query-language-reference.html#numeric)
  to efficiently implement top-k selection for ranking a subset of the documents in the index.

### Query processing and dispatch

1. A query is sent from a front-end application to a container node
   using the *Query API* or in any custom request format handled by a
   custom [request handler](jdisc/developing-request-handlers.html),
   which translates the custom request format to native Vespa APIs.
2. Query pre-processing, like [linguistic processing](linguistics.html)
   and [query rewriting](query-rewriting.html),
   is done in built-in and custom [search chains](components/chained-components.html) -
   see [searcher development](searcher-development.html).

   The default search chain is *vespa* -
   find installed components in this chain by inspecting `ApplicationStatus`
   like in the [quick-start](vespa-quick-start.html).
   Adding `&trace.level=4` (or higher) to the query will
   emit the components invoked in the query, and is useful to analyze ordering.

   This is the integration point to plug in code to enrich a query - example:
   Look up user profile data from a user ID in the request.
   Set *&trace.level=2* to inspect the search chain components.
3. The query is sent from the container to
   the [content cluster](schemas.html#content-cluster-mapping) -
   see [federation](federation.html) for more details.
   An application can have multiple content clusters - Vespa searches in all by default.
   [Federation](federation.html) controls how to query the clusters,
   [sources](reference/query-api-reference.html#model.sources) names the clusters
   The illustration above has one content cluster but multiple is fully supported
   and allows scaling [document types](schemas.html) differently.
   E.g. a *tweet* document type can be indexed in a separate content cluster
   from a *user* document type, enabling independent scaling of the two.

   ![Query processing and dispatch](/assets/img/query-dispatch.svg)

### Matching, ranking, grouping

1. At this point the query enters one or more [content clusters](reference/services-content.html).
   In a content cluster with [grouped distribution](elasticity.html#grouped-distribution),
   the query is dispatched to all content nodes within a single group using a
   [dispatch policy](reference/services-content.html#dispatch-tuning),
   while with a flat single group content cluster the query is dispatched to all content nodes.
2. The query arrives at the content nodes which performs matching,
   [ranking](ranking.html) and aggregation/grouping over the set of documents
   in the [Ready sub database](proton.html). By default, Vespa uses [DAAT](performance/feature-tuning.html#hybrid-taat-daat) where the matching and first-phase score calculation is interleaved and not two separate, sequential phases.
   *vespa-proton* does matching over the *ready* documents
   and [ranks](ranking.html) as specified with the request/schema.
   Each content node matches and ranks a subset of the total document corpus
   and returns the hits along with meta information
   like total hits and sorting and grouping data, if requested.

   ![Queries](/assets/img/proton-query.svg)
3. Once the content nodes within the group have replied within the [timeout](graceful-degradation.html),
   [max-hits / top-k](reference/services-content.html#dispatch-tuning)
   results are returned to the container for query phase result processing.
   In this phase, the only per hit data available is the internal global document id (gid) and the ranking score.
   There is also result meta information like coverage and total hit count.
   Additional hit specific data, like the contents of fields,
   is not available until the result processing phase has completed the content fetching.

### Result processing (fill) phase

1. When the result from the query phase is available,
   a custom chained [searcher component](searcher-development.html#multiphase-searching)
   can process the limited data available from the first search phase
   before contents of the hits is fetched from the content nodes.
   The fetching from content nodes is lazy and is not invoked before rendering the response,
   unless asked for earlier by a custom searcher component.
2. Only fields in the requested [document summaries](document-summaries.html) is fetched from content nodes.
   The summary request goes directly to the content nodes that produced the result from the query phase.
3. After the content node requests have completed,
   the full result set can be processed further by custom components
   (e.g. doing result deduping, top-k re-ranking),
   before [rendering](result-rendering.html) the response.

## HTTP

{% include note.html content='Vespa does not provide a java client library for the query API.
Best practice for queries is submitting the user-generated query as-is,
then use [Searcher components](searcher-development.html) to implement additional logic.' %}

The Vespa Team does not recommend any specific HTTP client, since we haven't done any systematic evaluation.
We have most experience with the Apache HTTP client.
See also [HTTP best practices](https://cloud.vespa.ai/en/http-best-practices)
(for Vespa Cloud, but most of it is generally applicable).
Also see a discussion in [#24534](https://github.com/vespa-engine/vespa/issues/24534).

Use GET or POST. Parameters can either be sent as GET-parameters or posted as JSON, these are equivalent:

```
$ curl -H "Content-Type: application/json" \
    --data '{"yql" : "select * from sources * where default contains \"coldplay\""}' \
    http://localhost:8080/search/

$ curl http://localhost:8080/search/?yql=select+%2A+from+sources+%2A+where+default+contains+%22coldplay%22
```

### Using POST

The format is based on the [Query API reference](reference/query-api-reference.html),
and has been converted from the *flat* dot notation to a *nested* JSON-structure.
The request-method must be POST and the *Content-Type* must be *"application/json"*, e.g.:

```
$ curl -X POST -H "Content-Type: application/json" --data '
  {
      "yql": "select * from sources * where true",
      "offset": 5,
      "ranking": {
          "matchPhase": {
              "ascending": true,
              "maxHits": 15
          }
      },
      "presentation" : {
          "bolding": false,
          "format": "json"
      }
  }' \
  http://localhost:8080/search/
```

{% include note.html content="Try the
[Query Builder](https://github.com/vespa-engine/vespa/tree/master/client/js/app#query-builder)
application!" %}
{% include important.html content="Security filters can block GET and POST requests differently.
This can block POSTed queries." %}

### HTTP

Configure the [http server](reference/services-http.html#server) -
e.g. set *requestHeaderSize* to configure URL length (including headers):

```
{% highlight xml %}




                32768




{% endhighlight %}
```

HTTP keepalive is supported.

Values must be encoded according to standard URL encoding.
Thus, space is encoded as +, + as %2b and so on -
see [RFC 2396](https://www.ietf.org/rfc/rfc2396.txt).

HTTP status codes are found in the
[Query API reference](reference/query-api-reference.html#http-status-codes).
Also see [Stack Overflow question](https://stackoverflow.com/questions/54340386/how-should-i-customize-my-search-result-in-vespa/54344429#54344429).

When implementing a client for the query API, consider the following guidelines for handling HTTP status codes:

#### Client errors vs. server errors

In general clients should only retry requests on *server errors* (5xx) - not on *client errors* (4xx).
For example, a client should **not** retry a request after receiving a `400 Bad Request` response.

#### Back-pressure handling

Be careful when handling 5xx responses, especially `503 Service Unavailable` and `504 Gateway Timeout`.
These responses typically indicate an overloaded system, and blindly retrying without backoff will only worsen the situation.
For example, `503 Service Unavailable` is returned whenever there are no available search handler threads
to serve the request. This is a clear indication of back-pressure from the system, and clients should
reduce overall throughput and implement appropriate throttling mechanisms to avoid exacerbating the overload condition.

## Timeout

See the [reference](reference/query-api-reference.html#timeout) for how to set the query timeout.
Common questions:
* *Does the timeout apply to the whole query or just from when it is sent to the content cluster?
  If a [Searcher](searcher-development.html) goes to sleep in the container for 2*timeout,
  will the caller still get a response indicating a timeout?*

  The timeout applies to the whole query, both container and content node processing.
  However, the timeout handling is cooperative -
  if having Searchers that are time-consuming or access external resources,
  the Searcher code should check
  [Query.getTimeLeft()](https://github.com/vespa-engine/vespa/blob/master/container-search/src/main/java/com/yahoo/search/Query.java).
  So, in this case, you will time out, but only after 2*timeout + some more.
* *During multiphase searching, is the query timeout set for each individual searcher,
  or is the query timeout set for the entire search chain?*

  The timeout is for the entire query (and most Searchers don’t check timeout -
  use `Query.getTimeLeft()`).
  E.g., if a Search Chain has 3 Searchers,
  it is OK for 1 Searcher to take 497 ms and 2 Searchers to each take 1 ms for a query timeout of 500 ms.
* *If we asynchronously execute several search chains,
  can we set different query timeouts for each of these chains
  plus a separate overall timeout for the searcher that performs the asynchronous executions?*

  You can set a different timeout in each cloned query you send to any of those chains,
  and you can specify the timeout when waiting for responses from them.

## Error handling

Check for a `root: error` element in the [result](reference/default-result-format.html#error):

```
{% highlight json %}
{
    "root": {
        "errors": [
            {
                "code": 8,
                "summary": "Error in search reply.",
                "source": "music",
                "message": "Could not locate attribute for grouping number 0 : Failed locating attribute vector 'year'. Ignoring this grouping."
            }
        ],
{% endhighlight %}
```

## Troubleshooting

If Vespa cannot generate a valid search expression from the query string,
it will issue the error message *Null query*.
To troubleshoot, add [&trace.level=2](reference/query-api-reference.html#trace.level) to the request.
A missing *yql* parameter will also emit this error message.

### Query tracing

Use *query tracing* to debug query execution.
Enable by using [trace.level=1](reference/query-api-reference.html#trace.level) (or higher).
Add [trace.timestamps=true](reference/query-api-reference.html#trace.timestamps)
for timing info for every searcher invoked.
Find a trace example in the result examples below,
and try the [practical search performance guide](performance/practical-search-performance-guide.html#advanced-query-tracing).

In custom code, use
[Query.trace](https://javadoc.io/page/com.yahoo.vespa/container-search/latest/com/yahoo/search/Query.html)
to add trace output.

### Large memory usage

Queries that allocate more than 2G RAM will log messages like:

```
mmap 2727 of size 8589934592 from : search::attribute::PostingListMerger<int>::reserveArray(unsigned int, unsigned long)(0x40001513eef0)

(0x400013595334) from (0x400013593acc) from operator new(unsigned long)(0x400013592f88) from search::attribute::PostingListMerger<int>::reserveArray(unsigned int, unsigned long)(0x40001513eef0) from search::attribute::PostingListSearchContextT<int>::fetchPostings(search::queryeval::ExecuteInfo const&, bool)(0x400015159a38) from search::queryeval::SameElementBlueprint::fetchPostings(search::queryeval::ExecuteInfo const&)(0x4000154f36fc) from search::queryeval::IntermediateBlueprint::fetchPostings(search::queryeval::ExecuteInfo const&)(0x40001549ad38) from proton::matching::MatchToolsFactory::MatchToolsFactory(proton::matching::QueryLimiter&, vespalib::Doom const&, proton::matching::ISearchContext&, search::attribute::IAttributeContext&, search::engine::Trace&, std::basic_string_view<char, std::char_traits<char> >, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, ...

1 mappings of accumulated size 8589934592
```

This does not necessarily indicate that something is wrong, e.g., range searches use much memory.

## Result examples

A regular query result:

```
{% highlight json %}
{
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1
        },
        "coverage": {
            "coverage": 100,
            "documents": 3,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "id:mynamespace:music::a-head-full-of-dreams",
                "relevance": 0.16343879032006284,
                "source": "music",
                "fields": {
                    "sddocname": "music",
                    "documentid": "id:mynamespace:music::a-head-full-of-dreams",
                    "artist": "Coldplay",
                    "album": "A Head Full of Dreams",
                    "year": 2015,
                    "category_scores": {
                        "cells": [
                            {
                                "address": {
                                    "cat": "pop"
                                },
                                "value": 1.0
                            },
                            {
                                "address": {
                                    "cat": "rock"
                                },
                                "value": 0.20000000298023224
                            },
                            {
                                "address": {
                                    "cat": "jazz"
                                },
                                "value": 0.0
                            }
                        ]
                    }
                }
            }
        ]
    }
}
{% endhighlight %}
```

An empty result:

```
{% highlight json %}
{
    "root": {
        "fields": {
            "totalCount": 0
        },
        "id": "toplevel",
        "relevance": 1.0
    }
}
{% endhighlight %}
```

An error result:

```
{% highlight json %}
{
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 2
        },
        "coverage": {
            "coverage": 100,
            "documents": 4,
            "full": true,
            "nodes": 2,
            "results": 2,
            "resultsFull": 2
        },
        "errors": [
            {
                "code": 8,
                "summary": "Error in search reply.",
                "source": "music",
                "message": "Could not locate attribute for grouping number 0 : Failed locating attribute vector 'year'. Ignoring this grouping."
            }
        ],
{% endhighlight %}
```

A simple search application, many undefined fields. Result for the query
`/search/?query=blues&hits=3&trace.level=2`

```
{% highlight json %}
{

    "trace": {
        "children": [
            {
                "message": "No query profile is used"
            },
            {
                "message": "Invoking chain 'vespa' [com.yahoo.prelude.statistics.StatisticsSearcher@native -> com.yahoo.prelude.querytransform.PhrasingSearcher@vespa -> ... -> federation@native]"
            },
            {
                "children": [
                    {
                        "message": "Detected language: ENGLISH"
                    },
                    {
                        "message": "Language ENGLISH determined by the characters in the terms."
                    },
                    {
                        "message": "Query parsed to: select * from sources * where default contains \"blues\" limit 3"
                    },
                    {
                        "message": "Child execution",
                        "children": [
                            {
                                "message": "Stemming: [select * from sources * where default contains ({\"origin\": {\"original\": \"blues\", \"offset\": 0, \"length\": 5}, \"stem\": false}\"blue\") limit 3]"
                            },
                            {
                                "message": "Lowercasing: [select * from sources * where default contains ({\"origin\": {\"original\": \"blues\", \"offset\": 0, \"length\": 5}, \"stem\": false, \"normalizeCase\": false}\"blue\") limit 3]"
                            },
                            {
                                "message": "sc0.num0 search to dispatch: query=[blue] timeout=5000ms offset=0 hits=3 grouping=0 : collapse=false restrict=[music]"
                            },
                            {
                                "message": "Current state of query tree: WORD[connectedItem=null connectivity=0.0 creator=ORIG explicitSignificance=false fromSegmented=false index=\"\" isRanked=true origin=\"(0 5)\" segmentIndex=0 significance=0.0 stemmed=true uniqueID=1 usePositionData=true weight=100 words=true]{\n \"blue\"\n}\n"
                            },
                            {
                                "message": "YQL+ representation: select * from sources * where default contains ({\"origin\": {\"original\": \"blues\", \"offset\": 0, \"length\": 5}, \"stem\": false, \"normalizeCase\": false, \"id\": 1}\"blue\") limit 3"
                            },
                            {
                                "message": "sc0.num0 dispatch response: Result (3 of total 10 hits)"
                            },
                            {
                                "message": "sc0.num0 fill to dispatch: query=[blue] timeout=5000ms offset=0 hits=3 grouping=0 : collapse=false restrict=[music] summary=[null]"
                            },
                            {
                                "message": "Current state of query tree: WORD[connectedItem=null connectivity=0.0 creator=ORIG explicitSignificance=false fromSegmented=false index=\"\" isRanked=true origin=\"(0 5)\" segmentIndex=0 significance=0.0 stemmed=true uniqueID=1 usePositionData=true weight=100 words=true]{\n \"blue\"\n}\n"
                            },
                            {
                                "message": "YQL+ representation: select * from sources * where default contains ({\"origin\": {\"original\": \"blues\", \"offset\": 0, \"length\": 5}, \"stem\": false, \"normalizeCase\": false, \"id\": 1}\"blue\") limit 3"
                            }
                        ]
                    },
                    {
                        "message": "Child execution"
                    }
                ]
            }
        ]
    },
    "root": {
        "id": "toplevel",
        "relevance": 1,
        "fields": {
            "totalCount": 10
        },
        "coverage": {
            "coverage": 100,
            "documents": 10,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "index:0/0/0/dfd9fcfa650b44545ef0b8b2",
                "relevance": "-Infinity",
                "source": "basicsearch",
                "fields": {
                    "sddocname": "music",
                    "title": "Electric Blues",
                    "artist": "",
                    "song": "",
                    "bgndata": "",
                    "sales": "NaN",
                    "pto": -1,
                    "mid": 2,
                    "ew": "blues",
                    "surl": "https://shopping.yahoo.com/shop?d=hab&id=1807865261",
                    "userrate": "NaN",
                    "pid": "",
                    "weight": "NaN",
                    "url": "",
                    "isbn": "",
                    "fmt": "",
                    "albumid": "",
                    "disp_song": "",
                    "pfrom": "NaN",
                    "bgnpfrom": "NaN",
                    "categories": "Blues",
                    "data": "",
                    "numreview": "NaN",
                    "bgnsellers": 0,
                    "image": "",
                    "artistspid": "",
                    "newestedition": "NaN",
                    "bgnpto": "",
                    "year": "NaN",
                    "did": "NaN",
                    "scorekey": "NaN",
                    "cbid": "NaN",
                    "summaryfeatures": "",
                    "documentid": "id:test:music::https://shopping.yahoo.com/shop?d=hab&id=1807865261"
                }
            },
            {
                "id": "index:0/0/0/273d384dc214386c934d793f",
                "relevance": "-Infinity",
                "source": "basicsearch",
                "fields": {
                    "sddocname": "music",
                    "title": "Delta Blues",
                    "artist": "",
                    "song": "",
                    "bgndata": "",
                    "sales": "NaN",
                    "pto": -1,
                    "mid": 2,
                    "ew": "blues",
                    "surl": "https://shopping.yahoo.com/shop?d=hab&id=1804905714",
                    "userrate": "NaN",
                    "pid": "",
                    "weight": "NaN",
                    "url": "",
                    "isbn": "",
                    "fmt": "",
                    "albumid": "",
                    "disp_song": "",
                    "pfrom": "NaN",
                    "bgnpfrom": "NaN",
                    "categories": "Blues",
                    "data": "",
                    "numreview": "NaN",
                    "bgnsellers": 0,
                    "image": "",
                    "artistspid": "",
                    "newestedition": "NaN",
                    "bgnpto": "",
                    "year": "NaN",
                    "did": "NaN",
                    "scorekey": "NaN",
                    "cbid": "NaN",
                    "summaryfeatures": "",
                    "documentid": "id:test:music::https://shopping.yahoo.com/shop?d=hab&id=1804905714"
                }
            },
            {
                "id": "index:0/0/0/b3c74a9bf3aea1e2260311c0",
                "relevance": "-Infinity",
                "source": "basicsearch",
                "fields": {
                    "sddocname": "music",
                    "title": "Chicago Blues",
                    "artist": "",
                    "song": "",
                    "bgndata": "",
                    "sales": "NaN",
                    "pto": -1,
                    "mid": 2,
                    "ew": "blues",
                    "surl": "https://shopping.yahoo.com/shop?d=hab&id=1804905710",
                    "userrate": "NaN",
                    "pid": "",
                    "weight": "NaN",
                    "url": "",
                    "isbn": "",
                    "fmt": "",
                    "albumid": "",
                    "disp_song": "",
                    "pfrom": "NaN",
                    "bgnpfrom": "NaN",
                    "categories": "Blues",
                    "data": "",
                    "numreview": "NaN",
                    "bgnsellers": 0,
                    "image": "",
                    "artistspid": "",
                    "newestedition": "NaN",
                    "bgnpto": "",
                    "year": "NaN",
                    "did": "NaN",
                    "scorekey": "NaN",
                    "cbid": "NaN",
                    "summaryfeatures": "",
                    "documentid": "id:test:music::https://shopping.yahoo.com/shop?d=hab&id=1804905710"
                }
            }
        ]
    }
}
{% endhighlight %}
```

Result for the grouping query
`/search/?hits=0&yql=select * from sources * where sddocname contains purchase | all(group(customer) each(output(sum(price))))`

```
{% highlight json %}
{

    "trace": {
        "children": [
            {
                "children": [
                    {
                        "message": "Child execution"
                    }
                ]
            }
        ]
    },
    "root": {
        "id": "toplevel",
        "relevance": 1,
        "fields": {
            "totalCount": 20
        },
        "coverage": {
            "coverage": 100,
            "documents": 20,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "group:root:0",
                "relevance": 1,
                "continuation": {
                    "this": ""
                },
                "children": [
                    {
                        "id": "grouplist:customer",
                        "relevance": 1,
                        "label": "customer",
                        "children": [
                            {
                                "id": "group:string:Jones",
                                "relevance": 9870,
                                "value": "Jones",
                                "fields": {
                                    "sum(price)": 39816
                                }
                            },
                            {
                                "id": "group:string:Brown",
                                "relevance": 8000,
                                "value": "Brown",
                                "fields": {
                                    "sum(price)": 20537
                                }
                            },
                            {
                                "id": "group:string:Smith",
                                "relevance": 6100,
                                "value": "Smith",
                                "fields": {
                                    "sum(price)": 19484
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
}
{% endhighlight %}
```
