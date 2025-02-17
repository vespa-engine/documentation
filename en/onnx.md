---
# Copyright Vespa.ai. All rights reserved.
title: "Ranking With ONNX Models"
---

Vespa supports advanced ranking models through its tensor API.
If your model is in the [ONNX format](https://onnx.ai/), Vespa can import and use the model directly.
You can use ONNX models with Vespa [embedder](/en/embedding.html) functionality or in [ranking](/en/ranking.html).



## Importing ONNX model files

Add the file containing the ONNX models somewhere under the application package.
For instance, if your model file is `my_model.onnx`,
you could add it to the application package under a `files` directory, something like:

```
├── files
│   └── my_model.onnx
├── schemas
│   └── main.sd
└── services.xml
```

An application package can have multiple onnx models. To download models during deployment,
see [deploying remote models](/en/application-packages.html#deploying-remote-models).



## Ranking with ONNX models

To make the above model available for ranking, you define the model in the schema,
and then you can refer to the model using the `onnx` (or `onnxModel`) ranking feature:

```
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
            expression: tensor<float>(d0[1],d1[10])(d1)
        }

        first-phase {
            expression: sum( onnx(my_onnx_model).output_name )
        }

    }

}
```

This defines the model called `my_onnx_model`. It is evaluated using the
`onnx` [ranking feature](/en/reference/rank-features.html).
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

The output of a model is a tensor, however the rank score should result
in a single scalar value. In the example above we use `sum` to sum all the elements
of the tensor to a single value. You can also slice out parts of
the result using Vespa's [tensor API](/en/reference/ranking-expressions.html#tensor-functions).
For instance, if the output of the example above is a tensor with the two dimensions `d0` and `d1`,
and you want to extract the first value, this can be expressed by:

```
onnx(my_onnx_model).output_name{d0:0,d1:0}
```

Note that inputs to the ONNX model must be tensors; scalars are not supported.
The input tensors must have dimension names starting with `"d0"` for the first
dimension, and increasing for each dimension (i.e. `"d1"`, `"d2"`, etc.). The
result of the evaluation will likewise be a tensor with names `"d0"`, `"d1"`, etc.

The types of document and input tensors are specified in the schema, as shown above.
You can pass tensors in HTTP requests by using the HTTP parameter
"input.query(myTensor)" (assuming the ranking expression contains "query(myTensor)").

A tensor example can be found in the
[sample application](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation).


#### Batch dimensions

When training your model you will typically have an input that contains a
dimension for batches, for instance an input with sizes `[-1, 784]`.  Here, -1
typically denotes the batch dimension. During ONNX inference in ranking, Vespa uses batch size 1.


## Limitations on model size and complexity

Note that in the above rank profile example, the `onnx` model evaluation
was evaluated in the first phase. In general, evaluating these types of models are
more suitable in the `second-phase` or `global-phase` phases.
See [phased ranking](/en/phased-ranking.html).
Vespa can only import ONNX models that are self-contained and below 2GB in size (protobuf limitation).
Models in which data tensors are split over multiple files, is currently not supported.



## Examples

The [MS Marco](https://github.com/vespa-engine/sample-apps/tree/master/msmarco-ranking)
sample application uses a cross-encoder model to re-rank documents.
The [model-exporting](https://github.com/vespa-engine/sample-apps/tree/master/examples/model-exporting) example
uses onnx models for embedding inference.
[custom-embeddings](https://github.com/vespa-engine/sample-apps/tree/master/custom-embeddings)
has an example of a PyTorch model that is exported to onnx format for use in re-ranking. 


### Using Optimum to export models to ONNX format

We can highly recommend using the [Optimum](https://huggingface.co/docs/optimum/index) library
for exporting models hosted on Huggingface model hub.

For example, to export [BAAI/bge-small-en](https://huggingface.co/BAAI/bge-small-en) from the model hub to onnx format:

```
$ python3 -m pip install optimum onnx onnxruntime
$ optimum-cli export onnx --library transformers --task feature-extraction -m BAAI/bge-small-en --optimize O3 model-output-dir
```

The exported files in `model-output-dir`: `model.onnx` and `tokenizer.json` imported directly
into the Vespa [huggingface-embedder](embedding.html#huggingface-embedder).

See also [debugging onnx](#onnx-debug).

In many cases, there are also onnx checkpoints available,
for example [mixedbread-ai/mxbai-embed-large-v1](https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1/tree/main),
these models can then be downloaded and used in Vespa.

```xml
<container id="default" version="1.0">
    <component id="mixedbread" type="hugging-face-embedder">
        <transformer-model url="https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1/resolve/main/onnx/model_quantized.onnx"/>
        <tokenizer-model url="https://huggingface.co/mixedbread-ai/mxbai-embed-large-v1/raw/main/tokenizer.json"/>
        <pooling-strategy>cls</pooling-strategy>
    </component>
    ...
</container>
```

Vespa defaults to `mean` pooling-strategy.
Consult the model card for the pooling method used.
Note the url pattern above.
The url must point to the actual file, not the model card.

Also, Vespa only supports models that are contained in a single onnx file;
if the model is larger than 2GB, the model is split over multiple files, and this is currently not supported in Vespa.

See [cross-encoders](/en/cross-encoders.html#exporting-cross-encoder-models) documentation for examples on how to
export cross-encoder re-rankers using the Optimum library.


## Using Auto Classes to export HF models to ONNX format

Transformer-based models have named inputs and outputs that must be compatible
with the input and output names used by the [embedder](/en/embedding.html).

The [model-exporting](https://github.com/vespa-engine/sample-apps/tree/master/examples/model-exporting)
example includes two scripts to export models and vocabulary files using the default expected input and output names
for embedders using ONNX models.
The input and output names to the embedder are tunable via the `transformer-`parameters in the
[config of the embedder in question](/en/reference/embedding-reference.html).


### Debugging ONNX models

When loading [ONNX](https://onnx.ai/) models for Vespa native [embedders](/en/embedding.html),
the model must have correct inputs and output parameters.
Vespa offers tools to inspect ONNX model files.
Here, _minilm-l6-v2.onnx_ is in the current working directory:

```
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
```

The above model input and output names conform with the
default [bert-embedder parameters](/en/reference/embedding-reference.html#bert-embedder-reference-config).

Similarly, a model for the [hugging-face-embedder parameters](/en/reference/embedding-reference.html#huggingface-embedder-reference-config) defaults:
```
model meta-data:
  input[0]: 'input_ids' long[batch][sequence]
  input[1]: 'attention_mask' long[batch][sequence]
  input[2]: 'token_type_ids' long[batch][sequence]
  output[0]: 'last_hidden_state' float[batch][sequence][384]
```

The shape of the output should be:
```
float[batch][sequence][vector-embedding-dimensionality]
```
Vespa embedders implement the pooling strategy over the output vectors (one per sequence length).

If loading models without the expected input and output parameter names, the container service will not start
(check _vespa.log_ in the container running Vespa):

```
 WARNING container        Container.com.yahoo.container.di.Container
  Caused by: java.lang.IllegalArgumentException: Model does not contain required input: 'input_ids'. Model contains: input
```

When this happens, a deploy looks like:
```
$ vespa deploy --wait 300
Uploading application package ... done

Success: Deployed .

Waiting up to 5m0s for query service to become available ...
Error: service 'query' is unavailable: services have not converged
```

Embedders supports changing the input and output names,
consult [embedding reference](/en/reference/embedding-reference.html) documentation.


### Using vespa-analyze-onnx-model

[vespa-analyze-onnx-model](/en/operations/tools.html#vespa-analyze-onnx-model)
is useful to find model inputs and outputs -
example run on a config server where an application package with a model is deployed to:

```
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
input[0]: tensor<float>(d0[1],d1[4]) -> float[1][4]
output[0]: float[1][3] -> tensor<float>(d0[1],d1[3])
unspecified option[2](max concurrent evaluations), fallback: 1
vm_size: 233792 kB, vm_rss: 54848 kB (no evaluations yet)
vm_size: 233792 kB, vm_rss: 54848 kB (concurrent evaluations: 1)
estimated model evaluation time: 0.00227701 ms
```

The corresponding input/output tensors should be defined as:
```
document doc {
    ...
    field flowercategory type tensor<float>(d0[1],d1[3]) {
        indexing: attribute | summary
    }
}

rank-profile myRank {
    inputs {
        query(myTensor) tensor<float>(d0[1],d1[4])
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
```
