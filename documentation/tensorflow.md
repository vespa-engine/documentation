---
# Copyright 2018 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Ranking with TensorFlow models in Vespa"
---

<div style="background-color: #CD5C5C;">
Import of TensorFlow models is currently a BETA feature.
</div>

Vespa has support for advanced ranking models through it's tensor API. If
you have models that are trained in TensorFlow, Vespa can import the models
and use them in ranking functions directly.

## Exporting models from TensorFlow

Vespa supports TensorFlow's [SavedModel](https://www.tensorflow.org/programmers_guide/saved_model#overview_of_saving_and_restoring_models)
for importing models. `SavedModel` is a hermetic serialization format
that stores the model and primarily contains a `meta graph` which holds
the dataflow graph, variables, assets and signatures. Signatures defines
the set of inputs and outputs to the graph and are instrumental to instruct
Vespa on how to import and evaluate the models.

Here is a Python example of storing a model:

```
    # Define python variables
    x = tf.placeholder(tf.float32, [None, 784, name="input_tensor"])
    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))
    y = tf.matmul(x, W) + b

    # Train model (omitted here) ...

    # Save model
    export_path = "saved"
    builder = tf.saved_model.builder.SavedModelBuilder(export_path)
    signature = tf.saved_model.signature_def_utils.predict_signature_def(
                        inputs = {'input':x},
                        outputs = {'output':y})
    builder.add_meta_graph_and_variables(sess,
                        [tf.saved_model.tag_constants.SERVING],
                        signature_def_map={'serving_default':signature})
    builder.save(as_text=True)
```

In the example above, we've added a single meta graph with the `SERVING` tag.
This tag is *mandatory* for Vespa to find the correct meta graph to use during
evaluation.

The meta graph contains a single signature called `serving_default`. The
signature is created using the `predict_signature_def` utility function, which
is a signature that does not impose any constraints on the inputs and output
types.  The signature here defines one input labeled 'input' which points to
the `x` Python placeholder, and one output labeled 'output' pointing to the `y`
Python expression. The inputs and outputs are used by Vespa to determine
how to import the model.

After adding the meta graph with the signature to the builder, it is saved to
disk. Vespa supports both text (.pbtxt) and protobuf (.pb) saved models. The output
is a directory containing the protobuf representation of the model as well as
a directory containing the variables of the graph.

## Vespa import

To import the saved TensorFlow model to Vespa, add the directory containing the
model to your application package under a specific directory named `models`.
For instance, if you would like to call the model above as `my_model`, you
would add it to the application package resulting in a directory structure
something like this:

```
├── models
│   └── my_model
│       └── saved
│           ├── saved_model.pbtxt
│           └── variables
│               ├── variables.data-00000-of-00001
│               └── variables.index
├── searchdefinitions
│   └── main.sd
└── services.xml
```

An application package can have multiple models, as long as they are in their
own directories.

## Ranking with TensorFlow models

Vespa has a special [ranking feature](http://docs.vespa.ai/documentation/reference/rank-features.html)
called `tensorflow`. This ranking feature specifies the model,
the signature and the output to use in a ranking expression. The
input to the computation must be provided by a macro with the same
name as the input variable. Consider the following example:

```
rank-profile default inherits default {
    macro input_tensor() {
        expression: attribute(document_tensor)
    }
    first-phase {
        expression: sum(tensorflow("my_model/saved", "serving_default", "output"))
    }
}
```

Here, we specify that the model `my_model` should be run, using the
`serving_default` signature and the `output` output. The signature is optional
if the model only contains a single signature. Likewise, the output is optional
if the model only contains a single output.

The input to the model was specified in the signature above as the Python variable
`x`. This was a placeholder given the name `input_tensor`. Vespa expects a
macro to be specified for each input tensor having the same name as the input. Note
that if a name has not been specified in TensorFlow, placeholder will be given
the default names 'Placeholder', 'Placeholder_1' etc. Also note that if names
have "/" in them, which is the case when using name scopes in TensorFlow, these
will be replaced with "\_" during import as slashes are illegal in Vespa ranking
expression names.

The input macro can retrieve the tensor value from any valid source: a document
field as shown here, a value sent along with the query, a constant value or a
parent value. However, the tensor type from the macro must match the tensor
type expected in the model. The input tensors must have dimension names
starting with `"d0"` for the first dimension, and increasing for each dimension
(i.e. `"d1"`, `"d2"`, etc). The result of the evaluation will likewise be
a tensor with names `"d0"`, `"d1"`, etc.

### Limitations on model size and complexity

Note that in the above rank profile example, the `tensorflow` model evaluation
was put in the first phase ranking. In general, evaluating these models are
expensive and more suitable in the second phase ranking.

The assumption when evaluating TensorFlow models in Vespa is that the models
will be used in ranking, meaning that the model will be evaluated once for each
document. Please be aware that this imposes some natural restrictions on the
size and complexity of the models, particularly if the application has a large
number of documents. However, effective use of the first and second phase can
make running deep models feasible.

### TensorFlow operation support

Currently, not [all operations in TensorFlow](https://www.tensorflow.org/api_docs/cc/)
are supported. Typical neural networks are supported, but convolutional and
recurrent neural networks are not yet supported.

