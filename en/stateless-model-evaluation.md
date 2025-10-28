---
# Copyright Vespa.ai. All rights reserved.
title: "Stateless Model Evaluation"
---

Vespa's speciality is evaluating machine-learned models quickly over large numbers of data points.
However, it can also be used to evaluate models once on request in stateless containers.
By enabling a feature in [services.xml](reference/services.html),
all machine-learned models -
[TensorFlow](tensorflow.html),
[Onnx](onnx.html),
[XGBoost](xgboost.html),
[LightGBM](lightgbm.html) and
[Vespa stateless models](reference/stateless-model-reference.html) -
added to the `models/` directory of the
[application package](reference/application-packages-reference.html),
are made available through both a REST API and a Java API
where you can compute inferences from your own code.

An example application package can be found at in the
[model-evaluation system test](https://github.com/vespa-engine/system-test/tree/master/tests/container/model_evaluation/app).

### The model evaluation tag

To enable both the REST API and the Java API, add the `model-evaluation` tag
inside the [container](jdisc/) clusters where
it is needed in [services.xml](reference/services.html):

```
<container>
    ...
    <model-evaluation/>
    ...
</container>
```

The `model-evaluation` section can optionally contain inference session options for
ONNX models. See [ONNX inference options](#onnx-inference-options).

## Model inference using the REST API

The simplest way to evaluate the model is to use the REST API.
After enabling it as above, a new API path is made available:
`/model-evaluation/v1/`.
To discover and find information about the models
(including expected input parameters to the model) in your application package,
simply follow the links from this root.
To evaluate a model add `/eval` to the query path:

```
http://host:port/model-evaluation/v1/<model-name>/<function>/eval?<param1=...>&...
```

Here <model-name> signifies which model to evaluate as you can deploy
multiple models in your application package.
The <function> specifies
which signature and output to evaluate as a model might have multiple
signatures and outputs you can evaluate.
If a model only has one function, this can be omitted.
Inputs to the model are specified as query parameters for GET requests,
and they can also be in the body part of the request for POST requests.
The expected format for input parameters are tensors as specified
with the [literal form](reference/tensor.html#tensor-literal-form).

See the
[model-inference sample app](https://github.com/vespa-engine/sample-apps/tree/master/model-inference) for an example of this.

### Model evaluation REST API parameters

Model evaluation requests accepts these request parameters:

| Parameter | Type | Description |
| --- | --- | --- |
| format.tensors | String | Controls how tensors are rendered in the result.   | Value | Description | | --- | --- | | `short` | **Default**. Render the tensor value in a JSON object having two keys, "type" containing the value, and "cells"/"blocks"/"values" ([depending on the type](reference/document-json-format.html#tensor)) containing the tensor content.  Render the tensor content in the [type-appropriate short form](reference/document-json-format.html#tensor). | | `long` | Render the tensor value in a JSON object having two keys, "type" containing the value, and "cells" containing the tensor content.  Render the tensor content in the [general verbose form](reference/document-json-format.html#tensor). | | `short-value` | Render the tensor content directly as a JSON value.  Render the tensor content in the [type-appropriate short form](reference/document-json-format.html#tensor). | | `long-value` | Render the tensor content directly as a JSON value.  Render the tensor content in the [general verbose form](reference/document-json-format.html#tensor). | | `string` | Render the tensor content as a string on the [appropriate literal short form](reference/tensor.html#tensor-literal-form). | | `string-long` | Render the tensor content as a string on the [general literal form](reference/tensor.html#general-literal-form). | |

## Model inference using Java

While the REST API gives a basic interface to run model inference,
the Java interface offers far more control
allowing you to for instance implement custom input and output formats.

First, add the following dependency in `pom.xml`:

```
<dependency>
    <groupId>com.yahoo.vespa</groupId>
    <artifactId>container</artifactId>
    <scope>provided</scope>
</dependency>
```

(Or, if you want the minimal dependency,
depend on `model-evaluation` instead of `container`.)

With the above dependency and the `model-evaluation` element
added to `services.xml`,
you can now have your Java component that should evaluate models
take a `ai.vespa.models.evaluation.ModelsEvaluator`
(see [ModelsEvaluator.java](https://github.com/vespa-engine/vespa/blob/master/model-evaluation/src/main/java/ai/vespa/models/evaluation/ModelsEvaluator.java)) instance as a constructor argument
(Vespa will [automatically inject it](jdisc/injecting-components.html)).

Use the `ModelsEvaluator` API (from any thread) to make inferences. Sample code:

```
{% highlight java %}
import ai.vespa.models.evaluation.ModelsEvaluator;
import ai.vespa.models.evaluation.FunctionEvaluator;
import com.yahoo.tensor.Tensor;

// ...

// Create evaluator
FunctionEvaluator evaluator = modelsEvaluator.evaluatorOf("myModel", "mySignature", "myOutput"); // Unambiguous args may be skipped

// Get model inputs for instance from query (here we just construct a sample tensor)
Tensor.Builder b = Tensor.Builder.of(new TensorType.Builder().indexed("d0", 3));
b.cell(0.1, 0);
b.cell(0.2, 0);
b.cell(0.3, 0);
Tensor input = b.build();

// Bind inputs to the evaluator
evaluator.bind("myInput", input);

// Evaluate model. Note: Evaluator must be discarded after a single use
Tensor result = evaluator.evaluate());

// Do something with the result
{% endhighlight %}
```

The [model-inference sample app](https://github.com/vespa-engine/sample-apps/tree/master/model-inference) also has an example of this.

## Unit testing model evaluation in Java

When developing your application it can be helpful to unit test your
models and/or your searchers and document processors during development. Vespa
provides a `ModelsEvaluatorTester` which can be constructed from the
contents of your "models" directory. This allows for testing that the model
works as expected in context of Vespa, and that your searcher or document
processor gets the correct results from your models.

The following dependency is needed in `pom.xml`:

```
<dependency>
    <groupId>com.yahoo.vespa</groupId>
    <artifactId>container-test</artifactId>
    <scope>test</scope>
</dependency>
```

With this you can construct a testable `ModelsEvaluator`:

```
{% highlight java %}
import com.yahoo.vespa.model.container.ml.ModelsEvaluatorTester;

public class ModelsTest {
    @Test
    public void testModels() {
        ModelsEvaluator modelsEvaluator = ModelsEvaluatorTester.create("src/main/application/models");

        // Test the modelsEvaluator directly or construct a searcher and pass it in

    }
}
{% endhighlight %}
```

The `ModelsEvaluator` object that is returned contains all models
found under the directory pass in. Note that this should only be used in unit
testing.

The [model-inference sample app](https://github.com/vespa-engine/sample-apps/tree/master/model-inference) uses this for testing handlers, searchers, and document
processors.

## ONNX inference options

ONNX models are evaluated using [ONNX Runtime](https://onnxruntime.ai/).
Vespa provides the following options to tune inference:

```
<model-evaluation>
    <onnx>
        <models>
            <model name="reranker_margin_loss_v4">
                <intraop-threads>[number]</intraop-threads>
                <interop-threads>[number]</interop-threads>
                <execution-mode>parallel | sequential</execution-mode>
                <gpu-device>[number]</gpu-device>
            </model>
        </models>
    </onnx>
</model-evaluation>
```

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| intraop-threads | optional | number | max(1, CPU count / 4) | The number of threads available for running operations with multithreaded implementations. |
| interop-threads | optional | number | `max(1, CPU count / 4)` if execution mode `parallel` | The number of threads available for running multiple operations in parallel. This is only applicable for `parallel` execution mode. |
| execution-mode | optional | string | sequential | Controls how the operators of a graph are executed, either `sequential` or `parallel`. |
| gpu-device | optional | number |  | Set the GPU device number to use for computation, starting at 0, i.e. if your GPU is `/dev/nvidia0` set this to 0. This must be an Nvidia CUDA-enabled GPU. |

Since stateless model evaluation is based on auto-discovery of models under the
`models` directory in the application package, the above would only
be needed for models that should not use the default settings, or should run on
a GPU.
