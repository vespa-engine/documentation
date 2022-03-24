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

<pre style="display:none" data-test="file" data-path="create-vespa-feed.py">
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
{% endhighlight %}
</pre>

With this small script we can process the lastfm test dataset and convert it to a Vespa feed file:

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
{% highlight json%}
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
{% endhighlight %}
</pre>

Observations: 

- The query searched one node and coverage was 100%, see [graceful-degradation](../graceful-degradation.html). 
- The query matched a total of 8 documents (`totalCount`) and we got back the best [ranking](../ranking.html). 
A total of 8 documents matched the query and was fully ranked. 
- We searched 104,212 documents in total. 

The `timing` has 3 fields:

- `querytime` - This is the first matching query protocol where Vespa searches all content nodes 
and where each content node retrieves and ranks documents. The results are merged. 
- `summaryfetchtime` - This is the second query protocol which fills summary data for the global top-k (&hits) parameter 
after the globalb top ranking documents have been found from the previous protocol phase.
- `searchtime` Is roughly the sum of the above and is close to what a benchmarking client will observe (except network latency).

All 3 metrics are reported in seconds. 

Now, we can change our matching to instead of `type=all` to use `type=any`. See 
[supported query types](../reference/query-api-reference.html#model.type)

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Sad Song">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' \
 'query=sad songs' 'hits=1' 'type=any'
</pre>
</div>

Now, our query matches 956 documents and is slightly slower than than the previous query. 
If we include a query term which is frequent in the collection we will recall more documents as
with `type=any` we match all documents that at least contains one of the query terms. 
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
field title type string {
  indexing: summary | index
}
</pre>

Now let us focus on the `tags` field which we defined with `attribute`. 

<pre>
 field tags type weightedset&lt;string&gt; {
      indexing: summary | attribute
 }
 </pre>

In this case, there is no index structure, searching the `attribute` 
field is performed as a linear scan, let us do a search for a popular tag *rock*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"item": "rock"'>
$ vespa query 'yql=select track_id, tags from track where tags contains "rock"' \
  'hits=1' 
</pre>
</div>

The recalls 9,872 documents and takes roughly 22 ms (Dependent on the HW you run on) - If we search
for a less frequent tag, e.g. *remix*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"item": "remix"'>
$ vespa query 'yql=select track_id, tags from track where tags contains "remix"' \
  'hits=1' 
</pre>
</div>

We match fewer documents (319), but roughly the same `querytime` because the matching is performed linearly, 
with millions and millions of documents these two queries would be slow. 

We can combine the tag search with query terms that do have index structures:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"item": "rock"'>
$ vespa query 'yql=select track_id, tags from track where tags contains "rock" and userQuery()' \
  'hits=1' 'query=love'
</pre>
</div>
In this case - the *love* term will restrict the number of documents that needs to be matched with the tags 
search because the two query terms are ANDed. 

#### Searching attribute fields using fast-search 
As we have seen in the previous section, fields with `attribute` does per default does not
build any [inverted index](https://en.wikipedia.org/wiki/Inverted_index) data structures. We can modify
the tags field and add `attribute:fast-search`:

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

We can now try our *remix* tag search again:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"item": "remix"'>
$ vespa query 'yql=select track_id, tags from track where tags contains "remix"' \
  'hits=1' 
</pre>
</div>

Now the query latency will be a few milliseconds since Vespa has built index structures to support
fast-search in the attribute. The downside is increased memory usage and reduced indexing
throughput. See also [when to use fast-search for attributes](feature-tuning.html#when-to-use-fast-search-for-attribute-fields).

### Multi-valued query operators

In this section we look at [multi-value query operators](../multivalue-query-operators.html) and performance
characteristics. Many real-world use cases want to retrieve using structured queries with many values. 

For example, for personalization. Let us assume that we have a process which have built a user profile 
where user x is interested in tags *hard rock*, *rock* and *metal*. How can we retrieve and rank results using
that information? 

We can start with the [dotProduct()](../reference/query-language-reference.html#dotproduct) query operator.
To gain control of [ranking](../ranking.html) we need to add a `rank-profile` to our schema:

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
<pre data-test="exec" data-test-assert-contains="300.0">
$ vespa query \
 'yql=select track_id, title, artist, tags from track where dotProduct(tags,@userProfile)' \
 'userProfile={"hard rock":1, "rock":1,"metal":1}' \
 'hits=1' \
 'ranking=personalized'
</pre>
</div>

<pre>
{% highlight json%}
{
    "timing": {
        "querytime": 0.007,
        "summaryfetchtime": 0.001,
        "searchtime": 0.009000000000000001
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 12191
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
                "id": "index:tracks/0/74d3f4df2989650b2cc095be",
                "relevance": 300.0,
                "source": "tracks",
                "fields": {
                    "track_id": "TRJTBAO128F932191C",
                    "title": "Vastarannan valssi",
                    "artist": "Viikate",
                    "tags": [
                        {
                            "item": "finnish",
                            "weight": 100
                        },
                        {
                            "item": "Suomi",
                            "weight": 100
                        },
                        {
                            "item": "finnish metal",
                            "weight": 100
                        },
                        {
                            "item": "melodic metal",
                            "weight": 100
                        },
                        {
                            "item": "metal",
                            "weight": 100
                        },
                        {
                            "item": "rock",
                            "weight": 100
                        },
                        {
                            "item": "hard rock",
                            "weight": 100
                        },
                        {
                            "item": "suomi rock",
                            "weight": 100
                        },
                        {
                            "item": "rautalanka",
                            "weight": 100
                        }
                    ]
                }
            }
        ]
    }
}
{% endhighlight %}
</pre>

Notice that the query above, would brute force rank tracks where tags would match any of the multi-valued inputs so 
the totalCount becomes 12,191 tracks. Including *pop* in the list increases the number of hits to 14,573. For a large
user profile with many tags, we would easily retrieve and rank the entire document collection. Also notice the 
`relevance` score which is 300, since the top document matches all 3 query tags (1x100 + 1x100 + 1x100 = 300)

This brings us 
to the [wand query operator](../reference/query-language-reference.html#wand). With `wand` we can 
specify the target number of hits that we want to retrieve, so instead of brute forcing ranking all tracks
which matched at least one of the user profile tags we want just to retrieve the best:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ vespa query \
 'yql=select track_id, title, artist, tags from track where ({targetHits:5}wand(tags,@userProfile))' \
 'hits=5' \
 'userProfile={"hard rock":1, "rock":1,"metal":1}' \
 'ranking=personalized'
</pre>
</div>

For larger document collections, the *wand* query operator can significantly improve query performance. We can also combine wand 
with for example the rank() query operator. 


### Tensor Ranking 
In the previous sections we looked at matching and where matching also produced rank features which we could
use to influence the order of the hits returned. In this section we look at ranking using tensor expressions. 

For each of the indexed tracks we have a field named `similar` which is of type `tensor`.

<pre>
field similar type tensor&lt;float&gt;(trackid{}) {
      indexing: summary | attribute
}
</pre>

Let us quickly look at one of the tracks in our collection:


<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ vespa document id:music:track::TRUAXHV128F42694E8
</pre>
</div>

We leave out some of the tags and the tensor cells from the output, but below is an executive summary:

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
                        "trackid": "TRHQMMO128E0791D97"
                    },
                    "value": 0.9855849742889404
                }
            ]
        },
        "tags": {
            "All time favourites": 1,
            "legend": 0,
            "happy": 2,
            "Driving": 3,
            "Love it": 0,
            "Awesome": 0,
            "fhEasy": 0,
            "youth": 0,
            "classic rock": 
        }
    }
}
{% endhighlight %}
</pre>

