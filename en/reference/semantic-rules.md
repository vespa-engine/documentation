---
# Copyright Vespa.ai. All rights reserved.
title: "Semantic Rule Language Reference"
---

This is the reference for the semantic rule language in Vespa.
For a guide on using this language,
see [query rewriting](../query-rewriting.html).
Refer to the [Query API](query-api-reference.html#semantic-rules) for how to use in queries.

## Rule bases

Semantic rules are collected in files called *rule bases*.
The name of these files are *[rule-base-name].sr*.
They must be placed in *[application-package]/rules/* to be deployed.

## Basic syntax

A rule base may contain any number of the following four constructs,
explained in the rest of this document:
* [directives](#directives)
* [production rules](#production-rules)
* [named conditions](#named-conditions)
* comments, starting by # and ending by newline.

Production rules and named conditions are *statements*.
Statements may span multiple lines and are terminated by `;`.

## Directives

A directive is a "meta-level" statement which is not used during rule evaluation,
but tells the rule engine how to use the rule base.
A statement starts by `@` and ends by newline.
They may take parameters. These directives exist:

| Statement | Usage | Location |
| --- | --- | --- |
| @default | Make this rule base the default, to be used with all queries | Anywhere outside other statements |
| @automata(<automata-filename>) | Use an automata file with this base | Anywhere outside other statements |
| @include(<rulebase-name>) | Include all the statements of another rule base in this | Anywhere outside other statements |
| @super | Include the conditions of the same-named conditions from the included rule base | In a condition |
| @stemming(<true|false>) | Whether terms should match after stemming or exactly (true by default) | Before any rule |
| @language(<[language-code](https://en.wikipedia.org/wiki/ISO_639-1)>) | The language of the rule base, which should also be the query language. Influences stemming. | Before any rule |

## Production Rules

A production rule is of the form:

```
<condition> <operator> <production-list>;
```

This performs the production as defined by the operator if the condition matches.
There are two kinds of production rules (and two operators), replacing and adding:

| Rule kind | Operator | Meaning |
| --- | --- | --- |
| Replacing | -> | *Replace* the matched terms by the production |
| Adding | +> | *Add* the production to the matched terms |

## Namespaces

A namespace is a collection of facts which can be read from conditions and changed by productions.
Namespaces may be positional (sequences), or not.
A positional namespace will track the current fact and match and insert at the current position,
while non-positional namespaces will match any fact against any condition.

There is a default namespace which does not need an explicit reference.
For query rules, the default namespace is the query terms.

To determine the namespace used to read from conditions or change in productions, use:

```
<namespace>.<condition>
<namespace>.<production>
```

There are two namespaces defined during query processing:

| Namespace | Syntax | Positional | Description |
| --- | --- | --- | --- |
| Query |  | Yes | The default namespace. References the terms of the query. The condition value returned will be the term itself. |
| Parameter | `parameter.` | No | References the parameter of the query. Conditions will be true if the parameter is set in the query. The value returned from conditions is the value of the parameter. Productions will need both a key and value specified to set a parameter value. |

## Named Conditions

A named condition is on the form:

```
[condition-name] :- <condition>;
```

This simply assigns a name to the condition on the right,
so it can be referred to the conditions in rules and other named conditions.

## Conditions

A condition is an expression which evaluates to true or false
over the *facts* of a [namespace](#namespaces).
If the namespace is *positional* (a *sequence*),
evaluation starts at the *current position* in the namespace.
When evaluated true, conditions will also return a value which can be referenced by comparison conditions.

Conditions may be preceded by a reference name and a label:

```
(<reference-name>/)?(<label>:)?<condition>
```

### Reference Name

The reference name allows an explicit name to be set,
from which the terms matched by the condition can be referred in a condition.
This is useful when multiple conditions of the same type are used in the condition of the same rule.

If no reference name is given,
the text standing between the square brackets of the condition is used as reference name.

### Label

If a label is specified,
the condition will only match terms having that label (the label is the index in query terms).
If a label is not set, the term will match if a label is not set, or if it is `default`.

### Condition

These are the supported kinds of conditions:

| Condition | Syntax | Meaning | Returned value |
| --- | --- | --- | --- |
| Term | <term> | True if this is the term at the current position | Determined by the [namespace](#namespaces) |
| Reference (produce the matched term(s)) | [<condition-name>] | Evaluate a named condition | The matched term(s) of the condition |
| Reference (produce all terms in the condition) | [<condition-name>*] | Evaluate a named condition | All the terms in the condition |
| Sequence | <condition> <condition> | Match both conditions by consecutive terms in the right order in the sequence | The last nested condition value |
| Choice | <condition>, <condition> | Match any one of the conditions, each one tried at the current position | The last nested condition value |
| Group | (<condition>) | Evaluate the condition inside the grouping as a unit | The last nested condition value |
| Ellipsis | … | Matches any sequence to make the overall condition match | The matched sequence |
| Referable ellipsis | […] | An ellipsis where the matched sequence can be referenced from the production | The matched sequence |
| Not | !<condition> | Matches if the condition does not match | Nothing |
| And | <condition> & <condition> | Matches if all the conditions matches at the (same) current position | The last nested condition value |
| Comparison | <condition> [<operator>](#operator) <condition> | True if the comparison is true for the values returned from the conditions | The last nested condition value |
| Literal | '<literal>' | Returns a value for comparison. This always evaluates to true. | The literal value |
| Start anchor | . <condition> | Matches condition only if it matches the query from the start | The matched sequence |
| End anchor | <condition> . | Matches condition only if it matches the query to the end | The matched sequence |

### Comparison Condition Operators

The possible operators of a comparison condition are:

| Operator | Meaning |
| --- | --- |
| = | Left and right values are equal |
| <= | Left value is smaller or equal |
| >= | Left value is larger or equal |
| < | Left value is smaller |
| > | Left value is larger |
| =~ | Left value contains right value as a substring |

## Production List

A production list consists of a space-separated list of *productions*
which are carried out when the production of a rule is matched.
A production can be preceded by the type of term to produce, a label (index in queries),
and followed by the weight (importance) of the produced value:

```
(<term-type>)?(<label>:)?<production>(!<weight>)?
```

### Term Type

The default term type is the term type of the context which the term is added to.
The possible explicit term types are:

| Syntax | Meaning |
| --- | --- |
| ? | Insert as an OR term |
| = | Insert as an EQUIV term |
| + | Insert as an AND term |
| $ | Insert as a RANK term |
| - | Insert as a NOT term |

### Label

If included, the label decides the label the produced term(s) will have in the namespace.
This is the index in the query namespace.

### Production

There are three types of productions:

| Production | Syntax | Meaning |
| --- | --- | --- |
| Literal term | <term> | Produce this term literally |
| Literal term with value | <term>='<value>' | Produce this term and value literally. |
| Reference | [<condition-reference>] | Produce the terms matched by the referenced condition. The reference name is either the name of a named condition used in the condition, an ellipsis - `…` - or an explicit condition reference name. |

### Weight

The weight is a percentage integer denoting the importance of the produced term.
The default is 100.
In the query namespace the weight becomes the term weight,
determining the relevance contribution of the term.
