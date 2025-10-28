---
# Copyright Vespa.ai. All rights reserved.
title: Using machine-learned models from Vespa Cloud
category: cloud
---

Vespa Cloud provides a set of machine-learned models that you can use
in your applications. These models will always be available on Vespa Cloud and are
[frozen models](https://blog.vespa.ai/tailoring-frozen-embeddings-with-vespa/). You
can also bring your own embedding model, by deploying it in the Vespa application package.

You specify to use a model provided by Vespa Cloud by setting the `model-id`
attribute where you specify a model config. For example, when configuring the
[Huggingface embedder](/en/embedding.html#huggingface-embedder)
provided by Vespa, you can write:

```
{% highlight xml %}




    ...

{% endhighlight %}
```

With this, your application will have support for
[text embedding](/en/embedding.html#embedding-a-query-text)
inference for both queries and documents. Nodes that have been provisioned with GPU acceleration, will automatically
use GPU for embedding inference.

## Vespa Cloud Embedding Models

Models on Vespa model hub are selected open-source embedding models with
great performance. See the [Massive Text Embedding Benchmark (MTEB) Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) for details.
These embedding models are useful for retrieval (semantic search), re-ranking, clustering, classification, and more.

### Huggingface Embedder

These models are available for the Huggingface Embedder `type="hugging-face-embedder"`.
All these models supports both mapping from `string` or `array<string>` to tensor representations.
The output tensor [cell-precision](/en/performance/feature-tuning.html#cell-value-types)
can be `<float>`  or `<bfloat16>`.

| nomic-ai-modernbert | |
| --- | --- |
| Trained from ModernBERT-base on the Nomic Embed datasets, bringing the new advances of ModernBERT to embeddings. | |
| Model id | `nomic-ai-modernbert` |
| Tensor definition | `tensor<float>(x[768])` (supports Matryoshka, so `x[256]` is also possible) |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| Source | <https://huggingface.co/nomic-ai/modernbert-embed-base> @ 92168cb |
| Language | English |
| Component declaration | ``` {% highlight xml %}                       token_embeddings         8192                      search_query:             search_document:               {% endhighlight %} ``` |
| lightonai-modernbert-large | |
| Trained from ModernBERT-large on the Nomic Embed datasets, bringing the new advances of ModernBERT to embeddings. | |
| Model id | `lightonai-modernbert-large` |
| Tensor definition | `tensor<float>(x[1024])` |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| Source | <https://huggingface.co/lightonai/modernbert-embed-large> @ b3a781f |
| Language | English |
| Component declaration | ``` {% highlight xml %}                       8192                      search_query:             search_document:               {% endhighlight %} ``` |
| alibaba-gte-modernbert | |
| GTE (General Text Embedding) model trained from ModernBERT-base. | |
| Model id | `alibaba-gte-modernbert` |
| Tensor definition | `tensor<float>(x[768])` (supports Matryoshka, so `x[256]` is also possible) |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| Source | <https://huggingface.co/Alibaba-NLP/gte-modernbert-base> @ 3ab3f8c |
| Language | English |
| Component declaration | ``` {% highlight xml %}                       8192         cls      {% endhighlight %} ``` |
| e5-small-v2 | |
| The smallest and most cost-efficient model from the *E5* family. | |
| Model-id | e5-small-v2 |
| Tensor definition | `tensor<float>(x[384])` or `tensor<float>(p{},x[384])` |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [MIT](https://github.com/microsoft/unilm/blob/master/LICENSE) |
| Source | <https://huggingface.co/intfloat/e5-small-v2> |
| Language | English |
| Comment | See [using E5 models](#using-e5-models) |
| e5-base-v2 | |
| The base model of the *E5* family. | |
| Model-id | e5-base-v2 |
| Tensor definition | `tensor<float>(x[768])` or `tensor<float>(p{},x[768])` |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [MIT](https://github.com/microsoft/unilm/blob/master/LICENSE) |
| Source | <https://huggingface.co/intfloat/e5-base-v2> |
| Language | English |
| Comment | See [using E5 models](#using-e5-models) |
| e5-large-v2 | |
| The largest model of the *E5* family, at time of writing, this is the best performing embedding model on the MTEB benchmark. | |
| Model-id | e5-large-v2 |
| Tensor definition | `tensor<float>(x[1024])` or `tensor<float>(p{},x[1024])` |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [MIT](https://github.com/microsoft/unilm/blob/master/LICENSE) |
| Source | <https://huggingface.co/intfloat/e5-large-v2> |
| Language | English |
| Comment | See [using E5 models](#using-e5-models) |
| multilingual-e5-base | |
| The multilingual model of the *E5* family. Use this model for multilingual queries and documents. | |
| Model-id | multilingual-e5-base |
| Tensor definition | `tensor<float>(x[768])` or `tensor<float>(p{},x[768])` |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [MIT](https://github.com/microsoft/unilm/blob/master/LICENSE) |
| Source | <https://huggingface.co/intfloat/multilingual-e5-base> |
| Language | Multilingual |
| Comment | See [using E5 models](#using-e5-models) |

#### Using E5 Models

The E5 family uses keywords with the input to differentiate query and document side embedding.

The query text should be prefixed with *"query: "*.
In this example the original user query is *how to format e5 queries*.

```
{% highlight json %}
{
  "yql": "select doc_id from doc where ({targetHits:10}nearestNeighbor(embeddings,e))",
  "input.query(e)": "embed(e5, \"query: how to format e5 queries\")"
}
{% endhighlight %}
```

The same technique also must be applied for document side embedding inference.
The input text should be prefixed with *"passage: "*

```
{% highlight raw %}
field embeddings type tensor(p{}, x[768]) {
  indexing {
    input chunks |
	  for_each {
	    "passage: " . (input title || "") . " " . ( _ || "")
	  } | embed e5 | attribute
  }
}
{% endhighlight %}
```

The above example reads a `chunks` field of type `array<string>`,
and prefixes each item with "passage: ", followed by the concatenation
of the title and the item chunk (*_*).
See [execution value example](/en/indexing.html#execution-value-example).

### Bert Embedder

These models are available for the [Bert Embedder](/en/embedding.html#bert-embedder)
`type="bert-embedder"`:

```
{% highlight xml %}





    ...

{% endhighlight %}
```

Note bert-embedder requires both `transformer-model` and `tokenizer-vocab`.

| minilm-l6-v2 | |
| --- | --- |
| A small, fast sentence-transformer model. | |
| Model-id | minilm-l6-v2 |
| Tensor definition | `tensor<float>(x[384])` or `tensor<float>(p{},x[384])` |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| Source | <https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2> |
| Language | English |
| mpnet-base-v2 | |
| A larger, but better than **minilm-l6-v2** sentence-transformer model. | |
| Model-id | mpnet-base-v2 |
| Tensor definition | `tensor<float>(x[768])` or `tensor<float>(p{},x[768])` |
| [distance-metric](/en/reference/schema-reference.html#distance-metric) | `angular` |
| License | [apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| Source | <https://huggingface.co/sentence-transformers/all-mpnet-base-v2> |
| Language | English |

### Tokenization Embedders

These are embedder implementations that tokenize text and embed string to the vocabulary identifiers.
These are most useful for creating the tensor inputs to re-ranking models that take both the query and document token identifiers as input.
Find examples in the
[sample applications](https://github.com/vespa-engine/sample-apps/blob/master/README.md#vector-search-hybrid-search-and-embeddings).

| bert-base-uncased | |
| --- | --- |
| A vocabulary text (*vocab.txt*) file on the format expected by [WordPiece](/en/reference/embedding-reference#wordpiece-embedder): A text token per line. | |
| Model-id | bert-base-uncased |
| License | [apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
| Source | <https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2> |
| e5-base-v2-vocab | |
| A *tokenizer.json* configuration file on the format expected by [HF tokenizer](/en/reference/embedding-reference#huggingface-tokenizer-embedder). This tokenizer configuration can be used with `e5-base-v2`, `e5-small-v2` and `e5-large-v2`. | |
| Model-id | e5-base-v2-vocab |
| License | [MIT](https://github.com/microsoft/unilm/blob/master/LICENSE) |
| Source | <https://huggingface.co/intfloat/e5-base-v2> |
| Language | English |
| multilingual-e5-base-vocab | |
| A *tokenizer.json* configuration file on the format expected by [HF tokenizer](/en/reference/embedding-reference#huggingface-tokenizer-embedder). This tokenizer configuration can be used with `multilingual-e5-base-vocab`.| Model-id | multilingual-e5-base-vocab | | License | [MIT](https://github.com/microsoft/unilm/blob/master/LICENSE) | | Source | <https://huggingface.co/intfloat/multilingual-e5-base> | | Language | Multilingual | | |

### Significance models

These are [global significance models](/en/significance.html#significance-models-in-servicesxml)
that can be added to [significance element in services.xml](/en/reference/services-search.html#significance).

| significance-en-wikipedia-v1 | |
| --- | --- |
| This significance model was generated from [English Wikipedia dump data from 2024-08-01](https://dumps.wikimedia.org/enwiki/20240801/). Available in Vespa as of version 8.426.8. | |
| Model-id | significance-en-wikipedia-v1 |
| License | [Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0) License](https://creativecommons.org/licenses/by-sa/3.0/deed.en). |
| Source | <https://data.vespa-cloud.com/significance_models/significance-en-wikipedia-v1.json.zst> |
| Language | English |

## Creating applications working both self-hosted and on Vespa Cloud

You can also specify both a `model-id`, which will be used on Vespa Cloud,
and a url/path, which will be used on self-hosted deployments:

```
{% highlight xml %}

{% endhighlight%}
```

This can be useful for example to create an application package which uses models from Vespa Cloud
for production and a scaled-down or dummy model for self-hosted development.

## Using Vespa Cloud models with any config

Specifying a model-id can be done for any
[config field of type `model`](/en/configuring-components.html#adding-files-to-the-component-configuration),
whether the config is from Vespa or defined by you.
