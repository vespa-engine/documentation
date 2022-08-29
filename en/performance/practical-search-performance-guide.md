---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa query performance - a practical guide"
---

This is a practical Vespa query performance guide. It uses the
[Last.fm](http://millionsongdataset.com/lastfm/) tracks dataset to illustrate Vespa query performance.
Latency numbers mentioned in the guide are obtained from running this guide on a MacBook Pro x86.

This guide covers the following query serving performance aspects:
- [Basic text search query performance](#basic-text-search-query-performance)
- [Hits and document summaries](#hits-and-summaries)
- [Multivalued query operators (dotProduct, weakAnd, wand, weightedSet)](#multi-valued-query-operators)
- [Searching attribute fields](#searching-attribute-fields)
- [Searching attribute fields with fast-search](#searching-attribute-fields-using-fast-search)
- [Ranking with tensor computations](#tensor-computations)
- [Multithreaded search and ranking](#multithreaded-search-and-ranking)
- [Range-search with hit limits for early termination](#advanced-range-search-with-hitlimit)
- [Early termination using match phase limits](#match-phase-limit---early-termination)
- [Advanced query tracing](#advanced-query-tracing)

The guide includes step-by-step instructions on how to reproduce the experiments. 
This guide is best read after having read the [Vespa Overview](../overview.html) documentation first.

{% include pre-req.html memory="4 GB" extra-reqs='
<li>Python3 for converting the dataset to Vespa JSON.</li>
<li><code>curl</code> to download the dataset and run the Vespa health-checks.</li>' %}


## Installing vespa-cli 

This tutorial uses [Vespa-CLI](../vespa-cli.html),
Vespa CLI is the official command-line client for Vespa.ai. 
It is a single binary without any runtime dependencies and is available for Linux, macOS and Windows.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ brew install vespa-cli 
</pre>
</div>

## Dataset
This guide uses the [Last.fm](http://millionsongdataset.com/lastfm/) tracks dataset. 
Note that the dataset is released under the following terms:

>Research only, strictly non-commercial. For details, or if you are unsure, please contact Last.fm. 
>Also, Last.fm has the right to advertise and refer to any work derived from the dataset.

To download the dataset directly (120 MB zip file), run:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o lastfm_test.zip \
    http://millionsongdataset.com/sites/default/files/lastfm/lastfm_test.zip 
$ unzip lastfm_test.zip
</pre>
</div>

The downloaded data needs to be converted to
[the JSON format expected by Vespa](../reference/document-json-format.html). 

This [python](https://www.python.org/) script is used to traverse the dataset
files and create a JSONL formatted feed file with Vespa feed operations.
The schema for this feed is introduced in the next sections. 

<pre style="display:none" data-test="file" data-path="create-vespa-feed.py">
import os
import sys
import json
import unicodedata

directory = sys.argv[1]
seen_tracks = set() 

def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def process_file(filename):
    global seen_tracks
    with open(filename) as fp:
        doc = json.load(fp)
        title = doc['title']
        artist = doc['artist']
        hash = title + artist
        if hash in seen_tracks:
            return
        else:
            seen_tracks.add(hash) 

        track_id = doc['track_id']
        tags = doc['tags']
        tags_dict = dict()
        for t in tags:
            k,v = t[0],int(t[1])
            tags_dict[k] = v
        similars = doc['similars']
        tensor_cells = []
        keys_seen = dict()
        for s in similars:
            k,v = s[0],float(s[1])
            if k in keys_seen:
                continue
            else:
                keys_seen[k] = 1
            cell = {
                "address": {
                    "trackid": k
                },
                "value": v
            }
            tensor_cells.append(cell)

        vespa_doc = {
            "put": "id:music:track::%s" % track_id,
                "fields": {
                    "title": remove_control_characters(title),
                    "track_id": track_id,
                    "artist": remove_control_characters(artist),
                    "tags": tags_dict,
                    "similar": {
                        "cells": tensor_cells
                    }
            }
        }
        print(json.dumps(vespa_doc))

sorted_files = []
for root, dirs, files in os.walk(directory):
    for filename in files:
        filename = os.path.join(root, filename)
        sorted_files.append(filename)
sorted_files.sort()
for filename in sorted_files:
    process_file(filename)
</pre>

<pre>{% highlight python%}
import os
import sys
import json
import unicodedata

directory = sys.argv[1]
seen_tracks = set() 

def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def process_file(filename):
    global seen_tracks
    with open(filename) as fp:
        doc = json.load(fp)
        title = doc['title']
        artist = doc['artist']
        hash = title + artist
        if hash in seen_tracks:
            return
        else:
            seen_tracks.add(hash) 

        track_id = doc['track_id']
        tags = doc['tags']
        tags_dict = dict()
        for t in tags:
            k,v = t[0],int(t[1])
            tags_dict[k] = v
        similars = doc['similars']
        tensor_cells = []
        keys_seen = dict()
        for s in similars:
            k,v = s[0],float(s[1])
            if k in keys_seen:
                continue
            else:
                keys_seen[k] = 1
            cell = {
                "address": {
                    "trackid": k
                },
                "value": v
            }
            tensor_cells.append(cell)

        vespa_doc = {
            "put": "id:music:track::%s" % track_id,
                "fields": {
                    "title": remove_control_characters(title),
                    "track_id": track_id,
                    "artist": remove_control_characters(artist),
                    "tags": tags_dict,
                    "similar": {
                        "cells": tensor_cells
                    }
            }
        }
        print(json.dumps(vespa_doc))

sorted_files = []
for root, dirs, files in os.walk(directory):
    for filename in files:
        filename = os.path.join(root, filename)
        sorted_files.append(filename)
sorted_files.sort()
for filename in sorted_files:
    process_file(filename)
{% endhighlight %}</pre>

Run the script and create the `feed.jsonl` file:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ python3 create-vespa-feed.py lastfm_test > feed.jsonl
</pre>
</div>

## Create a Vespa Application Package

A [Vespa application package](../application-packages.html) is the set 
of configuration files and Java plugins that together define the behavior of a Vespa system:
what functionality to use, the available document types, how ranking will be done,
and how data will be processed during feeding and indexing.

The minimum required files to create the basic search application are `track.sd` and `services.xml`.
Create directories for the configuration files:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir -p app/schemas; mkdir -p app/search/query-profiles/
</pre>
</div>

### Schema

A Vespa [schema](../schemas.html) is a configuration of a document type and ranking and
compute specifications. This app use a `track` schema defined as:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

    document track {

        field track_id type string {
            indexing: summary | attribute
            rank: filter
            match: word
        }

        field title type string {
            indexing: summary | index
            index: enable-bm25
        }

        field artist type string {
            indexing: summary | index
        }

        field tags type weightedset&lt;string&gt; {
            indexing: summary | attribute
        }

        field similar type tensor&lt;float&gt;(trackid{}) {
            indexing: summary | attribute
        }
    }

    fieldset default {
        fields: title, artist
    }
}
</pre>

Notice that the `track_id` field has :

- [rank: filter](../reference/schema-reference.html#rank). 
This setting can save resources when matching against the field.   
- [match: word](../reference/schema-reference.html#match). 
This is a database-style matching mode, preserving punctuation characters. 

### Services Specification

The [services.xml](../reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.

<pre data-test="file" data-path="app/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

    &lt;container id="default" version="1.0"&gt;
        &lt;search/&gt;
        &lt;document-api/&gt;
    &lt;/container&gt;

    &lt;content id="tracks" version="1.0"&gt;
        &lt;redundancy&gt;1&lt;/redundancy&gt;
        &lt;documents&gt;
            &lt;document type="track" mode="index"&gt;&lt;/document&gt;
        &lt;/documents&gt;
        &lt;nodes&gt;
            &lt;node distribution-key="0" hostalias="node1"&gt;&lt;/node&gt;
        &lt;/nodes&gt;
    &lt;/content&gt;
&lt;/services&gt;
</pre>

The default [query profile](../query-profiles.html) can be used to override
default query api settings for all queries.

The following enables [presentation.timing](../reference/query-api-reference.html#presentation.timing) and
renders `weightedset` fields as a JSON maps.

<pre data-test="file" data-path="app/search/query-profiles/default.xml">
&lt;query-profile id=&quot;default&quot;&gt;
    &lt;field name=&quot;presentation.timing&quot;&gt;true&lt;/field&gt;
    &lt;field name=&quot;renderer.json.jsonWsets&quot;&gt;true&lt;/field&gt;
&lt;/query-profile&gt;
</pre>

## Deploy the application package

The application package can now be deployed to a running Vespa instance.
See also the [Vespa quick start guide](../vespa-quick-start.html).

Start the Vespa container image using Docker:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker run --detach --name vespa --hostname vespa-container \
  --publish 8080:8080 --publish 19071:19071 --publish 19110:19110 \
  vespaengine/vespa
</pre>
</div>

Starting the container can take a short while. Before continuing, make sure
that the configuration service is running by using `vespa status deploy`. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa config set target local
$ vespa status deploy --wait 300 
</pre>
</div>

Once ready, the Vespa application can be deployed using the Vespa CLI:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

## Index the dataset

This guide uses the [vespa feed client](../vespa-feed-client.html) to
feed the feed file generated in the previous section:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o vespa-feed-client-cli.zip \
    https://search.maven.org/remotecontent?filepath=com/yahoo/vespa/vespa-feed-client-cli/{{site.variables.vespa_version}}/vespa-feed-client-cli-{{site.variables.vespa_version}}-zip.zip
$ unzip vespa-feed-client-cli.zip
$ ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --file feed.jsonl --endpoint http://localhost:8080
</pre>
</div>

## Basic text search query performance
The following sections uses the Vespa [query api](../reference/query-api-reference.html) and 
formulate queries using Vespa [query language](../query-language.html). 
For readability, all query examples are expressed using the 
[vespa-cli](../vespa-cli.html) command which supports running queries against an Vespa instance. 
The CLI uses the Vespa http search api internally. 
Use `vespa query -v` to see the actual http request sent:

<pre>
$ vespa query -v 'yql=select ..'
</pre>

The first query uses `where true` to match all all `track` documents.  
It also uses [hits](../reference/query-api-reference.html#hits) to specify how many
documents to return in the response:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"documents": 95666'>
$ vespa query \
    'yql=select artist, title, track_id, tags from track where true' \
    'hits=1'
</pre>
</div>

The [result json output](../reference/default-result-format.html) for this query will 
look something like this:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.009000000000000001,
        "summaryfetchtime": 0.001,
        "searchtime": 0.011
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 95666
        },
        "coverage": {
            "coverage": 100,
            "documents": 95666,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "index:tracks/0/632facf01973795ba294b7d5",
                "relevance": 0.0,
                "source": "tracks",
                "fields": {
                    "track_id": "TRRRGWV128F92FC7E0",
                    "title": "Zombies",
                    "artist": "True Blood"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

Observations: 

- The query searched one node (`coverage.nodes`) and the 
coverage (`coverage.coverage`) was 100%, 
see [graceful-degradation](../graceful-degradation.html) for more information about 
the `coverage` element, and Vespa timeout behavior. Vespa's default timeout is 0.5 seconds.   
- The query matched a total of 95666 documents (`totalCount`) out of 
95666 documents available (`coverage.documents`).

The response `timing` has three fields. A Vespa query is executed in two protocol phases:

- Query matching phase which fans the query out from the stateless container 
to a content group, each node in the group finds the nodes top-k documents and returns k. 
The stateless container then merges the nodes' k hits each to obtain a globally ordered top-k documents.
- Summary phase which asks the content nodes that produced the global top-k hits for summary data. 

See also [Life of a query in Vespa](sizing-search.html#life-of-a-query-in-vespa). The `timing`
in the response measures the time it takes to execute these two phases:

- `querytime` - Time to execute the first protocol phase/matching phase. 
- `summaryfetchtime` - Time to execute the summary fill protocol phase for the globally ordered top-k hits.
- `searchtime` Is roughly the sum of the above and is close to what a client will observe (except network latency).

All three metrics are second resolution. Moving on, the following query performs a free text query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=1'
</pre>
</div>

This query request combines YQL [userQuery()](../reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](../reference/simple-query-language-reference.html), the 
default [query type](../reference/query-api-reference.html#model.type) is 
using `all` requiring that all the terms match. 

The above example searches for *total AND eclipse AND of AND the AND heart* in the fieldset `default`, 
which in the schema includes the `title` and `artist` fields. 
Since the request did not specify any [ranking](../ranking.html) parameters,
the matched documents were ranked by Vespa's default 
text rank feature: [nativeRank](../nativerank.html).

The result output for the above query:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.012,
        "summaryfetchtime": 0.001,
        "searchtime": 0.014
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1
        },
        "coverage": {
            "coverage": 100,
            "documents": 95666,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "index:tracks/0/3f18869c19c25e3ae237702f",
                "relevance": 0.13274821039905835,
                "source": "tracks",
                "fields": {
                    "track_id": "TRUKHZD128F92DF70A",
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

This query only matched one document because the query terms were ANDed. 
Matching can be relaxed to `type=any` instead using 
[query model type](../reference/query-api-reference.html#model.type).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=1' \
    'type=any'
</pre>
</div>

Now, the query matches 24,053 documents and is considerably slower than the previous `all` query. 
Comparing `querytime` of these two query examples, the one which matches the most documents 
have the highest `querytime`. In worst case, the search query matches all documents, and 
without any techniques for early termination or skipping, all matches are exposed to ranking.
Query performance is greatly impacted by the number of documents 
that matches the query specification. Generally, type `any` queries 
requires more query compute resources than type `all`.  

There is an algorithmic optimization available for `type=any` queries, using
the `weakAnd` query operator which implements the WAND algorithm. 
See the [using wand with Vespa](../using-wand-with-vespa.html) for an 
introduction to the algorithm.

Run the same query, but instead of `type=any` use `type=weakAnd`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=1' \
    'type=weakAnd'
</pre>
</div>

Compared to the type `any` query which fully ranked 24,053 documents, 
, `weakAnd` only fully ranks 3,679 documents.
Also notice that the faster search returns the same document at the first position. 
Conceptually a search query is about finding the documents that match the query, 
then score the documents using a ranking model. 
In the worst case, a search query can match all documents which will expose
all of them to the ranking. 

## Hits and summaries 
The previous examples used `hits=1` query parameter, and in the previous
query examples, the `summaryfetchtime` has been close to constant. 

The following query requests considerably more hits, note that the result is piped to `head`
to increase readability:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=200' \
    'type=weakAnd' |head -40 
</pre>
</div>

Increasing number of hits, increases `summaryfetchtime` significantly from 
the previous query examples, while `querytime` is relatively unchanged. 
Repeating the query a second time will reduce the `summaryfetchtime`
due to the content node summary cache, 
see [caches in Vespa](../performance/caches-in-vespa.html) for details.

There are largely four factors which determines the `summaryfetchtime`:

- The number of hits requested and number of content nodes that produced the 
query result which makes up the `querytime`.
 With many content nodes in the group the query was dispatched to,
 we expect that top-ranking hits would be distributed across the nodes so that each node
 does less work.
- The network package size of each hit. 
Returning hits with larger fields, costs more resources and 
higher `summaryfetchtime` than smaller docs. Less is more. 
- The summary used with the query, and which fields go into the summary. 
For example, a [document-summary](../document-summaries.html) which only contain 
fields that are defined as `attribute` will be read from memory. For the `default` summary, or others 
containing at least one non-attribute field, a fill will potentially access data 
from summary storage on disk. Read more about in-memory [attribute](../attributes.html) fields.
- [summary-features](../reference/schema-reference.html#summary-features) used to return computed
 [rank features](../reference/rank-features.html) from the content nodes. 

Creating a dedicated [document-summary](../document-summaries.html) which
only contain the `track_id` field can improve performance, since `track_id` is defined in the schema with
`attribute`, any summary fetches using this document summary will be reading data from in-memory. 
In addition, since the summary only contain one field, it saves network time as less data is
transferred during the summary fill phase. 

<pre>
document-summary track_id {
    summary track_id type string { 
        source: track_id
    }
}
</pre>

The new schema then becomes:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

    document track {

        field track_id type string {
            indexing: summary | attribute
            rank: filter
            match: word
        }

        field title type string {
            indexing: summary | index
            index: enable-bm25
        }

        field artist type string {
            indexing: summary | index
        }

        field tags type weightedset&lt;string&gt; {
            indexing: summary | attribute
        }

        field similar type tensor&lt;float&gt;(trackid{}) {
            indexing: summary | attribute
        }
    }

    fieldset default {
        fields: title, artist
    }

    document-summary track_id {
        summary track_id type string { 
            source: track_id
        }
    }
}
</pre>

Re-deploy the application: 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

Re-executing the query using the `track_id` `document-summary` is done by
setting the [summary](../reference/query-api-reference.html#presentation.summary) 
query request parameter:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="track_id">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=200' \
    'type=weakAnd' \
    'summary=track_id' |head -40 
</pre>
</div>

In this particular case the `summaryfetchtime` difference is not that large, but for larger number of hits and 
larger documents the difference is significant. Especially in single content node deployments. 

A note on select field scoping with YQL, e.g. `select title, track_id from ..`. 
When using the default summary by not using a summary parameter, all fields are delivered from the 
content nodes to the stateless search container in the summary fill phase,
regardless of field scoping. The search container removes the set of fields not 
selected and renders the result. Hence, select scoping only reduces the amount of data 
transferred back to the client, and does not impact or optimize the performance 
of the internal communication and potential summary cache miss. 
For optimal performance for use cases asking for large number of hits to the client it is
recommended to use dedicated document summaries. 
Note also that Vespa per default limits the max hits to 400 per default, 
the behavior can be overridden in the 
[default queryProfile](../reference/query-api-reference.html#queryProfile).

When requesting large amount of data with hits, it is recommended to use result compression. 
Vespa will compress if the HTTP client uses
the [Accept-Encoding](https://www.rfc-editor.org/rfc/rfc9110.html#name-accept-encoding) HTTP request header:
<pre>
Accept-Encoding: gzip
</pre>

## Searching attribute fields 

The previous section covered free text searching in a `fieldset` containing fields with
`indexing:index`. See [indexing reference](../reference/schema-reference.html#indexing). 
Fields of [type string](../reference/schema-reference.html#field-types) are 
treated differently depending on having `index` or `attribute`:

- `index` integrates with [linguistic](../linguistics.html) processing and is matched using 
[match:text](../reference/schema-reference.html#match). 

- `attribute` does not integrate with linguistic processing and is matched using 
[match:word](../reference/schema-reference.html#match). 

With `index` Vespa builds inverted index data structures which roughly consists of:

- A dictionary of the unique text tokens (after linguistic processing)
- Posting lists for each unique text token in the collection. Posting lists comes in different
formats, and using `rank: filter` can help guide the decision on what format to use. Bitvector
representation is the most compacting post list representation. 

With `attribute`, Vespa per default, does not build any inverted index like data structures for 
potential faster query evaluation. See [Wikipedia:Inverted Index](https://en.wikipedia.org/wiki/Inverted_index) 
and [Vespa internals](../proton.html#index). 
The reason for this default setting is that Vespa `attribute` fields can be used
for many different aspects: [ranking](../ranking.html), [result grouping](../grouping.html),
 [result sorting](../reference/sorting.html), and finally searching/matching. 

The following section focuses on the `tags` field which we defined with `attribute`,
matching in this field will be performed using `match:word` which is the
default match mode for string fields with `indexing: attribute`.
The `tags` field is of type [weightedset](../reference/schema-reference.html#type:weightedset).

<pre>
 field tags type weightedset&lt;string&gt; {
      indexing: summary | attribute
 }
</pre>

Weightedset is a field type that allows representing a tag with an integer weight, which can be used for ranking. 
In this case, there is no inverted index structure,
and matching against the `tags` field is performed as a linear scan.
The following scans for documents where `tags` match *rock*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"rock":'>
$ vespa query \
    'yql=select track_id, tags from track where tags contains "rock"' \
    'hits=1' 
</pre>
</div>

The query matches 8,160 documents, notice that for `match: word`, matching can also include whitespace,
or generally punctuation characters which are removed and not searchable
when using `match:text` with string fields that have `index`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"classic rock":'>
$ vespa query \
    'yql=select track_id, tags from track where tags contains "classic rock"' \
    'hits=1' 
</pre>
</div>
The above query matches exactly tags with "classic rock", not "rock" and also not "classic rock music". 

Another query searching for *rock* or *pop*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"rock":'>
$ vespa query \
    'yql=select track_id, tags from track where tags contains "rock" or tags contains "pop"' \
    'hits=1' 
</pre>
</div>

In all these examples searching the `tags` field, the matching is done by a linear scan through all
`track` documents. The `tags` search can be combined with regular 
free text query terms searching fields that do have inverted index structures:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"rock"'>
$ vespa query \
    'yql=select track_id, tags from track where tags contains "rock" and userQuery()' \
    'hits=1' \
    'query=total eclipse of the heart'
</pre>
</div>

In this case - the query terms searching the default fieldset will restrict the number of 
documents that needs to be scanned for the _tags_ constraint. This query is automatically optimized
by the Vespa query planner. 

### Searching attribute fields using fast-search 
This section adds `fast-search` to the `tags` field to speed up searches where there are no 
other query filters which restricts the search. The schema with `fast-search`:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

    document track {

        field track_id type string {
            indexing: summary | attribute
            rank: filter
            match: word
        }

        field title type string {
            indexing: summary | index
            index: enable-bm25
        }

        field artist type string {
            indexing: summary | index
        }

        field tags type weightedset&lt;string&gt; {
            indexing: summary | attribute
            attribute: fast-search
        }

        field similar type tensor&lt;float&gt;(trackid{}) {
            indexing: summary | attribute
        }
    }

    fieldset default {
        fields: title, artist
    }

    document-summary track_id {
        summary track_id type string { 
            source: track_id
        }
    }
}
</pre>

Re-deploy the application: 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

The above will print a WARNING:

<pre>
vespa deploy --wait 300 app/ 
Uploading application package ... done

Success: Deployed app/
WARNING Change(s) between active and new application that require restart:
In cluster 'tracks' of type 'search':
    Restart services of type 'searchnode' because:
        1) Document type 'track': Field 'tags' changed: add attribute 'fast-search'

Waiting up to 300 seconds for query service to become available ...
</pre>   

To enable `fast-search`, content node(s) needs to be restarted to re-build the fast-search data structures
for the attribute. 

The following uses [vespa-sentinel-cmd command tool](../reference/vespa-cmdline-tools.html#vespa-sentinel-cmd)
to restart the searchnode process:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker exec vespa /opt/vespa/bin/vespa-sentinel-cmd restart searchnode
</pre>
</div>

This step requires waiting for the searchnode, use the [health state api](../reference/metrics.html):
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ curl -s http://localhost:19110/state/v1/health
</pre>
</div>

Wait for status code to flip to `up` before querying again:

<pre>{% highlight json%}
{
    "status": {
        "code": "up"
    }
}
{% endhighlight %}</pre>

<pre style="display:none" data-test="exec">
$ sleep 60
</pre>

Once up, execute the `tags` query again:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"rock":'>
$ vespa query \
    'yql=select track_id, tags from track where tags contains "rock" or tags contains "pop"' \
    'hits=1' 
</pre>
</div>

Now the `querytime` will be a few milliseconds since Vespa has built index structures to support
`fast-search` in the attribute. The downside of enabling `fast-search` is 
increased memory usage and slightly reduced indexing throughput. See also
[when to use fast-search for attributes](feature-tuning.html#when-to-use-fast-search-for-attribute-fields).

For use cases requiring `match:text` when searching multi-valued string field types 
like [weightedset](../reference/schema-reference.html#type:weightedset), see
[searching multi-value fields](../searching-multi-valued-fields.html).

For fields that don't need any match ranking features, it's strongly recommended
to use [rank: filter](../reference/schema-reference.html#rank).

<pre>
field availability type int {
    indexing: summary | attribute
    rank: filter
    attribute {
        fast-search
    }
}
</pre>

With the settings above, bit vector posting list representations are used. This is especially efficient
when used in combination with [TAAT (term at a time)](feature-tuning.html#hybrid-taat-daat) 
query evaluation. For some cases with many query terms, enabling `rank: filter` can reduce match latency
by 75%. 

## Multi-valued query operators

This section covers [multi-value query operators](../multivalue-query-operators.html) 
and their query performance characteristics. Many real-world search and recommendation use cases 
involve structured multivalued queries.

Assuming a process has learned a sparse user profile representation, which, for a given user, based
on past interactions with a service, could produce a user profile with 
*hard rock*, *rock*, *metal* and *finnish metal*. Sparse features from a fixed vocabulary/feature space.

Retrieving and ranking using sparse representations can be done using
the dot product between the sparse user profile representation and document representation. In the
track example, the `tags` field could be the document side sparse representation. Each document
is tagged with multiple `tags` using a weight, and similar the sparse user profile
representation could use weights.

In the following examples, the [dotProduct()](../reference/query-language-reference.html#dotproduct) and
[wand()](../reference/query-language-reference.html#wand) query operators are used.

To configure [ranking](../ranking.html), add a `rank-profile` to the schema:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

    document track {

        field track_id type string {
            indexing: summary | attribute
            rank: filter
            match: word
        }

        field title type string {
            indexing: summary | index
            index: enable-bm25
        }

        field artist type string {
            indexing: summary | index
        }

        field tags type weightedset&lt;string&gt; {
            indexing: summary | attribute
            attribute: fast-search
        }

        field similar type tensor&lt;float&gt;(trackid{}) {
            indexing: summary | attribute
        }
    }

    fieldset default {
        fields: title, artist
    }

    document-summary track_id {
        summary track_id type string { 
            source: track_id
        }
    }

    rank-profile personalized {
        first-phase {
            expression: rawScore(tags)
        }
    }
}
</pre>

The `dotProduct`and `wand` query operators produce a `rank feature` called
[rawScore(name)](../reference/rank-features.html#rawScore(field)). This feature calculates
the sparse dot product between the query and document weights. 

Deploy the application again:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

The [dotProduct](../reference/query-language-reference.html#dotproduct)
query operator accepts a field to match over and supports
[parameter substitution](../reference/query-language-reference.html#parameter-substitution).
Using substitution is recommended for large inputs as it saves compute resources when parsing the YQL input. 

The following example assumes a learned sparse representation, with equal weight:
<pre>
userProfile={"hard rock":1, "rock":1,"metal":1, "finnish metal":1}
</pre>

This userProfile is referenced as a parameter 

<pre>
where dotProduct(tags, @userProfile)
</pre>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Vastarannan valssi">
$ vespa query \
    'yql=select track_id, title, artist, tags from track where dotProduct(tags, @userProfile)' \
    'userProfile={"hard rock":1, "rock":1,"metal":1, "finnish metal":1}' \
    'hits=1' \
    'ranking=personalized'
</pre>
</div>
The query also specifies the `rank-profile` `personalized`, if not specified, ranking would be
using `nativeRank`.  The above query returns the following response:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.004,
        "summaryfetchtime": 0.001,
        "searchtime": 0.006
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 10323
        },
        "coverage": {
            "coverage": 100,
            "documents": 95666,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "index:tracks/0/74d3f4df2989650b2cc095be",
                "relevance": 400.0,
                "source": "tracks",
                "fields": {
                    "track_id": "TRJTBAO128F932191C",
                    "title": "Vastarannan valssi",
                    "artist": "Viikate",
                    "tags": {
                        "Suomi": 100,
                        "rautalanka": 100,
                        "suomi rock": 100,
                        "hard rock": 100,
                        "melodic metal": 100,
                        "finnish": 100,
                        "finnish metal": 100,
                        "metal": 100,
                        "rock": 100
                    }
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

Notice that the query above, will brute-force rank all tracks where the `tags` field matches *any* of the multivalued
userProfile features. Due to this, the query ranks 10,323 tracks as seen by `totalCount`. 
Including for example *pop* in the userProfile list increases the number of hits to 13,638. 

For a large user profile with many learned features/tags, one would easily match and rank the entire document collection. 
Also notice the `relevance` score which is 400 since the document matches all the query input tags (4x100 = 400).

To optimize the evaluation, the [wand query operator](../reference/query-language-reference.html#wand)
can be used. The `wand` query operator supports setting a target number of top ranking hits that gets
exposes to the `first-phase` ranking function. 

Repeating the query from above, replacing `dotProduct` with `wand`:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Vastarannan valssi">
$ vespa query \
    'yql=select track_id, title, artist, tags from track where {targetHits:10}wand(tags, @userProfile)' \
    'userProfile={"hard rock":1, "rock":1,"metal":1, "finnish metal":1}' \
    'hits=1' \
    'ranking=personalized'
</pre>
</div>

The `wand` query operator retrieves the exact same hit at rank 1 which is the expected behavior.
The `wand` query operator is safe, meaning, it returns the same top-k results as the `dotProduct` query operator. 

For larger document collections, the *wand* query operator can significantly
improve query performance compared to `dotProduct`. 

*wand* is a type of query operator which performs matching and ranking interleaved and skipping documents
which cannot make it into the top k results. See the [using wand with Vespa](../using-wand-with-vespa.html)
guide for more details on the WAND algorithm. 

Finally, these multi-value query operators works on both single valued fields, and array fields, 
but optimal performance is achieved using the [weightedset](../reference/schema-reference.html#type:weightedset) 
field type. The `weightedset` field type only supports integer weights. The next section
covers tensors that support more floating point number types. 

## Tensor Computations
The previous sections covered matching and where query matching query operators 
also produced rank features which could be used to influence the order of the hits returned. 
In this section we look at ranking with [tensor computations](../tensor-examples.html) 
using [tensor expressions](../tensor-user-guide.html). 

Tensor computations can be used to calculate dense dot products, sparse
dot products, matrix multiplication, neural networks and more. Tensor computations can be performed 
on documents that are retrieved by the query matching operators. The only exception to this is
dense single order tensors (vectors) where Vespa also supports "matching" using [(approximate) nearest
neighbor search](..//approximate-nn-hnsw.html). 


The `track` schema was defined with a `similar` tensor field with one named *mapped* dimension. 
*Mapped* tensors can be used to represent sparse feature representations, similar
to the `weightedset` field, but in a more generic way, and here using `float` to represent
the tensor cell value. 

<pre>
field similar type tensor&lt;float&gt;(trackid{}) {
      indexing: summary | attribute
}
</pre>

Inspecting one document, using the vespa-cli (Wraps [Vespa document/v1 api](../document-v1-api-guide.html)):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bryan Adams">
$ vespa document get id:music:track::TRQIQMT128E0791D9C
</pre>
</div>

Returns:

<pre>{% highlight json%}
{
    "pathId": "/document/v1/music/track/docid/TRUAXHV128F42694E8",
    "id": "id:music:track::TRUAXHV128F42694E8",
    "fields": {
        "artist": "Bryan Adams",
        "title": "Summer Of '69",
        "similar": {
            "cells": [
                {
                    "address": {
                        "trackid": "TRWJIPT128E0791D99"
                    },
                    "value": 1.0
                },
                {
                    "address": {
                        "trackid": "TRKPGHH128F1453DD0"
                    },
                    "value": 0.9129049777984619
                },
                 {
                    "address": {
                        "trackid": "TRGVORX128F4291DF1"
                    },
                    "value": 0.3269079923629761
                }
            ]
        },
        "tags": {
            "All time favourites": 1,
            "male vocalists": 7,
            "singer-songwriter": 6,
            "happy": 2,
            "Driving": 3,
            "classic rock": 59,
            "loved": 1,
            "Energetic": 2,
            "male vocalist": 1,
            "dance": 1,
            "soft rock": 2,
            "1980s": 1
        }
    }
}
{% endhighlight %}</pre>

In the lastfm collection, each track lists similar tracks with a similarity score using float resolution, according to this
similarity algorithm the most similar track to this sample document is `TRWJIPT128E0791D99` with a similarity score of 1.0. 

Searching for that doc using the query api:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bryan Adams">
$ vespa query \
    'yql=select title, artist from track where track_id contains "TRWJIPT128E0791D99"' \
    'hits=1'  
</pre>
</div>

Note that `track_id` was not defined with `fast-search` so searching it without any other query terms makes this
query a linear scan over all tracks.

The query returns:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.01,
        "summaryfetchtime": 0.002,
        "searchtime": 0.013000000000000001
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1
        },
        "coverage": {
            "coverage": 100,
            "documents": 95666,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "index:tracks/0/63eadd770a5dfde1f111aed7",
                "relevance": 0.0017429193899782135,
                "source": "tracks",
                "fields": {
                    "title": "Run To You",
                    "artist": "Bryan Adams"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

Given a single track, one could just retrieve the document and display the offline computed similar tracks, but,
if a user has listened to multiple tracks in a real time session, one could use a sparse dot product
between the user recent activity and the track similarity fields. For example, listening
to the following tracks:

- `TRQIQMT128E0791D9C` Summer Of '69 by Bryan Adams
- `TRWJIPT128E0791D99` Run To You by Bryan Adams
- `TRGVORX128F4291DF1` Broken Wings by Mr. Mister

Could be represented as a query tensor `query(user_liked)` and passed with the query request like this:

<pre>{% raw %}
input.query(user_liked)={{trackid:TRUAXHV128F42694E8 }:1.0,{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}
{% endraw %}</pre>

Both the document tensor and the query tensor are defined with `trackid{}` as the *named* *mapped* dimension. The 
sparse tensor dot product can then be expression in a `rank-profile`:

<pre>
rank-profile similar {
    inputs {
        query(user_liked) tensor&lt;float&gt;(trackid{})
    }
    first-phase {
        expression: sum(attribute(similar) * query(user_liked))
    }
}
</pre>

See [tensor user guide](../tensor-user-guide.html) for more on tensor fields and tensor computations
with Vespa. Adding this `rank-profile` to the document schema:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

    document track {

        field track_id type string {
            indexing: summary | attribute
            rank: filter
            match: word
        }

        field title type string {
            indexing: summary | index
            index: enable-bm25
        }

        field artist type string {
            indexing: summary | index
        }

        field tags type weightedset&lt;string&gt; {
            indexing: summary | attribute
            attribute: fast-search
        }

        field similar type tensor&lt;float&gt;(trackid{}) {
            indexing: summary | attribute
        }
    }

    fieldset default {
        fields: title, artist
    }

    document-summary track_id {
        summary track_id type string { 
            source: track_id
        }
    }

    rank-profile personalized {
        first-phase {
            expression: rawScore(tags)
        }
    }

    rank-profile similar {
        inputs {
            query(user_liked) tensor&lt;float&gt;(trackid{})
        }
        first-phase {
            expression: sum(attribute(similar) * query(user_liked))
        }
    }
}
</pre>

Deploy the application again :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

The track list of recently played tracks (or liked):

- `TRQIQMT128E0791D9C` Summer Of '69 by Bryan Adams
- `TRWJIPT128E0791D99` Run To You by Bryan Adams
- `TRGVORX128F4291DF1` Broken Wings by Mr. Mister

Is represented as the `query(user_liked)` query tensor
<pre>{% raw %}
input.query(user_liked)={{trackid:TRUAXHV128F42694E8 }:1.0,{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}
{% endraw %}</pre>

The first query example runs the tensor computation over all tracks using `where true`, notice also 
`ranking=similar`, without it, ranking with `nativeRank` would not take into account the query tensor:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">{% raw %}
$ vespa query \
    'yql=select title, artist, track_id from track where true' \
    'input.query(user_liked)={{trackid:TRUAXHV128F42694E8}:1.0,{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
    'ranking=similar' \
    'hits=5'
{% endraw %}</pre>
</div>

This query also retrieved some of the previous *liked* tracks. These can be removed
from the result set using the `not` query operator, in YQL represented as `!`.

<pre>
where !weightedSet(track_id, @userLiked) 
</pre>

The [weightedSet query operator](../reference/query-language-reference.html#weightedset) 
is the most efficient multi-value *filtering* query operator, either
using a positive filter (match if any of the keys matches) or negative filter using `not`
(remove from result if any of the keys matches).

See more examples in [feature-tuning set filtering](feature-tuning.html#multi-lookup-set-filtering).

Run query with the `not` filter:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">{% raw %}
$ vespa query \
    'yql=select title, artist, track_id from track where !weightedSet(track_id, @userLiked)' \
    'input.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
    'ranking=similar' \
    'hits=5' \
    'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}</pre>
</div>

Note that the tensor query input format is slightly different from the variable substitution supported for 
the multivalued query operators `wand`, `weightedSet` and `dotProduct`.
The above query produces the following result:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.121,
        "summaryfetchtime": 0.004,
        "searchtime": 0.125
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 95663
        },
        "coverage": {
            "coverage": 100,
            "documents": 95666,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "index:tracks/0/83b83fed0f2353b738591b15",
                "relevance": 1.1211640238761902,
                "source": "tracks",
                "fields": {
                    "track_id": "TRGJNAN128F42AEEF6",
                    "title": "Holding Out For A Hero",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/be76cb3bc209be6f818c91a7",
                "relevance": 1.0151770114898682,
                "source": "tracks",
                "fields": {
                    "track_id": "TRAONMM128F92DF7B0",
                    "title": "Africa",
                    "artist": "Toto"
                }
            },
            {
                "id": "index:tracks/0/074b6b937d0ff7b59710c279",
                "relevance": 1.0,
                "source": "tracks",
                "fields": {
                    "track_id": "TRFQRYC12903CD0BB9",
                    "title": "Kyrie",
                    "artist": "Mr. Mister"
                }
            },
            {
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 0.7835690081119537,
                "source": "tracks",
                "fields": {
                    "track_id": "TRKLIXH128F42766B6",
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/1c3ab39c8ffa4fd2ba388b4e",
                "relevance": 0.7503079921007156,
                "source": "tracks",
                "fields": {
                    "track_id": "TRAFGCY128F92E5F6C",
                    "title": "Hold The Line",
                    "artist": "Toto"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

This query retrieves 95,663 documents, and the three tracks previously *liked* were removed from the result.

The following example filters by a tags query, `tags:popular`, reducing the complexity of the
query as fewer documents gets ranked by the tensor ranking expression:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Ronan Keating">{% raw %}
$ vespa query \
    'yql=select title,artist, track_id from track where tags contains "popular" and !weightedSet(track_id,@userLiked)' \
    'input.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
    'ranking=similar' \
    'hits=5' \
    'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}</pre>
</div>

With fewer matches to score using the tensor expression the latency decreases. In this query case,
latency is strictly linear with number of matches. One could also use a combination of `wand` for
efficient retrieval and tensor computations for ranking. Notice that  `querytime` of the unconstrained search 
was around 120 ms which is on the high side for real-time serving. 

The sparse tensor product can be optimized by adding `attribute: fast-search` to the mapped field tensor. 
`attribute: fast-search` is supported for `tensor` fields using mapped dimensions, or mixed tensors using 
both mapped and dense dimensions. The cost of doing this is increased memory usage. The schema
with `attribute: fast-search` added to the `similar` tensor field:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {
    document track {

        field track_id type string {
            indexing: summary | attribute
            rank: filter
            match: word
        }

        field title type string {
            indexing: summary | index
            index: enable-bm25
        }

        field artist type string {
            indexing: summary | index
        }

        field tags type weightedset&lt;string&gt; {
            indexing: summary | attribute
            attribute: fast-search
        }

        field similar type tensor&lt;float&gt;(trackid{}) {
            indexing: summary | attribute
            attribute: fast-search 
        }
    }

    fieldset default {
        fields: title, artist
    }

    document-summary track_id {
        summary track_id type string { 
            source: track_id
        }
    }

    rank-profile personalized {
        first-phase {
            expression: rawScore(tags)
        }
    }

    rank-profile similar {
        inputs {
            query(user_liked) tensor&lt;float&gt;(trackid{})
        }
        first-phase {
            expression: sum(attribute(similar) * query(user_liked))
        }
    }
}
</pre>

Deploy the application again :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

And again, adding `fast-search`, requires a re-start of the searchnode process:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker exec vespa /opt/vespa/bin/vespa-sentinel-cmd restart searchnode
</pre>
</div>

Wait for the searchnode to start by waiting for `status:code:up`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ curl -s http://localhost:19110/state/v1/health
</pre>
</div>

<pre style="display:none" data-test="exec">
$ sleep 60
</pre>

Re-run the tensor ranking query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">{% raw %}
$ vespa query \
    'yql=select title,artist, track_id from track where !weightedSet(track_id,@userLiked)' \
    'input.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
    'ranking=similar' \
    'hits=5' \
    'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}</pre>
</div>

The `querytime` dropped to 40 ms instead of 120 ms without the `fast-search` option. 
See also [performance considerations](../tensor-user-guide.html#performance-considerations)
when using tensor expression. Vespa supports `int8`, `bfloat16`, `float` and
`double` precision cell types. A tradeoff between speed, accuracy and memory usage.

## Multithreaded search and ranking
So far in this guide all search queries and ranking computations have been performed using 
single threaded execution.
To enable multithreaded execution, a setting needs to be added to `services.xml`.
Multithreaded search and ranking can improve query latency significantly and make better
use of multi-cpu core architectures. 

The following adds a `tuning` element to `services.xml` overriding 
[requestthreads:persearch](../reference/services-content.html#requestthreads-persearch).
The default number of threads used `persearch` is one. 

<pre data-test="file" data-path="app/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

    &lt;container id="default" version="1.0"&gt;
        &lt;search/&gt;
        &lt;document-api/&gt;
    &lt;/container&gt;

    &lt;content id="tracks" version="1.0"&gt;
        &lt;engine&gt;
            &lt;proton&gt;
                &lt;tuning&gt;
                    &lt;searchnode&gt;
                        &lt;requestthreads&gt;
                            &lt;persearch&gt;4&lt;/persearch&gt;
                        &lt;/requestthreads&gt;
                    &lt;/searchnode&gt;
                &lt;/tuning&gt;
            &lt;/proton&gt;
        &lt;/engine&gt;
        &lt;redundancy&gt;1&lt;/redundancy&gt;
        &lt;documents&gt;
            &lt;document type="track" mode="index"&gt;&lt;/document&gt;
        &lt;/documents&gt;
        &lt;nodes&gt;
            &lt;node distribution-key="0" hostalias="node1"&gt;&lt;/node&gt;
        &lt;/nodes&gt;
    &lt;/content&gt;
&lt;/services&gt;
</pre>

Deploy the application again :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

Changing the global threads per search requires a restart of the `searchnode` process:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker exec vespa /opt/vespa/bin/vespa-sentinel-cmd restart searchnode
</pre>
</div>

Wait for the `searchnode` to start:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ curl -s localhost:19110/state/v1/health
</pre>
</div>

<pre style="display:none" data-test="exec">
$ sleep 60
</pre>

Then repeat the tensor ranking query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">{% raw %}
$ vespa query \
    'yql=select title,artist, track_id from track where !weightedSet(track_id,@userLiked)' \
    'input.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
    'ranking=similar' \
    'hits=5' \
    'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}</pre>
</div>

Now, the content node(s) will parallelize the matching and ranking 
using multiple search threads and `querytime` drops to about 15 ms. 

The setting in `services.xml` sets the global *persearch* value, 
It is possible to tune down the number of threads used for a query with 
`rank-profile` overrides using [num-threads-per-search](../reference/schema-reference.html#num-threads-per-search).
Note that the per rank-profile setting can only be used to tune the number of threads
to a lower number than the global default. 

This adds a new `rank-profile` `similar-t2` using `num-threads-per-search: 2` instead
of the global 4 setting. It's also possible to set the number of threads in the query request
using [ranking.matching.numThreadsPerSearch](../reference/query-api-reference.html#ranking.matching).

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

    document track {

        field track_id type string {
            indexing: summary | attribute
            rank: filter
            match: word
        }

        field title type string {
            indexing: summary | index
            index: enable-bm25
        }

        field artist type string {
            indexing: summary | index
        }

        field tags type weightedset&lt;string&gt; {
            indexing: summary | attribute
            attribute: fast-search
        }

        field similar type tensor&lt;float&gt;(trackid{}) {
            indexing: summary | attribute
            attribute: fast-search 
        }
    }

    fieldset default {
        fields: title, artist
    }

    document-summary track_id {
        summary track_id type string { 
            source: track_id
        }
    }

    rank-profile personalized {
        first-phase {
            expression: rawScore(tags)
        }
    }

    rank-profile similar {
        inputs {
            query(user_liked) tensor&lt;float&gt;(trackid{})
        }
        first-phase {
            expression: sum(attribute(similar) * query(user_liked))
        }
    }

    rank-profile similar-t2 inherits similar {
        num-threads-per-search: 2
    }
}
</pre>

Deploy the application again :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

And adding a new rank-profile does not require any restart, repeat the query again,
now using the `similar-t2` profile:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">{% raw %}
$ vespa query \
    'yql=select title,artist, track_id from track where !weightedSet(track_id,@userLiked)' \
    'input.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
    'ranking=similar-t2' \
    'hits=5' \
    'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}</pre>
</div>

By using multiple rank profiles like above, developers can find the sweet-spot 
where latency does not improve much by using more threads. Using more threads per search 
limits query concurrency as more threads will be occupied
per query. Read more in [Vespa sizing guide:reduce latency with 
multithreaded search](sizing-search.html#reduce-latency-with-multi-threaded-per-search-execution).

## Advanced range search with hitLimit  

Vespa has an advanced query operator that allows selecting the 
documents with the k-largest or k-smallest values of a `fast-search` attribute field. 

To demonstrate this query operator, this guide introduces a `popularity`
field. Since the last.fm dataset does not have a real popularity metric,  
the number of tags per track is used as a *proxy* of the true track popularity.  

The following script runs through the dataset and 
count the number of tags and creates a Vespa
[partial update](../partial-updates.html) feed operation per track. 

<pre style="display:none" data-test="file" data-path="create-popularity-updates.py">
import os
import sys
import json

directory = sys.argv[1]
seen_tracks = set() 

def process_file(filename):
    global seen_tracks
    with open(filename) as fp:
        doc = json.load(fp)
        title = doc['title']
        artist = doc['artist']
        hash = title + artist
        if hash in seen_tracks:
            return
        else:
            seen_tracks.add(hash) 

        track_id = doc['track_id']
        tags = doc['tags']
        tags_dict = dict()
        for t in tags:
            k,v = t[0],int(t[1])
            tags_dict[k] = v
        n = len(tags_dict)

        vespa_doc = {
            "update": "id:music:track::%s" % track_id,
                "fields": {
                    "popularity": {
                        "assign": n
                    }
                }
        }
        print(json.dumps(vespa_doc))

sorted_files = []
for root, dirs, files in os.walk(directory):
    for filename in files:
        filename = os.path.join(root, filename)
        sorted_files.append(filename)
sorted_files.sort()
for filename in sorted_files:
    process_file(filename)
</pre>

<pre>{% highlight python%}
import os
import sys
import json

directory = sys.argv[1]
seen_tracks = set() 

def process_file(filename):
    global seen_tracks
    with open(filename) as fp:
        doc = json.load(fp)
        title = doc['title']
        artist = doc['artist']
        hash = title + artist
        if hash in seen_tracks:
            return
        else:
            seen_tracks.add(hash) 

        track_id = doc['track_id']
        tags = doc['tags']
        tags_dict = dict()
        for t in tags:
            k,v = t[0],int(t[1])
            tags_dict[k] = v
        n = len(tags_dict)

        vespa_doc = {
            "update": "id:music:track::%s" % track_id,
                "fields": {
                    "popularity": {
                        "assign": n
                    }
                }
        }
        print(json.dumps(vespa_doc))

sorted_files = []
for root, dirs, files in os.walk(directory):
    for filename in files:
        filename = os.path.join(root, filename)
        sorted_files.append(filename)
sorted_files.sort()
for filename in sorted_files:
    process_file(filename)
{% endhighlight %}</pre>

With this script, run through the dataset and create the [partial update](../partial-updates.html) feed :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ python3 create-popularity-updates.py lastfm_test > updates.jsonl
</pre>
</div>

Add the `popularity` field to the track schema, the field is defined with `fast-search`.
Also, a `popularity` `rank-profile` is added, this profile using one thread per search:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

    document track {

        field track_id type string {
            indexing: summary | attribute
            rank: filter
            match: word
        }

        field title type string {
            indexing: summary | index
            index: enable-bm25
        }

        field artist type string {
            indexing: summary | index
        }

        field tags type weightedset&lt;string&gt; {
            indexing: summary | attribute
            attribute: fast-search
        }

        field similar type tensor&lt;float&gt;(trackid{}) {
            indexing: summary | attribute
            attribute: fast-search 
        }

        field popularity type int {
            indexing: summary | attribute
            attribute: fast-search
        }
    }

    fieldset default {
        fields: title, artist
    }

    document-summary track_id {
        summary track_id type string { 
            source: track_id
        }
    }

    rank-profile personalized {
        first-phase {
            expression: rawScore(tags)
        }
    }

    rank-profile similar {
        inputs {
            query(user_liked) tensor&lt;float&gt;(trackid{})
        }
        first-phase {
            expression: sum(attribute(similar) * query(user_liked))
        }
    }

    rank-profile similar-t2 inherits similar {
        num-threads-per-search: 2
    }

    rank-profile popularity {
        num-threads-per-search: 1
        first-phase {
            expression: attribute(popularity)
        }
    }
}
</pre>

Deploy the application again :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

Adding a new field does not require a restart, apply the partial updates by:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./vespa-feed-client-cli/vespa-feed-client \
    --verbose --file updates.jsonl --endpoint http://localhost:8080
</pre>
</div>

With that feed job completed, it is possible to select the five tracks with the highest popularity by 
using the [range()](../reference/query-language-reference.html) query operator with
[hitLimit](../reference/query-language-reference.html#hitlimit):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="1352">
$ vespa query \
    'yql=select track_id, popularity from track where {hitLimit:5,descending:true}range(popularity,0,Infinity)' \
    'ranking=popularity'
</pre>
</div>

The search returned 1,352 documents, while we asked for just five. The reason
is that the `hitLimit` annotation for the `range` operator only specifies the lower bound.
Documents that are tied with the same `popularity` value within the 5 largest values are returned.

The `range()` query operator with `hitLimit` can be used to efficiently implement 
*top-k* selection for ranking a subset of the documents in the index.  
For example, use the `range` search with `hitLimit` to only run the 
track [recommendation tensor computation](#tensor-computations) 
over the most popular tracks:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="1349">{% raw %}
$ vespa query \
    'yql=select title,artist, track_id, popularity from track where {hitLimit:5,descending:true}range(popularity,0,Infinity) and !weightedSet(track_id, @userLiked)' \
    'input.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
    'ranking=similar' \
    'hits=5' \
    'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}</pre>
</div>

Notice that this query returns 1,349 documents while the `range` search from previous example returned 
1,352 documents. This is due to the `not` filter. 

The range search with `hitLimit` can be used for cases where one wants to select efficiently *top-k* of a 
single valued numeric `attribute` with `fast-search`. Some use cases which can be efficiently implemented
by using it:

- Run ranking computations over the most recent documents 
using a `long` to represent a timestamp (e.g., using Unix epoch).
- Compute personalization tensor expressions over pre-selected content, e.g. using popularity.
- Optimize [sorting](../reference/sorting.html) queries, instead of sorting a large result, 
find the smallest or largest values quickly by using range search with `hitLimit`.

Do note that any other query or filter terms in the query are applied after having found the 
top-k documents, so an aggressive filter removing many documents might end up recalling 0 documents. 

This behavior is illustrated with this query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 0'>
$ vespa query \
    'yql=select track_id, popularity from track where {hitLimit:5,descending:true}range(popularity,0,Infinity) and popularity=99'
</pre>
</div>

This query fails to retrieve any documents because the range search finds 
1,352 documents where popularity is 100, *and'ing* that 
top-k result with the popularity=99 filter constraint ends up with 0 results. 

Using range search query operator with `hitLimit` is practical for search use cases 
like auto-complete or [search suggestions](https://github.com/vespa-engine/sample-apps/tree/master/incremental-search/search-suggestions)
where one typically use [match: prefix](../reference/schema-reference.html#match) or
n-gram matching using [match: gram](../reference/schema-reference.html#match). Limiting the short 
few first character searches to include a `hitLimit` range on popularity 
can greatly improve the query performance and at the same time match against popular suggestions. 
As the user types more characters, the number of matches is greatly reduced, so ranking can focus on more factors
than just the single popularity attribute and increase the `hitLimit`. 

## Match phase limit - early termination 
An alternative to `range` search with `hitLimit` is using
early termination with [match-phase](../reference/schema-reference.html#match-phase)
which enables early-termination of search and `first-phase` ranking 
using a document field to determine the search evaluation order. 

Match-phase early-termination uses a field with attribute during matching and ranking to impact the
order the search and ranking is performed in. 
If a query is likely to generate more than `ranking.matchPhase.maxHits` per node, the search core
will early terminate the search and matching and evaluate the query in the order dictated
by the `ranking.matchPhase.attribute` attribute field. 

Match phase early termination requires a single valued numeric field with `attribute` and `fast-search`. 
See [Match phase query parameters](../reference/query-api-reference.html#ranking.matchPhase). 
Match-phase limit cannot terminate/early stop any potential `second-phase` ranking expression, 
only matching and `first-phase` ranking, hence the name: *match phase limit*. 

The following enables `matchPhase` early termination with `maxHits` target set to 100:   

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"match-phase": true'>
$ vespa query \
    'yql=select track_id, popularity from track where true' \
    'ranking=popularity' \
    'ranking.matchPhase.maxHits=100' \
    'ranking.matchPhase.attribute=popularity' \
    'hits=2'
</pre>
</div>

Which will produce the following result:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.007,
        "summaryfetchtime": 0.002,
        "searchtime": 0.01
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1476
        },
        "coverage": {
            "coverage": 0,
            "documents": 252,
            "degraded": {
                "match-phase": true,
                "timeout": false,
                "adaptive-timeout": false,
                "non-ideal-state": false
            },
            "full": false,
            "nodes": 1,
            "results": 1,
            "resultsFull": 0
        },
        "children": [
            {
                "id": "index:tracks/0/63f963f1f9372275e12d9e9c",
                "relevance": 100.0,
                "source": "tracks",
                "fields": {
                    "track_id": "TRGCNGP12903CFA2BA",
                    "popularity": 100
                }
            },
            {
                "id": "index:tracks/0/7a74f1cd064acef348a1a701",
                "relevance": 100.0,
                "source": "tracks",
                "fields": {
                    "track_id": "TRFVTTT128F930D148",
                    "popularity": 100
                }
            }
        ]
    }
}
{% endhighlight %}</pre>
In this case, totalCount became 1,476, a few more than the `range` search with `hitLimit`. Notice
also the presence of `coverage:degraded` - This informs the client that this result was not fully evaluated 
over all matched documents. Read more about [graceful result degradation](../graceful-degradation.html). 
Note that the example uses the `popularity` rank-profile which was configured with one 
thread per search, for low settings of `maxHits`, this is the recommended setting. 

<pre>
rank-profile popularity {
    num-threads-per-search: 1
    first-phase {
        expression: attribute(popularity)
    }
}
</pre>

The core difference from capped range search is that `match-phase` is safe as filters works inline
with the search, and are not applied after finding the top-k documents. 

This query does not trigger match-phase early termination because there 
are few hits matching the query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"full": true'>
$ vespa query \
    'yql=select track_id, popularity from track where popularity=99' \
    'ranking=popularity' \
    'ranking.matchPhase.maxHits=100' \
    'ranking.matchPhase.attribute=popularity' \
    'hits=2'
</pre>
</div>

Generally, prefer `match-phase` early termination over `range` search with `hitLimit`.
Match phase limiting can also be used in combination with text search queries:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"match-phase": true'>
$ vespa query \
    'yql=select title, artist, popularity from track where userQuery()' \
    'query=love songs' \
    'type=any' \
    'ranking=popularity' \
    'ranking.matchPhase.maxHits=100' \
    'ranking.matchPhase.attribute=popularity' \
    'hits=2'
</pre>
</div>

Since this query uses `type=any` the above query retrieves a lot more documents than
the target `matchPhase.maxHits` so early termination is triggered, which will then cause the search core to match 
and rank tracks with the highest popularity. 

Early termination using match-phase limits is a powerful feature 
that can keep latency and cost in check for many large scale serving use cases 
where a document quality signal is available. 
Match phase termination also supports specifying a result diversity constraint.
See [Result diversification blog post](https://blog.vespa.ai/result-diversification-with-vespa/). 
Note that result diversity is normally obtained with Vespa [result grouping](../grouping.html), 
the match-phase diversity is used to ensure that diverse hits are also collected **if** 
early termination kicks in.  

## Advanced query tracing 

This section introduces query tracing. Tracing helps understand where time (and cost) is spent, and how
to best optimize the query or schema settings. Query tracing can be enabled using the following parameters:

- [trace.level](../reference/query-api-reference.html#trace.level)
- [trace.explainLevel](../reference/query-api-reference.html#trace.explainLevel)
- [trace.timestamps](../reference/query-api-reference.html#trace.timestamps)

A simple example query with tracing enabled:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="track_id">
$ vespa query 'yql=select track_id from track where tags contains "rock"' \
  'trace.level=3' 'trace.timestamps=true' 'trace.explainLevel=1' 'hits=1'
</pre>
</div>

The first part of the trace traces the query through the stateless container search 
chain. For each searcher invoked in the chain a timestamp relative to the start of the query request 
is emitted:
<pre>{% highlight json%}
{
    "trace": {
        "children": [
            {
                "message": "Using query profile 'default' of type 'root'"
            },
            {
                "message": "Invoking chain 'vespa' [com.yahoo.search.querytransform.WeakAndReplacementSearcher@vespa -> com.yahoo.prelude.statistics.StatisticsSearcher@native -> ... -> federation@native]"
            },
            {
                "children": [
                {
                    "timestamp": 0,
                    "message": "Invoke searcher 'com.yahoo.search.querytransform.WeakAndReplacementSearcher in vespa'"
                }]
            }
        ]
    }
}
{% endhighlight %}</pre>

The trace runs all the way to the query is dispatched to the content node(s) and the merged response
is returned up to the client. 

<pre>{% highlight json%}
{
    "timestamp": 2,
    "message": "sc0.num0 search to dispatch: query=[tags:rock] timeout=9993ms offset=0 hits=1 restrict=[track]"
}
{% endhighlight %}</pre>

In this case, with tracing it has taken 2ms of processing in the stateless container, 
before the query is about to be put on the wire on its way 
to the content nodes. 

The first protocol phase is the next trace message. 
In this case the reply, is ready read from the wire at timestamp 6, 
so approximately 4 ms was spent in the first protocol matching phase, 
including network serialization and deserialization. 
<pre>{% highlight json%}
{
    "timestamp": 6,
    "message": [
        {
            "start_time": "2022-03-27 15:03:20.769 UTC",
            "traces": [

            ],
            "distribution-key": 0,
            "duration_ms": 1.9814
        }
    ]
}
{% endhighlight %}</pre>
Inside this message is the content node traces of the query, `timestamp_ms` is relative to the start of the query
on the content node. In this case, the content node uses 1.98 ms to evaluate the first protocol phase 
of the query (`duration_ms`). 

More explanation of the content node `traces` is coming soon. It includes information like
- How much time was spent traversing the dictionary and setting up the query.
- How much time was spent on matching and first-phase ranking.
- How much time was spent on second-phase ranking (if enabled).

These traces can help guide both feature tuning decisions and [scaling and sizing](sizing-search.html).

Later in the trace one can also see the second query protocol phase which is the summary fill:
<pre>{% highlight json%}
{
    "timestamp": 7,
    "message": "sc0.num0 fill to dispatch: query=[tags:rock] timeout=9997ms offset=0 hits=1 restrict=[track] summary=[null]"
}
{% endhighlight %}</pre>

And finally an overall breakdown of the two phases:

<pre>{% highlight json%}
{
    "timestamp": 9,
    "message": "Query time query 'tags:rock': 7 ms"
}
{
    "timestamp": 9,
    "message": "Summary fetch time query 'tags:rock': 2 ms"
}
{% endhighlight %}</pre>

Also try the [Trace Visualizer](https://github.com/vespa-engine/vespa/tree/master/client/js/app#trace-visualizer)
for a flame-graph of the query trace.


## Tear down the container
This concludes this tutorial. The following removes the container and the data:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="after">
$ docker rm -f vespa
</pre>
</div>

<script src="/js/process_pre.js"></script>
