---
# Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Text Search Tutorial"
---

## Introduction

In this tutorial, we will guide you through the setup of a text search application built on top of Vespa. At the end you will be able to store text documents in Vespa and search them via text queries. The application built here will be the foundation to other tutorials that will add future improvements, such as creating ranking functions based on Machine Learning (ML) models. 

The main goal here is to setup a text search app based on simple term-match features such as BM25 [^1] and [NativeRank](../reference/nativerank.html). We will cover how to create, deploy and feed the Vespa application. We are going to go from raw data to a fully functional text search app. In addition we will showcase how easy it is to switch and experiment with different ranking functions in Vespa. 

We will start by describing the dataset used in this tutorial.

## Dataset

We will use a dataset called [MS MARCO](http://msmarco.org) throughout this tutorial. MS MARCO is a collection of large scale datasets released by Microsoft with the intent of helping the advance of deep learning research related to Search. There are many tasks associated with MS MARCO datasets, but here we are interested in the task of building an end-to-end search application capable of returning relevant documents to a text query. 

We can start by downloading the required data. We have made the scripts and code required to follow this tutorial available at [our sample apps repository](https://github.com/vespa-engine/sample-apps), including a script to download the data. The first step is then to clone the `sample-apps` repo from GitHub and move into the `text-search` folder as follows:

<pre data-test="exec">
$ git clone --depth 1 https://github.com/vespa-engine/sample-apps.git
$ cd sample-apps/text-search/
</pre>

We can now download the data with the following command:

<pre data-test="exec">
./bin/download-msmarco.sh
</pre>

It will create a `msmarco/download` folder within the `text-search` folder and download the required files. It currently takes around 21G of disk space.

After downloading the files we need to convert the data to [the format expected by Vespa](../reference/document-json-format.html). This includes extracting documents, queries and relevance judgements from the files we downloaded and then converting to the Vespa format. All those steps are encapsulated on the script below. For the convenience of following this tutorial on a laptop, we decided to sample 1,000 queries and 100,000 document out of the full dataset to speed up the time needed to get this application up and running.

<pre data-test="exec">
./bin/convert-msmarco.sh
</pre>

After running the script we end up with a `vespa.json` file containing lines such as the one below:

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

In addition to `vespa.json` we also have a `test-queries.tsv` file containing a list of the sampled queries along with the document id that is relevant to each particular query. Each of those relevant documents are guaranteed to be on the sampled pool of document that is included on `vespa.json` so that we have a fair chance of retrieving it when sending sample queries to our Vespa application.

## Create a Vespa Application Package

A Vespa application package is the set of configuration files and Java plugins that together define the behavior of a Vespa system: what functionality to use, the available document types, how ranking will be done and how data will be processed during feeding and indexing. Lets define the minimum set of required files to create our basic text search application, which are 
`msmarco.sd`, `services.xml` and `hosts.xml`. All those files need to be included within the `src/main/application` folder.

### Search definition

Write the following to
`application/searchdefinitions/msmarco.sd`, as it contains the search
definition for a document of type `msmarco`:

<pre data-test="file" data-path="application/searchdefinitions/msmarco.sd">
search msmarco {
    document msmarco {
        field id type string {
            indexing: summary | attribute
        }
        field title type string {
            indexing: index
            index: enable-bm25
        }
        field url type string {
            indexing: index
        }
        field body type string {
            indexing: index
            index: enable-bm25
        }
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

`document` is wrapped inside another element called `search`.  The name
following these elements, here `msmarco`, must be exactly the same for both.

The field property `indexing` configures the _indexing pipeline_ for a field,
which defines how Vespa will treat input during indexing — see [indexing
language](../reference/advanced-indexing-language.html).  Each part of the
indexing pipeline is separated by the pipe character '|':

- `index:` Create a search index for this field
- `attribute:` Store this field in memory as an [attribute](../attributes.html)
  — for [sorting](../reference/sorting.html),
    [searching](../search-api.html) and [grouping](../grouping.html)
- `summary:` Let this field be part of the
    [document summary](../document-summaries.html) in the result set

Note that we are enabling the usage of [BM25](../reference/bm25.html) for the fields `title` and `body` by including `index: enable-bm25` in the respective fields. This is a necessary step to allow us to use them in the `bm25` ranking profile.

[Fieldsets](../reference/search-definitions-reference.html#fieldset) provide a way to group fields together to be able to search multiple fields. That way a query such as 

```
curl -s http://localhost:8080/search/?query=is+sicily+a+state
```

will match all documents containing the words `is`, `sicily`, `a` and `state` in either the _title_ and/or the _body_.

Vespa allows creating any number of rank profiles: named collections of ranking and relevance calculations that one can choose from at query time. A number of built-in functions and expressions are available to create highly specialized rank expressions. In this tutorial we define our default _ranking-profile_ to be based on NativeRank, which is a linear combination of the normalized scores computed by the several term-matching features described in the [NativeRank documentation](../reference/nativerank.html). In addition,
we created a _bm25 ranking-profile_ to compare with the one based on _NativeRank_. _BM25_ is faster to compute than _NativeRank_ while still giving better results than _NativeRank_ in some applications. The `first-phase` keyword indicates that the `expression` defined in the _ranking-profile_ will be computed for every document matching your query.


### Services Specification

[services.xml](../reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.
Write the following to `application/services.xml`:

<pre data-test="file" data-path="application/services.xml">
<?xml version='1.0' encoding='UTF-8'?>
<!-- Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root. -->
<services version="1.0">

    <admin version="2.0">
        <adminserver hostalias="node1"/>
        <configservers>
        	<configserver hostalias="node1"/>
        </configservers>
        <cluster-controllers>
        	<cluster-controller hostalias="node1" />
        </cluster-controllers>
    </admin>

  <container id="stuff" version="1.0">
    <search/>
    <component id="com.yahoo.language.simple.SimpleLinguistics"/>
    <document-processing/>
    <document-api/>
  </container>

  <content id="msmarco" version="1.0">
       <redundancy reply-after='1'>1</redundancy>
       <documents>
         <document type='msmarco' mode="index"/>
         <document-processing cluster="stuff"/>
       </documents>
       <nodes>
       	<node distribution-key='0' hostalias='node1'/>
       </nodes>
  </content>
</services>
</pre>

Some notes about the elements above:

`<container>` defines the [container](../jdisc/index.html) cluster for
document, query and result processing

`<search>` sets up the [search](../search-api.html) endpoint for Vespa queries.
The default port is 8080.

`<document-api>` sets up the [document](../document-api.html) endpoint for
feeding.

`<content>` defines how documents are stored and searched

`<redundancy>` denotes how many copies to keep of each document.

`<documents>` assigns the document types in the _search definition_ — the
content cluster capacity can be increased by adding node elements — see
[elastic Vespa](../elastic-vespa.html). (See also the
[reference](../reference/services-content.html) for more on content cluster
setup.)

`<nodes>` defines the hosts for the content cluster.

### Deployment Specification

[hosts.xml](../reference/hosts.html) contains a list of all the hosts/nodes
that is part of the application, with an alias for each of them. This tutorial
uses a single node. Write the following to `application/hosts.xml`:

<pre data-test="file" data-path="application/hosts.xml">
<?xml version="1.0" encoding="utf-8" ?>
<hosts>
  <host name="localhost">
    <alias>node1</alias>
  </host>
</hosts>
</pre>

## Deploy the application package

Once we have finished writing our application package, we can deploy it in a Docker container

Indexing the full data set requires 47GB disk space.  These tutorials have been
tested with a Docker container with 12GB RAM.  We used similar settings as
described in the [vespa quick start guide](../vespa-quick-start.html).

In the following, we will assume you run all the commands from an empty
directory, i.e. the `pwd` directory is empty. We will map this directory
into the `/app` directory inside the Docker container. Now, to start the Vespa
container:

<pre data-test="exec">
docker run -m 12G --detach --name vespa-msmarco --hostname msmarco-app \
    --privileged --volume `pwd`:/app \
    --publish 8080:8080 --publish 19112:19112 vespaengine/vespa
</pre>

Make sure that the configuration server is running - signified by a 200 OK response:

<pre data-test="exec" data-test-wait-for="200 OK">
docker exec vespa-msmarco bash -c 'curl -s --head http://localhost:19071/ApplicationStatus'
</pre>

Now, deploy the Vespa application — start
Vespa as in the [quick start](../vespa-quick-start.html). To deploy the
application:

<pre data-test="exec">
docker exec vespa-msmarco bash -c '/opt/vespa/bin/vespa-deploy prepare /app/src/main/application && \
    /opt/vespa/bin/vespa-deploy activate'
</pre>

(or alternatively, run the equivalent commands inside the docker container. This prints that the application was activated successfully and also the
checksum, timestamp and generation for this deployment. The generation will increase by 1 each time a new application is successfully deployed, and is the easiest way to verify that the correct version is active.

After a short while, querying the port 8080 should return a 200 status code indicating that your application is up and running.

<pre data-test="exec">
curl -s --head http://localhost:8080/ApplicationStatus
</pre>

## Feed data and run a test query

### Feeding the data

The data fed to Vespa must match the search definition for the document type. The file `vespa.json` generated by the `convert-msmarco.sh` script described in the [Dataset section](#dataset) already has data in the approapriate format expected by Vespa. Send it to Vespa using one of the tools Vespa provides for feeding, as for example the [Java feeding API](../vespa-http-client.html):

<pre data-test="exec">
docker exec vespa-msmarco bash -c 'java -jar /opt/vespa/lib/jars/vespa-http-client-jar-with-dependencies.jar \
    --verbose --file /app/msmarco/vespa.json --host localhost --port 8080'
 </pre>

### Run a test query

Once the data has been fed, we can already send queries to our search app:

<pre data-test="exec">
curl -s http://localhost:8080/search/?query=is+sicily+a+state
</pre>

Following is a partial output of the query above:

```
{
  "root": {
    "id": "toplevel",
    "relevance": 1.0,
    "fields": {
      "totalCount": 3879
    },
    "coverage": {
      "coverage": 100,
      "documents": 3201751,
      "full": true,
      "nodes": 1,
      "results": 1,
      "resultsFull": 1
    },
    "children": [
      {
        "id": "id:msmarco:msmarco::D439103",
        "relevance": 0.2406705288318327,
        "source": "msmarco",
        "fields": {
          "sddocname": "msmarco",
          "documentid": "id:msmarco:msmarco::D439103",
          "id": "D439103"
        }
      },
      {
        "id": "id:msmarco:msmarco::D1335883",
        "relevance": 0.23397756764861974,
        "source": "msmarco",
        "fields": {
          "sddocname": "msmarco",
          "documentid": "id:msmarco:msmarco::D1335883",
          "id": "D1335883"
        }
      },
      ...
   ]
  }
}
```

As we can see, there were 3,879 documents that matched the query out of 3,201,751 available in the corpus. The results were ranked by the relevance score, which in this case is delivered by the `NativeRank` algorithm that we defined as the default _ranking-profile_ in our search definition file. 

## Compare and evaluate different ranking functions

Vespa allow us to easily experiment with different _ranking-profile_'s. For example, we could use the `bm25` _ranking-profile_ instead of the `default` _ranking-profile_ by including the `ranking` parameter in the query:

<pre data-test="exec">
curl -s http://localhost:8080/search/?query=is+sicily+a+state&ranking=bm25
</pre>

In order to align with the guidelines of the [MS MARCO competition](http://www.msmarco.org/leaders.aspx), we have created an `evaluate.py` script to compute the [mean reciprocal rank (MRR)](https://en.wikipedia.org/wiki/Mean_reciprocal_rank) metric given a file containing test queries. The script will loop through the queries, send them to Vespa, parse the results and compute the reciprocal rank for each query and log it to an output file.

<pre data-test="exec">
./src/python/evaluate.py bm25 msmarco
</pre>

<pre data-test="exec">
./src/python/evaluate.py default msmarco
</pre>

The commands above generate two output files named `test-output-default.tsv` and `test-output-bm25.tsv` containing the reciprocal rank metric for each query sent. We can than aggregate those values to compute the mean reciprocal rank for each _ranking-profile_ or plot those values to get a richer comparison between the two ranking functions, as shown in the figure below.

<div style="text-align:center"><img src="images/mrr_boxplot.png" style="width: 50%; margin-right: 1%; margin-bottom: 1.0em; margin-top: 1.0em;"></div>

Looking at the figure we can see that the faster BM25 feature has delivered superior results for this specific application.


[^1]: Robertson, Stephen and Zaragoza, Hugo and others, 2009. The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval.

<script>
function processFilePREs() {
    var tags = document.getElementsByTagName("pre");

    // copy elements, because the list above is mutated by the insert html below
    var elems = [];
    for (i = 0; i < tags.length; i++) {
        elems.push(tags[i]);
    }

    for (i = 0; i < elems.length; i++) {
        var elem = elems[i];
        if (elem.getAttribute("data-test") === "file") {
            var html = elem.innerHTML;
            elem.innerHTML = html.replace(/<!--\?/g, "<?").replace(/\?-->/g, "?>").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            elem.insertAdjacentHTML("beforebegin", "<pre class=\"filepath\">file: " + elem.getAttribute("data-path") + "</pre>");
        }
    }
};

processFilePREs();

</script>
