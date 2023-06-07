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

There are different entry points to this tutorial. This one is for getting
started using Docker on your local machine. Getting started on 
[cloud.vespa.ai](https://cloud.vespa.ai) is coming soon. We will also have a
version for [pyvespa](https://github.com/vespa-engine/pyvespa) soon.
For atomic model updates, see the [Models hot swap](models-hot-swap.html) tutorial.

In this part we will start with a minimal Vespa application to
get used to some basic operations for running the application on Docker.
In the next part of the tutorial, we'll start developing our application.

{% include pre-req.html memory="4 GB" extra-reqs='
<li>Python3 for converting the dataset to Vespa JSON.</li>
<li><code>curl</code> to download the dataset and run the Vespa health-checks.</li>
<li><a href="https://openjdk.java.net/projects/jdk/17/">Java 17</a> in part 6.</li>
<li><a href="https://maven.apache.org/install.html">Apache Maven</a> in part 6.</li>' %}

{% include note.html content='4 GB Docker memory is sufficient for the demo dataset in part 2.
The <span style="text-decoration: underline;">full</span> MIND dataset requires more, use 10 GB.' %}

In upcoming parts of this series, we will have some additional python dependencies -
we use [PyTorch](https://pytorch.org/) to train vector representations for news and users
and train machine learning models for use in ranking.


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


## A minimal Vespa application

This tutorial has a [companion sample application](https://github.com/vespa-engine/sample-apps/tree/master/news).
Throughout the tutorial we will be using support code from this application.
Also, the final state of each tutorial can be found in the various `app-...` sub-directories.

Let's start by cloning the sample application:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa clone -f news news && cd news
</pre>
</div>

The above downloads the `news` directory from the Vespa
[sample apps repository](https://github.com/vespa-engine/sample-apps/) and
places the contents in a folder called `news`. Use `--help` to see documentation 
for the vespa-cli utility:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa clone --help
</pre>
</div>
In the `news` directory there are several pre-configuration applications packages.
The `app-1-getting-started` directory contains a minimal Vespa application.
There are two files there:

- `services.xml` -  defines the services the application consists of
- `schemas/news.sd` - defines the schema for searchable content. 

We will get back to these files in the next part of the tutorial.


## Starting Vespa

This application doesn't contain much at the moment,
let's start up the application anyway by starting a Docker container to run it:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker pull vespaengine/vespa
$ docker run --detach --name vespa --hostname vespa-tutorial \
  --publish 8080:8080 --publish 19071:19071 --publish 19092:19092 \
  vespaengine/vespa
</pre>
</div>

First, we pull the latest [vespa-image](https://hub.docker.com/r/vespaengine/vespa/)
from the Docker hub, then we
start it with the name `vespa`. This starts the Docker container and the
initial Vespa services to be able to deploy an application.

Starting the container can take a short while. Before continuing, make sure
that the configuration service is running by using `vespa status`. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa status deploy --wait 300 
</pre>
</div>

With the config server up and running, deploy the application using vespa-cli:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app-1-getting-started 
</pre>
</div>

The command uploads the application and verifies the content.
If anything is wrong with the application, this step will fail with a failure description,
otherwise this switches the application to a live status.

Whenever you have a new version of your application, 
run the same command to deploy the application.
In most cases, there is no need to restart services.
Vespa takes care of reconfiguring the system.
If a restart of services is required in some rare case, however, the output will notify 
which services needs restart to make the change effective. 

In the upcoming parts of the tutorials, we'll frequently deploy the 
application changes in this manner. 


## Feeding to Vespa

We must index data before we can search for it. This is called "feeding", and
we'll get back to that in more detail in the next part of the tutorial. For
now, to test that everything is up and running, we'll feed in a single test
document. 

The first example uses the [vespa-feed-client](../vespa-feed-client.html) to index a document:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -L -o vespa-feed-client-cli.zip \
  "https://search.maven.org/remotecontent?filepath=com/yahoo/vespa/vespa-feed-client-cli/{{site.variables.vespa_version}}/vespa-feed-client-cli-{{site.variables.vespa_version}}-zip.zip"
$ unzip vespa-feed-client-cli.zip
</pre>
</div>

We can also feed using [Vespa document api](../document-v1-api-guide.html) directly,
or use the [Vespa CLI](../vespa-cli.html), which also uses the http document api.

This runs the `vespa-feed-client` Java client with the file `doc.json` file.
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --file doc.json --endpoint http://localhost:8080
</pre>
</div>

This runs the `vespa` cli with the file `doc.json` file. The `-v` option will make vespa-cli
print the http request:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ vespa document -v doc.json
</pre>
</div>

Once the feed operation is ack'ed by Vespa, the operation is visible in search.


## Querying Vespa

We can query the endpoint using the vespa-cli's support for performing queries.
It uses the [Vespa query api](../query-api.html) to query vespa,
including `-v` in the command we can see the exact endpoint and url request parameters used. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Hello world!'>
$ vespa query -v 'yql=select * from news where true'
</pre>
</div>

This example uses [YQL (Vespa Query Language)](../query-language.html) to 
search for all documents of type `news`. This query request will return `1` result, which is the document we fed above. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Hello world!'>
$ vespa query \
  'yql=select * from news where userQuery()' \
  'query=hello world' \
  'default-index=title'
</pre>
</div>

Another query language example that searches for hello or world in the title.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Hello world!'>
$ vespa query \
  'yql=select * from news where title contains phrase("hello","world")'
</pre>
</div>

Another query language example that searches for the phrase "hello world" in the title.
In the [next part of the tutorial](news-2-basic-feeding-and-query.html) we'll demonstrate more query examples,
and also ranking and grouping of results.


## Remove documents
Run the following to remove the document from the index:
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
$ docker exec vespa /opt/vespa/bin/vespa-stop-services
$ docker exec vespa /opt/vespa/bin/vespa-stop-configserver
</pre>
</div>

Likewise, to start the Vespa services:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ docker exec vespa /opt/vespa/bin/vespa-start-configserver
$ docker exec vespa /opt/vespa/bin/vespa-start-services
</pre>
</div>

If a [restart is required](../reference/schema-reference.html#changes-that-require-restart-but-not-re-feed)
due to change in the application package,
these two steps are what you need to do.

To wipe the index and restart:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ docker exec vespa sh -c ' \
  /opt/vespa/bin/vespa-stop-services && \
  /opt/vespa/bin/vespa-remove-index -force && \
  /opt/vespa/bin/vespa-start-services'
</pre>
</div>

You can stop and kill the Vespa container application like this:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="after">
$ docker stop vespa; docker rm -f vespa
</pre>
</div>

This will delete the Vespa application, including all data and configuration. See 
[container tuning for production](../operations/docker-containers.html). 


## Conclusion

Our simple application should now be up and running. In the [next part
of the tutorial](news-2-basic-feeding-and-query.html), we'll start building
from this foundation.

<script src="/js/process_pre.js"></script>
