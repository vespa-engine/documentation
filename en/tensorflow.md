---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Ranking with TensorFlow Models"
redirect_from:
- /documentation/tensorflow.html
---

Vespa has support for advanced ranking models through its tensor API.
If you have models that are trained in TensorFlow,
Vespa can import the models and use them directly.



## Exporting models from TensorFlow

Vespa supports TensorFlow's [SavedModel](https://www.tensorflow.org/programmers_guide/saved_model#save_and_restore_models)
for importing models. `SavedModel` is a hermetic serialization format
that stores the model and primarily contains a `meta graph` which holds
the dataflow graph, variables, assets and signatures. Signatures define
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
├── schemas
│   └── main.sd
└── services.xml
```

An application package can have multiple models, as long as they are in their
own directories.

To download models during deployment,
see [deploying remote models](application-packages.html#deploying-remote-models).

## Ranking with TensorFlow models

Vespa has a special [ranking feature](reference/rank-features.html) called `tensorflow`.
This ranking feature specifies the model, the signature and the output to use in a ranking expression.
The input to the computation must be provided by a function with the same name as the input variable.
Consider the following example:

```
schema tf {
    document tf {
        field document_tensor type tensor<float>(d0[1],d1[784]) {
            indexing: attribute | summary
        }
    }
    rank-profile default inherits default {
        inputs {
            query(myTensor) tensor(d0[1],d1[784])
        }

        function input_tensor() {
            expression: attribute(document_tensor)
        }
        first-phase {
            expression: sum(tensorflow("my_model/saved", "serving_default", "output"))
        }
    }
}
```

Here, we specify that the model `my_model` should be run, using the
`serving_default` signature and the `output` output. The signature is optional
if the model only contains a single signature. Likewise, the output is optional
if the model only contains a single output.

The input to the model was specified in the signature above as the Python variable
`x`. This was a placeholder given the name `input_tensor`. Vespa expects a
function to be specified for each input tensor having the same name as the input. Note
that if a name has not been specified in TensorFlow, placeholder will be given
the default names 'Placeholder', 'Placeholder_1' etc. Also note that if names
have "/" in them, which is the case when using name scopes in TensorFlow, these
will be replaced with "\_" during import as slashes are illegal in Vespa ranking
expression names.

If you are uncertain of which signatures, inputs, outputs and types a model
contains, you can use the `saved_model_cli` command to view a saved model:

    $ saved_model_cli show --dir saved --all

    MetaGraphDef with tag-set: 'serve' contains the following SignatureDefs:

    signature_def['serving_default']:
      The given SavedModel SignatureDef contains the following input(s):
        inputs['x'] tensor_info:
            dtype: DT_FLOAT
            shape: (-1, 784)
            name: Placeholder:0
      The given SavedModel SignatureDef contains the following output(s):
        outputs['y'] tensor_info:
            dtype: DT_FLOAT
            shape: (-1, 10)
            name: add:0
      Method name is: tensorflow/serving/predict

The input function can retrieve the tensor value from any valid source: a document
field as shown here, a value sent along with the query, a constant value or a
parent value. However, the tensor type from the function must match the tensor
type expected in the model. The input tensors must have dimension names
starting with `"d0"` for the first dimension, and increasing for each dimension
(i.e. `"d1"`, `"d2"`, etc.). The result of the evaluation will likewise be
a tensor with names `"d0"`, `"d1"`, etc.

The types of document and input tensors are specified in the schema as shown above.
You can then pass tensors in HTTP requests by using the HTTP parameter
"input.query(myTensor)" (assuming the ranking expression contains "query(myTensor)").

A tensor example can be found in the
[sample application](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation).

#### Batch dimensions

When training your model you will typically have an input placeholder which
contains a dimension for batches. In the example above, the `x` placeholder
has size `[None, 784]`, which signifies that the first dimension (of unknown
size) is the batch dimension. This allows control over the batch size during
training, and it is common to use a batch size much smaller than the entire
training set (i.e. mini-batches) during training.

During run-time evaluation, Vespa typically does inference over a single
exemplar. If this is the case in your network, take care to specifically
set the batch dimension to size 1, as certain optimizations are done
in Vespa to improve evaluation time. This is shown in the example above.

## Updating variables without redeploying the application

Sometimes it is desirable to update the TensorFlow variables of a model frequently,
e.g. when a neural net with a fixed layout is retrained frequently to update weights
and biases in a reinforcement learning setup.

It is possible to do this without redeploying the application by storing those
tensors in a global document instead of as constants in the application package.
This is explained in the following steps.

### 1. Determine the Vespa name and type of the TensorFlow variable(s)

Tensor dimensions in TensorFlow are implicitly named and ordered, while
this is explicit in Vespa. Vespa will determine the dimension name and
order which leads to the most efficient execution during import of your model.
This exact type specification needs to be used in the steps below.

In addition, Vespa will prefix the variable name by the directory path under "models"
and replace any slashes by underscore.

When importing the TensorFlow model during deployment, Vespa will output
the following INFO log message:

```
Importing TensorFlow variable [TensorFlow name] as [Vespa name] of type [Vespa type]
```

Find this log message for the variables you want to make update-able and take note
of the Vespa name and type.

### 2. Create a global document containing the tensor variables as fields

1. Add a <a href="reference/services-content.html#document">global document type</a>:
Add <code>&lt;document type="myvariables" mode="index" global="true"/&gt;</code> to
the &lt;documents&gt; list in your services.xml.

1. Add attribute fields for your tensors in the document definition
(one per TensorFlow variable to make update-able), using the type spec found
in step 1 and any name:
```
schema myvariables {
    document myvariables {
        field my_tf_variable type tensor<float>(y[10],x[20]) {
            indexing: attribute
        }
    }
}
```


### 3. Refer to the global document from your regular document type

1. Add a <a href="reference/schema-reference.html#type:reference">reference</a>
to the global document and import the fields:
```
schema mydocument {
    document mydocument {
        field myvariables_ref type reference<myvariables> {
            indexing: attribute
        }
    }
    import field myvariables_ref.my_tf_variable as my_tf_variable {}
}
```

1. Add a reference to the same global variable document from all your documents.
All documents should contain the value "id:mynamespace:myvariables::1" in the
myvariables_ref field. You can add this value to all documents by doing an
<a href="reference/document-v1-api-reference.html#put">update</a> on each document with the JSON
```
{
    "fields": {
        "myvariables_ref": {
            "assign": "id:mynamespace:myvariables::1"
        }
    }
}
```

### 4. Add a function returning the value of the imported global field

Create a function with the exact Vespa name found in step 1.
This function will override the variable value found in the application package.

```
function vespa_name_of_tf_variable {
    expression: attribute(my_tf_variable)
}
```

### 5. Convert and feed the variables whenever they are updated

Whenever the TensorFlow model is retrained to produce new variable values,
write them to Vespa as follows:

1. Convert the Variable value to the Vespa document format:
Obtain <a href="https://mvnrepository.com/artifact/com.yahoo.vespa/model-integration">model-integration.jar</a>
(with dependencies), and run
```
java -cp model-integration-jar-with-dependencies.jar ai.vespa.rankingexpression.importer.tensorflow.VariableConverter \
      [modelDirectory] [TensorFlowVariableName] [VespaType]
