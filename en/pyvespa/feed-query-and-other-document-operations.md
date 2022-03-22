---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Document operations"
redirect_from:
- /documentation/pyvespa/feed-query-and-other-document-operations.html
---
> Feed, query and other document operations

## Install pyvespa

```python
pip install pyvespa
```

## Define your application package

This tutorial assumes that a [Vespa application package](https://pyvespa.readthedocs.io/en/latest/create-text-app.html)
was defined and stored in the variable `app_package`.
To illustrate this tutorial, we will use a basic question answering app from our gallery.


```python
from vespa.gallery import QuestionAnswering

app_package = QuestionAnswering()
```

## Deploy the application

It is required to deploy the application to follow the commands below.
Deploy the `app_package` using either [Docker](deploy-vespa-docker)
or [Vespa Cloud](https://pyvespa.readthedocs.io/en/latest/deploy-vespa-cloud.html).
The resulting Vespa connection should be stored in the `app` variable.
For example, to deploy using Docker:


```python
import os
from vespa.deployment import VespaDocker

vespa_docker = VespaDocker(
    port=8081, 
    disk_folder=os.getenv("DISK_FOLDER") # requires absolute path
)
app = vespa_docker.deploy(application_package=app_package)
```

    Waiting for configuration server.
    Waiting for configuration server.
    Waiting for configuration server.
    Waiting for configuration server.
    Waiting for configuration server.
    Waiting for application status.
    Waiting for application status.
    Waiting for application status.
    Finished deployment.


## Sample data

Download sample data required to follow this guide.


```python
import json, requests

sentence_data = json.loads(
    requests.get("https://data.vespa.oath.cloud/blog/qa/sample_sentence_data_100.json").text
)
list(sentence_data[0].keys())
```




    ['text', 'dataset', 'questions', 'context_id', 'sentence_embedding']



## Feed data

Prepare the data as a list of dicts having the `id` key holding a unique id of the data point
and the `fields` key holding a dict with the data fields required by the application.


```python
batch_feed = [
    {
        "id": idx, 
        "fields": sentence
    }
    for idx, sentence in enumerate(sentence_data)
]
```

Feed the batch to the desired schema, which in this case is the `sentence` schema.


```python
response = app.feed_batch(schema="sentence", batch=batch_feed)
```

## Query the application

We can query the application using the [Vespa Query Language](../query-language.html).


```python
result = app.query(body={
  'yql': 'select text from sources sentence  where userQuery()',
  'query': 'What is in front of the Notre Dame Main Building?',
  'type': 'any',
  'hits': 5,
  'ranking.profile': 'bm25'
})
```


```python
result.hits[0]
```




    {'id': 'index:qa_content/0/a87ff679ab8603b42a4ffde2',
     'relevance': 11.194862200830393,
     'source': 'qa_content',
     'fields': {'text': 'Immediately in front of the Main Building and facing it, is a copper statue of Christ with arms upraised with the legend "Venite Ad Me Omnes".'}}



## Other document operations

### Get data

Get the sentences with ids = 0, 1 and 2.


```python
batch = [{"id": 0}, {"id": 1}, {"id": 2}]
response = app.get_batch(schema="sentence", batch=batch)
```

It is possible to inspect each of the Vespa responses through the `json` attribute, e.g. `response[0].json`.


```python
response
```




    [<vespa.io.VespaResponse at 0x121856f70>,
     <vespa.io.VespaResponse at 0x121c1dbb0>,
     <vespa.io.VespaResponse at 0x1218871c0>]



### Update data

To update a data point, it is required to inform the `id` of the data to be updated and the `fields` to be updated.
Optionally, we can choose to `create` the data point if it does not exist.


```python
batch_update = [
    {
        "id": 0,                               # data_id
        "fields": {"text": "this is a test"},  # fields to be updated
        "create": False                        # Optional. Create data point if not exist, default to False.
        
    }
]
```


```python
response = app.update_batch(schema="sentence", batch=batch_update)
```

### Delete data

Delete the sentences with ids = 0, 1 and 2.


```python
batch = [{"id": 0}, {"id": 1}, {"id": 2}]
response = app.delete_batch(schema="sentence", batch=batch)
```
