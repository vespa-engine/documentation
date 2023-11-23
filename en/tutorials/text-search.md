---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
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

{% include pre-req.html memory="4 GB" extra-reqs='
<li>Python3</li>
<li><code>curl</code></li>' %}

Note: Use 12 GB Ram for Docker if running with the full dataset.


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

We start by acquiring the scripts and code required to follow this tutorial from the
[sampleapps repository](https://github.com/vespa-engine/sample-apps).

The first step is then to clone the `sample-apps` repo from GitHub and move into the `text-search` directory.
Start in an empty directory:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa clone text-search text-search && cd text-search
</pre>
</div>

The repository contains a fully-fledged Vespa application including a front-end search UI. 
This tutorial however will start with the basics and develop the application over multiple parts.


## Dataset

We use a dataset called [MS MARCO](https://microsoft.github.io/msmarco/) throughout this tutorial.
MS MARCO is a collection of large scale datasets released by Microsoft
with the intent of helping the advance of deep learning research related to search.
There are many tasks associated with MS MARCO datasets,
but here we are interested in the task of building an end-to-end search application
capable of returning relevant documents to a text query.

For the purposes of this tutorial we have included a small sample of the dataset under the `msmarco/sample` directory
which contains only around 1000 documents. This is sufficient for following along with this tutorial.

However, if you want to experiment with the entire dataset of more than 3 million documents,
download the data. Make sure to accept the [terms and conditions](https://microsoft.github.io/msmarco/) 
MS MARCO dataset is released under. The following will download the entire MS Marco Document Ranking collection:

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
and then converting to the Vespa format. If you downloaded the entire dataset,
we take a small sample of 1,000 queries and 100,000 documents for the convenience of following this tutorial on a laptop.
To convert the data, run the following script:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./bin/convert-msmarco.sh
</pre>
</div>

To adjust the number of queries and documents to sample, edit this file to your liking.
After running the script we end up with a file `msmarco/vespa.json` containing lines such as the one below:

<pre>{% highlight json%}
{
    "put": "id:msmarco:msmarco::D1555982",
    "fields": {
        "id": "D1555982",
        "url": "https://answers.yahoo.com/question/index?qid=20071007114826AAwCFvR",
        "title": "The hot glowing surfaces of stars emit energy in the form of electromagnetic radiation  ",
        "body": "Science   Mathematics Physics The hot glowing surfaces of stars emit energy in the form of electromagnetic radiation ... "
    }
}
{% endhighlight %}</pre>


In addition to `vespa.json` we also have a `test-queries.tsv` file containing a list of the sampled queries
along with the document id that is relevant to each particular query.
Each of those relevant documents are guaranteed to be in the sampled pool of documents that is included on `vespa.json`
so that we have a fair chance of retrieving it when sending sample queries to our Vespa application.


## Create a Vespa Application Package

A [Vespa application package](../application-packages.html) is the set of configuration files and Java plugins
that together define the behavior of a Vespa system:
what functionality to use, the available document types, how ranking will be done
and how data will be processed during feeding and indexing.
Let's define the minimum set of required files to create our basic text search application,
which are `msmarco.sd`, `services.xml`.

For this tutorial we will create a new Vespa application rather than using the one in the repository,
so we create a directory for this application:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir -p app/schemas
</pre>
</div>


### Schema

A [schema](../schemas.html) is a configuration of a document type and what we should compute over it.
For this application we define a document type called `msmarco`.
Write the following to `text-search/app/schemas/msmarco.sd`:

<pre data-test="file" data-path="text-search/app/schemas/msmarco.sd">
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
            indexing: index | summary
        }
        field body type string {
            indexing: index
            index: enable-bm25
        }
    }

    document-summary minimal {
        summary id type string {  }
    }

    fieldset default {
        fields: title, body, url
    }

    rank-profile default {
        first-phase {
            expression: nativeRank(title, body, url)
        }
    }

    rank-profile bm25 inherits default {
        first-phase {
            expression: bm25(title) + bm25(body) + bm25(url)
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
Note that we are enabling the usage of [BM25](../reference/bm25.html) for the fields `title`, `body` and `url`
by including `index: enable-bm25` in the respective fields.

Next, the [document summary class](../document-summaries.html) `minimal` is defined.
Document summaries are used to control what data is returned for a query.
The `minimal` summary here only returns the document id,
which is useful for speeding up relevance testing as less data needs to be returned.
The default document summary is defined by which fields are indexed with the `summary` command,
which in this case are all the fields. We do not include `body` in the summary, this to save disk usage.

For more information, refer to the [document summaries reference](../reference/schema-reference.html#summary).
Document summaries can be selected by using 
the [summary](../reference/query-api-reference.html#presentation.summary) query api parameter.

[Fieldsets](../reference/schema-reference.html#fieldset) provide a way to group fields together
to be able to search multiple fields. String fields grouped using fieldsets should share the same
[match](../reference/schema-reference.html#match) and [linguistic processing](../linguistics.html) settings. 

Vespa allows creating any number of [rank](../ranking.html) profiles which are
named collections of ranking and relevance calculations that one can choose from at query time.

A number of built-in [rank features](../reference/rank-features.html) are available to 
create highly specialized ranking expressions.
In this tutorial we define our default _rank-profile_ to be based on `nativeRank`,
which is a linear combination of the normalized scores computed by the several term-matching features
described in the [nativeRank documentation](../reference/nativerank.html).In addition, 
we created a _bm25 ranking-profile_ to compare with the one based on _nativeRank_.
[BM25](../reference/bm25.html) is faster to compute than _nativeRank_ while still giving better results than _nativeRank_ in some applications.

The `first-phase` keyword indicates that the `expression` defined in the _ranking-profile_
will be computed for every document matching the query. Vespa ranking supports [phased ranking](../phased-ranking.html)
Rank profiles are selected at run-time by using the [ranking](../reference/query-api-reference.html#ranking.profile)
query api parameter.


### Services Specification

The [services.xml](../reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.
Write the following to `text-search/app/services.xml`:

<pre data-test="file" data-path="text-search/app/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

    &lt;container id="text_search" version="1.0"&gt;
        &lt;search /&gt;
        &lt;document-processing /&gt;
        &lt;document-api /&gt;
    &lt;/container&gt;

    &lt;content id="msmarco" version="1.0"&gt;
        &lt;redundancy&gt;1&lt;/redundancy&gt;
        &lt;documents&gt;
            &lt;document type="msmarco" mode="index" /&gt;
            &lt;document-processing cluster="text_search" /&gt;
        &lt;/documents&gt;
        &lt;nodes&gt;
            &lt;node distribution-key="0" hostalias="node1" /&gt;
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


## Deploy the application package

Once we have finished writing our application package, we can deploy it in a Docker container.

Note that indexing the full data set requires 47 GB disk space.
These tutorials have been tested with a Docker container with 12 GB RAM.
We used similar settings as described in the [vespa quick start guide](../vespa-quick-start.html).
Start the Vespa container:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker run --detach --name vespa-msmarco --hostname vespa-msmarco \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa
</pre>
</div>

Configure the Vespa CLI to use the local Docker container:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa config set target local
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

Now, deploy the Vespa application that you have created in the `app` directory:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>


## Feed the data

The data fed to Vespa must match the document type in the schema.
The file `vespa.json` generated by the `convert-msmarco.sh` script described in the [dataset section](#dataset)
already has data in the appropriate format expected by Vespa:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa feed -t http://localhost:8080 msmarco/vespa.json
</pre>
</div>


## Run a test query

Once the data is fed, send a query to the search app:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select title,url,id from msmarco where userQuery()' \
  'query=what is dad bod' \
  'type=all'
</pre>
</div>
This query combines YQL [userQuery()](../reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](../reference/simple-query-language-reference.html),
the default query type is using `all`, requiring that all the terms match the document.

Following is a partial output of the query above when using the small dataset sample:
<pre>{% highlight json%}
{
    "root": {
        "id": "toplevel",
        "relevance": 1,
        "fields": {
            "totalCount": 3
        },
        "children": [
            {
                "id": "index:msmarco/0/59444ddd06537a24953b73e6",
                "relevance": 0.2747543357589305,
                "source": "msmarco",
                "fields": {
                    "id": "D2977840",
                    "title": "What Is A  Dad Bod   An Insight Into The Latest Male Body Craze To Sweep The Internet",
                    "url": "http://www.huffingtonpost.co.uk/2015/05/05/what-is-a-dadbod-male-body_n_7212072.html"
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

As we can see, there were 3 documents that matched the query out of 1000 available in the corpus.
The number of matched documents will be much larger when using the full dataset.
We can change retrieval mode from `all` to `any`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select title,url,id from msmarco where userQuery()' \
  'query=what is dad bod' \
  'type=any'
</pre>
</div>

Which will retrieve and rank all documents which matches _any_ of the query terms. As can be seen
from the result, almost all documents matched the query.
These type of queries can be performance optimized using the
[Vespa WeakAnd query operator](../using-wand-with-vespa.html):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select title,url,id from msmarco where userQuery()' \
  'query=what is dad bod' \
  'type=weakAnd'
</pre>
</div>

In this case, a much lesser set of documents where fully ranked due to using `weakAnd` instead of `any`.

In any case, the retrieved documents are ranked by the relevance score,
which in this case is delivered by the `nativeRank` rank feature
that we defined as the default _ranking-profile_ in our schema definition file.


## Compare and evaluate different ranking functions

Vespa allow us to easily experiment with different [rank-profiles](../reference/schema-reference.html#rank-profile).
For example, we could use the `bm25` rank-profile instead of the `default` rank-profile
by including the `ranking` parameter in the query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select title,url,id from msmarco where userQuery()' \
  'query=what is dad bod' \
  'ranking=bm25' \
  'type=weakAnd'
</pre>
</div>

Note that the relevance score,
which is normalized in the range [0,1] for the default rank profile using `nativeRank`,
changed to an un-normalized range when using the `bm25` rank feature.

In order to align with the guidelines of the [MS MARCO competition](https://microsoft.github.io/msmarco/),
we have created
[evaluate.py](https://github.com/vespa-engine/sample-apps/blob/master/text-search/src/python/evaluate.py)
to compute the [mean reciprocal rank (MRR)](https://en.wikipedia.org/wiki/Mean_reciprocal_rank)
metric given a file containing test queries.
The script loops through the queries, sends them to Vespa, parses the results
and computes the reciprocal rank for each query, and logs it to an output file:

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
We can than aggregate those values to compute the mean reciprocal rank for each rank-profile
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


## Cleanup
Stop and remove the Docker container and data:

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