In the lastfm collection, each track lists similar tracks with a similarity score using float resolution, according to this
algorithm the most similar track to `TRUAXHV128F42694E8` is `TRWJIPT128E0791D99` with a similarity score of 1.0. Let
us search for that document using the query api this time:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ vespa query 'yql=select title,artist from track where track_id contains "TRWJIPT128E0791D99"' 'hits=1'  
</pre>
</div>

Which is 
<pre>
{% highlight json%}
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
            "totalCount": 1
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

Similiar (pun intended), the `TRHQMMO128E0791D97` track is *Heaven* with the same artist. 

Now, if we have have listened to these three tracks:

- `TRUAXHV128F42694E8` Summer Of '69 by Bryan Adams
- `TRWJIPT128E0791D99` Run To You by Bryan Adams
- `TRHQMMO128E0791D97` Heaven by Bryan Adams

What should our algorithm suggest next? We add a new ranking profile with
a tensor dot product between the `query(user_liked)` query tensor and the 
the `similar` document tensor. See [tensor user guide](../tensor-user-guide.html).

<pre>
rank-profile similar {
    first-phase {
      expression: sum(attribute(similar) * query(user_liked))
    }
}
</pre>

Our schema becomes:

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

Here we use a query tensor with our three tracks 
<pre>
ranking.features.query(user_liked)={{trackid:TRUAXHV128F42694E8}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRHQMMO128E0791D97}:1.0}'
</pre>

