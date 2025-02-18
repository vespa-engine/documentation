---
# Copyright Vespa.ai. All rights reserved.
title: "Text Search Tutorial"
---

This tutorial will guide you through setting up a simple text search application. 
At the end, you can index text documents in Vespa and search them via text queries.
The application built here will be the foundation for other tutorials,
such as creating ranking functions based on Machine Learning (ML) models.

The main goal is to set up a text search app based on simple text scoring features
such as [BM25](../reference/bm25.html) [^1] and [nativeRank](../reference/nativerank.html). 


{% include pre-req.html memory="4 GB" extra-reqs='
<li>Python3</li>
<li><code>curl</code></li>' %}

## Installing vespa-cli 

This tutorial uses [Vespa-CLI](../vespa-cli.html) to deploy, feed and query Vespa. Below, we use [HomeBrew](https://brew.sh/) to download and install `vespa-cli`, you can also
download a binary from [GitHub](https://github.com/vespa-engine/vespa/releases) for your OS/CPU architecture. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ brew install vespa-cli 
</pre>
</div>

We acquire the scripts to follow this tutorial from the
[sample-apps repository](https://github.com/vespa-engine/sample-apps/tree/master/text-search) via 
`vespa clone`.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa clone text-search text-search && cd text-search
</pre>
</div>

The repository contains a fully-fledged Vespa application, but below, we will build
it all from scratch for educational purposes. 

## Dataset

We use a dataset called [MS MARCO](https://microsoft.github.io/msmarco/) throughout this tutorial.
MS MARCO is a collection of large-scale datasets released by Microsoft
with the intent of helping the advance of deep learning research related to search.
Many tasks are associated with MS MARCO datasets,
but we want to build an end-to-end search application that returns relevant documents to a text query.
We have included a small dataset sample for this tutorial under the `ext/sample` directory, which contains around 1000 documents.

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

A [Vespa application package](../application-packages.html) is a set of configuration files and optional Java components that together define the behavior of a Vespa system. Let us define the minimum set of required files to create our basic text search application,
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
For this application, we define a schema `msmarco` which must be saved in a file named `schemas/msmarco.sd`.
Write the following to `text-search/app/schemas/msmarco.sd`:

<pre data-test="file" data-path="text-search/app/schemas/msmarco.sd">
schema msmarco {
    document msmarco {
        field language type string {
            indexing: "en" | set_language 
        }
        field id type string {
            indexing: attribute | summary
            match: word
        }
        field title type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
        field body type string {
            indexing: index
            match: text
            index: enable-bm25
        }
        field url type string {
            indexing: index | summary
            index: enable-bm25
        }
    }
    fieldset default {
        fields: title, body, url
    }
    document-summary minimal {
        summary id {  }
    }
    document-summary url-tokens {
        summary url {}
        summary url-tokens {
            source: url
            tokens
        }
        from-disk
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
A lot is going on here; let us go through it in detail. 

#### Document type and fields
The `document` section contains the fields of the document, their types,
and how Vespa should index and [match](/en/reference/schema-reference.html#match) them.

The field property `indexing` configures the _indexing pipeline_ for a field.
For more information, see [schemas - indexing](../schemas.html#indexing).
The [string](../reference/schema-reference.html#string) data type is used to represent both unstructured and structured texts, 
and there are significant differences between [index and attribute](../text-matching.html#index-and-attribute). The above
schema includes default `match` modes for `attribute` and `index` property for visibility.  

Note that we are enabling the usage of [BM25](../reference/bm25.html) for `title`, `body` and `url`.
by including `index: enable-bm25`. The language field is the only field not in the msmarco dataset. We hardcode its value 
to "en" since the dataset is English. Using `set_language` avoids automatic language detection and uses the value when processing the other
text fields. Read more in [linguistics](../linguistics.html).

#### Fieldset for matching across multiple fields

[Fieldset](../reference/schema-reference.html#fieldset) allows searching across multiple fields. Defining `fieldset` does not 
add indexing/storage overhead. String fields grouped using fieldsets must share the same 
[match](../reference/schema-reference.html#match) and [linguistic processing](../linguistics.html) settings because
the query processing that searches a field or fieldset uses *one* type of transformation.

#### Document summaries to control search response contents
Next, we define two [document summaries](../document-summaries.html). 
Document summaries control what fields are available in the [response](../reference/default-result-format.html); we include the `url-tokens` document-summary to 
demonstrate later how we can get visibility into how text is converted into searchable tokens. 

#### Ranking to determine matched documents ordering
You can define many [rank profiles](../ranking.html), 
named collections of score calculations, and ranking phases.

In this tutorial, we define our `default` to be using [nativeRank](../reference/nativerank.html).
In addition, we have a `bm25` rank-profile that uses [bm25](../reference/bm25.html). Both are examples of
text-scoring [rank-features](../reference/rank-features.html) in Vespa.

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
- `<documents>` assigns the document types in the _schema_  to content clusters —
  the content cluster capacity can be increased by adding node elements —
  see [elasticity](../elasticity.html).
  (See also the [reference](../reference/services-content.html) for more on content cluster setup.)
- `<nodes>` defines the hosts for the content cluster.

## Deploy the application package

Once we have finished writing our application package, we can deploy it.
We use settings similar to those in the [Vespa quick start guide](../vespa-quick-start.html).

Start the Vespa container:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker run --detach --name vespa-msmarco --hostname vespa-msmarco \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa
</pre>
</div>
Notice that we publish two ports (:8080) is the data-plane port where we write and query documents, and 19071 is
the control-plane where we can deploy the application. 

Configure the Vespa CLI to use the local container:
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

Now, deploy the Vespa application from the `app` directory:

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


## Querying the data

This section demonstrates various ways to search the data using the [Vespa query language](/en/query-language.html). All
the examples use the `vespa-cli` client, the tool uses the HTTP api and if you pass `-v`, you will see the `curl` equivalent
API request. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where userInput(@user-query)' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en'
</pre>
</div>

This query combines YQL [userInput()](../reference/query-language-reference.html#userinput), a robust
way to combine free text queries from users with application logic. Similar to `set_language` in indexing, we specify
the language of the query using the [language](../linguistics.html#querying-with-language) API parameter. This ensures
symmetric linguistic processing of both the query and the document text. Automatic language detection is inaccurate
for short query strings and might lead to asymmetric processing of queries and document texts. 

Following is a partial output of the query above when using the small dataset sample:
<pre>{% highlight json%}
{
    "root": {
        "id": "toplevel",
        "relevance": 1,
        "fields": {
            "totalCount": 562
        },
        "children":[
            {
                "id": "id:msmarco:msmarco::D2977840",
                "relevance": 0.20676669550322158,
                "source": "msmarco",
                "fields": {
                    "sddocname": "msmarco",
                    "body": "<sep />After The Cut released a piece explaining <hi>what</hi> the  <hi>dad</hi> <hi>bod</hi>  <hi>is</hi> last week  the internet pretty much exploded into debate over the trend  <sep />",
                    "documentid": "id:msmarco:msmarco::D2977840",
                    "id": "D2977840",
                    "title": "What Is A  Dad Bod   An Insight Into The Latest Male Body Craze To Sweep The Internet",
                    "url": "http://www.huffingtonpost.co.uk/2015/05/05/what-is-a-dadbod-male-body_n_7212072.html"
                }
            }
        ]

    }
}
{% endhighlight %}</pre>
As shown, 562 documents matched the query out of 996 in the corpus. The `first-phase` ranking expression scores all the matching documents.

A few important observations:

- We did not specify which fields to search in the query. Vespa will, by default, use a field set or field named `default` when the query terms do not specify a field. In our case:

<pre>
fieldset default {
  fields: title, body, url
}
</pre>
- Our query for `what is dad bod` searches across all those three fields. 
- If we did not specify a `default` fieldset in the schema, the above query would return zero hits as the query did not specify a field.  
- The hit `relevance` holds the score computed by the rank profile. Vespa uses `default` by default. 
In our case:

<pre>
rank-profile default {
    first-phase {
        expression: nativeRank(title, body, url)
    }
}
</pre>

We can use query operator annotations for the [userInput](..//reference/query-language-reference.html#userinput) to control various
matching aspects. The following uses the `defaultIndex` to specify which field (or fieldset) to search.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where {defaultIndex:"title"}userInput(@user-query)' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en'
</pre>
</div>
Notice how the query above matches fewer documents `totalCount:116` because we limited the free text query to the title field. We can 
change the [grammar](../reference/query-language-reference.html#grammar) to specify how the user query text is parsed into a query execution plan.
In the following example, we use `grammar:"all"` to specify that we only want to retrieve documents where *all* the query terms match the title field.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where {defaultIndex:"title", grammar:"all"}userInput(@user-query)' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en'
</pre>
</div>
This query, using `all`, matches only one document. Notice how the relevance of the hit is the same as in the above example. The difference
between the two types of queries is in the matching specification.

We can use `userInput` to build a query that searches multiple fields (or fieldsets):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where ({defaultIndex:"title", grammar:"all"}userInput(@user-query)) or ({defaultIndex:"url", grammar:"all"}userInput(@user-query))' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en'
</pre>
</div>

### Boosting by query terms 
Sometimes, we want to add a query time boost if some field matches a query term; the following uses the [rank](../reference/query-language-reference.html#rank) query operator.
The rank query operator allows us to retrieve using the first operand, and the remaining operands can only impact ranking. 

It is important to note that the following approach for query time term boosting is in the context of using the `nativeRank` text scoring feature.  

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="http://www.answers.com">
$ vespa query \
  'yql=select * from msmarco where rank(userInput(@user-query), url contains ({weight:1000, significance:1.0}"www.answers.com"))' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en'
</pre>
</div>
The above will match the user query against the default fieldset and produce match features for the second operand. It does not
change the *retrieval* or *matching* as the number of documents exposed to ranking is the same as before. The 
`rank` operator can be used to implement a variety of use case around boosting. 

#### Combine free text with filters
Now, we can combine the `userInput` with application logic.  We add an application-specific query filter on the `url` field 
to demonstrate how to combine `userInput` with other query time constraints. 
We add `ranked:false` to tell Vespa that this
specific term should not contribute to the relevance calculation and `filter`:true` to ensure that the term is not
used for [bolding/highlighting or dynamic snippeting](../document-summaries.html#dynamic-snippets).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where userInput(@user-query) and url contains ({filter:true,ranked:false}"huffingtonpost.co.uk")' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en'
</pre>
</div>

Notice that the `relevance` stays the same since we used `ranked:false` for the filter. 
Let us see what is going on by adding [query tracing](../query-api.html#query-tracing):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where userInput(@user-query) and url contains ({filter:true,ranked:false}"huffingtonpost.co.uk")' \
  'user-query=what is dad bod' \
  'trace.level=3' \
  'language=en'
</pre>
</div>

We can notice the following in the trace output:
<pre>
query=[AND (WEAKAND(100) default:what default:is default:dad default:bod) |url:'huffingtonpost co uk']
</pre>

Notice that the `userInput` part is converted to a [weakAnd](../using-wand-with-vespa.html) query operator and that this operator is 
AND'ed with a phrase search ('huffingtonpost co uk') in the `url` field. Notice also the field scoping where the query terms are
prefixed with `default`. Notice also that punctuation characters (.) are removed as part of the tokenization. Suppose this is a common pattern where we want to filter on specific strings. 
In that case, we should create a separate field to avoid phrase matching, phrase matching is more expensive than a single token search. 


### Debugging token string matching
Query tracing, combined with a summary using [tokens](../reference/schema-reference.html#tokens) can help debug matching. 
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="what-is-a-dadbod">
$ vespa query \
  'yql=select * from msmarco where url contains ({filter:true,ranked:false}"huffingtonpost.co.uk")' \
  'trace.level=0' \
  'language=en' \
  'summary=url-tokens'
</pre>
</div>

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
                "relevance": 0.0,
                "source": "msmarco",
                "fields": {
                    "sddocname": "msmarco",
                    "url": "http://www.huffingtonpost.co.uk/2015/05/05/what-is-a-dadbod-male-body_n_7212072.html",
                    "url-tokens": [
                        "http",
                        "www",
                        "huffingtonpost",
                        "co",
                        "uk",
                        "2015",
                        "05",
                        "05",
                        "what",
                        "is",
                        "a",
                        "dadbod",
                        "male",
                        "body",
                        "n",
                        "7212072",
                        "html"
                    ]
                }
            }
        ]

    }
}
{% endhighlight %}</pre>
This gives us insight into how the input `url` field was tokenized and indexed. Those are the tokens that the query can match. 
Notice how punctuation characters like `:`, `,`, `.`, `/`, `_` and `-` are removed as part of the text tokenization. 

Observations:

- Relevance is 0.0, because the term uses `ranked:false`. 
- We cannot match "://" because those are not searchable characters with `match:text`
- `dadbod` is a token in the url, this cannot match `dad` or `bod` as it is represented as a single token `dadbod`.

Let us do a similar example to demonstrate the impact of linguistic stemming

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="996">
$ vespa query \
  'yql=select * from msmarco where url contains ({filter:true,ranked:false}"http")' \
  'summary=url-tokens' \
  'language=en'
</pre>
</div>


<pre>
 "url": "http://www.ourbabynamer.com/meaning-of-Anika.html",
  "url-tokens": [
    "http",
    "www",
    "ourbabynamer",
    "com",
    "meaning",
    "of",
    "anika",
    "html"
  ]
</pre>
Notice that a query for `https` matches `http`, because 'https' on the query is stemmed to `http`.  
If we `turn off` stemming on` the query side, searching for `https` directly, we
end up with 0 results. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="0">
$ vespa query \
  'yql=select * from msmarco where url contains ({filter:true,ranked:false,stem:false}"https")' \
  'summary=debug-tokens' \
  'language=en'
</pre>
</div>

Similarly, if we pass a different language tag, which will not stem https to http, we also get 0 results:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="0">
$ vespa query \
  'yql=select * from msmarco where url contains ({filter:true,ranked:false}"https")' \
  'summary=debug-tokens' \
  'language=de'
</pre>
</div>

## Ranking
 The previous section covered free-text search matching, linguistics, and how to combine business logic with 
 free-text user queries. All the examples used a `default` rank-profile using Vespa's [nativeRank](../nativerank.html) text scoring feature.

 With free-text search, we can use other text scoring functions, like [BM25](../reference/bm25.html). All the matching 
 capabilities (or limitations) still apply, we can use fieldsets or fields; the difference is in the text scoring function where BM25
 is different from nativeRank.

 <div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where userInput(@user-query)' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en' \
  'ranking=bm25'
</pre>
</div> 

While the `nativeRank` text score is normalized to the range 0 to 1, BM25 is unbounded, as demonstrated above. When 
querying (matching), we can ask Vespa to compute both features in the same query. 

Modify the schema and add a new rank-profile `combined`:

<pre data-test="file" data-path="text-search/app/schemas/msmarco.sd">
schema msmarco {
    document msmarco {
        field language type string {
            indexing: "en" | set_language 
        }
        field id type string {
            indexing: attribute | summary
            match: word
        }
        field title type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
        field body type string {
            indexing: index
            match: text
            index: enable-bm25
        }
        field url type string {
            indexing: index | summary
            index: enable-bm25
        }
    }
    fieldset default {
        fields: title, body, url
    }
    document-summary minimal {
        summary id {  }
    }
    document-summary url-tokens {
        summary url {}
        summary url-tokens {
            source: url
            tokens
        }
        from-disk
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

    rank-profile combined inherits default {
        first-phase {
            expression: bm25(title) + bm25(body) + bm25(url) + nativeRank(title) + nativeRank(body) + nativeRank(url)
        }
        match-features { 
          bm25(title)
          bm25(body)
          bm25(url)
          nativeRank(title)
          nativeRank(body)
          nativeRank(url)
        }
    }
}
</pre>

Then, re-deploy the Vespa application from the `app` directory:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 app
</pre>
</div>

Adding or removing rank profiles is a live-change as it only impacts how we score documents, not how we index or match
them.

Run a query with the new rank-profile:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where userInput(@user-query)' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en' \
  'ranking=combined'
</pre>
</div> 

Which will produce a result like this:

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
                "id": "id:msmarco:msmarco::D2977840",
                "relevance": 25.482783473796484,
                "source": "msmarco",
                "fields": {
                    "matchfeatures": {
                        "bm25(body)": 19.51565699523739,
                        "bm25(title)": 4.978933753876959,
                        "bm25(url)": 0.3678926381724701,
                        "nativeRank(body)": 0.3010929113058281,
                        "nativeRank(title)": 0.24814575272673867,
                        "nativeRank(url)": 0.07106142247709807
                    },
                    "sddocname": "msmarco",
                    "documentid": "id:msmarco:msmarco::D2977840",
                    "id": "D2977840",
                    "title": "What Is A  Dad Bod   An Insight Into The Latest Male Body Craze To Sweep The Internet",
                    "url": "http://www.huffingtonpost.co.uk/2015/05/05/what-is-a-dadbod-male-body_n_7212072.html"
                }
            }
        ]

    }
}
{% endhighlight %}</pre>
Notice that `matchfeatures` field that is added to the hit when using `match-features` in the rank-profile. Here, we have all the computed features from the matched document, and the final `relevance` score is the sum of these features (In this case).
This query and ranking example demonstrates that for a single query searching a set of fields via fieldset, 
we can compute different types of text scoring features and use combinations. 

Now consider the following where we limit matching to the title field:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="What Is A  Dad Bod">
$ vespa query \
  'yql=select * from msmarco where {defaultIndex:"title"}userInput(@user-query)' \
  'user-query=what is dad bod' \
  'hits=3' \
  'language=en' \
  'ranking=combined'
</pre>
</div> 

Now, we do not get features for `body` or `url`, because they were not matched by the query.  

## Next steps
Check out the [Improving Text Search through ML](text-search-ml.html).

## Cleanup
If do not want to proceed with the [Improving Text Search through ML](text-search-ml.html) guide, you can 
stop and remove the container (and data):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="after">
$ docker rm -f vespa-msmarco
</pre>
</div>


[^1]: Robertson, Stephen and Zaragoza, Hugo and others, 2009. The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval.

<script src="/js/process_pre.js"></script>
