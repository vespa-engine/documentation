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

We strongly recommend following along this tutorial, by running the steps in the README of our corresponding [sample app](https://github.com/vespa-engine/sample-apps/tree/master/rag-blueprint) or [pyvespa notebook](TODO).

This tutorial will contain more of the reasoning behind the choices and design of the blueprint, as well as pointers to features to consider for customizing to your own application.

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

## Data modelling

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

You may not want to feed every chunk of the top k documents to the LLM.

1. Use all chunks.
2. Use `matched-elements-only` (lexical match).
3. Score and select chunks in the container.
4. Score and select chunks on content-node.
5. Score and select chunks in your frontend.

Compute closeness per chunk in a ranking function; use `elementwise(bm25(chunks), i, double)` for a per-chunk text signal.
Now available: elementwise rank functions and filtering on the content nodes.

You can pick a large document as the searchable unit, while still addressing the potential drawbacks many encounter as follows:

* Pick your (larger) document as your searchable unit.
* Chunk the text-fields automatically on indexing.
* Embed each chunk (enabled through Vespa's multivector support)
* Calculate chunk-level features (e.g. bm25 and embedding similarity) and document-level features. Combine as you want.
* Limit the actual chunks that are returned to the ones that are actually relevant context for the LLM.

**Conclusion:** It's often better to err on the side of slightly larger units.

* LLMs are increasingly capable of handling larger contexts.
* In Vespa, you can index larger units, while avoiding data duplication and performance issues, by returning only the most relevant parts.

Since Vespa version TODO, we added support for automatic [chunking](../reference/indexing-language-reference.html#converters) in the [indexing language](../indexing.html).

Here is our corresponding schema, which defines the searchable unit as a document with a text field, and automatically chunks it into smaller parts of 1024 characters, which each are embedded and indexed separately:

```
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

        field created_timestamp type int {
            indexing: attribute | summary
        }
        field modified_timestamp type int {
            indexing: attribute | summary
        }
        
        field last_opened_timestamp type int {
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
}
```

Keep reading for a reasoning behind the choices in the schema.

### Model metadata and signals as structured fields

**Metadata** — knowledge about your data:

* Authors, publish time, source, links, category, price, …
* Usage: filters, ranking, grouping/aggregation
* Index only metadata that are strong filters

**Signals** — observations about your data:

* Popularity, quality, spam probability, click_probability, …
* Usage: ranking
* Often updated separately via partial updates
* Multiple teams can add their own signals independently

For instance, num

Consider [parent-child](../parent-child.html) relationships for low-cardinality metadata.
Most large scale RAG application schemas contain at least a hundred structured fields.

## Configuring match-phase (retrieval)

This section will contain important considerations for the retrieval-phase of a RAG application in Vespa.
To learn more about the phased ranking approach in Vespa, see the [phased ranking docs](../phased-ranking.html).
The goal of the retrieval phase is to retrieve candidate documents efficiently, and maximize recall, without exposing too many documents to ranking.

### Vector, text or hybrid recall?

As you could see from the schema, we create and index both a text representation and a vector representation for each chunk of the document. This will allow us to use both text-based features and semantic features for both recall and ranking.

The text and vector representation complement each other well:

* **Text-only** → misses recall of semantically similar content
* **Vector-only** → misses recall of specific content not well understood by the embedding models

Our recommendation for this blueprint, is to default to hybrid retrieval:
`{targetHits:400}nearestNeighbor(embeddings_field, query_embedding) or userInput(@query)`

In generic domains, or if you have finetuned an embedding model to your specific data, _consider_ vector-only:
`rank({targetHits:2000}nearestNeighbor(embeddings_field, query_embedding, userInput(@query))=`.
Notice that only the first argument of the `rank`-operator will be used to determine if a document is a match, while all arguments are used for calculating rank features. This mean we can do vector only for matching, but still use text-based features such as `bm25` and `nativeRank` for ranking.
Note that if you do this, it makes sense to increase the number of `targetHits` afor the `nearestNeighbor`-operator. 

### Choosing your embedding model (and strategy)

Choice of embedding model will be a trade-off between inference time (both indexing and query time), memory usage (embedding dimensions) and quality. There are many good open-source models available, and we recommend checking out the [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard), and look at the `Retrieval`-column to gauge performance, while also considering the memory usage, vector dimensions, and context length of the model.

See [model hub](../cloud/model-hub.html) for a list of provided models ready to use with Vespa. See also [Huggingface Embedder](../embedding.html#huggingface-embedder) for details on using other models (exported as ONNX) with Vespa.

In addition to dense vector representation, Vespa supports sparse embeddings (token weights) and multi-vector (ColBERT-style) embeddings.
See our [example notebook](https://vespa-engine.github.io/pyvespa//examples/mother-of-all-embedding-models-cloud.html#bge-m3-the-mother-of-all-embedding-models) of using the bge-m3 model, which supports both, with Vespa.

Vespa also supports [Matryoshka embeddings](https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/), which can be a great way of reducing inference cost for retrieval phases, by using a subset of the embedding dimensions, while using more dimensions for increased precision in the later ranking phases.

For domain-specific applications or less popular languages, you may want to consider finetuning a model on your own data.

### Consider binary vectors for recall

Another decision to make is which precision you will use for your embeddings.
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

For example, if you want to calculate `closeness` for a paged embedding vector in first-phase, consider configuring your retrieval operators (typically `weakAnd` and/or `nearestNeighbor`) so that not too many hits are matched. Another option is to enable match-phase limiting, see [docs](). In essence, you restrict the number of matches by specifying an attribute field.

### Evaluating recall of the retrieval phase

To know whether your retrieval phase is working well, you need to measure recall, number of total matches and the reported time spent.

We can use [`VespaMatchEvaluator`](https://vespa-engine.github.io/pyvespa/api/vespa/evaluation.html#vespa.evaluation.VespaMatchEvaluator) from the pyvespa client library to do this.

For this sample application TODO

### Use WeakAND for text matching

RAG queries tend to be long → AND is unsuitable, OR is too expensive.
Consider for example a typical query from our eval set:

```json
{"query_text": "Find the Python script where I implemented the custom attention layer for the 'SynapseCore' module.",}
```

Terms like 'the', 'I', 'for' is likely very common in the corpus, and would likely not add much value to the weakAnd-operator.
We recommend tuning weakAnd to trade a tiny bit of accuracy for much lower cost.
See [blog post](https://blog.vespa.ai/tripling-the-query-performance-of-lexical-search/) for additional details.
Below are some sane default values for a large corpus (based on wikipedia-dataset):

<pre>
rank-profile optimized inherits baseline {
  filter-threshold: 0.05
  weakand {
    stopword-limit: 0.6
    adjust-target: 0.01
  }
}
</pre>


### Use multiple text fields, consider multiple embeddings

* Index different textual content (text, body, …) as separate indexes.
* Search across them with field sets: `field-set text, body`.

Consider indexing different content as different embeddings:

* Separate indexes for text/body may not be worth the cost.
* Separate indexes for different vector spaces (images) generally are.
* Special case: switching embedding model.

### Use complex linguistics/recall only for precision

Vespa gives you extensive control over linguistics: decide match mode, stemming, normalization, or control generated tokens.

…and token-based recall.
Use more specific operators than WeakAND to match only close occurrences `{near}`, multiple alternatives `{equiv}`, weight items, set connectivity, and apply query-rewrite rules.

Don’t use this to increase recall — improve your embedding model instead.
Consider using it to improve precision when needed.

## Configure ranking

### Use first-phase ranking to reduce cost

GBDT is usually too expensive for all matches.
Use a cheaper first-phase function that approximates the learned model:

* Include a handful of signals (text, vector closeness, metadata).
* Implement as a simple handwritten function, possibly with learned constants (passed in the query).

Signals should include [nativeRank](../reference/nativerank.html#nativerank) or [bm25](../reference/bm25.html#ranking-function) — not [fieldMatch](../reference/rank-features.html#field-match-features-normalized).

* **bm25**: cheapest, strong significance, no proximity, not normalized.
* **nativeRank**: 2 – 3 × costlier, truncated significance, includes proximity, normalized.

Measure quality loss from the cheaper first phase.



### Set up automated evals for fast iteration

So many knobs to tune — quantify their impact.
A small, diverse eval set (20 – 100 queries) is far better than none.
Consider using an LLM to generate questions during feeding.
Add user or stakeholder feedback to the eval set.

* Integrate into CI/CD pipelines (stage environment).
* Gate production deploys with quality-metric conditions.
* Choose metrics relevant to your use case (e.g. recall@100 if top-100 hits feed an LLM).

### Machine-learn ranking using many signals

Ranking functions should leverage many (hundreds) of signals:

* Vector closeness
* Rich text-matching features (bm25, nativeRank, fieldMatch, …)
* Metadata signals
* Functions injecting domain knowledge

Learn a ranking function from these signals, defaulting to GBDT models (XGBoost or LightGBM).
Use an LLM to help create training data.

## Structuring your vespa application

### Manage queries in query profiles

Query profiles let you maintain collections of query parameters in one file.
Clients choose a query profile → the profile sets everything else.
This lets us change behavior for a use case without involving clients.

For this blueprint, we have created 3 different query profile, to support 3 different use cases:

1. `rag`
2. `hybrid`
3. `deepresearch`

### **_hybrid_** query profile

This query profile will be the one used by clients for traditional search, where the user is presented a limited number of hits.
Our other query profiles will inherit this one (but may override some fields).

```xml
<query-profile id="hybrid">
    <field name="schema">doc</field>
    <field name="ranking.features.query(embedding)">embed(@query)</field>
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

Again, we will inherit from the `hybrid` query profile, but override with parameters that favor recall over latency.
We will also increase number of hits to be returned.

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

### Separating out rank profiles

Assume you’ll need many ranking models — to bucket-test alternatives continuously and to serve different use cases.

Separate common functions/setup into parent rank profiles and use `.profile` files.

(Slides list examples such as nativerank_parent.profile, nearest_neighbor.profile, bm_nn.profile, etc.)