In the first query we simply rank all documents using `where true`:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
{% raw %}
$ vespa query 'yql=select title,artist from track where true' \
 'ranking.features.query(user_liked)={{trackid:TRUAXHV128F42694E8}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRHQMMO128E0791D97}:1.0}' \
 'ranking=similar' \
 'hits=5'
 {% endraw %}
</pre>
</div>

Notice here that we retrieved all documents and ranked them using the `similar` ranking expression, executing 
the tensor expression. However, as we can also see, we retrieved also the same documents that the user had liked. 

Let us get rid of them using the not query operator (!) in YQL:

<pre>
where !weightedSet(track_id, {"TRUAXHV128F42694E8":1,"TRWJIPT128E0791D99":1,"TRHQMMO128E0791D97":1}) 
</pre>

At the same time we introduced the [weightedSet query operator](../reference/query-language-reference.html#weightedset).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
{% raw %}
$ vespa query 'yql=select title,artist, track_id from track where !weightedSet(track_id,@userLiked)' \
'ranking.features.query(user_liked)={{trackid:TRUAXHV128F42694E8}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRHQMMO128E0791D97}:1.0}' \
'ranking=similar' \
'hits=5' \
'userLiked={"TRUAXHV128F42694E8":1,"TRWJIPT128E0791D99":1,"TRHQMMO128E0791D97":1}'
{% endraw %}
</pre>
</div>

We do get back duplicate tracks back, this something that is an issue with the dataset, but the first non-duplicate hits are

- Please Forgive Me by Bryan Adams
- Total Eclipse Of The Heart by Bonnie Tyler

Some quality love songs right there. Now we can notice that with the not filter, the fully ranked 10,4209 documents out of 10,4212.
The `querytime` is around 120 ms which is on the higher end. We can optimize this as well by adding `fast-search`, which is 
supported for `tensor` fields using sparse mapped dimensions, or mixed tensors using both sparse and dense dimensions. 

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

Repating our query again :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
{% raw %}
$ vespa query 'yql=select title,artist, track_id from track where !weightedSet(track_id,@userLiked)' \
'ranking.features.query(user_liked)={{trackid:TRUAXHV128F42694E8}:1.0,{trackid:TRWJIPT128E0791D99}:1.0,{trackid:TRHQMMO128E0791D97}:1.0}' \
'ranking=similar' \
'hits=5' \
'userLiked={"TRUAXHV128F42694E8":1,"TRWJIPT128E0791D99":1,"TRHQMMO128E0791D97":1}'
{% endraw %}
</pre>
</div>

The `querytime` dropped down to 40 ms instead of 120 ms without the `fast-search` option. 


### Multi-threaded search and ranking 


### Advanced query tracing 


### Performance benchmarking 


## Tear down the container
This concludes this tutorial. The following removes the container and the data:
<pre data-test="after">
$ docker rm -f vespa
</pre>

<script src="/js/process_pre.js"></script>
