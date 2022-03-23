---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa query performance tracing"
---

In this guide, we will guide you through how to to understand Vespa query performance by using
query tracing. This is a practical guide which uses a concrete application and steps 
through how to optimize query serving performance. 

Since Vespa can be used for a wide range of serving use cases this guide is not complete, but covers some important
aspects. 

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
feed in the next section. 

<pre data-test="file" data-path="create-vespa-feed.py">
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

for root, dirs, files in os.walk(directory):
  for filename in files:
    filename = os.path.join(root, filename)
    process_file(filename)
</pre>

Then we can process the lastfm test dataset and convert it to a Vespa feed file:

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


### Services Specification

The [services.xml](../reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.
Write the following to `app/services.xml`:

<pre data-test="file" data-path="app/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

  &lt;container id="default" version="1.0"&gt;
    &lt;search&gt;&lt;/search&gt;
    &lt;document-processing&gt;&lt;/document-processing&gt;
    &lt;document-api&gt;&lt;/document-api&gt;
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

In addition we plan to use our `similar` tensor field for ranking so we also need to define the query tensor:

<pre data-test="file" data-path="app/search/query-profiles/types/root.xml">
&lt;query-profile-type id=&quot;root&quot; inherits=&quot;native&quot;&gt;
    &lt;field name=&quot;ranking.features.query(user_liked)&quot; type=&quot;tensor&amp;lt;float&amp;gt;(trackid{})&quot; /&gt;
&lt;/query-profile-type&gt;
</pre>

<pre data-test="file" data-path="app/search/query-profiles/default.xml">
&lt;query-profile id=&quot;default&quot; type=&quot;root&quot;&gt;
  &lt;field name=&quot;presentation.timing&quot;&gt;true&lt;/field&gt;
&lt;/query-profile&gt;
</pre>

## Deploy the application package

Once we have finished writing our application package, we can deploy it in a Docker container.
See also the [vespa quick start guide](../vespa-quick-start.html).

Start the Vespa container image:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker run -m 6G --detach --name vespa --hostname vespa-msmarco \
  --publish 8080:8080 --publish 19071:19071 \
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

Now, deploy the Vespa application:

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

Now, we have our dataset indexed and we can start look at query performance.

## Basic query performance understanding

Once the data has started feeding, we can already send queries to our search app 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Sad Song">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' 'query=sad songs' 'hits=1'
</pre>
</div>

This query combines YQL [userQuery()](../reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](../reference/simple-query-language-reference.html), the 
default query type is using `all` requiring that all the terms match the document. 


The above example searches for *sad AND songs* in the `default` fieldset, 
which in our schema includes the track `title` and `artist` fields. 

The result output for the above query will look something like this:

<pre>
{
    "timing": {
        "querytime": 0.007,
        "summaryfetchtime": 0.0,
        "searchtime": 0.009000000000000001
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 8
        },
        "coverage": {
            "coverage": 100,
            "documents": 104212,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "index:tracks/0/9820cd837f7687739120d201",
                "relevance": 0.17032164450816525,
                "source": "tracks",
                "fields": {
                    "track_id": "TRNYPDO128F92F61AC",
                    "title": "Sad Song",
                    "artist": "Davell Crawford"
                }
            }
        ]
    }
}
</pre>

Observations: 

- The query searched one node and coverage was 100%, see [graceful-degradation](../graceful-degradation.html). 
- The query matched a total of 8 documents (`totalCount`) and we got back the best [ranking](../ranking.html). 
A total of 8 documents matched the query and was fully ranked. 
- We searched 104,212 documents in total. 

The `timing` has 3 fields:

- `querytime` - This is the first matching query protocol where Vespa searches all content nodes 
and where each content node retrieves and ranks documents. The results are merged. 
- `summaryfetchtime` - This is the second query protocol which fills summary data for the top k (&hits) parameter after the global
best ranking documents have been found from the previous protocol phase.
- `searchtime` Is roughly the sum of the above and is close to what a benchmarking client will observe (except network latency).

Now, we can change our matching to instead of `type=all` to use `type=any`. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Sad Song">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
 'query=sad songs' 'hits=1' 'type=any'
</pre>
</div>

Now, our query matches 956 documents and is slightly slower than than the previous query. 
If we include a query term which is frequent in the collection we start recalling more documents. 
For example *the* is a very common word in English, let us try:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Sad Country Song">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
 'query=the sad songs' 'hits=1' 'type=any'
</pre>
</div>

Now, our query matches 22,763 documents, or roughly 20% of the total number of documents. 
If you compare the `querytime` of these two querie, the one which matches the most documents have highest `querytime`. 
In worst case, the search matches all documents.  

