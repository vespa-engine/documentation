---
# Copyright Vespa.ai. All rights reserved.
title: "Internal Configuration File Reference"
---

This reference describes the configuration file format used by Vespa internally.

## File Format

Configuration files (*.cfg*) contain lines on the form:

```
configuration-variable configuration-value
```

A simple example of a file containing an integer and a string:

```
myInt 3
myString "Hello"  # Strings must always be enclosed in quotation marks.
```

### Arrays

Arrays start with a line declaring the number of items in the array.
Each following line will contain the array name again,
the array offset (0-base) in square brackets and the value at this position.
For example, an array called "myArray" with 3 items:

```
myArray[3]
myArray[0] firstvalue
myArray[1] secondvalue
myArray[2] thirdvalue
```

When an array value contains a child array,
dots act as a separator between the parent value and the child array.
For example, to set a table with two rows,
the first with two columns and the second having one column
(provided the table structure is defined in the accompanying .def file):

```
row[2]
row[0].column[2]
row[0].column[0] value0_0
row[0].column[1] value0_1
row[1].column[1]
row[1].column[0] value1_0
```
