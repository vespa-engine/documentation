---
# Copyright Vespa.ai. All rights reserved.
title: "Ranking with LightGBM Models"
---

[LightGBM](https://github.com/microsoft/LightGBM) is a gradient boosting
framework, similar to [XGBoost](xgboost.html). Among other
[advantages](https://github.com/microsoft/LightGBM/blob/master/docs/Experiments.rst#comparison-experiment),
one defining feature of LightGBM over XGBoost is that it directly supports
categorical features. If you have models that are trained with
[LightGBM](https://github.com/microsoft/LightGBM), Vespa can import the models
and use them directly.


## Exporting models from LightGBM

Vespa supports importing LightGBM's
[`dump_model`](https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.Booster.html#lightgbm.Booster.dump_model).
This dumps the tree model and other useful data such as feature names,
objective functions, and values of categorical features to a JSON file.  
An example of training and saving a model suitable for use in Vespa is as follows.

<pre>{% highlight python %}
import json
import lightgbm as lgb
import numpy as np
import pandas as pd

# Create random training set
features = pd.DataFrame({
            "feature_1": np.random.random(100),
            "feature_2": np.random.random(100),
        })
targets = ((features["feature_1"] + features["feature_2"]) > 1.0) * 1.0
training_set = lgb.Dataset(features, targets)

# Train the model
params = {
    'objective': 'binary',
    'metric': 'binary_logloss',
    'num_leaves': 3,
}
model = lgb.train(params, training_set, num_boost_round=5)

# Save the model
with open("lightgbm_model.json", "w") as f:
    json.dump(model.dump_model(), f, indent=2)
{% endhighlight %}</pre>

While this particular model isn't doing anything really useful, the output
file `lightgbm_model.json` can be imported directly into Vespa.

See also a complete example of how to train a ranking function, using learning to rank 
with ranking losses, in this 
[notebook](https://github.com/vespa-engine/sample-apps/blob/master/commerce-product-ranking/notebooks/Train-lightgbm.ipynb).

## Importing LightGBM models

To import the LightGBM model into Vespa, add the model file to the
application package under a directory named `models`, or a
subdirectory under `models`.  For instance, for the above model `lightgbm_model.json`,
add it to the application package resulting in a directory structure like this:

<pre>
├── models
│   └── lightgbm_model.json
├── schemas
│   └── main.sd
└── services.xml
</pre>

Note that an application package can have multiple models. After putting the
model in the `models` directory, it is available for both ranking and
[stateless model evaluation](stateless-model-evaluation.html).

## Ranking with LightGBM models

Vespa has a [ranking feature](reference/rank-features.html)
called `lightgbm`. This ranking feature specifies the model to use in a ranking
expression, relative under the `models` directory. Consider the following example:

<pre>
schema test {
    rank-profile classify inherits default {
        first-phase {
            expression: lightgbm("lightgbm_model.json")
        }
    }
}
</pre>

Here, we specify that the model `lightgbm_model.json` (directly under the
`models` directory) is applied to all documents matching a query which uses
rank-profile `classify`. One important issue to consider is how to map features
in the model to features that are available for Vespa to use in ranking.

Take a look at the JSON file dumped from the example above:

<pre>
{
  "name": "tree",
  "version": "v3",
  "num_class": 1,
  "num_tree_per_iteration": 1,
  "label_index": 0,
  "max_feature_idx": 1,
  "average_output": false,
  "objective": "binary sigmoid:1",
  "feature_names": [
    "feature_1",
    "feature_2"
  ],
  "monotone_constraints": [],
  "tree_info": [
    ....
  ],
  "pandas_categorical": []
}
</pre>

Here, the section `feature_names` consists of the feature names used in the
training set. When this model is evaluated in Vespa, Vespa expects that these
feature names are valid [rank features](reference/rank-features.html).
Examples are `attribute(field_name)` for a value that should be retrieved from
a document, `query(name)` for a value that should be retrieved from the query,
or possibly from other more complex rank features such as `fieldMatch(name)`.
You can also define [functions](https://docs.vespa.ai/en/ranking-expressions-features.html#function-snippets) (which are valid rank features) with the LightGBM
feature name to perform the mapping. An example:

<pre>
schema test {
    document test {
        field doc_attrib type double {
            indexing: summary | attribute
        }
    }
    rank-profile classify inherits default {
        function feature_1() {
            expression: attribute(doc_attrib)
        }
        function feature_2() {
            expression: query(query_value)
        }
        first-phase {
            expression: nativeRank
        }
        second-phase {
            expression: lightgbm("lightgbm_model.json")
        }
    }
}
</pre>

Here, when Vespa evaluates the model, it retrieves the value of `feature_1`
from a document attribute called `doc_attrib`, and the value if `feature_2`
from a query value passed along with the query.

One can also use `attribute(doc_attrib)` directly as a feature name when
training the LightGBM model. This allows dumping rank features from Vespa
to train a model directly. 

Here, we specify that the model `lightgbm_model.json` is applied to the top ranking documents by the first-phase ranking expression. 
The query request must specify `classify` as the [ranking.profile](reference/query-api-reference.html#ranking.profile). 
See also [Phased ranking](phased-ranking.html) on how to control number of data points/documents which is exposed to the model.

Generally the run time complexity is determined by:

* The number of documents evaluated [per thread](performance/sizing-search.html) / number of nodes and the query filter
* The complexity of computing features. For example `fieldMatch` features are 100x more expensive that `nativeFieldMatch/nativeRank`.
* The number of trees and the maximum depth per tree

Serving latency can be brought down by [using multiple threads per query request](performance/practical-search-performance-guide.html#multithreaded-search-and-ranking). 

## Objective functions

If you have used XGBoost with Vespa previously, you might have noticed you
have to wrap the `xgboost` feature in for instance a `sigmoid` function if
using a binary classifier. That should not be needed in LightGBM, as that
information is passed along in the model dump as seen in the `objective` section
in the JSON output above.

Currently, Vespa supports importing models trained with the following objectives: 

- `binary` 
- `regression`
- `lambdarank`
- `rank_xendcg`
- `rank_xendcg`

For more information on LightGBM and objective functions, see
[`objective`](https://lightgbm.readthedocs.io/en/latest/Parameters.html#objective).

## Using categorical features

LightGBM has the option of directly training on categorical features. Example:

<pre>
features = pd.DataFrame({
            "numerical":   np.random.random(5),
            "categorical": pd.Series(np.random.permutation(["a", "b", "c", "d", "e"])), dtype="category"),
           })
</pre>

Here, the `categorical` feature is marked with the Pandas dtype `category`. This
tells LightGBM to send the categorical values in the `pandas_categorical` section
in the JSON example above. This allows Vespa to extract the proper categorical values
to use. This is important, because other methods of using categorical variables
will result in the category values being "1", "2", ... "n", and sending in "a" in
this case for model evaluation will probably result in an erroneous result. To ensure
that categorical variables are properly handled, construct training data based
on Pandas tables and use the `category` dtype on categorical columns.

In Vespa categorical features are strings, so mapping the above feature
for instance to a document field would be:

<pre>
schema test {
    document test {
        field numeric_attrib type double {
            indexing: summary | attribute
        }
        field string_attrib type string {
            indexing: summary | attribute
        }
    }
    rank-profile classify inherits default {
        function numerical() {
            expression: attribute(numeric_attrib)
        }
        function categorical() {
            expression: attribute(string_attrib)
        }
        first-phase {
            expression: lightgbm("lightgbm_model.json")
        }
    }
}
</pre>

Here, the string value of the document would be used as the feature value when evaluating
this model for every document.

## Debugging Vespa inference score versus LightGBM predict score 
 
* When dumping LightGBM models to a JSON representation some of the model information is lost
  (e.g. the `base_score` or the optimal number of trees if trained with early stopping).
  
* For training, features should be scraped from Vespa, using either `match-features` or `summary-features` so
  that features from offline training matches the online Vespa computed features. Dumping
  features can also help debug any differences by zooming into specific query,document pairs
  using [recall](reference/query-api-reference.html#recall) parameter. 

* It's also important to use the highest possible precision
  when reading Vespa features for training as Vespa outputs features using `double` precision. 
  If the training routine rounds features to `float` or other more compact floating number representations, feature split decisions might differ in Vespa versus XGboost.
* In a distributed setting when multiple nodes uses the model, text matching features such as `nativeRank`, `nativFieldMatch`, `bm25` and `fieldMatch`
  might differ, depending on which node produced the hit. The reason is that all these features use [term(n).significance](https://docs.vespa.ai/en/reference/rank-features.html#query-features), which is computed locally indexed corpus. The `term(n).significance` feature 
  is related to *Inverse Document Frequency (IDF)*. The `term(n).significance` should be set by a searcher in the container for global correctness as each node will estimate the significance values from the local corpus.

