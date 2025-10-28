---
# Copyright Vespa.ai. All rights reserved.
title: "Document Selector Language"
---

This document describes the *document selector language*, used to
select a subset of documents when feeding, dumping and garbage collecting data.
It defines a text string format that can be parsed to build a parse tree,
which in turn can answer whether a given document is contained within the subset or not.

## Examples

Match all documents in the `music` schema:

`music`

As applications can have multiple schemas,
match document type (schema) and then a specific value in the `artistname` field:

`music and music.artistname == "Coldplay"`

Below, the first condition states that the documents should be of type music,
and the author field must exist.
The second states that the field length must be set, and be less than or equal to 1000:

`music.author and music.length <= 1000`

The next expression selects all documents where either of the subexpressions are true.
The first one states that the author field should include the name John Doe, with anything in between or in front.
The `\n` escape is converted to a newline before the field comparison is done.
Thus requiring the field to end with Doe and a newline for a match to be true.
The second expression selects all books where no author is defined:

`book.author = "*John*Doe\n" or not book.author`

Here is an example of how parentheses are used to group expressions.
Also, a constant value false has been used. Note that the `(false or music.test)`
sub-expression could be exchanged with just `music.test` without altering the result of the selection.
The sub-expression within the `not` clause selects all documents
where the size field is above 1000 and the test field is defined.
The `not` clause inverts the selection,
thus selecting all documents with size less than or equal to 1000 or the test field undefined:

`not (music.length > 1000) and (false or music.test)`

Other examples:
* `music.version() == 3 and (music.givenname + " " + music.surname).lowercase() = "bruce spring*"`
* `id.user.hash().abs() % 300 % 7 = 1`
* `music.wavstream.hash() == music.checksum`
* `music.size / music.length > 10`
* `music.expire > now() - 7200`

## Case sensitiveness

The identifiers used in this language (`and or not true false null id
scheme namespace specific user group`) are not case-sensitive.
It is recommended to use lower cased identifiers for consistency with the documentation.

## Branch operators / precedence

The branch operators are used to combine other nodes in the parse tree
generated from the text format. The different branch nodes existing is
listed in the table below in order of precedence.
Operators listed in order of precedence:

| Operator | Description |
| --- | --- |
| NOT | Unary prefix operator inverting the selection of the child node |
| AND | Binary infix operator, which is true if all its children are |
| OR | Binary infix operator, which is true if any of its children are |

Use parentheses to define own precedence.
`a and b or c and d` is equivalent to `(a and b) or (c and d)` since and has higher precedence than or. The expression
`a and (b or c) and d` is not
equivalent to the previous two, since parentheses have been used to force the
or-expression to be evaluated first.

Parentheses can also be used in value calculations.
Where modulo `%` has the highest precedence,
multiplication `*` and division `/` next,
addition `+` and subtractions `-` have lowest precedence.

## Primitives

