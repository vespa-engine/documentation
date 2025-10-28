---
# Copyright Vespa.ai. All rights reserved.
title: "Tensor Computation Examples"
---

Tensors can be used to express machine-learned models such as neural nets,
but they can be used for much more than that. The tensor model in Vespa is powerful,
since it supports sparse dimensions, dimension names and lambda computations.
Whatever you want to compute, it is probably possible to express it succinctly as a tensor expression - the problem
is learning how. This page collects some real-world examples of tensor usage to provide some inspiration.

## Tensor playground

The tensor playground is a tool to get familiar with and explore tensor algebra. It can be found
at [docs.vespa.ai/playground](https://docs.vespa.ai/playground/). Below are some examples
of common tensor compute operations using [tensor functions](reference/ranking-expressions.html#tensor-functions).
Feel free to play around with them to explore further:
* [Dense tensor dot product](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QGNIAaFDSPBdDTAF30gBEBTAOwGdmxa32sAnMABMstMDn5YhAVwK0AdGABiAS37sxAdy5Dm0Fay4BDbrwHswAAwCClsEdZCrAITtGLujlx4dzcSGSoAL6BQaQY1OS4DMwkgRAU+JE0kKwM1nE0mLEIkD58-AAUAB6IAMwAugCUcIgADMRgdfIAjI11FQFZIRhhgckJ0bmx4SmUaPGYabnOmVlQOVD5AiXl1bXNbc0ATMQdXTQ9waMQA1BDhHPk42cJ9LkAKgAW3ppYpr7qYE9GAG7eLzA7CMAFsdCowRwVFhWGBWKDmOxGnx7GAQdIADa0FQ4DEqAhGbEwsAqCzMDHMSG0AC0mlJzH8kyOED6EUm2HGkBG7JukwS0ygVxSi0g1jAACowLMmaEThMshyGEQ5QlefMlgxnjpROJJDI5CSLLRAexpCCLFh-oJjVwCFgQSDiUIIbxoaxGd1Zf12RcuULVUk+VABZB-dkGKaQYVrOLnFUDr1QigKiAgkA)* [Sparse tensor dot product](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QGNIAaFDSPBdDTAF30gGUcBDAJwGcBTMWrgOw5Y2YACZZaYHGyyiArgVoA6MADEAlp1rEwAdx6iu0dfx61dWMB1aczAoZzAADAIJOwLfqOcAhJyoAdfgA5CXUCMwALHgiAG1iOXkiWSWSANwEAckkAIy4BMSMTLm9xLkT+CTB0nhYwNJZYuS44SDJUAF92jtIManJcBi4SdogKfH6aSH4GFxGaTGGESD5BYQAKAA9gDoBKOGAARjgABiVDjraFrowe9smxweXh3qnKNFHMGeWfeYWoJZQVYOLY7fbAE6nc7EY5nABMl0+N06rwgDygT0If3I73RY3oywAkvwkjwALZyWK0dQ4WLhFLqLD8HRM2IAT1JYDJKQIkRMAHMwHEEh42DFGgRKSkSq0kd1UR8Fth3pAXp9xlRPmNvlBsVNAZAXGAAFRgX5y24K9HKhhEBVjXFaoEMAAq0TEVWksgUknUiVo7opVJpdIIDKZYGgWHiWH03hyHLqHDkZLAWAyIgDMSwZLJEdE6jJ9kZ-Fl13l93VmNVeodEyd0wYtcWDGTZPWLmNPh0m12VxoyIgdz6VZVdvVjv+zuWbr9YDnXAAjnJ1A1YgJJLQsGWBxWR0rq2qlZP-o3ls2xgaxfIIusAFZYEwdnTdyNbYhs3ZbY2f3Y6Nt9hanQoAAuiAHRAA)
  * [Vector-matrix product](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QGNIAaFDSPBdDTAF30gDUBTA2rAJwFoBbAQ1ocAlgA8wODlgAmAVzYA6MADEhHAM60wAd2ZgpzaEIB2uvmABurdhzAADRrbB8jUp2H6DRdgLK24kMlQAX0Cg0gxqclwGZhJAiAp8SJpIIwZGOJpMWIRIWmYjNU4AChFEAGYAXQBKOEQABnkAVmIwRpa25sqArJCMMMDkhOjc2PCUyjR4zDTc70ysqByofMKSggrK4jKq2sQG+XrWxoBGY-kAJi2kE8PW27OwW6vWxAu7sHfH96vu6b7guMIEMoCNCAtyJMQQl6LkAIIWKycXgCYRiCTSOSaIRqMC0AAWuh4MgANrQhDgSUICAIhFgjGAsNA8YTEWxOE4XO5UV5nK41DIeDxjABzRmWGwE3QELBC+l6IQ8ApqOlGfz-UJAqZZbCTSBjaaJKjTBKzKAQlLLSACnjFRhgABUYG8rRE1R6NABEAGEUNYMgRC1CShJpWDAAclh8iyBCzdJx9DYme5SeTKdTafKpFhmGojAByTQefIcRQASWxuKlCqVhVVeKwYBt4uYkvxseLrbU8g9-U1gz9eoNOpDiygZsgFvIVptxW8jrAjFd7o1-S1IN1DEDhtHizyDAAKqy+AAjLCWMA4sDMACOMiE5j4JIKmnY6t6-d9Ov9w4mSVDqQMFO2QMBwzCyAQzDFAAVlgxh2q0LpgNApTEAAntUpQLhh1StDay69sEoQoJUIBBEAA)
  * [Matrix multiplication](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QGNIAaFDSPBdDTAF30gFEAPAQwFscAbAUzC2hhWYdq1oAnAJbMAtKInSwOcVgAmAVwK0AdGABik8QGdaYAO59VPaJIB2fWmawixUgjyPEwAAwCC3oVtVHwAhb21IMlQAXyjo0gxqclwGHhIoiAp8JJpIWwZfdJpMNIRIWh5bIyxxAApmRAAmAF1iAE9EAGZmgEo4REQABm0ARmJhxvHtbuJEEdHiecn57ubI4tiMeKiczJSytITcyjQMzHyykKLiqFKoCqqa2o6ZgC8m3v6hxdahhfmRr8JottC01mdNjEjhBdlB9oRruQTrDMvQygAVAAWfGUak0pgELgU7iMPn8gWC3jC5kkXC4YExrAAbnxWHSwAQsOwAEZ2HjBVSSdiVIySLBVXRYvic9jscVgQXCqpi2w+NoBdjqEwAHVsjJZYFo2LARg4fFFrz4djA3KwRsNIpqpNq0BqCpFDkdxj66xokIg20SZ2wJ0gh2DyLOmQuUERuTukF8YAAVGArhC4tDTsUQwwiFnMpGbvcGFKiVJmCJ1FxaJJuJICGIVWBJKSjeb1Ox+CzxIbjTK5arFSLm951V5xB5q7XbABzFuq4TyCv8QQWvjeZjEV4BViknjMHA8LT8uC+raZnbB+FhuOF7JRqAxyB3koMIyd2pJ1MhLxtHrnjEl5BjmN75hGD7FuUpaYq2Lb7gAjuokhMmylSmLQWBnhmWxZrCuYHK+WRUI+eQMK+mQJpOGjuLUABWWB2F+xC-tA9TtD09TJv+PTEB+7AcYBAZxCgzQgNEQA)
  * [Tensor generation, dimension renaming and concatenation](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QGNIAaFDSPBdDTAF30gBUBTAOwGcsAnMAczeZcAhrQCWWVsTAATUQFs27cazBc2QuaNa8wQ1tLAEJBEerESAdGABioru1pgA7sxnNoW17SdYwtRdzsYAAUAG7MBLSBAJRgADqsAAYAgom6+mCJAEJpAK5K2rp+ATz8rIIiymDMAB44auxKEnCQZKgAvm3tpBjU5LgMzCRtEBT4fTSQrAzJwzSYQwiQ-hzcwaKIAMwAutHr0a3znRjdbROjA0tDPZOUaCOY00tZc-NQi1ArnFzriABMu3WAGpNgcHscOjcIOcoJdCK9yHcYaN6EsAOquEwqIysEwrUx+AAWzDkfiw-FoxJ4EiJmKwcjkNNkCg4yha4K6UPu82wd0g1weYyoD1GTygCMmH0gOLxwWSxCyxFEYKOnLOgrh0oloyRIs+DAASupNIVKa5mYoqolRGktGAsmTMgArRLs1UnLkw3mDbVQXVvKBiyAAYV9oylalYGmYwUVomITpVNAhEFOvQ1fKIXJ14z1ywYGMMekMxlMUf8mVS6QMiWDaRpzFEZp4FtZNOt9Z4iRdbuTavTPM1Ap5-reUwYYfeDBlIjlxGDSqTJ37qC9Q99Qu5Y6Dk-509LtDnC8Thz7y4g2xA7SAA)
  * [Jaccard similarity between mapped (sparse) tensors](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEMAXZgJwEsAjAV2YIAUAYxYEA5lk4EAzgEoSZGpCIJI-WtMkAeDrWYAOAHzCWwAL6y4wADqRpOSc2m2EARmJhbtAgHdn8d08YXUZaIQIXVzNIRQgzRTNSDGpyXAYiJKVKNFi6BgBHHgI2AE8TfgkpOQUaTBUodU02HT0jcvNLGzsHNicXMHdbaBCwiIDo3PiMRMUUzDTVDNyKfDnyelUAK0YhETYAEwB9LG9DgBtdJdqIZQZpHgBbAULispEKyQ4ZWTAAKjAWOxuHxBO9xJ9vrIAPRgARge5PB7FMSCF6lcrgqqyDyAzi8fgYypfOQeaACAAexBKsgErlk9LA8kmCRQAF0QGYgA)
  * [Neural network](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QGNIAaFDSPBdDTAF30gDkBTAVwCcBDAGzADtmtAO5Z2AazDMAHpwC2ObszAAKAMxSArFICMASgB0YAGIBLdgGdaYIUoAmzaCYFhaACyUDhoiU5ytacJBkqAC+wSGkGNTkuAzMJMEQFPjRNJB8DL7+CTSY8QiQtMx85qLKWbSIqgC6unCIAAz62sRgTS1tzdVBuWEYEcGpSbEFRJFplGiJdAwAKu581nYOTkpuSq4mtvaL3JwAnszsSyYA5q605mCcfLZgAEYmnOaB032h4xBDUCNQ8Z+YSbfJIZApCTbbYo5XJ-BhFEplCpVarECE7RAaWr1AA6iyQAFomgB2bQADgAnAAmYjafTk8naSmk4hNBoAFjZZOIhOapMpbNULP0DX59JRuIgjX0ADZSUTSRpubTpfyNMympTVNL6ULpRoiUS2UKNOS9aTxXjEPjaRoOdKjRryQ12ULtNLpdpFbTDdpVOr9KptALMbjum9wgDvthJpB-tNklRpiCGPc0VCAeR8lB4aV2Mo03wMVipUyRUShSL9YrWc6PULKR7tC0eW7pQ1yWHehHBvHfpAxvGgUns3MFkswPZHM51mApzwwHtDscbGcLlcbndHs9Xl3+pHezG47kE1MYVBQVAhHPuNDj1nCsVc-mtujMcRr4htMWJQTpfo+RospKjaGiUvK3KsoG5Llqo+gaPqDYQQG0pEqoRLVKGPQ0O8EADFEB5xLegIpMO6QpteRGZnCj5lB+X51FKDR6kSbadth3b4cefYDseQ5noUDCmBYViLkc1wELQJgAG6cJJWB8K0rDmE4pzXGAAAG7DMNwrDqeJkkyXJizQKwfASSY8n6Fh-QcagUZ9keEwkfxF6QJReQMOYrCyOUfB+FYABU1gFq0FS6GAADUDwFtZoS2V8BEFI55B8TCZEFKJ7DaO5ST3lpOnKF5PkVGAQXgi+xShX5-jhVFqYVXwuixbh8Wnmk3HuSewIjgUACiACOrDSTwxS0Nw+yKcpfCqTO6lSEIAD6ChKQt9x6SZfBGTu7F7j2XGHp1qXHq5PBFOwfCydJzALZl2UZh5BT5awyjzUtOnmKtvn+a05WQgp0UNVV-m6E14a7Zx7UxjxTmJvx9AFKYF28Jl+nDUZk0qWpymnLIWBbKjhkWcZplbc1YA4eT+77YR91daRrk5bCBRFcot2ldY16tAWtUPBRYMfHtkM04Ozlpa5mWUozsaeWcuNbIV3mswcRzaOzV5ODwXMNTz9zXqDu4CxDMRQ4dovHvDUCI-OXB8BI5gEKIzDbTZ4N2YlsK00daQM-duWeYrEv6ztcUQNUIAhEAA)

## Values that depend on the current time

In an ecommerce application you may have promotions that sets a different product price in given
time intervals. Since the price is used for ranking, the correct price must be computed in ranking.
Can tensors be used to specify prices in arbitrary time intervals in documents and pick the right price
during ranking?

To do this, add three tensors to the document type as follows:

```
field startTime type tensor(id{}} {
    indexing: attribute
}
field endTime type tensor(id{}} {
    indexing: attribute
}
field price type tensor(id{}} {
    indexing: attribute
}
```

Here the id is an arbitrary label for the promotion which must be unique within the document, and
startTime and endTime are epoch timestamps.

Now documents can include promotions as follows
([document JSON syntax](reference/document-json-format.html)):

```
"startTime": { "cells": { "promo1": 40, "promo2": 60, "promo3": 80 }
"endTime":   { "cells": { "promo1": 50, "promo2": 70, "promo3": 90 }
"price":     { "cells": { "promo1": 16, "promo2": 18, "promo3": 10 }
```

And we can retrieve the currently valid price by the expression

```
reduce((attribute(startTime) < now) * (attribute(endTime) > now) * attribute(price), max)
```

This will return 0 if there is no matching interval, so a full expression will probably
wrap this in a function and check if it returns 0 (using an if expression) and return the
default price of that product otherwise.

To see why this retrieves the right price, notice that `(attribute(startTime) < now)`
[is a shorthand for](reference/ranking-expressions.html#non-primitive-functions)

```
join(attribute(startTime), now, f(x,y)(x < y))
```

That is joining all the cells of the `startTime` tensor by the zero-dimensional `now`
tensor (i.e a number), and setting the cell value in the joined tensor to 1 if now is larger than the cell
timestamp and 0 otherwise.
When this tensor is joined by multiplication with one that has 1's only where now is smaller,
the result is a tensor with 1's for promotion ids whose interval is currently valid and 0 otherwise.
Then we can just join by multiplication with the price tensor to get the final tensor (on which we just pick the
max value to retrieve the non-zero value.

[Play around with this example in the playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gGcAXAQwCdmAVASwFsipGpiIJIzArUZZ2ACh4ATYAF8AlHGA52WPlgCMCACwAGYmC06sAJgQA2U+e26AzAgAcx5ZDKplP5UKo1OS4DII+EBT4wTSQ9GKSCrwCJBEiDBJSMvJKahoWugZgAKwOBdYIAOxlTliuYACcnt7CfhgBPjGRoQmpwlFUaZHxUFo8AMbhwpGiUJnScooq6pq1RXq2ZuU2YHpuW7X1es1pbb6BEF1QPYR9sZRoQ1AjcVgA7nf9s5C2xS00ZwgHQwV2wD0gU3u0SecQYn1i3xYHG4-AIYAAPGBaO9-u1-BdHv0bhD4ZEHldhnCCeRvolkmiAHxYnGnfGdNJgsKk0bQ6bPKkw76yJGcekY5lvVRgABUYFkdNRYCZ2MluN8bJBHOJkPI5JhL25MwYwrYosVmJVUtl8toSUVyveVscEyIrPaBNB2u5A0J01hYkNtzE7AICgArpNZCbkWKLY6ZXKFQIlRKnWNJmY+KwAB6qNVA-woAC6IGUQA)

## Adding scalars to a tensor

A common situation is that you have dense embedding vectors to which you want to add some scalar attributes
(or function return values) as input to a machine-learned model. This can be done by the following expression
(assuming the dense vector dimension is named "x":

```
concat(concat(query(embedding),attribute(embedding),x), tensor(x[2]):[bm25(title),attribute(popularity)], x)
```

This creates a tensor from a set of scalar expressions, and concatenates it to the query and document embedding vectors.

[Play around with this example in the playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEMAXZgJwEsAjAV2YIAUBALZcCAE3EdaAcwCUJMjUhEEkfrQDOWNgIAeiAEwBdOXEQBGYichKIAXyX3SGauVwMiL5ZTR26DACOPARsAJ5CohJSsgreNIQMGtq6BiZmiADMAHQADMRgACx5xrYJjhjOSm6YHmpe-hT4NeT0alzChgCsAswczAA2BHH+ECoMhsWZZTQVqFWujXWJ8Zi+LQFqLOzcfII4uDwDjJzMYSMJY6pQXTOVTqsb2L7jq2Pro1BtUIqXiWoAYywtABLAEQJBYOCoQiIjEkmk8mI204vH4kXhMSRejkBWSOn0RlM5g63V6-SGuJRu3RBxwRxO-XOxgKOLu8ycKGMIHsQA)

## Dot Product between query and document vectors

Assume we have a set of documents where each document contains a vector of size 4.
We want to calculate the dot product between the document vectors and a vector passed down with the query
and rank the results according to the dot product score.

The following schema file defines an attribute tensor field
with a tensor type that has one indexed dimension `x` of size 4.
In addition, we define a rank profile with the input and the dot product calculation:

```
schema example {
    document example {
        field document_vector type tensor<float>(x[4]) {
            indexing: attribute | summary
        }
    }
    rank-profile dot_product {
        inputs {
            query(query_vector) tensor<float>(x[4])
        }
        first-phase {
            expression: sum(query(query_vector)*attribute(document_vector))
        }
    }
}
```

Example [JSON](reference/document-json-format.html#tensor) document with the
vector [1.0, 2.0, 3.0, 5.0], using indexed tensors short form:

```
[
    {
        "put": "id:example:example::0",
        "fields": {
            "document_vector" : [1.0, 2.0, 3.0, 5.0]
        }
    }
]
```

Example query set in a searcher with the vector [1.0, 2.0, 3.0, 5.0]:

```
public Result search(Query query, Execution execution) {
    query.getRanking().getFeatures().put("query(query_vector)",
        Tensor.Builder.of(TensorType.fromSpec("tensor<float>(x[4])")).
        cell().label("x", 0).value(1.0).
        cell().label("x", 1).value(2.0).
        cell().label("x", 2).value(3.0).
        cell().label("x", 3).value(5.0).build());
    return execution.search(query);
}
```

[Play around with this example in the playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKF9jgfQBuBAMYAXLGwCUJMjUhEEkMQVoBnSVwAeiACwBdKXEQBGYgCZiAZmIBWfZDkQAvnOekM1crgZEP8yjQnOgYAQzExNgBLACNmFS4AEywRZgBbVTEhUQlpWRpMRSgVdU0dAyNTC2s7B2DXDHc5L0wfJT9ginwW8nolfILCBjV0nlZOMb5s8UkpMAAqMHDI2PiCJJT0zOncqRl6txR9EGcgA)

Note that this example calculates the dot product for every document retrieved by the query. Consider
using [approximate nearest neighbor](approximate-nn-hnsw.html) search with
`distance-metric` [dotproduct](reference/schema-reference.html#distance-metric).

## Logistic regression models with cross features

One simple way to use machine-learning is to generate cross features from a set of base features
and then do a logistic regression on these. How can this be expressed as Vespa tensors?

Assume we have three base features:

```
query(interests): tensor(interest{}) - A sparse, weighted set of the interests of a user.
query(location): tensor(location{})  - A sparse set of the location(s) of the user.
attribute(topics): tensor(topic{})   - A sparse, weighted set of the topics of a given document.
```

From these we have generated all 3d combinations of these features and trained a logistic regression model,
leading to a weight for each possible combination:

```
tensor(interest{}, location{}, topic{})
```

This weight tensor can be added as a
[constant tensor](reference/schema-reference.html#constant)
to the application package, say `constant(model)`. With that we can compute the model
in a rank profile by the expression

```
sum(query(interests) * query(location) * attribute(topics) * constant(model))
```

Where the first three factors generates the 3d cross feature tensor and the last combines
them with the learned weights.

[Play around with this example in the playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKAS1oBd2BAM79hAShJkakIgkiDawrG14Cho4AF9xcYAGMAhm2FwADADoAHMTABbZsJ77zFgKxbI0iFulbSGNTkuAxEATKUaN50DCzs3AA2WEb8PFi0kuE0hAyKyqpJKWm02rrAtAQA7gD6HCoA1nAAjJ7Rvhj+0kGYIfJh0RT43eT08ob8-Gw8AEbMglz8uM4SUtkQsrkESioLS-qlek0ATADMzRZmrdntqJ2BA705WZiRwzHy+umihgJcdlgAEwICUy0XWcigeR2fEEbBE-G0xEK42KiMWOGcBzQAB1aBBgDCNPw4EYTEjkij0nAKjU6mx6sR0c5mqctK4msRcfjCXDRCTjMJyUUqTTag1GXs4CcACweVxHTl4tA8+H8snI1JU4Q-arQNg-fQ8YSfCUYlzHE5sywnRXc9S84mkwUa4pwbW0XX62iG41YU3MmVyyzS23K+2qhxOfRCym0alVMX0-3m1muNyhgnhvmR5wxzVx0V0hlMlyBq0WABsGZV2ccuZdWp1eoNRpNJZZltcVa5YdhEbr0YbcfdnpbvuTUtl5YA7NWs8TplgsPVnRT8-HaeL2xbyzYe5m+3zF8vV8KCwmixOy64AJxzw8LpcrvOukfN72tv3b1NNC73olwMez5Dm6TZej6baStev5NLiVw0DcPjPG82CRBszzrK8YJQKMUCrGsGzyMIzB2FwcScGoD4SGAABUYDkYka7FOItFgOMkwzHMBC7Ga1F0Z8Sj8D8-B-ICwLiJIbR+CgAC6IBaEAA)

## Matrix Product between 1d vector and 2d matrix

Assume we have a 3x2 matrix represented in an attribute tensor field `document_matrix`
with a tensor type `tensor<float>(x[3],y[2])` with content:

```
{ {x:0,y:0}:1.0, {x:1,y:0}:3.0, {x:2,y:0}:5.0, {x:0,y:1}:7.0, {x:1,y:1}:11.0, {x:2,y:1}:13.0 }
```

Also assume we have 1x3 vector passed down with the query as a tensor
with type `tensor<float>(x[3])` with content:

```
{ {x:0}:1.0, {x:1}:3.0, {x:2}:5.0 }
```

that is set as `query(query_vector)` in a searcher
as specified in [query feature](ranking-expressions-features.html#using-query-variables).

To calculate the matrix product between the 1x3 vector and 3x2 matrix (to get a 1x2 vector)
use the following ranking expression:

```
sum(query(query_vector) * attribute(document_matrix),x)
```

This is a sparse tensor product over the shared dimension `x`,
followed by a sum over the same dimension.

[Play around with this example in the playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEMAXZgJwEsAjAV2YIAUAEywBjHgFsCtZgH0JLTgA8AlCTI1IRBJH60AzljYAeaABssLAHwCliAMwBdYgE9EAJkcq4iRAEZiAHZnB2I-PxCAVjCnR0gNCABfDUTSDGpyXAYiNM1KNAS6BgBHHgI2FwFS8pdZADcCUWYjNVyaQgY9QxNzS2YbOydvf2J7Yki4wuSMVI0MzCydHMKKfHnyeh11dogtBn1JKrKKo5r6xua2FTAAKjAWdm4+QRFxKRl5RQ5VYlV49umqEBjhAiSAA)

## Using a tensor as a lookup structure

Tensors with mapped dimensions look similar to maps, but are more general.
What if all needed is a simple map lookup?
See [tensor performance](performance/feature-tuning.html#mapped-lookups) for more details.

Assume a tensor attribute `my_map` and this is the value for a specific document:

```
tensor<float>(x{},y[3]):{a:[1,2,3],b:[4,5,6],c:[7,8,9]}
```

To create a query to select which of the 3 named vectors (a,b,c) to use for some other calculation,
wrap the wanted label to look up inside a tensor.
Assume a query tensor `my_key` with type/value:

```
tensor<float>(x{}):{b:1.0}
```

Do the lookup, returning a tensor of type `tensor<float>(y[3])`:

```
sum(query(my_key)*attribute(my_map),x)
```

If the key does not match anything, the result will be empty: `tensor<float>(y[3]):[0,0,0]`.
For something else, add a check up-front to check if the lookup will be successful
and run a fallback expression if it is not, like:

```
if(reduce(query(my_key)*attribute(my_map),count) == 3,
  reduce(query(my_key)*attribute(my_map),sum,x),
  tensor<float>(y[3]):[0.5,0.5,0.5])
```

{% include note.html content='The above can be considered the same as creating a
[slice](reference/ranking-expressions.html#slice), like `(y*x){x:b}`.
The above syntax allows an optimized execution, find an example in the
[Tensor Playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gFssATAgGwGcSybIiEkAC4FanLACcAFIwD6ASxbAAvsQAeiAMwBdAJRxgjAIxxEAFgB0ABmJgArNdsA2a9tuMATKYDsjsAA4-AE5XZUheCGVeVV5qclwGIlIaKEo0CLoGZjZ2BRYeFIh+BhExSRk8lX1DLyNrMIyojBiMOMwEwSSMinw28npBRgBDHBwCFll2LCwAawBXPGTC4sFOOcYZVg5OACpsjjziOUVdcJSm1BbUPqgOwgK+NJuigahOdnkAYy7C+8FNnK7fa5E6GPJwTwNc7RFDaEDKIA).' %}

## Slicing with lambda

A common use case is to use a tensor lambda function to slice out the first `k` dimensions of a vector representation of `m`
dimensions where `m` is larger than `k`.
Slicing with lambda functions is great for representing vectors from [Matryoshka Representation Learning](https://arxiv.org/abs/2205.13147).

> Matryoshka Representation Learning (MRL) which encodes information at different granularities and allows a single embedding to adapt to the computational constraints of downstream tasks.

The following slices the first 256 dimensions of a tensor `t`:

```
  tensor<float>(x[256])(t{x:(x)})
```

Importantly, this does only reference into the original tensor, avoiding copying the tensor to a smaller tensor.

The following is a complete example where we have stored an original vector representation with 3072 dimensions, And
we slice the first 256 dimensions of the original representation to perform a dot product in the first-phase expression,
followed by a full computation over all dimensions in the second-phase expression. See [phased ranking](phased-ranking.html)
for context on using Vespa phased computations and [customizing reusable frozen embeddings with Vespa](https://blog.vespa.ai/tailoring-frozen-embeddings-with-vespa/).

```
{% raw %}
schema example {
  document example {
    field document_vector type tensor<float>(x[3072]) {
      indexing: attribute | summary
    }
  }
  rank-profile small-256-first-phase {
    inputs {
      query(query_vector) tensor<float>(x[3072])
    }
    function slice_first_dims(t) {
      expression: l2_normalize(tensor<float>(x[256])(t{x:(x)}), x)
    }
    first-phase {
      expression: sum( slice_first_dims(query(query_vector)) * slice_first_dims(attribute(document_vector)) )
    }
    second-phase {
      expression: sum( query(query_vector) * attribute(document_vector) )
    }
  }
}
{% endraw %}
```

See also a runnable example in this
[tensor playground example](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gFsBPAfQAsBLAc3dYBNOjVgDcCAYwAuWAE4kyNSEQSRJBWgGdZAHmgAbLAENJAPgAUAD0QBGAEwBdAJRwbxW8QDMxACzEArMQAbMQA7MQAHMQAnMTWAAyx1rEOkAoQAL4K6aQY1OS4DEQ5ipRoaXQM0JwyGpKsgQJCGqxY0KwsHDx8gsJiUrLyNJjKUGqaspaIgU5mHVy8jb0S0jLAFnCWjumOqUOZGNkKeZgFKkXlFPjH5PQqtLKMhnqcAF7nQxBKDHq2rPcyj2ebzMVRqdQaPWarXabHm3SEomWsmIYAsO3K+1QmPsIHSQA).
