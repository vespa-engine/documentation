---
# Copyright 2018 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Ranking With ONNX Models"
---

Vespa has support for advanced ranking models through it's tensor API. If you
have your model in the [ONNX format](https://onnx.ai/), Vespa can import the
models and use them directly.

## Importing ONNX models

To import the ONNX model to Vespa, add the directory containing the
model to your application package under a specific directory named `models`.
For instance, if you would like to call the model above as `my_model`, you
would add it to the application package resulting in a directory structure
something like this:

```
├── models
│   └── my_model.onnx
├── schemas
│   └── main.sd
└── services.xml
```

An application package can have multiple models.

To download models during deployment,
see [deploying remote models](cloudconfig/application-packages.html#deploying-remote-models).

## Ranking with ONNX models

Vespa has a special [ranking
feature](http://docs.vespa.ai/documentation/reference/rank-features.html)
called `ONNX`. This ranking feature specifies the model and optionally the
output to use in a ranking expression. The input to the computation must be
provided by a function with the same name as the input variable. Consider the
following example:

```
schema onnx {
    document onnx {
        field document_tensor type tensor(d0[1],d1[784]) {
            indexing: attribute | summary
        }
    }
    rank-profile default inherits default {
        function Placeholder() {
            expression: attribute(document_tensor)
        }
        first-phase {
            expression: sum(onnx("my_model.onnx", "add"))
        }
    }
}
```

Here, we specify that the model `my_model.onnx` should be run, using the
`add` output. The output is optional if the model only contains a single
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

Vespa expects a function to be specified for each input tensor, and the name of
the function should be the same as as the input name. In this case, the name of
the function should be `Placeholder`, which is illustrated in the example schema above.
The input function can retrieve the tensor value from any valid
source: a document field as shown here, a value sent along with the query, a
constant value or a parent value. However, the tensor type from the function must
match the tensor type expected in the model.  The input tensors must have
dimension names starting with `"d0"` for the first dimension, and increasing
for each dimension (i.e. `"d1"`, `"d2"`, etc). The result of the evaluation
will likewise be a tensor with names `"d0"`, `"d1"`, etc.

Note that if names have "/" in them, which is the case when for instance using
name scopes in TensorFlow, these will be replaced with "\_" during import as
slashes are illegal in Vespa ranking expression names.

The types of document tensors are specified in the schema as shown above.
If you specify the types of query tensors in the
[query profile types](query-profiles.html#query-profile-types),
you can pass tensors in HTTP requests by using the HTTP parameter
"ranking.features.query(myTensor)" (assuming the ranking expression contains
"query(myTensor)". To do this specify a
[query profile](query-profiles.html) of a type containing

    <field name="ranking.features.query(myTensor)" type="tensor(d0[1],d1[784])" />

A tensor example can be found in the
[sample application](https://github.com/vespa-engine/sample-apps/tree/master/vespa-cloud/album-recommendation).

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

The following is a list of operators currently supported with respective ONNX
opsets. In general, use ONNX opset 8 or above.

<table border="1" class="dataframe" style="text-align:center">
  <col width="150">
  <col width="150">
  <tbody>
    <tr>
      <td><b>Operator</b></td>
      <td><b>Supported opsets</b></td>
    </tr>
    <tr><td>abs</td>               <td>[6, 11]</td></tr>
    <tr><td>acos</td>               <td>[7, 11]</td></tr>
    <tr><td>add</td>                <td>[7, 11]</td></tr>
    <tr><td>asin</td>               <td>[7, 11]</td></tr>
    <tr><td>atan</td>               <td>[7, 11]</td></tr>
    <tr><td>div</td>                <td>[7, 11]</td></tr>
    <tr><td>cast</td>               <td>[1, 11]</td></tr>
    <tr><td>ceil</td>               <td>[6, 11]</td></tr>
    <tr><td>cos</td>                <td>[7, 11]</td></tr>
    <tr><td>concat</td>             <td>[4, 11]</td></tr>
    <tr><td>elu</td>                <td>[6, 11]</td></tr>
    <tr><td>equal</td>              <td>[7, 11]</td></tr>
    <tr><td>exp</td>                <td>[6, 11]</td></tr>
    <tr><td>floor</td>              <td>[6, 11]</td></tr>
    <tr><td>gather</td>             <td>[1, 11]</td></tr>
    <tr><td>greater</td>            <td>[7, 11]</td></tr>
    <tr><td>gemm</td>               <td>[7, 11]</td></tr>
    <tr><td>identity</td>           <td>[1, 11]</td></tr>
    <tr><td>leakyrelu</td>          <td>[6, 11]</td></tr>
    <tr><td>less</td>               <td>[7, 11]</td></tr>
    <tr><td>log</td>                <td>[6, 11]</td></tr>
    <tr><td>max</td>                <td>[8, 11]</td></tr>
    <tr><td>matmul</td>             <td>[1, 11]</td></tr>
    <tr><td>mean</td>               <td>[8, 11]</td></tr>
    <tr><td>min</td>                <td>[8, 11]</td></tr>
    <tr><td>mul</td>                <td>[7, 11]</td></tr>
    <tr><td>neg</td>                <td>[6, 11]</td></tr>
    <tr><td>reciprocal</td>         <td>[6, 11]</td></tr>
    <tr><td>reducel1</td>           <td>[1, 11]</td></tr>
    <tr><td>reducel2</td>           <td>[1, 11]</td></tr>
    <tr><td>reducelogsum</td>       <td>[1, 11]</td></tr>
    <tr><td>reducelogsumexp</td>    <td>[1, 11]</td></tr>
    <tr><td>reducemax</td>          <td>[1, 11]</td></tr>
    <tr><td>reducemean</td>         <td>[1, 11]</td></tr>
    <tr><td>reducemin</td>          <td>[1, 11]</td></tr>
    <tr><td>reduceprod</td>         <td>[1, 11]</td></tr>
    <tr><td>reducesum</td>          <td>[1, 11]</td></tr>
    <tr><td>reducesumsquare</td>    <td>[1, 11]</td></tr>
    <tr><td>relu</td>               <td>[6, 11]</td></tr>
    <tr><td>reshape</td>            <td>[5, 11]</td></tr>
    <tr><td>selu</td>               <td>[6, 11]</td></tr>
    <tr><td>shape</td>              <td>[1, 11]</td></tr>
    <tr><td>sigmoid</td>            <td>[6, 11]</td></tr>
    <tr><td>sin</td>                <td>[7, 11]</td></tr>
    <tr><td>slice</td>              <td>[1, 11]</td></tr>
    <tr><td>softmax</td>            <td>[1, 11]</td></tr>
    <tr><td>split</td>              <td>[2, 11]</td></tr>
    <tr><td>sqrt</td>               <td>[6, 11]</td></tr>
    <tr><td>squeeze</td>            <td>[1, 11]</td></tr>
    <tr><td>sub</td>                <td>[7, 11]</td></tr>
    <tr><td>tan</td>                <td>[7, 11]</td></tr>
    <tr><td>tanh</td>               <td>[6, 11]</td></tr>
    <tr><td>tile</td>               <td>[6, 11]</td></tr>
    <tr><td>transpose</td>          <td>[1, 11]</td></tr>
    <tr><td>unsqueeze</td>          <td>[1, 11]</td></tr>
    <tr><td>where</td>              <td>[1, 11]</td></tr>
  </tbody>
</table>

Currently, not [all operations in
ONNX](https://github.com/onnx/onnx/blob/master/docs/Operators.md) are
supported. Typical neural networks are supported, but convolutional and
recurrent neural networks are not yet supported. Also, the [ML
extensions](https://github.com/onnx/onnx/blob/master/docs/Operators-ml.md) for
ONNX are currently not yet supported.

