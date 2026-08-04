---
# Copyright Vespa.ai. All rights reserved.
title: "News search and recommendation tutorial - getting started on Vespa Cloud"
redirect_from:
- /en/tutorials/news-1-getting-started.html
- /en/tutorials/news-1-deploy-an-application
---


Our goal with this series is to set up a Vespa application for personalized
news recommendations on Vespa Cloud. We will do this in stages, starting with a simple news
search system and gradually adding functionality as we go through the
tutorial parts.

The parts are:  

1. [Getting started](news-1-deploy-an-application.html) - this part
2. [A basic news search application](news-2-basic-feeding-and-query.html) - application packages, feeding, query
3. [News search](news-3-searching.html) - sorting, grouping, and ranking
4. [Generating embeddings for users and news articles](news-4-embeddings.html)
5. [News recommendation](news-5-recommendation.html) - partial updates (news embeddings), ANNs, filtering
6. [News recommendation with searchers](news-6-recommendation-with-searchers.html) - custom searchers, doc processors
7. [News recommendation with parent-child](news-7-recommendation-with-parent-child.html) - parent-child, tensor ranking

In this part, we will start with a minimal Vespa application to get used to some basic
operations for deploying and running an application on Vespa Cloud.
In the next part of the tutorial, we'll start developing our application.

<div class="vespa-notification vespa-notification-prereqs" role="alert">
  <p><strong>Prerequisites:</strong></p>
  <ul>
    <li>A Vespa Cloud account - create a <a href="https://console.vespa-cloud.com/">tenant</a>
        if you do not have one.</li>
    <li><a href="https://brew.sh/">Homebrew</a> to install the <a href="../../clients/vespa-cli.html">Vespa CLI</a>,
        or download the Vespa CLI from <a href="https://github.com/vespa-engine/vespa/releases">Github releases</a>.</li>
    <li>Python3 for converting the dataset to Vespa JSON.</li>
    <li><code>curl</code> to download the dataset.</li>
    <li><a href="https://openjdk.org/projects/jdk/17/" data-proofer-ignore>Java 17</a> in part 6.</li>
    <li><a href="https://maven.apache.org/install.html">Apache Maven</a> in part 6.</li>
  </ul>
</div>

In upcoming parts of this series, we will have some additional Python dependencies -
we use [PyTorch](https://pytorch.org/) to train vector representations for news and users
and train machine learning models for use in ranking.


## Installing Vespa CLI

This tutorial uses [Vespa-CLI](../../clients/vespa-cli.html),
Vespa CLI is the official command-line client for Vespa.ai.
It is a single binary without any runtime dependencies and is available for Linux, macOS, and Windows.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ brew install vespa-cli 
</pre>
</div>

In this tutorial it is possible to use either a local or global 
Vespa CLI configuration mode for configuration variables. Using 
local configuration mode is generally recommended when working 
with multiple distinct Vespa applications, but most parts of 
this tutorial uses the same configuration values which makes 
it easier to use global configuration mode:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ vespa config set default_config_scope global
</pre>
</div>


## A minimal Vespa application

This tutorial has a [companion sample application](https://github.com/vespa-engine/sample-apps/tree/master/news).
Throughout the tutorial, we will be using support code from this application.
Also, the final state of each tutorial can be found in the various `app-...` subdirectories.

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
In the `news` directory, several pre-configured application packages are available.
The `app-1-getting-started` directory contains a minimal Vespa application.
There are two files there:

- `services.xml` -  defines the services that the application consists of
- `schemas/news.sd` - defines the schema for searchable content. 

We will revisit these files in the next part of the tutorial.


## Configuring Vespa CLI for Vespa Cloud
Configure the Vespa CLI to use Vespa Cloud, and set the application name.
Replace `tenant-name` with your tenant name from [console.vespa-cloud.com](https://console.vespa-cloud.com):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ vespa config set target cloud
$ vespa config set application tenant-name.news
</pre>
</div>

Usually its better to use local configuration for each application, 
but this tutorial uses global configuration to avoid having to set the 
configuration values for each part of the tutorial.

Authenticate with Vespa Cloud:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ vespa auth login
</pre>
</div>

Follow the browser instructions to complete authentication.

Next, add a certificate for [data plane access](/en/security/guide#data-plane) to the application:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ vespa auth cert app-1-getting-started
</pre>
</div>




## Deploying to Vespa Cloud

This application doesn't contain much at the moment,
but let's deploy it to Vespa Cloud anyway to get used to the basic operations.
The first deployment may take a few minutes while nodes are provisioned:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 600 app-1-getting-started 
</pre>
</div>

The command uploads the application and verifies the content.
If anything is wrong with the application, this step will fail with a failure description;
otherwise, this switches the application to a live status.

Whenever you have a new version of your application,
run the same command to deploy the application.
In most cases, there is no need to restart services.
Vespa takes care of reconfiguring the system.

In the upcoming parts of the tutorials, we'll frequently deploy the
application changes in this manner.


## Feeding to Vespa

We must index data before we can search for it.
This is called "feeding", and we'll get back to that in more detail in the next part of the tutorial.
For now, to test that everything is up and running, we'll feed in a single test document:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ vespa feed doc.json
</pre>
</div>

The `-v` option will make vespa-cli print the http request:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ vespa document -v doc.json
</pre>
</div>

We can also feed using [Vespa document api](../../writing/document-v1-api-guide.html) directly.

Once the feed operation is acknowledged by Vespa, the operation is visible in search.


## Querying Vespa

We can query the endpoint using the vespa-cli's support for performing queries.
It uses the [Vespa query api](../../querying/query-api.html) to query vespa,
including `-v` in the command, we can see the exact endpoint and url request parameters used. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='Hello world!'>
$ vespa query -v 'yql=select * from news where true'
</pre>
</div>

This example uses [YQL (Vespa Query Language)](../../querying/query-language.html) to 
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


## Managing the Vespa Cloud application

Application instances in the [dev zone](../operations/environments.html#dev) will by default keep running for 14 days after the last deployment.
You can control this in the [console](https://console.vespa-cloud.com/).

The [Vespa Cloud console](https://console.vespa-cloud.com) can also be used to delete the application instance.


## Conclusion

Our simple application should now be up and running. In the [next part
of the tutorial](news-2-basic-feeding-and-query.html), we'll start building
from this foundation.

<script src="/js/process_pre.js"></script>
