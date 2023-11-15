---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Ranking With Transformer Cross-Encoder Models"
redirect_from:
- /documentation/cross-encoders.html
---

[Cross-Encoder Transformer](https://blog.vespa.ai/pretrained-transformer-language-models-for-search-part-4/) 
based text ranking models are generally more effective than [text embedding](embedding.html) models
as they take both the query and the document as input with full cross-attention between all the query and document tokens. 

The downside of cross-encoder models is the computional complexity. This document is a guide
on how to export cross-encoder Transformer based models from [huggingface](https://huggingface.co/), 
and how to configure them for use in Vespa. 

## Exporting cross-encoder models 
For exporting models from HF to [ONNX](onnx.html), we recommend the [Optimum](https://huggingface.co/docs/optimum/main/en/index)
library. Example usage for two relevant ranking models.

Export [intfloat/simlm-msmarco-reranker](https://huggingface.co/intfloat/simlm-msmarco-reranker), which is
a BERT-based transformer model for English texts:

<pre>
$ optimum-cli export onnx --task text-classification -m intfloat/simlm-msmarco-reranker ranker
</pre>

Export [BAAI/bge-reranker-base](https://huggingface.co/BAAI/bge-reranker-base), which is
a ROBERTA-based transformer model for English and Chinese texts (multilingual):

<pre>
$ optimum-cli export onnx --task text-classification -m BAAI/bge-reranker-base ranker
</pre>

These two example ranking models use different 
language model [tokenization](reference/embedding-reference.html#huggingface-tokenizer-embedder) and also
different transformer inputs.

After the above Optimum export command you have two important
files that is needed for importing the model to Vespa: 

<pre>
├── ranker
│   └── model.onnx
    └── tokenizer.json
</pre>

The Optimum tool also supports various Transformer optimizations, including quantization to 
optimize the model for faster inference. 

## Importing ONNX and tokenizer model files to Vespa

Add the generated `model.onnx` and `tokenizer.json` files from the `ranker` directory 
created by Optimum to the Vespa [application package](application-packages.html):

<pre>
├── models
│   └── model.onnx
    └── tokenizer.json
├── schemas
│   └── doc.sd
└── services.xml
</pre>

## Configure tokenizer embedder
To speed up inference, Vespa avoids re-tokenizing the document tokens, so we need to configure the 
[huggingface-tokenizer-embedder](reference/embedding-reference.html#huggingface-tokenizer-embedder) 
in the `services.xml` file:

<pre>
&lt;container id="default" version="1.0"&gt;
    ..
    &lt;component id="tokenizer" type="hugging-face-tokenizer"&gt;
      &lt;model path="models/tokenizer.json"&gt;
    &lt;/component&gt;
    ..
&lt;/container&gt;
</pre>

This allows us to use the tokenizer while indexing documents in Vespa and also at query time to
map (embed) query text to language model tokens.

## Using tokenizer in schema
Assuming we have two fields that we want to index and use for re-ranking (title, body), we
can use the `embed` indexing expression to invoke the tokenizer configured above:

<pre>
schema my_document {
    document my_document {
        field title type string {..}
        field body type string {..}
    }
    field tokens type tensor&lt;float&gt;(d0[512]) {
        indexing: (input title || "") . " "  .  (input body || "") | embed tokenizer | attribute
    }
}</pre>

The above will concat the title and body input document fields, and input to the 
`hugging-face-tokenizer` tokenizer which saves the output tokens as float (101.0).  
To use the generated `tokens` tensor in ranking, the tensor field must be defined with [attribute](attributes.html).

## Using the cross-encoder model in ranking
Cross-encoder models are not practical for *retrieval* over large document volumes due to their complexity, so we configure them
using [phased ranking](phased-ranking.html). 

### Bert-based model
Bert-based models have three inputs:

- input_ids
- token_type_ids
- attention_mask


The [onnx-model](reference/schema-reference.html#onnx-model) configuration specifies the input names
of the model and how to calculate them. It also specifies the file `models/model.onnx`.
Notice also the [GPU](/en/operations-selfhosted/vespa-gpu-container.html).
GPU inference is not required, and Vespa will fallback to CPU if no GPU device is found.
See section on [performance](#performance).

<pre>
rank-profile bert-ranker inherits default {
    inputs {
        query(q_tokens) tensor&lt;float&gt;(d0[32])
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
}</pre>

The example above limits the sequence lenght to `256` using the built-in 
[convenience functions](reference/rank-features.html#tokenInputIds(length,%20input_1,%20input_2,%20...)) 
for generating token sequence input to Transformer models. Note that `tokenInputIds` uses 101 as start of sequence
and 102 as padding. This is only compatible with BERT-based tokenizers. See section on [performance](#performance)
about sequence length and impact on inference performance.

### Roberta-based model
ROBERTA-based models only have two inputs (input_ids and attention_mask). In addition, the default tokenizer
start of sequence token is 1 and end of sequence is 2. In this case we use the
`customTokenInputIds` function in `my_input_ids` function. See
[customTokenInputIds](reference/rank-features.html#customTokenInputIds(start_sequence_id, sep_sequence_id, length, input_1, input_2, ...)).

<pre>
rank-profile roberta-ranker inherits default {
    inputs {
        query(q_tokens) tensor&lt;float&gt;(d0[32])
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
}</pre>

## Using the cross-encoder model at query time 
At query time, we need to tokenize the user query using the [embed](embedding.html#embedding-a-query-text) support. 

The `embed` of the query text, sets the `query(q_tokens)`
tensor that we defined in the ranking profile.

<pre>{% highlight json %}
 {
    "yql": "select title,body from doc where userQuery()",
    "query": "semantic search",
    "input.query(q_tokens)": "embed(tokenizer, \"semantic search\")",
    "ranking": "bert-ranker",
}{% endhighlight %}</pre>

The retriever (query + first-phase ranking) can be anything, including 
[nearest neighbor search](nearest-neighbor-search.html) a.k.a. dense retrival using bi-encoders.

## Performance
There are three major scaling dimensions:

- The number of hits that are re-ranked [rerank-count](reference/schema-reference.html#globalphase-rerank-count) Complexity is linear with the number of hits that are re-ranked.
- The size of the transformer model used.
- The sequence input length. Transformer models scales quadratic with the input sequence length.

For models larger than 30-40M parameters, we recommend using GPU to accelerate inference. 
Quantization of model weights can drastically improve serving efficiency on CPU. See
[Optimum Quantization](https://huggingface.co/docs/optimum/onnxruntime/usage_guides/quantization)

## Examples

The [Transformers](https://github.com/vespa-engine/sample-apps/tree/master/transformers)
sample application demonstrates using cross-encoders. 

## Using cross-encoders with multi-vector indexing
When using [multi-vector indexing](https://blog.vespa.ai/semantic-search-with-multi-vector-indexing/) 
we can do the following to feed the best (closest) paragraph using the 
[closest()](reference/rank-features.html#closest(name)) feature into re-ranking with the cross-encoder model. 

<pre>
schema my_document {
    document my_document {  
        field paragraphs type array&lt;string&gt;string {..}
    }
    field tokens type tensor&lt;float&gt;(p{}, d0[512]) {
        indexing: input paragraphs | embed tokenizer | attribute
    }
    field embedding type tensor&lt;float&gt;(p{}, x[768]) {
        indexing: input paragraphs | embed embedder | attribute
    }
}</pre>

Notice that both tokens uses the same mapped embedding dimension name `p`. 

<pre>
rank-profile max-paragraph-into-cross-encoder inherits default {
    inputs {
        query(tokens) tensor&lt;float&gt;(d0[32])
        query(q) tensor&lt;float&gt;(x[768])
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
    global-phase {
        rerank-count: 25
        expression: onnx(cross_encoder){d0:0,d1:0}
    }
}
</pre>

The `best_input` uses a tensor join between the `closest(embedding)` tensor and the `tokens` tensor
which then returns the tokens of the best matching paragraph, this is then fed into the other transformer
related functions as the document tokens.  


