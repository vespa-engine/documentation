---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Ranking with TensorFlow Models"
redirect_from:
- /documentation/tensorflow.html
---

Vespa can import TensorFlow models converted to the ONNX format. The tutorial 
[TensorFlow: Deploy model to Vespa through ONNX](https://pyvespa.readthedocs.io/en/latest/use_cases/tensorflow-via-onnx.html) 
shows an end-to-end example from training a Learning-to-Rank (LTR) model to 
deploying it to Vespa. The tutorial can be reproduced by running the 
[Jupyter Notebook](https://github.com/vespa-engine/pyvespa/blob/master/docs/sphinx/source/use_cases/tensorflow-via-onnx.ipynb).

Key steps covered in the tutorial above:

1. Define and train a `tf_model`.
2. Save the model to disk: `tf_model.save("tf_model_file")`
3. Convert the model to ONNX with the `tf2onnx` library:
```bash
python3 -m tf2onnx.convert --saved-model tf_model_file --output tf_model.onnx
```
4. Inspect expected input/output format with the `onnx` library:
```python
import onnx                  

m = onnx.load("simpler_keras_model.onnx")
m.graph.input # check input format
m.graph.output # check output format
```
5. Include the model on Vespa .sd file
```
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
                    tensor<float>(x[1],y[3]):[
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
```


