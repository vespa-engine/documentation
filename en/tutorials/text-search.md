---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Text Search Tutorial"
redirect_from:
- /documentation/tutorials/text-search.html
---

In this tutorial, we will guide you through the setup of a text search application built on top of Vespa.
At the end you will be able to store text documents in Vespa and search them via text queries.
The application built here will be the foundation to other tutorials that will add future improvements,
such as creating ranking functions based on Machine Learning (ML) models.

The main goal here is to set up a text search app based on simple term-match features
such as [BM25](../reference/bm25.html) [^1] and [nativeRank](../reference/nativerank.html). 
We will cover how to create, deploy and feed the Vespa application.
We are going to go from raw data to a fully functional text search app.
In addition, we will showcase how easy it is to switch and experiment with different ranking functions in Vespa.


## Preamble

We start by acquiring the scripts and code required to follow this tutorial from
[our sample apps repository](https://github.com/vespa-engine/sample-apps).
The first step is then to clone the `sample-apps` repo from GitHub and move into the `text-search` directory.
Start in an empty directory:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ git clone --depth 1 https://github.com/vespa-engine/sample-apps.git
$ cd sample-apps/text-search
</pre>
</div>

This repository contains a fully-fledged Vespa application including a front-end search UI. 
This tutorial however will start with the basics and develop the application over multiple parts.



## Dataset

We use a dataset called [MS MARCO](https://microsoft.github.io/msmarco/) throughout this tutorial.
MS MARCO is a collection of large scale datasets released by Microsoft
with the intent of helping the advance of deep learning research related to search.
There are many tasks associated with MS MARCO datasets,
but here we are interested in the task of building an end-to-end search application
capable of returning relevant documents to a text query.

For the purposes of this tutorial we have included a small sample of the dataset under the `msmarco/sample` directory
which contains only around 1000 documents.
This is sufficient for following along with this tutorial,
however if you want to experiment with the entire dataset of more than 3 million documents,
download the data with the following command:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ ./bin/download-msmarco.sh
</pre>
</div>

It will create a `msmarco/download` directory within the `text-search` directory and download the required files.
Note that it currently takes around 21G of disk space, and the conversion scripts below can take a fair amount of time.

The sample or downloaded data needs to be converted to
[the format expected by Vespa](../reference/document-json-format.html).
This includes extracting documents, queries and relevance judgements from the files we downloaded
and then converting to the Vespa format.
If you downloaded the entire dataset,
we take a small sample of 1,000 queries and 100,000 documents for the convenience of following this tutorial on a laptop.
To convert the data, run the following script (for either the sample or downloaded dataset):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./bin/convert-msmarco.sh
</pre>
</div>

To adjust the number of queries and documents to sample, edit this file to your liking.
After running the script we end up with a file `msmarco/vespa.json` containing lines such as the one below:

```
{
  "put": "id:msmarco:msmarco::D1555982",
  "fields": {
    "id": "D1555982",
    "url": "https://answers.yahoo.com/question/index?qid=20071007114826AAwCFvR",
    "title": "The hot glowing surfaces of stars emit energy in the form of electromagnetic radiation  ",
    "body": "Science   Mathematics Physics The hot glowing surfaces of stars emit energy in the form of electromagnetic radiation ... "
  }
}
```

In addition to `vespa.json` we also have a `test-queries.tsv` file containing a list of the sampled queries
along with the document id that is relevant to each particular query.
Each of those relevant documents are guaranteed to be on the sampled pool of documents that is included on `vespa.json`
so that we have a fair chance of retrieving it when sending sample queries to our Vespa application.



## Create a Vespa Application Package

A Vespa application package is the set of configuration files and Java plugins
that together define the behavior of a Vespa system:
what functionality to use, the available document types, how ranking will be done
and how data will be processed during feeding and indexing.
Let's define the minimum set of required files to create our basic text search application,
which are `msmarco.sd`, `services.xml` and `hosts.xml`.
All those files need to be included within the application package directory.

For this tutorial we will create a new Vespa application rather than using the one in the repository,
so we create a directory for this application:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir application
</pre>
</div>



### Schema

A [schema](../schemas.html) is a configuration of a document type and what we should compute over it.
For this application we define a document type called `msmarco`.
Write the following to `application/schemas/msmarco.sd`:

<pre data-test="file" data-path="sample-apps/text-search/application/schemas/msmarco.sd">
schema msmarco {
    document msmarco {
        field id type string {
            indexing: attribute | summary
        }
        field title type string {
            indexing: index | summary
            index: enable-bm25
        }
        field url type string {
            indexing: summary
        }
        field body type string {
            indexing: index | summary
            index: enable-bm25
            summary: dynamic
        }
    }

    document-summary minimal {
        summary id type string {  }
    }

    fieldset default {
        fields: title, body
    }

    rank-profile default {
        first-phase {
            expression: nativeRank(title, body)
        }
    }

    rank-profile bm25 inherits default {
        first-phase {
            expression: bm25(title) + bm25(body)
        }
    }
}
</pre>

Here, we define the `msmarco` schema, which includes primarily two things:
a definition of fields the `msmarco` document type should have,
and a definition on how Vespa should rank documents given a query.

The `document` section contains the fields of the document, their types and how Vespa should index them.
The field property `indexing` configures the _indexing pipeline_ for a field.
For more information see [schemas - indexing](../schemas.html#indexing).
Note that we are enabling the usage of [BM25](../reference/bm25.html) for the fields `title` and `body`
by including `index: enable-bm25` in the respective fields.
This is a necessary step to allow us to use them in the `bm25` ranking profile.

Next, the [document summary class](../document-summaries.html) `minimal` is defined.
Document summaries are used to control what data is returned for a query.
The `minimal` summary here only returns the document id,
which is useful for speeding up relevance testing as less data needs to be returned.
The default document summary is defined by which fields are indexed with the `summary` command,
which in this case are all the fields.
In addition, we've set up the `body` field to show a dynamic summary,
meaning that Vespa will try to extract relevant parts of the document.
For more information, refer to the [the reference documentation on document summaries](../reference/schema-reference.html#summary).

Document summaries can be selected by using the `summary` query parameter.

[Fieldsets](../reference/schema-reference.html#fieldset) provide a way to group fields together
to be able to search multiple fields. That way a query such as

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ curl -s http://localhost:8080/search/?query=what+is+dad+bod
</pre>
</div>

will match all documents containing the words `what`, `is`, `dad`, and `bod` in either the _title_ and/or the _body_.

Vespa allows creating any number of rank profiles:
named collections of ranking and relevance calculations that one can choose from at query time.
A number of built-in functions and expressions are available to create highly specialized rank expressions.
In this tutorial we define our default _ranking-profile_ to be based on nativeRank,
which is a linear combination of the normalized scores computed by the several term-matching features
described in the [nativeRank documentation](../reference/nativerank.html).
In addition, we created a _bm25 ranking-profile_ to compare with the one based on _nativeRank_.
_BM25_ is faster to compute than _nativeRank_ while still giving better results than _nativeRank_ in some applications.
The `first-phase` keyword indicates that the `expression` defined in the _ranking-profile_
will be computed for every document matching your query.

Rank profiles are selected by using the `ranking` query parameter.



### Services Specification

The [services.xml](../reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.
Write the following to `application/services.xml`:

<pre data-test="file" data-path="sample-apps/text-search/application/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

  &lt;container id="text_search" version="1.0"&gt;
    &lt;search&gt;&lt;/search&gt;
    &lt;document-processing&gt;&lt;/document-processing&gt;
    &lt;document-api&gt;&lt;/document-api&gt;
  &lt;/container&gt;

  &lt;content id="msmarco" version="1.0"&gt;
    &lt;redundancy&gt;1&lt;/redundancy&gt;
    &lt;documents&gt;
      &lt;document type="msmarco" mode="index"&gt;&lt;/document&gt;
      &lt;document-processing cluster="text_search"&gt;&lt;/document-processing&gt;
    &lt;/documents&gt;
    &lt;nodes&gt;
      &lt;node distribution-key="0" hostalias="node1"&gt;&lt;/node&gt;
    &lt;/nodes&gt;
  &lt;/content&gt;
&lt;/services&gt;
</pre>

Some notes about the elements above:

- `<container>` defines the [container cluster](../jdisc/index.html) for document, query and result processing
- `<search>` sets up the [query endpoint](../query-api.html).  The default port is 8080.
- `<document-api>` sets up the [document endpoint](../reference/document-v1-api-reference.html) for feeding.
- `<content>` defines how documents are stored and searched
- `<redundancy>` denotes how many copies to keep of each document.
- `<documents>` assigns the document types in the _schema_ —
  the content cluster capacity can be increased by adding node elements —
  see [elasticity](../elasticity.html).
  (See also the [reference](../reference/services-content.html) for more on content cluster setup.)
- `<nodes>` defines the hosts for the content cluster.


### Deployment Specification

[hosts.xml](../reference/hosts.html) contains a list of all the hosts/nodes
that is part of the application, with an alias for each of them. This tutorial
uses a single node. Write the following to `application/hosts.xml`:

<pre data-test="file" data-path="sample-apps/text-search/application/hosts.xml">
&lt;?xml version="1.0" encoding="utf-8"?&gt;
&lt;hosts&gt;
  &lt;host name="localhost"&gt;
    &lt;alias&gt;node1&lt;/alias&gt;
  &lt;/host&gt;
&lt;/hosts&gt;
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
$ docker run -m 12G --detach --name vespa-msmarco --hostname vespa-msmarco \
  --publish 8080:8080 --publish 19112:19112 --publish 19071:19071 \
  vespaengine/vespa
</pre>
</div>

Make sure that the configuration server is running - signified by a 200 OK response:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-wait-for="200 OK">
$ curl -s --head http://localhost:19071/ApplicationStatus
</pre>
</div>

Now, to deploy the Vespa application:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="prepared and activated.">
$ (cd application && zip -r - .) | \
  curl --header Content-Type:application/zip --data-binary @- \
  localhost:19071/application/v2/tenant/default/prepareandactivate
</pre>
</div>

This prints that the application was activated successfully
and also the checksum, timestamp and generation for this deployment.
The generation will increase by 1 each time a new application is successfully deployed,
and is the easiest way to verify that the correct version is active.

After a short while, querying the port 8080 should return a 200 status code,
indicating the application is up and running.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-wait-for="200 OK">
$ curl -s --head http://localhost:8080/ApplicationStatus
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
  --verbose --file msmarco/vespa.json --endpoint http://localhost:8080
</pre>
</div>



## Run a test query

Once the data has started feeding, we can already send queries to our search app even before it has finished:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -s "http://localhost:8080/search/?query=what+is+dad+bod&amp;summary=minimal"
</pre>
</div>

Following is a partial output of the query above when using the small dataset sample:

```
{
  "root": {
    "id": "toplevel",
    "relevance": 1.0,
    "fields": {
      "totalCount": 3
    },
    "coverage": {
      "coverage": 100,
      "documents": 1000,
      "full": true,
      "nodes": 1,
      "results": 1,
      "resultsFull": 1
    },
    "children": [
      {
        "id": "index:msmarco/0/59444ddd06537a24953b73e6",
        "relevance": 0.2747543357589305,
        "source": "msmarco",
        "fields": {
          "sddocname": "msmarco",
          "id": "D2977840"
        }
      },
      ...
    ]
  }
}
```

As we can see, there was 3 documents that matched the query out of 1000 available in the corpus.
The number of matched documents will be much larger when using the full dataset.
The results are ranked by the relevance score,
which in this case is delivered by the `nativeRank` algorithm
that we defined as the default _ranking-profile_ in our schema definition file.



## Compare and evaluate different ranking functions

Vespa allow us to easily experiment with different _ranking-profile_'s.
For example, we could use the `bm25` _ranking-profile_ instead of the `default` _ranking-profile_
by including the `ranking` parameter in the query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ curl -s "http://localhost:8080/search/?query=what+is+dad+bod&amp;ranking=bm25"
</pre>
</div>

In order to align with the guidelines of the [MS MARCO competition](http://www.msmarco.org/leaders.aspx),
we have created an `evaluate.py` script to compute the
[mean reciprocal rank (MRR)](https://en.wikipedia.org/wiki/Mean_reciprocal_rank)
metric given a file containing test queries.
The script will loop through the queries, send them to Vespa, parse the results
and compute the reciprocal rank for each query and log it to an output file.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./src/python/evaluate.py bm25 msmarco
</pre>
</div>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./src/python/evaluate.py default msmarco
</pre>
</div>

The commands above output the mean reciprocal rank score as well as generate two output files 
`msmarco/test-output-default.tsv` and `msmarco/test-output-bm25.tsv`
containing the reciprocal rank metric for each query sent.
We can than aggregate those values to compute the mean reciprocal rank for each _ranking-profile_
or plot those values to get a richer comparison between the two ranking functions.
For the small dataset in the sample data, the MRR is approximately equal.
For the full MSMARCO dataset on the other hand, we see a different picture:

<div style="text-align:center">
<img src="/assets/img/tutorials/mrr_boxplot.png"
     style="width: 50%; margin-right: 1%; margin-bottom: 1.0em; margin-top: 1.0em;"
     alt="Plot with Ranking scores for BM25 and nativerank" />
</div>

Looking at the figure we can see that the faster BM25 feature
has delivered superior results for this specific application.

To stop and remove the Docker container for this application:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="after">
$ docker rm -f vespa-msmarco
</pre>
</div>



## Next steps
Check out the [Improving Text Search through ML](text-search-ml.html).


[^1]: Robertson, Stephen and Zaragoza, Hugo and others, 2009. The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval.

<script src="/js/process_pre.js"></script>
