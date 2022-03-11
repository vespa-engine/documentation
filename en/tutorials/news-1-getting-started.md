---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "News search and recommendation tutorial - getting started on Docker"
redirect_from:
- /documentation/tutorials/news-1-getting-started.html
---


Our goal with this series is to set up a Vespa application for personalized
news recommendations. We will do this in stages, starting with a simple news
search system and gradually adding functionality as we go through the
tutorial parts.

The parts are:  

1. [Getting started](news-1-getting-started.html) - this part
2. [A basic news search application](news-2-basic-feeding-and-query.html) - application packages, feeding, query
3. [News search](news-3-searching.html) - sorting, grouping, and ranking
4. [Generating embeddings for users and news articles](news-4-embeddings.html)
5. [News recommendation](news-5-recommendation.html) - partial updates (news embeddings), ANNs, filtering
6. [News recommendation with searchers](news-6-recommendation-with-searchers.html) - custom searchers, doc processors
7. [News recommendation with parent-child](news-7-recommendation-with-parent-child.html) - parent-child, tensor ranking
8. Advanced news recommendation - intermission - training a ranking model
9. Advanced news recommendation - ML models

There are different entry points to this tutorial. This one is for getting
started using Docker on your local machine. Getting started on 
[cloud.vespa.ai](https://cloud.vespa.ai) is coming soon. We will also have a
version for [pyvespa](https://github.com/vespa-engine/pyvespa) soon.
For atomic model updates, see the [Models hot swap](models-hot-swap.html) tutorial.

In this part we will start with a minimal Vespa application to
get used to some basic operations for running the application on Docker.
In the next part of the tutorial, we'll start developing our application.

## Prerequisites

* [Docker](https://www.docker.com/) Desktop installed and running. 10GB available memory for Docker is recommended.
  Refer to [Docker memory](https://docs.vespa.ai/en/operations/docker-containers.html#memory)
  for details and troubleshooting
* Operating system: Linux, macOS or Windows 10 Pro (Docker requirement)
* Architecture: x86_64
* Minimum **10 GB** memory dedicated to Docker (the default is 2 GB on Macs)
* [Homebrew](https://brew.sh/) to install [Vespa CLI](https://docs.vespa.ai/en/vespa-cli.html), or download
  a vespa cli release from [Github releases](https://github.com/vespa-engine/vespa/releases).
* python3 

In upcoming parts of this series, we will have some additional python dependencies -
we use [PyTorch](https://pytorch.org/) to train vector representations for news and users
and train machine learning models for use in ranking.

## Installing vespa-cli 

This tutorial uses [Vespa-CLI](https://docs.vespa.ai/en/vespa-cli.html), Vespa CLI is the official command-line client for Vespa.ai.
It is a single binary without any runtime dependencies and is available for Linux, macOS and Windows.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ brew install vespa-cli 
</pre>
</div>

## A minimal Vespa application

This tutorial has a [companion sample application](https://github.com/vespa-engine/sample-apps.git)
found under the `news` directory. Throughout the tutorial we will be
using support code from this application. Also, the final state of 
each tutorial can be found in the various `app-...` sub-directories.

Let's start by cloning the sample application:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa clone news news
$ cd news
</pre>
</div>

The `app-1-getting-started` directory contains a minimal Vespa application.
There are two files there:

- `services.xml` -  defines the services the application consists of
- `schemas/news.sd` - defines the schema for searchable content. 

We will get back to these files in the next part of the tutorial.

## Starting Vespa

This application doesn't contain much at the moment, but let's start up the
application anyway by starting a Docker container to run it:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker pull vespaengine/vespa
$ docker run -m 10G --detach --name vespa --hostname vespa-tutorial \
  --publish 8080:8080 --publish 19071:19071 --publish 19092:19092 \
  vespaengine/vespa
</pre>
</div>

First, we pull the latest Vespa-image from the Docker repository, then we
start it with the name `vespa`. This starts the Docker container and the
initial Vespa services to be able to deploy an application.

Starting the container can take a short while. Before continuing, make sure
that the configuration service is running. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="is ready">
$ vespa status deploy --wait 300 --color never
</pre>
</div>

With the config server up and running, deploy the application using vespa-cli:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="is ready">
$ (cd app-1-getting-started && vespa deploy --wait 300 --color never)  
</pre>
</div>

The command uploads the application and verifies the content.
If anything is wrong with the application, this step will fail with a failure description,
otherwise this switches the application to a live status.

Whenever you have a new version of your application, 
run the same command to deploy the application.
In most cases, there is no need to restart the application.
Vespa takes care of reconfiguring the system.
If a restart of services is required in some rare case, however, the output will notify you.

In the upcoming parts of the tutorials, we'll frequently deploy the 
application in this manner. 

## Feeding to Vespa

We must index data before we can search for it. This is called 'feeding', and
we'll get back to that in more detail in the next part of the tutorial. For
now, to test that everything is up and running, we'll feed in a single test
document. We'll use the [vespa-feed-client](https://docs.vespa.ai/en/vespa-feed-client.html) 
Java feeder for this:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o vespa-feed-client-cli.zip \
    "https://search.maven.org/remotecontent?filepath=com/yahoo/vespa/vespa-feed-client-cli/7.527.20/vespa-feed-client-cli-7.527.20-zip.zip"
$ unzip vespa-feed-client-cli.zip
</pre>
</div>

We can also feed using [Vespa document api](https://docs.vespa.ai/en/document-v1-api-guide.html) directly,
 or using vespa-cli which uses the document api. 

This runs the `vespa-feed-client` Java client with the file `doc.json` file.
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --file doc.json --endpoint http://localhost:8080
</pre>
</div>

This runs the `vespa`cli with the file `doc.json` file. The `-v` option will make vespa-cli
print the http request:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ vespa document -v doc.json
</pre>
</div>

## Testing Vespa

If everything is ok so far, our application should be up and running.

We can query the endpoint using the vespa-cli (including verbose output with `-v`)

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Hello world!'>
$ vespa query -v 'yql=select * from news where true'
</pre>
</div>

This uses the `search` API to search for all documents of type `news`.
This should return `1` result, which is the document we fed above. 

Remove the document:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='id:news:news::1'>
$ vespa document -v remove id:news:news::1
</pre>
</div>

Well done!


## Stopping and starting Vespa

Keep Vespa running to continue with next steps in this tutorial set (skip the below).

To stop Vespa, we can run the following commands:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-stop-services'
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-stop-configserver'
</pre>
</div>

Likewise, to start the Vespa services:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-start-configserver'
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-start-services'
</pre>
</div>

If a restart is required due to changes in the application package,
these two steps are what you need to do.

To wipe the index and restart:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ docker exec vespa bash -c ' \
  /opt/vespa/bin/vespa-stop-services && \
  /opt/vespa/bin/vespa-remove-index -force && \
  /opt/vespa/bin/vespa-start-services'
</pre>
</div>

You can stop and kill the Vespa Docker application like this:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="after">
$ docker rm -f vespa
</pre>
</div>

This will delete the Vespa application, including all data, so don't do this unless you are sure.

## Conclusion

Our simple application should now be up and running. In the [next part
of the tutorial](news-2-basic-feeding-and-query.html), we'll start building
from this foundation.

<script src="/js/process_pre.js"></script>
