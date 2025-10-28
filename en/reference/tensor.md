---
# Copyright Vespa.ai. All rights reserved.
title: "Tensor Reference"
---

A tensor is a set of named *dimensions* defining its *order*
and a set of values located in the space of those dimensions:
* *Cell*: A value located in the dimension space.
  Consists of a cell address and the value at that address.
* *Address*: A set of key-values
  where each key is a *dimension* from the set of dimensions of the tensor,
  and each value is a *label* (integer or string) determining the cell's location in that dimension.

The set of dimensions, cell values and cell address key-values can be of any size including zero.
A dimension can be either mapped or indexed.
Mapped dimensions use string identifiers as labels in the cell addresses (like a map),
while indexed dimensions use integers in the range `[0,N>` (like an array),
where N is the size of the dimension.

## Tensor type spec

Contained in [constant](schema-reference.html#constant)
or [tensor field type](schema-reference.html#tensor).
The dimensions of a tensor and the cell type defines its type.
A tensor type contains a list of dimensions on the format:

```
tensor<value-type>(dimension-1,dimension-2,...,dimension-N)
```

The value-type is one of:

| Type | Description |
| --- | --- |
| float | 32-bit IEEE 754 floating point |
| double | 64-bit IEEE 754 floating point |
| int8 | signed 8-bit integer - see [performance considerations](../performance/feature-tuning.html#cell-value-types) |
| bfloat16 | first 16 bits of 32-bit IEEE 754 floating point - see [performance considerations](../performance/feature-tuning.html#cell-value-types) |

A dimension is specified as follows:
* `dimension-name{}` - a mapped dimension
* `dimension-name[size]` - an indexed dimension

The tensor type for a tensor<float> with two mapped dimensions *x* and *y* looks like:

```
tensor<float>(x{},y{})
```

Example tensor with this type:

```
{% raw %}
{{x:a,y:b}:10.0, {x:c,y:d}:20.1}
{% endraw %}
```

The tensor type for a tensor<float> with two indexed dimensions *x* and *y*
with sizes 3 and 2 respectively looks like:

```
tensor<float>(x[3],y[2])
```

Example tensor with this type (representing a matrix):

```
{% raw %}
{{x:0,y:0}:1, {x:0,y:1}:2.1,
 {x:1,y:0}:3, {x:1,y:1}:5,
 {x:2,y:0}:7, {x:2,y:1}:11}
{% endraw %}
```

Note that the labels are indexes in the range *[0,dimension-size>*

A tensor<double> with both mapped and indexed dimensions is *mixed*:

```
tensor<double>(key{},x[2])
```

Example:

```
{% raw %}
{{key:a,x:0}:10,  {key:b,x:0}:2.7,
 {key:a,x:1}:5.3, {key:b,x:1}:-7  }
{% endraw %}
```

## Tensor literal form

The tensor literal form is used in:
* Tensors in queries,
  see [defining query feature types](../ranking-expressions-features.html#query-feature-types)
  and [tensor user guide](../tensor-user-guide.html#querying-with-tensors)
* Constant tensors in [stateless model evaluation](stateless-model-reference.html)
* Building tensors using the
  [Java Tensor API](https://javadoc.io/doc/com.yahoo.vespa/vespajlib/latest/com/yahoo/tensor/Tensor.html)

The tensor literal form is *not* a JSON format.
When sent inside a JSON format (like when you POST a query),
it should be passed as a string.

### General literal form

The general literal form is verbose and explicit,
can represent any tensor and is as follows (EBNF):

```
literal tensor = ( tensor-type-spec ":" )? "{" cells "}" ;
cells = | cell , { "," cell } ;
cell = "{" address "}:" scalar ;
address = | element, { "," element } ;
element = dimension ":" label ;
dimension = integer | identifier ;
label = integer | identifier | 'string' | "string" ;
identifier = ["A"-"Z","a"-"z","0"-"9","_","@"](["A"-"Z","a"-"z","0"-"9","_","@","$"])*
```

For query inputs, the type should be declared as an input in the ranking profile,
so the type spec is usually skipped.

#### General literal form examples:

An empty tensor:

```
{}
```

A single value tensor with a single mapped dimension *x*:

```
{ {x:foo}:5.0 }
```

A tensor with multiple values and mapped dimensions *x* and *y*:

```
{ {x:foo, y:bar}:5.0, {x:foo, y:baz}:7.0 }
```

A tensor where type is specified explicitly with a single indexed dimension *x* representing a vector:

```
tensor<float>(x[3]):{ {x:0}:3.0, {x:1}:5.0, {x:2}:7.0 }
```

A tensor with a type using the default value type (double) and quoted labels:

```
tensor(key{}):{ {key:'key.1'}:3.0, {key:'key 2'}:5.0, {key:"key's"}:7.0 }
```

### Indexed short form

Tensors where all dimensions are indexed can be written as numbers wrapped in square brackets in
*right dimension adjacent* order. If the type isn't declared already, this form requires
an explicit tensor type. Note: Dimensions should be alphabetically ordered.

Brackets must be nested according to the structure of the
type, where values in dimensions to the right are closer than
dimensions on the left. For backwards compatibility (not supported
in expressions), cell values may also be given in the same order
as a flat array.

#### Indexed short form examples:

A float 1d tensor in indexed form:

```
tensor<float>(x[3]):[3.0, 5.0, 7.0]
```

A matrix in indexed form. Since the values for the right-most dimension (y) are adjacent,
the value 3 is here assigned to the cell {x:0,y:2}:

```
tensor<float>(x[2],y[3]):[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
```

Deprecated:
Since inner brackets can be omitted, the above is equivalent to

```
tensor<float>(x[2],y[3]):[1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
```

### Binary hex format

Tensors representing binary data (indexed tensors with `int8`
cell value type) may be represented using a hexadecimal representation,
similar to the corresponding
[JSON tensor feed format](document-json-format.html#tensor-hex-dump).
If the tensor type is declared as
`tensor<int8>(x[2],y[3])` input could be just

```
0B22038405FF
```

which would be equivalent to:

```
[[11, 34, 3], [-124, 5, -1]]
```

### Mapped short form

Tensors with a single mapped dimension can be written by specifying
just the label in that implicit dimension instead of a full address map.
This form requires a type to be declared or explicitly specified.

#### Map short form example:

```
tensor<float>(key{}):{ key1:1.0, key2:2.0 }
```

### Mixed short form

Tensors with a single mapped dimension and one or more indexed dimensions
can be written by specifying the mapped dimension in the map short form
and the values of each dense subspace on the indexed short form.
This form requires a type to be known (declared) or specified.

#### Mixed short form example:

A map of matrices:

```
tensor<float>(key{},x[2],y[3]):{ key1:[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
                                 key2:[[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]] }
```

This may even be combined with a hexadecimal format for the dense subspace:

```
tensor<int8>(key{},x[5]):{ key1: 0102030405, key2: fffefdfcfb }
```

Tensors with a multiple mapped dimensions may use an extended
variant of the mixed short form, where labels are nested.
Again note that the type should be declared with dimensions
in alphabetic order, so the nesting will follow a consistent
ordering.

```
tensor(category{},key{},x[2],y[3]):{
   cat1:{key1:[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]],
         key2:[[1.1, 2.1, 3.1], [4.1, 5.1, 6.1]]},
   cat2:{key1:[[7.3, 8.3, 9.3], [7.0, 8.0, 9.0]],
         key3:[[7.5, 8.5, 9.5], [7.9, 8.9, 9.9]]}
}
```

the equivalent fully-specified literal form would be

```
{% raw %}
tensor(category{},key{},x[2],y[3]):{{category:cat1, key:key1, x:0, y:0}: 1.0,
                                    {category:cat1, key:key1, x:0, y:1}: 2.0,
                                    {category:cat1, key:key1, x:0, y:2}: 3.0,
                                    {category:cat1, key:key1, x:1, y:0}: 4.0,
                                    {category:cat1, key:key1, x:1, y:1}: 5.0,
                                    {category:cat1, key:key1, x:1, y:2}: 6.0,
                                    {category:cat1, key:key2, x:0, y:0}: 1.1,
                                    {category:cat1, key:key2, x:0, y:1}: 2.1,
                                    {category:cat1, key:key2, x:0, y:2}: 3.1,
                                    {category:cat1, key:key2, x:1, y:0}: 4.1,
                                    {category:cat1, key:key2, x:1, y:1}: 5.1,
                                    {category:cat1, key:key2, x:1, y:2}: 6.1,
                                    {category:cat2, key:key1, x:0, y:0}: 7.3,
                                    {category:cat2, key:key1, x:0, y:1}: 8.3,
                                    {category:cat2, key:key1, x:0, y:2}: 9.3,
                                    {category:cat2, key:key1, x:1, y:0}: 7.0,
                                    {category:cat2, key:key1, x:1, y:1}: 8.0,
                                    {category:cat2, key:key1, x:1, y:2}: 9.0,
                                    {category:cat2, key:key3, x:0, y:0}: 7.5,
                                    {category:cat2, key:key3, x:0, y:1}: 8.5,
                                    {category:cat2, key:key3, x:0, y:2}: 9.5,
                                    {category:cat2, key:key3, x:1, y:0}: 7.9,
                                    {category:cat2, key:key3, x:1, y:1}: 8.9,
                                    {category:cat2, key:key3, x:1, y:2}: 9.9}
{% endraw %}
```

## Tensor functions

Tensor functions are listed in the [expressions](ranking-expressions.html#tensor-functions) documentation.

## Tensor rank features

The following rank features can be used to refer to or create tensors in ranking expressions.
The tensors can come from the document, the query or a constant in the application package:
* [attribute(tensor_attribute)](rank-features.html#attribute(name))
* [query(tensor_feature)](rank-features.html#query(value))
* [constant(tensor_constant)](rank-features.html#constant(name))
* [tensorFromWeightedSet(source, dimension)](rank-features.html#tensorFromWeightedSet(source,dimension))
* [tensorFromLabels(source, dimension)](rank-features.html#tensorFromLabels(source,dimension))

Use the following reference documentation on how use tensors in documents:
* [Tensor field in schema](schema-reference.html#tensor)
* [Document JSON Format](document-json-format.html)
