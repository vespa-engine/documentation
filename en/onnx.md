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

When training your model you will typically have an input which contains a
dimension for batches, for instance an input with sizes `[-1, 784]`.  Here, -1
typically denotes the batch dimension. This allows control over the batch size
during training, and it is common to use a batch size much smaller than the
entire training set (i.e. mini-batches) during training.

During run-time evaluation, Vespa typically does inference over a single
exemplar. If this is the case in your network, take care to specifically
set the batch dimension to size 1.


## Limitations on model size and complexity

Note that in the above rank profile example, the `onnx` model evaluation
was put in the first phase ranking. In general, evaluating these models are
expensive and more suitable in the second-phase or global-phase ranking.

The assumption when evaluating ONNX models in Vespa is that the models will be
used in ranking, meaning that the model will be evaluated once for each
document. Please be aware that this imposes some natural restrictions on the
size and complexity of the models, particularly if the application has a large
number of documents. However, effective use of [phased ranking](phased-ranking.html)
can make running deep models feasible.

## Examples

The [Transformers](https://github.com/vespa-engine/sample-apps/tree/master/transformers)
sample application uses an ONNX model to
[re-rank documents](https://github.com/vespa-engine/sample-apps/blob/master/transformers/application/schemas/msmarco.sd).
The model is [exported](https://github.com/vespa-engine/sample-apps/blob/master/transformers/bin/setup-model.py)
from [HuggingFace's Transformers](https://huggingface.co/docs/transformers/index) library.

The [Question-Answering](https://github.com/vespa-engine/sample-apps/tree/master/dense-passage-retrieval-with-ann)
sample application uses two different ONNX models:

- One for creating a dense vector representation of a query string for use in ANN retrieval
- One for extracting an answer string from a relevant passage

## Using vespa-analyze-onnx-model
[vespa-analyze-onnx-model](reference/vespa-cmdline-tools.html#vespa-analyze-onnx-model)
is useful to find model inputs and outputs -
example run on a config server where an application package with a model is deployed to:
<pre>
$ docker exec vespa /opt/vespa/bin/vespa-analyze-onnx-model \
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
