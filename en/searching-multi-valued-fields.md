---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Searching and ranking of multi-valued fields"
---

This guide explores how to search and rank over structured multi-valued fields. 

## Introduction

When building a search application we need to think about

- How to [match](query-language.html) a user query against our document schema  
- How to [rank](ranking.html) documents matching the query 

During the matching or retriveal stage, Vespa calculates several matching ranking features 
which can influence the order of the documents retrieved. This process is called ranking. A
single query request might retrieve documents into ranking by multiple different strategies combing
the strategies using logica disjunction (OR): 


### Matching

There is a lot of matching options we should think about when 
designing both our document schema and the way we query the schema

- For string fields we need to decide if we want to use text style matching or database style exact matching?
- For free text string fields, should we disable 
linguistic processing like tokenization, normalization and language dependent stemming?
- String fields which shares the same match and linguistic processing settings can be combined using fieldset. 
- Should query matching in the field impact ranking, or is it just a filter which should not impact ranking order?

At query time, we can take the user query and translate it into a valid Vespa query request which implements
our matching and retriveal strategy. 

### Ranking 

The documents which matches the query and is retrieved by the query expression is ranked. Once a document
is retrieved by the query logic one has access to the full flexibility of the Vespa ranking framework. In the
following section we demonstrate both retriveal and ranking. 