```
or, if you do this from Java, call ai.vespa.rankingexpression.importer.tensorflow.VariableConverter.importVariable
with the same arguments.

1. Update the global document.
   Use e.g. <a href="reference/document-v1-api-reference.html">/document/v1/</a> to PUT a new value for your variable:
```
curl -X PUT -H "Content-Type:application/json" --data-binary @update.json http://hostname:8080/document/v1/mynamespace/myvariables/docid/1
```
Where update.json follows the <a href="reference/document-json-format.html">document json format</a>:
```
{
    "fields": {
        "my_tf_variable": {
            "assign": [The variable value output from the previous step]
        }
    }
}
```

As this is a global document, the new value will immediately be used when evaluating any document.

## Limitations on model size and complexity

Note that in the above rank profile example, the `tensorflow` model evaluation
was put in the first phase ranking. In general, evaluating these models are
expensive and more suitable in the second phase ranking.

The assumption when evaluating TensorFlow models in Vespa is that the models
will be used in ranking, meaning that the model will be evaluated once for each
document. Please be aware that this imposes some natural restrictions on the
size and complexity of the models, particularly if the application has a large
number of documents. However, effective use of the first and second phase can
make running deep models feasible.

## TensorFlow operation support

Currently, not [all operations in TensorFlow](https://www.tensorflow.org/api_docs/cc/)
are supported. Typical neural networks are supported, but convolutional and
recurrent neural networks are not yet supported.


