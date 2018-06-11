---
# Copyright 2018 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Importing ONNX models for ranking"
---

Vespa has support for advanced ranking models through it's tensor API. If you
have your model in the [ONNX format](https://onnx.ai/), Vespa can import the
models and use them in ranking functions directly.

## Importing ONNX models

To import the ONNX model to Vespa, add the directory containing the
model to your application package under a specific directory named `models`.
For instance, if you would like to call the model above as `my_model`, you
would add it to the application package resulting in a directory structure
something like this:

```
├── models
│   └── my_model.onnx
├── searchdefinitions
│   └── main.sd
└── services.xml
```

An application package can have multiple models.

## Ranking with ONNX models

Vespa has a special [ranking
feature](http://docs.vespa.ai/documentation/reference/rank-features.html)
called `ONNX`. This ranking feature specifies the model and optionally the
output to use in a ranking expression. The input to the computation must be
provided by a macro with the same name as the input variable. Consider the
following example:

```
search onnx {
    document onnx {
        field document_tensor type tensor(d0[1],d1[784]) {
            indexing: attribute | summary
            attribute: tensor(d0[1],d1[784])
        }
    }
    rank-profile default inherits default {
        macro Placeholder() {
            expression: attribute(document_tensor)
        }
        first-phase {
            expression: sum(onnx("my_model.onnx", "add"))
        }
    }
}
```

Here, we specify that the model `my_model.onnx` should be run, using the
`output` output. The output is optional if the model only contains a single
output.

ONNX models contain a computational graph. In the following, assume that
the computational graph of the model `my_model.onnx` is as follows, as
visualized by [Netron](https://github.com/lutzroeder/Netron):

![ONNX model](img/onnx_model.png)

This is a very simple graph, illustrating a single layer (without the
activation function) of a neural network. Here, we have a single input,
`Placeholder` and a single output `add`. There are two constant tensors,
the `B` inputs to the MatMul and Add nodes. For Vespa to calculate the
value of the output, it requires the user to specify where to retrieve
the input tensors.

Vespa expects a macro to be specified for each input tensor, and the name of
the macro should be the same as as the input name. In this case, the name of
the macro should be `Placeholder`, which is illustrated in the example search
definition above. The input macro can retrieve the tensor value from any valid
source: a document field as shown here, a value sent along with the query, a
constant value or a parent value. However, the tensor type from the macro must
match the tensor type expected in the model.  The input tensors must have
dimension names starting with `"d0"` for the first dimension, and increasing
for each dimension (i.e. `"d1"`, `"d2"`, etc). The result of the evaluation
will likewise be a tensor with names `"d0"`, `"d1"`, etc.

Note that if names have "/" in them, which is the case when for instance using
name scopes in TensorFlow, these will be replaced with "\_" during import as
slashes are illegal in Vespa ranking expression names.

The types of document tensors are specified in the search definition as shown above.
If you specify the types of query tensors in the
[query profile types](query-profiles.html#query-profile-types"),
you can pass tensors in HTTP requests by using the HTTP parameter
"ranking.features.query(myTensor)" (assuming the ranking expression contains
"query(myTensor)". To do this specify a
[query profile](query-profiles.html) of a type containing

    <field name="ranking.features.query(myTensor)" type="tensor(d0[1],d1[784])" />

[An example can be found in the tensor sample application](https://github.com/vespa-engine/sample-apps/tree/master/basic-search-tensor).

#### Batch dimensions

When training your model you will typically have an input placeholder which
contains a dimension for batches. In the example above, the Placeholder
has size `[-1, 784]`, which signifies that the first dimension (of unknown
size) is the batch dimension. This allows control over the batch size during
training, and it is common to use a batch size much smaller than the entire
training set (i.e. mini-batches) during training.

During run-time evaluation, Vespa typically does inference over a single
exemplar. If this is the case in your network, take care to specifically
set the batch dimension to size 1, as certain optimizations are done
in Vespa to improve evaluation time. This is shown in the example above.


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

## ONNX operation support

Currently, not [all operations in
ONNX](https://github.com/onnx/onnx/blob/master/docs/Operators.md) are
supported. Typical neural networks are supported, but convolutional and
recurrent neural networks are not yet supported. Also, the [ML
extensions](https://github.com/onnx/onnx/blob/master/docs/Operators-ml.md) for
ONNX are currently not yet supported.