## Prerequisites
- [Docker Desktop on Mac](https://docs.docker.com/docker-for-mac/install) 
  or Docker on Linux
- Operating system: macOS or Linux
- Architecture: x86_64
- [Homebrew](https://brew.sh/) to install [Vespa CLI](https://docs.vespa.ai/en/vespa-cli.html), or download 
 a vespa cli release from [Github releases](https://github.com/vespa-engine/vespa/releases).

## A minimal Vespa application

Assuming we have the following sample data document

<pre data-test="file" data-path="doc.json"> 
{
    "put": "id:photos:photo::0",
    "fields": {
        "title": "Mira in the sunset",
        "description": "A sunny afternoon with our dogs",
        "interestingness": 0.23,
        "tags": {
            "#sunny": 1,
            "no filter":1,
            "light": 3,
            "black and white": 3,
            "clear sky": 2,
            "sunset dogs": 4
        }
    }
}
</pre>

How should we design our Vespa schema, and how should we match and search this data model for 
end user free text queries? 

- We want to use traditional text matching when searching the title and description
- We also want to match the free form tags field as these tags might increase recall and the weight might
impact the ranking. 

We can start with the following schema:

<pre data-test="file" data-path="my-app/schemas/photo.sd"> 
schema photo {

  stemming: none 
  
  document photo {

    field title type string {
      indexing: summary | index
      match:text 
      index: enable-bm25
    }

    field description type string {
      indexing: summary | index
      match:text
      index: enable-bm25
    }

    field interestingness type float {
      indexing: summary | attribute
    }

    field tags type weightedset&lt;string&gt; {
      indexing: summary | index
      match:text
      index: enable-bm25
    }

  }
  fieldset default {
    fields: title, description, tags
  }
}
</pre>
We disable [stemming](reference/schema-reference.html#stemming) and
also enable [bm25](reference/bm25.html) ranking for all string fields. 
Since all string fields shares the same [match](reference/schema-reference.html#match)
settings we can use a [fieldset](reference/schema-reference.html#fieldset) 
so that searches does not need to mention all 3 fields we plan to match against. Along with the 
schema, we also need a [services.xml](reference/services.html) file to deploy the application:

<pre data-test="file" data-path="my-app/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

    &lt;container id="default" version="1.0"&gt;
        &lt;search&gt;&lt;/search&gt;
        &lt;document-api&gt;&lt;/document-api&gt;
        &lt;nodes&gt;
            &lt;node hostalias="node1"&gt;&lt;/node&gt;
        &lt;/nodes&gt;
    &lt;/container&gt;

    &lt;content id="photos" version="1.0"&gt;
        &lt;redundancy&gt;1&lt;/redundancy&gt;
        &lt;documents&gt;
            &lt;document type="photo" mode="index"/&gt;
        &lt;/documents&gt;
        &lt;nodes&gt;
            &lt;node hostalias="node1" distribution-key="0" /&gt;
        &lt;/nodes&gt;
    &lt;/content&gt;

&lt;/services&gt;
</pre>

## Starting Vespa

This example uses docker container:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker pull vespaengine/vespa
$ docker run --detach --name vespa --hostname vespa-container \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa
</pre>
</div>

Install [Vespa-cli](vespa-cli.html):

<pre>
brew install vespa-cli
</pre>

Deploy the application using vespa-cli:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>

## Feeding to Vespa

Feed the sample document 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa document -v doc.json 
</pre>
</div>

## Query our data
Assuming a free text query *sunset photos featuring dogs*, we translate the user query into
a Vespa query reques using YQL:

<pre data-test="exec" data-test-assert-contains='"totalCount": 0'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=sunset photos featuring dogs' 
</pre>

The above query returns 0 hits, since by default query will require that *all* query terms matches the document. 
By adding [tracelevel](reference/query-api-reference.html#tracelevel) to the request we can see this:

<pre data-test="exec" data-test-assert-contains='"totalCount": 0'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=sunset photos featuring dogs' 'tracelevel=3'
</pre>

<pre>
query=[AND sunshot photos featuring dogs]
</pre>

 Since our sample document does not contain the term *featuring* or *photos*, the query fails to retrieve the example document. 
 We can relax the query matching to instead of requiring that **all** terms match, to use **any**. See
 [model.type](reference/query-api-reference.html#model.type) query api reference for supported query types.

<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=sunshot photos featuring a dog' 'type=any'
</pre>

Changing the type to any, brings back the document as we don't require that all query terms needs to match.

Now, let us explore how Vespa matches the multi-valued tags field of 
type [weightedset](reference/schema-reference.html#weightedset).

<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=clear sky' 'type=all' 'default-index=tags'
</pre>

Matches, there is a tag with exactly that content so there is a match. Let us
search for just *clear* instead:

<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=clear' 'type=all' 'default-index=tags'
</pre>

Also matches the document. But what about 'black sky'? 

<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=black sky' 'type=all' 'default-index=tags'
</pre>

Also matches our document, since all elements of the tag field is indexed as a bag of words, we
get matches across elements. This might be a good decision, as we increase recall, however
in some cases we want to differentiate an exact match from a partial match during ranking.  


## Ranking
We have now explored matching, now it's time to focus on how we want to rank the documents matched. 

We start with having Vespa calculate [ranking features](reference/rank-features.html), then we can explore
and create a baseline ranking function. We use `match-features` to return calculated ranking features.
These are all built-in ranking features which Vespa exposes:

<pre data-test="file" data-path="my-app/schemas/photo.sd"> 
schema photo {

  stemming: none

  document photo {

    field title type string {
      indexing: summary | index
      match:text
    }

    field description type string {
      indexing: summary | index
      match:text
    }

    field interestingness type float {
      indexing: summary | attribute
    }

    field tags type weightedset&lt;string&gt; {
      indexing: summary | index
      match:text
    }

  }

  fieldset default {
    fields: title, description, tags
  }

  rank-profile default {
    first-phase {
      expression: nativeRank
    }
    match-features {
      bm25(title)
      bm25(description)
      bm25(tags)

      nativeRank
      nativeRank(title)
      nativeRank(description)

      attribute(interestingness)

      elementSimilarity(tags)
      elementCompleteness(tags).elementWeight
      elementCompleteness(tags).fieldCompleteness
      elementCompleteness(tags).queryCompleteness
      elementCompleteness(tags).completeness
    }
  }
}
</pre>

Re-deploy with the new ranking profile

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>


<pre data-test="exec" data-test-assert-contains='matchfeatures'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=black sky' 'type=any'
</pre>
<script src="/js/process_pre.js"></script>
