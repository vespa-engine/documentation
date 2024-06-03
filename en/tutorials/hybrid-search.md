---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Hybrid Text Search Tutorial"
redirect_from:
- /documentation/tutorials/hybrid-search.html
---

This tutorial will guide you through setting up a hybrid text search application. 
The main goal is to set up a text search app that combines simple text scoring features
such as [BM25](../reference/bm25.html) [^1] with vector search in combination with text-embedding models. 
We demonstrate how to obtain text embeddings within Vespa using Vespa's [embedder](https://docs.vespa.ai/en/embedding.html#huggingface-embedder)
functionality. In this guide, we use [snowflake-arctic-embed-xs](https://huggingface.co/Snowflake/snowflake-arctic-embed-xs) as the 
text embedding model. 

For demonstration purposes, we use the small IR dataset that is part of the [BEIR](https://github.com/beir-cellar/beir) benchmark: [NFCorpus](https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/). The BEIR version of this dataset has 2590 train queries, 323 test queries, and 3633 documents. In these experiments
we only use the test queries. Later tutorials will demonstrate how to use the train split to learn how to rank documents. 

{% include pre-req.html memory="4 GB" extra-reqs='
<li>Python3</li>
<li><code>curl</code></li>' %}

## Installing vespa-cli and ir_datasets

This tutorial uses [Vespa-CLI](../vespa-cli.html) to deploy, feed, and query Vespa. We also use 
[ir-datasets](https://ir-datasets.com/) to obtain the dataset.
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ pip3 install --ignore-installed vespacli ir_datasets ir_measures
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
<pre data-test="file" data-path="convert.py">{% highlight python %}
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
  print(json.dumps(vespa_doc)){% endhighlight %}</pre>
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

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
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
            indexing: index | summary
            match: text
            index: enable-bm25
        }
    }
    fieldset default {
        fields: title, text
    }
    
    field embedding type tensor&lt;bfloat16&gt;(v[384]) {
      indexing: input title." ".input text | embed | attribute
      attribute {
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
</div>
A lot is happening here; let us go through it in detail. 

#### Document type and fields
The `document` section contains the fields of the document, their types, and how Vespa should index and [match](reference/schema-reference.html#match) them.

The field property `indexing` configures the _indexing pipeline_ for a field.
For more information, see [schemas - indexing](../schemas.html#indexing).
The [string](../reference/schema-reference.html#string) data type represents both unstructured and structured texts, 
and there are significant differences between [index and attribute](../text-matching.html#index-and-attribute). The above
schema includes default `match` modes for `attribute` and `index` property for visibility.  

Note that we are enabling [BM25](../reference/bm25.html) for `title` and `text`.
by including `index: enable-bm25`. The language field is the only field not in the NFCorpus dataset. 
We hardcode its value to "en" since the dataset is English. Using `set_language` avoids automatic language detection and uses the value when processing the other
text fields. Read more in [linguistics](../linguistics.html).

#### Fieldset for matching across multiple fields

[Fieldset](../reference/schema-reference.html#fieldset) allows searching across multiple fields. Defining `fieldset` does not 
add indexing/storage overhead. String fields grouped using fieldsets must share the same 
[match](../reference/schema-reference.html#match) and [linguistic processing](../linguistics.html) settings because
the query processing that searches a field or fieldset uses *one* type of transformation.

#### Embedding inference
Our `embedding` field is a [tensor](../tensor-user-guide.html) with a single dense dimension of 384 values. 

```
field embedding type tensor<bfloat16>(v[384]) {
      indexing: input title." ".input text | embed arctic | attribute
      attribute {
        distance-metric: angular
      }
    }
```
The `indexing` expression creates the input to the `embed` inference call (in our example the concatenation of the title and the text field). Since
the dataset is small, we do not specify `index` which would build [HNSW](../approximate-nn-hnsw.html) datastructures for faster (but approximate) vector search. This guide uses [snowflake-arctic-embed-xs](https://huggingface.co/Snowflake/snowflake-arctic-embed-xs) as the text embedding model. The model is
trained with cosine similarity, which maps to Vespa's `angular` [distance-metric](../reference/schema-reference.html#distance-metric) for 
nearestNeighbor search. 

#### Ranking to determine matched documents ordering
You can define many [rank profiles](../ranking.html), 
named collections of score calculations, and ranking phases.

In this starting point, we have two simple rank-profile's:
- a `bm25` rank-profile that uses [bm25](../reference/bm25.html). We sum the two field-level BM25 scores
using a Vespa [ranking expression](../ranking-expressions-features.html). 
- a `semantic` rank-profile which is used in combination Vespa's nearestNeighbor query operator (vector search).

Both profiles specify a single [ranking phase](../phased-ranking.html).

### Services Specification

The [services.xml](../reference/services.html) defines the services that make up
the Vespa application — which services to run and how many nodes per service.
Write the following to `app/services.xml`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="file" data-path="app/services.xml">{% highlight xml%}
<services version="1.0">

    <container id="default" version="1.0">
        <search />
        <document-processing />
        <document-api />
        <component id="arctic" type="hugging-face-embedder">
          <transformer-model url="https://huggingface.co/Snowflake/snowflake-arctic-embed-xs/resolve/main/onnx/model_quantized.onnx"/>
          <tokenizer-model url="https://huggingface.co/Snowflake/snowflake-arctic-embed-xs/raw/main/tokenizer.json"/>
          <pooling-strategy>cls</pooling-strategy>
          <prepend>
            <query>Represent this sentence for searching relevant passages: </query>
          </prepend>
      </component>
    </container>

    <content id="content" version="1.0">
        <min-redundancy>1</min-redundancy>
        <documents>
            <document type="doc" mode="index" />
        </documents>
        <nodes>
            <node distribution-key="0" hostalias="node1" />
        </nodes>
    </content>
</services>
{% endhighlight %}
</pre>
</div>

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

Notice that we publish two ports: 8080 is the data-plane where we write and query documents, and 19071 is
the control-plane where we can deploy the application. Note that the data-plane port is inactive before deploying the application. 

Configure the Vespa CLI to use the local container:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa config set target local
</pre>
</div>

Starting the container can take a short while. Make sure
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
<pre data-test="exec" data-test-assert-contains="Success">
$ vespa deploy --wait 300 app
</pre>
</div>


## Feed the data

The data fed to Vespa must match the document type in the schema. This step performs embed inference inside Vespa 
using the snowflake arctic embedding model. Remember the `component` definition in `services.xml` and the `embed` call in the schema.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa feed -t http://localhost:8080 vespa-docs.jsonl
</pre>
</div>

On an M1, we expect output like the following:

<pre>{% highlight json%}
{
  "feeder.operation.count": 3633,
  "feeder.seconds": 39.723,
  "feeder.ok.count": 3633,
  "feeder.ok.rate": 91.459,
  "feeder.error.count": 0,
  "feeder.inflight.count": 0,
  "http.request.count": 13157,
  "http.request.bytes": 21102792,
  "http.request.MBps": 0.531,
  "http.exception.count": 0,
  "http.response.count": 13157,
  "http.response.bytes": 1532828,
  "http.response.MBps": 0.039,
  "http.response.error.count": 9524,
  "http.response.latency.millis.min": 0,
  "http.response.latency.millis.avg": 1220,
  "http.response.latency.millis.max": 13703,
  "http.response.code.counts": {
    "200": 3633,
    "429": 9524
  }
}{% endhighlight %}</pre>

Notice:

- `feeder.ok.rate` which is the throughput (Note that this step includes embedding inference). See [embedder-performance](../embedding.html#embedder-performance) for details on embedding inference performance. In this case, embedding inference is the bottleneck for overall indexing throughput. 
- `http.response.code.counts` matches with `feeder.ok.count` - The dataset has 3633 documents. The `429` are harmless. Vespa asks the client
to slow down the feed speed because of resource contention.


## Sample queries 
We can now run a few sample queries to demonstrate various ways to perform searches over this data using the [Vespa query language](../query-language.html).

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="PLAIN-2">
$ ir_datasets export beir/nfcorpus/test queries | head -1
</pre>
</div> 

<pre>
PLAIN-2	Do Cholesterol Statin Drugs Cause Breast Cancer?
</pre>

Here, `PLAIN-2` is the query id of the first test query. We'll use this test query to demonstrate querying Vespa.

### Lexical search with BM25 scoring
The following query uses [weakAnd](../using-wand-with-vespa.html) and where `targetHits` is a hint 
of how many documents we want to expose to configurable [ranking phases](../phased-ranking.html). Refer
to [text search tutorial](text-search.html#querying-the-data) for more on querying with `userInput`. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="MED-10">
$ vespa query \
  'yql=select * from doc where {targetHits:10}userInput(@user-query)' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'hits=1' \
  'language=en' \
  'ranking=bm25'
</pre>
</div>

Notice that we choose `ranking` to specify which rank profile to rank the documents retrieved by the query. 
This query returns the following [JSON result response](../reference/default-result-format.html):

<pre>{% highlight json %}
{
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 65
        },
        "coverage": {
            "coverage": 100,
            "documents": 3633,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "id:doc:doc::MED-10",
                "relevance": 25.521817426330887,
                "source": "content",
                "fields": {
                    "sddocname": "doc",
                    "documentid": "id:doc:doc::MED-10",
                    "doc_id": "MED-10",
                    "title": "Statin Use and Breast Cancer Survival: A Nationwide Cohort Study from Finland",
                    "text": "Recent studies have suggested that statins, an established drug group in the prevention of cardiovascular mortality, could delay or prevent breast cancer recurrence but the effect on disease-specific mortality remains unclear. We evaluated risk of breast cancer death among statin users in a population-based cohort of breast cancer patients. The study cohort included all newly diagnosed breast cancer patients in Finland during 1995–2003 (31,236 cases), identified from the Finnish Cancer Registry. Information on statin use before and after the diagnosis was obtained from a national prescription database. We used the Cox proportional hazards regression method to estimate mortality among statin users with statin use as time-dependent variable. A total of 4,151 participants had used statins. During the median follow-up of 3.25 years after the diagnosis (range 0.08–9.0 years) 6,011 participants died, of which 3,619 (60.2%) was due to breast cancer. After adjustment for age, tumor characteristics, and treatment selection, both post-diagnostic and pre-diagnostic statin use were associated with lowered risk of breast cancer death (HR 0.46, 95% CI 0.38–0.55 and HR 0.54, 95% CI 0.44–0.67, respectively). The risk decrease by post-diagnostic statin use was likely affected by healthy adherer bias; that is, the greater likelihood of dying cancer patients to discontinue statin use as the association was not clearly dose-dependent and observed already at low-dose/short-term use. The dose- and time-dependence of the survival benefit among pre-diagnostic statin users suggests a possible causal effect that should be evaluated further in a clinical trial testing statins’ effect on survival in breast cancer patients."
                }
            }
        ]
    }
}

{% endhighlight %}</pre>

The query retrieves and ranks `MED-10` as the most relevant document—notice the `totalCount` which is the number of documents that were retrieved for ranking
phases. In this case, we exposed 65 documents, it is higher than our target, but also much fewer than the total number of documents that match any query terms like below, changing the 
grammar from the default `weakAnd` to `any` matches 1780, or almost 50% of the indexed documents. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="MED-10">
$ vespa query \
  'yql=select * from doc where {targetHits:10, grammar:"any"}userInput(@user-query)' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'hits=1' \
  'language=en' \
  'ranking=bm25'
</pre>
</div>

The bm25 profile calculates the relevance score ( "relevance": 25.5..)

<pre>
rank-profile bm25 {
        first-phase {
            expression: bm25(title) + bm25(text)
        }
    }
</pre>

So, in this case, `relevance` is the sum of the two BM25 scores. The retrieved document looks relevant; we can look at the graded judgment for this query `PLAIN-2`. The following exports the query relevance judgments (we grep for the query id that we are interested in):

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="MED-10">
$ ir_datasets export beir/nfcorpus/test qrels |grep "PLAIN-2 "
</pre>
</div>

The following is the output from the above command. Notice line two, the `MED-10` document retrieved above, is judged as very relevant with the grade 2 for the query PLAIN-2. 
This dataset has graded relevance judgments where a grade of 1 is less relevant than 2. 

<pre>
PLAIN-2 0 MED-2427 2
PLAIN-2 0 MED-10 2
PLAIN-2 0 MED-2429 2
PLAIN-2 0 MED-2430 2
PLAIN-2 0 MED-2431 2
PLAIN-2 0 MED-14 2
PLAIN-2 0 MED-2432 2
PLAIN-2 0 MED-2428 1
PLAIN-2 0 MED-2440 1
PLAIN-2 0 MED-2434 1
PLAIN-2 0 MED-2435 1
PLAIN-2 0 MED-2436 1
PLAIN-2 0 MED-2437 1
PLAIN-2 0 MED-2438 1
PLAIN-2 0 MED-2439 1
PLAIN-2 0 MED-3597 1
PLAIN-2 0 MED-3598 1
PLAIN-2 0 MED-3599 1
PLAIN-2 0 MED-4556 1
PLAIN-2 0 MED-4559 1
PLAIN-2 0 MED-4560 1
PLAIN-2 0 MED-4828 1
PLAIN-2 0 MED-4829 1
PLAIN-2 0 MED-4830 1
</pre>

### Dense search using text embedding

Now, we turn to embedding-based retrieval, where we embed the query text using the configured text-embedding model and perform
an exact `nearestNeighbor` search. We use [embed query](.//embedding.html#embedding-a-query-text) to produce the
input tensor `query(e)`, defined in the `semantic` rank-profile in the schema.

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="MED-2429">
$ vespa query \
  'yql=select * from doc where {targetHits:10}nearestNeighbor(embedding,e)' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'input.query(e)=embed(@user-query)' \
  'hits=1' \
  'ranking=semantic'
</pre>
</div>

This query returns the following [JSON result response](../reference/default-result-format.html):

<pre>{% highlight json %}
{
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 64
        },
        "coverage": {
            "coverage": 100,
            "documents": 3633,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "id:doc:doc::MED-2429",
                "relevance": 0.6061378635706601,
                "source": "content",
                "fields": {
                    "sddocname": "doc",
                    "documentid": "id:doc:doc::MED-2429",
                    "doc_id": "MED-2429",
                    "title": "Statin use and risk of breast cancer: a meta-analysis of observational studies.",
                    "text": "Emerging evidence suggests that statins' may decrease the risk of cancers. However, available evidence on breast cancer is conflicting. We, therefore, examined the association between statin use and risk of breast cancer by conducting a detailed meta-analysis of all observational studies published regarding this subject. PubMed database and bibliographies of retrieved articles were searched for epidemiological studies published up to January 2012, investigating the relationship between statin use and breast cancer. Before meta-analysis, the studies were evaluated for publication bias and heterogeneity. Combined relative risk (RR) and 95 % confidence interval (CI) were calculated using a random-effects model (DerSimonian and Laird method). Subgroup analyses, sensitivity analysis, and cumulative meta-analysis were also performed. A total of 24 (13 cohort and 11 case-control) studies involving more than 2.4 million participants, including 76,759 breast cancer cases contributed to this analysis. We found no evidence of publication bias and evidence of heterogeneity among the studies. Statin use and long-term statin use did not significantly affect breast cancer risk (RR = 0.99, 95 % CI = 0.94, 1.04 and RR = 1.03, 95 % CI = 0.96, 1.11, respectively). When the analysis was stratified into subgroups, there was no evidence that study design substantially influenced the effect estimate. Sensitivity analysis confirmed the stability of our results. Cumulative meta-analysis showed a change in trend of reporting risk of breast cancer from positive to negative in statin users between 1993 and 2011. Our meta-analysis findings do not support the hypothesis that statins' have a protective effect against breast cancer. More randomized clinical trials and observational studies are needed to confirm this association with underlying biological mechanisms in the future."
                }
            }
        ]
    }
}{% endhighlight %}</pre>

The result of this vector-based search differed from the previous sparse keyword search, with a different relevant document @1. 

## Evaluate ranking accuracy 
The previous section demonstrated how to combine the Vespa query language with rank-profile's 
to implement two different retrieval and ranking strategies.

In the following section we evaluate all 323 test queries with both models to compare their overall effectiveness, measured using [nDCG@10](https://en.wikipedia.org/wiki/Discounted_cumulative_gain).`nDCG@10` is the official evaluation metric of the BEIR benchmark and is an appropriate metric for test sets with graded relevance judgments. 

For this evaluation task, we need to write a small script. The following script iterates over the queries in the test set, executes the query against the Vespa instance, and reads 
the response from Vespa. It then evaluates and prints the metric. 

<div class="pre-parent">
<button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="file" data-path="evaluate_ranking.py">
{% highlight python %}
import requests
import ir_datasets
from ir_measures import calc_aggregate, nDCG, ScoredDoc
from enum import Enum
from typing import List

class RModel(Enum):
    SPARSE = 1
    DENSE = 2
    HYBRID = 3

def parse_vespa_response(response:dict, qid:str) -> List[ScoredDoc]:
    result = []
    hits = response['root'].get('children',[])
    for hit in hits:
      doc_id = hit['fields']['doc_id']
      relevance = hit['relevance']
      result.append(ScoredDoc(qid, doc_id, relevance))
    return result

def search(query:str, qid:str, ranking:str, 
           hits=10, language="en", mode=RModel.SPARSE) -> List[ScoredDoc]:
    yql = "select doc_id from doc where ({targetHits:100}userInput(@user-query))"
    if mode == RModel.DENSE:
        yql = "select doc_id from doc where ({targetHits:10}nearestNeighbor(embedding, e))"
    query_request = {
        'yql': yql,
        'user-query': query, 
        'ranking.profile': ranking,
        'hits' : hits, 
        'language': language
    }
    if mode == RModel.DENSE:
        query_request['input.query(e)'] = "embed(@user-query)"

    response = requests.post("http://localhost:8080/search/", json=query_request)
    if response.ok:
        return parse_vespa_response(response.json(), qid)
    else:
      print("Search request failed with response " + str(response.json()))
      return []

def main():
  dataset = ir_datasets.load("beir/nfcorpus/test")
  sparse_results = []
  dense_results = []
  metrics = [nDCG@10]
  for query in dataset.queries_iter():
    qid = query.query_id
    query_text = query.text
    sparse_results.extend(search(query_text, qid, "bm25", mode=RModel.SPARSE))
    dense_results.extend(search(query_text, qid, "semantic", mode=RModel.DENSE))

  sparse_metrics = calc_aggregate(metrics, dataset.qrels, sparse_results)
  dense_metrics = calc_aggregate(metrics, dataset.qrels, dense_results)

  print("Sparse BM25: nDCG@10 {:.4f}".format(sparse_metrics[nDCG@10]))
  print("Dense Semantic: nDCG@10 {:.4f}".format(dense_metrics[nDCG@10]))
  

if __name__ == "__main__":
    main(){% endhighlight %}</pre>
</div>

Then execute the script:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="nDCG@10: 0.3">
$ python3 evaluate_ranking.py
</pre>
</div>

The script will produce the following output:

<pre>
Sparse BM25: nDCG@10 0.3195
Dense Semantic: nDCG@10 0.3077
</pre>

This is the *average* `nDCG@10` score across all the 327 test queries for both methods. In a real-word scenario, we would also 
weigh the query frequency (The set here has unique queries). You can also experiment beyond a single metric and modify the
script to calculate more [measures](https://ir-measur.es/en/latest/measures.html), for example, including precision with 
a relevance label cutoff of 2: 

<pre>
metrics = [nDCG@10, P(rel=2)@10]
</pre>

## Hybrid Search & Ranking

We demonstrated and evaluated two independent retrieval and ranking strategies in the previous sections. Now, we want to explore hybrid search techniques
where we combine:

- traditional lexical keyword matching with a text scoring method (BM25) 
- embedding-based search using a generic text embedding model 

With Vespa, there is a distinction between retrieval (matching) and configurable [ranking](../ranking.html). In the Vespa ranking phases, we can express arbitrary
scoring complexity with the full power of the Vespa [ranking](../ranking.html) framework. Meanwhile, top-k retrieval relies on simple built-in functions associated with Vespa's top-k query operators.  
These operators aim to avoid scoring all documents in the collection for a query by using a simplistic scoring function to identify the top-k documents.

These top-k query operators use `index` structures to accelerate the query evaluation, avoiding scoring all documents using heuristics. In the context of hybrid text
search, the following Vespa top-k query operators are relevant: 

- YQL `{targetHits:k}nearestNeighbor()` for dense representations (text embeddings) using 
a configured [distance-metric](reference/schema-reference.html#distance-metric) as the scoring function. 
- YQL `{targetHits:k}userInput(@user-query)` which by default uses [weakAnd](../using-wand-with-vespa.html) for sparse representations


We can combine these using boolean query operators like AND/OR/RANK to express a hybrid search query. Then, there is a wild number of
ways that we can combine various signals in [ranking](../ranking.html). 


### Define our first simple hybrid rank profile

First, we can add our first simple hybrid rank profile that combines the dense and sparse components using multiplication to 
combine them into a single score. 

<pre>
closeness(field, embedding) * (1 + bm25(title) + bm25(text))
</pre>

- the `closeness(field, embeddding)` rank-feature returns a score in the range 0 to 1 inclusive
- Any of the per-field BM25 scores are in the range of 0 to infinity 

We add a bias constant (1) to avoid the overall score becoming 0 if the document does not match any query terms, 
as the BM25 scores would be 0. We also add `match-features` to be able to debug each of the scores. 


<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
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
            indexing: index | summary
            match: text
            index: enable-bm25
        }
    }
    fieldset default {
        fields: title, text
    }
    
    field embedding type tensor&lt;bfloat16&gt;(v[384]) {
      indexing: input title." ".input text | embed | attribute
      attribute {
        distance-metric: angular
      }
    }
  
    rank-profile hybrid {
        inputs {
          query(e) tensor&lt;bfloat16&gt;(v[384])
        }
        first-phase {
            expression: closeness(field, embedding) * (1 + (bm25(title) + bm25(text)))
        }
        match-features: bm25(title) bm25(text) closeness(field, embedding)
    }
}
</pre>
</div>

Now, re-deploy the Vespa application from the `app` directory:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Success">
$ vespa deploy --wait 300 app
</pre>
</div>

After that, we can start experimenting with how to express hybrid queries using the Vespa query language. 

### Hybrid query examples

#### Hybrid query with OR operator

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="MED-10">
$ vespa query \
  'yql=select * from doc where ({targetHits:10}userInput(@user-query)) or ({targetHits:10}nearestNeighbor(embedding,e))' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'input.query(e)=embed(@user-query)' \
  'hits=1' \
  'language=en' \
  'ranking=hybrid'
</pre>
</div>
With this query, we express that we want to retrieve the top 10 documents that match the query using either the sparse or dense representation. Then, in the ranking phase, we determine how we score the retrieved documents, using the `hybrid` rank-profile.

The query returns the following [JSON result response](../reference/default-result-format.html):

<pre>{% highlight json %}
{
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 105
        },
        "coverage": {
            "coverage": 100,
            "documents": 3633,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "id:doc:doc::MED-10",
                "relevance": 15.898915593367988,
                "source": "content",
                "fields": {
                    "matchfeatures": {
                        "bm25(text)": 17.35556767018612,
                        "bm25(title)": 8.166249756144769,
                        "closeness(field,embedding)": 0.5994655395517325
                    },
                    "sddocname": "doc",
                    "documentid": "id:doc:doc::MED-10",
                    "doc_id": "MED-10",
                    "title": "Statin Use and Breast Cancer Survival: A Nationwide Cohort Study from Finland",
                    "text": "Recent studies have suggested that statins, an established drug group in the prevention of cardiovascular mortality, could delay or prevent breast cancer recurrence but the effect on disease-specific mortality remains unclear. We evaluated risk of breast cancer death among statin users in a population-based cohort of breast cancer patients. The study cohort included all newly diagnosed breast cancer patients in Finland during 1995–2003 (31,236 cases), identified from the Finnish Cancer Registry. Information on statin use before and after the diagnosis was obtained from a national prescription database. We used the Cox proportional hazards regression method to estimate mortality among statin users with statin use as time-dependent variable. A total of 4,151 participants had used statins. During the median follow-up of 3.25 years after the diagnosis (range 0.08–9.0 years) 6,011 participants died, of which 3,619 (60.2%) was due to breast cancer. After adjustment for age, tumor characteristics, and treatment selection, both post-diagnostic and pre-diagnostic statin use were associated with lowered risk of breast cancer death (HR 0.46, 95% CI 0.38–0.55 and HR 0.54, 95% CI 0.44–0.67, respectively). The risk decrease by post-diagnostic statin use was likely affected by healthy adherer bias; that is, the greater likelihood of dying cancer patients to discontinue statin use as the association was not clearly dose-dependent and observed already at low-dose/short-term use. The dose- and time-dependence of the survival benefit among pre-diagnostic statin users suggests a possible causal effect that should be evaluated further in a clinical trial testing statins’ effect on survival in breast cancer patients."
                }
            }
        ]
    }
}{% endhighlight %}</pre>

What is going on here is that we are combining the two top-k query operators using a boolean OR. The `totalCount` is the number of documents retrieved into
configurable ranking.  The `relevance` is the hybrid score (assigned by the rank-profile `hybrid`). Notice that the `matchfeatures` field shows the individual scores.

## Cleanup

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
  <pre data-test="after">
  $ docker rm -f vespa-hybrid
  </pre>
  </div>

[^1]: Robertson, Stephen and Zaragoza, Hugo and others, 2009. The probabilistic relevance framework: BM25 and beyond. Foundations and Trends in Information Retrieval.

<script src="/js/process_pre.js"></script>