| Primitive | Description |
| --- | --- |
| Boolean constant | The boolean constants `true` and `false` can be used to match all/nothing |
| Null constant | Referencing a field that is not present in a document returns a special `null` value. The expression `music.title` is shorthand for `music.title != null`. There are potentially subtle interactions with null values when used with comparisons, see [comparisons with missing fields (null values)](#comparisons-with-missing-fields-null-values). |
| Document type | A document type can be used as a primitive to select a given type of documents - [example](/en/visiting.html#analyzing-field-values). |
| Document field specification | A document field specification (`doctype.field`) can be used as a primitive to select all documents that have field set - a shorter form of `doctype.field != null` |
| Comparison | The comparison is a primitive used to compare two values |

## Comparison

Comparisons operators compares two values using an operator.
All the operators are infix and take two arguments.

| Operator | Description |
| --- | --- |
| > | This is true if the left argument is greater than the right one. Operators using greater than or less than notations only makes sense where both arguments are either numbers or strings. In case of strings, they are ordered by their binary (byte-wise) representation, with the first character being the most significant and the last character the least significant. If the argument is of mixed type or one of the arguments are not a number or a string, the comparison will be invalid and not match. |
| < | Matches if left argument is less than the right one |
| <= | Matches if the left argument is less than or equal to the right one |
| >= | Matches if the left argument is greater than or equal to the right one |
| == | Matches if both arguments are exactly the same. Both arguments must be of the same type for a match |
| != | Matches if both arguments are not the same |
| = | String matching using a glob pattern. Matches only if the pattern given as the right argument matches the whole string given by the left argument. Asterisk `*` can be used to match zero or more of any character. Question mark `?` can be used to match any one character. The pattern matching operators, regex `=~` and glob `=`, only makes sense if both arguments are strings. The regex operator will never match anything else. The glob operator will revert to the behaviour of `==` if both arguments are not strings. |
| =~ | String matching using a regular expression. Matches if the regular expression given as the right argument matches the string given as the left argument. Regex notation is like perl. Use '^' to indicate start of value, '$' to indicate end of value |

### Comparisons with missing fields (null values)

The only comparison operators that are well-defined when one or both operands may be `null`
(i.e. field is not present) are `==` and `!=`. Using any other comparison operators
on a `null` value will yield a special *invalid* value.

Invalid values may "poison" any logical expression they are part of:
* `AND` returns invalid if none of its operands are false and at least one is invalid
* `OR` returns invalid if none of its operands are true and at least one is invalid
* `NOT` returns invalid if the operand is invalid

If an invalid value is propagated as the root result of a selection expression, the document is
not considered a match. This is usually the behavior you want; if a field does not exist, any selection
requiring it should not match either. However, in garbage collection, documents which results in an invalid
selection are *not* removed as that could be dangerous.

One example where this may have *unexpected* behavior:

1. You have many documents of type `foo` already fed into a cluster.
2. You add a new field `expires_at_time` to the document type and update a subset of the
   documents that you wish to keep.
3. You add a garbage collection selection to the `foo` document declaration to only
   keep non-expired documents: `foo.expires_at_time > now()`

At this point, the old documents that *do not* contain an `expires_at_time` field will *not*
be removed, as the expression will evaluate to invalid instead of `false`.

To work around this issue, "short-circuiting" using a field presence check may be used:
`(foo.expires_at_time != null) and (foo.expires_at_time > now())`.

## Null behavior with imported fields

If your selection references imported fields,
`null` will be returned for any imported field when the selection is evaluated
in a context where the referenced document can't be retrieved.
For GC expressions this will happen in the client as part of the feed routing logic,
and it may also happen on backend nodes whose parent document set is incomplete (in case of node failures etc.).
It is therefore important that you have this in mind when writing GC selections using imported fields.

When you specify a selection criteria in a `<document>` tag, you're stating what
a document must satisfy in order to be fed into the content cluster and to be kept there.

As an example, imagine a document type `music_recording` with an imported field
`artist_is_cool` that points to a boolean field `is_cool` in a parent
`artist` document.
If you only want your cluster to retain recordings from artists that are certifiably cool,
you might be tempted to write a selection like the following:

```
{% highlight xml %}

{% endhighlight %}
```
**This won't work as expected**, because this expression is evaluated as part of the feeding pipeline to figure
out if a cluster should accept a given document. At that point in time, there is no access to the parent document.
Consequently, the field will return `null` and the document won't be routed to the cluster.

Instead, write your expressions to handle the case where the parent document *may not exist*:

```
{% highlight xml %}

{% endhighlight %}
```

With this selection, we explicitly let a document be accepted into the cluster if its imported field
is *not* available. However, if it *is* available, we allow it to be used for GC.

## Locale / Character sets

The language currently does not support character sets other than ASCII.
Glob and regex matching of single characters are not guaranteed to match exactly one character,
but might match a part of a character represented by multiple byte values.

## Values

The comparison operator compares two values. A value can be any of the following:

| Document field specification | Syntax: `<doctype>.<fieldpath>`  Documents have a set of fields defined, depending on the document type. The field name is the identifier used for the field. This expression returns the value of the field, which can be an integer, a floating point number, a string, an array, or a map of these types.  For multivalues, we support only the *equals* operator for comparison. The semantics is that the array returned by the fieldvalue must *contain* at least one element that matches the other side of the comparison. For maps, there must exist a key matching the comparison.  The simplest use of the fieldpath is to specify a field, but for complex types please refer to [the field path syntax documentation](document-field-path.html). |
| Id | Syntax:  `id.[scheme|namespace|type|specific|user|group]`  Each document has a Document Id, uniquely identifying that document within a Vespa installation. The id operator returns the string identifier, or if an optional argument is given, a part of the id.   * scheme (id) * namespace (to separate different users' data) * type (specified in the id scheme) * specific (User specified part to distinguish documents within a namespace) * user (The number specified in document ids using the n= modifier) * group (The string group specified in document ids using the g= modifier) |
| null | The value null can be given to specify nothingness. For instance, a field specification for a document not containing the field will evaluate to null, so the comparison 'music.artist == null' will select all documents that don't have the artist field set. 'id.user == null' will match all documents that don't use the `n=` [document id scheme](../documents.html#id-scheme).  Tensor fields can *only* be compared against null. It's not possible to write a document selection that uses the *contents* of tensor fields—only their presence can be checked. |
| Number | A value can be a number, either an integer or a floating point number. Type of number is insignificant. You don't have to use the same type of number on both sides of a comparison. For instance '3.0 < 4' will match, and '3.0 == 3' will probably match (operator == is generally not advised for floating point numbers due to rounding issues). Numbers can be written in multiple ways - examples:   ```   1234  -234  +53  +534.34  543.34e4  -534E-3  0.2343e-8 ``` |
| Strings | A string value is given quoted with double quotes (i.e. "mystring"). The string is interpreted as an ASCII string. that is, only ASCII values 32 to 126 can be used unescaped, apart from the characters \ and " which also needs to be escaped. Escape common special characters like:   | Character | Escaped character | | --- | --- | | Newline | \n | | Carriage return | \r | | Tab | \t | | Form feed | \f | | " | \" | | Any other character | \x## (where ## is a two digit hexadecimal number specifying the ASCII value. | |

### Value arithmetics

You can do arithmetics on values.
The common arithmetics operators addition `+`, subtraction `-`,
multiplication `*`, division `/` and modulo `%` are supported.

### Functions

Functions are called on something and returns a value that can be used in comparison expressions:

| Value functions | A value function takes a value, does something with it and returns a value which can be of any type.  * *abs()* Called on a numeric type, returns the absolute value of that numeric type.   That is -3 returns 3 and -4.3 returns 4.3. * *hash()* Calculates an MD5 hash of whatever value it is called on. The result is a   signed 64-bit integer. (Use abs() after if you want to only get positive hash values). * *lowercase()* Called on a string value to turn upper   case characters into lower case ones.   **NOTE:** This only works for the characters 'a' through 'z', no locale support. |
| Document type functions | Some functions can take a document type instead of a value, and return a value based on the type.  * *version()* The `version()` function returns   the version number of a document type. |

#### Now function

Document selection provides a *now()* function, which returns the current date timestamp.
Use this to filter documents by age, typically for [garbage collection](services-content.html#documents).
**Example**: If you have a long field *inserttimestamp* in your `music` schema,
this expression will only match documents from the last two hours:

`music.inserttimestamp > now() - 7200`

## Using imported fields in selections

When using [parent-child](../parent-child.html) you can refer to simple imported
fields (i.e. top-level primitive fields) in selections as if they were regular fields
in the child document type. Complex fields (collections, structures etc.) are not supported.

{% include important.html content="special care needs to be taken
when using document selections referencing imported fields,
especially if using these are part of garbage collection expressions. If an imported field
references a document that cannot be accessed at evaluation time, the imported field behaves
as if it had been a regular, non-present field in the child document.
In other words, it will return the special `null` value."%}

See [comparisons with missing fields (null values)](#comparisons-with-missing-fields-null-values)
for a more detailed discussion of null-semantics and how to write selections that handle these
in a well-defined manner. In particular, read  [null
behavior with imported fields](#null-behavior-with-imported-fields) if you're writing GC selections.

### Example

The following is an example of a 3-level parent-child hierarchy.

Grandparent schema:

```
schema grandparent {
    document grandparent {
        field a1 type int {
            indexing: attribute | summary
        }
    }
}
```

Parent schema, with reference to grandparent:

```
schema parent {
    document parent {
        field a2 type int {
            indexing: attribute | summary
        }
        field ref type reference<grandparent> {
            indexing: attribute | summary
        }
    }
    import field ref.a1 as a1 {}
}
```

Child schema, with reference to parent and (transitively) grandparent:

```
schema child {
    document child {
        field a3 type int {
            indexing: attribute | summary
        }
        field ref type reference<parent> {
            indexing: attribute | summary
        }
    }
    import field ref.a1 as a1 {}
    import field ref.a2 as a2 {}
}
```

Using these in document selection expressions is easy:

Find all child docs whose grandparents have an `a1` greater than 5:

`child.a1 > 5`

Find all child docs whose parents have an `a2` of 10 and grandparents have `a1` of 4:

`child.a1 == 10 and child.a2 == 4`

Find all child docs where the parent document cannot be found (or where the referenced field is not set in the parent):

`child.a2 == null`

Note that when visiting `child` documents we only ever access imported fields via the
**child** document type itself.

A much more complete list usage examples for the above document schemas and
reference relations can be found in the
[imported fields in selections](https://github.com/vespa-engine/system-test/blob/master/tests/search/parent_child/imported_fields_in_selections.rb) system test. This test covers both the visiting and GC cases.

## Constraints

Language identifiers restrict what can
be used as document type names. The following values are not valid document type names:
*true, false, and, or, not, id, null*

## Grammar - EBNF of the language

To simplify, double casing of strings has not been included.
The identifiers "null", "true", "false" etc. can be written in any case, including mixed case.

```
nil              = "null" ;
bool             = "true" | "false" ;
posdigit         = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' ;
digit            = '0' | posdigit ;
hexdigit         = digit | 'a' | 'b' | 'c' | 'd' | 'e' | 'f'
					 	   | 'A' | 'B' | 'C' | 'D' | 'E' | 'F' ;
integer          = [ '-' | '+' ], posdigit, { digit } ;
float            = [ '-' | '+' ], digit, { digit },
      			[ '.' , { digit }, [ ('e' | 'E'), posdigit, { digit } ] ] ;
number           = float | integer ;
stdchars         = ? All ASCII chars except '\\', '"', 0 - 31 and 127 - 255 ? ;
alpha            = ? ASCII characters in the range a-z and A-Z ? ;
alphanum         = alpha | digit ;
space            = ( ' ' | '\t' | '\f' | '\r' | '\n' ) ;
string           = '"', { stdchars | ( '\\', ( 't' | 'n' | 'f' | 'r' | '"' ) )
							| ( "\\x", hexdigit, hexdigit ) }, '"' ;
doctype          = alpha, { alphanum } ;
fieldname        = { alphanum '{' |'}' | '[' | ']' '.' } ;
function         = alpha, { alphanum } ;
idarg            = "scheme" | "namespace" | "type" | "specific" | "user" | "group" ;
searchcolumnarg  = integer ;
operator         = ">=" | ">" | "==" | "=~" | "=" | "<=" | "<" | "!=" ;
idspec           = "id", [ '.', idarg ] ;
searchcolumnspec = "searchcolumn", [ '.', searchcolumnarg ] ;
fieldspec        = doctype, ( function | ('.', fieldname) ) ;
value            = ( valuegroup | nil | number | string | idspec | searchcolumnspec | fieldspec ),
				   { function } ;
valuefuncmod     = ( valuegroup | value ), '%',
				   ( valuefuncmod | valuegroup | value ) ;
valuefuncmul     = ( valuefuncmod | valuegroup | value ), ( '*' | '/' ),
				   ( valuefuncmul | valuefuncmod | valuegroup | value ) ;
valuefuncadd     = ( valuefuncmul | valuefuncmod | valuegroup | value ),
				   ( '+' | '-' ),
				   ( valuefuncadd | valuefuncmul | valuefuncmod | valuegroup
				   | value ) ;
valuegroup       = '(', arithmvalue, ')' ;
arithmvalue      = ( valuefuncadd | valuefuncmul | valuefuncmod | valuegroup
				   | value ) ;
comparison       = arithmvalue, { space }, operator, { space },
				   arithmvalue ;
leaf             = bool | comparison | fieldspec | doctype ;
not              = "not", { space }, ( group | leaf ) ;
and              = ( not | group | leaf ), { space }, "and", { space },
				   ( and | not | group | leaf ) ;
or               = ( and | not | group | leaf ), { space }, "or", { space },
				   ( or | and | not | group | leaf ) ;
group            = '(', { space }, ( or | and | not | group | leaf ),
				   { space }, ')' ;
expression       = ( or | and | not | group | leaf ) ;
```
