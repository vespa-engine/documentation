---
# Copyright Vespa.ai. All rights reserved.
title: "Default JSON Result Format"
---

The default Vespa query response format is used when
[presentation.format](../reference/query-api-reference.html#presentation.format)
is unset or set to `json`.
Results are rendered with one or more objects:
* `root`: mandatory object with the tree of returned data
* `timing`: optional object with query timing information
* `trace`: optional object for metadata about query execution

Refer to the [query API guide](../query-api.html#result-examples) for result and tracing examples.

All object names are literal strings,
the node `root` is the map key "root" in the return JSON object,
in other words, only strings are used as map keys.

| Element | Parent | Mandatory | Type | Description |
| --- | --- | --- | --- | --- |
| root | | | | |
| root |  | yes | Map of string to object | The root of the tree of returned data. |
| children | root | no | Array of objects | Array of JSON objects with the same structure as `root`. |
| fields | root | no | Map of string to object |  |
| totalCount | fields | no | Integer | Number of documents matching the query. Not accurate when using *nearestNeighbor*, *wand* or *weakAnd* query operators.  The value is the number of hits after [first-phase dropping](schema-reference.html#rank-score-drop-limit). |
| coverage | root | no | Map of string to string and number | Map of metadata about how much of the total corpus has been searched to return the given documents. |
| coverage | coverage | yes | Integer | Percentage of total corpus searched (when lower than 100 this is an approximation and is a lower bound, as no info from nodes down is known) |
| documents | coverage | yes | Long | The number of active documents searched. |
| full | coverage | yes | Boolean | Whether the full corpus was searched. |
| nodes | coverage | yes | Integer | The number of search nodes returning results. |
| results | coverage | yes | Integer | The number of results merged creating the final rendered result. |
| resultsFull | coverage | yes | Integer | The number of full result sets merged, e.g. when there are several sources/clusters for the results. |
| degraded | coverage | no | Map of string to object | Map of match-phase degradation elements. |
| match-phase | degraded | no | Boolean | Indicator whether [match-phase degradation](schema-reference.html#match-phase) has occurred. |
| timeout | degraded | no | Boolean | Indicator whether the query [timed out](query-api-reference.html#timeout) before completion. |
| adaptive-timeout | degraded | no | Boolean | Indicator whether the query timed out with [adaptive timeout](query-api-reference.html#ranking.softtimeout.enable) before completion. |
| non-ideal-state | degraded | no | Boolean | Indicator whether the content cluster is in [ideal state](../content/idealstate.html). |
| errors | root | no | Array of objects | Array of error messages with the fields given below. [Example](../query-api.html#error-result). |
| code | errors | yes | Integer | Numeric identifier used by the container application. See [error codes](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/container/protect/Error.java) and [ErrorMessage.java](https://github.com/vespa-engine/vespa/blob/master/container-search/src/main/java/com/yahoo/search/result/ErrorMessage.java) for a short description. |
| message | errors | no | String | Full error message. |
| source | errors | no | String | Which [data provider](../federation.html) logged the error condition. |
| stackTrace | errors | no | String | Stack trace if an exception was involved. |
| summary | errors | yes | String | Short description of error. |
| transient | errors | no | Boolean | Whether the system is expected to recover from the faulty state on its own. If the flag is not present, this may or may not be the case, or the flag is not applicable. |
| fields | root | no | Map of string to object | The named document (schema) [fields](schema-reference.html#field). Fields without value are not rendered.  In addition to the fields defined in the schema, the following might be returned:   | Fieldname | Description | | --- | --- | | sddocname | Schema name. Returned in the [default document summary](../document-summaries.html). | | documentid | Document ID. Returned in the [default document summary](../document-summaries.html). | | summaryfeatures | Refer to [summary-features](schema-reference.html#summary-features) and [observing values used in ranking](../getting-started-ranking.html#observing-values-used-in-ranking). | | matchfeatures | Refer to [match-features](schema-reference.html#match-features) and [example use](../nearest-neighbor-search-guide.html#strict-filters-and-distant-neighbors). | |
| id | root | no | String | String identifying the hit, document or other data type. For document hits, this is the full string document id if the hit is filled with a document summary from disk. If it is not filled or only filled with data from memory (attributes), it is an internally generated unique id on the form `index:[source]/[node-index]/[hex-gid]`.  Also see the [/document/v1/ guide](../document-v1-api-guide.html#troubleshooting) and [receiving-responses-of-different-formats-for-the-same-query-in-vespa](https://stackoverflow.com/questions/74033383/receiving-responses-of-different-formats-for-the-same-query-in-vespa). |
| label | root | no | String | The label of a grouping list. |
| limits | root | no | Object | Used in grouping, the limits of a bucket in histogram style data. |
| from | limits | no | String | Lower bound of a bucket group. |
| to | limits | no | String | Upper bound of a bucket group. |
| relevance | root | yes | Double | Double value representing the rank score. |
| source | root | no | String | Which data provider created this node. |
| types | root | no | Array of string | Metadata about what kind of document or other kind of node in the result set this object is. |
| value | root | no | String | Used in grouping for value groups, the argument for the grouping data which is in the fields. |
|  | | | | |
| timing | | | | |
| timing |  | no | Map of string to object | Query timing information, enabled by [presentation.timing](query-api-reference.html#presentation.timing). The [query performance guide](/en/performance/practical-search-performance-guide.html#basic-text-search-query-performance) is a useful resource to understand the values in its child elements. |
| querytime | timing | no | Double | Time to execute the first protocol phase/matching phase, in seconds. |
| summaryfetchtime | timing | no | Double | [Document summary](../document-summaries.html) fetch time, in seconds. This is the time to execute the summary fill protocol phase for the globally ordered top-k hits. |
| searchtime | timing | no | Double | Approximately the sum of `querytime` and `summaryfetchtime` and is close to what a client will observe (except network latency). In seconds. |
|  | | | | |
| trace{% include note.html content="The tracing elements below is a subset of all elements. Refer to the [search performance guide](../performance/practical-search-performance-guide.html#advanced-query-tracing) for examples." %} | | | | |
| trace |  | no | Map of string to object | Metadata about query execution. |
| children | trace | no | Array of object | Array of maps with exactly the same structure as `trace` itself. |
| timestamp | children | no | Long | Number of milliseconds since the start of query execution this node was added to the trace. |
| message | children | no | String | Descriptive trace text regarding this step of query execution. |
| message | children | no | Array of objects | Array of messages |
| start_time | message | no | String | Timestamp, e.g. 2022-07-27 09:51:21.938 UTC |
| traces | message or threads | no | Array of traces or objects |  |
| distribution-key | message | no | Integer | The [distribution key](services-content.html#node) of the content node creating this span. |
| duration_ms | message | no | float | duration of span |
| timestamp_ms | traces | no | float | time since start of parent, see `start_time`. |
| event | traces | no | String | Description of span |
| tag | traces | no | String | Name of span |
| threads | traces | no | Array of objects | Array of object that again has traces elements. |

## JSON Schema

Formal schema for the query API default result format:

```
{% highlight json %}
{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Result",
    "description": "Schema for Vespa results",
    "type": "object",

    "properties": {
        "root": {
            "type": "document_node",
            "required": true
        },
        "trace": {
            "type": "trace_node",
            "required": false
        }
    },

    "definitions": {
        "document_node": {
            "properties": {
                "children": {
                    "type": "array",
                    "items": {
                        "type": "document_node"
                    },
                    "required": false
                },
                "coverage": {
                    "type": "coverage",
                    "required": false
                },
                "errors": {
                    "type": "array",
                    "items": {
                        "type": "error"
                    },
                    "required": false
                },
                "fields": {
                    "type": "object",
                    "additionalProperties": true,
                    "required": false
                },
                "id": {
                    "type": "string",
                    "required": false
                },
                "relevance": {
                    "type": "number",
                    "required": true
                },
                "types": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "required": false
                },
                "source": {
                    "type": "string",
                    "required": false
                },
                "value": {
                    "type": "string",
                    "required": false
                },
                "limits": {
                    "type": "object",
                    "required": false
                },
                "label": {
                    "type": "string",
                    "required": false
                }
            },
            "additionalProperties": true,
        },
        "trace_node": {
            "properties": {
                "children": {
                    "type": "array",
                    "items": {
                        "type": "trace_node"
                    },
                    "required": false
                },
                "timestamp": {
                    "type": "number",
                    "required": false
                },
                "message": {
                    "type": "string",
                    "required": false
                }
            }
        },
        "fields": {
            "properties": {
                "totalCount": {
                    "type": "number",
                    "required": true
                }
            }
        },
        "coverage": {
            "properties": {
                "coverage": {
                    "type": "number",
                    "required": true
                },
                "documents": {
                    "type": "number",
                    "required": true
                },
                "full": {
                    "type": "boolean",
                    "required": true
                },
                "nodes": {
                    "type": "number",
                    "required": true
                },
                "results": {
                    "type": "number",
                    "required": true
                },
                "resultsFull": {
                    "type": "number",
                    "required": true
                }
            }
        },
        "error": {
            "properties": {
                "code": {
                    "type": "number",
                    "required": true
                },
                "message": {
                    "type": "string",
                    "required": false
                },
                "source": {
                    "type": "string",
                    "required": false
                },
                "stackTrace": {
                    "type": "string",
                    "required": false
                },
                "summary": {
                    "type": "string",
                    "required": true
                },
                "transient": {
                    "type": "boolean",
                    "required": false
                }
            }
        }
    }
}
{% endhighlight %}
```

## Appendix: Legacy Vespa 7 JSON rendering

There were some inconsistencies between search results and document rendering in Vespa 7, which are fixed in Vespa 8.
This appendix describes the old behavior, what the changes are,
and how to configure to select a specific rendering.

### Inconsistent weightedset rendering

Fields with various weightedset types has a JSON input representation (for feeding) as a JSON object;
for example `{"one":1, "two":2,"three":3}` for
the value of a a `weightedset<string>` field.
The same format is used when rendering a document (for example when visiting).

In search results however, there are intermediate processing steps during which the
field value is represented as an array of item/weight pairs,
so in a search result the field value would render as
`[ {"item":"one", "weight":1},
{"item":"two", "weight":2},
{"item":"three", "weight":3} ]`

In Vespa 8, the default JSON renderer for search results outputs the same format
as document rendering. If you have code that depends on the old format you can
turn off this by setting `renderer.json.jsonWsets=false`
in the query (usually via a [query profile](../query-profiles.html)).

### Inconsistent map rendering

Fields with various map types has a JSON input representation (for feeding) as a JSON object;
for example `{"1001":1.0, "1002":2.0, "1003":3.0}` for
the value of a a `map<int,float>` field.
The same format is used when rendering a document (for example when visiting).

In search results however, there are intermediate processing steps and the field value
is represented as an array of key/value pairs,
so in a search results the field value would (in some cases) render as
`[ {"key":1001, "value":1.0},
{"key":1002, "value":2.0},
{"key":1003, "value":3.0} ]`

In Vespa 8, the default JSON renderer for search results output the same format as document rendering.
For code that depends on the old format one can
turn off this by setting `renderer.json.jsonMaps=false`
in the query (usually via a [query profile](../query-profiles.html)).

### Geo position rendering

Fields with the type `position` would in Vespa 7 be rendered using the internal fields "x" and "y".
These are integers representing microdegrees,
aka geographical degrees times 1 million, of longitude (for x) and latitude (for y).
Also, any field *foo* of type `position` would trigger addition of
two extra synthetic summary fields *foo.position* and *foo.distance* (see below for details).

In Vespa 8, positions are rendered with two JSON fields "lat" and "lng",
both having a floating-point value.
The "lat" field is latitude (going from -90.0 at the South Pole to +90.0 at the North Pole).
The "lng" field is longitude (going from -180.0 at the dateline seen as extreme west,
via 0.0 at the Greenwich meridian, to +180.0 at the dateline again, now as extreme east).
The field names are chosen so the format is the same as used in the Google "places" API.

It's possible to switch back to the legacy (Vespa 7) rendering for geo positions.
Set the flag to true by adding the following below the root `services` element in services.xml:

```
<legacy>
    <v7-geo-positions>true</v7-geo-positions>
</legacy>
```

Note that this flag affects rendering both in documents fetched/visited,
and in search results; but both the new and old formats are accepted as feed input.

A closely related change is the removal of two synthetic summary fields
which would be returned in search results. For example with this in schema:

```
field mainloc type position {
    indexing: attribute | summary
}
```

Vespa 7 would include the *mainloc* summary field,
but also *mainloc.position* and *mainloc.distance*;
the latter only when the query actually had a position to take the distance from.

The first of these (*mainloc.position* in this case) was
mainly useful for producing XML output in older Vespa versions,
and now contains just the same information as the *mainloc* summary field.
The second (*mainloc.distance* in this case) would return a distance in internal units,
and can be replaced by a summary feature -
here `distance(mainloc)` would give the same number,
while `distance(mainloc).km` would be the recommended replacement with suitable code changes.

### Summary-features wrapped in "rankingExpression"

In Vespa 7, if a rank profile wanted a function
`foobar` returned in summary-features (or match-features),
it would be rendered as `rankingExpression(foobar)` in the output.

For programmatic use, the `FeatureData` class has extra checking to allow lookup with
`getDouble("foobar")` or
`getTensor("foobar")`,
but now it's present and rendered with just the original name as specified.

If applications needs the JSON rendering to look exactly as in Vespa 7, one can specify that in the rank profile.
For example, with this in the schema:

```
rank-profile whatever {
    function lengthScore() { expression: matchCount(title)/fieldLength(title) }
    summary-features {
        matchCount(title)
        lengthScore
        ...
```

could, in Vespa 7, yield JSON output containing:

```
    summaryfeatures: {
        matchCount(title): 1,
        rankingExpression(lengthScore): 0.25,
        ...
```

in Vespa 8, you instead get the expected:

```
    summaryfeatures: {
        matchCount(title): 1,
        lengthScore: 0.25,
        ...
```

But to get the old behavior one can specify:

```
rank-profile whatever {
    function lengthScore() { expression: matchCount(title)/fieldLength(title) }
    summary-features {
        matchCount(title)
			  rankingExpression(lengthScore)
        ...
```

which gives you the same output as before.
