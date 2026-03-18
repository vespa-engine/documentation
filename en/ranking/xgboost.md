---
# Copyright Vespa.ai. All rights reserved.
title: "Ranking with XGBoost Models"
redirect_from:
  - /en/xgboost
---

Vespa supports importing Gradient Boosting Decision Tree (GBDT) models trained with
[XGBoost](https://xgboost.readthedocs.io/).

## Exporting models from XGBoost

Vespa supports two XGBoost model formats: UBJ (recommended) and JSON (legacy).

### UBJ format (recommended)

{% include version.html version="8.656.31" %}

The recommended way to export an XGBoost model for Vespa is using
[`save_model()`](https://xgboost.readthedocs.io/en/latest/python/python_api.html#xgboost.Booster.save_model)
with the `.ubj` (Universal Binary JSON) extension.
UBJ has been the default XGBoost model format since XGBoost 2.1.0 and
preserves all model information: tree structure, `base_score`, feature names, and objective.

<pre>{% highlight python %}
import xgboost as xgb
import numpy as np

# Train a model
dtrain = xgb.DMatrix(np.random.rand(100, 2), label=np.random.randint(2, size=100),
                      feature_names=["feature_1", "feature_2"])
param = {"max_depth": 2, "objective": "binary:logistic"}
model = xgb.train(param, dtrain, num_boost_round=10)

# Export as UBJ
model.save_model("my_model.ubj")
{% endhighlight %}</pre>

{% include warning.html content='Do **not** use `save_model("model.json")` — this produces a different JSON structure
(with a `learner` wrapper) that Vespa cannot parse. Only `dump_model()` with `dump_format="json"` is supported for the JSON path.' %}

Since the UBJ format preserves the objective, Vespa automatically applies the correct
transformation (e.g. sigmoid for logistic objectives) — no need to wrap the ranking expression manually.

### JSON format (legacy)

Vespa also supports importing XGBoost's JSON model dump via
[`dump_model()`](https://xgboost.readthedocs.io/en/latest/python/python_api.html#xgboost.Booster.dump_model)
with `dump_format="json"`.

<pre>{% highlight python %}
import xgboost as xgb

dtrain = xgb.DMatrix("training-vectors.txt")
param = {"base_score": 0, "max_depth": 1, "objective": "reg:squarederror"}
bst = xgb.train(param, dtrain, 2)
bst.dump_model("trained-model.json", fmap="feature-map.txt", with_stats=False, dump_format="json")
{% endhighlight %}</pre>

This produces a JSON array of tree objects:

<pre>{% highlight json %}
[
  { "nodeid": 0, "depth": 0, "split": "fieldMatch(title).completeness", "split_condition": 0.772132337, "yes": 1, "no": 2, "missing": 1, "children": [
    { "nodeid": 1, "leaf": 0.673938096 },
    { "nodeid": 2, "leaf": 0.791884363 }
  ]},
  { "nodeid": 0, "depth": 0, "split": "fieldMatch(title).importance", "split_condition": 0.606320798, "yes": 1, "no": 2, "missing": 1, "children": [
    { "nodeid": 1, "leaf": 0.469432801 },
    { "nodeid": 2, "leaf": 0.55586201 }
  ]}
]
{% endhighlight %}</pre>

The `split` attribute represents the Vespa feature name and must resolve to a Vespa
[rank feature](../reference/ranking/rank-features.html) defined in the [document schema](../basics/schemas.html),
or a user-defined [function](ranking-expressions-features.html#function-snippets).

The training data is represented using [LibSVM text format](https://xgboost.readthedocs.io/en/latest/tutorials/input_format.html).
See also a complete [XGBoost training notebook](https://github.com/vespa-engine/sample-apps/blob/master/commerce-product-ranking/notebooks/Train-xgboost.ipynb) using `ranking` objective.

{% include warning.html content='`dump_model()` JSON does **not** preserve `base_score`.
Set `base_score=0` during training, or accept that Vespa predictions will be offset.
For logistic objectives, you must manually wrap the expression in `sigmoid()` (see [Objective types](#xgboost-objective-types)).' %}

## Feature mappings from XGBoost to Vespa

Model feature names must map to Vespa [rank features](../reference/ranking/rank-features.html).
The mapping method depends on the model format.

### UBJ feature mapping

For UBJ models, place a features file named `<model_name>-features.txt` alongside the `.ubj` file
in the `models` directory. The file contains one feature name per line, matching the training column order:

<pre>
feature_1
feature_2
feature_3
</pre>

For a model file named `my_model.ubj`, the features file must be named `my_model-features.txt`.

Then define rank profile [functions](ranking-expressions-features.html#function-snippets)
that match the feature names and map them to Vespa document attributes or query features:

<pre>
schema my_app {
    document my_app {
        field price type double {
            indexing: summary | attribute
        }
        field popularity type double {
            indexing: summary | attribute
        }
    }
    rank-profile my_rank_profile inherits default {
        function feature_1() {
            expression: attribute(price)
        }
        function feature_2() {
            expression: attribute(popularity)
        }
        function feature_3() {
            expression: query(user_context)
        }
        first-phase {
            expression: xgboost("my_model.ubj")
        }
    }
}
</pre>

If the model was trained with feature names that are valid Vespa rank features
(e.g. `attribute(price)`), the functions are not needed — Vespa resolves them directly.

### JSON feature mapping

When using `dump_model()`, XGBoost names features by array index (`f0`, `f1`, ...) unless a feature map file (`fmap`) is provided.
The `fmap` maps feature indices to named Vespa features:

<pre>
$ cat feature-map.txt | egrep "fieldMatch\(title\).completeness|fieldMatch\(title\).importance"
36  fieldMatch(title).completeness q
39  fieldMatch(title).importance q
</pre>

In this example, feature at index 36 maps to
[fieldMatch(title).completeness](../reference/ranking/rank-features.html#fieldMatch(name).completeness)
and index 39 maps to [fieldMatch(title).importance](../reference/ranking/rank-features.html#fieldMatch(name).importance).

Format of `feature-map.txt: <featureid> <featurename> <q or i or int>\n`:
  - Feature id must be from 0 to number of features, in sorted order
  - `i` means this feature is a binary indicator feature
  - `q` means this feature is a quantitative value, such as age, time, can be missing
  - `int` means this feature is an integer value (when int is hinted, the decision boundary will be integer)

When using Pandas `DataFrame`s with column names, the feature names are embedded directly in the JSON dump
and a feature map file is not needed.

## Importing XGBoost models

To import an XGBoost model, add the model file to your application package
under the `models` directory.
For UBJ models, also include the corresponding `-features.txt` file:

<pre>
├── models
│   ├── my_model.ubj
│   ├── my_model-features.txt
│   └── legacy_model.json
├── schemas
│   └── main.sd
└── services.xml
</pre>

An application package can have multiple models.

## Ranking with XGBoost models

Vespa has a `xgboost` [ranking feature](../reference/ranking/rank-features.html).
This ranking feature specifies the model to use in a ranking expression.
Both UBJ and JSON models use the same ranking feature:

<pre>
schema my_app {
    rank-profile prediction inherits default {
        first-phase {
            expression: nativeRank
        }
        second-phase {
            expression: xgboost("my_model.ubj")
        }
    }
}
</pre>

Here, we specify that the model `my_model.ubj` is applied to the top ranking documents
by the first-phase ranking expression.
The query request must specify `prediction` as the [ranking.profile](../reference/api/query.html#ranking.profile).
See also [Phased ranking](phased-ranking.html) on how to control number of data points/documents which is exposed to the model.

Generally the run time complexity is determined by:

* The number of documents evaluated [per thread](../performance/sizing-search.html) / number of nodes and the query filter
* The complexity of computing features. For example `fieldMatch` features are 100x more expensive than `nativeFieldMatch/nativeRank`.
* The number of XGBoost trees and the maximum depth per tree

Serving latency can be brought down by [using multiple threads per query request](../performance/practical-search-performance-guide.html#multithreaded-search-and-ranking).

## Categorical features

{% include warning.html content="Vespa does **not** support XGBoost's native categorical splits
(`enable_categorical=True`). Deploying a model with native categorical splits will **silently produce
wrong predictions** — Vespa interprets the categorical split condition as a numerical threshold." %}

To use categorical features with XGBoost models in Vespa, integer-encode them before training:

<pre>{% highlight python %}
import xgboost as xgb
import pandas as pd

# Integer-encode categorical features
category_map = {"small": 0, "medium": 1, "large": 2}
df["size"] = df["size_raw"].map(category_map).astype(float)

# Train without enable_categorical — XGBoost uses numerical splits on the integers
dtrain = xgb.DMatrix(df[feature_cols], label=targets)
param = {"max_depth": 4, "objective": "binary:logistic"}
model = xgb.train(param, dtrain, num_boost_round=100)
model.save_model("my_model.ubj")
{% endhighlight %}</pre>

In the Vespa schema, store integer-encoded categoricals as `int` attributes
and map them via rank profile functions like any other numerical feature.

Note: Vespa's [LightGBM](lightgbm.html) importer does support native categorical splits.

## XGBoost objective types

Vespa can import XGBoost models trained with any
[objective](https://xgboost.readthedocs.io/en/stable/parameter.html#learning-task-parameters).
Common objectives include:

* Regression `reg:squarederror` / `reg:logistic`
* Classification `binary:logistic`
* Ranking `rank:pairwise`, `rank:ndcg` and `rank:map`

Vespa evaluates XGBoost models by summing the tree outputs.
The only objective-specific behavior is for logistic objectives (`reg:logistic` and `binary:logistic`),
where the raw tree sum must be passed through a sigmoid function to produce a probability.

### UBJ models

For UBJ models, Vespa reads the objective from the model file.
For logistic objectives, the `base_score` is automatically transformed (logit)
so the model output matches XGBoost's predictions without manual adjustment:

<pre>
schema my_app {
    rank-profile classify inherits default {
        first-phase {
            expression: xgboost("my_classifier.ubj")
        }
    }
}
</pre>

Note that UBJ does not automatically apply a sigmoid to the final output.
For logistic objectives, wrap the expression in `sigmoid()` if you need a probability:

<pre>
schema my_app {
    rank-profile classify inherits default {
        first-phase {
            expression: sigmoid(xgboost("my_classifier.ubj"))
        }
    }
}
</pre>

For ranking objectives and `reg:squarederror`, the raw tree sum can be used directly.

### JSON models

For JSON models exported with `dump_model()`, the objective and `base_score` are **not** preserved.

For `reg:logistic` and `binary:logistic`, the raw margin tree sum
needs to be passed through the [sigmoid function](../reference/ranking/ranking-expressions.html)
to represent the probability of class 1.
For regression, the model can be directly imported
but `base_score` should be set to 0 during training as it is not included in the dump.

An example using the sklearn toy datasets:

<pre>{% highlight python %}
from sklearn import datasets
import xgboost as xgb
breast_cancer = datasets.load_breast_cancer()
c = xgb.XGBClassifier(n_estimators=20, objective="binary:logistic")
c.fit(breast_cancer.data, breast_cancer.target)
c.get_booster().dump_model("binary_breast_cancer.json", fmap="feature-map.txt", dump_format="json")
c.predict_proba(breast_cancer.data)[:, 1]
{% endhighlight %}</pre>

To represent the `predict_proba` function of XGBoost for the binary classifier in Vespa,
use the [sigmoid function](../reference/ranking/ranking-expressions.html):

<pre>
schema my_app {
    rank-profile prediction-binary inherits default {
        first-phase {
            expression: sigmoid(xgboost("binary_breast_cancer.json"))
        }
    }
}
</pre>

When the `base_score` is not the default (0.5), the sigmoid alone is insufficient.
The full formula accounting for `base_score` is:

<pre>
schema my_app {
    rank-profile prediction-binary inherits default {
        constants {
            base_score: 0.5
        }
        first-phase {
            expression: 1.0 / (1.0 + (1.0 - base_score) / base_score * exp(-(xgboost("binary_breast_cancer.json"))))
        }
    }
}
</pre>

Replace `0.5` with the actual `base_score` used during training.
See the [XGBoost System Test](https://github.com/vespa-engine/system-test/tree/master/tests/search/xgboost) for a complete working example.

## Debugging Vespa inference score versus XGBoost predict score

* For JSON models, the `base_score` and optimal number of trees (if trained with early stopping) are lost in the dump.
  UBJ models preserve this information.
  XGBoost also has different predict functions (e.g. predict/predict_proba).
  The following [XGBoost System Test](https://github.com/vespa-engine/system-test/tree/master/tests/search/xgboost)
  demonstrates how to represent different types of XGBoost models in Vespa.
* For training, features should be scraped from Vespa, using either `match-features` or `summary-features` so
  that features from offline training matches the online Vespa computed features.
  Dumping features can also help debug any differences by zooming into specific query,document pairs
  using [recall](../reference/api/query.html#recall) parameter.
* It's also important to use the highest possible precision
  when reading Vespa features for training as Vespa outputs features using `double` precision.
  If the training routine rounds features to `float` or other more compact floating number representations, feature split decisions might differ in Vespa versus XGBoost.
* In a distributed setting when multiple nodes use the model, text matching features such as `nativeRank`, `nativeFieldMatch`, `bm25` and `fieldMatch`
  might differ, depending on which node produced the hit. The reason is that all these features use [term(n).significance](../reference/ranking/rank-features.html#query-features), which is computed from the locally indexed corpus. The `term(n).significance` feature
  is related to *Inverse Document Frequency (IDF)*. The `term(n).significance` should be set by a searcher in the container for global correctness as each node will estimate the significance values from the local corpus.
