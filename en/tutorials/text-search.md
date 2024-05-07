---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Text Search Tutorial"
redirect_from:
- /documentation/tutorials/text-search.html
---

This tutorial will guide you through setting up a simple text search application. 
At the end, you can index text documents in Vespa and search them via text queries.
The application built here will be the foundation for other tutorials,
such as creating ranking functions based on Machine Learning (ML) models.

The main goal is to set up a text search app based on simple term-match features
such as [BM25](../reference/bm25.html) [^1] and [nativeRank](../reference/nativerank.html). 
We will cover how to create, deploy, and index documents.

{% include pre-req.html memory="4 GB" extra-reqs='
<li>Python3</li>
<li><code>curl</code></li>' %}

## Installing vespa-cli 

This tutorial uses [Vespa-CLI](../vespa-cli.html),
it is a binary without any runtime dependencies and is available for Linux, macOS, and Windows.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ brew install vespa-cli 
</pre>
</div>

We acquire the scripts and code to follow this tutorial from the
[sample-apps repository](https://github.com/vespa-engine/sample-apps).

The first step is to clone the `sample-apps` repo from GitHub and move it into the `text-search` directory:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa clone text-search text-search && cd text-search
</pre>
</div>

The repository contains a fully-fledged Vespa application. 

## Dataset

We use a dataset called [MS MARCO](https://microsoft.github.io/msmarco/) throughout this tutorial.
MS MARCO is a collection of large-scale datasets released by Microsoft
with the intent of helping the advance of deep learning research related to search.
Many tasks are associated with MS MARCO datasets,
but we want to build an end-to-end search application that returns relevant documents to a text query.
We have included a small dataset sample for this tutorial under the `ext/`sample` directory, which contains around 1000 documents.

The sample data must be converted to Vespa [JSON feed format](../reference/document-json-format.html).
The following step includes extracting documents, queries and relevance judgments from the sample files:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./bin/convert-msmarco.sh
</pre>
</div>


After running the script, we end up with a file `ext/vespa.json` containing lines such as the one below:

<pre>{% highlight json%}
{
    "put": "id:msmarco:msmarco::D1555982",
    "fields": {
        "id": "D1555982",
        "url": "https://answers.yahoo.com/question/index?qid=20071007114826AAwCFvR",
        "title": "The hot glowing surfaces of stars emit energy in the form of electromagnetic radiation",
        "body": "Science   Mathematics Physics The hot glowing surfaces of stars emit energy in the form of electromagnetic radiation ... "
    }
}
{% endhighlight %}</pre>

In addition to `vespa.json` we also have a `test-queries.tsv` file containing a list of the sampled queries
along with the document ID relevant to each particular query.


## Create a Vespa Application Package

A [Vespa application package](../application-packages.html) is a set of configuration files and optional Java components
that together define the behavior of a Vespa system.

Let us define the minimum set of required files to create our basic text search application,
: `msmarco.sd` and `services.xml`.

For this tutorial, we will create a new Vespa application rather than using the one in the repository,
so we will create a directory for this application:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir -p app/schemas
</pre>
</div>


### Schema
A [schema](../schemas.html) is a document-type configuration; a single vespa application can have multiple schemas with document types.

For this application, we define a document type called `msmarco`.
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
        summary id {  }
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
Document summaries are used to control what fields are returned in the response for a query.
The `minimal` summary here only returns the document ID,
which is useful for speeding up relevance testing as less data needs to be returned.
The default document summary is defined by which fields are indexed with the `summary` command,
which in this case are all the fields. 

For more information, refer to the [document summaries reference](../reference/schema-reference.html#summary).
Document summaries can be selected by using 
the [summary](../reference/query-api-reference.html#presentation.summary) query api parameter.

[Fieldsets](../reference/schema-reference.html#fieldset) provide a way to group fields together
to be able to search multiple fields. String fields grouped using fieldsets should share the same
[match](../reference/schema-reference.html#match) and [linguistic processing](../linguistics.html) settings. 

Vespa allows creation any number of [rank-profiles](../ranking.html), which are
named collections of ranking and relevance calculations that one choose at query time.
Ma
ny built-in [rank](../reference/rank-features.html) features](../reference/rank-features.html) 
are available to create highly specialized ranking expressions.

In this tutorial, we define our default _rank-profile_ to be based on `nativeRank`,
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
        &lt;min-redundancy&gt;1&lt;/min-redundancy&gt;
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
- `<min-redundancy>` denotes how many copies to keep of each document.
- `<documents>` assigns the document types in the _schema_ —
  the content cluster capacity can be increased by adding node elements —
  see [elasticity](../elasticity.html).
  (See also the [reference](../reference/services-content.html) for more on content cluster setup.)
- `<nodes>` defines the hosts for the content cluster.


## Deploy the application package

Once we have finished writing our application package, we can deploy it.

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

Starting the container can take a short while.  Make sure
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
$ vespa feed -t http://localhost:8080 ext/vespa.json
</pre>
</div>


## Run a test query

Once the data is indexed, send a query to the search app:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select title, url, id from msmarco where userQuery()' \
  'query=what is dad bod' 
</pre>
</div>
This query combines YQL [userQuery()](../reference/query-language-reference.html#userquery) 
with Vespa's [simple query language](../reference/simple-query-language-reference.html).


Following is a partial output of the query above when using the small dataset sample:
<pre>{% highlight json%}
{
    "root": {
        "id": "toplevel",
        "relevance": 1,
        "fields": {
            "totalCount": 562
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

As we can see, there were 562 documents that matched the query out of 996 available in the corpus.
The number of matched documents will be much larger when using the full dataset.
We can change retrieval mode from the default `weakAnd` to `all`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select title, url, id from msmarco where userQuery()' \
  'query=what is dad bod' \
  'type=all'
</pre>
</div>

Which will retrieve and rank fewer (3) documents because we require that all query terms be matched.  

## Compare and evaluate different ranking functions

Vespa supports experimenting with different [rank-profiles](../reference/schema-reference.html#rank-profile).
For example, we could use the `bm25` rank-profile instead of the `default` rank-profile
by including the `ranking` parameter in the query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select title, url, id from msmarco where userQuery()' \
  'query=what is dad bod' \
  'ranking=bm25' 
</pre>
</div>


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
