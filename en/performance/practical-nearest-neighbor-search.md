---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa nearest neighbor search - a practical guide"
---

 This is a practical guide to using Vespa nearest neighbor search query operator and how to combine nearest
 neighbor search, or dense evalretri with other Vespa query operators. The guide also covers
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

<pre style="display:none" data-test="exec">
$ export A='[0.1]'
</pre>

<pre style="display:none" data-test="exec">
$ echo 'hello'
</pre>

<pre style="display:none" data-test="exec">
$ export Q='[-0.0080656, 0.08453, 0.0501827, -0.0088412, -0.0375374, -0.0028978, 0.0188007, -0.084556, 0.1227091, -0.1103576, 0.0290083, -0.0318114, -0.0594996, -0.0054527, -0.0215126, 0.0309114, 0.007444, 0.0033167, 0.0060253, 0.0407075, -0.0943574, -0.0435473, -0.0037225, 0.0454928, -0.016461, 0.1011756, -0.0288496, -0.0279207, -0.0444061, -0.0123097, 0.0246346, -0.0109059, 0.0163485, 0.0312062, -0.0368921, -0.0266069, 0.0071874, 0.026255, -0.0278789, 0.048874, -0.0409381, -0.0405915, -0.0181801, 0.0334766, 0.0343639, -0.0097735, -0.037618, -0.0516596, 0.0203054, 0.0290699, -0.0292707, -0.0430217, -0.1427398, -0.0545176, 0.0522107, -0.0210134, -0.0115793, -0.0584748, 0.0173052, -0.0168775, 0.0226562, 0.0169906, -0.07423, 0.0670929, -0.0430992, -0.0647613, -0.028336, 0.0656044, -0.0481388, 0.0343898, 0.0259061, -0.0338747, 0.0851298, -0.0820004, -0.0431986, 0.0537727, -1.35e-05, -0.0745728, -0.0118949, -0.0560037, 0.0274468, -0.0268313, -0.087518, 0.0099496, 0.0099474, 0.0710547, 0.0068166, 0.0221402, -0.0322347, 0.0684828, -0.0028653, -0.109068, -0.0047946, 0.0700575, -0.0173586, 0.0058507, -0.0073866, -0.0342253, -0.061861, 0.0963524, 0.037653, 0.0384074, -0.0313258, -0.0225977, 0.0641297, -0.0456949, 0.0551023, -0.0111908, 0.0161633, -0.0158734, -0.006617, -0.082577, 0.0614679, -0.0369055, 0.0396663, 0.0993733, 0.0628795, 0.0319597, 0.0187742, 0.0985167, 0.1054884, -0.0458782, 0.0840971, 0.0408955, -0.0875789, -0.0151988, -0.001526, -0.0, 0.0451272, 0.0202274, 0.1087354, 0.0313362, 0.0204399, 0.0118029, -0.0426079, 0.0341571, -0.0530575, -0.0227116, -0.0733112, -0.0515179, -0.0064122, 0.0040739, -0.0180893, -0.0329192, -0.0671505, 0.1264736, 0.0183072, -0.0064678, -0.0295881, -0.044353, -0.085251, -0.0426447, -0.0505233, 0.056785, 0.0476007, 0.042321, -0.0126808, 0.0405753, -0.0167153, -0.0385036, 0.0597075, 0.0152995, -0.0309791, 0.0432276, -0.0485107, 0.0076979, -0.0076571, 0.0280585, -0.0135271, 0.0353356, -0.0800245, -0.0515937, 0.0167273, 0.0203833, 0.0589626, 0.0494391, 0.0484147, 0.0332999, 0.0241375, 0.0094593, 0.0209609, -0.0421367, -0.0207969, 0.048218, 0.0145274, 0.0420539, -0.003727, -0.0124045, 0.0406918, 0.0528117, 0.0146593, -0.0343233, -0.0045528, 0.0683803, -0.0530779, -0.1066446, -0.0511333, 0.0298499, -0.0626605, -0.0358492, 0.03204, -0.053634, 0.0849829, 0.0220122, 0.0797861, 0.0539202, -0.0445405, -0.0578091, -0.1614962, 0.0663213, 0.0651223, -0.0433821, 0.0838076, 0.0434812, -0.0097607, -0.0103866, -0.0842544, -0.0207552, 0.0409892, 0.0256384, -0.0114766, -0.0652713, -0.045849, 0.0, -0.0458775, -0.0143272, -0.0088958, -0.0799194, 0.0633599, 0.0203553, -0.0815927, 0.0877588, 0.0461394, 0.0581993, 0.0049472, -0.0242142, 0.0470287, 0.0187628, 0.0506065, -0.0207376, 0.0204496, -0.0031521, -0.0194968, 0.0800378, 0.0308126, 0.0211927, 0.0407469, -0.0101613, -0.0175022, 0.0702793, 0.0762144, -0.0212912, 0.0273195, -0.085934, 0.0589711, -0.0681355, -0.1261579, 0.0248279, -0.0365093, 0.0358352, -0.0283494, 0.0354447, -0.0682077, 0.0048192, -0.0319204, 0.0226411, 0.0122717, 0.0736794, 0.0280528, -0.0197341, 0.0541101, 0.1244635, 0.0220489, -0.0206451, -0.0992789, -0.0438464, -0.0440968, 0.0927352, 0.003665, -0.0058917, -0.037426, 0.034304, -0.0213557, -0.0462586, -0.0313907, -0.0337182, 0.0150439, -0.0409606, 0.0005862, 0.022101, 0.0148025, 0.0197435, -0.159895, 0.0650961, -0.0161128, 0.0592946, -0.2489148, 0.0232608, 0.0308979, 0.0474843, 0.0630218, -0.0601183, -0.0019892, -0.0491558, -0.0596902, -0.0144281, 0.0126324, 0.0042079, 0.0191651, -0.0393426, 0.0065003, 0.0241508, -0.0043933, 0.0450282, -0.0257466, 0.0783089, -0.0144606, -0.0375567, 0.0028512, -0.0, 0.0191276, 0.0399261, -0.017315, -0.0884983, -0.0397119, -0.0291985, 0.0502013, 0.0121449, -0.0423099, 0.0520202, 0.0350937, 0.0607452, 0.0114293, 0.0304191, -0.0679947, 0.014796, 0.0324882, -0.0276794, -0.0456678, -0.0323445, 0.0944864, 0.0062212, 0.0822617, -0.1027467, 0.0126391, -0.0536811, 0.0375399, 0.0103175, 0.0289256, -0.0253649, 0.1187586, 0.0340801, 0.0243494, -0.0342731, -0.0548621, -0.0136205, 0.0257108, 0.0683986, -0.0086934, 0.0852202, 0.0276048, -0.0855886, 0.0382037, 0.0097574, -0.0235475, 0.0104069, 0.0711452, -0.0779296, -0.0333784, -0.0242875, 0.0229399, -0.0049452, -0.0017098, -0.0466988, 0.0313197, 0.0225947, 0.0043567, 0.0690206, -0.0179485, 0.0340914, 0.1087105, 0.0360675, 0.0094858, 0.0287547]'
</pre>

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

