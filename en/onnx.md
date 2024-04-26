---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Ranking With ONNX Models"
redirect_from:
- /documentation/onnx.html
---

Vespa has support for advanced ranking models through its tensor API. If you
have your model in the [ONNX format](https://onnx.ai/), Vespa can import the
models and use them directly.

See [embedding](embedding.html) and the
[simple-semantic-search](https://github.com/vespa-engine/sample-apps/tree/master/simple-semantic-search)
sample application for a minimal, practical example.



## Importing ONNX model files

Add the file containing the ONNX models somewhere under the application
package. For instance, if your model file is `my_model.onnx` you could
add it to the application package under a `files` directory something like
this:

<pre>
├── files
│   └── my_model.onnx
├── schemas
│   └── main.sd
└── services.xml
</pre>

An application package can have multiple models.

To download models during deployment,
see [deploying remote models](application-packages.html#deploying-remote-models).

See the [model-exporting](https://github.com/vespa-engine/sample-apps/blob/master/msmarco-ranking/src/main/python/model-exporting.ipynb)
notebook for examples of how to export models to ONNX.
Use this when experimenting with different models.
Also relevant is the [model-deployment](https://github.com/vespa-engine/sample-apps/tree/master/examples/model-deployment)
example, which is a minimal create-train-convert-deploy script.
This also includes sample use of the _onnx/onnxruntime_ modules.



## Ranking with ONNX models

To make the above model available for ranking, you define the model in the
schema, and then you can refer to the model using the `onnx` (or `onnxModel`)
ranking feature:

<pre>
schema my_schema {

    document my_document {
        field my_field type tensor(d0[1],d1[10]) {
            indexing: attribute | summary
        }
    }

    rank-profile my_rank_profile {

        inputs {
            query(myTensor) tensor(d0[1],d1[784])
        }

        onnx-model my_onnx_model {
            file: files/my_model.onnx
            input "model_input_0": attribute(my_field)
            input "model_input_1": my_function
            output "model_output_0": output_name
        }

        function my_function() {
            expression: tensor&lt;float&gt;(d0[1],d1[10])(d1)
        }

        first-phase {
            expression: sum( onnx(my_onnx_model).output_name )
        }

    }

}
</pre>

This defines the model called `my_onnx_model`. It is evaluated using the
`onnx` [ranking feature](reference/rank-features.html).
This rank feature specifies which model to evaluate in the ranking expression
and, optionally, which output to use from the model.

The `onnx-model` section defines three things:

1. The model's location under the applications package
2. The inputs to use for evaluation and where they should come from
3. The outputs to use for evaluation

In the example above, the model should be found in `files/my_model.onnx`. This
model has two inputs. For inputs, the first name specifies the input as
named in the ONNX model file. The source is where the input should
come from.  This can be either:

- A document field:  `attribute(field_name)`
- A query parameter: `query(query_param)`
- A constant: `constant(name)`
- A user-defined function: `function_name`

For outputs, the output name is the name used in Vespa to specify the output.
If this is omitted, the first output in the ONNX file will be used.

The output of a model is usually a tensor, however the rank score should result
in a single scalar value. In the example above we use `sum` to sum all the elements
of the tensor to a single value. You can also slice out parts of
the result using Vespa's [tensor API](reference/ranking-expressions.html#tensor-functions).
For instance, if the output of the example above is a tensor with the two dimensions `d0` and `d1`,
and you want to extract the first value, this can be expressed by:

<pre>
onnx(my_onnx_model).output_name{d0:0,d1:0}
</pre>

Note that inputs to the ONNX model must be tensors; scalars are not supported.
The input tensors must have dimension names starting with `"d0"` for the first
dimension, and increasing for each dimension (i.e. `"d1"`, `"d2"`, etc.). The
result of the evaluation will likewise be a tensor with names `"d0"`, `"d1"`,
etc.

The types of document and input tensors are specified in the schema as shown above.
You can pass tensors in HTTP requests by using the HTTP parameter
"input.query(myTensor)" (assuming the ranking expression contains "query(myTensor)").

A tensor example can be found in the
[sample application](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation).


#### Batch dimensions

When training your model you will typically have an input that contains a
dimension for batches, for instance an input with sizes `[-1, 784]`.  Here, -1
typically denotes the batch dimension. 

During inference in ranking, Vespa typically inferences over a single
exemplar.


## Limitations on model size and complexity

Note that in the above rank profile example, the `onnx` model evaluation
was evaluated in the first phase. In general, evaluating these type of models are
more suitable in the <code>second-phase</code> or <code>global-phase</code> phases. 
See <a href="phased-ranking.html">phased ranking</a>.

The assumption when evaluating ONNX models in Vespa is that the models will be
used in ranking, meaning that the model will be evaluated once for each
document. Please be aware that this imposes some natural restrictions on the
size and complexity of the models, particularly if the application has a large
number of documents. However, effective use of [phased ranking](phased-ranking.html)
can make running deep models feasible.

## Examples

The [Transformers](https://github.com/vespa-engine/sample-apps/tree/master/transformers)
sample application uses a cross-encoder model to
[re-rank documents](https://github.com/vespa-engine/sample-apps/blob/master/transformers/application/schemas/msmarco.sd).

The [simple semantic search](https://github.com/vespa-engine/sample-apps/tree/master/simple-semantic-search) sample application
uses onnx for embedding inference. 


## Using vespa-analyze-onnx-model
[vespa-analyze-onnx-model](/en/operations/tools.html#vespa-analyze-onnx-model)
is useful to find model inputs and outputs -
example run on a config server where an application package with a model is deployed to:

<pre>
$ docker exec vespa vespa-analyze-onnx-model \
  /opt/vespa/var/db/vespa/config_server/serverdb/tenants/default/sessions/1/files/Network.onnx

unspecified option[0](optimize model), fallback: true
vm_size: 230228 kB, vm_rss: 44996 kB (before loading model)
vm_size: 233792 kB, vm_rss: 54848 kB (after loading model)
model meta-data:
input[0]: 'input' float[input][4]
output[0]: 'output' float[output][3]
unspecified option[1](symbolic size 'input'), fallback: 1
test setup:
input[0]: tensor&lt;float&gt;(d0[1],d1[4]) -> float[1][4]
output[0]: float[1][3] -&gt; tensor&lt;float&gt;(d0[1],d1[3])
unspecified option[2](max concurrent evaluations), fallback: 1
vm_size: 233792 kB, vm_rss: 54848 kB (no evaluations yet)
vm_size: 233792 kB, vm_rss: 54848 kB (concurrent evaluations: 1)
estimated model evaluation time: 0.00227701 ms
</pre>

The corresponding input/output tensors should be defined as:
<pre>
document doc {
    ...
    field flowercategory type tensor&lt;float&gt;(d0[1],d1[3]) {
        indexing: attribute | summary
    }
}

rank-profile myRank {
    inputs {
        query(myTensor) tensor&lt;float&gt;(d0[1],d1[4])
    }
    onnx-model my_onnx_model {
        file: files/Network.onnx
        input  "input" : query(myTensor)
        output "output": outputTensor
    }
    first-phase {
        expression: sum( onnx(my_onnx_model).outputTensor * attribute(flowercategory) )
    }
}
</pre>


<h2 id="onnx-export">Exporting HF models to ONNX format</h2>

<p>Transformer-based models have named inputs and outputs that must be compatible
with the input and output names used by the <a href="embedding.html">embedder</a>.</p>

<p>The <a href="https://github.com/vespa-engine/sample-apps/tree/master/simple-semantic-search#model-exporting">simple-semantic-search</a>
sample app includes two scripts to export models and vocabulary files using the default expected input and output names
for embedders using ONNX models. The input and output names to the embeder are tunable via the  <code>transformer-</code>
parameters in the <a href="reference/embedding-reference.html">config of the embedder in question</a>.</p>

<h3 id="using-optimum-to-export-models-to-onnx-format">Using Optimum to export models to onnx format</h3>
<p>We can highly recommend using the <a href="https://huggingface.co/docs/optimum/index">Optimum</a> library for exporting
models hosted on Huggingface model hub.</p>

<p>
For example, to export <a href="https://huggingface.co/BAAI/bge-small-en">BAAI/bge-small-en</a> from the model hub to onnx format:

<pre>
$ python3 -m pip install optimum onnx  onnxruntime
$ optimum-cli export onnx --task feature-extraction -m BAAI/bge-small-en --optimize O3 model-output-dir
</pre>

The exported files in <code>model-output-dir</code>: <code>model.onnx</code> and <code>tokenizer.json</code> imported directly
into the Vespa <a href="embedding.html#huggingface-embedder">huggingface-embedder</a>.</p> See also [debugging onnx](#onnx-debug).

<p>In many cases, there are also onnx checkpoints available, for example <a href="https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1/tree/main">mixedbread-ai/mxbai-embed-large-v1</a>, this models can then be downloaded and used in Vespa. 

<pre>{% highlight xml %}
<container id="default" version="1.0">
    <component id="mixedbread" type="hugging-face-embedder">
        <transformer-model url="https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1/resolve/main/onnx/model_quantized.onnx"/>
        <tokenizer-model url="https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1/raw/main/tokenizer.json"/>
        <pooling-strategy>cls</pooling-strategy>
    </component>
    ...
</container>{% endhighlight %}</pre>
<p> Vespa defaults to <code>mean</code> <code>pooling-strategy</code>. Consult the model card for the pooling method used. Note the url patterns on HUB, the url
must point to the actual file, not the model card. Also, Vespa only supports models that are contained in a single onnx file, if the original model is larger than
2GB, the model is split over multiple files and this is not currently supported.</p>

<p>See <a href="cross-encoders.html#exporting-cross-encoder-models">cross-encoders</a> documentation for examples on how to 
export cross-encoder re-rankers using the Optimum library.</p>

<h3 id="onnx-debug">Debugging ONNX models</h3>

<p>When loading <a href="https://onnx.ai/">ONNX</a> models for Vespa native <a href="embedding.html">embedders</a>, 
the model must have correct inputs and output parameters. Vespa offers tools to inspect ONNX model files.
Here, <em>minilm-l6-v2.onnx</em> is in the current working directory:
</p>
<pre>
$ docker run -v `pwd`:/w \
  --entrypoint /opt/vespa/bin/vespa-analyze-onnx-model \
  vespaengine/vespa \
  /w/minilm-l6-v2.onnx

...
model meta-data:
  input[0]: 'input_ids' long[batch][sequence]
  input[1]: 'attention_mask' long[batch][sequence]
  input[2]: 'token_type_ids' long[batch][sequence]
  output[0]: 'output_0' float[batch][sequence][384]
  output[1]: 'output_1' float[batch][384]
...
</pre>

<p>The above model input and output names conform with the
default <a href="reference/embedding-reference.html#bert-embedder-reference-config">bert-embedder parameters</a>.</p>
<p>Similarly, a model for the <a href="reference/embedding-reference.html#huggingface-embedder-reference-config">hugging-face-embedder parameters</a> defaults:</p>
<pre>
model meta-data:
  input[0]: 'input_ids' long[batch][sequence]
  input[1]: 'attention_mask' long[batch][sequence]
  input[2]: 'token_type_ids' long[batch][sequence]
  output[0]: 'last_hidden_state' float[batch][sequence][384]
</pre>
<p>The shape of the output should be:
<pre>
float[batch][sequence][vector-embedding-dimensionality]
</pre>
Vespa embedders implement the pooling strategy over the output vectors (one per sequence length).
</p>

<p>If loading models without the expected input and output parameter names, the container service will not start
(check <em>vespa.log</em> in the container running Vespa):</p>

<pre>
 WARNING container        Container.com.yahoo.container.di.Container
  Caused by: java.lang.IllegalArgumentException: Model does not contain required input: 'input_ids'. Model contains: input
</pre>

<p>When this happens, a deploy looks like:</p>
<pre>
$ vespa deploy --wait 300
Uploading application package ... done

Success: Deployed .

Waiting up to 5m0s for query service to become available ...
Error: service 'query' is unavailable: services have not converged
</pre>

<p>Embedders supports changing the input and output names, consult <a href="reference/embedding-reference.html">embedding reference</a>
documentation.</p>
