---
# Copyright Vespa.ai. All rights reserved.
title: "Select Query Reference"
---


This document describes what the `select` parameter is and gives a few examples on how to use it. Refer to the [Query API](../query-api.html) for how to execute queries with POST.

The query has JSON syntax, and can be used with queries that are executed with HTTP POST. The `select` parameter is equivalent with YQL, and can be used instead of, but not together with YQL. Nor can it be used together with the `query` parameter.

## Structure


```json
"select" : {
  "where" : {...},
  "grouping" : {...}
}
```

Example query searching for the term 'country' in the field 'title':

```json
{
  "select": {
    "where": {
      "contains": ["title", "country"]
    }
  }
}
```

This query can be executed with `curl`:

```bash
curl -H "Content-Type: application/json" \
    --data "{ 'select': { 'where': { 'contains': ['default', 'country'] } } }" \
    http://localhost:8080/search/
```


### Where

Unlike the sql-like syntax in [YQL](../query-language.html), the *where* queries are written in a tree syntax. By combining YQLs functions and arguments, queries equivalent with YQL can be written in JSON.

#### Formal structure


Functions are nested like this: 

```
FUNCTION : {
  "children" : [ argument, argument,..],
  "attributes" : {annotations}
{
```

or like this, by moving the `children`-key up, if attributes are not in use with the function:

```
FUNCTION : [
  argument,
  argument,
  ...
]
```

YQL is a regular language and is parsed into a query tree when parsed in Vespa. That tree can also be built
with the `where` parameter in JSON.

Let's take a look at this yql: `select * from sources * where default contains foo and rank(a contains "A", b contains "B")`, which will create the following query tree:

<img src="/assets/img/querytree.svg" width="737px" height="auto" alt="Example query tree" />

The tree above can be written with the 'where' parameter, like this:

```json
{
  "and" :  [
    { "contains" : ["default", "foo"] },
    { "rank" : [
      { "contains" : ["a", "A"] },
      { "contains" : ["b", "B"] }
    ]}
  ]
}
```
which is equivalent with the YQL.



### Grouping

One or more [grouping statements](../grouping.html) can be set as a JSON array in the `grouping` field.
Each array item is a grouping statement represented as JSON where
- Each grouping function is represented by a JSON object where the name of the function is the field
  name and the value is the function content.
- Lists of arguments are represented as JSON arrays.

Examples:

Grouping statement:

```
| all(group(time.year(a)) each(output(count())
    all(group(time.monthofyear(a)) each(output(count())))
```
equivalent JSON `grouping`-argument:

```json
"grouping" : [
  {
    "all" : {
      "group" : "time.year(a)",
      "each" : { "output" : "count()" },
      "all" : {
        "group" : "time.monthofyear(a)",
        "each" : { "output" : "count()" },
      }
    }
  }
]
```

Grouping statement:

```
all(group(predefined(foo, bucket[1, 2>, bucket[3, 4>)))
```
equivalent JSON `grouping`-argument:

```json
"grouping" : [ 
  { 
    "all" : { 
      "group" : { 
        "predefined" : [ "foo", { "bucket": [1,2]}, { "bucket": [3,4]} ] 
      } 
    } 
  } 
]
```


### Complete examples

Query everything (`"where": true`), create one bucket for all documents (`"group": "\"all\""`) and output overall price statistics (`"avg(price)"` and `"sum(price)"`):

```json
{
  "select": {
    "where": true,
    "grouping": [
      {
        "all": {
          "group": "\"all\"",
          "each": {
            "output": [
              "avg(price)",
              "sum(price)"
            ]
          }
        }
      }
    ]
  }
}
```

A more complex example:
```json
{
  "select" : {
    "where" : {
      "and" : {
        "children" : [
          {"title" : "music"},
          {"default" : "festival"}
        ]
      }
     },
    "grouping" : [ {
      "all" : {
        "group" : "time.year(a)",
          "each" : { "output" : "count()" }
      }		
    } ]
  },
  "offset" : 5,
  "presentation" : {
    "bolding" : false,
    "format" : "json"
  }
}
```


---
### Examples with the different functions


##### CONTAINS
YQL: `where title contains 'a'`.

Format of this in JSON:

```json
"where" : {
  "contains" : [ "title", "a" ]
}
```

##### Numeric Operators
YQL: `where date >= 10`.

Format of this in JSON:

*Introducing the range parameter:*

```json
"range" : [
  "date",
  { ">=" : 10}
]
```

The range query accepts the following parameters:

<table class="table table-striped">
<tr><td><b>Operator</b></td><td><b>Description</b></td></tr>
<tr><td>≥</td><td>Greater-than or equal to</td></tr>
<tr><td>></td><td>Greater-than</td></tr>
<tr><td><</td><td>Less-than</td></tr>
<tr><td>≤</td><td>Less-than or equal to</td></tr>
</table>