We can try a different query specification where we retrieve all documents and instead 
use the [rank()](../reference/query-language-reference.html#rank) query. The first operand is 'true' which 
means just match all documents, then rank by the query terms. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Sad Country Song">
$ vespa query 'yql=select artist, title, track_id from track where rank(true,userQuery())' \
 'query=the sad songs' 'hits=1' 'type=any'
</pre>
</div>

Now, our query matched all documents (Compare `totalCount` with `documents`) and latency is much higher than the previous query.  

So for query and matching performance is greatly impacted by the number of documents that matches the query. Or like queries with
type `any` requires more compute resources than type `all`.  There is an optimization of *or-like* queries, using
`weakAnd`. See the [using wand with vespa](../using-wand-with-vespa.html) guide for details. 

Run the same query, but instead of `type=any` use `type=weakAnd`, 
see [supported query types](../reference/query-api-reference.html#model.type)

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Sad Country Song">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' 'query=the sad songs' 'hits=1' 'type=weakAnd'
</pre>
</div>

Compared to the type `any` query which fully ranked 22,763 documents we now only rank 2,590 documents and latency is much lower, 
also notice that the much faster search returns the same document at the first position. 


### Hits and summaries 
In the previous examples we only asked for one hit with `hits=1` parameter, also if you have been paying attention you would
see that the `summaryfetchtime` have been pretty constant over the previous text search examples. Let us see 
what happens when we ask for 200 hits:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Sad Country Song">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
 'query=the sad songs' 'hits=200' 'type=weakAnd' | head -31
</pre>
</div>

Now, we can notice that the `summaryfetchtime` increases significantly,
 while `querytime` is relatively unchanged. Repeating the query a second time will reduce the time
 due to the summary cache, see [caches in vespa](../performance/caches-in-vespa.html).

There are largely four factors which determines the `summaryfetchtime`

- The number of hits requested and number of content nodes that produced the query result. With many content nodes
in the group the query was dispatched to we expect that hits should be distributed across the nodes so that each node
does less work.  
- The network package size of each hit (larger fields, more resources spent)
- The summary used and which fields goes into the summary. For example, a
 [document-summary](../document-summaries.html) which only contain fields that are `attribute` fields will
 be fetched out of memory, while the `default` summary, or others containing at least one none-attribute
 field will potentially touch disk. 
- [summary-features](../reference/schema-reference.html#summary-features) used to return [rank features](../reference/rank-features.html)

Let us create a dedicated [document-summary](../document-summaries.html) which
only contain the `track_id` field. 

<pre>
document-summary track_id {
    summary track_id type string { 
      source: track_id
    }
}
</pre>

The full new schema:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

  document track {

    field track_id type string {
      indexing: summary | attribute
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
<pre data-test="exec" data-test-assert-contains="TRTCULM128F933542C">
$ vespa query 'yql=select track_id from track where userQuery()' \
 'query=the sad songs' 'hits=200' 'type=weakAnd' 'summary=track_id' | head -31
</pre>
</div>

In this particular case the difference is not that large, but for larger number of hits and larger documents. 
A note on select scoping, e.g, `select title, track_id from ..`. When using the default summary, all
fields are regardless delivered to the stateless container, which removes the set of fields not wanted. Hence select
scoping only reduces the amount of data transfered back to the client, and does not impact the performance of
the internal communication.

### Searching attribute fields 
In the previous sections we looked at text searching over a `default` `fieldset` using fields with
`indexing:index`. With `index` Vespa builds inverted index structures for faster evaluation of the query. 

<pre>
field foo type string {
  indexing: index
}
</pre>

Now let us focus on the `tags` field which we defined with `attribute`. 

<pre>
 field tags type weightedset&lt;string&gt; {
      indexing: summary | attribute
 }
 </pre>

In this case, there is no index structure, let us do a search for a popular tag *rock*

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="TRFPDMZ128F1491C75">
$ vespa query 'yql=select track_id from track where tags contains "rock"' \
  'hits=1' 
</pre>
</div>

The recalls 9,872 documents and takes roughly 22 ms (Dependent on the HW you run on) - If we search
for a less frequent tag, e.g. *remix*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="TRKOOUV128F931E8F0">
$ vespa query 'yql=select track_id from track where tags contains "remix"' \
  'hits=1' 
</pre>
</div>

We get less hits (319), but roughly the same `querytime`. 


## Tear down the container
This removes the container and the data:
<pre data-test="after">
$ docker rm -f vespa
</pre>
</div>

<script src="/js/process_pre.js"></script>
