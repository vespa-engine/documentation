---
# Copyright Vespa.ai. All rights reserved.
title: "Ranking with TensorFlow Models"
---

Vespa can import TensorFlow models converted to the ONNX format. The tutorial 
[TensorFlow: Deploy model to Vespa through ONNX](https://vespa-engine.github.io/learntorank-DEPRECATED/notebooks/tensorflow-via-onnx.html) 
shows an end-to-end example from training a Learning-to-Rank (LTR) model to 
deploying it to Vespa. The tutorial can be reproduced by running the 
[Jupyter Notebook](https://github.com/vespa-engine/learntorank-DEPRECATED/blob/main/notebooks/tensorflow-via-onnx.ipynb).

Key steps covered in the tutorial above:

- Define and train a `tf_model`.
- Save the model to disk: `tf_model.save("tf_model_file")`
- Convert the model to ONNX with the `tf2onnx` library:
<pre>{% highlight sh %}
$ python3 -m tf2onnx.convert --saved-model tf_model_file --output tf_model.onnx
{% endhighlight %}</pre>
- Inspect expected input/output format with the `onnx` library:
<pre>{% highlight python %}
import onnx
m = onnx.load("simpler_keras_model.onnx")
m.graph.input # check input format
m.graph.output # check output format
{% endhighlight %}</pre>
- Include the model on Vespa .sd file
<pre>
    schema msmarco {
        document msmarco {
            field id type string {
                indexing: summary | attribute
            }
            field text type string {
                indexing: summary | index
            }
        }
        onnx-model ltr_tensorflow {
            file: files/tf_model.onnx
            input input: vespa_input
            output dense: dense
        }
        rank-profile tensorflow {
            function vespa_input() {
                expression {
                    tensor&lt;float&gt;(x[1],y[3]):[
                    	[fieldMatch(text).queryCompleteness, 
                    	fieldMatch(text).significance, 
                    	nativeRank(text)]
                    ]
                }
            }
            first-phase {
                expression: sum(onnx(ltr_tensorflow).dense)
            }
            summary-features {
                onnx(ltr_tensorflow)
                fieldMatch(text).queryCompleteness
                fieldMatch(text).significance
                nativeRank(text)
            }
        }
    }
</pre>
