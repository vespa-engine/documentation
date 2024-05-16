---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Hybrid Text Search Tutorial"
redirect_from:
- /documentation/tutorials/hybrid-search.html
---

This tutorial will guide you through setting up a hybrid text search application. 
The main goal is to set up a text search app that combines simple text scoring features
such as [BM25](../reference/bm25.html) [^1] with vector search in combination with text-embedding models. We 
demonstrate obtaining the text embeddings within Vespa using Vespa's [embedder](https://docs.vespa.ai/en/embedding.html#huggingface-embedder)
functionality. In this guide, we use [snowflake-arctic-embed-xs](https://huggingface.co/Snowflake/snowflake-arctic-embed-xs) as the 
text embedding model.

For demonstration purposes, we use the small IR dataset that is part of the [BEIR](https://github.com/beir-cellar/beir) benchmark: [NFCorpus](https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/). The BEIR version has 2590 train queries, 323 test queries, and 3633 documents. In these experiments
we only use the test queries to evaluate various hybrid search techniques. Later tutorials will demonstrate how to use the train split to learn how to rank documents. 

{% include pre-req.html memory="4 GB" extra-reqs='
<li>Python3</li>
<li><code>curl</code></li>' %}

## Installing vespa-cli and ir_datasets

This tutorial uses [Vespa-CLI](../vespa-cli.html) to deploy, feed, and query Vespa. We also use 
[ir-datasets](https://ir-datasets.com/) to obtain the dataset.
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ pip3 install --ignore-installed vespacli ir_datasets
</pre>
</div>

We can quickly look at a document from [nfcorpus](https://ir-datasets.com/beir.html#beir/nfcorpus):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="MED-10">
$ ir_datasets export beir/nfcorpus docs --format jsonl | head -1
</pre>
</div> 

Which outputs:

<pre>{% highlight json%}
{"doc_id": "MED-10", "text": "Recent studies have suggested that statins, an established drug group in the prevention of cardiovascular mortality, could delay or prevent breast cancer recurrence but the effect on disease-specific mortality remains unclear. We evaluated risk of breast cancer death among statin users in a population-based cohort of breast cancer patients. The study cohort included all newly diagnosed breast cancer patients in Finland during 1995\u20132003 (31,236 cases), identified from the Finnish Cancer Registry. Information on statin use before and after the diagnosis was obtained from a national prescription database. We used the Cox proportional hazards regression method to estimate mortality among statin users with statin use as time-dependent variable. A total of 4,151 participants had used statins. During the median follow-up of 3.25 years after the diagnosis (range 0.08\u20139.0 years) 6,011 participants died, of which 3,619 (60.2%) was due to breast cancer. After adjustment for age, tumor characteristics, and treatment selection, both post-diagnostic and pre-diagnostic statin use were associated with lowered risk of breast cancer death (HR 0.46, 95% CI 0.38\u20130.55 and HR 0.54, 95% CI 0.44\u20130.67, respectively). The risk decrease by post-diagnostic statin use was likely affected by healthy adherer bias; that is, the greater likelihood of dying cancer patients to discontinue statin use as the association was not clearly dose-dependent and observed already at low-dose/short-term use. The dose- and time-dependence of the survival benefit among pre-diagnostic statin users suggests a possible causal effect that should be evaluated further in a clinical trial testing statins\u2019 effect on survival in breast cancer patients.", "title": "Statin Use and Breast Cancer Survival: A Nationwide Cohort Study from Finland", "url": "http://www.ncbi.nlm.nih.gov/pubmed/25329299"}
{% endhighlight %}</pre>

The NFCorpus documents have four fields

- The `doc_id` and `url` 
- The `text` and the `title` 

We are interested in the title and the text, and we want to be able to search across these two fields. We also need to store the `doc_id` to evaluate [ranking](../ranking.html)
accuracy. We will create a small script that converts the above output to Vespa JSON feed format. Create a `convert.py` file:

<div class="pre-parent">
<button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="file" data-path="convert.py">
import sys
import json

for line in sys.stdin:
  doc = json.loads(line)
  del doc['url']
  vespa_doc = {
    "put": "id:hybrid-search:doc::%s" % doc['doc_id'],
    "fields": {
      **doc
    }
  }
  print(json.dumps(vespa_doc))
</pre>
</div>


Then we can export the documents using ir_datasets and pipe it to the `convert.py` script:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ir_datasets export beir/nfcorpus docs --format jsonl | python3 convert.py > vespa-docs.jsonl
</pre>
</div> 


## Create a Vespa Application Package

A [Vespa application package](../application-packages.html) is a set of configuration files and optional Java components that together define the behavior of a Vespa system. Let us define the minimum set of required files to create our hybrid text search application: `doc.sd` and `services.xml`.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ mkdir -p app/schemas
</pre>
</div>


### Schema
A [schema](../schemas.html) is a document-type configuration; a single vespa application can have multiple schemas with document types.
For this application, we define a schema `doc` which must be saved in a file named `schemas/doc.sd` in the app directory.
Write the following to `app/schemas/doc.sd`:

<pre data-test="file" data-path="app/schemas/doc.sd">
schema doc {
    document doc {
        field language type string {
            indexing: "en" | set_language 
        }
        field doc_id type string {
            indexing: attribute | summary
            match: word
        }
        field title type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
        field text type string {
            indexing: index
            match: text
            index: enable-bm25
        }
    }
    fieldset default {
        fields: title, text
    }
    
    field embedding type tensor&lt;bfloat16&gt;(v[384]) {
      indexing: input title . " " . input text | embed | summary | attribute
      attribute: {
        distance-metric: angular
      }
    }
  
    rank-profile bm25 {
        first-phase {
            expression: bm25(title) + bm25(text)
        }
    }

    rank-profile semantic {
        inputs {
          query(e) tensor&lt;bfloat16&gt;(v[384])
        }
        first-phase {
            expression: closeness(field, embedding)
        }
    }
}
</pre>
A lot is happening here; let us go through it in detail. 

#### Document type and fields
The `document` section contains the fields of the document, their types, and how Vespa should index and [match](reference/schema-reference.html#match) them.

The field property `indexing` configures the _indexing pipeline_ for a field.
For more information, see [schemas - indexing](../schemas.html#indexing).
The [string](../reference/schema-reference.html#string) data type represents both unstructured and structured texts, 
and there are significant differences between [index and attribute](../text-matching.html#index-and-attribute). The above
schema includes default `match` modes for `attribute` and `index` property for visibility.  

Note that we are enabling the usage of [BM25](../reference/bm25.html) for `title` and `text`.
by including `index: enable-bm25`. The language field is the only field not in the NFCorpus dataset. 
We hardcode its value to "en" since the dataset is English. Using `set_language` avoids automatic language detection and uses the value when processing the other
text fields. Read more in [linguistics](../linguistics.html).

#### Fieldset for matching across multiple fields

[Fieldset](../reference/schema-reference.html#fieldset) allows searching across multiple fields. Defining `fieldset` does not 
add indexing/storage overhead. String fields grouped using fieldsets must share the same 
[match](../reference/schema-reference.html#match) and [linguistic processing](../linguistics.html) settings because
the query processing that searches a field or fieldset uses *one* type of transformation.


#### Ranking to determine matched documents ordering
You can define many [rank profiles](../ranking.html), 
named collections of score calculations, and ranking phases.

In this basic starting point, we have a `bm25` rank-profile that uses [bm25](../reference/bm25.html). We sum the two field-level BM25 scores
using a Vespa [ranking expression](../ranking-expressions-features.html). This example uses a single [ranking phase](../phased-ranking.html).

Then we have a `semantic` rank-profile which is used in combination with nearestNeighbor query operator (vector search).

### Services Specification

The [services.xml](../reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.
Write the following to `app/services.xml`:

<pre data-test="file" data-path="app/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

    &lt;container id="default" version="1.0"&gt;
        &lt;search /&gt;
        &lt;document-processing /&gt;
        &lt;document-api /&gt;
        &lt;component id=&quot;arctic&quot; type=&quot;hugging-face-embedder&quot;&gt;
          &lt;transformer-model url=&quot;https://huggingface.co/Snowflake/snowflake-arctic-embed-xs/resolve/main/onnx/model_quantized.onnx&quot;/&gt;
          &lt;tokenizer-model url=&quot;https://huggingface.co/Snowflake/snowflake-arctic-embed-xs/raw/main/tokenizer.json&quot;/&gt;
          &lt;pooling&gt;cls&lt;/pooling&gt;
          &lt;prepend&gt;
            &lt;query&gt;Represent this sentence for searching relevant passages: &lt;/query&gt;
          &lt;/prepend&gt;
      &lt;/component&gt;
    &lt;/container&gt;

    &lt;content id="content" version="1.0"&gt;
        &lt;min-redundancy&gt;1&lt;/min-redundancy&gt;
        &lt;documents&gt;
            &lt;document type="doc" mode="index" /&gt;
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
- `component` with type `hugging-face-embedder` configures the embedder in the application package. This include where to fetch the model files from, the prepend
instructions, and the pooling strategy. 
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
$ docker run --detach --name vespa-hybrid --hostname vespa-container \
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


<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa feed -t http://localhost:8080 vespa-docs.jsonl
</pre>
</div>


<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="after">
$ docker rm -f vespa-hybrid
</pre>
</div>



[^1]: Robertson, Stephen and Zaragoza, Hugo and others, 2009. The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval.

<script src="/js/process_pre.js"></script>

