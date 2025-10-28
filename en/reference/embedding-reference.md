---
# Copyright Vespa.ai. All rights reserved.
title: "Embedding Reference"
---

Reference configuration for [embedders](../embedding.html).

## Model config reference

Embedder models use the [model](config-files.html#model) type configuration which accepts the attributes
`model-id`, `url` or `path`.
Multiple of these can be specified as a single config value, where one is used depending on the deployment environment:
* If a `model-id` is specified and the application is deployed on Vespa Cloud, the `model-id` is used.
* Otherwise, if a `url` is specified, it is used
* Otherwise, `path` is used.

When using `path`, the model files must be supplied in the
Vespa [application package](../application-packages.html#deploying-remote-models).

## Huggingface Embedder

An embedder using any [Huggingface tokenizer](https://huggingface.co/docs/tokenizers/index),
including multilingual tokenizers,
to produce tokens which is then input to a supplied transformer model in ONNX model format.

The Huggingface embedder is configured in [services.xml](services.html),
within the `container` tag:

```
{% highlight xml %}





          query:
          passage:


    ...

{% endhighlight %}
```

### Private Model Hub

You may also use models hosted in a
[private Huggingface model hub](https://huggingface.co/docs/hub/en/repositories-settings#private-repositories).

Retrieve an API key from Huggingface with the appropriate permissions, and add it to the [vespa secret store.](/en/cloud/security/secret-store)
Add the secret to the container `<secrets>` and refer to it in your Huggingface model configuration:

```
{% highlight xml %}








{% endhighlight %}
```

### Huggingface embedder reference config

In addition to [embedder ONNX parameters](#embedder-onnx-reference-config):

| Name | Occurrence | Description | Type | Default |
| --- | --- | --- | --- | --- |
| transformer-model | One | Use to point to the transformer ONNX model file | [model-type](#model-config-reference) | N/A |
| tokenizer-model | One | Use to point to the `tokenizer.json` Huggingface tokenizer configuration file | [model-type](#model-config-reference) | N/A |
| max-tokens | One | The maximum number of tokens accepted by the transformer model | numeric | 512 |
| transformer-input-ids | One | The name or identifier for the transformer input IDs | string | input_ids |
| transformer-attention-mask | One | The name or identifier for the transformer attention mask | string | attention_mask |
| transformer-token-type-ids | One | The name or identifier for the transformer token type IDs. If the model does not use `token_type_ids` use `<transformer-token-type-ids/>` | string | token_type_ids |
| transformer-output | One | The name or identifier for the transformer output | string | last_hidden_state |
| pooling-strategy | One | How the output vectors of the ONNX model is pooled to obtain a single vector representation. Valid values are `mean`,`cls` and `none` | string | mean |
| normalize | One | A boolean indicating whether to normalize the output embedding vector to unit length (length 1). Useful for `prenormalized-angular` [distance-metric](schema-reference.html#distance-metric) | boolean | false |
| prepend | Optional | Prepend instructions that are prepended to the text input before tokenization and inference. Useful for models that have been trained with specific prompt instructions. The instructions are prepended to the input text.  * Element <query> - Optional query prepend instruction. * Element <document> - Optional document prepend instruction.  ``` {% highlight xml %}            query:       passage:     {% endhighlight %} ``` | Optional <query> <document> elements. |  |

## Bert embedder

The Bert embedder is configured in [services.xml](services.html),
within the `container` tag:

```
{% highlight xml %}






{% endhighlight %}
```

### Bert embedder reference config

In addition to [embedder ONNX parameters](#embedder-onnx-reference-config):

| Name | Occurrence | Description | Type | Default |
| --- | --- | --- | --- | --- |
| transformer-model | One | Use to point to the transformer ONNX model file | [model-type](#model-config-reference) | N/A |
| tokenizer-vocab | One | Use to point to the Huggingface `vocab.txt` tokenizer file with valid wordpiece tokens. Does not support `tokenizer.json` format. | [model-type](#model-config-reference) | N/A |
| max-tokens | One | The maximum number of tokens allowed in the input | integer | 384 |
| transformer-input-ids | One | The name or identifier for the transformer input IDs | string | input_ids |
| transformer-attention-mask | One | The name or identifier for the transformer attention mask | string | attention_mask |
| transformer-token-type-ids | One | The name or identifier for the transformer token type IDs. If the model does not use `token_type_ids` use `<transformer-token-type-ids/>` | string | token_type_ids |
| transformer-output | One | The name or identifier for the transformer output | string | output_0 |
| transformer-start-sequence-token | One | The start of sequence token | numeric | 101 |
| transformer-end-sequence-token | One | The start of sequence token | numeric | 102 |
| pooling-strategy | One | How the output vectors of the ONNX model is pooled to obtain a single vector representation. Valid values are `mean` and `cls` | string | mean |

## colbert embedder

The colbert embedder is configured in [services.xml](services.html),
within the `container` tag:

```
{% highlight xml %}




    32
    256


{% endhighlight %}
```

The Vespa colbert implementation works with default configurations for transformer models that use WordPiece tokenization.

### colbert embedder reference config

In addition to [embedder ONNX parameters](#embedder-onnx-reference-config):

| Name | Occurrence | Description | Type | Default |
| --- | --- | --- | --- | --- |
| transformer-model | One | Use to point to the transformer ColBERT ONNX model file | [model-type](#model-config-reference) | N/A |
| tokenizer-model | One | Use to point to the `tokenizer.json` Huggingface tokenizer configuration file | [model-type](#model-config-reference) | N/A |
| max-tokens | One | Max length of token sequence the transformer-model can handle | numeric | 512 |
| max-query-tokens | One | The maximum number of ColBERT query token embeddings. Queries are padded to this length. Must be lower than max-tokens | numeric | 32 |
| max-document-tokens | One | The maximum number of ColBERT document token embeddings. Documents are not padded. Must be lower than max-tokens | numeric | 512 |
| transformer-input-ids | One | The name or identifier for the transformer input IDs | string | input_ids |
| transformer-attention-mask | One | The name or identifier for the transformer attention mask | string | attention_mask |
| transformer-mask-token | One | The mask token id used for ColBERT query padding | numeric | 103 |
| transformer-start-sequence-token | One | The start of sequence token id | numeric | 101 |
| transformer-end-sequence-token | One | The end of sequence token id | numeric | 102 |
| transformer-pad-token | One | The pad sequence token id | numeric | 0 |
| query-token-id | One | The colbert query token marker id | numeric | 1 |
| document-token-id | One | The colbert document token marker id | numeric | 2 |
| transformer-output | One | The name or identifier for the transformer output | string | contextual |

The Vespa colbert-embedder uses `[unused0]`token id 1 for `query-token-id`, and `[unused1]`,
token id 2 for  `document-token-id`document marker. Document punctuation chars are filtered (not configurable).
The following characters are removed `` !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~ ``.

### splade embedder reference config

In addition to [embedder ONNX parameters](#embedder-onnx-reference-config):

| Name | Occurrence | Description | Type | Default |
| --- | --- | --- | --- | --- |
| transformer-model | One | Use to point to the transformer ONNX model file | [model-type](#model-config-reference) | N/A |
| tokenizer-model | One | Use to point to the `tokenizer.json` Huggingface tokenizer configuration file | [model-type](#model-config-reference) | N/A |
| term-score-threshold | One | An optional threshold to increase sparseness, tokens/terms with a score lower than this is not retained. | numeric | N/A |
| max-tokens | One | The maximum number of tokens accepted by the transformer model | numeric | 512 |
| transformer-input-ids | One | The name or identifier for the transformer input IDs | string | input_ids |
| transformer-attention-mask | One | The name or identifier for the transformer attention mask | string | attention_mask |
| transformer-token-type-ids | One | The name or identifier for the transformer token type IDs. If the model does not use `token_type_ids` use `<transformer-token-type-ids/>` | string | token_type_ids |
| transformer-output | One | The name or identifier for the transformer output | string | logits |

## Huggingface tokenizer embedder

The Huggingface tokenizer embedder is configured in [services.xml](services.html),
within the `container` tag:

```
{% highlight xml %}





{% endhighlight %}
```

### Huggingface tokenizer reference config

| Name | Occurrence | Description | Type | Default |
| --- | --- | --- | --- | --- |
| model | One To Many | Use to point to the `tokenizer.json` Huggingface tokenizer configuration file. Also supports `language`, which is only relevant if one wants to tokenize differently based on the document language. Use "unknown" for a model to be used for any language (i.e. by default). | [model-type](#model-config-reference) | N/A |

## Embedder ONNX reference config

Vespa uses [ONNX Runtime](https://onnxruntime.ai/) to accelerate inference of embedding models.
These parameters are valid for both [Bert embedder](#bert-embedder) and
[Huggingface embedder](#huggingface-embedder).

| Name | Occurrence | Description | Type | Default |
| --- | --- | --- | --- | --- |
| onnx-execution-mode | One | Low level ONNX execution model. Valid values are `parallel` or `sequential`. Only relevant for inference on CPU. See [ONNX runtime documentation](https://onnxruntime.ai/docs/performance/tune-performance/threading.html) on threading. | string | sequential |
| onnx-interop-threads | One | Low level ONNX setting.Only relevant for inference on CPU. | numeric | 1 |
| onnx-intraop-threads | One | Low level ONNX setting. Only relevant for inference on CPU. | numeric | 4 |
| onnx-gpu-device | One | The GPU device to run the model on. See [configuring GPU for Vespa container image](/en/operations-selfhosted/vespa-gpu-container.html). Use `-1` to not use GPU for the model, even if the instance has available GPUs. | numeric | 0 |

## SentencePiece embedder

A native Java implementation of [SentencePiece](https://github.com/google/sentencepiece).
SentencePiece breaks text into chunks independent of spaces,
which is robust to misspellings and works with CJK languages.
Prefer the [Huggingface tokenizer embedder](#huggingface-tokenizer-embedder) over this
for better compatibility with Huggingface models.

This is suitable to use in conjunction with [custom components](../jdisc/container-components.html),
or the resulting tensor can be used in [ranking](../ranking.html).

To use the
[SentencePiece embedder](https://github.com/vespa-engine/vespa/blob/master/linguistics-components/src/main/java/com/yahoo/language/sentencepiece/SentencePieceEmbedder.java), add it to [services.xml](services.html):

```
{% highlight xml %}


      ;


                unknown
                model/en.wiki.bpe.vs10000.model





  {% endhighlight %}
```

See the options available for configuring SentencePiece in
[the full configuration definition](https://github.com/vespa-engine/vespa/blob/master/linguistics-components/src/main/resources/configdefinitions/language.sentencepiece.sentence-piece.def).

## WordPiece embedder

A native Java implementation of
[WordPiece](https://github.com/google-research/bert#tokenization),
which is commonly used with BERT models.
Prefer the [Huggingface tokenizer embedder](#huggingface-tokenizer-embedder)
over this for better compatibility with Huggingface models.

This is suitable to use in conjunction with [custom components](../jdisc/container-components.html),
or the resulting tensor can be used in [ranking](../ranking.html).

To use the
[WordPiece embedder](https://github.com/vespa-engine/vespa/blob/master/linguistics-components/src/main/java/com/yahoo/language/wordpiece/WordPieceEmbedder.java),
add it to [services.xml](services.html) within the `container` tag:

```
{% highlight xml %}


             class="com.yahoo.language.wordpiece.WordPieceEmbedder"
             bundle="linguistics-components">



            unknown
            models/bert-base-uncased-vocab.txt





  {% endhighlight %}
```

See the options available for configuring WordPiece in
[the full configuration definition](https://github.com/vespa-engine/vespa/blob/master/linguistics-components/src/main/resources/configdefinitions/language.wordpiece.word-piece.def).

WordPiece is suitable to use in conjunction with custom components,
or the resulting tensor can be used in [ranking](../ranking.html).

## Using an embedder from Java

When writing custom Java components (such as [Searchers](../searcher-development.html)
or [Document processors](../document-processing.html#document-processors)),
use embedders you have configured by
[having them injected in the constructor](../jdisc/injecting-components.html),
just as any other component:

```
{% highlight java %}
class MyComponent {
  @Inject
  public MyComponent(ComponentRegistry embedders) {
    // embedders contains all the embedders configured in your services.xml
  }
}
{% endhighlight %}
```

See a concrete example of using an embedder in a custom searcher in
[LLMSearcher](https://github.com/vespa-cloud/vespa-documentation-search/blob/main/src/main/java/ai/vespa/cloud/docsearch/LLMSearcher.java).

## Custom Embedders

Vespa provides a Java interface for defining components which can provide embeddings of text:
[com.yahoo.language.process.Embedder](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/process/Embedder.java).

To define a custom embedder in an application and make it usable by Vespa
(see [embedding a query text](../embedding.html#embedding-a-query-text)),
implement this interface and add it as a [component](../developer-guide.html#developing-components) to
[services.xml](services-container.html):

```
{% highlight xml %}





            foo



{% endhighlight %}
```
