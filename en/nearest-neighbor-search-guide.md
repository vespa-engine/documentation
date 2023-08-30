---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa nearest neighbor search - a practical guide"
---

 This guide is a practical introduction to using Vespa nearest neighbor search query operator and how to combine nearest
 neighbor search with other Vespa query operators. The guide uses Vespa's [embedding](embedding.html)
 support to map text to vectors. The guide also covers diverse, efficient candidate retrievers 
 which can be used as candidate retrievers in a [multi-phase ranking](phased-ranking.html) funnel. 

 The guide uses the [Last.fm](http://millionsongdataset.com/lastfm/) tracks dataset for illustration. 
 Latency numbers mentioned in the guide are obtained from running this guide on a M1.
 See also the generic [Vespa performance - a practical guide](performance/practical-search-performance-guide.html).

This guide covers the following:

- [Free text search using Vespa weakAnd](#free-text-search-using-vespa-weakand)
- [Sparse maximum inner product search using Vespa wand](#maximum-inner-product-search-using-vespa-wand)
- [Exact nearest neighbor search](#exact-nearest-neighbor-search)
- [Approximate nearest neighbor search](#approximate-nearest-neighbor-search)
- [Combining approximate nearest neighbor search with filters](#combining-approximate-nearest-neighbor-search-with-query-filters)
- [Strict filters and distant neighbors - distanceThresholding](#strict-filters-and-distant-neighbors)
- [Hybrid sparse and dense retrieval methods with Vespa](#hybrid-sparse-and-dense-retrieval-methods-with-vespa)
- [Using multiple nearest neighbor search operators in the same query](#multiple-nearest-neighbor-search-operators-in-the-same-query)
- [Controlling filter behavior](#controlling-filter-behavior)

The guide includes step-by-step instructions on how to reproduce the experiments. 

{% include pre-req.html memory="4 GB" extra-reqs="
<li>Python3 for converting the dataset to Vespa json.</li>
<li><code>curl</code> to download the dataset.</li>"%}

## Installing vespa-cli
This tutorial uses [Vespa-CLI](vespa-cli.html),
the official command-line client for Vespa.ai. 
It is a single binary without any runtime dependencies and is available for Linux, macOS and Windows:

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

To download the dataset execute the following (120 MB zip file):
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o lastfm_test.zip \
    http://millionsongdataset.com/sites/default/files/lastfm/lastfm_test.zip 
$ unzip lastfm_test.zip
</pre>
</div>

The downloaded data must to be converted to
[the Vespa JSON feed format](reference/document-json-format.html). 

This [python](https://www.python.org/) script can be used to traverse 
the dataset files and create a JSONL formatted feed file with Vespa put operations. 
The [schema)(schemas.html) is covered in the next section. 
The number of unique `tags` is used as a proxy for the popularity of the track. 

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
        n = len(tags_dict)

        vespa_doc = {
            "put": "id:music:track::%s" % track_id,
                "fields": {
                    "title": remove_control_characters(title),
                    "track_id": track_id,
                    "artist": remove_control_characters(artist),
                    "tags": tags_dict,
                    "popularity": n
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
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
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
        n = len(tags_dict)

        vespa_doc = {
            "put": "id:music:track::%s" % track_id,
                "fields": {
                    "title": remove_control_characters(title),
                    "track_id": track_id,
                    "artist": remove_control_characters(artist),
                    "tags": tags_dict,
                    "popularity": n
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
{% endhighlight %}</pre></div>

Process the dataset and convert it to
[Vespa JSON document operation](reference/document-json-format.html) format.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ python3 create-vespa-feed.py lastfm_test > feed.jsonl
</pre>
</div>

## Create a Vespa Application Package
A [Vespa application package](application-packages.html) is the set 
of configuration files and Java plugins that together define the behavior of a Vespa system:
what functionality to use, the available document types, how ranking will be done,
and how data will be processed during feeding and indexing.

The minimum required files to create the basic search application are `track.sd` and `services.xml`.
Create directories for the configuration files and embedding model:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir -p app/schemas; mkdir -p app/search/query-profiles/; mkdir -p app/model
</pre>
</div>

### Schema

A [schema](schemas.html) is a configuration of a document type and additional synthetic fields and [ranking](ranking.html)
configuration.

For this application, we define a `track` document type.

Write the following to `app/schemas/track.sd`:

<pre data-test="file" data-path="app/schemas/track.sd">
schema track {

    document track {

        field track_id type string {
            indexing: summary | attribute
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

        field popularity type int {
            indexing: summary | attribute
            attribute: fast-search
            rank: filter
        }
    }

    field embedding type tensor&lt;float&gt;(x[384]) {
            indexing: input title | embed e5 |attribute | index
            attribute {
                distance-metric: angular
            }
            index {
                hnsw {
                    max-links-per-node: 16
                    neighbors-to-explore-at-insert: 50
                }
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

    rank-profile tags {
        first-phase {
            expression: rawScore(tags)
        }
    }

    rank-profile bm25 {
        first-phase {
            expression: bm25(title)
        }
    }

    rank-profile closeness {
        num-threads-per-search: 1
        match-features: distance(field, embedding)

        inputs {
            query(q)  tensor&lt;float&gt;(x[384])
            query(q1) tensor&lt;float&gt;(x[384])
        } 

        first-phase {
            expression: closeness(field, embedding)
        }
    }

    rank-profile closeness-t4 inherits closeness {
        num-threads-per-search: 4
    }

    rank-profile closeness-label inherits closeness {
        match-features: closeness(label, q) closeness(label, q1)
    }

    rank-profile hybrid inherits closeness {
        inputs {
            query(wTags) : 1.0
            query(wPopularity) :  1.0
            query(wTitle) : 1.0
            query(wVector) : 1.0
        }
        first-phase {
            expression {
                query(wTags) * rawScore(tags) + 
                query(wPopularity) * log(attribute(popularity)) + 
                query(wTitle) * log(bm25(title)) + 
                query(wVector) * closeness(field, embedding)
            }
        }
        match-features {
            rawScore(tags)
            attribute(popularity)
            bm25(title)
            closeness(field, embedding)
            distance(field, embedding)
        }
    }
}
</pre>

This document schema is explained in the [practical search performance guide](performance/practical-search-performance-guide.html),
the addition is the `embedding` field which is defined as a synthetic field outside of the document. This 
field is populated by Vespa's [embedding](embedding.html) functionality. Using the [E5](https://huggingface.co/intfloat/e5-small-v2) 
text embedding model (described in this [blog post](https://blog.vespa.ai/enhancing-vespas-embedding-management-capabilities/)). 

Note that the `closeness` rank-profile defines two
query input tensors using [inputs](reference/schema-reference.html#inputs). 

<pre>
field embedding type tensor&lt;float&gt;(x[384]) {
    indexing: input title | embed e5 | attribute | index
    attribute {
        distance-metric: angular
    }
    index {
        hnsw {
            max-links-per-node: 16
            neighbors-to-explore-at-insert: 50
        }
    }
 }
</pre>

See [Approximate Nearest Neighbor Search using HNSW Index](approximate-nn-hnsw.html)
for an introduction to `HNSW` and the `HNSW` tuning parameters.

### Services Specification

The [services.xml](reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.
Write the following to `app/services.xml`:

<pre data-test="file" data-path="app/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

    &lt;container id="default" version="1.0"&gt;
        &lt;search/&gt;
        &lt;document-api/&gt;
        &lt;component id="e5" type="hugging-face-embedder"&gt;
            &lt;transformer-model path="model/e5-small-v2-int8.onnx"/&gt;
            &lt;tokenizer-model path="model/tokenizer.json"/&gt;
        &lt;/component&gt;
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

The default [query profile](query-profiles.html) can be used to override
default query api settings for all queries.

The following enables [presentation.timing](reference/query-api-reference.html#presentation.timing) and
renders `weightedset` fields as a JSON maps. 

<pre data-test="file" data-path="app/search/query-profiles/default.xml">
&lt;query-profile id=&quot;default&quot;&gt;
    &lt;field name=&quot;presentation.timing&quot;&gt;true&lt;/field&gt;
    &lt;field name=&quot;renderer.json.jsonWsets&quot;&gt;true&lt;/field&gt;
&lt;/query-profile&gt;
</pre>

The final step is to download embedding model files

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o app/model/e5-small-v2-int8.onnx \
    https://github.com/vespa-engine/sample-apps/raw/master/simple-semantic-search/model/e5-small-v2-int8.onnx 
$ curl -L -o app/model/tokenizer.json \
    https://github.com/vespa-engine/sample-apps/raw/master/simple-semantic-search/model/tokenizer.json 
</pre>
</div>

## Deploy the application package

The application package can now be deployed to a running Vespa instance.
See also the [Vespa quick start guide](vespa-quick-start.html).

Start the Vespa container image using Docker:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker run --detach --name vespa --hostname vespa-container \
  --publish 8080:8080 --publish 19071:19071 \
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

Once ready, deploy the application using `vespa deploy`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

## Index the dataset

Feed the dataset. During indexing, Vespa will invoke the embedding model (which is relatively computionally expensive), 
so feeding and indexing this dataset takes about 180 seconds on a M1 laptop (535 inserts/s).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa feed -t http://localhost:8080 feed.jsonl
</pre>
</div>

## Free-text search using Vespa weakAnd 
The following sections uses the Vespa [query api](reference/query-api-reference.html) and 
formulate queries using Vespa [query language](query-language.html). The examples uses the
[vespa-cli](vespa-cli.html) command which supports running queries.

The CLI uses the [Vespa query api](query-api.html). 
Use `vespa query -v` to see the curl equivalent:

<pre>
$ vespa query -v 'yql=select ..'
</pre>

The first example is searching and ranking using the `bm25` rank profile defined in the schema.
It uses the [bm25](reference/bm25.html) rank feature as the `first-phase` relevance score:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=1' \
    'type=all' \
    'ranking=bm25'
</pre>
</div>

This query combines YQL [userQuery()](reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](reference/simple-query-language-reference.html).
The [query type](reference/query-api-reference.html#model.type) is
using `all`, requiring that all the terms match. 

The above query example searches for *total AND eclipse AND of AND the AND heart* 
in the `default` fieldset, which in the schema includes the `title` and `artist` fields.

The [result](reference/default-result-format.html) 
for the above query will look something like this:

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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 22.590392521579684,
                "source": "tracks",
                "fields": {
                    "track_id": "TRKLIXH128F42766B6",
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

This query only matched one document because the query terms were `AND`ed. 
We can change matching to use `type=any` instead of the default `type=all`. See 
[supported query types](reference/query-api-reference.html#model.type).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=1' \
    'ranking=bm25' \
    'type=any'
</pre>
</div>

Now, the query matches 24,053 documents and is considerably slower than the previous query. 
Comparing `querytime` of these two query examples, the one which matches the most documents have highest `querytime`. 
In worst case, the search query matches all documents.

Query matching performance is greatly impacted by the number of documents that matches the query specification. 
Type `any` queries requires more compute resources than type `all`.  

There is an optimization available for `type=any` queries, using
the `weakAnd` query operator which implements the WAND algorithm. 
See the [using wand with Vespa](using-wand-with-vespa.html) guide for more details. 

Run the same query, but instead of `type=any` use `type=weakAnd`, 
see [supported query types](reference/query-api-reference.html#model.type):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=1' \
    'ranking=bm25' \
    'type=weakAnd'
</pre>
</div>

Compared to the type `any` query which fully ranked 24,053 documents, 
the query only expose about 3,600 documents to the `first-phase` ranking expression. 
Also notice that the faster search returns the same document at the first position. 


<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query="total eclipse of the heart"' \
    'hits=1' \
    'ranking=bm25' \
    'type=weakAnd'
</pre>
</div>
In this case, the query input *"total eclipse of the heart"* is parsed as a phrase query, and the
search only finds 1 document matching the exact phrase.  

## Maximum Inner Product Search using Vespa WAND

The previous section introduced the `weakAnd` query operator which integrates 
with [linguistic processing](linguistics.html) and string matching using `match: text`.  

The following examples uses the
[wand()](reference/query-language-reference.html#wand) query operator. 
The `wand` query operator calculates the maximum inner product
between the sparse query and document feature integer
weights. The inner product ranking score calculated by the `wand` query operator 
can be used in a ranking expression by the [rawScore(name)](reference/rank-features.html#match-operator-scores)
rank feature. 

<pre>
rank-profile tags {
    first-phase {
        expression: rawScore(tags)
    }
}
</pre>

This query searches the track document type using a learned sparse *userProfile* representation, 
performing a maximum inner product search over the `tags` weightedset field. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="The Rose">
$ vespa query \
    'yql=select track_id, title, artist from track where {targetHits:10}wand(tags, @userProfile)' \
    'userProfile={"pop":1, "love songs":1,"romantic":10, "80s":20 }' \
    'hits=2' \
    'ranking=tags'
</pre>
</div>
The query asks for 2 hits to be returned, and uses the `tags` rank profile. 
The [result](reference/default-result-format.html) 
for the above query will look something like this:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.051000000000000004,
        "summaryfetchtime": 0.004,
        "searchtime": 0.057
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 66
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
                "id": "index:tracks/0/57037bdeb9caadebd8c235e1",
                "relevance": 2500.0,
                "source": "tracks",
                "fields": {
                    "track_id": "TRMIBBE128E078B487",
                    "title": "The Rose   ***",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/8eb2e19ee627b054113ba4c9",
                "relevance": 2344.0,
                "source": "tracks",
                "fields": {
                    "track_id": "TRKDRVK128F421815B",
                    "title": "Nothing's Gonna Change My Love For You",
                    "artist": "Glenn Medeiros"
                }
            }
        ]
    }
}

{% endhighlight %}</pre>
The `wand` query operator exposed a total of about 60 documents to the `first-phase` ranking which 
uses the `rawScore(tag)` rank-feature directly, so the `relevancy` is the 
result of the sparse dot product between the sparse user profile and the document tags. 

The `wand` query operator is safe, meaning, it returns the same top-k results as 
the brute-force `dotProduct` query operator. `wand` is a type of query operator which
performs matching and ranking interleaved and skipping documents
which cannot compete into the final top-k results. 
See the [using wand with Vespa](using-wand-with-vespa.html) guide for more details on 
using `wand` and `weakAnd` query operators. 

## Exact nearest neighbor search
Vespa's nearest neighbor search operator supports doing exact brute force nearest neighbor search
using dense representations. The first query example uses [exact nearest neighbor search](nearest-neighbor-search.html)
and Vespa embed functionality: 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select title, artist from track where {approximate:false,targetHits:10}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

Query breakdown:

- Search for ten (`targetHits:10`) nearest neighbors of the `query(q)` query tensor over the `embedding`
document tensor field. 
- The annotation `approximate:false` tells Vespa to perform exact search.
- The `hits` parameter controls how many results are returned in the response. Number of `hits`
requested does not impact `targetHits`. Notice that `targetHits` is per content node involved in the query. 
- `ranking=closeness` tells Vespa which [rank-profile](ranking.html) to score documents. One must 
specify how to *rank* the `targetHits` documents retrieved and exposed to `first-phase` ranking expression
in the `rank-profile`.
- `input.query(q)` is the query vector produced by the [embedder](embedding.html#embedding-a-query-text).

Not specifying [ranking](reference/query-api-reference.html#ranking.profile) will cause
Vespa to use [nativeRank](nativerank.html) which does not use the vector similarity, causing
results to be randomly sorted. 

The above exact nearest neighbor search will return the following
[result](reference/default-result-format.html):

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
            "totalCount": 101
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 1.0,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

The exact search takes approximately 14ms, performing 95,666 distance calculations. 
A total of about 101 documents were exposed to the first-phase ranking during the search as can be seen from
`totalCount`. The `relevance` is the result of the `rank-profile` scoring. 

It is possible to reduce search latency of the exact search by throwing more CPU resources at it. 
Changing the rank-profile to `closeness-t4` makes Vespa use four threads per query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select title, artist from track where {approximate:false,targetHits:10}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness-t4' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

Now, the exact search latency is reduced by using more threads, 
see [multi-threaded searching and ranking](performance/practical-search-performance-guide.html#multithreaded-search-and-ranking)
for more on this topic.
<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.008,
        "summaryfetchtime": 0.001,
        "searchtime": 0.008
    }
}
{% endhighlight %}</pre>

## Approximate nearest neighbor search
This section covers using the faster, but approximate, nearest neighbor search. The 
`track` schema's `embedding` field has the `index` property,  which means Vespa builds a 
`HNSW` index to support fast, approximate vector search. See 
[Approximate Nearest Neighbor Search using HNSW Index](approximate-nn-hnsw.html)
for an introduction to `HNSW` and the tuning parameters.

The default query behavior is using `approximate:true` when the `embedding` 
field has `index`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec"  data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select title, artist from track where {targetHits:10,hnsw.exploreAdditionalHits:20}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

Which returns the following response:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.004,
        "summaryfetchtime": 0.001,
        "searchtime": 0.004
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 10
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 0.5992897837210658,
                "source": "tracks",
                "fields": {
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

Now, the query is faster, and also uses less resources during the search. 
To get latency down to 20 ms with the exact search one had to use 4 matching threads. In this case the
result latency is down to 4ms with a single matching thread. 
For this query example, the approximate search returned the exact same top-1 hit and there was
no accuracy loss for the top-1 position. Note that the overall query time is dominated
by the `embed` inference. 

A few key differences between `exact` and `approximate` neighbor search:

- `totalCount` is different, when using the approximate version, Vespa exposes exactly `targethits` to the 
configurable `first-phase` rank expression in the chosen `rank-profile`.
 The exact search is using a scoring heap during evaluation (chunked distance calculations), and documents which at some time
were put on the top-k heap are exposed to first phase ranking.

- The search is approximate and might not return the exact top 10 closest vectors as with exact search. This
is a complex tradeoff between accuracy, query performance , and memory usage. 
See [Billion-scale vector search with Vespa - part two](https://blog.vespa.ai/billion-scale-knn-part-two/)
for a deep-dive into these trade-offs.

With the support for setting `approximate:false|true` a developer can quantify accuracy loss by comparing the 
results of exact nearest neighbor search with the results of the approximate search. 
By doing so, developers can quantify the recall@k or overlap@k, 
and find the right balance between search performance and accuracy. Increasing `hnsw.exploreAdditionalHits`
improves accuracy (recall@k) at the cost of a slower query. 

## Combining approximate nearest neighbor search with query filters
Vespa allows combining the search for nearest neighbors to be constrained by regular query filters. 
In this query example the `title` field must contain the term `heart`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="of the Heart">
$ vespa query \
    'yql=select title, artist from track where {targetHits:10}nearestNeighbor(embedding,q) and title contains "heart"' \
    'hits=2' \
    'ranking=closeness' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>
Which returns the following response:
<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.005,
        "summaryfetchtime": 0.001,
        "searchtime": 0.007
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 47
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 1.0,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/d0cb22cbcdb30796eca3a731",
                "relevance": 0.6831990558852824,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.46370225688355227
                    },
                    "title": "Cirrhosis of the Heart",
                    "artist": "Foetus"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>
The query term `heart` does in this case not impact the ordering (ranking) of the results, as the
rank-profile used only uses the vector similarity closeness. 

When using filtering, it is important for performance reasons that the fields that are included in the filters have
been defined with `index` or `attribute:fast-search`.
See [searching attribute fields](performance/practical-search-performance-guide.html#searching-attribute-fields).

The optimal performance for combining nearestNeighbor search with filtering, where the query term(s) does not influence ranking, is achieved
using `rank: filter` in the schema (See [blog post for details](reference/ranking-expressions.html)):

<pre>
field popularity type int {
    indexing: summary | attribute
    rank: filter
    attribute: fast-search
}
</pre>

Matching against the popularity field does not influence ranking, and Vespa can use the most efficient posting
list representation. Note that one can still access the value of
the `popularity` attribute in [ranking expressions](ranking.html). 

<pre>
rank-profile popularity {
    first-phase {
        expression: attribute(popularity)
    }
}
</pre>


In the following example, since the `title` field does not have `rank: filter` one can instead
flag that the term should not be used by any ranking expression by 
using the [`ranked` query annotation](reference/query-language-reference.html#ranked). 

The following disables [term based ranking](reference/query-language-reference.html#ranked) and
the matching against the `title` field can use the most efficient posting list representation.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="of the Heart">
$ vespa query \
    'yql=select title, artist from track where {targetHits:10}nearestNeighbor(embedding,q) and title contains ({ranked:false}"heart")' \
    'hits=2' \
    'ranking=closeness' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

In the previous examples, since the rank-profile did only use the `closeness` rank feature,  
the matching would not impact the score anyway. 

Vespa also allows combining the `nearestNeighbor` query operator with any other Vespa query operator.  

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"popularity": 100'>
$ vespa query \
    'yql=select title, popularity, artist from track where {targetHits:10}nearestNeighbor(embedding,q) and popularity > 20 and artist contains "Bonnie Tyler"' \
    'hits=2' \
    'ranking=closeness' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

This query example restricts the earch to tracks by `Bonnie Tyler` with `popularity > 20`.

### Strict filters and distant neighbors 
When combining nearest neighbor search with strict filters which matches less than 5 percentage of the total number of documents, 
Vespa will instead of searching the HNSW graph, constrained by the filter, fall back to using exact nearest neighbor search.
See [Controlling filter behavior](#controlling-filter-behavior) for how to adjust the threshold for which strategy that is used.
When falling back to exact search users will observe that `totalCount` increases and is higher than `targetHits`.
As seen from previous examples, more hits are exposed to the `first-phase` ranking expression when using 
exact search. When using exact search with filters, the search can also use multiple threads to evaluate the query, which
helps reduce the latency impact. 

With strict filters that removes many hits, the hits (nearest neighbors) might not be *near* in the embedding space, but *far*,
or *distant* neighbors. Technically, all document vectors are a neighbor of the query vector, 
but with a varying distance.

With restrictive filters, the neighbors that are returned might be of low quality (far distance). 
One way to combat this effect is to use the [distanceThreshold](reference/query-language-reference.html#distancethreshold)
query annotation parameter of the `nearestNeighbor` query operator. 
The value of the `distance` depends on the [distance-metric](reference/schema-reference.html#distance-metric) used. 
By adding the [distance(field,embedding)](reference/rank-features.html#distance(dimension,name)) rank-feature to
the `match-features` of the `closeness` rank-profiles, it is possible to analyze what distance 
could be considered too far. 
See [match-features reference](reference/schema-reference.html#match-features).


Note that distance of 0 is perfect, while distance of 1 is distant. The `distanceThreshold` 
remove hits that have a **higher** `distance(field, embedding)` than `distanceThreshold`. The
`distanceThreshold` is applied regardless of performing exact or approximate search. 

The following query with a restrictive filter on popularity is used for illustration:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title, popularity, artist from track where {targetHits:10}nearestNeighbor(embedding,q) and popularity > 80' \
    'hits=2' \
    'ranking=closeness-t4' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

The above query returns 

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.008,
        "summaryfetchtime": 0.002,
        "searchtime": 0.011
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 63
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 0.5992897875290117,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.6686418170467985
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler",
                    "popularity": 100
                }
            },
            {
                "id": "index:tracks/0/57c74bd2d466b7cafe30c14d",
                "relevance": 0.6700445710774405,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.49243803049099677
                    },
                    "title": "Eclipse",
                    "artist": "Kyoto Jazz Massive",
                    "popularity": 100
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

By using a `distanceTreshold` of 0.2,  the `Eclipse` track will be removed from the result
because it's `distance(field, embedding)` is close to 0.5. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query \
    'yql=select title, popularity, artist from track where {distanceThreshold:0.2,targetHits:10}nearestNeighbor(embedding,q) and popularity > 80' \
    'hits=2' \
    'ranking=closeness' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.008,
        "summaryfetchtime": 0.001,
        "searchtime": 0.011
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 0.5992897875290117,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.6686418170467985
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler",
                    "popularity": 100
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

Setting appropriate `distanceThreshold` is best handled by supervised learning as 
the distance threshold should be calibrated based on the query complexity 
and possibly also the feature distributions of the returned top-k hits. 
Having the `distance` rank feature returned as `match-features`, 
enables post-processing of the result using a custom 
[re-ranking/filtering searcher](reranking-in-searcher.html). 
The post-processing searcher can analyze the score distributions of the returned top-k hits
(using the features returned with `match-features`), 
remove low scoring hits before presenting the result to the end user, 
or not return any results at all. 

## Hybrid sparse and dense retrieval methods with Vespa
In the previous filtering examples the ranking was not impacted by the filters.
They were only used to impact recall, not the order of the results. The following examples
demonstrate how to perform hybrid retrieval combining the efficient query operators in
a single query. Hybrid retrieval can be used as the first phase in a multi-phase ranking funnel, see 
Vespa's [phased ranking](phased-ranking.html).

The first query example combines the `nearestNeighbor` operator with the `weakAnd` operator,
combining them using logical disjunction (`OR`). This type of query enables retrieving
both based on semantic (vector distance) and traditional sparse (exact) matching. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title, artist from track where {targetHits:100}nearestNeighbor(embedding,q) or userQuery()' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

The query combines the sparse `weakAnd` and dense `nearestNeighbor` query operators 
using logical disjunction. 
Both query operator retrieves the target number of hits (or more), ranked by its inner 
raw score function.

The hits exposed to the configurable `first-phase` ranking expression is a combination
of the best hits from the two different retrieval strategies. 
The ranking is performed using the `hybrid` rank profile which serves as an example
how to combine the different efficient retrievers. 

<pre>
rank-profile hybrid inherits closeness {
        inputs {
            query(wTags) : 1
            query(wPopularity) : 1
            query(wTitle) : 1
            query(wVector) : 1
        }
        first-phase {
            expression {
                query(wTags) * rawScore(tags) + 
                query(wPopularity) * log(attribute(popularity)) + 
                query(wTitle) * log(bm25(title)) + 
                query(wVector) * closeness(field, embedding)
            }
        }
        match-features {
            rawScore(tags)
            attribute(popularity)
            bm25(title)
            closeness(field, embedding)
        }
    }
</pre>

The query returns the following result:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.005,
        "summaryfetchtime": 0.0,
        "searchtime": 0.005
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1181
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 8.72273659535481,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 22.591334631476823,
                        "closeness(field,embedding)": 1.0,
                        "distance(field,embedding)": 0.0,
                        "query(wVector)": 1.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/57c74bd2d466b7cafe30c14d",
                "relevance": 7.762818642331215,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 12.03241051547921,
                        "closeness(field,embedding)": 0.6700445710774405,
                        "distance(field,embedding)": 0.49243803049099677,
                        "query(wVector)": 1.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Eclipse",
                    "artist": "Kyoto Jazz Massive"
                }
            }
        ]
    }
}{% endhighlight %}</pre>

The result hits also include [match-features](reference/schema-reference.html#match-features) which 
can be used for feature logging for learning to rank, or to simply
debug the various feature components used to calculate the `relevance` score. 

In the below query, we lower the weight of the popularity factor by adjusting `query(wPopularity)` to 0.1: 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title, artist from track where {targetHits:100}nearestNeighbor(embedding,q) or userQuery()' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")' \
    'input.query(wPopularity)=0.1'
</pre>
</div>

Which changes the order and a different hit is surfaced at position two:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.005,
        "summaryfetchtime": 0.0,
        "searchtime": 0.006
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1181
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 4.5780834279655265,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 22.591334631476823,
                        "closeness(field,embedding)": 1.0,
                        "distance(field,embedding)": 0.0,
                        "query(wVector)": 1.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/51bae2353aa0c9e9c70bf94e",
                "relevance": 4.044676118507788,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 23.0,
                        "bm25(title)": 20.07427771872962,
                        "closeness(field,embedding)": 0.7316874168710507,
                        "distance(field,embedding)": 0.3667038368328748,
                        "query(wVector)": 1.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Total Eclipse",
                    "artist": "The Alan Parsons Project"
                }
            }
        ]
    }
}

{% endhighlight %}</pre>

The following query adds the personalization component using the sparse
user profile into the retriever mix. 
<pre>
userProfile={"love songs":1, "love":1,"80s":1}
</pre>
Which can be used with the `wand` query operator to retrieve personalized hits for ranking. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Straight From The Heart'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where {targetHits:100}nearestNeighbor(embedding,q) or userQuery() or ({targetHits:10}wand(tags, @userProfile))' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")' \
    'input.query(wPopularity)=0.1' \
    'userProfile={"love songs":1, "love":1,"80s":1}' 
</pre>
</div>

Now we have new top ranking documents. Notice that `totalCount` increases as the 
`wand` query operator retrieved more hits into `first-phase` ranking.

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.01,
        "summaryfetchtime": 0.003,
        "searchtime": 0.014
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1243
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
                "id": "index:tracks/0/fc82cbb0d5d5b5747d65c451",
                "relevance": 144.9997464905854,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 6.722228506472074,
                        "closeness(field,embedding)": 0.633809749439362,
                        "distance(field,embedding)": 0.5777605202263811,
                        "query(wVector)": 1.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Straight From The Heart",
                    "artist": "Bryan Adams"
                }
            },
            {
                "id": "index:tracks/0/66b3ab21d5eb0a9078bf8787",
                "relevance": 135.51757722374737,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 34.0,
                        "bm25(title)": 4.7884050004449215,
                        "closeness(field,embedding)": 0.5987438006081908,
                        "distance(field,embedding)": 0.6701634304759765,
                        "query(wVector)": 1.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Lady Of The Dawn",
                    "artist": "Mike Batt"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

Changing from logical `OR` to `AND` instead will intersect the result of the two efficient retrievers.
The search for nearest neighbors is then constrained to documents which at least matches one of
the query terms in the `weakAnd`.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where {targetHits:100}nearestNeighbor(embedding,q) and userQuery()' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")' 
</pre>
</div>

In this case, the documents exposed to ranking must match at least one of the query terms (for WAND to retrieve it).
It is also possible to combine hybrid search with filters:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Little Black Heart'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where {targetHits:100}nearestNeighbor(embedding,q) and userQuery() and popularity < 75' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")' 
</pre>
</div>

Another interesting approach for hybrid retrieval is to use Vespa's 
[rank()](reference/query-language-reference.html#rank) query operator. The first operand
of the `rank()` operator is used for retrieval, and the remaining operands are only used to compute
rank features for those hits retrieved by the first operand. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where rank({targetHits:100}nearestNeighbor(embedding,q), userQuery())' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")' 
</pre>
</div>

This query returns 100 documents, since only the first operand of the `rank` query operator was used for 
*retrieval*, the sparse `userQuery()` representation was only used to calculate sparse 
[rank features](reference/rank-features.html) for
the results retrieved by the `nearestNeighbor`. Sparse rank features such as `bm25(title)` for example.

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.005,
        "summaryfetchtime": 0.003,
        "searchtime": 0.009000000000000001
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 100
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 8.72273659535481,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 22.591334631476823,
                        "closeness(field,embedding)": 1.0,
                        "distance(field,embedding)": 0.0,
                        "query(wVector)": 1.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/202014b34cdd67ac28585105",
                "relevance": 7.063803473430664,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 6.120690332283275,
                        "closeness(field,embedding)": 0.6469583978870177,
                        "distance(field,embedding)": 0.5456944422794805,
                        "query(wVector)": 1.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Loose Heart",
                    "artist": "Riverside"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

One can also do this the other way around, retrieve using the sparse representation, and have
Vespa calculate the `closeness(field, embedding)` or related rank features for the hits 
retrieved by the sparse query representation. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where rank(userQuery(),{targetHits:100}nearestNeighbor(embedding,q))' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")' 
</pre>
</div>

The `weakAnd` query operator exposes more hits to ranking than approximate nearest neighbor search, similar
to the `wand` query operator. Generally, using the `rank` query operator is more efficient than combining
query retriever operators using `or`. See also the 
[Vespa passage ranking](https://github.com/vespa-engine/sample-apps/blob/master/msmarco-ranking/passage-ranking-README.md)
for complete examples of different retrieval strategies for multi-phase ranking funnels.

One can also use the `rank` operator to first retrieve by some logic, and then compute distance for the retrieved documents.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title, popularity, artist from track where rank(popularity>99,{targetHits:100}nearestNeighbor(embedding,q))' \
    'hits=2' \
    'ranking=closeness' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")' 
</pre>
</div>

## Multiple nearest neighbor search operators in the same query 
This section looks at how to use multiple `nearestNeighbor` query operator instances in the same Vespa query request. 
The following Vespa query combines two `nearestNeighbor` query operators 
using logical disjunction (`OR`) and referencing two different
query tensor inputs:

- `input.query(q)` holding the *Total Eclipse Of The Heart* query vector.
- `input.query(q1)` holding the *Summer of '69* query vector.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title from track where ({targetHits:10}nearestNeighbor(embedding,q)) or ({targetHits:10}nearestNeighbor(embedding,q1))' \
    'hits=2' \
    'ranking=closeness' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'  \
    'input.query(q1)=embed(e5, "Summer of 69")'  
</pre>
</div>

The query exposes 20 hits to first phase ranking, as seen from `totalCount`. Ten from each nearest neighbor query operator:
<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.004,
        "summaryfetchtime": 0.002,
        "searchtime": 0.007
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 20
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
                "id": "index:tracks/0/5b1c2ae1024d88451c2f1c5a",
                "relevance": 1.0,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.0
                    },
                    "title": "Summer of 69"
                }
            },
            {
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 1.0,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart"
                }
            }
        ]
    }
}

{% endhighlight %}</pre>

One can also use the `label` annotation when there are multiple `nearestNeighbor` operators in the same query
to get the distance or closeness per query vector. Notice we use the `closeness-label` rank-profile.

<pre>
rank-profile closeness-label inherits closeness {
    match-features: closeness(label, q) closeness(label, q1)
}
</pre>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title from track where ({ label:"q", targetHits:10}nearestNeighbor(embedding,q)) or ({label:"q1",targetHits:10}nearestNeighbor(embedding,q1))' \
    'hits=2' \
    'ranking=closeness-label' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'  \
    'input.query(q1)=embed(e5, "Summer of 69")'  
</pre>
</div>

The above query annotates the two `nearestNeighbor` query operators using 
[label](reference/query-language-reference.html#label) query annotation. 

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.004,
        "summaryfetchtime": 0.0,
        "searchtime": 0.005
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 20
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
                "id": "index:tracks/0/5b1c2ae1024d88451c2f1c5a",
                "relevance": 1.0,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "closeness(label,q)": 0.6039000433424319,
                        "closeness(label,q1)": 1.0
                    },
                    "title": "Summer of 69"
                }
            },
            {
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 1.0,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "closeness(label,q)": 1.0,
                        "closeness(label,q1)": 0.6039000433424319
                    },
                    "title": "Total Eclipse Of The Heart"
                }
            }
        ]
    }
}{% endhighlight %}</pre>

Note that the previous examples used `or` to combine the two operators. Using `and` instead, requires 
that there are documents that is in both the top-k results. Increasing `targetHits` to 500,  
finds 5 tracks that overlap. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Dolorous Stroke'>
$ vespa query \
    'yql=select title from track where ({label:"q", targetHits:500}nearestNeighbor(embedding,q)) and ({label:"q1",targetHits:500}nearestNeighbor(embedding,q1))' \
    'hits=2' \
    'ranking=closeness-label' \
    'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'  \
    'input.query(q1)=embed(e5, "Summer of 69")' 
</pre>
</div>

Which returns the following top two hits. Note that the `closeness-label` rank profile
uses `closeness(field, embedding)` which in the case of multiple nearest neighbor search operators 
uses the maximum score to represent the unlabeled `closeness(field,embedding)`. This
can be seen from the `relevance` value, compared with the labeled `closeness()` rank features. 

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.008,
        "summaryfetchtime": 0.0,
        "searchtime": 0.009000000000000001
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 5
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
                "id": "index:tracks/0/439ca5f008b2b72704704b65",
                "relevance": 0.6442831379812195,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "closeness(label,q)": 0.6442831379812195,
                        "closeness(label,q1)": 0.6212453963738567
                    },
                    "title": "Dolorous Stroke"
                }
            },
            {
                "id": "index:tracks/0/698485b7a93ddeb7574670ec",
                "relevance": 0.6401157063988596,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "closeness(label,q)": 0.6401157063988596,
                        "closeness(label,q1)": 0.6324869732783777
                    },
                    "title": "Fever of the Time"
                }
            }
        ]
    }
}{% endhighlight %}</pre>

Vespa also supports having multiple document side embedding fields, which also
can be searched using multiple `nearestNeighbor` operators in the query.

<pre>
field embedding type tensor&lt;float&gt;(x[384]) {
    indexing: attribute | index
    attribute {
        distance-metric: euclidean
    }
    index {
        hnsw {
            max-links-per-node: 16
            neighbors-to-explore-at-insert: 50
        }
    }
 }
 field embedding_two tensor&lt;float&gt;(x[768]) {
    indexing: attribute | index
    attribute {
        distance-metric: euclidean
    }
    index {
        hnsw {
            max-links-per-node: 16
            neighbors-to-explore-at-insert: 50
        }
    }
 }
</pre>

## Controlling filter behavior

Vespa allows developers to control how filters are combined with nearestNeighbor query operator, see
[Query Time Constrained Approximate Nearest Neighbor Search](https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/) 
for a detailed description of *pre-filtering* and *post-filtering* strategies. 
The following query examples explore the two query-time parameters
which can be used to control the filtering behavior. The parameters are

- [ranking.matching.postFilterThreshold](reference/query-api-reference.html#ranking.matching) default 1.0 
- [ranking.matching.approximateThreshold](reference/query-api-reference.html#ranking.matching) default 0.05

These parameters can be used per query or configured in the rank-profile in the 
[document schema](reference/schema-reference.html#post-filter-threshold). 

The following query runs with the default setting for *ranking.matching.postFilterThreshold* which is 1, which means, 
do not perform post-filtering, use *pre-filtering* strategy:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 10'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:10}nearestNeighbor(embedding,q) and tags contains "rock"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=1.0' \
  'ranking.matching.approximateThreshold=0.05' \
  'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'  
</pre>
</div>

The query exposes `targetHits` to ranking as seen from the `totalCount`. Now, repeating the query, but
forcing *post-filtering* instead by setting *ranking.matching.postFilterThreshold=0.0*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:10}nearestNeighbor(embedding,q) and tags contains "rock"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=0.0' \
  'ranking.matching.approximateThreshold=0.05' \
  'input.query(q)=embed(e5, "Total Eclipse Of The Heart")' 
</pre>
</div>

In this case, Vespa will estimate how many documents the filter matches and auto-adjust `targethits` internally to a
higher number, attempting to expose the `targetHits` to first phase ranking:

The query exposes 16 documents to ranking as can be seen from `totalCount`. There are `8420` documents in the collection
that are tagged with the `rock` tag, so roughly 8%. 

Auto adjusting `targetHits` upwards for postFiltering is not always what you want, because it is slower than just retrieving
uconstrained, and post filter the hits that does not satifies the filters. We can adjust the 
`targetHits` adjustement factor with the [ranking.matching.targetHitsMaxAdjustmentFactor](reference/query-api-reference.html#ranking.matching) parameter.
In this case, we set it to 1, which effectively disables adjusting the `targetHits` upwards. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='totalCount": 1'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:10}nearestNeighbor(embedding,q) and tags contains "rock"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=0.0' \
  'ranking.matching.approximateThreshold=0.05' \
  'ranking.matching.targetHitsMaxAdjustmentFactor=1' \
  'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>
Since we are post-filtering without upward adjusting the targetHits, we end up with just one hit. 


Changing to a tag which is less frequent, for example, `90s`, which
matches 1,695 documents or roughly 1.7% will cause Vespa to fall back to exact search as the estimated filter hit count
is less than the `approximateThreshold`. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Bonnie Tyler'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:10}nearestNeighbor(embedding,q) and tags contains "90s"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=0.0' \
  'ranking.matching.approximateThreshold=0.05' \
  'input.query(q)=embed(e5, "Total Eclipse Of The Heart")'
</pre>
</div>

The exact search exposes more documents to ranking. Read more about combining filters with nearest neighbor search in the 
[Query Time Constrained Approximate Nearest Neighbor Search](https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/) 
blog post. 

## Tear down the container
This concludes this tutorial. 
The following removes the container and the data:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="after">
$ docker rm -f vespa
</pre>
</div>

<script src="/js/process_pre.js"></script>
