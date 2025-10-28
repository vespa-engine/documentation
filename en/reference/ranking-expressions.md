---
# Copyright Vespa.ai. All rights reserved.
title: "Ranking Expressions"
---

This is a complete reference to the *ranking expressions*
used to configure application specific ranking functions.
For examples and an overview of how to use ranking expressions,
see the [ranking overview](../ranking.html).

Ranking expressions are written in a simple language similar to ordinary functional notation.
The atoms in ranking expressions are *rank features* and *constants*.
These atoms can be combined by *arithmetic operations* and other
*built-in functions* over scalars and tensor.

| Rank Features | A rank feature is a named value calculated or looked up by vespa for each query/document combination. See the [rank feature reference](rank-features.html) for a list of all the rank features available to ranking expressions. |
| Constants | A constant is either a floating point number, a boolean (true/false) or a quoted string. Since ranking expressions can only work on scalars and tensors, strings and booleans are immediately converted to scalars - true becomes 1.0, false 0.0 and a string its hash value. This means that **strings can only be used for equality comparisons**, other purposes such as parametrizing the key to slice out of a tensor will not work correctly. |

## Arithmetic operations

Basic mathematical operations are expressed in in-fix notation:

```
a + b * c
```

Arithmetic operations work on any tensor in addition to scalars, and are a short form
of joining the tensors with the arithmetic operation used to join the cells.
For example `tensorA * tensorB` is the same as `join(tensorA, tensorB, f(a,b)(a * b))`.

All arithmetic operators in order of decreasing precedence:

| Arithmetic operator | Description |
| --- | --- |
| ^ | Power |
| % | Modulo |
| / | Division |
| * | Multiplication |
| - | Subtraction |
| + | Addition |
| && | And: 1 if both arguments are non-zero, 0 otherwise. |
| || | Or: 1 if either argument is non-zero, 0 otherwise. |

## Mathematical scalar functions

| Function | Description |
| --- | --- |
| acos(*x*) | Inverse cosine of *x* |
| asin(*x*) | Inverse sine of *x* |
| atan(*x*) | Inverse tangent of *x* |
| atan2(*y*, *x*) | Inverse tangent of *y / x*, using signs of both arguments to determine correct quadrant. |
| bit(*x*, *y*) | Returns value of bit *y* in value *x* (for int8 values) |
| ceil(*x*) | Lowest integral value not less than *x* |
| cos(*x*) | Cosine of *x* |
| cosh(*x*) | Hyperbolic cosine of *x* |
| elu(*x*) | The Exponential Linear Unit activation function for value *x* |
| erf(*x*) | The Gauss error function for value *x* |
| exp(*x*) | Base-e exponential function. |
| fabs(*x*) | Absolute value of (floating-point) number *x* |
| floor(*x*) | Largest integral value not greater than *x* |
| fmod(*x*, *y*) | Remainder of *x / y* |
| isNan(*x*) | Returns 1.0 if *x* is NaN, 0.0 otherwise |
| ldexp(*x*, *exp*) | Multiply *x* by 2 to the power of *exp* |
| log(*x*) | Base-e logarithm of *x* |
| log10(*x*) | Base-10 logarithm of *x* |
| max(*x*, *y*) | Larger of *x* and *y* |
| min(*x*, *y*) | Smaller of *x* and *y* |
| pow(*x*, *y*) | Return *x* raised to the power of *y* |
| relu(*x*) | The Rectified Linear Unit activation function for value *x* |
| sigmoid(*x*) | The sigmoid (logistic) activation function for value *x* |
| sin(*x*) | Sine of *x* |
| sinh(*x*) | Hyperbolic sine of *x* |
| sqrt(*x*) | Square root of *x* |
| tan(*x*) | Tangent of *x* |
| tanh(*x*) | Hyperbolic tangent of *x* |
| hamming(*x*, *y*) | Hamming (bit-wise) distance between *x* and *y* (considered as 8-bit integers). |

`x` and `y` may be any ranking expression.

## The if function

The `if` function chooses between two sub-expressions based on the truth value of a condition.

```
if (expression1 operator expression2, trueExpression, falseExpression)
```

