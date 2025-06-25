---
# Copyright Vespa.ai. All rights reserved.
title: "RAG Blueprint"
---

Many of our users use Vespa to power large scale RAG Applications.

This blueprint aims to exemplify many of the best practices we have learned while supporting these users.
There are a lot of RAG tutorials out there, but this one aims to provide a customizable template that:

* Can [(auto)scale](../cloud/autoscaling.html) with your data size and/or query load.
* Is fast and [production grade](../cloud/production-deployment.html).
* Let you create RAG applications with state-of-the-art quality.

This tutorial will show how we can develop a high-quality RAG application step-by-step by taking you through the following steps:

1.  [Our use case](#our-use-case)
2.  [Data modeling](#data-modeling)
3.  [Structuring your Vespa application](#structuring-your-vespa-application)
4.  [Configuring match-phase (retrieval)](#configuring-match-phase-retrieval)
5.  [First-phase ranking](#first-phase-ranking)
6.  [Second-phase ranking](#second-phase-ranking)
7.  [(Optional) Global-phase reranking](#optional-global-phase-reranking)

All the accompanying code can be found in our [sample app](https://github.com/vespa-engine/sample-apps/tree/master/rag-blueprint) repo. You can also deploy the sample app by running this [pyvespa notebook](TODO).

Each step will contain reasoning behind the choices and design of the blueprint, as well as pointers for customizing to your own application.

{% include note.html content="This is not a 'Deploy RAG in 5 minutes' tutorial (although you _can_ do that by just running the steps in the README of our [sample app](https://github.com/vespa-engine/sample-apps/tree/master/rag-blueprint)). The focus is rather to provide a blueprint that allows _you_ to build a high-quality RAG application with an evaluation-driven mindset, while being a resource you can go to for making informed choices for your own use case." %}

{% include pre-req.html memory="4 GB" extra-reqs=
'<li><a href="https://docs.astral.sh/uv/">uv</a> For Python dependency handling</li>' %}

## Our use case

The sample use case is a document search application, for a user who wants to get answers and insights quickly from a document collection containing company documents, notes, learning material, training logs.
We wanted a dataset with a bit more structured fields than we could find in the public datasets to make the blueprint more realistic, so we had an LLM generate it for us.

It is a toy example, with only 100 documents, but we think it will illustrate the necessary concepts.
You can also feel confident that the blueprint will provide a starting point that can scale as you want, with minimal changes.

Below you can see a sample document from the dataset:

```json
{
  "put": "id:doc:doc::78",
  "fields": {
    "created_timestamp": 1717750000,
    "modified_timestamp": 1717750000,
    "text": "# Feature Brainstorm: SynapseFlow Model Monitoring Dashboard v1\n\n**Goal:** Provide users with basic insights into their deployed model's performance and health.\n\n**Key Metrics to Display:**\n- **Inference Latency:** Avg, p95, p99 (Histogram).\n- **Request Rate / Throughput:** Requests per second/minute.\n- **Error Rate:** Percentage of 5xx errors.\n- **CPU/Memory Usage:** Per deployment/instance.\n- **GPU Usage / Temp (if applicable).**\n\n**Visualizations:**\n- Time series graphs for all key metrics.\n- Ability to select time range (last hour, day, week).\n- Filter by deployment ID.\n\n**Data Sources:**\n- Prometheus metrics from model server (see `code_review_pr123_metrics.md`).\n- Kubernetes metrics (via Kube State Metrics or cAdvisor).\n\n**Future Ideas (v2+):**\n- Data drift detection.\n- Concept drift detection.\n- Alerting on anomalies or threshold breaches.\n- Custom metric ingestion.\n\n## <MORE_TEXT:HERE> (UI mock-up sketches, specific Prometheus queries)",
    "favorite": true,
    "last_opened_timestamp": 1717750000,
    "open_count": 3,
    "title": "feature_brainstorm_monitoring_dashboard.md",
    "id": "78"
  }
}
```

In order to evaluate the quality of the RAG application, we also need a set of representative queries, with annotated relevant documents.
The most important thing is to have a set of representative queries that cover your expected use case well. More is better, but _some_ eval is always better than none.

We used `gemini-2.5-pro` to create our queries and relevant document labels. Please check out our [blog post](https://blog.vespa.ai/improving-retrieval-with-llm-as-a-judge/) to learn more about using LLM-as-a-judge.

We decided to generate some queries that need several documents to provide a good answer, and some that only need one document.
If these queries are representative of the use case, we will show that they can be a great starting point for creating an (initial) ranking expression that can be used for retrieving and ranking candidate documents. But, it can (and should) also be improved, for example by collecting user interaction data, human labeling and/ or using an LLM to generate relevance feedback following the initial ranking expression.

## Data modeling

Here is the schema that we will use for our sample application.

```txt
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
schema doc {

    document doc {

        field id type string {
            indexing: summary | attribute
        }

        field title type string {
            indexing: index | summary
            index: enable-bm25
        }

        field text type string {
            
        }

        field created_timestamp type long {
            indexing: attribute | summary
        }
        field modified_timestamp type long {
            indexing: attribute | summary
        }
        
        field last_opened_timestamp type long {
            indexing: attribute | summary
        }
        field open_count type int {
            indexing: attribute | summary
        }
        field favorite type bool {
            indexing: attribute | summary
        }

    }

    field title_embedding type tensor<int8>(x[96]) {
        indexing: input title | embed | pack_bits | attribute | index
        attribute {
            distance-metric: hamming
        }
    }

    field chunks type array<string> {
        indexing: input text | chunk fixed-length 1024 | summary | index
        index: enable-bm25
    }

    field chunk_embeddings type tensor<int8>(chunk{}, x[96]) {
        indexing: input text | chunk fixed-length 1024 | embed | pack_bits | attribute | index
        attribute {
            distance-metric: hamming
        }
    }

    fieldset default {
        fields: title, chunks
    }

    document-summary no-chunks {
        summary id {}
        summary title {}
        summary created_timestamp {}
        summary modified_timestamp {}
        summary last_opened_timestamp {}
        summary open_count {}
        summary favorite {}
        summary chunks {}
    }

    document-summary top_3_chunks {
        from-disk
        summary chunks_top3 {
            source: chunks
            select-elements-by: top_3_chunk_sim_scores #this needs to be added a summary-feature to the rank-profile
        }
    }
}
```

Keep reading for an explanation and reasoning behind the choices in the schema.

### Picking your searchable unit

When building a RAG application, your first key decision is choosing the "searchable unit." This is the basic block of information your system will search through and return as context to the LLM. For instance, if you have millions of documents, some hundreds of pages long, what should be your searchable unit?

Consider these points when selecting your searchable unit:

* **Too fine-grained (e.g., individual sentences or very small paragraphs):**
  * Leads to duplication of context and metadata across many small units.
  * May result in units lacking sufficient context for the LLM to make good selections or generate relevant responses.
  * Increases overhead for managing many small document units.
* **Too coarse-grained (e.g., very long chapters or entire large documents):**
  * Can cause performance issues due to the size of the units being processed.
  * May lead to some large documents appearing relevant to too many queries, reducing precision.
  * If you embed the whole document, a too large context will lead to reduced retrieval quality.

We recommend to err on the side of slightly larger units.

* LLMs are increasingly capable of handling larger contexts.
* In Vespa, you can index larger units, while avoiding data duplication and performance issues, by returning only the most relevant parts.

With Vespa, it is now possible to return only the top k most relevant chunks of a document, and include and combine both document-level and chunk-level features in ranking. 

### Chunk selection

Assume you have chosen a document as your searchable unit.
Then your document may containt text index fields of very variable lengths. Consider for example a corpus of web pages. Some might be very long, while the average is well within the recommended size. See [scaling retrieval size](../performance/sizing-search.html#scaling-retrieval-size) for more details.

While we recommend implementing guards against too long documents in your feeding pipeline, you still probably do not want to return every chunk of the top k documents to an LLM for RAG.

In Vespa, we now have a solution for this problem. Below, we show how you can score both documents as well as individual chunks, and use that score to select the best chunks to be returned in a summary, instead of returning all chunks belonging to the top k ranked documents. 

Compute closeness per chunk in a ranking function; use `elementwise(bm25(chunks), i, double)` for a per-chunk text signal. See [rank feature reference](..reference/rank-features.html#elementwise-bm25)
Now available: elementwise rank functions and filtering on the content nodes.

This allows you to pick a large document as the searchable unit, while still addressing the potential drawbacks many encounter as follows:

* Pick your (larger) document as your searchable unit.
* Chunk the text-fields automatically on indexing.
* Embed each chunk (enabled through Vespa's multivector support)
* Calculate chunk-level features (e.g. bm25 and embedding similarity) and document-level features. Combine as you want.
* Limit the actual chunks that are returned to the ones that are actually relevant context for the LLM.

This allows you to index larger units, while avoiding data duplication and performance issues, by returning only the most relevant parts.

Vespa also supports automatic [chunking](../reference/indexing-language-reference.html#converters) in the [indexing language](../indexing.html).

Here are the parts of the schema, which defines the searchable unit as a document with a text field, and automatically chunks it into smaller parts of 1024 characters, which each are embedded and indexed separately:

```txt
field chunks type array<string> {
    indexing: input text | chunk fixed-length 1024 | summary | index
    index: enable-bm25
}

field chunk_embeddings type tensor<int8>(chunk{}, x[96]) {
    indexing: input text | chunk fixed-length 1024 | embed | pack_bits | attribute | index
    attribute {
        distance-metric: hamming
    }
}
```

In Vespa, we can specify which chunks to be returned with a summary feature, see [docs](../reference/schema-reference.html#select-elements-by) for details. For this blueprint, we will return the top 3 chunks based on the similarity score of the chunk embeddings, which is calculated in the ranking phase. Note that this feature could be any chunk-level summary feature defined in your rank-profile.

Here is how the summary feature is calculated in the rank-profile:

```txt
# This function unpack the bits of each dimenrion of the mapped chunk_embeddings attribute tensor
function chunk_emb_vecs() {
    expression: unpack_bits(attribute(chunk_embeddings))
}

# This function calculate the dot product between the query embedding vector and the chunk embeddings (both are now float) over the x dimension
function chunk_dot_prod() {
    expression: reduce(query(float_embedding) * chunk_emb_vecs(), sum, x)
}

# This function calculate the L2 normalized length of an input tensor
function vector_norms(t) {
    expression: sqrt(sum(pow(t, 2), x))
}

# Here we calculate cosine similarity by dividing the dot product by the product of the L2 normalized query embedding and document embeddings
function chunk_sim_scores() {
    expression: chunk_dot_prod() / (vector_norms(chunk_emb_vecs()) * vector_norms(query(float_embedding)))
}

function top_3_chunk_text_scores() {
    expression: top(3, chunk_text_scores())
}

function top_3_chunk_sim_scores() {
        expression: top(3, chunk_sim_scores())
    }

summary-features {
        top_3_chunk_sim_scores
    }
```

Note that we want to use the float-representation of the query-embedding, and thus also need to convert the binary embedding of the chunks to float. After that, we can calculate the similarity score between the query embedding and the chunk embeddings using cosine similarity (the dot product, and then normalize it by the norms of the embeddings).

See [ranking expressions](../reference/ranking-expressions.html#non-primitive-functions) for more details on the `top`-function, and other functions available for ranking expressions.

Now, we can use this summary feature in our document summary to return the top 3 chunks of the document, which will be used as context for the LLM. Note that we can also define a document summary that returns all chunks, which might be useful for another use case, such as deep research.

```txt
document-summary top_3_chunks {
      from-disk
      summary chunks_top3 {
          source: chunks
          select-elements-by: top_3_chunk_sim_scores #this needs to be added a summary-feature to the rank-profile
      }
  }
```

### Use multiple text fields, consider multiple embeddings

We recommend indexing different textual content as separate indexes.
These can be searched together, using [field-sets](../reference/schema-reference.html#fieldset)

In our schema, this is exemplified by the sections below, which define the `title` and `chunks` fields as separate indexed text fields.

```txt
...
field title type title {
    indexing: index | summary
    index: enable-bm25
}
field chunks type array<string> {
    indexing: input text | chunk fixed-length 1024 | summary | index
    index: enable-bm25
}
```

Whether you should have separate embedding fields, depends on whether the added memory usage is justified by the quality improvement you could get from the additional embedding field.

We choose to index both a `title_embedding` and a `chunk_embeddings` field for this blueprint, as we aim to minimize cost by embedding the binary vectors.

```txt
field title_embedding type tensor<int8>(title{}, x[96]) {
    indexing: input text | embed | pack_bits | attribute | index
    attribute {
        distance-metric: hamming
    }
}
field chunk_embeddings type tensor<int8>(chunk{}, x[96]) {
    indexing: input text | chunk fixed-length 1024 | embed | pack_bits | attribute | index
    attribute {
        distance-metric: hamming
    }
}
```

Indexing several embedding fields may not be worth the cost for you. Evaluate whether the cost-quality trade-off is worth it for your application.

If you have different vector space representations of your document (e.g images), indexing them separately is likely worth it, as they are likely to provide signals that are complementary to the text-based embeddings.

### Model metadata and signals as structured fields

We recommend modeling metadata and signals as structured fields in your schema.
Below are some general recommendations, as well as the implementation in our blueprint schema.

**Metadata** — knowledge about your data:

* Authors, publish time, source, links, category, price, …
* Usage: filters, ranking, grouping/aggregation
* Index only metadata that are strong filters

In our blueprint schema, we include these metadata fields to demonstrate these concepts:

* `id` - document identifier 
* `title` - document name/filename for display and text matching
* `created_timestamp`, `modified_timestamp` - temporal metadata for filtering and ranking by recency

**Signals** — observations about your data:

* Popularity, quality, spam probability, click_probability, …
* Usage: ranking
* Often updated separately via partial updates
* Multiple teams can add their own signals independently

In our blueprint schema, we include several of these signals:

* `last_opened_timestamp` - user engagement signal for personalization
* `open_count` - popularity signal indicating document importance
* `favorite` - explicit user preference signal, can be used for boosting relevant content

These fields are configured as `attribute | summary` to enable efficient filtering, sorting, and grouping operations while being returned in search results. The timestamp fields allow for temporal filtering (e.g., "recent documents") and recency-based ranking, while usage signals like `open_count` and `favorite` can boost frequently accessed or explicitly marked important documents.

Consider [parent-child](../parent-child.html) relationships for low-cardinality metadata.
Most large scale RAG application schemas contain at least a hundred structured fields.

## LLM-generation with OpenAI-client

Vespa supports both Local LLMs, and any OpenAI-compatible API for LLM generation. For details, see [LLMs in Vespa](../llms-in-vespa.html)

The recommended way of providing an API key is through using the [secret store](../cloud/security/secret-store.html) in Vespa Cloud.

To enable this, you need to create a vault (if you don't have one already) and a secret through the [Vespa Cloud console](https://cloud.vespa.ai/). If your vault is named `sample-apps` and contains a secret with the name `openai-api-key`, you would use the following configuration in your `services.xml` to set up the OpenAI client to use that secret:

```xml
  <secrets>
      <openai-api-key vault="sample-apps" name="openai-dev" />
  </secrets>
  <!-- Setup the client to OpenAI -->
  <component id="openai" class="ai.vespa.llm.clients.OpenAI">
      <config name="ai.vespa.llm.clients.llm-client">
          <apiKeySecretName>openai-api-key</apiKeySecretName>
      </config>
  </component>
```

Alternatively, for local deployments, you can set the `X-LLM-API-KEY` header in your query to use the OpenAI client for generation.

To test generation using the OpenAI client, post a query that runs the `openai` search chain, with `format=sse`. (Use `format=json` for a streaming json response including both the search hits and the LLM-generated tokens.)

<pre>
$ vespa query \
    --timeout 60 \
    --header="X-LLM-API-KEY:<your-api-key>" \
    yql='select *
    from doc
    where userInput(@query) or
    ({label:"title_label", targetHits:100}nearestNeighbor(title_embedding, embedding)) or
    ({label:"chunks_label", targetHits:100}nearestNeighbor(chunk_embeddings, embedding))' \
    query="Summarize the key architectural decisions documented for SynapseFlow's v0.2 release." \
    searchChain=openai \
    format=sse \
    hits=5
</pre>

## Structuring your vespa application

This section will provide some recommendations on how to structure your Vespa application package. See also the [application package docs](../application-package.html) for more details on the application package structure.
Note that this is not mandatory, and it might be simpler to start without query profiles and rank profiles, but as you scale out your application, it will be beneficial to have a well-structured application package.

Consider the following structure for our application package:

```txt
app
├── models
│   └── lightgbm_model.json
├── schemas
│   ├── doc
│   │   ├── collect-second-phase.profile
│   │   ├── collect-training-data.profile
│   │   ├── learned-linear.profile
│   │   ├── match-only.profile
│   │   └── second-with-gbdt.profile
│   └── doc.sd
├── search
│   └── query-profiles
│       ├── deepresearch-with-gbdt.xml
│       ├── deepresearch.xml
│       ├── hybrid-with-gbdt.xml
│       ├── hybrid.xml
│       ├── rag-with-gbdt.xml
│       └── rag.xml
├── security
│   └── clients.pem
└── services.xml
```

You can see that we have separated the [query profiles](https://docs.vespa.ai/en/query-profiles.html), and [rank profiles](../ranking.html#rank-profiles) into their own directories.

### Manage queries in query profiles

Query profiles let you maintain collections of query parameters in one file.
Clients choose a query profile → the profile sets everything else.
This lets us change behavior for a use case without involving clients.

Let us take a closer look at 3 of the query profiles in our sample application.

1. `hybrid`
2. `rag`
3. `deepresearch`

### **_hybrid_** query profile

This query profile will be the one used by clients for traditional search, where the user is presented a limited number of hits.
Our other query profiles will inherit this one (but may override some fields).

```xml
<query-profile id="hybrid">
    <field name="schema">doc</field>
    <field name="ranking.features.query(embedding)">embed(@query)</field>
    <field name="ranking.features.query(float_embedding)">embed(@query)</field>
    <field name="yql">
        select *
        from %{schema}
        where userInput(@query) or
        ({label:"title_label", targetHits:100}nearestNeighbor(title_embedding, embedding)) or
        ({label:"chunks_label", targetHits:100}nearestNeighbor(chunk_embeddings, embedding))
    </field>
    <field name="hits">10</field>
    <field name="ranking.profile">learned-linear</field>
    <field name="presentation.summary">top_3_chunks</field>
</query-profile>
```

### **_rag_** query profile

This will be the query profile where the `openai` searchChain will be added, to generate a response based on the retrieved context. 
Here, we set some configuration that are specific to this use case.

```xml
<query-profile id="rag" inherits="hybrid">
  <field name="hits">50</field>
  <field name="searchChain">openai</field>
  <field name="presentation.format">sse</field>
</query-profile>
```

### **_deepresearch_** query profile

Again, we will inherit from the `hybrid` query profile, but override with a `targetHits` value of 10 000 (original was 100) that prioritizes recall over latency.
We will also increase number of hits to be returned, and increase the timeout to 5 seconds.

```xml
<query-profile id="deepresearch" inherits="hybrid">
  <field name="yql">
    select *
    from %{schema}
    where userInput(@query) or
    ({label:"title_label", targetHits:10000}nearestNeighbor(title_embedding, embedding)) or
    ({label:"chunks_label", targetHits:10000}nearestNeighbor(chunk_embeddings, embedding))
  </field>
  <field name="hits">100</field>
  <field name="timeout">5s</field>
</query-profile>
```

We will leave out the LLM-generation for this one, and let an LLM agent on the client side be responsible for using this API call as a tool, and to determine whether enough relevant context to answer has been retrieved.
Note that the `targetHits` parameter set here does not really makes sense until your dataset reach a certain scale.

As we add more rank-profiles, we can also inherit the existing query profiles, only to override the `ranking.profile` field to use a different rank profile. This is what we have done for the `rag-with-gbdt` and `deepresearch-with-gbdt` query profiles, which will use the `second-with-gbdt` rank profile instead of the `learned-linear` rank profile.

```xml
<query-profile id="rag-with-gbdt" inherits="hybrid-with-gbdt">
  <field name="hits">50</field>
  <field name="searchChain">openai</field>
  <field name="presentation.format">sse</field>
</query-profile>
```

### Separating out rank profiles

To build a great RAG application, assume you’ll need many ranking models. This will allow you to bucket-test alternatives continuously and to serve different use cases, including data collection for different phases, and the rank profiles to be used in production.

Separate common functions/setup into parent rank profiles and use `.profile` files.

## Configuring match-phase (retrieval)

This section will contain important considerations for the retrieval-phase of a RAG application in Vespa.
To learn more about the phased ranking approach in Vespa, see the [phased ranking docs](../phased-ranking.html).
The goal of the retrieval phase is to retrieve candidate documents efficiently, and maximize recall, without exposing too many documents to ranking.

### Vector, text or hybrid recall?

As you could see from the schema, we create and index both a text representation and a vector representation for each chunk of the document. This will allow us to use both text-based features and semantic features for both recall and ranking.

The text and vector representation complement each other well:

* **Text-only** → misses recall of semantically similar content
* **Vector-only** → misses recall of specific content not well understood by the embedding models

Our recommendation is to default to hybrid retrieval:

```sql
select *
        from doc
        where userInput(@query) or
        ({label:"title_label", targetHits:1000}nearestNeighbor(title_embedding, embedding)) or
        ({label:"chunks_label", targetHits:1000}nearestNeighbor(chunk_embeddings, embedding))
```

In generic domains, or if you have finetuned an embedding model to your specific data, _consider_ vector-only:

```sql
select *
        from doc
        where rank({targetHits:10000}nearestNeighbor(embeddings_field, query_embedding, userInput(@query)))
```

Notice that only the first argument of the [rank](../reference/query-language-reference.html#rank)-operator will be used to determine if a document is a match, while all arguments are used for calculating rank features. This mean we can do vector only for matching, but still use text-based features such as `bm25` and `nativeRank` for ranking.
Note that if you do this, it makes sense to increase the number of `targetHits` for the `nearestNeighbor`-operator.

For our sample application, we add three different retrieval operators (that are combined with `OR`), one with `weakAnd` for text matching, and two `nearestNeighbor` operators for vector matching, one for the title and one for the chunks. This will allow us to retrieve both relevant documents based on text and vector similarity, while also allowing us to return the most relevant chunks of the documents.

```sql
select *
        from doc
        where userInput(@query) or
        ({targetHits:100}nearestNeighbor(title_embedding, embedding)) or
        ({targetHits:100}nearestNeighbor(chunk_embeddings, embedding))
```

### Choosing your embedding model (and strategy)

Choice of embedding model will be a trade-off between inference time (both indexing and query time), memory usage (embedding dimensions) and quality. There are many good open-source models available, and we recommend checking out the [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard), and look at the `Retrieval`-column to gauge performance, while also considering the memory usage, vector dimensions, and context length of the model.

See [model hub](../cloud/model-hub.html) for a list of provided models ready to use with Vespa. See also [Huggingface Embedder](../embedding.html#huggingface-embedder) for details on using other models (exported as ONNX) with Vespa.

In addition to dense vector representation, Vespa supports sparse embeddings (token weights) and multi-vector (ColBERT-style) embeddings.
See our [example notebook](https://vespa-engine.github.io/pyvespa//examples/mother-of-all-embedding-models-cloud.html#bge-m3-the-mother-of-all-embedding-models) of using the bge-m3 model, which supports both, with Vespa.

Vespa also supports [Matryoshka embeddings](https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/), which can be a great way of reducing inference cost for retrieval phases, by using a subset of the embedding dimensions, while using more dimensions for increased precision in the later ranking phases.

For domain-specific applications or less popular languages, you may want to consider finetuning a model on your own data.

### Consider binary vectors for recall

Another decision to make is which precision you will use for your embeddings.
See [binarization docs](../binarizing-vectors.html) for an introduction to binarization in Vespa.

For most cases, binary vectors will provide an attractive tradeoff, especially for recall during match-phase.
Consider these factors to determine whether this holds true for your application:

* Reduces memory-vector cost by 5 – 30 ×
* Reduces query and indexing cost by 30 ×
* Often reduces quality by only a few percentage points

```txt
field binary_chunk_embeddings type tensor<int8>(chunk{}, x) {
  indexing: input text | chunk fixed-length 1024 | embed | pack_bits | attribute | index 
  attribute { distance-metric: hamming }
}
```

If you need higher precision vector similarity, you should use bfloat16 precision, and consider paging these vectors to disk to avoid large memory cost. Note that this means that when accessing this field in ranking, they will also need to be read from disk, so you need to restrict the number of hits that accesses this field to avoid performance issues.

```txt
field chunk_embeddings type tensor<bfloat16>(chunk{}, x) {
  indexing: input text | chunk fixed-length 1024 | embed | attribute 
  attribute: paged
}
```

For example, if you want to calculate `closeness` for a paged embedding vector in first-phase, consider configuring your retrieval operators (typically `weakAnd` and/or `nearestNeighbor`, optionally combined with filters) so that not too many hits are matched. Another option is to enable match-phase limiting, see [match-phase docs](../reference/schema-reference.html#match-phase). In essence, you restrict the number of matches by specifying an attribute field.

## Consider float-binary for ranking

In our blueprint, we choose to index binary vectors of the documents. This does not prevent us from using the float-representation of the query embedding though.

By unpacking the binary document chunk embeddings to their float representations (using [`unpack_bits`](../reference/ranking-expressions.html#unpack-bits)), we can calculate the similarity between query and document with slightly higher precision using a `float-binary` dot product, instead of hamming distance (`binary-binary`)

Below, you can see how we can do this:

```txt
rank-profile collect-training-data {
 
        inputs {
            query(embedding) tensor<int8>(x[96])
            query(float_embedding) tensor<float>(x[768])
        }
        
        function chunk_emb_vecs() {
            expression: unpack_bits(attribute(chunk_embeddings))
        }

        function chunk_dot_prod() {
            expression: reduce(query(float_embedding) * chunk_emb_vecs(), sum, x)
        }

        function vector_norms(t) {
            expression: sqrt(sum(pow(t, 2), x))
        }
        function chunk_sim_scores() {
            expression: chunk_dot_prod() / (vector_norms(chunk_emb_vecs()) * vector_norms(query(float_embedding)))
        }

        function top_3_chunk_text_scores() {
            expression: top(3, chunk_text_scores())
        }

        function top_3_chunk_sim_scores() {
            expression: top(3, chunk_sim_scores())
        }
}
```

### Use complex linguistics/recall only for precision

Vespa gives you extensive control over [linguistics](../linguistics.html).
You can decide [match mode](../reference/schema-reference.html#match), stemming, normalization, or control derived tokens.


It is also possible to use more specific operators than [weakAnd](../reference/query-language-reference.html#weakand) to match only close occurrences `{near}`, multiple alternatives `{equiv}`, weight items, set connectivity, and apply query-rewrite rules.

Don’t use this to increase recall — improve your embedding model instead.
Consider using it to improve precision when needed.

### Evaluating recall of the retrieval phase

To know whether your retrieval phase is working well, you need to measure recall, number of total matches and the reported time spent.

We can use [`VespaMatchEvaluator`](https://vespa-engine.github.io/pyvespa/api/vespa/evaluation.html#vespa.evaluation.VespaMatchEvaluator) from the pyvespa client library to do this.

For this sample application, we set up an evaluation script that compares three different retrieval strategies, let us call them "retrieval arms":

1. **Semantic-only**: Uses only vector similarity through `nearestNeighbor` operators.
2. **WeakAnd-only**: Uses only text-based matching with `userQuery()`.
3. **Hybrid**: Combines both approaches with OR logic.

It is recommended to use a ranking profile that does not use any first-phase ranking, to run the match-phase evaluation faster. 

The evaluation will output metrics like:

* Recall (percentage of relevant documents matched)
* Total number of matches per query
* Query latency statistics
* Per-query detailed results (when `write_verbose=True`) to identify "offending" queries with regards to recall or performance.

This will be valuable input for tuning each of them.

Run the complete evaluation script from the `eval/` directory to see detailed comparisons between all three retrieval strategies on your dataset.

#### Semantic Query Evaluation

```sql
select * from doc where 
({targetHits:100}nearestNeighbor(title_embedding, embedding)) or
({targetHits:100}nearestNeighbor(chunk_embeddings, embedding))
```

<style>
table, th, td { border: 1px solid black; }
th { width: 120px; }
</style>
<table>
  <thead>
    <tr>
      <th>Metric</th>
      <th>Value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Match Recall</td>
      <td>1.0000</td>
    </tr>
    <tr>
      <td>Average Recall per Query</td>
      <td>1.0000</td>
    </tr>
    <tr>
      <td>Total Relevant Documents</td>
      <td>51</td>
    </tr>
    <tr>
      <td>Total Matched Relevant</td>
      <td>51</td>
    </tr>
    <tr>
      <td>Average Matched per Query</td>
      <td>100.0000</td>
    </tr>
    <tr>
      <td>Total Queries</td>
      <td>20</td>
    </tr>
    <tr>
      <td>Search Time Average (s)</td>
      <td>0.0090</td>
    </tr>
    <tr>
      <td>Search Time Q50 (s)</td>
      <td>0.0060</td>
    </tr>
    <tr>
      <td>Search Time Q90 (s)</td>
      <td>0.0193</td>
    </tr>
    <tr>
      <td>Search Time Q95 (s)</td>
      <td>0.0220</td>
    </tr>
  </tbody>
</table>

#### WeakAnd Query Evaluation

The `userQuery` is just a convenience wrapper for `weakAnd`, see [reference/query-language-reference.html](../reference/query-language-reference.html). The default `targetHits` for `weakAnd` is 100, but it is [overridable](../reference/query-language-reference.html#targethits).

```sql
select * from doc where userQuery()
```

<style>
table {
  border-collapse: collapse;   /* optional but usually nicer */
  border: none;                /* no outer border */
}
th, td { border: 1px solid black; }
th { width: 120px; }
</style>
<table>
  <thead>
    <tr>
      <th>Metric</th>
      <th>Value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Match Recall</td>
      <td>1.0000</td>
    </tr>
    <tr>
      <td>Average Recall per Query</td>
      <td>1.0000</td>
    </tr>
    <tr>
      <td>Total Relevant Documents</td>
      <td>51</td>
    </tr>
    <tr>
      <td>Total Matched Relevant</td>
      <td>51</td>
    </tr>
    <tr>
      <td>Average Matched per Query</td>
      <td>88.7000</td>
    </tr>
    <tr>
      <td>Total Queries</td>
      <td>20</td>
    </tr>
    <tr>
      <td>Search Time Average (s)</td>
      <td>0.0071</td>
    </tr>
    <tr>
      <td>Search Time Q50 (s)</td>
      <td>0.0060</td>
    </tr>
    <tr>
      <td>Search Time Q90 (s)</td>
      <td>0.0132</td>
    </tr>
    <tr>
      <td>Search Time Q95 (s)</td>
      <td>0.0171</td>
    </tr>
  </tbody>
</table>

#### Hybrid Query Evaluation

```sql
select * from doc where 
({targetHits:100}nearestNeighbor(title_embedding, embedding)) or
({targetHits:100}nearestNeighbor(chunk_embeddings, embedding)) or
userQuery()
```

<table>
  <thead>
    <tr>
      <th>Metric</th>
      <th>Value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Match Recall</td>
      <td>1.0000</td>
    </tr>
    <tr>
      <td>Average Recall per Query</td>
      <td>1.0000</td>
    </tr>
    <tr>
      <td>Total Relevant Documents</td>
      <td>51</td>
    </tr>
    <tr>
      <td>Total Matched Relevant</td>
      <td>51</td>
    </tr>
    <tr>
      <td>Average Matched per Query</td>
      <td>100.0000</td>
    </tr>
    <tr>
      <td>Total Queries</td>
      <td>20</td>
    </tr>
    <tr>
      <td>Search Time Average (s)</td>
      <td>0.0076</td>
    </tr>
    <tr>
      <td>Search Time Q50 (s)</td>
      <td>0.0055</td>
    </tr>
    <tr>
      <td>Search Time Q90 (s)</td>
      <td>0.0150</td>
    </tr>
    <tr>
      <td>Search Time Q95 (s)</td>
      <td>0.0201</td>
    </tr>
  </tbody>
</table>

### Tuning the retrieval phase

We can see that all queries match all relevant documents, which is expected, since we use `targetHits:100` in the `nearestNeighbor` operator, and this is also the default for `weakAnd`(and `userQuery`). By setting `targetHits` lower, we can see that recall will drop.

In general, you have these options if you want to increase recall:

1. Increase `targetHits` in your retrieval operators (e.g., `nearestNeighbor`, `weakAnd`).
2. Improve your embedding model (use a better model or finetune it on your data).
3. You can also consider tuning HNSW parameters, see [docs on HNSW](../approximate-nn-hnsw.html#using-vespas-approximate-nearest-neighbor-search).

On the other hand, if you want to reduce latency of on of your retrieval "arms", with a small trade-off in recall, you can:

1. Tune `weakAnd` parameters. This has potential to 3x your performance for the `weakAnd`-parameter of your query, see [blog post](https://blog.vespa.ai/tripling-the-query-performance-of-lexical-search/).

Below are some empirically found default parameters that work well for most use cases:

```txt
rank-profile optimized inherits baseline {
    filter-threshold: 0.05
    weakand {
      stopword-limit: 0.6
      adjust-target: 0.01
    }
  }
```

See the [reference](../reference/schema-reference.html#weakand) for more details on the `weakAnd` parameters.
These can also be set as query parameters.

1. As already [mentioned](#consider-binary-vectors-for-recall), consider binary vectors for your embeddings.
2. Consider using an embedding model with less dimensions, or using only a subset of the dimensions (e.g., using [Matryoshka embeddings](https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/)).

## First-phase ranking

For first-phase ranking, we want to use a cheaper function, as all matched documents from the retrieval phase will be exposed to first-phase ranking. For most applications, this can be several millions candidate documents.

Common options include (learned) linear combination of features including text similarity features, vector closeness, and metadata.
It could also be a heuristic handwritten function.

Text features should include [nativeRank](../reference/nativerank.html#nativerank) or [bm25](../reference/bm25.html#ranking-function) — not [fieldMatch](../reference/rank-features.html#field-match-features-normalized) (it is too expensive).

* **bm25**: cheapest, strong significance, no proximity, not normalized.
* **nativeRank**: 2 – 3 × costlier, truncated significance, includes proximity, normalized.

### Collecting training data for first-phase ranking

For our blueprint we collect training data for first-phase ranking using `VespaFeatureCollector` from the pyvespa library. 

These are the features we will include:

```txt
rank-profile collect-training-data {
        match-features {
            bm25(title)
            bm25(chunks)
            max_chunk_sim_scores
            max_chunk_text_scores
            avg_top_3_chunk_sim_scores
            avg_top_3_chunk_text_scores

        }
        inputs {
            query(embedding) tensor<int8>(x[96])
            query(float_embedding) tensor<float>(x[768])
        }

        rank chunks {
            element-gap: 0 # Fixed length chunking should not cause any positional gap between elements
        }
        function chunk_text_scores() {
            expression: elementwise(bm25(chunks),chunk,float)
        }

        function chunk_emb_vecs() {
            expression: unpack_bits(attribute(chunk_embeddings))
        }

        function chunk_dot_prod() {
            expression: reduce(query(float_embedding) * chunk_emb_vecs(), sum, x)
        }

        function vector_norms(t) {
            expression: sqrt(sum(pow(t, 2), x))
        }
        function chunk_sim_scores() {
            expression: chunk_dot_prod() / (vector_norms(chunk_emb_vecs()) * vector_norms(query(float_embedding)))
        }

        function top_3_chunk_text_scores() {
            expression: top(3, chunk_text_scores())
        }

        function top_3_chunk_sim_scores() {
            expression: top(3, chunk_sim_scores())
        }

        function avg_top_3_chunk_text_scores() {
            expression: reduce(top_3_chunk_text_scores(), avg, chunk)
        }
        function avg_top_3_chunk_sim_scores() {
            expression: reduce(top_3_chunk_sim_scores(), avg, chunk)
        }
        
        function max_chunk_text_scores() {
            expression: reduce(chunk_text_scores(), max, chunk)
        }

        function max_chunk_sim_scores() {
            expression: reduce(chunk_sim_scores(), max, chunk)
        }

        first-phase {
            expression {
                # Not used in this profile
                bm25(title) + 
                bm25(chunks) +
                max_chunk_sim_scores() +
                max_chunk_text_scores()
            }
        }

        second-phase {
            expression: random
        }
    }
```

As you can see, we rely on the `bm25` and different vector similarity features (both document-level and chunk-level) for the first-phase ranking.
These are relatively cheap to calculate, and will likely provide good enough ranking signals for the first-phase ranking.

Running the command below will save a .csv-file with the collected features, which can be used to train a ranking model for the first-phase ranking.

<pre>
python eval/collect_pyvespa.py --collect_matchfeatures 
</pre>

Our output file looks like this:

<style>
/* keep the 1-pixel borders */
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;   /* so adjacent borders overlap cleanly */
}

/* width stays the same */
th { width: 120px; }

/* add breathing room for header and body cells */
th, td {
  padding: 6px 10px;   /* top-bottom 6 px, left-right 10 px — tweak as you like */
}
</style>
<table>
  <thead>
    <tr>
      <th>query_id</th>
      <th>doc_id</th>
      <th>relevance_label</th>
      <th>relevance_score</th>
      <th>match_avg_top_3_chunk_sim_scores</th>
      <th>match_avg_top_3_chunk_text_scores</th>
      <th>match_bm25(chunks)</th>
      <th>match_bm25(title)</th>
      <th>match_max_chunk_sim_scores</th>
      <th>match_max_chunk_text_scores</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>alex_q_01</td>
      <td>50</td>
      <td>1</td>
      <td>0.660597</td>
      <td>0.248329</td>
      <td>8.444725</td>
      <td>7.717984</td>
      <td>0.</td>
      <td>0.268457</td>
      <td>8.444725</td>
    </tr>
    <tr>
      <td>alex_q_01</td>
      <td>82</td>
      <td>1</td>
      <td>0.649638</td>
      <td>0.225300</td>
      <td>12.327676</td>
      <td>18.611592</td>
      <td>2.453409</td>
      <td>0.258905</td>
      <td>15.644889</td>
    </tr>
    <tr>
      <td>alex_q_01</td>
      <td>1</td>
      <td>1</td>
      <td>0.245849</td>
      <td>0.358027</td>
      <td>15.100841</td>
      <td>23.010389</td>
      <td>4.333828</td>
      <td>0.391143</td>
      <td>20.582403</td>
    </tr>
    <tr>
      <td>alex_q_01</td>
      <td>28</td>
      <td>0</td>
      <td>0.988250</td>
      <td>0.278074</td>
      <td>0.179929</td>
      <td>0.197420</td>
      <td>0.</td>
      <td>0.278074</td>
      <td>0.179929</td>
    </tr>
    <tr>
      <td>alex_q_01</td>
      <td>23</td>
      <td>0</td>
      <td>0.968268</td>
      <td>0.203709</td>
      <td>0.182603</td>
      <td>0.196956</td>
      <td>0.</td>
      <td>0.203709</td>
      <td>0.182603</td>
    </tr>
  </tbody>
</table>

Note that the `relevance_score` in this table is just the random expression we used in the `second-phase` of the `collect-training-data` rank profile, and will be dropped before training the model.

### Training a first-phase ranking model

As you recall, a first-phase ranking expression must be cheap to evaluate.
This most often means a heuristic handwritten combination of match features, or a linear model trained on match features.

We will demonstrate how to train a simple Logistic Regression model to predict relevance based on the collected match features.
The full training script can be found in the TODO. 

Some "gotchas" to be aware of:

* We sample an equal number of relevant and random documents for each query, to avoid class imbalance.
* We make sure that we drop `query_id` and `doc_id` columns.
* We apply standard scaling to the features before training the model. We apply the inverse transform to the model coefficients after training, so that we can use them in Vespa.
* We do 5-fold stratified cross-validation to evaluate the model performance, ensuring that each fold has a balanced number of relevant and random documents.
* We also make sure to have an unseen set of test queries to evaluate the model on, to avoid overfitting.

Run the training script:

```bash
python eval/train_logistic_regression.py
```

Expect output like this:

```txt
------------------------------------------------------------
      Cross-Validation Results (5-Fold, Standardized)       
------------------------------------------------------------
Metric             | Mean               | Std Dev           
------------------------------------------------------------
Accuracy           | 0.9024             | 0.0294            
Precision          | 0.9236             | 0.0384            
Recall             | 0.8818             | 0.0984            
F1-Score           | 0.8970             | 0.0415            
Log Loss           | 0.2074             | 0.0353            
ROC AUC            | 0.9749             | 0.0103            
Avg Precision      | 0.9764             | 0.0117            
------------------------------------------------------------
Transformed Coefficients (for original unscaled features):
--------------------------------------------------
avg_top_3_chunk_sim_scores   : 13.383840
avg_top_3_chunk_text_scores  : 0.203145
bm25(chunks)                 : 0.159914
bm25(title)                  : 0.191867
max_chunk_sim_scores         : 10.067169
max_chunk_text_scores        : 0.153392
Intercept                    : -7.798639
--------------------------------------------------
```

Which seems quite good. With such a small dataset however, it is easy to overfit. Let us evaluate on the unseen test queries to see how well the model generalizes.

First, we need to add the coefficients as inputs to a new rank profile in our schema, so that we can use them in Vespa.

```txt
rank-profile learned-linear inherits collect-training-data {
        match-features: 
        inputs {
            query(embedding) tensor<int8>(x[96])
            query(float_embedding) tensor<float>(x[768])
            query(intercept) double
            query(avg_top_3_chunk_sim_scores_param) double
            query(avg_top_3_chunk_text_scores_param) double
            query(bm25_chunks_param) double
            query(bm25_title_param) double
            query(max_chunk_sim_scores_param) double
            query(max_chunk_text_scores_param) double
        }
        first-phase {
            expression {
                query(intercept) + 
                query(avg_top_3_chunk_sim_scores_param) * avg_top_3_chunk_sim_scores() +
                query(avg_top_3_chunk_text_scores_param) * avg_top_3_chunk_text_scores() +
                query(bm25_title_param) * bm25(title) + 
                query(bm25_chunks_param) * bm25(chunks) +
                query(max_chunk_sim_scores_param) * max_chunk_sim_scores() +
                query(max_chunk_text_scores_param) * max_chunk_text_scores()
            }
        }
        summary-features {
            top_3_chunk_sim_scores
        }
        
    }
```

For simplicity, we will also add the values of the coefficients as query parameters to a new query profile.

```xml
<query-profile id="hybrid">
    <field name="schema">doc</field>
    <field name="ranking.features.query(embedding)">embed(@query)</field>
    <field name="ranking.features.query(float_embedding)">embed(@query)</field>
    <field name="ranking.features.query(intercept)">-7.798639</field>
    <field name="ranking.features.query(avg_top_3_chunk_sim_scores_param)">13.383840</field>
    <field name="ranking.features.query(avg_top_3_chunk_text_scores_param)">0.203145</field>
    <field name="ranking.features.query(bm25_chunks_param)">0.159914</field>
    <field name="ranking.features.query(bm25_title_param)">0.191867</field>
    <field name="ranking.features.query(max_chunk_sim_scores_param)">10.067169</field>
    <field name="ranking.features.query(max_chunk_text_scores_param)">0.153392</field>
    <field name="yql">
        select *
        from %{schema}
        where userInput(@query) or
        ({label:"title_label", targetHits:100}nearestNeighbor(title_embedding, embedding)) or
        ({label:"chunks_label", targetHits:100}nearestNeighbor(chunk_embeddings, embedding))
    </field>
    <field name="hits">10</field>
    <field name="ranking.profile">learned-linear</field>
    <field name="presentation.summary">top_3_chunks</field>
</query-profile>    
```

### Evaluating first-phase ranking

Now we are ready to evaluate our first-phase ranking function.
We can use the [VespaEvaluator](https://vespa-engine.github.io/pyvespa/evaluating-vespa-application-cloud.html#vespaevaluator) from the [pyvespa](https://vespa-engine.github.io/pyvespa/) library to evaluate the first-phase ranking function.

By running the following command

```
python eval/evaluate_ranking.py
```

We run the evaluation script on a set of unseen test queries, and get the following output:

```json
{
    "accuracy@1": 0.0,
    "accuracy@3": 0.0,
    "accuracy@5": 0.05,
    "accuracy@10": 0.3,
    "precision@10": 0.034999999999999996,
    "recall@10": 0.1340909090909091,
    "precision@20": 0.04250000000000001,
    "recall@20": 0.3886363636363636,
    "mrr@10": 0.0476984126984127,
    "ndcg@10": 0.05997203651967424,
    "map@100": 0.06688634552753898,
    "searchtime_avg": 0.022150000000000006,
    "searchtime_q50": 0.0165,
    "searchtime_q90": 0.05550000000000001,
    "searchtime_q95": 0.0604
}
```

For the first phase ranking, we care most about recall, as we just want to make sure that the candidate documents are ranked high enough to be included in the second-phase ranking. (the default number of documents that will be exposed to second-phase is 10 000, but can be controlled by the `rerank-count` parameter).

We can see that our recall@20 is 0.39, which is not very good, but an OK start, and a lot better than random. We could later aim to improve on this by approximating a better function after we have learned one for second-phase ranking.

We can also see that our search time is quite fast, with an average of 22ms. You should consider whether this is well within your latency budget, as you want some headroom for second-phase ranking.

The ranking performance is not great, but this is expected for a simple linear model, where it only needs to be good enough to make sure that the most relevant documents are passed to the second-phase ranking, where ranking performance matters a lot more.


## Second-phase ranking

For the second-phase ranking, we can afford to use a more expensive ranking expression, since we will only run it on the top-k documents from the first-phase ranking (defined by the `rerank-count` parameter, which defaults to 10,000 documents).

This is where we can significantly improve ranking quality by using more sophisticated models and features that would be too expensive to compute for all matched documents.

### Collecting features for second-phase ranking

For second-phase ranking, we request Vespa's default set of rank features, which includes a comprehensive set of text features. See the [rank features documentation](../reference/rank-features.html) for complete details.

We can collect both match features and rank features by running:

```bash
python eval/collect_pyvespa.py --collect_rankfeatures --collect_matchfeatures --collector_name rankfeatures-secondphase
```

This collects approximately 194 features, providing a rich feature set for training more sophisticated ranking models.

### Training a GBDT model for second-phase ranking

With the expanded feature set, we can train a Gradient Boosted Decision Tree (GBDT) model to predict document relevance. We use [LightGBM](../lightgbm.html) for this purpose. 

Vespa also supports [XGBoost](../xgboost.html) and [ONNX](../onnx.html) models.

To train the model, we run the following command:

```bash
python eval/train_lightgbm.py --input_file eval/output/Vespa-training-data_match_rank_second_phase_20250623_135819.csv
```

The training process includes several important considerations:

* **Cross-validation**: We use 5-fold stratified cross-validation to evaluate model performance and prevent overfitting
* **Hyperparameter tuning**: We set conservative hyperparameters to prevent growing overly large and deep trees, especially important for smaller datasets
* **Feature selection**: Features with zero importance during cross-validation are excluded from the final model
* **Early stopping**: Training stops when validation scores don't improve for 50 rounds

Example training output:

```txt
------------------------------------------------------------
             Cross-Validation Results (5-Fold)             
------------------------------------------------------------
Metric             | Mean               | Std Dev           
------------------------------------------------------------
Accuracy           | 0.9214             | 0.0664            
ROC AUC            | 0.9863             | 0.0197            
------------------------------------------------------------
Overall CV AUC: 0.9249 • ACC: 0.9216
------------------------------------------------------------
```

### Feature importance analysis

The trained model reveals which features are most important for ranking quality. For our sample application, the top features include:

| Feature                     | Importance |
| --------------------------- | ---------- |
| nativeProximity             | 168.8498   |
| firstPhase                  | 151.7382   |
| max_chunk_sim_scores        | 69.4377    |
| avg_top_3_chunk_text_scores | 56.5079    |
| avg_top_3_chunk_sim_scores  | 31.8700    |
| nativeRank                  | 20.0716    |
| nativeFieldMatch            | 15.9914    |
| elementSimilarity(chunks)   | 9.7003     |

Key observations:

* **Text proximity features** ([nativeProximity](../reference/nativerank.html#nativeProximity)) are highly valuable for understanding query-document relevance
* **First-phase score** (`firstPhase`) being important validates that our first-phase ranking provides a good foundation
* **Chunk-level features** (both text and semantic) contribute significantly to ranking quality
* **Traditional text features** like [nativeRank](../reference/nativerank.html#nativeRank) and [bm25](../reference/bm25.html#ranking-function) remain important

### Integrating the GBDT model into Vespa

The trained LightGBM model is exported and added to your Vespa application package:

```txt
app/
├── models/
│   └── lightgbm_model.json
```

Create a new rank profile that uses this model:

```txt
rank-profile second-with-gbdt inherits collect-training-data {
    ...

    second-phase {
        expression: lightgbm("lightgbm_model.json")
    }

    ...
}
```

### Evaluating second-phase ranking performance

Evaluate the GBDT-powered second-phase ranking on unseen test queries:

```bash
python evaluate_ranking.py --second_phase
```

Expected results show significant improvement over first-phase ranking:

```json
{
    "accuracy@1": 0.9,
    "accuracy@3": 0.95,
    "accuracy@5": 1.0,
    "accuracy@10": 1.0,
    "precision@10": 0.23,
    "recall@10": 0.93,
    "precision@20": 0.13,
    "recall@20": 0.99,
    "mrr@10": 0.94,
    "ndcg@10": 0.85,
    "map@100": 0.78,
    "searchtime_avg": 0.035
}
```

This represents a dramatic improvement over first-phase ranking, with:

* **accuracy@10** improving from 0.3 to 1.0
* **recall@20** improving from 0.39 to 0.99
* **NDCG@10** improving from 0.06 to 0.85

The slight increase in search time (from 22ms to 35ms average) is well worth the quality improvement.

### Query profiles with GBDT ranking

Create new query profiles that leverage the improved ranking:

```xml
<query-profile id="hybrid-with-gbdt" inherits="hybrid">
    <field name="ranking.profile">second-with-gbdt</field>
    <field name="hits">20</field>
</query-profile>

<query-profile id="rag-with-gbdt" inherits="hybrid-with-gbdt">
    <field name="hits">50</field>
    <field name="searchChain">openai</field>
    <field name="presentation.format">sse</field>
</query-profile>
```

Test the improved ranking:

```bash
vespa query query="what are key points learned for finetuning llms?" queryProfile=hybrid-with-gbdt
```

For RAG applications with LLM generation:

```bash
vespa query \
    --timeout 60 \
    --header="X-LLM-API-KEY:<your-api-key>" \
    query="what are key points learned for finetuning llms?" \
    queryProfile=rag-with-gbdt
```

### Best practices for second-phase ranking

**Model complexity considerations:**
* Use more sophisticated models (GBDT, neural networks) that would be too expensive for first-phase
* Take advantage of the reduced candidate set (typically 100-10,000 documents)
* Include expensive text features like `nativeProximity` and `fieldMatch`

**Feature engineering:**

* Combine first-phase scores with additional text and semantic features
* Use chunk-level aggregations (max, average, top-k) to capture document structure
* Include metadata signals that require complex computations

**Training data quality:**

* Use the first-phase ranking to generate better training data
* Consider having LLMs generate relevance judgments for top-k results
* Iteratively improve with user interaction data when available

**Performance monitoring:**
* Monitor latency impact of second-phase ranking
* Adjust `rerank-count` based on quality vs. performance trade-offs
* Consider using different models for different query types or use cases

The second-phase ranking represents a crucial step in building high-quality RAG applications, providing the precision needed for effective LLM context while maintaining reasonable query latencies.

## (Optional) Global-phase ranking

We also have the option of configuring [global-phase](../reference/schema-reference.html#globalphase-rank) ranking, which can rerank the top k (as set by `rerank-count` parameter) documents from the second-phase ranking.

Common options for global-phase are [cross-encoders](..cross-encoders.html#) or another GBDT model, trained for better separating top ranked documents on objectives such as [LambdaMart](https://xgboost.readthedocs.io/en/latest/tutorials/learning_to_rank.html). For RAG applications, we consider this less important than for search applications where the results are mainly consumed by an human, as LLMs don't care that much about the ordering of the results.

## Further improvements

Finally, we will sketch out some opportunities for further improvements.
As you have seen, we started out with only binary relevance labels for a few queries, and trained a model based on the relevant docs and a set of random documents.

As you may have noted, we have not discussed what most people think about when discussing RAG evals, evaluating the "Generation"-step. There are several tools available to do this, for example [ragas](https://docs.ragas.io/en/stable/) and [ARES](https://github.com/stanford-futuredata/ARES). We refer to other sources for details on this, as this tutorial is probably enough to digest as it is. 

This was useful initially, as we had no better way to retrieve the candidate documents.
Now, that we have a reasonably good second-phase ranking, we could potentially generate a new set of relevance labels for queries that we did not have labels for by having an LLM do relevance judgments of the top k returned hits. This training dataset would likely be even better in separating the top documents.

## Summary

In this tutorial, we have built a complete RAG application using Vespa, starting from a simple retrieval phase with binary vectors and text matching, to a sophisticated two-phase ranking system with GBDT models.

By using the principles demonstrated in this tutorial, you can create high-quality RAG applications that can scale to any dataset size, and any query load.

We hope to have provided a solid foundation for how to think about developing a RAG application with Vespa, and how to iteratively improve it over time.

## FAQ

* **Q: Do I need to use an LLM with Vespa?**
  A: No, you are free to use Vespa as a search engine. We provide the option of calling out to LLMs from within a Vespa application for reduced latency compared to sending large search results sets several times over network as well as the option to deploy Local LLMs, optionally in your own infrastructure if you prefer. See [Vespa Cloud Enclave](https://docs.vespa.ai/en/cloud/enclave/enclave.html)
* **Q: Why do we use binary vectors for the document embeddings?**
  A: Binary vectors takes up a lot less memory and are faster to compute distances on, with only a slight reduction in quality. See blog [post](https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/) for details.
* **Q: How can you say that Vespa can scale to any data and query load?**
  A: Vespa can scale both the stateless container nodes and content nodes of your application. See [overview](../overview.html) and [elasticity](../elasticity.html) for details. ∂