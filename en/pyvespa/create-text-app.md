---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Create a text search application"
---
> Get started with the Python API to create and modify Vespa applications

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vespa-engine/pyvespa/blob/master/docs/sphinx/source/create-text-app.ipynb)

This self-contained tutorial will create a basic text search application from scratch based on the MS MARCO dataset,
similar to Vespa's [text search tutorials](../tutorials/text-search.html).
Visit [pyvespa reference API](https://pyvespa.readthedocs.io/en/latest/reference-api.html)
for more detailed information about the API presented here.

## Install pyvespa


```python
!pip install pyvespa
```

## Document

Create a `Document` instance containing the `Field`s to store in the app.
To simplify the application, include only the `id`, the `title` and the `body` of the MS MARCO documents.


```python
from vespa.package import Document, Field

document = Document(
    fields=[
        Field(name = "id", type = "string", indexing = ["attribute", "summary"]),
        Field(name = "title", type = "string", indexing = ["index", "summary"], index = "enable-bm25"),
        Field(name = "body", type = "string", indexing = ["index", "summary"], index = "enable-bm25")        
    ]
)
```

## Schema

The complete `Schema` will be named `msmarco` and contain the `Document` instance defined above.
The default `FieldSet` indicates that queries will look for matches
by searching both in the titles and bodies of the documents.
The default `RankProfile` indicates that all the matched documents will be ranked by the `nativeRank` expression
involving the title and the body of the matched documents.


```python
from vespa.package import Schema, FieldSet, RankProfile

msmarco_schema = Schema(
    name = "msmarco", 
    document = document, 
    fieldsets = [FieldSet(name = "default", fields = ["title", "body"])],
    rank_profiles = [RankProfile(name = "default", first_phase = "nativeRank(title, body)")]
)
```

## Application package

Once the `Schema` is defined, create the msmarco `ApplicationPackage`:


```python
from vespa.package import ApplicationPackage

app_package = ApplicationPackage(name = "msmarco", schema=[msmarco_schema])
```

At this point, `app_package` contains all the relevant information required
to create an MS MARCO text search app and is ready for deployment.
