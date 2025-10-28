---
# Copyright Vespa.ai. All rights reserved.
title: "Constant Tensor JSON Format"
---

This document describes with examples the JSON formats accepted when reading tensor constants from a file.
For convenience, compactness, and readability there are various formats that can be used depending on the detailed tensor type:
* [Dense tensors](#dense-tensors): indexed dimensions only
* [Sparse tensors](#sparse-tensors): mapped dimensions only
* [Mixed tensors](#mixed-tensors): both indexed and mapped dimensions

## Canonical type

A tensor type can be declared with its dimension in any order, but
internally they will always be sorted in alphabetical order.
So the type "`tensor(category{}, brand{}, a[3], x[768], d0[1])`" has
the canonical string representation "`tensor(a[3],brand{},category{},d0[1],x[768])`"
and the "x" dimension with size 768 is the innermost.
For constants, all indexed dimensions must have a known size.

## Dense tensors

Tensors using only indexed dimensions are used for storing a vector,
a matrix, and so on and are collectively known as "dense" tensors.
These are particularly easy to handle, as they always have a known
number of cells in a well-defined order.
They can be input as nested arrays of numerical values.
Example with vector of size 5:

```
  {
      "type": "tensor(x[5])",
      "values": [ 13.25, -22, 0.4242, 0, -17.0 ]
  }
```

The "type" field is optional, but must match the
[canonical form of the tensor type](#canonical-type)
if present. This format is similar to "Indexed tensors short form" in the
[document JSON format](document-json-format.html#tensor-short-form-indexed).

Example of a 3x4 matrix; note that the dimension names will
always be processed in
[alphabetical order](#canonical-type)
from outermost to innermost.

```
  {
      "type": "tensor(bar[3],foo[4])",
      "values": [
            [ 2.5, 1.0, 2.0, 3.0 ],
            [ 1.0, 2.0, 3.0, 2.0 ],
            [ 2.0, 3.0, 2.0, 1.5 ]
      ]
  }
```

Note that the arrays must have exactly the declared number of
elements for each dimension, and be correctly nested.

Example of an ONNX model input where we have an extra "batch" dimension
which is unused (size 1) for this particular input, but still requires
extra brackets:

```
  {
      "type": "tensor(d0[1],d1[5],d2[2])",
      "values": [ [
          [ 1.1, 1.2 ],
          [ 2.1, 2.2 ],
          [ 3.1, 3.2 ],
          [ 4.1, 4.2 ],
          [ 5.1, 5.2 ]
      ] ]
  }
```

## Sparse tensors

Tensors using only mapped dimensions are collectively known as "sparse" tensors.
JSON input for these will list the cells directly.
Tensors with only one mapped dimension can use as simple JSON object as input:

```
  {
      "type": "tensor(category{})",
      "cells": {
          "tag": 2.5,
          "another": 2.75
      }
  }
```

The "type" field is optional.
This format is similar to "Short form for tensors with a single mapped dimension"
in the [document JSON format](document-json-format.html#tensor-short-form-mapped).

Tensors with multiple mapped dimensions must use an array of objects,
where each object has an "address" containing the labels for all
dimensions, and a "value" with the cell value:

```
  {
      "type": "tensor(category{},product{})",
      "cells": [
          {
              "address": { "category": "foo", "product": "bar" },
              "value": 1.5
          },
          {
              "address": { "category": "qux", "product": "zap" },
              "value": 3.5
          },
          {
              "address": { "category": "pop", "product": "rip" },
              "value": 6.5
          }
      ]
  }
```

Again, the "type" field is optional, but must match the
[canonical form of the tensor type](#canonical-type)
if present.

This format is also known as the
[general verbose form](document-json-format.html#tensor),
and it's possible to use it for any tensor type.

## Mixed tensors

Tensors with both mapped and indexed dimensions can use
a "blocks" format; this is similar to the "cells" formats for sparse tensors,
but instead of a single cell value you get a block of
values for each address.
With one mapped dimension and two indexed dimensions:

```
  {
      "type": "tensor(a{},x[3],y[4])",
      "blocks": {
          "bar": [
              [ 1.0, 2.0, 0.0, 3.0 ],
              [ 2.0, 2.5, 2.0, 0.5 ],
              [ 3.0, 6.0, 9.0, 9.0 ]
          ],
          "foo": [
              [ 1.0, 0.0, 2.0, 3.0 ],
              [ 2.0, 2.5, 2.0, 0.5 ],
              [ 3.0, 3.0, 6.0, 9.0 ]
          ]
      }
  }
```

The "type" field is optional, but must match the
[canonical form of the tensor type](#canonical-type)
if present.
This format is similar to the first variant of "Mixed tensors short form"
in the [document JSON format](document-json-format.html#tensor-short-form-mixed).

With two mapped dimensions and one indexed dimensions:

```
  {
      "type": "tensor(a{},b{},x[3])",
      "blocks": [
          {
              "address": { "a": "qux", "b": "zap" },
              "values": [ 2.5, 3.5, 4.5 ]
          },
          {
              "address": { "a": "foo", "b": "bar" },
              "values": [ 1.5, 2.5, 3.5 ]
          },
          {
              "address": { "a": "pop", "b": "rip" },
              "values": [ 3.5, 4.5, 5.5 ]
          }
      ]
  }
```

Again, the "type" field is optional.
This format is similar to the second variant of "Mixed tensors short form"
in the [document JSON format](document-json-format.html#tensor-short-form-mixed).
