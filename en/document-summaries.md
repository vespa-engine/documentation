---
# Copyright Vespa.ai. All rights reserved.
title: "Document Summaries"
---

A *document summary* is the information that is shown for each document in a query result.
What information to include is determined by a *document summary class*:
A named set of fields with config on which information they should contain.

A special document summary named `default` is always present and used by default.
This contains:
* all fields which specifies in their indexing statements that they may be included in summaries* all fields specified in any document summary* [sddocname](reference/default-result-format.html#sddocname)* [documentid](reference/default-result-format.html#documentid).

Summary classes are defined in the schema:

```
schema music {

    document music {
        field artist type string {
            indexing: summary | index
        }
        field album type string {
            indexing: summary | index
            index: enable-bm25
        }
        field year type int {
            indexing: summary | attribute
        }
        field category_scores type tensor<float>(cat{}) {
            indexing: summary | attribute
        }
    }

    document-summary my-short-summary {
        summary artist {}
        summary album {}
    }
}
```

See the [schema reference](reference/schema-reference.html#summary) for details.

The summary class to use for a query is determined by the parameter
[presentation.summary](reference/query-api-reference.html#presentation.summary);:

```
$ vespa query "select * from music where album contains 'head'" \
  "presentation.summary=my-short-summary"
```

A common reason to define a document summary class is [performance](#performance):
By configuring a document summary which only contains attributes the result can be generated
without disk accesses. Note that this is needed to ensure only memory is accessed even if all fields are
attributes because the [document id](documents.html#document-ids) is not stored as an attribute.

Document summaries may also contain [dynamic snippets and highlighted terms](#dynamic-snippets).

The document summary class to use can also be issued programmatically to the `fill()`
method from a searcher, and multiple fill operations interleaved with programmatic filtering can be used to
optimize data access and transfer when programmatic filtering in a Searcher is used.

## Selecting summary fields in YQL

A [YQL](query-language.html) statement can also be used to filter which fields from a document summary
to include in results. Note that this is just a field filter in the container -
a summary containing all fields of a summary class is always
fetched from content nodes, so to optimize performance it is necessary to create custom summary classes.

```
$ vespa query "select artist, album, documentid, sddocname from music where album contains 'head'"
```
```
{% highlight json %}
{
    "root": { },
        "children": [
            {
                "id": "id:mynamespace:music::a-head-full-of-dreams",
                "relevance": 0.16343879032006284,
                "source": "mycontentcluster",
                "fields": {
                    "sddocname": "music",
                    "documentid": "id:mynamespace:music::a-head-full-of-dreams",
                    "artist": "Coldplay",
                    "album": "A Head Full of Dreams"
                }
            }
        ]
    }
}
{% endhighlight %}
```

Use `*` to select all the fields of the chosen document summary class used,
(which is `default` by default).

```
$ vespa query "select * from music where album contains 'head'"
```
```
{% highlight json %}
{
    "root": { },
        "children": [
            {
                "id": "id:mynamespace:music::a-head-full-of-dreams",
                "relevance": 0.16343879032006284,
                "source": "mycontentcluster",
                "fields": {
                    "sddocname": "music",
                    "documentid": "id:mynamespace:music::a-head-full-of-dreams",
                    "artist": "Coldplay",
                    "album": "A Head Full of Dreams",
                    "year": 2015,
                    "category_scores": {
                        "type": "tensor(cat{})",
                        "cells": {
                            "pop": 1.0,
                            "rock": 0.20000000298023224,
                            "jazz": 0.0
                        }
                    }
                }
            }
        ]
    }
}
{% endhighlight %}
```

## Summary field rename

Summary classes may define fields by names not used in the document type:

```
    document-summary rename-summary {
        summary artist_name {
            source: artist
        }
    }
```

Refer to the [schema reference](reference/schema-reference.html#source) for
adding [attribute](reference/schema-reference.html#add-or-remove-an-existing-document-field-from-document-summary) and
[non-attribute](reference/schema-reference.html#add-or-remove-a-new-non-attribute-document-field-from-document-summary) fields - some changes require re-indexing.

## Dynamic snippets

Use [dynamic](reference/schema-reference.html#summary)
to generate dynamic snippets from fields based on the query keywords.
Example from Vespa Documentation Search - see the
[schema](https://github.com/vespa-cloud/vespa-documentation-search/blob/main/src/main/application/schemas/doc.sd):

```
document doc {

    field content type string {
        indexing: summary | index
        summary : dynamic
    }
```

A query for *document summary* returns:

> Use **document summaries** to configure which fields ...
> indexing: **summary** | index } } **document-summary**
> titleyear { **summary** title ...

The example above creates a dynamic summary with the matched terms highlighted.
The latter is called [bolding](reference/schema-reference.html#bolding)
and can be enabled independently of dynamic summaries.

Refer to the [reference](reference/schema-reference.html#summary) for the response format.

### Dynamic snippet configuration

You can configure generation of dynamic snippets by adding an instance of the
[vespa.config.search.summary.juniperrc config](https://github.com/vespa-engine/vespa/blob/master/searchsummary/src/vespa/searchsummary/config/juniperrc.def)
in services.xml inside the <content> cluster tag for the content cluster in question. E.g:

```
<content ...>
    ...
    <config name="vespa.config.search.summary.juniperrc">
      <max_matches>2</max_matches>
      <length>1000</length>
      <surround_max>500</surround_max>
      <min_length>300</min_length>
    </config>
    ...
</content>
```

Numbers here are in bytes.

## Performance

[Attribute](attributes.html) fields are held in memory.
This means summaries are memory-only operations if all fields requested are attributes,
and is the optimal way to get high query throughput.
The other document fields are stored as blobs in the
[document store](proton.html#document-store).
Requesting these fields may therefore require a disk access, increasing latency.

{% include important.html content='The default summary class will access the document store
as it includes the [documentid](reference/default-result-format.html#documentid) field
which is stored there.
For maximum query throughput using memory-only access, use a dedicated summary class with attributes only.' %}

When using additional summary classes to increase performance,
only the network data size is changed - the data read from storage is unchanged.
Having "debug" fields with summary enabled will hence also affect the
amount of information that needs to be read from disk.

See [query execution](query-api.html#query-execution) -
breakdown of the summary (a.k.a. result processing, rendering) phase:
* The document summary latency on the content node,
  tracked by [content_proton_search_protocol_docsum_latency_average](operations/metrics.html).
* Getting data across from content nodes to containers.
* Deserialization from internal binary formats (potentially) to Java objects
  if touched in a [Searcher](searcher-development.html),
  and finally serialization to JSON (default rendering) + rendering and network.

The work, and thus latency, increases with more [hits](reference/query-api-reference.html#hits).
Use [query tracing](query-api.html#query-tracing) to analyze performance.

Refer to [content node summary cache](performance/caches-in-vespa.html#content-node-summary-cache).
