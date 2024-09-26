---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Significance Model"
---

*Significance* is a measure of how rare a term is in a collection of documents.
Rare terms like "neurotransmitter" are weighted higher during ranking than common terms like "the".
Significance is calculated as inverse document frequency (IDF):

$$ IDF(t, N) = log(\frac{N}{n_t}) $$

where:
- $$ N $$ is the total number of documents
- $$ n_t $$ is the number of documents containing term $$ t $$

Variations of IDF are used in [bm25](reference/bm25.html) and [nativeRank](reference/nativerank.html).

*Significance model* provides the data necessary to calculate IDF, i.e. $$ n_t $$ for each term and $$ N $$ for the document collection.
We distinguish between *local and global* significance models.
A local model is node-specific and a global model is shared across nodes.

# Local significance model

For string fields indexed with [bm25](reference/bm25.html) or [nativeRank](reference/nativerank.html),
Vespa creates a local significance model on each content node.
Each node uses its own local model for the queries it processes.

Nodes can have different significance values for the same query term.
In large collections, this difference is usually small and doesn’t affect ranking quality.

Ranking becomes non-deterministic in the following situations:
1. When new documents are added, local models on affected content nodes are updated.
2. When the content cluster [redistributes documents](elasticity.html) across nodes, e.g. adding, removing nodes for scaling and failure recovery, the models change on the nodes involved.
3. When using [grouped distribution](elasticity.html#grouped-distribution),
queries can return different results depending on which group processes them.

Local significance models are not available in [streaming search](streaming-search.html) because inverted indexes are not constructed so IDF values can't be extracted.
All significance values are set to 1, which is the default value for unknown terms.
The lack of significance values may [substantially degrade the ranking quality](blog/global-significance.html).

A global significance model addresses these issues.

# Global significance model

In a *global significance model*, significance values are shared across nodes and don’t change when new documents are added. There are two ways to provide a global model:

1. Include [significance values in a query](#significance-values-in-a-query).
2. Specify [models in services.xml](#significance-models-in-servicesxml).


## Significance values in a query

Significance values can be specified in [YQL](https://docs.vespa.ai/en/query-language.html) using the [significance feature](reference/query-language-reference.html#significance), e.g.

```sql
select * from example where content contains ({significance:0.9}"neurotransmitter")
```

Alternatively, a [custom Searcher](https://docs.vespa.ai/en/searcher-development.html#writing-a-searcher) can be used to add document frequency to query terms:

```java
private void setIDF(WordItem item, frequency: long, numDocuments: long) {
    var word = item.getWord();
    word.setDocumentFrequency(new DocumentFrequency(frequency, numDocuments));
}
```

## Significance models in services.xml

The `significance` element in [services.xml](reference/services-search.html#significance) specifies one or more models:

```xml
<container version="1.0">
    <search>
        <significance>
            <model model-id="wikimedia"/>
            <model url="https://some/uri/mymodel.multilingual.json" />
            <model path="models/mymodel.no.json.zst" />
        </significance>
    </search>
</container>
```

Models are identified by `model-id` or by providing `url` or `path` to a model file in the application package.
The `path` should be relative to the package root.
The order in which the models are specified determines the model precedence, with the last model overriding the previous ones.
See [model resolution](#model-resolution).

In addition to adding models in [services.xml](reference/services-search.html#significance),
the `significance` feature must be enabled in the [`rank-profile` section of the schema](reference/schema-reference.html#significance), e.g.

```xml
schema example {
    document example {
        field content type string {
            indexing: index | summary
            index: enable-bm25
        }
    }

    rank-profile default {
        significance {
            use-model: true
        }
    }
}
```

The model will be applied to all query terms except those that already have significance values from the query.

### Significance model file

The significance model file is a JSON file that contains term document frequencies and document count for one or more languages, e.g.

```json
{
  "version": 1,
  "id": "wikipedia",
  "description": "Some optional description",
  "languages": {
    "en": {
      "description": "Some optional description for English model",
      "document-count": 1000,
      "document-frequencies": {
        "and": 500,
        "car": 100,
        ...
      }
    },
    "no": {
      "description": "Some optional description for Norwegian model",
      "document-count": 800,
      "document-frequencies": {
        "bil": 80,
        "og": 400,
        ...
      }
    }
  }
}
```

Significance model files can be compressed with <a href="https://facebook.github.io/zstd/">zstandard</a>.

Vespa provides a <a href="operations-selfhosted/vespa-cmdline-tools.html#vespa-significance">CLI tool for generating model files from vespa-feed document files</a>.

### Model resolution

Model resolution selects a model from the models specified in [services.xml](#significance-models-in-servicesxml) based on the language of the query.
The language can be either [explicitly tagged](reference/query-api-reference.html#model.language) or [implicitly detected](linguistics.html#query-language-detection).

The resolution logic is as follows:
- When language is explicitly tagged
  - Select the last model specified in [services.xml](#significance-models-in-servicesxml) that has the tagged language.
    Fail if none are available.
  - If the language is tagged as “un” (unknown), select the model for “un” first, fall back to “en” (english).
    Fail if none are available.
- When language is implicitly detected
  - Select the last specified model with the detected language. If not available, try “un” and then “en” languages.
    Fail if none are available.
