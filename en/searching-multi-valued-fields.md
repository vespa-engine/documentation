---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Searching and ranking of multi-valued fields"
---

This guide explores how to search and rank over structured multi-valued fields. 

## Introduction

When building a search application we need to think about

- How to [match](query-language.html) a user query against our document schema  
- How to [rank](ranking.html) documents matching the query 

During the matching or retriveal stage, Vespa calculates several matching rank features 
which can influence the order of the documents retrieved. This process is called ranking. A
single query request might retrieve documents using multiple different 
retriveal strategies combined using logical disjunction (OR).

### Matching

There is a lot of text matching options we should think about when 
designing and mapping or document model to a Vespa document schema:

- For string fields we should think about using text style matching or database-style exact matching.
- For string fields there are also several
[linguistic processing](linguistics.html) options like [tokenization](linguistics.html#tokenization), 
normalization and language dependent [stemming](linguistics.html#stemming).
- String fields which shares the same [match](reference/schema-reference.html#match) 
and linguistic processing settings can be combined using [fieldsets](reference/schema-reference.html#fieldset). 

At query time, we can take the user query and translate it into a valid Vespa query request which implements
our matching and retrieval strategy over the designed document schema.

### Ranking 

The documents which matches the query and is retrieved by the query is scored using a ranking model. 
Once a document is retrieved by the query logic the document can be scored using the full 
flexibility of the Vespa [ranking](ranking.html) framework. 

## Exploration

In the following sections we explore matching and ranking over multi-valued string fields.  

### Prerequisites
- [Docker Desktop on Mac](https://docs.docker.com/docker-for-mac/install) 
  or Docker on Linux
- Operating system: macOS or Linux
- Architecture: x86_64
- [Homebrew](https://brew.sh/) to install [Vespa CLI](https://docs.vespa.ai/en/vespa-cli.html), or download 
 a vespa cli release from [Github releases](https://github.com/vespa-engine/vespa/releases).

### A minimal Vespa application

Assuming we have the following sample data document where we have a structured
tag-like field where there is a weight associated with each element. 

<pre data-test="file" data-path="doc.json"> 
{
    "put": "id:photos:photo::0",
    "fields": {
        "title": "Mira in the sunset",
        "description": "A sunny afternoon with our dogs",
        "tags": {
            "no filter":1,
            "light": 3,
            "black and white": 3,
            "clear sky": 2,
            "sunset dogs": 4
        }
    }
}
</pre>

Structured data like the <code>tags</code>, where we both want to match and rank is best represented using 
the [weightedset](reference/schema-reference.html#type:weightedset)
[field type](reference/schema-reference.html#field-types). The Vespa weightedset field type can be used to represent:

- Document side tags like in the above example
- [Document expansion by query prediction](https://github.com/castorini/docTTTTTquery)  
- Editoral ranking overrides, for example sponsored search listings.

How should we design our Vespa schema, and how should we match and search this data model for 
end user free text queries? 

- We want to use text matching when searching the title and description
- We also want to match the free form tags field as these tags might increase recall and the weight of the matched
element(s) could influence scoring and ranking. We can start with the following schema:
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
  rank-profile default {
    first-phase {
      expression: nativeRank
    }
  }
}
</pre>

In the schema we disable [stemming](reference/schema-reference.html#stemming) and
also enable [bm25](reference/bm25.html) text ranking fature for all string fields.

Since all string fields shares the same [match](reference/schema-reference.html#match)
settings we can use a [fieldset](reference/schema-reference.html#fieldset) 
so that queries does not need to mention all three fields.

We also include a default ranking profile (this is the implicit default ranking profile)
using the Vespa [nativeRank](nativerank.html) text ranking feature.

Along with the schema, we also need a [services.xml](reference/services.html) file:

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

### Starting Vespa

This example uses the vespa container image:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker pull vespaengine/vespa
$ docker run --detach --name vespa --hostname vespa-container \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa
</pre>
</div>

Install [Vespa-cli](vespa-cli.html) using Homebrew:

<pre>
brew install vespa-cli
</pre>

Now we can deploy the application using vespa-cli:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>

### Feeding to Vespa

Feed the sample document 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa document -v doc.json 
</pre>
</div>

### Query our data
Assuming a free text query *sunset photos featuring dogs*, we translate the user query into
a Vespa query reques using YQL:

<pre data-test="exec" data-test-assert-contains='"totalCount": 0'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=sunset photos featuring dogs' 
</pre>

The above query returns 0 hits, since by default query will require that *all* query terms matches the document. 
By adding [tracelevel](reference/query-api-reference.html#tracelevel) to the query request we can see this:

<pre data-test="exec" data-test-assert-contains='"totalCount": 0'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=sunset photos featuring dogs' 'tracelevel=3'
</pre>

In the trace we can see the query which is dispatched to the content nodes:

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

Changing the type to `any`, recalls our sample document as we no longer require that all query terms needs to match.

Now, let us explore how Vespa matches the multi-valued tags field of 
type [weightedset](reference/schema-reference.html#weightedset). Notice that we change
back to default `type=all`. 
In this example we also use the [default-index](reference/query-api-reference.html#model.defaultIndex) 
parameter to limit matching to the `tags` field.

<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=clear sky' 'type=all' 'default-index=tags'
</pre>

The query matches the document which is no surprise since a tag contains the exact content `clear sky`.
Let us search for just `clear` instead:

<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=clear' 'type=all' 'default-index=tags'
</pre>

Also matches the document, this demonstrates that matching is partial, it does not require
to match the element exactly. `clear` matches `clear sky` and `sky` will match `clear sky`.  

But what about `black sky`:

<pre data-test="exec" data-test-assert-contains='"totalCount": 1'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=black sky' 'type=all' 'default-index=tags'
</pre>

Also matches our document. This is an example of cross-element matching. With weightedset
usig `indexing:index` with `match:text` multi term queries match across elements. 

This might be a good decision, as we increase recall, however
in some cases we want to differentiate an exact match from a partial match during ranking, so that
exact matches are ranked higher than partial matches. This is however highly domain-dependent. 

### Ranking

We have now explored matching, now it's time to focus on how we want to rank the documents matched. 
You might not have noticed, but in the above examples, each of the queries produced a `relevance` score, 
this score was in our previous examples calculated using the `default` ranking profile which in our case
used [nativeRank](nativerank.html). 
We can start by analyzing other [rank features](reference/rank-features.html) we can ask Vespa to produce
for us.We use [match-features](reference/schema-reference.html#match-features) to return 
rank features with the retrieved documents. We explicit mention which ranking features we want to have calculated
and returned. Notice that we don't change the actual scoring, we still use `nativeRank` as the scoring function.
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

      elementSimilarity(tags)
      elementCompleteness(tags).elementWeight
      elementCompleteness(tags).fieldCompleteness
      elementCompleteness(tags).queryCompleteness
      elementCompleteness(tags).completeness
    }
  }
}
</pre>

Re-deploy with the changed ranking profile:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>

Now we will see a list of features in the response:
<pre data-test="exec" data-test-assert-contains='matchfeatures'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=clear sky' 'type=any'
</pre>

The output includes `matchfeatures` where we can see the various scores for the features:

Especially look at the `elementCompleteness` and `elementSimilarity` rank features which
are example of [features for indexed multivalued string 
fields](reference/rank-features.html#features-for-indexed-multivalue-string-fields).

We can also notice that `elementCompleteness(tags).fieldCompleteness` is 1.0 which means 
that the tag was matched exactly and the `"elementCompleteness(tags).elementWeight` outputs
the weight of the best matched element. 

The `elementSimilarity(tags)` ranking feature is very flexible and even allow us to override
the [calculation and output new features](reference/rank-feature-configuration.html#elementSimilarity). 

In this example we produce two new ranking feature

- `elementSimilarity(tags).sumWeight` which uses the sum of matching elements using field completeness x weight.
- `elementSimilarity(tags).maxWeight` which uses the max over the matching elements using field completeness x weight.


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

  rank-profile default {
    rank-properties {
      elementSimilarity(tags).output.sumWeight: "sum(f*w)"
      elementSimilarity(tags).output.maxWeight: "max(f*w)"
    }
   
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

      elementSimilarity(tags)
      elementSimilarity(tags).sumWeight
      elementSimilarity(tags).maxWeight

      elementCompleteness(tags).elementWeight
      elementCompleteness(tags).fieldCompleteness
      elementCompleteness(tags).queryCompleteness
      elementCompleteness(tags).completeness
    }
  }
}
</pre>

Re-deploy with the changed ranking profile:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>

Now we will see a list of features in the response:
<pre data-test="exec" data-test-assert-contains='matchfeatures'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=clear sky' 'type=any'
</pre>

The output includes `matchfeatures` where we can see the various scores for the features:


Now, we can include these features in a ranking expression used in `first-phase`. The actual
best function is data dependend, and a trained function using machine learned ranking is by far the
easiest way. The bag of words [bm25](reference/bm25.html) ranking feature is not normalized so combining
it in a linear function is challenging as the score range is unbound. We can make the parameters in our function
overridable on a per query basis by 

<pre>
  first-phase {
    expression {
      query(titleWeight)*bm25(title) + query(descriptionWeight)*bm25(description) +
      query(tagWeight)*elementSimilarity(tags).maxWeight
    }
  }
</pre>


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

  rank-profile tunable inherits default {
    rank-properties {
      query(titleWeight): 2
      query(descriptionWeight): 1
      query(tagWeight): 2

      elementSimilarity(tags).output.sumWeight: "sum(f*w)"
      elementSimilarity(tags).output.maxWeight: "max(f*w)"
    }
   
    first-phase {
      expression {
        query(titleWeight)*bm25(title) + query(descriptionWeight)*bm25(description) +
        query(tagWeight)*elementSimilarity(tags).maxWeight
      }
    }

    match-features {
      bm25(title)
      bm25(description)
      bm25(tags)
      elementSimilarity(tags).maxWeight
      firstPhase
    }
  }
}
</pre>

Re-deploy

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>

Run a query with the new ranking profile

<pre data-test="exec" data-test-assert-contains='"relevance": 4.0'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=clear sky' 'type=any' 'ranking=tunable' 
</pre>

With the function above, since 'clear sky' does not match any of the title or description
fields, the bm25 features are 0 for those fields.  
Our `elementSimilarity(tags).maxWeight` feature is 2.0 and the first phase
expression becomes 4 which is reflected in the hit relevance score.

Change the tagWeight and observe that the relevance becomes 6.0

<pre data-test="exec" data-test-assert-contains='"relevance": 6.0'>
$ vespa query 'yql=select * from photos where userQuery()' \
 'query=clear sky' 'type=any' 'ranking=tunable' \
 'ranking.features.query(tagWeight)=3' 
</pre>

That concludes our matching and ranking experiments. To shutdown the container run:

<pre data-test="after">
$ docker rm -f vespa
</pre>

## Conclusion
In this guide we have looked at how one can build a query retrieval strategy and how to change ranking 
when searching multi-valued fields using the weightedset field type. A natural continuation is to look
at how to use the many rank features by learning a ranking function. See for example
[learning to rank](learning-to-rank.html) and [improving text search through ML](tutorials/text-search-ml.html). 


<script src="/js/process_pre.js"></script>
