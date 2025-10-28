---
# Copyright Vespa.ai. All rights reserved.
title: Migrating from Elasticsearch
category: cloud
---

This is a guide for how to move data from Elasticsearch to Vespa.
By the end of this guide you will have exported documents from Elasticsearch,
generated a deployable Vespa application package and tested this with documents and queries.

{% include pre-req.html extra-reqs='- Linux, macOS or Windows 10 Pro on x86_64 or arm64,
  with Podman or [Docker](https://docs.docker.com/engine/install/) installed.
  See [Docker Containers](/en/operations-selfhosted/docker-containers.html)
  for system limits and other settings.
' %}

To get started, [sign up](https://vespa.ai/free-trial/) to get an endpoint to deploy to.
Set the *tenant name* from the signup:

```
$ export TENANT_NAME=vespa-team    # Replace with your tenant name
```

Alternatively, [test with local deployment](#test-with-local-deployment).

## Feed a sample Elasticsearch index

This section sets up an index with 1000 sample documents using
[getting-started-index](https://www.elastic.co/guide/en/elasticsearch/reference/7.9/getting-started-index.html).
Skip this part if you already have an index.
Wait for Elasticsearch to start:

```
$ docker network create --driver bridge esnet

$ docker run -d --rm --name esnode --network esnet -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" \
  docker.elastic.co/elasticsearch/elasticsearch:7.10.2

$ while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' localhost:9200)" != "200" ]]; do sleep 1; echo 'waiting ...'; done
```

Download test data, and feed it to the Elasticsearch instance:

```
$ curl 'https://raw.githubusercontent.com/elastic/elasticsearch/7.10/docs/src/test/resources/accounts.json' \
  > accounts.json

$ curl -H "Content-Type:application/json" --data-binary @accounts.json 'localhost:9200/bank/_bulk?pretty&refresh'
```

Verify that the index has 1000 documents:

```
$ curl 'localhost:9200/_cat/indices?v'
```

## Export documents from Elasticsearch

This guide uses [ElasticDump](https://github.com/elasticsearch-dump/elasticsearch-dump)
to export the index contents and the index mapping.
Export the documents and mappings, then delete the Docker network and the Elasticsearch container:

```
$ docker run --rm --name esdump --network esnet -v "$PWD":/dump -w /dump elasticdump/elasticsearch-dump \
  --input=http://esnode:9200/bank --output=bank_data.json --type=data

$ docker run --rm --name esdump --network esnet -v "$PWD":/dump -w /dump elasticdump/elasticsearch-dump \
  --input=http://esnode:9200/bank --output=bank_mapping.json --type=mapping

$ docker rm -f esnode && docker network remove esnet
```

## Generate Vespa documents and Application Package

[ES_Vespa_parser.py](https://github.com/vespa-engine/vespa/tree/master/config-model/src/main/python)
is provided for conversion of Elasticsearch data and index mappings to Vespa data and configuration.
It is a basic script with minimal error checking -
it is designed for a simple export, modify this as needed for your application's needs.
Generate Vespa documents and configuration:

```
$ curl 'https://raw.githubusercontent.com/vespa-engine/vespa/master/config-model/src/main/python/ES_Vespa_parser.py' \
  > ES_Vespa_parser.py

$ python3 ./ES_Vespa_parser.py --application_name bank bank_data.json bank_mapping.json
```

This generates documents in *documents.json*
(see [JSON format](/en/reference/document-json-format.html))
where each document has IDs like this `id:bank:_doc::1`.
It also generates a *bank* folder with an [application package](/en/application-packages.html):

```
/bank
      │
      ├── documents.json
      ├── hosts.xml
      ├── services.xml
      └── /schemas
            └── _doc.sd
```

Enter the application package directory:

```
$ cd bank
```

## Deploy

Install [Vespa CLI](/en/vespa-cli.html).
In this example we use [Homebrew](https://brew.sh/),
you can also download from [GitHub](https://github.com/vespa-engine/vespa/releases):

```
$ brew install vespa-cli
```

Configure for Vespa Cloud deployment, log in and add credentials:

```
$ vespa config set target cloud
$ vespa config set application $TENANT_NAME.myapp.default
```
```
$ vespa auth login
```
```
$ export VESPA_CLI_HOME=$PWD/.vespa TMPDIR=$PWD/.tmp
$ mkdir -p $TMPDIR
$ vespa config set target cloud
$ vespa config set application vespa-team.migration
$ export VESPA_CLI_API_KEY="$(echo "$VESPA_TEAM_API_KEY" | openssl base64 -A -a -d)"
```
```
$ vespa auth cert
```

Also see [getting started](getting-started) guide.
Deploy the application package:

```
$ vespa deploy --wait 300
```

Index the documents exported from Elasticsearch:

```
$ vespa feed documents.json
```

## Interfacing with Vespa

Export all documents:

```
$ vespa visit
```

Get a document:

```
$ vespa document get id:bank:_doc::1
```

Count documents, find `"totalCount":1000` in the output:

```
$ vespa query 'select * from _doc where true'
```

Run a simple query against the *firstname* field:

```
$ vespa query 'select firstname,lastname from _doc where firstname contains "amber"'
```

## Next steps

Review the differences in document records, Vespa to the right:

|  |  |
| --- | --- |
| ``` {     "_index": "bank",     "_type": "_doc",     "_id": "1",     "_score": 1,     "_source": {       "account_number": 1,       "balance": 39225,       "firstname": "Amber",       "lastname": "Duke",       "age": 32,       "gender": "M",       "address": "880 Holmes Lane",       "employer": "Pyrami",       "email": "amberduke@pyrami.com",       "city": "Brogan",       "state": "IL"     } } ``` | ``` {      "put": "id:bank:_doc::1",       "fields": {       "account_number": 1,       "balance": 39225,       "firstname": "Amber",       "lastname": "Duke",       "age": 32,       "gender": "M",       "address": "880 Holmes Lane",       "employer": "Pyrami",       "email": "amberduke@pyrami.com",       "city": "Brogan",       "state": "IL"     } } ``` |

The [id](/en/documents.html#document-ids) field
`id:bank:_doc::1` is composed of:
* namespace: `bank`
* schema: `_doc`
* id: `1`

Read more in [Documents](/en/documents.html) and
[Schemas](/en/schemas.html).
The schema is the key Vespa configuration file where field types
and [ranking](/en/ranking.html) are configured.
The schema (found in `schemas/_doc.sd`) also has
[indexing](/en/schemas.html#indexing) settings, example:

```
search _doc {
    document _doc {
        field account_number type long {
            indexing: summary | attribute
        }
        field address type string {
            indexing: summary | index
        }
        ...
    }
}
```

These settings impact both performance and how fields are matched.
For example, the *account_number* above is using the *attribute* keyword,
which makes the field available for [sorting](/en/reference/sorting.html),
[ranking](/en/ranking.html), [grouping](/en/grouping.html),
but which by default does not have data structures for fast search.
Read more in [attributes](/en/attributes.html) and
[practical search performance guide](/en/performance/practical-search-performance-guide.html).

## Test with local deployment

To run the steps above, using a local deployment,
follow the steps in the [quickstart](/en/vespa-quick-start.html)
to start a local container running Vespa.
Then, deploy the application package from the *bank* folder.