The previous section introduced the `weakAnd` query operator which integrates 
with [linguistic processing](../linguistics.html) and string matching using `match: text`.  

The following examples uses the
[wand()](../reference/query-language-reference.html#wand) query operator. 
The `wand` query operator calculates the maximum inner product search 
between the sparse query and document feature integer
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
The `wand` query operator exposed a total of about 60 documents to the first phase ranking which 
uses the `rawScore(tag)` rank-feature directly, hence the `relevancy` is the 
result of the sparse dot product between the user profile and the document tags. 

The `wand` query operator is safe, meaning, it returns the same top-k results as 
the brute-force `dotProduct` query operator. `wand` is a type of query operator which
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
query encoding is obtained using the following snippet:

<pre>
{% highlight python%}
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
print(model.encode("Total Eclipse Of The Heart").tolist())
{% endhighlight %}
</pre>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ export Q="[-0.0080656, 0.08453, 0.0501827, -0.0088412, -0.0375374, -0.0028978, 0.0188007, -0.084556, 0.1227091, -0.1103576, 0.0290083, -0.0318114, -0.0594996, -0.0054527, -0.0215126, 0.0309114, 0.007444, 0.0033167, 0.0060253, 0.0407075, -0.0943574, -0.0435473, -0.0037225, 0.0454928, -0.016461, 0.1011756, -0.0288496, -0.0279207, -0.0444061, -0.0123097, 0.0246346, -0.0109059, 0.0163485, 0.0312062, -0.0368921, -0.0266069, 0.0071874, 0.026255, -0.0278789, 0.048874, -0.0409381, -0.0405915, -0.0181801, 0.0334766, 0.0343639, -0.0097735, -0.037618, -0.0516596, 0.0203054, 0.0290699, -0.0292707, -0.0430217, -0.1427398, -0.0545176, 0.0522107, -0.0210134, -0.0115793, -0.0584748, 0.0173052, -0.0168775, 0.0226562, 0.0169906, -0.07423, 0.0670929, -0.0430992, -0.0647613, -0.028336, 0.0656044, -0.0481388, 0.0343898, 0.0259061, -0.0338747, 0.0851298, -0.0820004, -0.0431986, 0.0537727, -1.35e-05, -0.0745728, -0.0118949, -0.0560037, 0.0274468, -0.0268313, -0.087518, 0.0099496, 0.0099474, 0.0710547, 0.0068166, 0.0221402, -0.0322347, 0.0684828, -0.0028653, -0.109068, -0.0047946, 0.0700575, -0.0173586, 0.0058507, -0.0073866, -0.0342253, -0.061861, 0.0963524, 0.037653, 0.0384074, -0.0313258, -0.0225977, 0.0641297, -0.0456949, 0.0551023, -0.0111908, 0.0161633, -0.0158734, -0.006617, -0.082577, 0.0614679, -0.0369055, 0.0396663, 0.0993733, 0.0628795, 0.0319597, 0.0187742, 0.0985167, 0.1054884, -0.0458782, 0.0840971, 0.0408955, -0.0875789, -0.0151988, -0.001526, -0.0, 0.0451272, 0.0202274, 0.1087354, 0.0313362, 0.0204399, 0.0118029, -0.0426079, 0.0341571, -0.0530575, -0.0227116, -0.0733112, -0.0515179, -0.0064122, 0.0040739, -0.0180893, -0.0329192, -0.0671505, 0.1264736, 0.0183072, -0.0064678, -0.0295881, -0.044353, -0.085251, -0.0426447, -0.0505233, 0.056785, 0.0476007, 0.042321, -0.0126808, 0.0405753, -0.0167153, -0.0385036, 0.0597075, 0.0152995, -0.0309791, 0.0432276, -0.0485107, 0.0076979, -0.0076571, 0.0280585, -0.0135271, 0.0353356, -0.0800245, -0.0515937, 0.0167273, 0.0203833, 0.0589626, 0.0494391, 0.0484147, 0.0332999, 0.0241375, 0.0094593, 0.0209609, -0.0421367, -0.0207969, 0.048218, 0.0145274, 0.0420539, -0.003727, -0.0124045, 0.0406918, 0.0528117, 0.0146593, -0.0343233, -0.0045528, 0.0683803, -0.0530779, -0.1066446, -0.0511333, 0.0298499, -0.0626605, -0.0358492, 0.03204, -0.053634, 0.0849829, 0.0220122, 0.0797861, 0.0539202, -0.0445405, -0.0578091, -0.1614962, 0.0663213, 0.0651223, -0.0433821, 0.0838076, 0.0434812, -0.0097607, -0.0103866, -0.0842544, -0.0207552, 0.0409892, 0.0256384, -0.0114766, -0.0652713, -0.045849, 0.0, -0.0458775, -0.0143272, -0.0088958, -0.0799194, 0.0633599, 0.0203553, -0.0815927, 0.0877588, 0.0461394, 0.0581993, 0.0049472, -0.0242142, 0.0470287, 0.0187628, 0.0506065, -0.0207376, 0.0204496, -0.0031521, -0.0194968, 0.0800378, 0.0308126, 0.0211927, 0.0407469, -0.0101613, -0.0175022, 0.0702793, 0.0762144, -0.0212912, 0.0273195, -0.085934, 0.0589711, -0.0681355, -0.1261579, 0.0248279, -0.0365093, 0.0358352, -0.0283494, 0.0354447, -0.0682077, 0.0048192, -0.0319204, 0.0226411, 0.0122717, 0.0736794, 0.0280528, -0.0197341, 0.0541101, 0.1244635, 0.0220489, -0.0206451, -0.0992789, -0.0438464, -0.0440968, 0.0927352, 0.003665, -0.0058917, -0.037426, 0.034304, -0.0213557, -0.0462586, -0.0313907, -0.0337182, 0.0150439, -0.0409606, 0.0005862, 0.022101, 0.0148025, 0.0197435, -0.159895, 0.0650961, -0.0161128, 0.0592946, -0.2489148, 0.0232608, 0.0308979, 0.0474843, 0.0630218, -0.0601183, -0.0019892, -0.0491558, -0.0596902, -0.0144281, 0.0126324, 0.0042079, 0.0191651, -0.0393426, 0.0065003, 0.0241508, -0.0043933, 0.0450282, -0.0257466, 0.0783089, -0.0144606, -0.0375567, 0.0028512, -0.0, 0.0191276, 0.0399261, -0.017315, -0.0884983, -0.0397119, -0.0291985, 0.0502013, 0.0121449, -0.0423099, 0.0520202, 0.0350937, 0.0607452, 0.0114293, 0.0304191, -0.0679947, 0.014796, 0.0324882, -0.0276794, -0.0456678, -0.0323445, 0.0944864, 0.0062212, 0.0822617, -0.1027467, 0.0126391, -0.0536811, 0.0375399, 0.0103175, 0.0289256, -0.0253649, 0.1187586, 0.0340801, 0.0243494, -0.0342731, -0.0548621, -0.0136205, 0.0257108, 0.0683986, -0.0086934, 0.0852202, 0.0276048, -0.0855886, 0.0382037, 0.0097574, -0.0235475, 0.0104069, 0.0711452, -0.0779296, -0.0333784, -0.0242875, 0.0229399, -0.0049452, -0.0017098, -0.0466988, 0.0313197, 0.0225947, 0.0043567, 0.0690206, -0.0179485, 0.0340914, 0.1087105, 0.0360675, 0.0094858, 0.0287547]"
</pre>
</div>

The first query example uses [exact nearest neighbor search](../nearest-neighbor-search.html): 

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

The query expresses the following :

- Search for 10 (`targetHits:10`) nearest neighbors of the `q` query tensor over the `embedding`
document tensor field. 
- The annotation `approximate:false` tells Vespa to perform exact search.
- The `hits` parameter controls how many results are returned in the response. 
- `ranking=closeness` tells Vespa which rank-profile to use. One must 
specify how to *rank* the `targetHits` documents retrieved and exposed to `first-phase` rank expression.
Not specifying [ranking](..//reference/query-api-reference.html#ranking.profile) will cause
Vespa to use [nativeRank](../nativerank.html) which does not use the semantic similarity, causing
results to be randomly sorted. 

The above exact nearest neighbor search will return the following
[result](../reference/default-result-format.html):

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
`totalCount`.  Vespa's brute force nearest neighbor search uses chunked distance calculations, splitting
the vector into chunks - this way Vespa does not need to fully evaluate all distance calculations using
the complete representation. 

It is possible to reduce search latency of the exact search by throwing more CPU resources at it. 
Changing the rank-profile used with the search to `closeness-t4` makes Vespa use four threads:

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
`HNSW` index to support fast, approximate search. See 
[Approximate Nearest Neighbor Search using HNSW Index](../approximate-nn-hnsw.html).

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

In this case, the approximate search returned the exact same top-1 hit, so for this query, there was
no accuracy loss for the top-1 position. 

A few key differences with approximate versus exact search:

- `totalCount` is different, when using the approximate version, Vespa exposes exactly `targethits` to the 
configurable `first-phase` rank expression in the chosen `rank-profile`.
 The exact search is using a scoring heap during distance calculations, and documents which at some time
were put on the top-k heap are exposed to first phase ranking.
- The search is approximate, it might not return the exact top 10 closest vectors as with exact search, this
is a complex tradeoff between accuracy, query performance , and memory usage. 
See [Billion-scale vector search with Vespa - part two](https://blog.vespa.ai/billion-scale-knn-part-two/)
for a deep-dive into these trade-offs.

With the support for setting `approximate:false|true` a developer can quantify accuracy loss by comparing the 
results of exact nearest neighbor search with the results of the approximate search. 
By doing so, developers can quantify the recall@k or overlap@k, 
and find the right balance between search performance and accuracy. 

## Combining approximate nearest neighbor search with query filters
Vespa allows combining the search for nearest neighbors to be constrained by regular query filters. 
In this example the `title` must contain the term `heart`:

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
See [searching attribute fields](../practical-search-performance-guide.html#searching-attribute-fields).

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
using the [`ranked` query annotation](../reference/query-language-reference.html#ranked). 

The following disables term based ranking and 
the matching against the `title` field can use the most efficient 
posting list representation.

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

In the previous examples, since the rank-profile did only use the `closeness` rank feature,  
the matching would not impact the score anyway. 

Vespa also allow combining the `nearestNeighbor` query operator with any other Vespa query operator.  

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

## Hybrid sparse and dense retrieval methods with Vespa
In the previous filtering examples the ranking was not impacted by the filters, the filters were only used to impact recall, not the
order of the results. The following examples demonstrates how to perform hybrid retrieval combining the efficient query operators in 
a single query. Hybrid retrieval can be used as the first phase in a multi-phase ranking funnel, see 
[phased ranking](../phased-ranking.html).

The first example combines the `nearestNeighbor` operator with the `weakAnd` query operator, combining them using logical
disjunction (`OR`):

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

The query combines the `weakAnd` and `nearestNeighbor` query operator using logical disjunction. Both query operator retrievers
the target number of hits ranked by it's inner raw score/distance. The list of documents exposed to configurable ranking expression
is hence a combination of the best of two different strategies. The ranking is performed using the following
`hybrid` rank profile:

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

The result hits also include [match-features](../reference/schema-reference.html#match-features) which 
can be used for feature logging for [learning to rank](../learning-to-rank.html) or to simply
debug the final score. 

In the below query, the weight of the embedding similarity (closeness) is increased by overriding
the `query(wWector)` weight:

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
user profile into the retriever mix. For example having a user profile:

<pre>
userProfile={"love songs":1, "love":1,"80s":1}
</pre>

One can add the `wand` query operator using the sparse user profile representation to the retrieval mix:

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

In this case, another document is surfaced at position 2, which have a non-zero personalized score,
notice that `totalCount` increases as the `wand` query operator brought more hits into the mix.

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
This means that the hit was not retrieved by the nearest neighbor search operator, similar `rawScore(tags)` might
also be 0 if a hit was not retrieved by the `wand` query operator. This is because of two things:

- The skipping query operator rank feature is only valid in the case where the hit was retrieved by the operator
- The query used logical disjunction to retrieve hits into ranking. 

Changing from logical `OR` to `AND` instead will intersect the result of the sub retrievers, the
search for nearest neighbors is constrained to documents at least matching one query term. 

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
[rank()](../reference/query-language-reference.html#rank) query operator. 

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
*retrieval*, the sparse `userQuery()` representation was only use to calculate sparse rank features for
the results retrieved by the nearest neighbor search. 

<pre>
{% highlight json%}
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
{% endhighlight %} 
</pre>

One can also do this the other way around, retrieve using the sparse representation, and have
Vespa calculate the closeness rank feature for the hits retrieved by the sparse query representation. 

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
for complete examples of different retrieval and multi-phase ranking using Transformer models. 

## Tear down the container
This concludes this tutorial. The following removes the container and the data:
<pre data-test="after">
$ docker rm -f vespa
</pre>

<script src="/js/process_pre.js"></script>
