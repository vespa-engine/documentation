---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa nearest neighbor search - a practical guide"
---

 This guide is a practical introduction to using Vespa nearest neighbor search query operator and how to combine nearest
 neighbor search with other Vespa query operators. The guide also covers
 diverse, efficient candidate retrievers which can be used as candidate retrievers in a multi-phase ranking funnel. 

 The guide uses the [Last.fm](http://millionsongdataset.com/lastfm/) tracks dataset for illustration. 
 Latency numbers mentioned in the guide are obtained from running this guide on a MacBook Pro x86.
 See also the the generic [Vespa performance - a practical guide](performance/practical-search-performance-guide.html).

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

## Prerequisites
These are the prerequisites for reproducing the steps in this performance guide:

* [Docker](https://www.docker.com/) Desktop installed and running.
* Operating system: Linux, macOS or Windows 10 Pro (Docker requirement)
* Architecture: x86_64
* Minimum **6 GB** memory dedicated to Docker (the default is 2 GB on Macs).
  Refer to [Docker memory](https://docs.vespa.ai/en/operations/docker-containers.html#memory)
  for details and troubleshooting
* [Homebrew](https://brew.sh/) to install [Vespa CLI](https://docs.vespa.ai/en/vespa-cli.html), or download
  a vespa cli release from [Github releases](https://github.com/vespa-engine/vespa/releases).
* Python3 for converting the dataset to Vespa json. 
* `curl` to download the dataset and `zstd` to decompress published embedding data. 

## Installing vespa-cli 

This tutorial uses [Vespa-CLI](https://docs.vespa.ai/en/vespa-cli.html), 
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
[the Vespa JSON format](reference/document-json-format.html). 

This [python](https://www.python.org/) script can be used to traverse 
the dataset files and create a JSONL formatted feed file with Vespa put operations. 
The schema used with this feed format is introduced in the next section. 
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
{% endhighlight %}</pre>

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
Create directories for the configuration files:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir -p app/schemas
</pre>
</div>

### Schema

A [schema](schemas.html) is a configuration of a document type and what we should compute over it.
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
            attribute: fast-search
        }

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

        field popularity type int {
            indexing: summary | attribute
            attribute: fast-search
            rank: filter
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
        inputs {
           query(q) tensor&lt;float&gt;(x[384])
           query(qa) tensor&lt;float&gt;(x[384])
        }
        num-threads-per-search: 1
        match-features: distance(field, embedding)
        first-phase {
            expression: closeness(field, embedding)
        }
    }

    rank-profile closeness-t4 inherits closeness {
        num-threads-per-search: 4
    }

    rank-profile closeness-label inherits closeness {
        match-features: closeness(label, q) closeness(label, qa)
    }

    rank-profile hybrid inherits closeness {
        num-threads-per-search: 1
        rank-properties {
            query(wTags):1
            query(wPopularity):1
            query(wTitle):1
            query(wVector): 1
        }
        first-phase {
            expression {
                query(wTags) * rawScore(tags) + 
                query(wPopularity) * attribute(popularity) + 
                query(wTitle) * bm25(title) + 
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

This schema is explained in the [practical search performance guide](performance/practical-search-performance-guide.html),
the addition is the `embedding` field and the various `closeness` rank profiles. Note
that the `closeness` schema defines the query tensor inputs which needs to be declared to be
used with Vespa's nearestNeighbor query operator. 

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

The default query profile can be used to override
default query api settings for all queries.

The following enables [presentation.timing](reference/query-api-reference.html#presentation.timing) and
renders weightedset fields as a JSON map. 

<pre data-test="file" data-path="app/search/query-profiles/default.xml">
&lt;query-profile id=&quot;default&quot;&gt;
    &lt;field name=&quot;presentation.timing&quot;&gt;true&lt;/field&gt;
    &lt;field name=&quot;renderer.json.jsonWsets&quot;&gt;true&lt;/field&gt;
&lt;/query-profile&gt;
</pre>

## Deploy the application package

The application package can now be deployed to a running Vespa instance.
See also the [Vespa quick start guide](vespa-quick-start.html).

Start the Vespa container image using Docker:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker run -m 6G --detach --name vespa --hostname vespa-container \
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

Feed the dataset:

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

## Free text search using Vespa weakAnd 
The following sections uses the Vespa [query api](reference/query-api-reference.html) and 
formulate queries using Vespa [query language](query-language.html). The examples uses the
[vespa-cli](vespa-cli.html) command which supports running queries.

The CLI uses the Vespa http search api. Use `vespa query -v` to see the actual http request sent:

<pre>
$ vespa query -v 'yql=select ..'
</pre>

The first example is searching and ranking using the `bm25` rank profile defined in the
schema. It uses the [bm25](reference/bm25.html) rank feature as the `first-phase` relevance
score:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select artist, title, track_id from track where userQuery()' \
    'query=total eclipse of the heart' \
    'hits=1' \
    'ranking=bm25'
</pre>
</div>

This query combines YQL [userQuery()](reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](reference/simple-query-language-reference.html).
The default [query type](reference/query-api-reference.html#model.type) is
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

Now, the query matches 24,053 documents and is considerably slower than than the previous query. 
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
performing a maxium inner product search over the `tags` weightedset field. 

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
The query asks for 2 hits to be returned, and uses the `tags` ranking profile. 
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
uses the `rawScore(tag)` rank-feature directly, hence the `relevancy` is the 
result of the sparse dot product between the sparse user profile and the document tags. 

The `wand` query operator is safe, meaning, it returns the same top-k results as 
the brute-force `dotProduct` query operator. `wand` is a type of query operator which
performs matching and ranking interleaved and skipping documents
which cannot compete into the final top-k results. 
See the [using wand with Vespa](using-wand-with-vespa.html) guide for more details on 
using `wand` and `weakAnd` query operators. 

## Exact nearest neighbor search
Vespa's nearest neighbor search operator supports doing exact brute force nearest neighbor search
using dense representations. This guide uses
the [sentence-transformers/all-MiniLM-L6-V2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
embedding model. Download the pre-generated document embeddings and feed them to Vespa. 
The feed file uses [partial updates](partial-updates.html) to add the vector embedding. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o lastfm_embeddings.jsonl.zst \
    https://data.vespa.oath.cloud/sample-apps-data/lastfm_embeddings.jsonl.zst
$ zstdcat lastfm_embeddings.jsonl.zst | ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --stdin --endpoint http://localhost:8080
</pre>
</div>

The following query examples use a static query vector embedding for the
query string *Total Eclipse Of The Heart*. The query embedding was obtained by the
following snippet using [sentence-transformers](https://www.sbert.net/):

<pre>{% highlight python%}
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(model.encode("Total Eclipse Of The Heart").tolist())
{% endhighlight %}</pre>

<pre data-test="exec">
$ export Q='[-0.008,0.085,0.05,-0.009,-0.038,-0.003,0.019,-0.085,0.123,-0.11,0.029,-0.032,-0.059,-0.005,-0.022,0.031,0.007,0.003,0.006,0.041,-0.094,-0.044,-0.004,0.045,-0.016,0.101,-0.029,-0.028,-0.044,-0.012,0.025,-0.011,0.016,0.031,-0.037,-0.027,0.007,0.026,-0.028,0.049,-0.041,-0.041,-0.018,0.033,0.034,-0.01,-0.038,-0.052,0.02,0.029,-0.029,-0.043,-0.143,-0.055,0.052,-0.021,-0.012,-0.058,0.017,-0.017,0.023,0.017,-0.074,0.067,-0.043,-0.065,-0.028,0.066,-0.048,0.034,0.026,-0.034,0.085,-0.082,-0.043,0.054,-0.0,-0.075,-0.012,-0.056,0.027,-0.027,-0.088,0.01,0.01,0.071,0.007,0.022,-0.032,0.068,-0.003,-0.109,-0.005,0.07,-0.017,0.006,-0.007,-0.034,-0.062,0.096,0.038,0.038,-0.031,-0.023,0.064,-0.046,0.055,-0.011,0.016,-0.016,-0.007,-0.083,0.061,-0.037,0.04,0.099,0.063,0.032,0.019,0.099,0.105,-0.046,0.084,0.041,-0.088,-0.015,-0.002,-0.0,0.045,0.02,0.109,0.031,0.02,0.012,-0.043,0.034,-0.053,-0.023,-0.073,-0.052,-0.006,0.004,-0.018,-0.033,-0.067,0.126,0.018,-0.006,-0.03,-0.044,-0.085,-0.043,-0.051,0.057,0.048,0.042,-0.013,0.041,-0.017,-0.039,0.06,0.015,-0.031,0.043,-0.049,0.008,-0.008,0.028,-0.014,0.035,-0.08,-0.052,0.017,0.02,0.059,0.049,0.048,0.033,0.024,0.009,0.021,-0.042,-0.021,0.048,0.015,0.042,-0.004,-0.012,0.041,0.053,0.015,-0.034,-0.005,0.068,-0.053,-0.107,-0.051,0.03,-0.063,-0.036,0.032,-0.054,0.085,0.022,0.08,0.054,-0.045,-0.058,-0.161,0.066,0.065,-0.043,0.084,0.043,-0.01,-0.01,-0.084,-0.021,0.041,0.026,-0.011,-0.065,-0.046,0.0,-0.046,-0.014,-0.009,-0.08,0.063,0.02,-0.082,0.088,0.046,0.058,0.005,-0.024,0.047,0.019,0.051,-0.021,0.02,-0.003,-0.019,0.08,0.031,0.021,0.041,-0.01,-0.018,0.07,0.076,-0.021,0.027,-0.086,0.059,-0.068,-0.126,0.025,-0.037,0.036,-0.028,0.035,-0.068,0.005,-0.032,0.023,0.012,0.074,0.028,-0.02,0.054,0.124,0.022,-0.021,-0.099,-0.044,-0.044,0.093,0.004,-0.006,-0.037,0.034,-0.021,-0.046,-0.031,-0.034,0.015,-0.041,0.001,0.022,0.015,0.02,-0.16,0.065,-0.016,0.059,-0.249,0.023,0.031,0.047,0.063,-0.06,-0.002,-0.049,-0.06,-0.014,0.013,0.004,0.019,-0.039,0.007,0.024,-0.004,0.045,-0.026,0.078,-0.014,-0.038,0.003,-0.0,0.019,0.04,-0.017,-0.088,-0.04,-0.029,0.05,0.012,-0.042,0.052,0.035,0.061,0.011,0.03,-0.068,0.015,0.032,-0.028,-0.046,-0.032,0.094,0.006,0.082,-0.103,0.013,-0.054,0.038,0.01,0.029,-0.025,0.119,0.034,0.024,-0.034,-0.055,-0.014,0.026,0.068,-0.009,0.085,0.028,-0.086,0.038,0.01,-0.024,0.01,0.071,-0.078,-0.033,-0.024,0.023,-0.005,-0.002,-0.047,0.031,0.023,0.004,0.069,-0.018,0.034,0.109,0.036,0.009,0.029]'
</pre>

The first query example uses [exact nearest neighbor search](nearest-neighbor-search.html): 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select title, artist from track where {approximate:false,targetHits:10}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness' \
    "ranking.features.query(q)=$Q"
</pre>
</div>

Query breakdown:

- Search for 10 (`targetHits:10`) nearest neighbors of the `query(q)` query tensor over the `embedding`
document tensor field. 
- The annotation `approximate:false` tells Vespa to perform exact search.
- The `hits` parameter controls how many results are returned in the response. Number of `hits`
requested does not impact `targetHits`. Notice that `targetHits` is per content node involved in the query. 
- `ranking=closeness` tells Vespa which [rank-profile](ranking.html) to score documents. One must 
specify how to *rank* the `targetHits` documents retrieved and exposed to `first-phase` rank expression
in the `rank-profile`.
Not specifying [ranking](reference/query-api-reference.html#ranking.profile) will cause
Vespa to use [nativeRank](nativerank.html) which does not use the vector similarity, causing
results to be randomly sorted. 

The above exact nearest neighbor search will return the following
[result](reference/default-result-format.html):

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.051,
        "summaryfetchtime": 0.001,
        "searchtime": 0.051
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 118
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
                "relevance": 0.5992897741908119,
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
The exact search takes approximately 51ms, performing 95,666 distance calculations. 
A total of about 120 documents were exposed to the first-phase ranking during the search as can be seen from
`totalCount`. Vespa's exact nearest neighbor search uses chunked vector distance calculations.
Splitting the vectors into chunks reduces the computational complexity.

It is possible to reduce search latency of the exact search by throwing more CPU resources at it. 
Changing the rank-profile to `closeness-t4` makes Vespa use four threads per query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Bonnie Tyler">
$ vespa query \
    'yql=select title, artist from track where {approximate:false,targetHits:10}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q"
</pre>
</div>

Now, the exact search latency is reduced by using more threads, 
see [multi-threaded searching and ranking](performance/practical-search-performance-guide.html#multi-threaded-search-and-ranking)
for more on this topic.
<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.019,
        "summaryfetchtime": 0.001,
        "searchtime": 0.021
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
    'yql=select title, artist from track where {targetHits:10}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness' \
    "ranking.features.query(q)=$Q"
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

Now, the query is significantly faster, and also uses less resources during the search. To get latency down 
to 20 ms with the exact search one had to use 4 matching threads. In this case the
result latency is down to 4ms with a single matching thread. 
For this query example, the approximate search returned the exact same top-1 hit and there was
no accuracy loss for the top-1 position. 

A few key differences between `exact` and `approximate` neighbor search:

- `totalCount` is different, when using the approximate version, Vespa exposes exactly `targethits` to the 
configurable `first-phase` rank expression in the chosen `rank-profile`.
 The exact search is using a scoring heap during chunked distance calculations, and documents which at some time
were put on the top-k heap are exposed to first phase ranking.
- The search is approximate and might not return the exact top 10 closest vectors as with exact search. This
is a complex tradeoff between accuracy, query performance , and memory usage. 
See [Billion-scale vector search with Vespa - part two](https://blog.vespa.ai/billion-scale-knn-part-two/)
for a deep-dive into these trade-offs.

With the support for setting `approximate:false|true` a developer can quantify accuracy loss by comparing the 
results of exact nearest neighbor search with the results of the approximate search. 
By doing so, developers can quantify the recall@k or overlap@k, 
and find the right balance between search performance and accuracy. 

## Combining approximate nearest neighbor search with query filters
Vespa allows combining the search for nearest neighbors to be constrained by regular query filters. 
In this query example the `title` field must contain the term `heart`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Heart Of My Heart">
$ vespa query \
    'yql=select title, artist from track where {targetHits:10}nearestNeighbor(embedding,q) and title contains "heart"' \
    'hits=2' \
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q"
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
            "totalCount": 55
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
                "relevance": 0.5992897741908119,
                "source": "tracks",
                "fields": {
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/cb79ca7f404071e95561ca38",
                "relevance": 0.5259774715154759,
                "source": "tracks",
                "fields": {
                    "title": "Heart Of My Heart",
                    "artist": "Quest"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

When using filtering, it is important for performance reasons that the fields that are included in the filters have
been defined with `index` or `attribute:fast-search`.
See [searching attribute fields](performance/practical-search-performance-guide.html#searching-attribute-fields).

The optimal performance for pure filtering, where the query term(s) does not influence ranking, is achieved
using `rank: filter` in the schema.

<pre>
field popularity type int {
    indexing: summary | attribute
    rank: filter
    attribute: fast-search
}
</pre>
Matching against the popularity field does not influence ranking and Vespa can use the most efficient posting
list representation. Note that one can still access the value of
the attribute in ranking expressions. 

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
<pre data-test="exec" data-test-assert-contains="Heart Of My Heart">
$ vespa query \
    'yql=select title, artist from track where {targetHits:10}nearestNeighbor(embedding,q) and title contains ({ranked:false}"heart")' \
    'hits=2' \
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q"
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
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q"
</pre>
</div>

In this case restricting the nearest neighbor search to tracks by `Bonnie Tyler` with `popularity > 20`.

### Strict filters and distant neighbors 
When combining nearest neighbor search with strict filters which matches less than 5 percentage of the total number of documents, 
Vespa will instead of searching the HNSW graph, constrained by the filter, fall back to using exact nearest neighbor search. When
falling back to exact search users will observe that `totalCount` increases and is higher than `targetHits`.
As seen from previous examples, more hits are exposed to the `first-phase` ranking expression when using 
exact search. When using exact search with filters, the search can also use multiple threads to evaluate the query, which
helps reducing the latency impact. 

With strict filters that removes many hits, the hits (nearest neighbors) might not be *near* in the embedding space, but *far*,
or *distant* neighbors. Technically, all document vectors are a neighbor of the query, 
but with a varying distance, some are close, others are distant.

With strict filters, the neighbors that are returned might be of low quality (far distance). 
One way to combat this is to use the [distanceThreshold](reference/query-language-reference.html#distancethreshold)
query annotation parameter of the `nearestNeighbor` query operator. 
The value of the `distance` depends on the [distance-metric](reference/schema-reference.html#distance-metric) used. 
By adding the [distance(field,embedding)](reference/rank-features.html#distance(dimension,name)) rank-feature to
the `match-features` of the `closeness` rank-profiles, it is possible to analyze what distance 
could be consider too far. 
See [match-features reference](reference/schema-reference.html#match-features).


Note that distance of 0 is perfect, while distance of 1 is distant. The `distanceThreshold` 
remove hits that have a **higher** `distance(field, embedding)` than `distanceThreshold`. The
`distanceThreshold` is applied regardless of performing exact or approximate search. 

The following query with a restrictive filter on popularity is used for illustration:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select matchfeatures, title, popularity, artist from track where {targetHits:10}nearestNeighbor(embedding,q) and popularity > 80' \
    'hits=2' \
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q"
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
                "id": "index:tracks/0/3517728cc88356c8ca6de0d9",
                "relevance": 0.5005276509131764,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "distance(field,embedding)": 0.9978916213231626
                    },
                    "title": "Closer To The Heart",
                    "artist": "Rush",
                    "popularity": 100
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

By using a `distanceTreshold` of 0.7,  the `Closer To The Heart` track will be removed from the result
because it's `distance(field, embedding)` is close to 1. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query \
    'yql=select matchfeatures, title, popularity, artist from track where {distanceThreshold:0.7,targetHits:10}nearestNeighbor(embedding,q) and popularity > 80' \
    'hits=2' \
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q"
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
The post processing searcher can analyze the score distributions of the returned top-k hits
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
<pre data-test="exec" data-test-assert-contains='matchfeatures'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where {targetHits:100}nearestNeighbor(embedding,q) or userQuery()' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    "ranking.features.query(q)=$Q"
</pre>
</div>

The query combines the sparse `weakAnd` and the dense `nearestNeighbor` query operators 
using logical disjunction. 
Both query operator retrievers the target number of hits (or more) ranked by it's inner 
raw score/distance. The list of documents exposed to the configurable ranking expression is a combination
of the best of these two different retrieval strategies. 
The ranking is performed using the following`hybrid` rank profile which serves as an example
how to combine the different scoring techniques. 

<pre>
rank-profile hybrid {
        num-threads-per-search: 1
        rank-properties {
            query(wTags):1
            query(wPopularity):1
            query(wTitle):1
            query(wVector): 1
        }
        first-phase {
            expression {
                query(wTags) * rawScore(tags) + 
                query(wPopularity) * attribute(popularity) + 
                query(wTitle) * bm25(title) + 
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
        "querytime": 0.007,
        "summaryfetchtime": 0.001,
        "searchtime": 0.009000000000000001
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1176
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
                "relevance": 123.18970542319387,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 22.590415639472816,
                        "closeness(field,embedding)": 0.5992897837210658,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/57c74bd2d466b7cafe30c14d",
                "relevance": 112.03224663886917,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 12.032246638869161,
                        "closeness(field,embedding)": 0.0,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Eclipse",
                    "artist": "Kyoto Jazz Massive"
                }
            }
        ]
    }
{% endhighlight %}</pre>

The result hits also include [match-features](reference/schema-reference.html#match-features) which 
can be used for feature logging for [learning to rank](learning-to-rank.html), or to simply
debug the final score. 

In the below query, the `weight` of the embedding similarity (closeness) is increased by overriding
the `query(wVector)` weight:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='matchfeatures'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where {targetHits:100}nearestNeighbor(embedding,q) or userQuery()' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    "ranking.features.query(q)=$Q" \
    'ranking.features.query(wVector)=40'
</pre>
</div>

Which changes the order and a different hit is surfaced at position two:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.011,
        "summaryfetchtime": 0.001,
        "searchtime": 0.014
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1176
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
                "relevance": 146.56200698831543,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 22.590415639472816,
                        "closeness(field,embedding)": 0.5992897837210658,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/3517728cc88356c8ca6de0d9",
                "relevance": 126.74309103465859,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 6.7219852584615865,
                        "closeness(field,embedding)": 0.5005276444049249,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Closer To The Heart",
                    "artist": "Rush"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

One can also throw the personalization component using the sparse
user profile into the retriever mix. For example having a user profile:

<pre>
userProfile={"love songs":1, "love":1,"80s":1}
</pre>
Which can be used with the `wand` query operator:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Change My Love For You'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where {targetHits:100}nearestNeighbor(embedding,q) or userQuery() or ({targetHits:10}wand(tags, @userProfile))' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    "ranking.features.query(q)=$Q" \
    'ranking.features.query(wVector)=340' \
    'userProfile={"love songs":1, "love":1,"80s":1}' 
</pre>
</div>

In this case, another document is surfaced at position 2, which have a non-zero personalized score.
Notice that `totalCount` increases as the `wand` query operator brought more hits into `first-phase` ranking.

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.014,
        "summaryfetchtime": 0.001,
        "searchtime": 0.017
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 1244
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
                "relevance": 326.34894210463517,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 22.590415639472816,
                        "closeness(field,embedding)": 0.5992897837210658,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/8eb2e19ee627b054113ba4c9",
                "relevance": 281.0,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 0.0,
                        "closeness(field,embedding)": 0.0,
                        "rawScore(tags)": 181.0
                    },
                    "title": "Nothing's Gonna Change My Love For You",
                    "artist": "Glenn Medeiros"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

In the examples above, some of the hits had 
<pre>
"closeness(field,embedding)": 0.0
</pre>
This means that the hit was not retrieved by the `nearestNeighbor` operator, similar `rawScore(tags)` might
also be 0 if the hit was not retrieved by the `wand` query operator. 

It is nevertheless possible to calculate the semantic distance/similarity using 
[tensor computations](tensor-examples.html) for the hits that were not retrieved by the `nearestNeighbor`
query operator. See also [tensor functions](reference/ranking-expressions.html#tensor-functions). 
For example to compute the `euclidean` distance one can add a 
[function](reference/schema-reference.html#function-rank) to the rank-profile:

<pre>
rank-profile compute-also-for-sparse {
    function euclidean() {
        expression: sqrt(sum(map(query(q) - attribute(embedding), f(x)(x * x))))
    }
    function match_closeness() {
        expression: 1/(1 + euclidean())
    }
    first-phase {
        expression {
         bm25(title) + 
         if(closeness(field, embedding) == 0, match_closeness(), closeness(field, embedding))
        }
    }
}
</pre>

Changing from logical `OR` to `AND` instead will intersect the result of the two efficient retrievers.
The search for nearest neighbors is then constrained to documents which at least matches one of
the query terms in the `weakAnd`.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Closer To The Heart'>
$ vespa query \
    'yql=select title, matchfeatures, artist from track where {targetHits:100}nearestNeighbor(embedding,q) and userQuery()' \
    'query=total eclipse of the heart' \
    'type=weakAnd' \
    'hits=2' \
    'ranking=hybrid' \
    "ranking.features.query(q)=$Q" \
    'ranking.features.query(wVector)=340'
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
    "ranking.features.query(q)=$Q" \
    'ranking.features.query(wVector)=340' 
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
    "ranking.features.query(q)=$Q" \
    'ranking.features.query(wVector)=340' 
</pre>
</div>

This query returns 100 documents, since only the first operand of the `rank` query operator was used for 
*retrieval*, the sparse `userQuery()` representation was only used to calculate sparse 
[rank features](reference/rank-features.html) for
the results retrieved by the `nearestNeighbor`. Sparse rank features such as `bm25(title)` for example.

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.01,
        "summaryfetchtime": 0.002,
        "searchtime": 0.015
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
                "relevance": 326.34896241725517,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 22.590435952092836,
                        "closeness(field,embedding)": 0.5992897837210658,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart",
                    "artist": "Bonnie Tyler"
                }
            },
            {
                "id": "index:tracks/0/3517728cc88356c8ca6de0d9",
                "relevance": 276.90138973270746,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "attribute(popularity)": 100.0,
                        "bm25(title)": 6.721990635032981,
                        "closeness(field,embedding)": 0.5005276444049249,
                        "rawScore(tags)": 0.0
                    },
                    "title": "Closer To The Heart",
                    "artist": "Rush"
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
    "ranking.features.query(q)=$Q" \
    'ranking.features.query(wVector)=340' 
</pre>
</div>

The `weakAnd` query operator exposes more hits to ranking than approximate nearest neighbor search, similar
to the `wand` query operator. Generally, using the `rank` query operator is more efficient than combining
query retriever operators using `or`. See also the 
[Vespa passage ranking](https://github.com/vespa-engine/sample-apps/blob/master/msmarco-ranking/passage-ranking.md)
for complete examples of different retrieval strategies for multi-phase ranking funnels.

## Multiple nearest neighbor search operators in the same query 
This section looks at how to use multiple `nearestNeighbor` query operator instances in the same Vespa query request. 

First, the query embedding for *Total Eclipse Of The Heart*:

<pre>{% highlight python%}
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(model.encode("Total Eclipse Of The Heart").tolist())
{% endhighlight %}</pre>

<pre data-test="exec">
$ export Q='[-0.008,0.085,0.05,-0.009,-0.038,-0.003,0.019,-0.085,0.123,-0.11,0.029,-0.032,-0.059,-0.005,-0.022,0.031,0.007,0.003,0.006,0.041,-0.094,-0.044,-0.004,0.045,-0.016,0.101,-0.029,-0.028,-0.044,-0.012,0.025,-0.011,0.016,0.031,-0.037,-0.027,0.007,0.026,-0.028,0.049,-0.041,-0.041,-0.018,0.033,0.034,-0.01,-0.038,-0.052,0.02,0.029,-0.029,-0.043,-0.143,-0.055,0.052,-0.021,-0.012,-0.058,0.017,-0.017,0.023,0.017,-0.074,0.067,-0.043,-0.065,-0.028,0.066,-0.048,0.034,0.026,-0.034,0.085,-0.082,-0.043,0.054,-0.0,-0.075,-0.012,-0.056,0.027,-0.027,-0.088,0.01,0.01,0.071,0.007,0.022,-0.032,0.068,-0.003,-0.109,-0.005,0.07,-0.017,0.006,-0.007,-0.034,-0.062,0.096,0.038,0.038,-0.031,-0.023,0.064,-0.046,0.055,-0.011,0.016,-0.016,-0.007,-0.083,0.061,-0.037,0.04,0.099,0.063,0.032,0.019,0.099,0.105,-0.046,0.084,0.041,-0.088,-0.015,-0.002,-0.0,0.045,0.02,0.109,0.031,0.02,0.012,-0.043,0.034,-0.053,-0.023,-0.073,-0.052,-0.006,0.004,-0.018,-0.033,-0.067,0.126,0.018,-0.006,-0.03,-0.044,-0.085,-0.043,-0.051,0.057,0.048,0.042,-0.013,0.041,-0.017,-0.039,0.06,0.015,-0.031,0.043,-0.049,0.008,-0.008,0.028,-0.014,0.035,-0.08,-0.052,0.017,0.02,0.059,0.049,0.048,0.033,0.024,0.009,0.021,-0.042,-0.021,0.048,0.015,0.042,-0.004,-0.012,0.041,0.053,0.015,-0.034,-0.005,0.068,-0.053,-0.107,-0.051,0.03,-0.063,-0.036,0.032,-0.054,0.085,0.022,0.08,0.054,-0.045,-0.058,-0.161,0.066,0.065,-0.043,0.084,0.043,-0.01,-0.01,-0.084,-0.021,0.041,0.026,-0.011,-0.065,-0.046,0.0,-0.046,-0.014,-0.009,-0.08,0.063,0.02,-0.082,0.088,0.046,0.058,0.005,-0.024,0.047,0.019,0.051,-0.021,0.02,-0.003,-0.019,0.08,0.031,0.021,0.041,-0.01,-0.018,0.07,0.076,-0.021,0.027,-0.086,0.059,-0.068,-0.126,0.025,-0.037,0.036,-0.028,0.035,-0.068,0.005,-0.032,0.023,0.012,0.074,0.028,-0.02,0.054,0.124,0.022,-0.021,-0.099,-0.044,-0.044,0.093,0.004,-0.006,-0.037,0.034,-0.021,-0.046,-0.031,-0.034,0.015,-0.041,0.001,0.022,0.015,0.02,-0.16,0.065,-0.016,0.059,-0.249,0.023,0.031,0.047,0.063,-0.06,-0.002,-0.049,-0.06,-0.014,0.013,0.004,0.019,-0.039,0.007,0.024,-0.004,0.045,-0.026,0.078,-0.014,-0.038,0.003,-0.0,0.019,0.04,-0.017,-0.088,-0.04,-0.029,0.05,0.012,-0.042,0.052,0.035,0.061,0.011,0.03,-0.068,0.015,0.032,-0.028,-0.046,-0.032,0.094,0.006,0.082,-0.103,0.013,-0.054,0.038,0.01,0.029,-0.025,0.119,0.034,0.024,-0.034,-0.055,-0.014,0.026,0.068,-0.009,0.085,0.028,-0.086,0.038,0.01,-0.024,0.01,0.071,-0.078,-0.033,-0.024,0.023,-0.005,-0.002,-0.047,0.031,0.023,0.004,0.069,-0.018,0.034,0.109,0.036,0.009,0.029]'
</pre>

Secondly, the query embedding for *Summer of '69*:
<pre>{% highlight python%}
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(model.encode("Summer of '69").tolist())
{% endhighlight %}</pre>


<pre data-test="exec">
$ export QA='[-0.043,0.027,-0.017,0.018,0.034,0.067,0.037,-0.046,-0.014,-0.114,0.033,-0.028,0.02,0.024,0.025,0.019,0.045,0.007,0.018,-0.035,-0.126,0.024,0.005,0.05,-0.005,0.048,0.059,0.07,-0.041,0.006,-0.008,0.113,-0.046,-0.007,0.065,-0.02,-0.007,-0.067,-0.099,0.069,-0.068,-0.013,0.054,0.029,-0.031,-0.018,0.036,-0.015,0.027,0.011,0.04,0.038,-0.046,-0.025,-0.042,0.028,-0.006,-0.091,0.033,-0.016,-0.079,-0.058,-0.044,-0.022,0.086,-0.107,0.002,-0.037,-0.058,-0.039,-0.028,0.037,-0.015,0.035,0.0,0.072,-0.021,-0.01,0.044,-0.094,0.116,-0.109,-0.04,0.01,0.012,-0.031,0.087,0.005,-0.035,0.049,-0.088,-0.02,-0.023,-0.01,-0.063,-0.018,-0.024,-0.05,-0.009,0.115,0.049,0.017,-0.05,0.017,0.084,-0.053,0.051,0.033,-0.001,-0.087,-0.031,-0.019,0.132,0.006,0.056,-0.117,0.043,0.01,-0.03,0.176,0.055,0.042,0.051,0.025,-0.041,-0.027,0.041,-0.0,0.01,-0.016,0.048,-0.031,0.103,-0.044,-0.003,-0.005,-0.029,-0.032,-0.046,-0.095,-0.074,-0.094,0.111,-0.042,0.004,0.048,0.006,0.042,-0.092,0.109,0.016,-0.04,-0.01,0.033,-0.034,0.049,0.03,0.02,0.04,0.015,0.007,0.03,0.018,0.017,-0.029,-0.082,0.015,0.002,-0.048,0.047,-0.03,-0.029,-0.008,0.088,0.04,0.023,0.052,-0.034,0.006,0.003,-0.048,-0.094,-0.014,-0.086,-0.052,-0.01,0.062,-0.03,0.062,0.058,-0.027,-0.04,-0.084,-0.061,0.09,-0.049,-0.032,0.007,-0.071,-0.052,0.055,-0.064,0.041,-0.008,0.076,-0.018,-0.025,-0.034,0.016,-0.007,0.041,0.023,-0.021,-0.046,0.01,-0.022,-0.019,-0.027,-0.039,-0.037,0.014,0.004,0.017,0.0,0.034,0.003,0.015,-0.019,0.02,0.025,-0.05,0.056,-0.047,-0.088,0.004,-0.116,0.07,-0.057,0.032,0.006,-0.021,0.09,-0.02,0.035,-0.114,-0.006,-0.01,-0.005,0.025,-0.046,0.054,-0.002,-0.003,0.028,-0.025,0.001,-0.003,0.09,-0.084,0.058,0.091,-0.025,-0.034,-0.032,0.026,-0.032,0.054,0.039,0.033,-0.029,0.015,0.076,-0.054,0.021,-0.069,-0.049,-0.051,-0.006,0.002,-0.058,-0.021,-0.011,0.025,-0.003,-0.001,-0.018,-0.064,-0.023,-0.013,0.029,-0.022,0.023,-0.019,-0.028,-0.072,-0.044,-0.082,0.074,0.086,-0.016,0.041,0.004,-0.047,-0.029,-0.137,0.005,-0.075,0.136,0.054,0.024,0.052,0.01,0.024,-0.038,0.078,0.005,0.013,-0.034,-0.051,-0.0,0.03,-0.007,0.025,-0.042,0.065,0.02,0.05,0.045,0.004,0.095,0.044,0.044,0.091,0.024,0.0,0.022,0.027,0.011,-0.011,0.009,-0.056,-0.026,0.173,-0.019,0.024,-0.014,-0.064,0.079,0.083,-0.033,0.051,-0.005,-0.056,-0.043,-0.061,-0.034,0.112,0.072,0.042,-0.047,0.055,0.058,0.015,0.017,0.015,0.083,0.024,-0.023,-0.024,0.007,0.043,0.042,0.025,0.011,0.042,-0.032,-0.044,0.021,-0.064,-0.065,0.078,0.051,-0.028,-0.136]'
</pre>

The following Vespa query combines two `nearestNeighbor` query operators 
using logical disjunction (`OR`) and referencing two different
query tensor inputs:

- `ranking.features.query(q)` holding the *Total Eclipse Of The Heart* query vector.
- `ranking.features.query(qa)` holding the *Summer of '69* query vector.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title from track where ({targetHits:10}nearestNeighbor(embedding,q)) or ({targetHits:10}nearestNeighbor(embedding,qa))' \
    'hits=2' \
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q" \
    "ranking.features.query(qa)=$QA" 
</pre>
</div>

The above query returns 20 documents to first phase ranking, as seen from `totalCount`. Ten from each nearest neighbor query operator:
<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.007,
        "summaryfetchtime": 0.001,
        "searchtime": 0.01
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 0.5992897917249415,
                "source": "tracks",
                "fields": {
                    "title": "Total Eclipse Of The Heart"
                }
            },
            {
                "id": "index:tracks/0/5b1c2ae1024d88451c2f1c5a",
                "relevance": 0.5794361034642413,
                "source": "tracks",
                "fields": {
                    "title": "Summer of 69"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

One can also use the `label` annotation when there are multiple `nearestNeighbor` operators in the same query
to differentiate which of them produced the match. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Total Eclipse Of The Heart'>
$ vespa query \
    'yql=select title, matchfeatures from track where ({ label:"q", targetHits:10}nearestNeighbor(embedding,q)) or ({label:"qa",targetHits:10}nearestNeighbor(embedding,qa))' \
    'hits=2' \
    'ranking=closeness-label' \
    "ranking.features.query(q)=$Q" \
    "ranking.features.query(qa)=$QA" 
</pre>
</div>

The above query annotates the two `nearestNeighbor` query operators using 
[label](reference/query-language-reference.html#label) query annotation. The result include 
`match-features` so one can see which query operator retrieved the document from the 
`closeness(label, ..)` feature output:

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.011,
        "summaryfetchtime": 0.001,
        "searchtime": 0.014
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
                "id": "index:tracks/0/f13697952a0d5eaeb2c43ffc",
                "relevance": 0.5992897917249415,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "closeness(label,q)": 0.5992897917249415,
                        "closeness(label,qa)": 0.0
                    },
                    "title": "Total Eclipse Of The Heart"
                }
            },
            {
                "id": "index:tracks/0/5b1c2ae1024d88451c2f1c5a",
                "relevance": 0.5794361034642413,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "closeness(label,q)": 0.0,
                        "closeness(label,qa)": 0.5794361034642413
                    },
                    "title": "Summer of 69"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

Note that the previous examples used `or` to combine the two operators. Using `and` instead, requires 
that there are documents that is in both the top-k results. Increasing `targetHits` to 500,  
finds 9 tracks that overlap. In this case both closeness labels have a non-zero score. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Summer Of Love'>
$ vespa query \
    'yql=select title, matchfeatures from track where ({label:"q", targetHits:500}nearestNeighbor(embedding,q)) and ({label:"qa",targetHits:500}nearestNeighbor(embedding,qa))' \
    'hits=2' \
    'ranking=closeness-label' \
    "ranking.features.query(q)=$Q" \
    "ranking.features.query(qa)=$QA" 
</pre>
</div>

Which returns the following top two hits. Note that the `closeness-label` rank profile
uses `closeness(field, embedding)` which in the case of multiple nearest neighbor search operators 
uses the maximum score to represent the unlabeled `closeness(field,embedding)`. This
can be seen from the `relevance` value, compared with the labeled `closeness()` rank features. 

<pre>{% highlight json%}
{
    "timing": {
        "querytime": 0.015,
        "summaryfetchtime": 0.001,
        "searchtime": 0.017
    },
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 9
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
                "id": "index:tracks/0/99a2a380cac4830bfee63ae0",
                "relevance": 0.5174298300948759,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "closeness(label,q)": 0.4755796429687308,
                        "closeness(label,qa)": 0.5174298300948759
                    },
                    "title": "Summer Of Love"
                }
            },
            {
                "id": "index:tracks/0/a373d26938a20dbdda8fc7c1",
                "relevance": 0.5099393361432658,
                "source": "tracks",
                "fields": {
                    "matchfeatures": {
                        "closeness(label,q)": 0.5099393361432658,
                        "closeness(label,qa)": 0.47990179066646654
                    },
                    "title": "Midnight Heartache"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

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
Vespa allows developers to control how filters are combined with nearestNeighbor query operator, please 
[https://blog.vespa.ai/constrained-approximate-nearest-neighbor-search/] for a detailed description
of *pre-filtering* and *post-filtering*. 

The following runs with the default setting for *ranking.matching.postFilterThreshold* which is 1, which means, 
do not perform post-filtering, use *pre-filtering*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 10'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:10}nearestNeighbor(embedding,q) and tags contains "rock"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=1.0' \
  'ranking.matching.approximateThreshold=0.05' \
  "ranking.features.query(q)=$Q"
</pre>
</div>
The query exposes *targetHits* to ranking as seen from the `totalCount`. Now, repeating the query, but using
*post-filtering* instead by setting *ranking.matching.postFilterThreshold=0.0*:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 2'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:10}nearestNeighbor(embedding,q) and tags contains "rock"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=0.0' \
  'ranking.matching.approximateThreshold=0.05' \
  "ranking.features.query(q)=$Q"
</pre>
</div>

In this case, Vespa first finds the `targethits` closest hits by searching the HNSW graph, and then performs post filtering, 
which for this query exposes only two documents to ranking (`totalCount=2`) which is less than the wanted `targetHits`. 
It is possible to increase `targetHits` to try to combat this, the following query increases the `targethits` by 10x to 100:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 12'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:100}nearestNeighbor(embedding,q) and tags contains "rock"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=0.0' \
  'ranking.matching.approximateThreshold=0.05' \
  "ranking.features.query(q)=$Q"
</pre>
</div>

The query exposes 12 documents to ranking as can be seen from `totalCount`. There is `8420` documents in the collection
which is tagged with the `rock` tag, so roughly 8%. Changing to a tag which is less frequent, for example, `90s`, which
matches 1695 documents or roughly 1.7%, only exposes one document to ranking.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:10}nearestNeighbor(embedding,q) and tags contains "90s"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=0.0' \
  'ranking.matching.approximateThreshold=0.00' \
  "ranking.features.query(q)=$Q"
</pre>
</div>

Increasing targetHits to 100 finds another valid document

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 2'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:100}nearestNeighbor(embedding,q) and tags contains "90s"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=0.0' \
  'ranking.matching.approximateThreshold=0.00' \
  "ranking.features.query(q)=$Q"
</pre>
</div>

The above query examples cheated a bit, as *ranking.matching.approximateThreshold* was set to 0, which caused Vespa to not fall back
to exact nearest neighbor search for very restrictive filters. 
Changing back to *ranking.matching.approximateThreshold=5.00* and the restrictive filter 
causes Vespa to fallback to exact search because the filter is estimated
to match less than the threshold. (2% &lt; 5%):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 364'>
$ vespa query \
  'yql=select title, artist, tags from track where {targetHits:100}nearestNeighbor(embedding,q) and tags contains "90s"' \
  'hits=2' \
  'ranking=closeness' \
  'ranking.matching.postFilterThreshold=0.0' \
  'ranking.matching.approximateThreshold=0.05' \
  "ranking.features.query(q)=$Q"
</pre>
</div>

The exact search exposes more documents to ranking and the query returns `364` hits. 

## Tear down the container
This concludes this tutorial. 
The following removes the container and the data:
<pre data-test="after">
$ docker rm -f vespa
</pre>

<script src="/js/process_pre.js"></script>
