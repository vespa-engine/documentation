---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa query performance - a practical guide"
---

 This is a practical Vespa query performance guide. It uses the 
 [Last.fm](http://millionsongdataset.com/lastfm/) tracks dataset to illustrate Vespa query performance. 
 Latency numbers mentioned in the guide are obtained from running this guide on a Macbook Pro x86.  

## Prerequisites

* [Docker](https://www.docker.com/) Desktop installed and running. 10GB available memory for Docker is recommended.
  Refer to [Docker memory](https://docs.vespa.ai/en/operations/docker-containers.html#memory)
  for details and troubleshooting
* Operating system: Linux, macOS or Windows 10 Pro (Docker requirement)
* Architecture: x86_64
* Minimum **6 GB** memory dedicated to Docker (the default is 2 GB on Macs)
* [Homebrew](https://brew.sh/) to install [Vespa CLI](https://docs.vespa.ai/en/vespa-cli.html), or download
  a vespa cli release from [Github releases](https://github.com/vespa-engine/vespa/releases).

## Installing vespa-cli 

This tutorial uses [Vespa-CLI](https://docs.vespa.ai/en/vespa-cli.html), 
Vespa CLI is the official command-line client for Vespa.ai. 
It is a single binary without any runtime dependencies and is available for Linux, macOS and Windows.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ brew install vespa-cli 
</pre>
</div>

## Dataset

This guide uses the [Last.fm](http://millionsongdataset.com/lastfm/) tracks dataset, we use the the
TEST SET split with about 100k documents. Note that the dataset is released under the following terms:

>Research only, strictly non-commercial. For details, or if you are unsure, please contact Last.fm. 
>Also, Last.fm has the right to advertise and refer to any work derived from the dataset.

To download the dataset directly (About 120MB zip file):
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

We use this small python script to traverse the track files and create a JSONL 
file with Vespa feed operations. We will introduce the schema to be used with this 
feed in the next section. The dataset contains some duplicates which we remove based
on the combination of artist name and title. 

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
        "value": v }
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

<pre>
{% highlight python%}
import os
import sys
import json
import unicodedata

directory = sys.argv[1]

def remove_control_characters(s):
  return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def process_file(filename):
  with open(filename) as fp:
    doc = json.load(fp)
    title = doc['title']
    artist = doc['artist']
    track_id = doc['track_id']
    tags = doc['tags']
    tags_dict = dict()
    for t in tags:
      k,v = t[0],int(t[1])
      if v > 0:
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
        "value": v }
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
{% endhighlight %}
</pre>

With this small script we can process the lastfm test dataset and convert it a
format which Vespa can understand. See [Vespa document json format](../reference/document-json-format.html).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ python3 create-vespa-feed.py lastfm_test > feed.jsonl
</pre>
</div>

## Create a Vespa Application Package

A [Vespa application package](../cloudconfig/application-packages.html) is the set of configuration files and Java plugins
that together define the behavior of a Vespa system:
what functionality to use, the available document types, how ranking will be done
and how data will be processed during feeding and indexing.
Let's define the minimum set of required files to create our basic search application,
which are `track.sd`, `services.xml`.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir app
</pre>
</div>

### Schema

A [schema](../schemas.html) is a configuration of a document type and what we should compute over it.
For this application we define a document type called `track`.
Write the following to `app/schemas/track.sd`:

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

Already here we introduce an optimization for the `track_id` field:

- We do not want to compute any rank-features for the track_id so so we use `rank:filter` 
- We do not want to tokenize the field, we want to match it exact using `match: word`


### Services Specification

The [services.xml](../reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.
Write the following to `app/services.xml`:

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

In addition we plan to use our `similar` tensor document field for ranking computations so we also need to define 
a query tensor type. Don't worry too much about this now, these concepts will be explained later
in this guide. 

<pre data-test="file" data-path="app/search/query-profiles/types/root.xml">
&lt;query-profile-type id=&quot;root&quot; inherits=&quot;native&quot;&gt;
    &lt;field name=&quot;ranking.features.query(user_liked)&quot; type=&quot;tensor&amp;lt;float&amp;gt;(trackid{})&quot; /&gt;
&lt;/query-profile-type&gt;
</pre>

<pre data-test="file" data-path="app/search/query-profiles/default.xml">
&lt;query-profile id=&quot;default&quot; type=&quot;root&quot;&gt;
    &lt;field name=&quot;presentation.timing&quot;&gt;true&lt;/field&gt;
    &lt;field name=&quot;renderer.json.jsonWsets&quot;&gt;true&lt;/field&gt;
&lt;/query-profile&gt;
</pre>

## Deploy the application package

Once we have finished writing our application package, we can deploy it to a running Vespa instance.
See also the [vespa quick start guide](../vespa-quick-start.html).

Start the Vespa container image:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker run -m 6G --detach --name vespa --hostname vespa-container \
  --publish 8080:8080 --publish 19071:19071 --publish 19110:19110 \
  vespaengine/vespa
</pre>
</div>

Starting the container can take a short while. Before continuing, make sure
that the configuration service is running by using `vespa status deploy`. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa status deploy --wait 300 
</pre>
</div>

Now, once ready, we can deploy the Vespa application using the Vespa CLI:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

## Feed the data

The data fed to Vespa must match the document type in the schema. 
We use the [vespa feed client](../vespa-feed-client.html):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o vespa-feed-client-cli.zip \
    https://search.maven.org/remotecontent?filepath=com/yahoo/vespa/vespa-feed-client-cli/7.527.20/vespa-feed-client-cli-7.527.20-zip.zip
$ unzip vespa-feed-client-cli.zip
$ ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --file feed.jsonl --endpoint http://localhost:8080
</pre>
</div>

Now, we have our dataset indexed and we can start querying our data. 

## Basic text search query performance
The following sections uses the Vespa [query api](../reference/query-api-reference.html) and 
formulate queries using Vespa [query language](../query-language.html). We use the
[vespa-cli](../vespa-cli.html) command which supports running queries. The CLI
uses the Vespa http search api. Use `-v` to see the actual http request sent:

<pre>
$ vespa query -v 'yql=select ..'
</pre>

In the first query example we simply match everything using `where true` and we 
use the [hits](..(reference/query-api-reference.html#hits) to specify how many documents we want to be returned 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"documents": 95666'>
$ vespa query 'yql=select artist, title, track_id, tags from track where true' 'hits=1'
</pre>
</div>

The [result json output](../reference/default-result-format.html) for this query will 
look something like this:

<pre>
{% highlight json%}
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
{% endhighlight %}
</pre>

Observations: 

- The query searched one node (`coverage.nodes`) and the coverage (`coverage.coverage`) was 100%, 
see [graceful-degradation](../graceful-degradation.html) for more information about 
coverage and Vespa timeout behaviour. Vespa's default timeout is 0.5 seconds.   
- The query matched a total of 95666 documents (`totalCount`) out of 95666 documents searched (`coverage.documents`).

The response `timing` has 3 fields:

- `querytime` - This is the first matching query protocol where Vespa searches all content nodes 
and where each content node matches and ranks the documents and the container merges the results from each node
involved in the query into a global ordering. See [Life of a query in Vespa](sizing-search.html#life-of-a-query-in-vespa).

- `summaryfetchtime` - This is the second query protocol which fills summary data for the global top-k parameter 
after the globalb top ranking documents have been found from the previous protocol phase.
- `searchtime` Is roughly the sum of the above and is close to what a benchmarking client will observe (except network latency).

All 3 metrics are reported in seconds.

Now, we can try to search for *total eclipse of the heart*

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
  'query=total eclipse of the heart' 'hits=1'
</pre>
</div>

This query combines YQL [userQuery()](../reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](../reference/simple-query-language-reference.html), the 
default query type is using `all` requiring that all the terms match the document. 

The above example searches for *total AND eclipse AND of AND the AND heart* in the `default` fieldset, 
which in our schema includes the track `title` and `artist` fields. The result output for the 
above query will look something like this:

<pre>
{% highlight json%}
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
{% endhighlight %}
</pre>

This query only matched one document because the query terms were ANDed. 
We can change matching  to use `type=any` instead of the default `type=all`. See 
[supported query types](../reference/query-api-reference.html#model.type).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
  'query=total eclipse of the heart' 'hits=1' 'type=any'
</pre>
</div>

Now, our query matches 24,053 documents and is slower than than the previous query. 
If we compare the `querytime` of these two query examples, the one which matches the most documents have highest `querytime`. 
In worst case, the search query matches all documents.

Query matching performance is greatly impacted by the number of documents that matches the query specification. 
Type `any` queries requires more compute resources than type `all`.  There is an optimization of `any` queries, using
the `weakAnd` query operator which implements the WAND algorithm. 
See the [using wand with Vespa](../using-wand-with-vespa.html) guide for more details. 

Run the same query, but instead of `type=any` use `type=weakAnd`, 
see [supported query types](../reference/query-api-reference.html#model.type)

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
  'query=total eclipse of the heart' 'hits=1' 'type=weakAnd'
</pre>
</div>

Compared to the type `any` query which fully ranked 24,053 documents, we now only rank 3,679 documents.   
also notice that the much faster search returns the same document at the first position. 


## Hits and summaries 
In the previous examples we only asked for one hit with `hits=1` parameter, also if you have been paying attention you would
see that the `summaryfetchtime` have been pretty constant over the previous text search examples. Let us see 
what happens when we ask for 200 hits (Note that we pipe the large JSON result payload into `head`):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
  'query=total eclipse of the heart' 'hits=200' 'type=weakAnd' |head -40 
</pre>
</div>

Now, we can notice that the `summaryfetchtime` increases significantly from the previous query examples,
while `querytime` is relatively unchanged. Repeating the query a second time will reduce the `summaryfetchtime`
due to the summary cache, see [caches in Vespa](../performance/caches-in-vespa.html) for details.

There are largely four factors which determines the `summaryfetchtime`:

- The number of hits requested and number of content nodes that produced the query result. With many content nodes
in the group the query was dispatched to, we expect that top-ranking hits would be distributed across the nodes so that each node
does less work.
- The network package size of each hit (larger fields returned means more resources spent and higher summary fetch latency).
- The summary used and which fields goes into the summary. For example, a
 [document-summary](../document-summaries.html) which only contain fields that are defined as `attribute` will
 be fetched out of memory, while the `default` summary, or others containing at least one none-attribute
 field will potentially access data from disk storage. Read more about [Vespa attributes](../attributes.html).
- [summary-features](../reference/schema-reference.html#summary-features) used to return computed
 [rank features](../reference/rank-features.html) from the content nodes.

Let us create an explicit [document-summary](../document-summaries.html) which
only contain the `track_id` field. Since `track_id` is defined in the schema as `attribute`, summary
fetches using this document summary will be requesting data from in-memory. Plus the network 
footprint per hit becomes smaller.

<pre>
document-summary track_id {
    summary track_id type string { 
      source: track_id
    }
}
</pre>

The new schema:

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

And re-execute the query, now using this `document-summary` instead:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="track_id">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
  'query=total eclipse of the heart' 'hits=200' 'type=weakAnd' \
  'summary=track_id' |head -40 
</pre>
</div>

In this particular case the `summaryfetchtime` difference is not that large, but for larger number of hits and 
larger documents the difference is significant. 

A note on select field scoping with YQL. For example `select title, track_id from ..`. When using the default summary, all
fields are regardless of field scoping delivered from the content nodes to the search container in the summary fill phase. 
The search container removes the set of fields not selected and renders the result. Hence select
scoping only reduces the amount of data transfered back to the client, and does not impact the performance of
the internal communication and potential summary cache miss. For optimial performance with large hit request, use dedicated
document summaries. Note also that Vespa per default limits the max hits to 400 per default, 
this can be overriden in the [default queryProfile](../reference/query-api-reference.html#queryProfile).

## Searching attribute fields 

In the previous sections we looked at text searching in a `fieldset` containing fields with
`indexing:index`. See [indexing reference](../reference/schema-reference.html#indexing). 
Fields of [type string](../reference/schema-reference.html#field-types) are 
treated differently depending on having `index` or `attribute`:

- `index` integrates with [linguistic](../linguistics.html) processing and is matched using 
[match:text](../reference/schema-reference.html#match). 

- `attribute` does not integarte with lingustic processing and is matched using 
[match:word](../reference/schema-reference.html#match). 

With `index` Vespa builds inverted index data structures which consists of
- A dictionary of the unique text tokens (after linguistic processing)
- Posting lists for each unique text token in the collection 

With `attribute` Vespa per default does not build any inverted index like data structures for 
potential faster query evaluation. See [Wikipedia:Inverted Index](https://en.wikipedia.org/wiki/Inverted_index) 
and [Vespa internals](../proton.html#index). The reason for this is that Vespa `attribute` fields can be used
for many different things: ranking, grouping, sorting, and potentially searching. 

Now let us focus on the `tags` field which we defined with `attribute`, matching
in this fields will be performed using `match:word`. 

<pre>
 field tags type weightedset&lt;string&gt; {
      indexing: summary | attribute
 }
 </pre>

In this case, there is no index structure, searching the `attribute` 
field is performed as a linear scan, let us do a search for a popular tag *rock*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"rock":'>
$ vespa query 'yql=select track_id, tags from track where tags contains "rock"' \
  'hits=1' 
</pre>
</div>

The query matches 8,160 documents, notice that for `match: word`, matching can also include
white space, or generally puncation characters which are removed and not searchable
when using `match:text` with string fields that have `index`. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"classic rock":'>
$ vespa query 'yql=select track_id, tags from track where tags contains "classic rock"' \
  'hits=1' 
</pre>
</div>

Another query searching for *rock* or *pop*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"rock":'>
$ vespa query 'yql=select track_id, tags from track where tags contains "rock" or tags contains "pop"' \
  'hits=1' 
</pre>
</div>

In all these examples searching the `tags` field, the matching is performed by a linear scan through all our documents. 

We can combine the tag search with query terms searching fields that do have index structures:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"rock"'>
$ vespa query 'yql=select track_id, tags from track where tags contains "rock" and userQuery()' \
  'hits=1' 'query=total eclipse of the heart'
</pre>
</div>

In this case - the query terms searching the default fieldset will restrict the number of 
documents that needs to be scanned for the tags constraint. This query is automatically optimized
by the Vespa query planner. 

### Searching attribute fields using fast-search 
As we have seen in the previous section, fields with `attribute` does per default does not
build any [inverted index](https://en.wikipedia.org/wiki/Inverted_index) data structures. We can modify
the tags field and add `attribute:fast-search` which will add inverted index structures for the attribute as well:

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

The above will print 

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

To enable `fast-search` Vespa content node(s) needs to be restarted to re-build the index. 
This example uses [vespa-sentinel-cmd command tool](../reference/vespa-cmdline-tools.html#vespa-sentinel-cmd):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker exec vespa bash -c "/opt/vespa/bin/vespa-sentinel-cmd restart searchnode"
</pre>
</div>

Wait for the searchnode to start up using the [healt state api](../reference/metrics.html):

<pre>
curl -s http://localhost:19110/state/v1/health
</pre>

We want the page to return: 
<pre>
{% highlight json%}
{
  "status": {
    "code": "up"
  }
}
{% endhighlight %}
</pre>

<pre style="display:none" data-test="exec">
$ sleep 60
</pre>

We can now try our multi-tag search again:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"rock":'>
$ vespa query 'yql=select track_id, tags from track where tags contains "rock" or tags contains "pop"' \
  'hits=1' 
</pre>
</div>

Now the `querytime` will be a few milliseconds since Vespa has built index structures to support
fast-search in the attribute. The downside is increased memory usage and reduced indexing
throughput. See also [when to use fast-search for attributes](feature-tuning.html#when-to-use-fast-search-for-attribute-fields).

Finally, for those interested in using `match:text` for searching multi-valued field types like `weightedset`, see
[searching multi-value fields](../searching-multi-valued-fields.html).

## Multi-valued query operators

In this section we look at [multi-value query operators](../multivalue-query-operators.html) 
and their query performance characteristics. 
Many real-world use cases needs search using structured queries with many values. 

Let us assume that we have a process which have built a user profile where we have identified tags which
the user has shown previous interest for. For example *hard rock*, *rock* and *metal*. 
How can we retrieve and rank results using that information? One way is to search and rank using
the dotproduct between the sparse user profile representation and the track tags representation.

We can start with the [dotProduct()](../reference/query-language-reference.html#dotproduct) query operator.
To gain control of [ranking](../ranking.html) we need to add a `rank-profile` to our schema:

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

Deploy the application again :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

Now, we query our data using the `dotProduct` 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Vastarannan valssi">
$ vespa query \
 'yql=select track_id, title, artist, tags from track where dotProduct(tags,@userProfile)' \
 'userProfile={"hard rock":1, "rock":1,"metal":1, "finnish metal":1}' \
 'hits=1' \
 'ranking=personalized'
</pre>
</div>
<pre>
{% highlight json%}
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
{% endhighlight %}
</pre>

Notice that the query above, it brute force rank tracks where tags would match any of the multi-valued inputs so 
the `totalCount` 10,323 tracks. Including *pop* in the userProfile list increases the number of hits to 13,638. 
For a large user profile with many tags, we would easily retrieve and rank the entire document collection. 
Also notice the `relevance` score which is 400 as the document 

This brings us to the [wand query operator](../reference/query-language-reference.html#wand). 
With `wand` we can specify the target number of hits that we want to retrieve, so instead of brute forcing ranking all tracks
which matched at least one of the user profile tags we want just to retrieve the k top-ranking documents:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Vastarannan valssi">
$ vespa query \
 'yql=select track_id, title, artist, tags from track where {targetHits:10}wand(tags,@userProfile)' \
 'userProfile={"hard rock":1, "rock":1,"metal":1, "finnish metal":1}' \
 'hits=1' \
 'ranking=personalized'
</pre>
</div>
The `wand` query retrieves the exact same hit at rank 1.
For larger document collections, the *wand* query operator can significantly improve query performance. We can also combine wand 
with for example the rank() query operator. *wand* tries to do matching and ranking interleaved and skipping documents
which cannot compete into the best k. See the [using wand with Vespa](../using-wand-with-vespa.html) guide for more details. 

Finally, these query operators all works on both single valued fields, and array fields, but optimal performance
is obtained when using the weightedset field type. Weightedsets can only use integer to represent the weight. In the 
next section we look at Tensors which supports floating point numbers. 


## Tensor Computations
In the previous sections we looked at matching and where matching also produced rank features which we could
use to influence the order of the hits returned. In this section we look at [tensor computations](../tensor-examples.html) 
using [tensor expressions](../tensor-user-guide.html). Tensor computations can be used to calculate dense dot products, sparse
dotproducts, matrix multiplication, neural networks and more. 

For each of the track documents we have a field named `similar` which is of type `tensor`
with one named *mapped* dimension. *Mapped* tensors can be used to represent sparse feature representations. 

<pre>
field similar type tensor&lt;float&gt;(trackid{}) {
      indexing: summary | attribute
}
</pre>

Let us look at one of the tracks in our collection:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bryan Adams">
$ vespa document get id:music:track::TRQIQMT128E0791D9C
</pre>
</div>

We leave out some of the tags and the tensor cells from the output, but below is a summary:

<pre>
{% highlight json%}
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
{% endhighlight %}
</pre>

In the lastfm collection, each track lists similar tracks with a similarity score using float resolution, according to this
similarity algorithm the most similar track to our sample document is `TRWJIPT128E0791D99` with a similarity score of 1.0. 
Let us search for that document using the query api this time:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bryan Adams">
$ vespa query 'yql=select title, artist from track where track_id contains "TRWJIPT128E0791D99"' 'hits=1'  
</pre>
</div>

Which returns:

<pre>
{% highlight json%}
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
{% endhighlight %}
</pre>

Now, if a user have have listened to these three tracks in a session:

- `TRQIQMT128E0791D9C` Summer Of '69 by Bryan Adams
- `TRWJIPT128E0791D99` Run To You by Bryan Adams
- `TRGVORX128F4291DF1` Broken Wings by Mr. Mister

What should our algorithm suggest next? It is straight forward to suggest tracks given a single track, but the
unique sequence of tracks played or *liked* in real time has a very high cardinality which makes it next to impossible to
generate offline. We can use tensor ranking expression for this use case, we do so by passing
the song tracks recently played with the query request, and with a rank profile which express the following 
computation: 

<pre>
rank-profile similar {
    first-phase {
      expression: sum(attribute(similar) * query(user_liked))
    }
}
</pre>

The `similar` rank profile with defines a sparse tensor dotproduct between the `query(user_liked)` query tensor and the 
the `attribute(similar)` document tensor. See [tensor user guide](../tensor-user-guide.html) for more on tensors. We could
also use [phased ranking](../phased-ranking.html). 

<pre>
rank-profile similar {
    first-phase {
      expression: sum(attribute(similar) * query(user_liked))
    }
    second-phase {
      expression: #Even more compute, but only for the top-scoring docs from first-phase
    }
}
</pre>

Our complete track schema becomes:

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

Here we use a query tensor with our three sample tracks using the short query tensor format:

- `TRQIQMT128E0791D9C` Summer Of '69 by Bryan Adams
- `TRWJIPT128E0791D99` Run To You by Bryan Adams
- `TRGVORX128F4291DF1` Broken Wings by Mr. Mister

<pre>
{% raw %}
ranking.features.query(user_liked)={{trackid:TRUAXHV128F42694E8 }:1.0,{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}
{% endraw %}
</pre>

In the first query example we simply run our tensor computation over all documents using `where true`:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
{% raw %}
$ vespa query 'yql=select title, artist, track_id from track where true' \
 'ranking.features.query(user_liked)={{trackid:TRUAXHV128F42694E8}:1.0,{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
 'ranking=similar' \
 'hits=5'
 {% endraw %}
</pre>
</div>

However, as we can see,  we retrieved some of the liked docments as well. Let us eliminate these
from the result using the `not` query operator (`!`) in YQL:

<pre>
where !weightedSet(track_id, @userLiked) 
</pre>

The [weightedSet query operator](../reference/query-language-reference.html#weightedset) is a handy query operator
when we don't need any rank feature calculated, it can also be used for large scale filters (x in large list of options).
 See [feature-tuning set filtering](feature-tuning.html#multi-lookup-set-filtering)

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
{% raw %}
$ vespa query 'yql=select title, artist, track_id from track where !weightedSet(track_id, @userLiked)' \
'ranking.features.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
'ranking=similar' \
'hits=5' \
'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}
</pre>
</div>

Note that the tensor query input format is slightly different from the variable subsitution supported for wand/weightedSet/dotProduct
multi-valued query operators. The above query produces the following result:

<pre>
{% highlight json%}
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
{% endhighlight %}
</pre>

Now we can notice that with the `not` filter, we retrieved 9,5663 documents
as our 3 tracks where filtered out as compared with `documents`. 

We can also add tag filters, here we filter the recommended by `tags:popular`, by filtering we reduce the complexity of the
query as few documents gets ranked by the tensor ranking expression:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Ronan Keating">
{% raw %}
$ vespa query 'yql=select title,artist, track_id from track where tags contains "popular" and !weightedSet(track_id,@userLiked)' \
'ranking.features.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
'ranking=similar' \
'hits=5' \
'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}
</pre>
</div>

With fewer matches to score using the tensor expression the latency decreases. In this query case,
latency is strictly linear with number of matches. 

The `querytime` of the unconstrained search was around 120 ms which is on the high side for real time serving. 
We can optimize this as well by adding `fast-search` to the mapped field tensor. 
`fast-search` is supported for `tensor` fields using mapped dimensions, or mixed tensors using both mapped and dense dimensions.

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

And again, since we added `fast-search` we need to restart the searchnode process:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker exec vespa bash -c "/opt/vespa/bin/vespa-sentinel-cmd restart searchnode"
</pre>
</div>

Wait for the searchnode to start up 
<pre>
curl -s localhost:19110/state/v1/health
</pre>

<pre style="display:none" data-test="exec">
$ sleep 60
</pre>

Let us re-run our query example :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
{% raw %}
$ vespa query 'yql=select title,artist, track_id from track where !weightedSet(track_id,@userLiked)' \
'ranking.features.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
'ranking=similar' \
'hits=5' \
'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}
</pre>
</div>

The `querytime` dropped down to 40 ms instead of 120 ms without the `fast-search` option. 
See also [performance considerations](../tensor-user-guide.html#performance-considerations)
when using tensor expressions and especially the tensor cell precision used. Vespa supports both `int8`, `bfloat16`, `float` and
`double` precision cell types.  

## Multi-threaded search and ranking 
So far in this guide all our searches and computations have been performed using single threaded matching and ranking. 
To enable multi-threaded execution we need to change our `services.xml`. 
Multi-threaded search and ranking can improve latency significantly and make
use of multi-cpu core architectures better. Search and ranking has evolved since 1998 and using multi-threaded execution
we can significantly reduce serving latency. In many deployment systems, low latency is critical.  

To enable multi-threaded matching and ranking we need to add a `tuning` element to `services.xml` where we override 
[requestthreads:persearch](../reference/services-content.html#requestthreads-persearch). The default is 1. 

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

Changing threads per search requires a restart of the searchnode process:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker exec vespa bash -c "/opt/vespa/bin/vespa-sentinel-cmd restart searchnode"
</pre>
</div>

Wait for the searchnode to start up 
<pre>
curl -s localhost:19110/state/v1/health
</pre>

<pre style="display:none" data-test="exec">
$ sleep 60
</pre>

Then we can repeat our tensor ranking query again:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
{% raw %}
$ vespa query 'yql=select title,artist, track_id from track where !weightedSet(track_id,@userLiked)' \
'ranking.features.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
'ranking=similar' \
'hits=5' \
'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}
</pre>
</div>

Now, the content node will parallelize the matching and ranking 
using multiple search threads and `querytime` drops to about 15 ms. 

The setting in services.xml sets to the global value, we can override number of threads used with 
`rank-profile` overrides using [num-threads-per-search](../reference/schema-reference.html#num-threads-per-search)

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

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
{% raw %}
$ vespa query 'yql=select title,artist, track_id from track where !weightedSet(track_id,@userLiked)' \
'ranking.features.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
'ranking=similar' \
'hits=5' \
'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}
</pre>
</div>

By using multiple ranking profiles like above we can find the sweet spot where latency does not get any better.
Using more threads then nessacary limits throughput. See 
[Vespa sizing guide:reduce latecy with 
multi-threaded search](sizing-search.html#reduce-latency-with-multi-threaded-per-search-execution).

## Advanced range search with hitLimit  

Vespa has a advanced query operator which allows you to select the 
k-largest or K-smallest values of a `fast-search` attribute. 
This allows users so skip pre-defined index sorting, 
one can chose at query runtime which field is used for selecting top-k.

Let us first define a new field, which we call `popularity`, 
since we don't have real popularity value from the dataset, we create
a proxy of the popularity, the number of tags per track. 
The following script runs through the dataset and 
count the number of tags and creates a Vespa
[partial update](../partial-updates.html) operation per track. 

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

<pre>
{% highlight python%}
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
{% endhighlight %}
</pre>

WIth this script, run through the dataset and create the [partial update](../partial-updates.html) feed :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ python3 create-popularity-updates.py lastfm_test > updates.jsonl
</pre>
</div>

Add the `popularity` field to the track schema, notice we defined this field with 
`fast-search`. We also add a popularity rank profile which uses 1 thread per search. 

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
Adding a new field, does not require any restart but we do need to populate the popularity field:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --file updates.jsonl --endpoint http://localhost:8080
</pre>
</div>

With that feed job completed we can select 5 tracks with the highest popularity by 
using the [range()](../reference/query-language-reference.html) query operator:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="1352">
$ vespa query 'yql=select track_id, popularity from track where {hitLimit:5,descending:true}range(popularity,0,Infinity)' \
  'ranking=popularity'
</pre>
</div>

The search returned 1352 documents, that is because the popularity is capped at 100 
and several tracks share the same unique value.
The `hitLimit` annotation for the `range` operator only specifies the lower bound, the search might return 
more, like in this case. Let us double check how many documents have the popularity equal to 100:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="1352">
$ vespa query 'yql=select track_id, popularity from track where popularity=100' \
  'ranking=popularity'
</pre>
</div>
Which also returns 1352 documents as expected. We can use the `range` query operator in many ways, 
for example, returning to our recommendation search using tensors, 
we can use the range search with `hitLimit` to only run the tensor computation over the generally most popular tracks:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="1349">
{% raw %}
$ vespa query 'yql=select title,artist, track_id, popularity from track where {hitLimit:5,descending:true}range(popularity,0,Infinity) and !weightedSet(track_id, @userLiked)' \
'ranking.features.query(user_liked)={{trackid:TRQIQMT128E0791D9C}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRGVORX128F4291DF1}:1.0}' \
'ranking=similar' \
'hits=5' \
'userLiked={TRQIQMT128E0791D9C:1,TRWJIPT128E0791D99:1,TRGVORX128F4291DF1:1}'
{% endraw %}
</pre>
</div>

Notice that we get a totalCount of 1349, the range search from previous example returned 1352 documents, 
since we added the not filter on previous listened tracks, 3 tracks were removed.  

The range search with `hitLimit` can be used for cases where we want to select efficiently *top-k* of a 
single valued numeric `attribute` with `fast-search`:

- We can use it to for example to only run computations over the 1,000 most recent documents 
using a long to represent a timestamp
- We can use it as above to compute and rank the most popular documents.
- Optimize sorting queries, instead of sorting a large result, 
find the smallest or largest values quickly with `hitLimit`.

Do note that any other query terms in the query are applied after having found the top-k documents, 
hence, an aggresive filter removing many documents might end up recalling 0 documents. 

We can illustrate this with the following query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 0'>
$ vespa query 'yql=select track_id, popularity from track where {hitLimit:5,descending:true}range(popularity,0,Infinity) and popularity=99'
</pre>
</div>

This query fails to retrieve any documents becase the range search finds 1352 documents where popularity is 100, *and'ing* that 
result with the popularity=99 filter constraint leaves us with 0 results. 

### Match phase 
A more relaxed alternative to range search with `hitLimit` is using
[match-phase](../reference/schema-reference.html#match-phase) which will use a document side signal during matching and ranking,
if the result set is estimated to become too large, documents with the highest or lowest value (depending on config) is
evaluated first. 

### Advanced query tracing 

In this section we introduce query tracing, which can allow developers to understand the latency of
any given Vespa query request. 


<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="track_id">
$ vespa query 'yql=select track_id from track where tags contains "rock"' \
  'tracelevel=4' 'trace.timestamps=true' 'hits=1'
</pre>
</div>

Explanation of the trace is coming soon:

## Tear down the container
This concludes this tutorial. The following removes the container and the data:
<pre data-test="after">
$ docker rm -f vespa
</pre>

<script src="/js/process_pre.js"></script>
