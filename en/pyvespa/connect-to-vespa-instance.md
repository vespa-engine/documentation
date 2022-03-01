---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Connect to a running Vespa instance"
redirect_from:
- /documentation/pyvespa/connect-to-vespa-instance.html
---

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vespa-engine/pyvespa/blob/master/docs/sphinx/source/connect-to-vespa-instance.ipynb)

This self-contained tutorial will show you how to connect to a pre-existing Vespa instance.
We will use the [https://cord19.vespa.ai/](https://cord19.vespa.ai/) app as an example.
You can run this tutorial yourself in Google Colab by clicking on the badge located at the top of the tutorial.

## Connect to a running Vespa application

We can connect to a running Vespa application by creating an instance of
[Vespa](https://pyvespa.readthedocs.io/en/latest/reference-api.html#vespa.application.Vespa) with the appropriate url.
The resulting `app` will then be used to communicate with the application.


```python
from vespa.application import Vespa

app = Vespa(url = "https://api.cord19.vespa.ai")
```

## Query the application

We have full flexibility to specify the request body based on the
[Vespa query language](../reference/query-api-reference.html).


```python
body = {
  'yql': 'select cord_uid, title, abstract from sources * where userQuery()',
  'hits': 5,
  'query': 'Is remdesivir an effective treatment for COVID-19?',
  'type': 'any',
  'ranking': 'bm25'
}
query_result = app.query(body)
```

## Inspect the query result

We can see the number of documents that were retrieved by Vespa:


```python
query_result.number_documents_retrieved
```




    268858



And the number of documents that were returned to us:


```python
len(query_result.hits)
```




    5



We can then retrieve specific information from the hit list through the `query_result.hits` or access the entire Vespa response through `query_result.json`.


```python
[hit["fields"]["cord_uid"] for hit in query_result.hits]
```




    ['2lwzhqer', '8n6eybze', '8n6eybze', '8art2tyj', 'oud5ioks']


