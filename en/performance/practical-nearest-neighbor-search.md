---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa nearest neighbor search - a practical guide"
---

 This is a practical guide to using Vespa nearest neighbor search query operator and how to combine nearest
 neighbor search, or dense retrieval with other Vespa query operators. The guide also covers
 diverse efficient candidate retrievers which can be used in a multi-phase ranking funnel. 

 The guide uses the [Last.fm](http://millionsongdataset.com/lastfm/) tracks dataset to illustrate Vespa query performance. 
 Latency numbers mentioned in the guide are obtained from running this guide on a MacBook Pro x86.  
 See also the the generic [Vespa performance - a practical guide](practical-search-performance-guide.html).

This guide covers the following:

- [Free text search using Vespa weakAnd](#free-text-search-using-vespa-weakand)
- [Sparse maximum inner product search using Vespa wand](#maximum-inner-product-search-using-vespa-wand)
- [Brute-force exact nearest neighbor search](#brute-force-exact-nearest-neighbor-search)
- [Approximate nearest neighbor search](#approximate-nearest-neighbor-search)
- [Combining approximate nearest neighbor search with filters](#combining-approximate-nearest-neighbor-search-with-query-filters)
- [Hybrid sparse and dense retrieval methods with Vespa](#hybrid-sparse-and-dense-retrieval-methods-with-vespa)

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

This small [python](https://www.python.org/) script can be used to traverse 
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

<pre>
{% highlight python%}
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
{% endhighlight %}
</pre>

Process the dataset and convert it to a Vespa
JSON document operation format. See [Vespa document json format](../reference/document-json-format.html).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ python3 create-vespa-feed.py lastfm_test > feed.jsonl
</pre>
</div>

## Create a Vespa Application Package
A [Vespa application package](../cloudconfig/application-packages.html) is the set 
of configuration files and Java plugins that together define the behavior of a Vespa system:
what functionality to use, the available document types, how ranking will be done,
and how data will be processed during feeding and indexing.

The minimum required files to create the basic search application are `track.sd` and `services.xml`.
Create directories for the configuration files:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir -p app/schemas; mkdir -p app/search/query-profiles/types
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
        first-phase {
            expression: closeness(field, embedding)
        }
    }

    rank-profile closeness-t4 inherits closeness {
        num-threads-per-search: 4
    }

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

To query with the [nearestNeighbor](../reference/query-language-reference.html#nearestneighbor)
query operator the input query tensor type must be defined:

<pre data-test="file" data-path="app/search/query-profiles/types/root.xml">
&lt;query-profile-type id=&quot;root&quot; inherits=&quot;native&quot;&gt;   
    &lt;field name=&quot;ranking.features.query(q)&quot; type=&quot;tensor&amp;lt;float&amp;gt;(x[384])&quot; /&gt;
&lt;/query-profile-type&gt;
</pre>

Note that the query tensor's dimensionality (*384*) and dimension name (*x*) 
must match the document tensor. 

The tensor type must be reference in the the `default` [queryProfile](../query-profiles.html), 
it also enables [timing](../reference/query-api-reference.html#presentation.timing).

<pre data-test="file" data-path="app/search/query-profiles/default.xml">
&lt;query-profile id=&quot;default&quot; type=&quot;root&quot;&gt;
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
The following sections uses the Vespa [query api](../reference/query-api-reference.html) and 
formulate queries using Vespa [query language](../query-language.html). The examples uses the
[vespa-cli](../vespa-cli.html) command which supports running queries.

The CLI uses the Vespa http search api. Use `vespa query -v` to see the actual http request sent:

<pre>
$ vespa query -v 'yql=select ..'
</pre>

The first example is searching and ranking using the `bm25` rank profile defined in the
schema, it uses the [bm25](../reference/bm25.html) rank feature as the `first-phase` relevance
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

This query combines YQL [userQuery()](../reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](../reference/simple-query-language-reference.html), the 
default [query type](../reference/query-api-reference.html#model.type) is 
using `all` requiring that all the terms match. 

The above example searches for *total AND eclipse AND of AND the AND heart* in the `default` fieldset, 
which in the schema includes the track `title` and `artist` fields. 

The result output for the above query will look something like this:

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
{% endhighlight %}
</pre>

This query only matched one document because the query terms were ANDed. 
We can change matching to use `type=any` instead of the default `type=all`. See 
[supported query types](../reference/query-api-reference.html#model.type).

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
See the [using wand with Vespa](../using-wand-with-vespa.html) guide for more details. 

Run the same query, but instead of `type=any` use `type=weakAnd`, 
see [supported query types](../reference/query-api-reference.html#model.type)

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

The previous section introduced the `weakAnd` query operator which integrates with linguistic processing and 
string matching using `match: text`.  

The following examples uses the
[wand()](../reference/query-language-reference.html#wand) query operator. The `wand` query operator
calculates the maximum inner product search between the sparse query and document feature integer
weights. The inner product ranking score can be used in a ranking expression using 
the [rawScore(name)](../reference/rank-features.html#match-operator-scores). 

<pre>
rank-profile tags {
    first-phase {
        expression: rawScore(tags)
    }
}
</pre>

This query searches using a pre-defined *userProfile* input with weights, this could be used
to serve personalized search results:

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


<pre>
{% highlight json%}
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

{% endhighlight %}
</pre>
The *wand* query operator exposed a total of about 60 documents to the first phase ranking which 
used the `rawScore` rank-feature directly, hence the `relevancy` is the 
result of the sparse dot product.

The `wand` query operator is safe, meaning, it returns the same top-k results as 
the brute-force `dotProduct` query operator. *wand* is a type of query operator which
performs matching and ranking interleaved and skipping documents
which cannot compete into the top-k results. 
See the [using wand with Vespa](../using-wand-with-vespa.html) guide for more details. 

## Brute-force exact nearest neighbor search
Vespa's nearest neighbor search operator supports doing exact brute force nearest neighbor search
using dense representations. This guide uses
the [sentence-transformers/all-MiniLM-L6-V2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
embedding model. Download the pre-generated document embeddings and feed them to Vespa. 
The feed file uses [partial updates](../partial-updates.html) to add the vector embedding. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o lastfm_embeddings.jsonl.zst \
    https://data.vespa.oath.cloud/sample-apps-data/lastfm_embeddings.jsonl.zst
$ zstdcat lastfm_embeddings.jsonl.zst | ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --stdin --endpoint http://localhost:8080
</pre>
</div>

Throughout the nearest neighbor search examples a pre-generated query vector embedding is used. The
query encoding is obtained using the following python snippet:

<pre>
{% highlight python%}
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(model.encode("Total Eclipse Of The Heart").tolist())
{% endhighlight %}
</pre>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ export Q="[-0.008065593428909779, 0.08453001081943512, 0.05018267780542374, -0.00884118303656578, -0.03753741458058357, -0.002897844184190035, 0.018800711259245872, -0.08455602824687958, 0.12270907312631607, -0.11035755276679993, 0.02900831587612629, -0.03181139752268791, -0.059499651193618774, -0.005452691577374935, -0.021512603387236595, 0.03091139905154705, 0.007443971000611782, 0.0033167325891554356, 0.006025344133377075, 0.0407075360417366, -0.09435737133026123, -0.043547291308641434, -0.003722529858350754, 0.04549279063940048, -0.01646103896200657, 0.10117562115192413, -0.028849618509411812, -0.02792065404355526, -0.04440610110759735, -0.012309690937399864, 0.02463461086153984, -0.010905942879617214, 0.016348496079444885, 0.03120623156428337, -0.03689209371805191, -0.026606908068060875, 0.007187394890934229, 0.026255015283823013, -0.027878889814019203, 0.04887397959828377, -0.040938086807727814, -0.04059148579835892, -0.018180137500166893, 0.03347662836313248, 0.034363873302936554, -0.009773473255336285, -0.03761803358793259, -0.05165955796837807, 0.02030535228550434, 0.029069935902953148, -0.029270710423588753, -0.04302166402339935, -0.14273975789546967, -0.054517582058906555, 0.05221065133810043, -0.021013369783759117, -0.011579306796193123, -0.05847478657960892, 0.017305167391896248, -0.01687753014266491, 0.02265619859099388, 0.016990581527352333, -0.07423004508018494, 0.0670929029583931, -0.043099191039800644, -0.06476132571697235, -0.02833601087331772, 0.06560441106557846, -0.04813879355788231, 0.034389808773994446, 0.025906093418598175, -0.03387472406029701, 0.08512983471155167, -0.08200040459632874, -0.043198585510253906, 0.05377274006605148, -1.3492515790858306e-05, -0.07457280158996582, -0.011894909664988518, -0.056003738194704056, 0.02744675986468792, -0.02683129347860813, -0.08751800656318665, 0.009949575178325176, 0.009947385638952255, 0.07105473428964615, 0.006816620007157326, 0.02214016579091549, -0.03223466873168945, 0.06848280131816864, -0.002865268150344491, -0.10906799882650375, -0.004794569220393896, 0.0700574591755867, -0.017358610406517982, 0.005850719287991524, -0.007386602461338043, -0.03422526270151138, -0.06186102703213692, 0.09635236859321594, 0.03765295445919037, 0.03840741887688637, -0.031325798481702805, -0.022597692906856537, 0.06412969529628754, -0.04569492116570473, 0.05510227382183075, -0.011190789751708508, 0.016163261607289314, -0.01587338000535965, -0.006616983097046614, -0.08257699012756348, 0.061467889696359634, -0.036905497312545776, 0.0396663062274456, 0.09937333315610886, 0.0628795400261879, 0.031959712505340576, 0.018774161115288734, 0.09851669520139694, 0.10548844188451767, -0.04587824270129204, 0.08409712463617325, 0.0408954881131649, -0.08757888525724411, -0.015198812820017338, -0.0015260233776643872, -4.5127051803914994e-33, 0.04512721300125122, 0.02022739127278328, 0.10873544216156006, 0.031336165964603424, 0.020439941436052322, 0.01180290151387453, -0.04260794073343277, 0.034157123416662216, -0.0530574694275856, -0.02271156944334507, -0.07331117987632751, -0.051517896354198456, -0.006412195973098278, 0.004073905758559704, -0.01808927021920681, -0.03291923180222511, -0.06715051829814911, 0.1264735609292984, 0.01830722764134407, -0.006467769853770733, -0.02958807535469532, -0.04435303434729576, -0.08525101095438004, -0.0426446832716465, -0.05052332580089569, 0.056784987449645996, 0.04760073125362396, 0.04232100024819374, -0.012680839747190475, 0.04057534411549568, -0.016715282574295998, -0.038503557443618774, 0.05970745533704758, 0.015299498103559017, -0.030979091301560402, 0.04322757199406624, -0.04851067438721657, 0.007697853725403547, -0.00765706691890955, 0.028058459982275963, -0.013527121394872665, 0.03533558547496796, -0.08002450317144394, -0.05159372836351395, 0.016727318987250328, 0.020383279770612717, 0.058962564915418625, 0.04943905025720596, 0.0484146922826767, 0.03329985961318016, 0.024137509986758232, 0.00945933535695076, 0.02096088044345379, -0.042136695235967636, -0.020796949043869972, 0.048218026757240295, 0.014527356252074242, 0.04205385595560074, -0.0037270491011440754, -0.012404494918882847, 0.0406918004155159, 0.052811697125434875, 0.014659274369478226, -0.0343233197927475, -0.004552842583507299, 0.06838028877973557, -0.05307793244719505, -0.1066446378827095, -0.05113332346081734, 0.029849926009774208, -0.06266053766012192, -0.03584916889667511, 0.03204002231359482, -0.05363399535417557, 0.08498287945985794, 0.022012196481227875, 0.07978614419698715, 0.05392017215490341, -0.04454052820801735, -0.05780909210443497, -0.16149619221687317, 0.06632131338119507, 0.06512226164340973, -0.04338205233216286, 0.08380760252475739, 0.043481167405843735, -0.00976069737225771, -0.010386576876044273, -0.08425439894199371, -0.020755212754011154, 0.04098920896649361, 0.025638438761234283, -0.011476637795567513, -0.0652712807059288, -0.0458490215241909, 3.3561006564449414e-33, -0.045877546072006226, -0.014327161014080048, -0.00889583770185709, -0.07991943508386612, 0.06335989385843277, 0.020355327054858208, -0.08159274607896805, 0.08775875717401505, 0.04613940790295601, 0.058199282735586166, 0.004947203677147627, -0.024214154109358788, 0.04702865704894066, 0.018762843683362007, 0.05060647055506706, -0.020737560465931892, 0.020449569448828697, -0.00315210223197937, -0.019496789202094078, 0.08003784716129303, 0.030812574550509453, 0.021192725747823715, 0.04074690118432045, -0.010161326266825199, -0.01750219613313675, 0.07027928531169891, 0.07621443271636963, -0.021291153505444527, 0.02731945924460888, -0.08593399077653885, 0.05897112935781479, -0.06813547760248184, -0.12615789473056793, 0.024827904999256134, -0.036509256809949875, 0.03583522513508797, -0.028349364176392555, 0.03544466942548752, -0.06820773333311081, 0.004819205962121487, -0.031920406967401505, 0.02264106273651123, 0.012271669693291187, 0.07367941737174988, 0.02805280312895775, -0.019734136760234833, 0.05411006510257721, 0.1244635060429573, 0.02204885520040989, -0.020645083859562874, -0.09927894175052643, -0.04384636506438255, -0.044096820056438446, 0.09273523837327957, 0.0036650339607149363, -0.00589165510609746, -0.03742601349949837, 0.03430400416254997, -0.021355658769607544, -0.046258632093667984, -0.03139067813754082, -0.03371819108724594, 0.015043865889310837, -0.040960583835840225, 0.0005861789686605334, 0.022100983187556267, 0.014802497811615467, 0.01974347233772278, -0.15989500284194946, 0.06509614735841751, -0.016112778335809708, 0.059294622391462326, -0.24891476333141327, 0.023260807618498802, 0.030897853896021843, 0.04748426005244255, 0.06302175670862198, -0.060118284076452255, -0.0019891539122909307, -0.04915579780936241, -0.05969022586941719, -0.014428123831748962, 0.012632399797439575, 0.004207937978208065, 0.019165141507983208, -0.039342571049928665, 0.006500255316495895, 0.024150803685188293, -0.004393275361508131, 0.0450282096862793, -0.02574659138917923, 0.07830891013145447, -0.01446054968982935, -0.03755667433142662, 0.0028512096032500267, -1.3547870381103166e-08, 0.019127607345581055, 0.039926059544086456, -0.017314990982413292, -0.0884983018040657, -0.03971191495656967, -0.02919849194586277, 0.05020134150981903, 0.012144864536821842, -0.042309850454330444, 0.05202021449804306, 0.035093676298856735, 0.06074520945549011, 0.011429301463067532, 0.030419116839766502, -0.06799472123384476, 0.014796014875173569, 0.03248818218708038, -0.02767939120531082, -0.045667778700590134, -0.032344453036785126, 0.09448641538619995, 0.006221190560609102, 0.08226171135902405, -0.10274671763181686, 0.012639115564525127, -0.053681086748838425, 0.037539899349212646, 0.010317509062588215, 0.028925608843564987, -0.025364894419908524, 0.11875864863395691, 0.03408011421561241, 0.02434944547712803, -0.034273095428943634, -0.05486215278506279, -0.013620521873235703, 0.025710809975862503, 0.06839863955974579, -0.008693386800587177, 0.08522018790245056, 0.027604777365922928, -0.08558861166238785, 0.03820370137691498, 0.009757391177117825, -0.023547468706965446, 0.010406864807009697, 0.07114516198635101, -0.07792956382036209, -0.033378396183252335, -0.02428746409714222, 0.02293989062309265, -0.004945156630128622, -0.001709840609692037, -0.04669877141714096, 0.031319715082645416, 0.022594738751649857, 0.004356659483164549, 0.069020576775074, -0.017948495224118233, 0.03409144654870033, 0.10871049016714096, 0.03606746718287468, 0.009485756978392601, 0.028754733502864838]"
</pre>
</div>

The first query example uses exact nearest neighbor search: 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Boonie Tyler">
$ vespa query \
    'yql=select title, artist from track where {approximate:false,targetHits:10}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness' \
    "ranking.features.query(q)=$Q"
</pre>
</div>

The query expresses the following :

- Search for 10 (`targetHits:10`) nearest neighbors of the `q` query tensor over the `embedding`
document tensor field. 
- The annotation `approximate:false` tells Vespa to perform exact search.
- The `hits` parameter controls how many results are returned in the response. 
- `ranking=closeness` tells Vespa which rank-profile to use. One must 
specify how to rank the `targetHits` documents retrieved and exposed to `first-phase` rank expression.

The above exact nearest neighbor search will return the following:

<pre>
{% highlight json%}
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
{% endhighlight %}  
</pre>
The exact search takes approximately 51ms, performing 95,666 distance calculations. 
A total of about 120 documents were exposed to the first-phase ranking during the search as can be seen from
`totalCount`.  

It is possible to reduce search latency of the exact search by throwing more cpu resources at it. 
Changing the rank-profile used with the search to `closeness-t4` uses four threads:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Boonie Tyler">
$ vespa query \
    'yql=select title, artist from track where {approximate:false,targetHits:10}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q"
</pre>
</div>

Now, the exact search latency is reduced by using more threads, 
see [multi-threaded searching and ranking](practical-search-performance-guide.html#multi-threaded-search-and-ranking).
<pre>
{% highlight json%}
{
    "timing": {
        "querytime": 0.019,
        "summaryfetchtime": 0.001,
        "searchtime": 0.021
    }
}  
{% endhighlight %}  
</pre>

## Approximate nearest neighbor search
This section covers using the faster, but approximate, nearest neighbor search. The 
`track` schema's `embedding` field has `index` enabled which means Vespa builds a 
`HNSW` index to support fast, approximate search.

The default query behavior is using `approximate:true` :

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec"  data-test-assert-contains="Boonie Tyler">
$ vespa query \
    'yql=select title, artist from track where {targetHits:10}nearestNeighbor(embedding,q)' \
    'hits=1' \
    'ranking=closeness' \
    "ranking.features.query(q)=$Q"
</pre>
</div>

Which returns the following response:

<pre>
{% highlight json%}
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
{% endhighlight %} 
</pre>

Now, the query is significantly faster, but also uses less resources during the search. To get latency down 
to 20 ms with the exact search one had to use 4 matching threads, in this case, the
result latency is down to 4ms with a single matching thread. 

In this case, the approximate search returned the exact same top-1 hit, so no accuracy loss compared
to the exact search.

A few key differences with approximate versus exact:

- `totalCount` is different, when using the approximate version, it exposes exactly `targethits` to the 
configurable `first-phase` rank expression. The exact search is using a scoring heap during scoring and documents which at some time
were put on the heap are exposed to first phase ranking.
- The search is approximate, it might not return the exact top 10 closest vectors as with exact search, this
is a complex tradeoff between accuracy, query performance , and memory usage. 

With the support for setting `approximate:false|true` a developer can quantify accuracy loss by comparing the 
k exact nearest neighbor search with the k returned by the approximate search. 
By doing so, developers can quantify the recall@k or overlap@k, and find the right balance between search performance and accuracy. 

## Combining approximate nearest neighbor search with query filters
Vespa allows combining the search for nearest neighbors to be constrained by regular query filters:


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
<pre>
{% highlight json%}
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
{% endhighlight %} 
</pre>

When using filtering, it is important for performance reasons that the fields that are included in the filters have
been defined with `index` or `attribute:fast-search`. 

The optimal performance for pure filtering (where the query term does not influence ranking) is achieved
using `rank: filter` in the schema. 

<pre>
field category type string {
    indexing: summary | attribute
    rank: filter
    attribute: fast-search
}
</pre>

Or 

<pre>
field category type string {
    indexing: summary | index
    rank: filter
}
</pre>

In this case, where searching in the `title` field which one can specify `ranked:false` for the query term, which
disables term ranking and the search can use the most efficient posting list representation which is a bit vector.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Heart Of My Heart">
$ vespa query \
    'yql=select title, artist from track where {targetHits:10}nearestNeighbor(embedding,q) and title contains ({"ranked":false}"heart")' \
    'hits=2' \
    'ranking=closeness-t4' \
    "ranking.features.query(q)=$Q"
</pre>
</div>

In these examples, since we did not change the rank profile, the matching would not impact the rank score anyway. 

The filter expression can be also complex using the full Vespa query language:

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

## Hybrid sparse and dense retrieval methods with Vespa
In the previous filtering examples the result ranking was not impacted by the filters, the filters were only used to impact recall, not the
order of the results. The following examples demonstrates how to perform hybrid retrieval combining the efficient query operators in 
a single query. 

The first example combines nearestNeighbor search with the `weakAnd` query operator, combining them using logical
disjunction (OR):

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

The query above uses both efficient retrievers to retrieve hits which are ranked using the ranking profile `hybrid`
which is defined as:

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
{% endhighlight %} 
</pre>
The result also include [match-features](../reference/schema-reference.html#match-features) which 
can be used for feature logging for [learning to rank](../learning-to-rank.html) or to simply
debug the final relevancy score. 

In the below query, the weight of the embedding score is increased:

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


<pre>
{% highlight json%}
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
{% endhighlight %} 
</pre>

One can also throw the personalization component using the sparse
user profile into the retriever mix using 

<pre>
userProfile={"love songs":1, "love":1,"80s":1}
<pre>

In combination with the wand query operator: 

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

<pre>
{% highlight json%}
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
{% endhighlight %} 
</pre>

In the examples above, some of the hits had 
<pre>
"closeness(field,embedding)": 0.0
</pre>
This means that the hit was not retrieved by the nearest neighbor search operator,similar rawScore(tags) might
also be 0 if a hit was not retrieved by the `wand` query operator. This is because of two things:

- The skipping query operator rank feature is only valid in the case where the hit was retrieved by the operator
- The query used logical disjunction to retrieve. 

Changing to `AND` instead:

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

In this case, the documents must be in the top 100 hits returned from the nearest neighbor search operator
and match at least one of the query terms. 

Finally, it is possible to combine hybrid search with filters:

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

In this case, `popularity` is not defined with `fast-search`, but since the data volume is so small 
it's not a problem, but for optimal performance make sure that fields that are used have either `index`
or `attribute` with `fast-search` and `rank: filter`. 

## Tear down the container
This concludes this tutorial. The following removes the container and the data:
<pre data-test="after">
$ docker rm -f vespa
</pre>

<script src="/js/process_pre.js"></script>
