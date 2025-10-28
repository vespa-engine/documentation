---
# Copyright Vespa.ai. All rights reserved.
title: "Indexing Language Reference"
redirect_from:
- /en/reference/advanced-indexing-language.html
---

This reference documents the full Vespa *indexing language*.
If more complex processing of input data is required, implement a
[document processor](../document-processing.html).

The indexing language is analogous to UNIX pipes, in that statements
consists of expressions separated by the *pipe* symbol
where the output of each expression is the input of the next.
Statements are terminated by semicolon and are independent of each
other (except when using variables).

Find examples in the [indexing](/en/indexing.html) guide.

## Indexing script

An indexing script is a sequence of [indexing
statements](#indexing-statement) separated by a semicolon (`;`). A script is
executed statement-by-statement, in order, one document at a time.

Vespa derives one indexing script per search cluster based on the search
definitions assigned to that cluster. As a document is fed to a search
cluster, it passes through the corresponding
[indexing cluster](services-content.html#document-processing), which runs the
document through its indexing script.
Note that this also happens whenever the document is
[reindexed](../operations/reindexing.html), so expressions such as [now](#now) must
be thought of as the time the document was (last) *indexed*, not when it was *fed*.

You can examine the indexing script generated for a specific search
cluster by retrieving the configuration of the indexing document processor.

```
$ vespa-get-config -i search/cluster.<cluster-name> -n vespa.configdefinition.ilscripts
```

The current *execution value* is set to `null` prior to
executing a statement.

## Indexing statement

An indexing statement is a sequence of [indexing
expressions](#indexing-expression) separated by a pipe (`|`).
A statement is executed expression-by-expression, in order.

Within a statement, the execution value is passed from one expression to the next.

The simplest of statements passes the value of an input field into an attribute:

```
input year | attribute year;
```

The above statement consists of 2 expressions; `input year` and
`attribute year`. The former sets the execution value to the
value of the "year" field of the input document. The latter writes the
current execution value into the attribute "year".

## Indexing expression

### Primitives

A string, numeric literal and true/false can be used as an expression to explicitly
set the execution value. Examples: `"foo"`, `69`, `true`).

### Outputs

An output expression is an expression that writes the current execution
value to a document field. These expressions also double as the indicator
for the type of field to construct (i.e. attribute, index or summary). It
is important to note that you can not assign different values to
the same field in a single document (e.g. `attribute | lowercase |
index` is **illegal** and will not deploy).

| Expression | Description |
| --- | --- |
| `attribute` | Writes the execution value to the current field. During deployment, this indicates that the field should be stored as an attribute. |
| `index` | Writes the execution value to the current field. During deployment, this indicates that the field should be stored as an index field. |
| `summary` | Writes the execution value to the current field. During deployment, this indicates that the field should be included in the document summary. |

### Arithmetics

Indexing statements can contain any combination of arithmetic operations,
as long as the operands are numeric values. In case you need to convert
from string to numeric, or convert from one numeric type to another,
use the applicable [converter](#converters) expression.
The supported arithmetic operators are:

| Operator | Description |
| --- | --- |
| `<lhs> + <rhs>` | Sets the execution value to the result of adding of the execution value of the `lhs` expression with that of the `rhs` expression. |
| `<lhs> - <rhs>` | Sets the execution value to the result of subtracting of the execution value of the `lhs` expression with that of the `rhs` expression. |
| `<lhs> * <rhs>` | Sets the execution value to the result of multiplying of the execution value of the `lhs` expression with that of the `rhs` expression. |
| `<lhs> / <rhs>` | Sets the execution value to the result of dividing of the execution value of the `lhs` expression with that of the `rhs` expression. |
| `<lhs> % <rhs>` | Sets the execution value to the remainder of dividing the execution value of the `lhs` expression with that of the `rhs` expression. |
| `<lhs> . <rhs>` | Sets the execution value to the concatenation of the execution value of the `lhs` expression with that of the `rhs` expression. If *both* `lhs` and `rhs` are collection types, this operator will append `rhs` to `lhs` (if any operand is null, it is treated as an empty collection). If not, this operator concatenates the string representations of `lhs` and `rhs` (if any operand is null, the result is null). |

You may use parenthesis to declare precedence of execution (e.g. `(1
+ 2) * 3`). This also works for more advanced array concatenation
statements such as `(input str_a | split ',') . (input str_b | split
',') | index arr`.

### Converters

These expressions let you convert from one data type to another.

| Converter | Input | Output | Description |
| --- | --- | --- | --- |
| `binarize [threshold]` | Any tensor | Any tensor | Replaces all values in a tensor by 0 or 1. This takes an optional argument specifying the threshold a value needs to be larger than to be replaced by 1 instead of 0. The default threshold is 0. This is useful to create a suitable input to [pack_bits](#pack_bits). |
| `embed [id] [args]` | String | A tensor | Invokes an [embedder](../embedding.html) to convert a text to one or more vector embeddings. The type of the output tensor is what is required by the following expression (as supported by the specific embedder). Arguments are given space separated, as in `embed colbert chunk`. The first argument and can be omitted when only a single embedder is configured. Any additional arguments are passed to the embedder implementation. If the same chunk expression with the same input occurs multiple times in a schema, its value will only be computed once. |
| `chunk id [args]` | String | A tensor | Invokes a which convert a string into an array of strings. Arguments are given space separated, as in `chunk fixed-length 512`. The id of the chunker to use is required and can be a chunker bundled with Vespa, or any chunker component added in the services.xml, see the [chunking reference](chunking-reference.html). Any additional arguments are passed to the chunker implementation. If the same chunk expression with the same input occurs multiple times in a schema, its value will only be computed once. |
| `hash` | String | int or long | Converts the input to a hash value (using SipHash). The hash will be int or long depending on the target field. |
| `pack_bits` | A tensor | A tensor | Packs the values of a binary tensor into bytes with 1 bit per value in big-endian order. The input tensor must have a single dense dimension. It can have any value type and any number of sparse dimensions. Values that are not 0 or 1 will be binarized with 0 as the threshold.  The output tensor will have:   * `int8` as the value type. * The dense dimension size divided by 8 (rounded upwards to integer). * The same sparse dimensions as before.   The resulting tensor can be unpacked during ranking using [unpack_bits](ranking-expressions.html#unpack-bits). A tensor can be converted to binary form suitable as input to this by the [binarize function](#binarize). |
| `to_array` | Any | Array<inputType> | Converts the execution value to a single-element array. |
| `to_byte` | Any | Byte | Converts the execution value to a byte. This will throw a NumberFormatException if the string representation of the execution value does not contain a parseable number. |
| `to_double` | Any | Double | Converts the execution value to a double. This will throw a NumberFormatException if the string representation of the execution value does not contain a parseable number. |
| `to_float` | Any | Float | Converts the execution value to a float. This will throw a NumberFormatException if the string representation of the execution value does not contain a parseable number. |
| `to_int` | Any | Integer | Converts the execution value to an int. This will throw a NumberFormatException if the string representation of the execution value does not contain a parseable number. |
| `to_long` | Any | Long | Converts the execution value to a long. This will throw a NumberFormatException if the string representation of the execution value does not contain a parseable number. |
| `to_bool` | Any | Bool | Converts the execution value to a boolean type. If the input is a string it will become true if it is not empty. If the input is a number it will become true if it is != 0. |
| `to_pos` | String | Position | Converts the execution value to a position struct. The input format must be either a) `[N|S]<val>;[E|W]<val>`, or b) `x;y`. |
| `to_string` | Any | String | Converts the execution value to a string. |
| `to_uri` | String | Uri | Converts the execution value to a URI struct |
| `to_wset` | Any | WeightedSet<inputType> | Converts the execution value to a single-element weighted set with default weight. |
| `to_epoch_second` | String | Long | Converts an ISO-8601 instant formatted String to Unix epoch (or Unix time or POSIX time or Unix timestamp) which is the number of seconds elapsed since January 1, 1970, UTC. The converter uses [java.time.Instant.parse](https://docs.oracle.com/en/java/javase/20/docs/api/java.base/java/time/Instant.html#parse(java.lang.CharSequence)) to parse the input string value. This will throw a DateTimeParseException if the input cannot be parsed. Examples:   * `2023-12-24T17:00:43.000Z` is converted to `1703437243L` * `2023-12-24T17:00:43Z` is converted to `1703437243L` * `2023-12-24T17:00:43.431Z` is converted to `1703437243L` * `2023-12-24T17:00:43.431+00:00` is converted to `1703437243L` |

### Other expressions

The following are the unclassified expressions available:

| Expression | Description |
| --- | --- |
| `_` | Returns the current execution value. This is useful, e.g., to prepend some other value to the current execution value, see [this example](/en/indexing.html#execution-value-example). |
| `attribute <fieldName>` | Writes the execution value to the named attribute field. |
| `base64decode` | If the execution value is a string, it is base-64 decoded to a long integer. If it is not a string, the execution value is set to `Long.MIN_VALUE`. |
| `base64encode` | If the execution value is a long integer, it is base-64 encoded to a string. If it is not a long integer, the execution value is set to `null`. |
| `echo` | Prints the execution value to standard output, for debug purposes. |
| `flatten` | {% include deprecated.html content='Use [tokens](/en/reference/schema-reference.html#tokens) in the schema instead.' %} |
| `for_each { <script> }` | Executes the given indexing script for each element in the execution value. Here, element refers to each element in a collection, or each field value in a struct. |
| `generate [id] [args]` | Invokes a [field generator](../llms-document-enrichment.html) to generate a field valued from an input string. The argument is the id of the `FieldGenerator` component as described in [Document enrichment with LLMs](../llms-document-enrichment.html#). If the same generate expression with the same input occurs multiple times in a schema, its value will only be computed once. |
| `get_field <fieldName>` | Retrieves the value of the named field from the execution value (which needs to be either a document or a struct), and sets it as the new execution value. |
| `get_language` | Retrieves the code of the last assigned or detected language, ur "un" for "unknown" if no language has been assigned or detected. Language is detected when a string is tokenized or embedded, so this can be used to retrieve the language detected by a previous field executing one such operation, e.g. by indexing. |
| `get_var <varName>` | Retrieves the value of the named variable from the execution context and sets it as the execution value. Note that variables are scoped to the indexing script of the current field. |
| `hex_decode` | If the execution value is a string, it is parsed as a long integer in base-16. If it is not a string, the execution value is set to `Long.MIN_VALUE`. |
| `hex_encode` | If the execution value is a long integer, it is converted to a string representation of an unsigned integer in base-16. If it is not a long integer, the execution value is set to `null`. |
| `hostname` | Sets the execution value to the name of the host computer. |
| `if (<left> <cmp> <right>) {      <trueScript>  }  [ else { <falseScript> } ]` | Executes the `trueScript` if the conditional evaluates to true, or the `falseScript` if it evaluates to false. If either `left` or `right` is null, no expression is executed. The value produced is the value returned from the chosen branch, and these must produce values of compatible types (or none). |
| `index <fieldName>` | Writes the execution value to the named index field. |
| `input <fieldName>` | Retrieves the value of the named field from the document and sets it as the execution value. The field name may contain '.' characters to retrieve nested struct fields. |
| `join "<delim>"` | Creates a single string by concatenating the string representation of each array element of the execution value. This function is useful or indexing data from a [multivalue](../schemas.html#field) field into a singlevalue field. |
| `lowercase` | Lowercases all the strings in the execution value. |
| `ngram <size>` | Adds ngram annotations to all strings in the execution value. |
| `normalize` | [normalize](../linguistics.html#normalization) the input data. The corresponding query command for this function is `normalize`. |
| `now` | Outputs the current system clock time as a UNIX timestamp, i.e. seconds since 0 hours, 0 minutes, 0 seconds, January 1, 1970, Coordinated Universal Time (Epoch). |
| `random [ <max> ]` | Returns a random integer value. Lowest value is 0 and the highest value is determined either by the argument or, if no argument is given, the execution value. |
| `sub-expression1 || sub-expression2 || ...` | Returns the value of the first alternative sub-expression which returns a non-null value. See [this example](/en/indexing.html#choice-example). |
| `select_input {   ( case <fieldName>: <statement>; )*   }` | Performs the statement that corresponds to the **first** named field that is not empty (see [example](/en/indexing.html#select-input-example)). |
| `set_language` | Sets the language of this document to the string representation of the execution value. Parses the input value as an RFC 3066 language tag, and sets that language for the current document. This affects the behavior of the [tokenizer](../linguistics.html#tokenization). The recommended use is to have one field in the document containing the language code, and that field should be the **first** field in the document, as it will only affect the fields defined **after** it in the schema. Read [linguistics](../linguistics.html) for more information on how language settings are applied. |
| `set_var <varName>` | Writes the execution value to the named variable. Note that variables are scoped to the indexing script of the current field. |
| `substring <from> <to>` | Replaces all strings in the execution value by a substring of the respective value. The arguments are inclusive-from and exclusive-to. Both arguments are clamped during execution to avoid going out of bounds. |
| `split <regex>` | Splits the string representation of the execution value into a string array using the given regex pattern. This function is useful for creating [multivalue](../schemas.html#field) fields such as an integer array out of a string of comma-separated numbers. |
| `summary <fieldName>` | Writes the execution value to the named summary field. During deployment, this indicates that the field should be included in the document summary. |
| `switch {   ( case '<value>': <caseStatement>; )*   [ default: <defaultStatement>; ]   }` | Performs the statement of the case whose value matches the string representation of the execution value (see [example](/en/indexing.html#switch-example)). |
| `tokenize [ normalize ] [ stem ]` | Adds linguistic annotations to all strings in the execution value. Read [linguistics](../linguistics.html) for more information. |
| `trim` | Removes leading and trailing whitespace from all strings in the execution value. |
| `uri` | Converts all strings in the execution value to a URI struct. If a string could not be converted, it is removed. |