If the condition given in the first argument is true,
the expression in argument 2 is used, otherwise argument 3.
The four expressions may be any ranking expression.
Conditional operators in ranking expression if functions:

| Boolean operator | Description |
| --- | --- |
| <= | Less than or equal |
| < | Less than |
| == | Equal |
| ~= | Approximately equal |
| >= | Greater than or equal |
| > | Greater than |

The `in` membership operator uses a slightly modified if-syntax:

```
if (expression1 in [expression2, expression3, ..., expressionN], trueExpression, falseExpression)
```

If expression1 is equal to either of expression1 through expressionN,
then trueExpression is used, otherwise falseExpression.

## The foreach function

The foreach function is not really part of the expression language but implemented as a
[rank feature](rank-features.html#foreach(dimension,variable,feature,condition,operation)).

## Tensor functions

The following set of tensors functions are available to use in ranking expressions.
The functions are grouped in primitive functions and convenience
functions that can be implemented in terms of the primitive ones.

### Primitive functions

| Function | Description |
| --- | --- |
| map(   tensor,   f(x)(expr) ) | Returns a new tensor with the lambda function defined in `f(x)(expr)` applied to each cell.  Arguments:   * `tensor`: a tensor expression. For example `attribute(tensor_field)` * `f(x)(expr)`: a [lambda function](#lambda) with one argument.  Returns a new tensor where the expression in the lambda function is evaluated in each cell in `tensor`. Examples:  ``` map(t, f(x)(x*x)) ```  [playground example map](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKAFwEoSZGpCIJIPArQDOWNgB5oAGywBDHgD4uAD0QAWALp84iAAzEAjMQBMxAMz7IQiAF8hz0hmrlcDIh+GUaE50DAC2KjgA+gRaKqE4in7BECJhEVws7Nz8xGDQ2nzaAHpWfALBrhiVYPogzkA) |
| map_subspaces(   tensor,   f(x)(expr) ) | Returns a new tensor with the lambda function defined in `f(x)(expr)` applied to each dense subspace.  Arguments:   * `tensor`: a tensor expression. For example `attribute(tensor_field)` * `f(x)(expr)`: a [lambda function](#lambda) with one argument.  Returns a new tensor where the lambda function is evaluated for each dense subspace in `tensor`. This is an advanced feature that enables using dense [tensor generator](#tensor) expressions to transform mixed tensors. Example:  ``` map_subspaces(tensor(x{},y[3]):{a:[1,2,3]},f(d)(tensor(z[2])(d{y:(z)}+d{y:(z+1)}))) ```  [playground example for map_subspaces](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKAFwEoSZGpCIJIPArQDOWNgB4AlrR4AOAHxcAHsAC+xDogBMAXT5xgAQziIAjAFZiAWhsA2YzshCIOoXqHVyXAYiUhooSjQvOgZmWhwLAGMAawB9ACMFHikUgHdMgAsUgFsLHBSpZjSpeISCKUEwiBEGErKKqpq6rhZ2bn5iaC4AEz5eSRl5JVUNA1dTLgyeYeAOOC4OAHoVPj0AdkcOAFJtvlPPMJ8MS7BjEB0gA) |
| filter_subspaces(   tensor,   f(x)(expr) ) | Returns a new tensor containing only the subspaces for which the lambda function defined in `f(x)(expr)` returns true.  Arguments:   * `tensor`: a tensor expression. Must have at least one mapped dimension. * `f(x)(expr)`: a [lambda function](#lambda) with one argument.  Returns a new tensor containing only the subspaces for which the lambda function defined in `f(x)(expr)` returns true. Typically used to get rid of unneeded values in sparse tensors. Example:  ``` filter_subspaces(tensor(x{}):{a:1,b:2,c:3,d:4},f(value)(value>2)) # tensor(x{}):{c:3,d:4} ```  [playground example for filter_subspaces](https://docs.vespa.ai/playground/#N4IgZiBcDaoPYAcogMYgDQiZUAXZABLgBYCmBAjgK4CGANgJa4CeBcYB9dBKxVAdgGsAziAC+Y9PGwhSGLFFD9kuAIzy5kELlL9hcAE4AeMHTg1cAPgAUvAYOBiAlDgAMkVQGZ0qyAHZ0ACZIAFZ0Tw8wgBZIT1d0EMhAsXFJaWQ0TGw8QgA5AgZhAgATZn4aAFsGNAkpEERkOSzFEGUtXI1kT1S6hq1MhRxtQjAGfmK2A2LSAzGAczYOFFI6OlFa9K0mwaUVQM7+lboAfUNpg2s1dAIKmgAPJx7N1Hls4a0bmkFyGk-hQQIYEMRDIBAARqRhLgCB0NvUZNs3m1tN1MJptIEjLC0vCMq8WvgPsUDIhOKsCMIqGDhAgaMsimASRUQeRbv8QRZOAZyGB6MI5HC+rJ8UNkbgogdwAw6DoDMdKdTafTLt5AdZhE51U5HoKZAM3oSQDw4BUwWMedLZaQJmyAQB3JjESYMOZjehEXT6AyA4Hcykyp64rYi3ZaXAhSXigBUalSAF0xEA) |
| reduce(   tensor,   aggregator,   dim1,   dim2,   ... ) | Returns a new tensor with the `aggregator` applied across dimensions dim1, dim2, etc. If no dimensions are specified, reduce over all dimensions.  Arguments:   * `tensor`: a tensor expression. * `aggregator`: the aggregator to use. See below. * `dim1, dim2, ...`: the dimensions to reduce over. Optional.   Returns a new tensor with the aggregator applied across dimensions `dim1`, `dim2`, etc. If no dimensions are specified, reduce over all dimensions.  Available aggregators are:   * `avg`: arithmetic mean * `count`: number of elements * `max`: maximum value * `median`: median value * `min`: minimum value * `prod`: product of all values * `sum`: sum of all values  Examples:  ``` reduce(t, sum)         # Sum all values in tensor reduce(t, count, x)    # Count number of cells along dimension x ```  [playground example reduce](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKAFwEoSZGpCIJIPArQDOWNgB5oAGywBDHgD4uAD0QAWALp84iAAzEAjMQBMxAMz7IQiAF8hz0hmrlcDIh+GUaE50DGwEACbMAMYEAPpSzAC2sQRaKok4in7BECKhEdEEXCzs3PzEYAmJAsGuGHVg+iDOQA) |
| join(   tensor1,   tensor2,   f(x,y)(expr) ) | Returns a new tensor constructed from the *natural join* between `tensor1` and `tensor2`, with the resulting cells having the value as calculated from `f(x,y)(expr)`, where `x` is the cell value from `tensor1` and `y` from `tensor2`.  Arguments:   * `tensor1`: a tensor expression. * `tensor2`: a tensor expression. * `f(x,y)(expr)`: a [lambda function](#lambda) with two arguments.   Returns a new tensor constructed from the *natural join* between `tensor1` and `tensor2`, with the resulting cells having the value as calculated from `f(x,y)(expr)`, where `x` is the cell value from `tensor1` and `y` from `tensor2`.  Formally, the result of the `join` is a new tensor with dimensions the union of dimension between `tensor1` and `tensor2`. The cells are the set of all combinations of cells that have equal values on their common dimensions.  Examples:   ``` {% raw %} join(t1, t2, f(x,y)(x * y)) {% endraw %} ```  [playground example join](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKAFwEoSZGpCIJIPArQDOWNgB5oAGywBDHgD4uAD2ABfPnGDAtcAAy6EARgB0p4mhOWLYAEy3dkIRF1DdpDNTkuAxE-sKUaF50DGo8bACWAEbMErwCYTSEDBLSsgrKapo6fhx6BkYmdhxmzgDMtvbGZsTVTggALA0OcJYtNQgArF1Nva3OAGzunpk+GH5CgZjBYqFRFPiL5PRiAFZY8fQZwqJQewdcLOzc-PaxCcmpN2DQ2i182mAAVGAcfAJRs1QgIAuiBdEA) |
| merge(   tensor1,   tensor2,   f(x,y)(expr) ) | Returns a new tensor consisting of all cells from both the arguments, where the lambda function is used to produce a single value in the cases where both arguments provide a value for a cell.  Arguments:   * `tensor1`: a tensor expression. * `tensor2`: a tensor expression. * `f(x,y)(expr)`: a [lambda function](#lambda) with two arguments.   Returns a new tensor having all the cells of both arguments, where the lambda is invoked to produce a single value only when both arguments have a value for the same cell.  The argument tensors must have the same type, and that will be the type of the resulting tensor. Example:   ``` {% raw %} merge(t1, t2, f(left,right)(right)) {% endraw %} ```  [playground example merge](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKAFwEoSZGpCIJIPArQDOWNlwDWBDsAC+xAB6IATAF0+cYAEM4iAIzFdxAEYmAzMQAsOlZCEQVQtUOrlcDIqQ0UJRobnQMhjw8bACWVswSvAKBQYQMEtKyCkqqGtp6BjaIAKzEAGw6xADGJgDsxAAczq5BHhheGD6YfmIBYRT4XeT0YgC27ADmBAD6BOqGozgANn2paWOTBFws7Nz8xGCR0XEJW-tg0Fwr0DzEsRMAFvxc9098AmFtqF86ICpAA) |
| tensor(   tensor-type-spec )(expr) | Generates new tensors according to type specification and expression `expr`.  Arguments:   * `tensor-type-spec`: an [indexed tensor type specification.](tensor.html#tensor-type-spec) * `(expression)`: a [lambda function](#lambda) expressing how to generate the tensor.   Generates new tensors according to the type specification and expression `expr`. The tensor type must be an indexed tensor (e.g. `tensor<float>(x[10])`). The expression in `expr` will be evaluated for each cell. The arguments in the expression is implicitly the names of the dimensions defined in the type spec.  Useful for creating transformation tensors. Examples:   ``` {% raw %} tensor<float>(x[3])(x) {% endraw %} ```  [playground generate examples](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gHMDaCAnAQwBcCB9VgO4kyNSEQSQetAM5Y2ACgAeiAMwBdAJRKNkERAC+I-aQzVyuBkROjKaPXQbNWnHvwIDeAJmE1M4qFKybAA80AA2WNwAfEqInmrEAJ5xmkpgALzpYIk69oYYxiJmmBYSVvYU+MXk9BJcPr6EDIFysQAsmnCIAIwAdAAMxGCeA0Mqo2BtA2q6vvmohaYVpU3W5LbVDhJO7Nx8grzQbFgAtrwctFhcABbsvC1sDb5izSxB8tApWlzAinDQAGpuvpcnMjCg1CB9EA) |
| rename(   tensor,   dim-to-rename,   new-names ) | Renames one or more dimensions in the tensor.  Arguments:   * `tensor`: a tensor expression. * `dim-to-rename`: a dimension, or list of dimensions, to rename. * `new-names`: new names for the dimensions listed above.  Returns a new tensor with one or more dimension renamed. Examples:  ``` {% raw %} rename(t1,x,z) {% endraw %} ```  [playground rename examples](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gBcSybIiEmDaBnLAJwAUAD2ABfYgE9xASjjBgwuAAYpKsQgCMAOlVolqyXE0awy3cX3G1y0+b2LrRk1t1jIrCGNYTW1crgMRKQ0UJRonnQM-NwAhgC2BAD6BMIJOAA2wZEQ7NFxiYKMxMLEAF4yHqHeGL4Y-piBnNmhFPgN5PScMbQJyanpWUmMAO5YLKG5HFA9fUXEIlIyCwCWxABWMpWRNai7ALogYkA) |
| concat(   tensor1,   tensor2,   dim ) | Concatenates two tensors along dimension `dim`.  Arguments:   * `tensor1`: a tensor expression. * `tensor2`: a tensor expression. * `dim`: the dimension to concatenate along.  Returns a new tensor with the two tensors `tensor1` and `tensor2` concatenated along dimension `dim`. Examples:  ``` {% raw %} concat(t,t2,x) {% endraw %} ```  [playground concat examples](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gBcSybIiEmDaBnLAJwAUAD0QBmALoBKOIgAsxAKzEAbBMisIAX1ZbSGauVwMi+tpTSa6DRgCYWNTByiNufIaNvTZY4nPVWOhh6rIaYxpymVhT4YeT0nADGWLSJAIbMZo7sDMmpGYKMxHbEwlIajkGoIQbREYQO5rFWEJAJUHnpjAD6WIwAFgT83QDuaQCejdnOkJ0FJUVlFTRV2igSIFpAA) |
| (tensor)partial-address | Slice - returns a new tensor containing the cells matching the partial address.  Arguments:   * `tensor`: a tensor expression. * `partial-address`: Can be given in the form of a tensor address `{dimension:label,..}`,   or for tensors referenced directly and having a single mapped or indexed type respectively   as just a label in curly brackets `{label}`   or just an index in square brackets, `[index]`.   Index labels may be specified by a lambda expression enclosed in parentheses.  Returns a new tensor containing the cells matching the partial address. A common special case is producing a single value by specifying a full address. The type of the resulting tensor is the dimensions of the argument tensor not specified by the partial address. Examples:  ``` {% raw %} # a_tensor is of type tensor(key{},x[2]) a_tensor{key:key1,x:1} {% endraw %} ```  [playground slice examples](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gBcSybIiEmDaBnLAJwAUAD0QBmALoBKOIgAsxAKzEAbBMisIAX1ZbSGauVwMi+tpTSa6DHgBsAlgGNTViOwaNgwuAAYtGmjAdDD1WQ0xjThdAinxw8npOOycCAH0AJhZAtw4oT290-ytg1FCDK2wLdzNyC3jrTkZMmrZcrl4BQQBrAgBPYD1RdOk4YDAe3oBGWUmAOh9iMHT5iUWJ9NkxecW5FaCAmhLtFvrKkyzzONcoRKhk51SAWwBDHBwCABNU+1oPgmFPhcYm0msAJnAJpNiN5JkVAkcgicKpFCEDMHVrpBbpB7mkXm9Pt9fv9Cc1MSD0mC+hC+lDvIIxABadJSOGHXQoCQgLRAA) |
| tensor-literal-form | Returns a new tensor having the type and cell values given explicitly. Each cell value may be supplied by a lambda which can access other features.  Returns a new tensor from the [literal form](tensor.html#tensor-literal-form), where the type must be specified explicitly. Each value may be supplied by a lambda, which - in contrast to all other lambdas - *may refer to features and expressions from the context*. Examples:   ``` {% raw %} # Declare an indexed tensor tensor(x[2]):[1.0, 2.0]  # Declare an mapped tensor tensor(x{}):{x1:3, x2:4} {% endraw %} ``` |
| cell_cast(   tensor,   cell_type ) | Returns a new tensor that is the same as the argument, except that all cell values are converted to the given [cell type](tensor.html#tensor-type-spec).  Arguments:   * `tensor`: a tensor expression. * `cell_type`: wanted cell type.  Example, casting from `bfloat16` to `float`:  ``` {% raw %} # With a tensor t of the type tensor<bfloat16>(x[5])(x+1) cell_cast(t, float) {% endraw %} ``` |
| cell_order(   tensor,   order ) | Returns a new tensor with the rank of the original cells based on the given order.  Arguments:   * `tensor`: a tensor expression. * `order`: `max` or `min`  Returns a new tensor with the rank of the original cells based on the given order. With `max` the largest value gets rank 0. With `min` the smallest value gets rank 0. Examples:  ``` cell_order(tensor(x[3]):[2,3,1],max) # tensor(x[3]):[1,0,2] cell_order(tensor(x[3]):[2,3,1],min) # tensor(x[3]):[1,2,0] ```  [playground example for cell_order](https://docs.vespa.ai/playground/#N4IgZiBcDaoPYAcogMYgDQiZUAXZABLgBYCmBAjgK4CGANgJa4CeBcYB9dBKxVAdgGsAziAC+Y9PGwhSGLFFD9kuAIzy5kELlL9hcAE4AeMHTg1cAPgAUvAYOBiAlDgAMkVQGZ0qyAHZ0ACZIAFZ0Tw8wgBZIT1d0EMhAsXFJaWQ0TGw8QgA5AgZhAgATZn4aAFsGNAkpEERkOSzFEGUtXI1kT1S6hq1MhRxtQjAGfmK2A2LSAzGAczYOFFI6OlFa9K0mwaUVQM7+lboAfUNpg2s1dAIKmgAPJx7N1Hls4a0bmkFyGk-hQQIYEMRDIBAARqRhLgCB0NvUZNs3m1tN1MJptIEjLC0vCMq8WvgPsUDIhOKsCMIqGDhAgaMsimASRUQeRbv8QRZOAZyGB6MI5HC+rJ8UNkbgogdwAw6DoDMdKdTafTLt5AdZhE51U5HoKZAM3oSQDw4BUwWMedLZaQJmyAQB3JjESYMOZjehEXT6AyA4Hcykyp64rYi3ZaXAhSXigBUalSAF0xEA) |

### Lambda functions in primitive functions

Some of the primitive functions accept lambda functions that are evaluated
and applied to a set of tensor cells.
The functions contain a single expression that have the same format and built-in functions as
[general ranking expressions](ranking-expressions.html).
However, the atoms are the arguments defined in the argument list of the lambda.

The expression cannot access variables or data structures outside the lambda,
i.e. they are not closures.

Examples:

```
f(x)(log(x))
f(x,y)(if(x < y, 0, 1))
```

### Non-primitive functions

Non-primitive functions can be implemented by primitive functions,
but are not necessarily so for performance reasons.
Note that all the arithmetic operators, comparison operators, and
scalar operations can also be applied to tensors directly,
those are not repeated below here.

| Function | Description |
| --- | --- |
| argmax(t, dim) | `join(t, reduce(t, max, dim), f(x,y)(if (x == y, 1, 0)))`  Returns a tensor with cell(s) of the highest value(s) in the tensor set to 1. The dimension argument follows the same format as reduce as multiple dimensions can be given and is optional. |
| argmin(t, dim) | `join(t, reduce(t, min, dim), f(x,y)(if (x == y, 1, 0)))`  Returns a tensor with cell(s) of the lowest value(s) in the tensor set to 1. The dimension argument follows the same format as reduce as multiple dimensions can be given and is optional. |
| avg(t, dim) | `reduce(t, avg, dim)`  Reduce the tensor with the `average` aggregator along dimension `dim`. If the dimension argument is omitted, this reduces over all dimensions. |
| count(t, dim) | `reduce(t, count, dim)`  Reduce the tensor with the `count` aggregator along dimension `dim`. If the dimension argument is omitted, this reduces over all dimensions. |
| cosine_similarity(t1, t2, dim) | `reduce(t1*t2, sum, dim) / sqrt(reduce(t1*t1, sum, dim) * reduce(t2*t2, sum, dim))`  The cosine similarity between the two vectors in the given dimension. |
| diag(n1, n2) | `tensor(i[n1],j[n2])(if (i==j, 1.0, 0.0)))`  Returns a tensor with the diagonal set to 1.0. |
| elu(t) | `map(t, f(x)(if(x < 0, exp(x)-1, x)))`  [Exponential linear unit](https://arxiv.org/abs/1511.07289). |
| euclidean_distance(t1, t2, dim) | `join(reduce(map(join(t1, t2, f(x,y)(x-y)), f(x)(x * x)), sum, dim), f(x)(sqrt(x)))`  euclidean_distance: `sqrt(sum((t1-t2)^2, dim))`. |
| expand(t, dim) | `t * tensor(dim[1])(1)`  Adds an indexed dimension with name `dim` to the tensor `t`. |
| hamming(t1, t2) | `join(t1, t2, f(x,y)(hamming(x,y)))`  Join and return the Hamming distance between matching cells of `t1` and `t2`. This function is mostly useful when the input contains vectors with binary data and summing the hamming distance over the vector dimension, e.g.:   | type of input *t1* → | `tensor<int8>(dimone{},z[32])` | | type of input *t2* → | `tensor<int8>(dimtwo{},z[32])` | | expression → | `reduce(join(t1, t2, f(a,b)(hamming(a,b)), sum, z)` | | output type → | `tensor<float>(dimone{},dimtwo{})` |   Note that the cell values are always treated as if they were both 8-bit integers in the range [-128,127], and only then counting the number of bits that are different. See also the corresponding [distance metric](schema-reference.html#distance-metric). Arguments can be scalars. |
| l1_normalize(t, dim) | `join(t, reduce(t, sum, dim), f(x,y) (x / y))`  L1 normalization: `t / sum(t, dim)`. |
| l2_normalize(t, dim) | `join(t, map(reduce(map(t, f(x)(x * x)), sum, dim), f(x)(sqrt(x))), f(x,y)(x / y))`  L2 normalization: `t / sqrt(sum(t^2, dim)`. |
| matmul(t1, t2, dim) | `reduce(join(t1, t2, f(x,y)(x * y)), sum, dim)`  Matrix multiplication of two tensors. This is the product of the two tensors summed along a shared dimension. |
| max(t, dim) | `reduce(t, max, dim)`  Reduce the tensor with the `max` aggregator along dimension `dim`. |
| median(t, dim) | `reduce(t, median, dim)`  Reduce the tensor with the `median` aggregator along dimension `dim`. If the dimension argument is omitted, this reduces over all dimensions. |
| min(t, dim) | `reduce(t, min, dim)`  Reduce the tensor with the `min` aggregator along dimension `dim`. |
| prod(t, dim) | `reduce(t, prod, dim)`  Reduce the tensor with the `product` aggregator along dimension `dim`. If the dimension argument is omitted, this reduces over all dimensions. |
| random(n1, n2, ...) | `tensor(i1[n1],i2[n2],...)(random(1.0))`  Returns a tensor with random values between 0.0 and 1.0, uniform distribution. |
| range(n) | `tensor(i[n])(i)`  Returns a tensor with increasing values. |
| relu(t) | `map(t, f(x)(max(0,x)))`  Rectified linear unit. |
| sigmoid(t) | `map(t, f(x)(1.0 / (1.0 + exp(0.0-x))))`  Returns the sigmoid of each element. |
| softmax(t, dim) | `join(map(t, f(x)(exp(x))), reduce(map(t, f(x)(exp(x))), sum, dim), f(x,y)(x / y))`  The softmax of the tensor, e.g. `e^x / sum(e^x)`. |
| sum(t, dim) | `reduce(t, sum, dim)`  Reduce the tensor with the `summation` aggregator along dimension `dim`. If the dimension argument is omitted, this reduces over all dimensions. |
| top(n, t) | `t * filter_subspaces(cell_order(t, max) < n, f(s)(s))`  top N function: Picks top N cells in a simple mapped tensor. |
| unpack_bits(t) | unpacks bits from int8 input to 8 times as many floats  The innermost indexed dimension will expand to have 8 times as many cells, each with a float value of either 0.0 or 1.0 determined by one bit in the 8-bit input value. Comparable to `numpy.unpackbits` which gives the same basic functionality. A minimal input such as `tensor<int8>(x[1]):[9]` would give output `tensor<float>(x[8]):[0,0,0,0,1,0,0,1]` (default bit-order is big-endian). As a very complex example, an input with type `tensor<int8>(foo{},x[3],y[11],z{})` will produce output with type `tensor<float>(foo{},x[3],y[88],z{})` where "foo", "x" and "z" are unchanged, as "y" is the innermost indexed dimension. |
| unpack_bits(t, cell_type) | unpacks bits from int8 input to 8 times as many values  Same as above, but with optionally different cell_type (could be `double` for example, if you will combine the output with other tensors using double). |
| unpack_bits(t, cell_type, endian) | unpacks bits from int8 input to 8 times as many values  Same as above, but also optionally different endian for the bits; must be either `big` (default) or `little`. |
| xw_plus_b(x, w, b, dim) | `join(reduce(join(x, w, f(x,y)(x * y)), sum, dim), b, f(x,y)(x+y))`  Matrix multiplication of `x` (usually a vector) and `w` (weights), with `b` added (bias). A typical operation for activations in a neural network layer, e.g. `sigmoid(xw_plus_b(x,w,b)))`. |
