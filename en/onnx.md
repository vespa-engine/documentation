---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Ranking With ONNX Models"
redirect_from:
- /documentation/onnx.html
---

Vespa has support for advanced ranking models through its tensor API. If you
have your model in the [ONNX format](https://onnx.ai/), Vespa can import the
models and use them directly.

## Importing ONNX model files

Add the file containing the ONNX models somewhere under the application
package. For instance, if your model file is `my_model.onnx` you could
add it to the application package under a `files` directory something like
this:

```
├── files
│   └── my_model.onnx
├── schemas
│   └── main.sd
└── services.xml
```

An application package can have multiple models.

To download models during deployment,
see [deploying remote models](application-packages.html#deploying-remote-models).

## Ranking with ONNX models

To make the above model available for ranking, you define the model in the
schema, and then you can refer to the model using the `onnx` (or `onnxModel`)
ranking feature:

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

```
onnx(my_onnx_model).output_name{d0:0,d1:0}
```

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
expensive and more suitable in the second phase ranking.

The assumption when evaluating ONNX models in Vespa is that the models will be
used in ranking, meaning that the model will be evaluated once for each
document. Please be aware that this imposes some natural restrictions on the
size and complexity of the models, particularly if the application has a large
number of documents. However, effective use of the first and second phase can
make running deep models feasible.

## Examples

The [Transformers](https://github.com/vespa-engine/sample-apps/tree/master/transformers)
sample application uses an ONNX model to
[re-rank documents](https://github.com/vespa-engine/sample-apps/blob/master/transformers/src/main/application/schemas/msmarco.sd).
The model is [exported](https://github.com/vespa-engine/sample-apps/blob/master/transformers/src/python/setup-model.py)
from [HuggingFace's Transformers](https://huggingface.co/docs/transformers/index) library.

The [Question-Answering](https://github.com/vespa-engine/sample-apps/tree/master/dense-passage-retrieval-with-ann)
sample application uses two different ONNX models:

- One for creating a dense vector representation of a query string for use in ANN retrieval
- One for extracting an answer string from a relevant passage