YQL: `where range(field, 0, 500)`.

Format of this in JSON:

```json
"where" : {
  "range" : [
    "field",
    { ">=" : 0, "<=" : 500}
  ]
}
```


##### OR
YQL: `where title contains 'a' or title contains 'b'`.

Format of this in JSON:

```json
"where" : {
  "or" : [
    { "contains" : [ "title", "a" ] },
    { "contains" : [ "title", "b" ] }
  ]
}
```


##### AND
YQL: `where title contains 'a' and title contains 'b'`.

Format of this in JSON:

```json
"where" : {
  "and" : [
    {"contains" : [ "title", "a" ] },
  {"contains" : [ "title", "b" ] }
  ]
}
```


##### AND NOT
YQL: `where title contains 'a' and !(title contains 'b')`.

Format of this in JSON:

```json
"where" : {
  "and_not" : [
    {"contains" : [ "title", "a" ] },
    {"contains" : [ "title", "b" ] }
  ]
}
```

Formal structure:

```
"where" : {
  "and_not" : [
    <Statement>,
    <!Statement>,
    ..
  ]
}
```



##### Regular expressions
YQL: `where title matches "madonna"`.

Format of this in JSON:

```json
"where" : {
  "matches" : [
    "title",
    "madonna"
  ]
}
```
Another example:

YQL: `where title matches "mado[n]+a"`

```json
"where" : {
  "matches" : [
    "title",
    "mado[n]+a"
  ]
}
```


##### Phrase

YQL: `where text contains phrase("st", "louis", "blues")`.

Format of this in JSON:

```json
"where" : {
  "contains" : [ "text", { "phrase" : ["st", "louis", "blues"] } ]
}
```


##### Near and Ordered Near
YQL: `where description contains ([ {"distance": 100} ]onear("a", "b"))`.

Format of this in JSON:

```json
"where" : {
  "contains" : [ 
    "description",
    { "onear" : {
      "children" : ["a", "b"],
      "attributes" : {"distance" : 100} 
      }
    }
  ]
}
```


##### Search within same struct element
YQL: `where persons contains sameElement(first_name contains 'Joe', last_name contains 'Smith', year_of_birth < 1940)`.

Format of this in JSON:

```json
"where" : {
  "contains" : [
    "persons",
    { "sameElement" : [
      {"first_name" : "Joe",
      "last_name" : "Smith",
      "range" : [
        "year_of_birth",
        { "<" : 1940}
      ]
      }
    ]
    }
  ]
}
```


##### Term Equivalence
YQL: `where fieldName contains equiv("A","B")`.

Format of this in JSON:

```json
"where" : {
  "contains" : [
    "fieldName",
    { "equiv" : ["A", "B"] }
  ]
}
```


##### Rank
YQL: `where rank(a contains "A", b contains "B")`.

Format of this in JSON:

```json
"where" : {
  "rank" : [
    { "contains" : [ "a", "A" ] },
    { "contains" : [ "b", "B" ] }
  ]
}
```



##### Advanced functions

###### Wand
YQL: `where wand(description, {"a":1, "b":2}`.

Format of this in JSON:

```json
"where" : {
  "wand" : [ "description", {"a" : 1, "b":2} ]
}
```

Another example:

YQL: `where [ {"scoreThreshold": 13, "targetHits": 7} ]wand(description, {"a":1, "b":2})`.

Format of this in JSON:

```json
"where" : {
  "wand" : {
    "children" : [ "description", {"a" : 1, "b":2} ],
    "attributes" : {"scoreThreshold": 13, "targetHits": 7}
  }
}
```

###### dotProduct
YQL: `where dotProduct(description, {"a":1, "b":2})`.

Format of this in JSON:

```json
"where" : {
  "dotProduct" : [ "description", {"a" : 1, "b":2} ]
}
```

###### weightedSet
YQL: `where weightedSet(description, {"a":1, "b":2})`.

Format of this in JSON:

```json
"where" : {
  "weightedSet" : [ "description", {"a" : 1, "b":2} ]
}
```

###### weakAnd
YQL: `where {scoreThreshold: 41, "targetHits": 7}weakAnd(a contains "A", b contains "B")`.

Format of this in JSON:

```json
"where" : {
  "weakAnd" : {
    "children" : [ { "contains" : ["a", "A"] }, { "contains" : ["b", "B"] } ],
    "attributes" : {"scoreThreshold": 41, "targetHits": 7}
	}
}
```



##### Predicate
YQL: `where predicate(predicate_field,{"gender":"Female"},{"age":20L})`.

Format of this in JSON:

```
"where" : {
  "predicate" : [
    "predicate_field",
    {"gender" : "Female"},
    {"age" : 20L}
  ]
}
```



