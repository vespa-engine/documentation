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
* Minimum **10 GB** memory dedicated to Docker (the default is 2 GB on Macs)
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

To download the dataset directly:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o lastfm_test.zip \
 http://millionsongdataset.com/sites/default/files/lastfm/lastfm_test.zip 
$ unzip lastfm_test.zip
</pre>
</div>

The sample or downloaded data needs to be converted to
[the JSON format expected by Vespa](reference/document-json-format.html).

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

A [Vespa application package[](cloudconfig/application-packages.html) is the set of configuration files and Java plugins
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

In addition we need plan to use our `similar` tensor field for ranking so we also need to define the query tensor:

<pre data-test="file" data-path="app/search/query-profiles/types/root.xml">
&lt;query-profile-type id=&quot;root&quot; inherits=&quot;native&quot;&gt;
    &lt;field name=&quot;ranking.features.query(user_liked)&quot; type=&quot;tensor&amp;lt;float&amp;gt;(trackid{})&quot; /&gt;
&lt;/query-profile-type&gt;
</pre>

<pre data-test="file" data-path="app/search/query-profiles/default.xml">
&lt;query-profile id=&quot;default&quot; type=&quot;root&quot;/&gt;
</pre>
## Deploy the application package

Once we have finished writing our application package, we can deploy it in a Docker container.

Note that indexing the full data set requires 47GB disk space. These tutorials have been
tested with a Docker container with 12GB RAM.  We used similar settings as
described in the [vespa quick start guide](../vespa-quick-start.html).
Start the Vespa container:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker run -m 12G --detach --name vespa --hostname vespa-msmarco \
  --publish 8080:8080 --publish 19112:19112 --publish 19071:19071 \
  vespaengine/vespa
</pre>
</div>

Starting the container can take a short while. Before continuing, make sure
that the configuration service is running by using `vespa status`. 

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
The file `vespa.json` generated by the `convert-msmarco.sh` script described in the [dataset section](#dataset)
already has data in the appropriate format expected by Vespa.
Feed it to Vespa using one of the tools Vespa provides for feeding,
as for example the [Java feeding API](../vespa-feed-client.html):

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


## Run a test query 

Once the data has started feeding, we can already send queries to our search app 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Sad Song">
$ vespa query 'yql=select artist, title, track_id from track where userQuery()' 'query=sad songs' 
</pre>
</div>

This query combines YQL [userQuery()](../reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](../reference/simple-query-language-reference.html), the 
default query type is using `all` requiring that all the terms match the document. 


<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>

## Tear down the container
This removes the container and the data:
<pre data-test="after">
$ docker rm -f vespa
</pre>
</div>

<script src="/js/process_pre.js"></script>
