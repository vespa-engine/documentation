---
# Copyright 2018 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Ranking with XGBoost Models"
---

If you have models that are trained in XGBoost, Vespa can import the models
and use them directly.

## Exporting models from XGBoost

Vespa supports XGBoost's JSON model dump for importing models. When dumping
the trained model, XGBoost allows users to set the `dump_format` to `json`,
and users can specify the feature names to be used in `fmap`.

Here is an example of an XGBoost JSON model dump with 2 trees:

```
[
  { "nodeid": 0, "depth": 0, "split": "f29", "split_condition": -0.1234567, "yes": 1, "no": 2, "missing": 1, "children": [
    { "nodeid": 1, "depth": 1, "split": "f56", "split_condition": -0.242398, "yes": 3, "no": 4, "missing": 3, "children": [
      { "nodeid": 3, "leaf": 1.71218 },
      { "nodeid": 4, "leaf": -1.70044 }
    ]},
    { "nodeid": 2, "depth": 1, "split": "f109", "split_condition": 0.8723473, "yes": 5, "no": 6, "missing": 5, "children": [
      { "nodeid": 5, "leaf": -1.94071 },
      { "nodeid": 6, "leaf": 1.85965 }
    ]}
  ]},
  { "nodeid": 0, "depth": 0, "split": "f60", "split_condition": -0.482947, "yes": 1, "no": 2, "missing": 1, "children": [
    { "nodeid": 1, "depth": 1, "split": "f29", "split_condition": -4.2387498, "yes": 3, "no": 4, "missing": 3, "children": [
      { "nodeid": 3, "leaf": 0.784718 },
      { "nodeid": 4, "leaf": -0.96853 }
    ]},
    { "nodeid": 2, "leaf": -6.23624 }
  ]}
]
```

## Importing XGBoost models

To import the XGBoost model to Vespa, add the directory containing the
model to your application package under a specific directory named `models`.
For instance, if you would like to call the model above as `my_model`, you
would add it to the application package resulting in a directory structure
like this:

```
├── models
│   └── my_model.json
├── searchdefinitions
│   └── main.sd
└── services.xml
```

An application package can have multiple models.

To download models during deployment, see [deploying remote models](deploying-remote-models.html).

## Ranking with XGBoost models

Vespa has a special [ranking feature](http://docs.vespa.ai/documentation/reference/rank-features.html)
called `xgboost`. This ranking feature specifies the model to use in a ranking expression.
Consider the following example:

```
search xgboost {
    rank-profile default inherits default {
        first-phase {
            expression: xgboost("my_model.json")
        }
    }
}
```

Here, we specify that the model `my_model.json` should be run.
The example XGBoost JSON model dump shown above would be converted
to the following ranking expression:

```
if (f29 < -0.1234567, if (f56 < -0.242398, 1.71218, -1.70044), if (f109 < 0.8723473, -1.94071, 1.85965)) +
if (f60 < -0.482947, if (f29 < -4.2387498, 0.784718, -0.96853), -6.23624)
```


