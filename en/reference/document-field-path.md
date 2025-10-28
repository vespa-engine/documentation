---
# Copyright Vespa.ai. All rights reserved.
title: "Document Field Path Syntax"
---

The field path syntax is used several places in Vespa to traverse documents through
arrays, structs, maps and sets and generate a set of values matching the expression. Examples -
If the document contains the field `mymap`, and it has a
key `mykey`, the expression returns the value of the map for that key:

```
mymap{mykey}
```

Returns the value in index 3 of the `myarray` field, if set:

```
myarray[3]
```

Returns the value of the `value1` field in the struct
field `mystruct`, if set:

```
mystruct.value1
```

If mystructarray is an array field containing structs,
returns the values of value1 for each of those structs:

```
mystructarray.value1
```

The following syntax can be used for the different field types,
and can be combined recursively as required:

## Maps/weighted Sets

| <mapfield>{<keyvalue>} | Retrieve the value of a specific key |
| <mapfield>{$<variablename>} | Retrieve all values, setting the [variable](#variables) to the key value for each |
| <mapfield>.key | Retrieve all key values |
| <mapfield>.value | Retrieve all values |
| <mapfield> | Retrieve all keys |

In the case of weighted sets, the value referenced above is the weight of the item.

## Array

| <arrayfield>[<index>] | Retrieve the value in a specific index |
| <arrayfield>[$<variablename>] | Retrieve all values in the array, setting the [variable](#variables) to the index of each |
| <arrayfield> | Retrieve all values in the array |

## Struct

| <structfield>{.<subfield>} | Return the value of the struct field |
| <structfield> | Return the value of all subfields |

Note that when specifying values of subscripts of maps, weighted sets and arrays,
only primitive types (numbers and strings) may be used.

## Variables

It can be useful to reference several field paths using a common variable.
For instance, if you have an array of structs,
you may want to use document selection on fields within the same array index together.
This could be done by an expression like:

```
mydoctype.mystructarray{$x}.field1=="foo" AND mydoctype.mystructarray{$x}.field2=="bar"
```

Variables either have a `key` value (for maps and weighted sets),
or an `index` value (for arrays).
Variables cannot be used across such contexts
(that is, a map key cannot be used to index into an array).
