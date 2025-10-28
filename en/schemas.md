---
# Copyright Vespa.ai. All rights reserved.
title: "Schemas"
redirect_from:
- /en/schema-inheritance.html
---

A schema defines a [document type](documents.html) and what we want to compute over it, the
[rank-profiles](reference/schema-reference.html#rank-profile).
Schemas are stored in files named the same as the schema, with the ending ".sd" (for schema definition),
in the `schemas/` directory of the application package.
Refer to the [schema reference](reference/schema-reference.html).

Document types, rank profiles and document summaries in schemas can be [inherited](#schema-inheritance).

Schema example:

```
schema music {
    document music {

        field artist type string {
            indexing: summary | index
        }

        field artistId type string {
            indexing: summary | attribute
            match: word
            rank: filter
        }

        field title type string {
            indexing: summary | index
        }

        field album type string {
            indexing: index
        }

        field duration type int {
            indexing: summary
        }

        field year type int {
            indexing: summary | attribute
        }

        field popularity type int {
            indexing: summary | attribute
        }
    }

    fieldset default {
        fields: artist, title, album
    }

    rank-profile song inherits default {
        first-phase {
            expression {
                nativeRank(artist,title) +
                if(isNan(attribute(popularity)) == 1, 0, attribute(popularity))
            }
        }
    }
}
```

{% include deprecated.html content="Compatibility note: Schemas can be stored in the `searchdefinitions/`
directory and use `search` instead of `schema` as the top level tag. This is deprecated."%}

## document

A [document](documents.html) is the unit the rank-profile evaluates, and is returned in query results.
Documents have fields - reads and writes updates full documents or some fields of documents.
Refer to the [schema reference](reference/schema-reference.html#document).

Documents can have relations, field values can be imported from [parent documents](parent-child.html).

Note that the document id is not a field of the document - add this explicitly if needed.

## field

A field has a type, see [field reference](reference/schema-reference.html#field) for a full list.

A field contained in a document can be written to, read from and queried - this is the normal field use.
A field can also be generated (i.e. a *synthetic field*) -
in this case, the field definition is *outside* the document.
See [reindexing](operations/reindexing.html) for examples.

### Multivalue field

A field can be *single value*, like a string, or *multivalue*, like an array of strings -
see the [field type list](reference/schema-reference.html#field).
Most multivalue fields can be used in [grouping](reference/grouping-syntax.html#multivalue-attributes).
Accessing attributes in [maps](reference/schema-reference.html#map) and
[arrays of struct](reference/schema-reference.html#array) in ranking is not possible.

The rank feature [attribute(name).count](reference/rank-features.html#attribute(name).count)
can be used in ranking to *rank* based on number of elements in a multivalue attribute.
To *filter* based on number of elements, create a
[strict tiering rank function](ranking-expressions-features.html#the-if-function-and-string-equality-tests)
combined with a [rank-score-drop-limit](reference/schema-reference.html#rank-score-drop-limit).
Then use a [query variable](ranking-expressions-features.html#using-query-variables) for number of elements.
Note that doing this filtering is more expensive to evaluate than just having a separate field for the count.

### Field size

There is no general setting for max field size in terms of size in bytes.
Example of fields with potentially large value includes
[string](/en/reference/schema-reference.html#string)
and [raw](/en/reference/schema-reference.html#raw) fields.
Other large values include multivalue fields with many elements,
like an [array](/en/reference/schema-reference.html#array),
[weightedset](/en/reference/schema-reference.html#weightedset) or
[tensor](/en/reference/schema-reference.html#tensor).
This is relevant when the field is returned in query responses -
large result sets and parallel queries requires the Container with the query endpoint
to keep many field instances in memory simultaneously.
Use a [summary class](/en/document-summaries.html) to tune which fields to return in query responses,
and keep result sets smaller using [limit](/en/reference/query-language-reference.html#limit-offset)
or [hits](/en/reference/query-api-reference.html#hits).

Vespa requires a document to be able to load into memory in serialized form.
A document in json format is serialized in the Container hosting the
[document-api](/en/document-v1-api-guide.html) endpoint,
and persisted in the content node [document store](/en/proton.html#document-store).

A text field is capped at [max-length](/en/reference/schema-reference.html#max-length)
characters when indexing.
Increase this to index all terms in large string fields, example:

```
match {
    max-length: 15000000
}
```

## struct

A [struct](/en/reference/schema-reference.html#struct)
is contained in a document and groups one or more fields into a composite type that can be accessed like a single field.

Example:

```
    struct email {
        field sender type string {}
        field recipient type string {}
        field subject type string {}
        field content type string {}
    }

    field emails type array<email> {}
```

In this example the struct is part of an
[array](/en/reference/schema-reference.html#array).
A struct can also be used in a [map](/en/reference/schema-reference.html#map).

## struct-field

A [struct-field](/en/reference/schema-reference.html#struct-field)
defines how a given field in a struct should be indexed and searched.

Note that though a struct-field refers to a field in a struct, the struct-field itself is defined inside a field.

Using the *email* struct defined previously (see [struct](schemas.html#struct)),
we can define indexing for a specific field, like *content*:

```
    field emails type array<email> {
        indexing: summary
        struct-field content {
            indexing: attribute
            attribute: fast-search
        }
    }
```

The equivalent code (including the struct definition) in Pyvespa is as follows:

```
    email_struct = Struct(name="email", fields=[
      Field(name="sender", type="string"),
      Field(name="recipient", type="string"),
      Field(name="subject", type="string"),
      Field(name="content", type="string"),
    ])
    emails_field = Field(name="emails",
                    type="array<email>",
                    indexing=["summary"],
                    struct_fields=[StructField(name="content", indexing=["attribute"], attribute=["fast-search"])]
    )
    schema = Schema(name="schema", document=Document())
    schema.add_fields(emails_field)
    schema.document.add_structs(email_struct)
```

## indexing

[indexing](reference/schema-reference.html#indexing)
configures how to process data of a field during indexing - the most important ones are:

| `index` | For unstructured text: Create a text index for this field. [Text matching](text-matching.html) and all text ranking features become available. Indexes are disk backed and do not need to fit in memory. [Reference](reference/schema-reference.html#indexing) / [index details](proton.html#index) |
| `attribute` | For structured data: Keep this field in memory in a forward structure. This makes the field available for grouping, sorting and ranking. Attributes may also be searched by complete match (word or exact), or (for numerical fields) by range. Optionally a B-tree in memory can also be created by adding the fast-search option - this improves performance if the attribute is a strong criterion in queries (i.e. filters out many documents). [Reference](reference/schema-reference.html#attribute) / [attribute details](attributes.html) |
| `summary` | Include this field in the document summary in search result sets. [Reference](reference/schema-reference.html#summary) / [document summary details](document-summaries.html) |

Indexing instructions have pipeline semantics similar to unix shell
commands, with data flowing from left to right.
They can perform complex transformations on field values,
or just send the field value unchanged to the next sections of the index structure.
Example: The data is first added to the document summary,
then added as an in-memory attribute and finally indexed:

```
indexing: summary | attribute | index
```

{% include important.html content='If both
`attribute` and `index` is set on a field,
queries to this field use `index` mode.
The normal case for setting both is to run queries (using `index`) with
[grouping](grouping.html) (that requires `attribute`).' %}

### match

The [match](reference/schema-reference.html#match) mode configures
*how* query items are matched to fields (e.g. exact or prefix matching),
and is tightly coupled with *indexing*.
Find more details in [text matching](text-matching.html).

When searching in array or map of struct,
[sameElement()](reference/query-language-reference.html#sameelement) is a useful query operator
to restrict matches to same struct element
(e.g. *first_name contains 'Joe', last_name contains 'Smith'* -
both must match in the *same* field value).
Note that the document summary will not contain which element(s) matched.

### fieldset

A [fieldset](reference/schema-reference.html#fieldset) create a group of fields which can be queried as one:

```
fieldset myset {
    fields: artist, title, album
}
```
```
$ vespa query "select * from sources * where myset contains 'bob' and title contains 'best'"
```

Each term searching a fieldset is only tokenized once, so all the field in a field set should have compatible types
and match settings.

If you want to let some user text search multiple fields with different match settings, repeat the
[userInput](/en/reference/query-language-reference.html#userinput) query operator multiple times in the query:

```
select * from sources * where ({defaultIndex: 'fieldsetOrField1'}userInput(@query)) or ({defaultIndex: 'fieldsetOrField2'}userInput(@query))
```

### rank-profile

The [rank profile](ranking.html#rank-profiles) defines the computation to be made over
documents of this type when matching a query.
Learn more in [getting started with ranking](getting-started-ranking.html).

## IDE support

Vespa provides schema editing IDE plugins for VSCode and Jetbrains (IntelliJ, PyCharm etc.), see
[IDE support](/en/ide-support).

## Schema modifications

Vespa is built for safe schema modifications,
like adding a field or changing indexing or match modes.
A new version of the schema is deployed in an [application package](application-packages.html).
As some changes are potentially destructive (e.g. change a field index settings),
the `deploy` command will by default not accept such changes.
Example output from deploy (change from *index* to *attribute*):

```
Invalid application package: Error loading default.default: indexing-change:
Document type 'music': Field 'artist' changed:
remove index aspect,
  matching: 'text' -> 'word',
  stemming: 'best' -> 'none', normalizing: 'ACCENT' -> 'LOWERCASE',
  summary field 'artist' transform: 'none' -> 'attribute',
  indexing script:
    '{ input artist | tokenize normalize stem:\"BEST\" | summary artist | index artist; }' ->
    '{ input artist | summary artist | attribute artist; }'
To allow this add <allow until='yyyy-mm-dd'>indexing-change</allow> to validation-overrides.xml
```

To accept such changes, add a [validation-override](reference/validation-overrides.html):

```
{% highlight xml %}

    indexing-change

{% endhighlight %}
```

By blocking destructive changes, it is safe and easy to automate on an evolving schema.
Many schema changes are non-destructive and does not require the validation override, like adding a field.
Read more in [modifying-schemas](reference/schema-reference.html#modifying-schemas).

Refer to procedure to change from
[attribute to index](/en/operations-selfhosted/procedure-change-attribute-index.html).

### Field rename

Renaming a field is not directly supported. Options:

1. Drop the field, then refeed data with a partial update for just that field.
   Change queries, rank-profiles, query profiles and fieldsets to use the new field.
   This will make the field's data unavailable until fully re-fed.
2. Add the field with the new name, then refeed data with a partial update for that field.
   Once done, change queries, rank-profiles, query profiles and fieldsets to use the new field.
   This keeps the data available at all times, but increases storage requirements temporarily.

Also try using an [alias](/en/reference/schema-reference.html#alias).

## Multiple schemas

An application can define multiple document types, each in their own schema.
Multiple schemas can either be mapped to a single content cluster, or one
can define separate content clusters for schemas to be able to scale differently for the document types.
A single container cluster can be used to query all the document types in both these configurations.

In an application with multiple document types, the query restricts which document types to be used.
Vespa will by default query all document types and all clusters in parallel,
and blend results based on score - find details in [federation](federation.html).

To limit a query to a subset of the document types,
set [restrict](reference/query-api-reference.html#model.restrict)
to a comma-separated list of schema names:

```
$ vespa query 'select * from sources * where title contains "bob"' restrict=music,books
```

### Content nodes and schemas

Schemas can be thought of as tables in a database.
Most applications start off with one schema, adding schemas as more content types are needed.
Queries can hit one, some, or all schemas,
using the [restrict](#multiple-schemas) query parameter
or selecting in [YQL](/en/query-language.html).

Content nodes can hold multiple schemas:

```
{% highlight xml %}






{% endhighlight %}
```

One or more schemas can be deployed in separate content clusters:

```
{% highlight xml %}









{% endhighlight %}
```

The evolution can be illustrated like:

![Schemas deployed in multiple content clusters](/assets/img/schemas-and-content-clusters.svg)

The optimal mapping from schema to content cluster is application dependent:
* If there are no performance or sizing problems with all schemas in one content cluster,
  keep this - one cluster is easier to manage than multiple.
* Data in one schema can dominate the others.
  In these cases, consider a separate content cluster with a resource specification targeted for the write/query load.
  The extreme case of this is one content cluster per schema.
  This is a simple model, too, and enables resource optimization per schema.
* Applications using *both* indexed and streaming [mode](/en/reference/services-content.html#document.mode)
  should use *separate* content clusters for the different modes.

[Sizing search](/en/performance/sizing-search.html) is a good read for how to optimize content clusters.

### Content cluster mapping

To limit a query to a subset of the content clusters,
set [from sources](reference/query-language-reference.html#from-sources)
to a comma-separated list of content cluster ids, e.g.:

```
$ vespa query 'select * from sources items, news where title contains "bob"'
```

The request parameter *restrict* and *from sources* can be combined
to search both a subset of document types and content clusters.

## Inheritance

Both document types and full schemas can be inherited to make it easy to
design a structured application package with little duplication.
Document type inheritance defines a type hierarchy which is also useful for applications that
[federate queries](federation.html)
as queries can be written to the common supertype.
This guide covers the different elements in the schema that supports inheritance:

1. Schemas
2. Document types
3. Rank profiles
4. Document summaries

![Schema elements that support inheritance](/assets/img/inheritance-overview.svg)
{% include note.html content="Inheritance is not to be confused with [parent/child](parent-child.html),
which is a feature to import field values at query time."%}

## Schema inheritance

A schema that inherits another gets all the content of the parent schema
as if it was defined inside the inheriting schema.
A schema that inherits another must also (explicitly) inherit its document type:

```
schema books inherits items {
    document books inherits items  {
        field author type string {
            indexing: summary | index
        }
    }
}
```

## Document type inheritance

A document type can inherit another document type. This will include all fields, also fields declared outside the
document block in the schema, rank-profiles defined in the super-schema can then be inherited in the schema of this
document, see [Rank profile inheritance](#rank-profile-inheritance) below.

Both schemas *music* and *books* have the *title* field through inheritance:

`my-app/schemas/items.sd`:

```
document items {
    field title type string {
        indexing: summary | index
    }
}
```

`my-app/schemas/books.sd`:

```
schema books {
    document books inherits items {
        field author type string {
            indexing: summary | index
        }
    }
}
```

`my-app/schemas/music.sd`:

```
schema music {
    document music inherits items {
        field artist type string {
            indexing: summary | index
        }
    }
}
```

This is equivalent to:

`my-app/schemas/books.sd`:

```
schema books {
    document books {
        field title type string {
            indexing: summary | index
        }
        field author type string {
            indexing: summary | index
        }
    }
}
```

`my-app/schemas/music.sd`:

```
schema music {
    document music  {
        field title type string {
            indexing: summary | index
        }
        field artist type string {
            indexing: summary | index
        }
    }
}
```

Notes:
* Multiple inheritance and multiple levels of inheritance is supported.
* Inheriting a document type defined in another content cluster is allowed.
* Overriding fields defined in supertypes is not allowed.
* [Imported fields](reference/schema-reference.html#import-field)
  defined in supertypes are not inherited.

## Rank profile inheritance

Where fields define the document types, rank profiles define the computations over the documents.
Rank profiles can be inherited from rank-profiles defined in the same schema, or defined in another schema when this
document inherits the document defined in the schema where the rank profile is defined:

`my-app/schemas/items.sd`:

```
schema items {
    document items {
        field title type string {
            indexing: summary | index
        }
    }

    rank-profile items_ranking_base {
        function title_score() {
            expression: fieldLength(title)
        }
        first-phase {
            expression: title_score
        }
        summary-features {
            title_score
        }
    }
}
```

`my-app/schemas/books.sd`:

```
schema books {
    document books inherits items {
        field author type string {
            indexing: summary | index
        }
    }

    rank-profile items_ranking inherits items_ranking_base {}

    rank-profile items_subschema_ranking inherits items_ranking_base {
        first-phase {
            expression: title_score + fieldMatch(author)
        }
        summary-features inherits items_ranking_base {
            fieldMatch(author)
        }
    }
}
```

`my-app/schemas/music.sd`:

```
schema music {
    document music inherits items {
        field artist type string {
            indexing: summary | index
        }
    }

    rank-profile items_ranking inherits items_ranking_base {}

    rank-profile items_subschema_ranking inherits items_ranking_base {
        first-phase {
            expression: title_score + fieldMatch(artist)
        }
        summary-features inherits items_ranking_base {
            fieldMatch(artist)
        }
    }
}
```
*items_ranking* can be considered the "base" ranking.
Pro-tip: Set this as the *default* rank profile
by modifying the default [query profile](query-profiles.html):

`my-app/search/query-profiles/default.xml`:

```
<query-profile id="default">
    <field name="ranking.profile">items_ranking</field>
</query-profile>
```

Queries using *ranking.profile=default* will then use the first-phase ranking defined in *items.sd*.

Another way to inherit behavior is to override the first-phase ranking in the sub-schemas,
still using functions defined in the super-schema (e.g. *title_score*).

### Summary features

[Summary-features](reference/schema-reference.html#summary-features) and
[match-features](reference/schema-reference.html#match-features)
are rank features computed during ranking,
to be included in [results](reference/default-result-format.html).
These features can be inherited from parent rank profiles - the
above example uses `inherits` to include scores from
features in super- and sub-schema - example result:

```
{% highlight json %}
"summaryfeatures": {
    "fieldMatch(author)": 0,
    "rankingExpression(title_score)": 4
}
{% endhighlight %}
```

In the examples above, both *books* and *music* schemas implement rank profiles
with same names (e.g. *items_subschema_ranking*),
so they can be used in queries spanning both.
If a query's rank profile can not be found in a given schema,
Vespa's default rank profile [nativerank](nativerank.html) is used.

[Inputs](reference/schema-reference.html#inputs) to a rank profile are automatically inherited from
the parent rank profile. If a new inputs block is defined in a child rank profile, those inputs will be
added cumulatively to those defined in the parent.

## Document summary inheritance

[Document summaries](document-summaries.html) can inherit others defined in the same
or an inherited schema.

`my-app/schemas/books.sd`:

```
schema books {
    document books {
        field title type string {
            indexing: summary | index
        }
        field author type string {
            indexing: summary | index
        }
    }

    document-summary items_summary_tiny {
        summary title {}
    }

    document-summary items_summary_full inherits items_summary_tiny {
        summary author {}
    }
}
```
