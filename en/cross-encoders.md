---
title: Ranking With Transformer Cross-Encoder Models
---

# Ranking With Transformer Cross-Encoder Models

[Cross-Encoder Transformer](https://blog.vespa.ai/pretrained-transformer-language-models-for-search-part-4/) based text ranking models are generally more effective than [text embedding](embedding.html) models as they take both the query and the document as input with full cross-attention between all the query and document tokens.

The downside of cross-encoder models is the computational complexity. This document is a guide on how to export cross-encoder Transformer based models from [huggingface](https://huggingface.co/), and how to configure them for use in Vespa.

### Exporting cross-encoder models

For exporting models from HF to [ONNX](onnx.html), we recommend the [Optimum](https://huggingface.co/docs/optimum/main/en/index) library. Example usage for two relevant ranking models.

Export [intfloat/simlm-msmarco-reranker](https://huggingface.co/intfloat/simlm-msmarco-reranker), which is a BERT-based transformer model for English texts:

```
$ optimum-cli export onnx --task text-classification -m intfloat/simlm-msmarco-reranker ranker
```

Export [BAAI/bge-reranker-base](https://huggingface.co/BAAI/bge-reranker-base), which is a ROBERTA-based transformer model for English and Chinese texts (multilingual):

```
$ optimum-cli export onnx --task text-classification -m BAAI/bge-reranker-base ranker
```

These two example ranking models use different language model [tokenization](reference/embedding-reference.html#huggingface-tokenizer-embedder) and also different transformer inputs.

After the above Optimum export command you have two important files that is needed for importing the model to Vespa:

```
├── ranker
│   └── model.onnx
    └── tokenizer.json
```

The Optimum tool also supports various Transformer optimizations, including quantization to optimize the model for faster inference.

### Importing ONNX and tokenizer model files to Vespa

Add the generated `model.onnx` and `tokenizer.json` files from the `ranker` directory created by Optimum to the Vespa [application package](application-packages.html):

```
├── models
│   └── model.onnx
    └── tokenizer.json
├── schemas
│   └── doc.sd
└── services.xml
```

### Configure tokenizer embedder

To speed up inference, Vespa avoids re-tokenizing the document tokens, so we need to configure the [huggingface-tokenizer-embedder](reference/embedding-reference.html#huggingface-tokenizer-embedder) in the `services.xml` file:

```
<container id="default" version="1.0">
    ..
    <component id="tokenizer" type="hugging-face-tokenizer">
      <model path="models/tokenizer.json">
    </component>
    ..
</container>
```

This allows us to use the tokenizer while indexing documents in Vespa and also at query time to map (embed) query text to language model tokens.

### Using tokenizer in schema

Assuming we have two fields that we want to index and use for re-ranking (title, body), we can use the `embed` indexing expression to invoke the tokenizer configured above:

```
schema my_document {
    document my_document {
        field title type string {..}
        field body type string {..}
    }
    field tokens type tensor<float>(d0[512]) {
        indexing: (input title || "") . " "  .  (input body || "") | embed tokenizer | attribute
    }
}
```

The above will concat the title and body input document fields, and input to the `hugging-face-tokenizer` tokenizer which saves the output tokens as float (101.0).\
To use the generated `tokens` tensor in ranking, the tensor field must be defined with [attribute](attributes.html).

### Using the cross-encoder model in ranking

Cross-encoder models are not practical for _retrieval_ over large document volumes due to their complexity, so we configure them using [phased ranking](phased-ranking.html).

#### Bert-based model

Bert-based models have three inputs:

* input\_ids
* token\_type\_ids
* attention\_mask

The [onnx-model](reference/schema-reference.html#onnx-model) configuration specifies the input names of the model and how to calculate them. It also specifies the file `models/model.onnx`. Notice also the [GPU](operations-selfhosted/vespa-gpu-container.html). GPU inference is not required, and Vespa will fallback to CPU if no GPU device is found. See section on [performance](cross-encoders.md#performance).

```
rank-profile bert-ranker inherits default {
    inputs {
        query(q_tokens) tensor<float>(d0[32])
    }
    onnx-model cross_encoder {
        file: models/model.onnx
        input input_ids: my_input_ids
        input attention_mask: my_attention_mask
        input token_type_ids: my_token_type_ids
        gpu-device: 0
    }
    function my_input_ids() {
        expression: tokenInputIds(256, query(q_tokens), attribute(tokens))
    }

    function my_token_type_ids() {
        expression: tokenTypeIds(256, query(q_tokens), attribute(tokens))
    }

    function my_attention_mask() {
        expression: tokenAttentionMask(256, query(q_tokens), attribute(tokens))
    }

    first-phase {
        expression: #depends on the retriever used
    }

    # The output of this model is a tensor of size ["batch", 1]
    global-phase {
        rerank-count: 25
        expression: onnx(cross_encoder){d0:0,d1:0}
    }
}
```

The example above limits the sequence length to `256` using the built-in convenience functions for generating token sequence input to Transformer models. Note that `tokenInputIds` uses 101 as start of sequence and 102 as padding. This is only compatible with BERT-based tokenizers. See section on [performance](cross-encoders.md#performance) about sequence length and impact on inference performance.

#### Roberta-based model

ROBERTA-based models only have two inputs (input\_ids and attention\_mask). In addition, the default tokenizer start of sequence token is 1 and end of sequence is 2. In this case we use the `customTokenInputIds` function in `my_input_ids` function. See \[customTokenInputIds]\(reference/rank-features.html#customTokenInputIds(start\_sequence\_id, sep\_sequence\_id, length, input\_1, input\_2, ...)).

```
rank-profile roberta-ranker inherits default {
    inputs {
        query(q_tokens) tensor<float>(d0[32])
    }
    onnx-model cross_encoder {
        file: models/model.onnx
        input input_ids: my_input_ids
        input attention_mask: my_attention_mask
        gpu-device: 0
    }
    function my_input_ids() {
        expression: customTokenInputIds(1, 2, 256, query(q_tokens), attribute(tokens))
    }

    function my_attention_mask() {
        expression: tokenAttentionMask(256, query(q_tokens), attribute(tokens))
    }

    first-phase {
        expression: #depends on the retriever used
    }

    # The output of this model is a tensor of size ["batch", 1]
    global-phase {
        rerank-count: 25
        expression: onnx(cross_encoder){d0:0,d1:0}
    }
}
```

### Using the cross-encoder model at query time

At query time, we need to tokenize the user query using the [embed](embedding.html#embedding-a-query-text) support.

The `embed` of the query text, sets the `query(q_tokens)` tensor that we defined in the ranking profile.

```
```

The retriever (query + first-phase ranking) can be anything, including [nearest neighbor search](nearest-neighbor-search.html) a.k.a. dense retrieval using bi-encoders.

### Performance

There are three major scaling dimensions:

* The number of hits that are re-ranked [rerank-count](reference/schema-reference.html#globalphase-rerank-count) Complexity is linear with the number of hits that are re-ranked.
* The size of the transformer model used.
* The sequence input length. Transformer models scales quadratic with the input sequence length.

For models larger than 30-40M parameters, we recommend using GPU to accelerate inference. Quantization of model weights can drastically improve serving efficiency on CPU. See [Optimum Quantization](https://huggingface.co/docs/optimum/onnxruntime/usage_guides/quantization)

### Examples

The [MS Marco](https://github.com/vespa-engine/sample-apps/tree/master/msmarco-ranking) sample application demonstrates using cross-encoders.

### Using cross-encoders with multi-vector indexing

When using [multi-vector indexing](https://blog.vespa.ai/semantic-search-with-multi-vector-indexing/) we can do the following to feed the best (closest) paragraph using the [closest()](reference/rank-features.html#closest\(name\)) feature into re-ranking with the cross-encoder model.

```
schema my_document {
    document my_document {  
        field paragraphs type array<string>string {..}
    }
    field tokens type tensor<float>(p{}, d0[512]) {
        indexing: input paragraphs | embed tokenizer | attribute
    }
    field embedding type tensor<float>(p{}, x[768]) {
        indexing: input paragraphs | embed embedder | attribute
    }
}
```

Notice that both tokens use the same mapped embedding dimension name `p`.

```
rank-profile max-paragraph-into-cross-encoder inherits default {
    inputs {
        query(tokens) tensor<float>(d0[32])
        query(q) tensor<float>(x[768])
    }
    first-phase {
        expression: closeness(field, embedding)
    }
    function best_input() {
        expression: reduce(closest(embedding)*attribute(tokens), max, p)
    }
    function my_input_ids() {
        expression: tokenInputIds(256, query(tokens), best_input)
    }
    function my_token_type_ids() {
        expression: tokenTypeIds(256, query(tokens), best_input)
    }

    function my_attention_mask() {
        expression: tokenAttentionMask(256, query(tokens), best_input)
    }
    match-features: best_input my_input_ids my_token_type_ids my_attention_mask
    global-phase {
        rerank-count: 25
        expression: onnx(cross_encoder){d0:0,d1:0} #Slice 
    }
}
```

The `best_input` uses a tensor join between the `closest(embedding)` tensor and the `tokens` tensor, which then returns the tokens of the best-matching (closest) paragraph.

This tensor is used in the other Transformer-related functions (`tokenTypeIds tokenAttentionMask tokenInputIds`) as the document tokens.
