---
# Copyright Vespa.ai. All rights reserved.
title: Data management and backup
category: cloud
---

This guide documents how to export data from a Vespa cloud application and how to do mass updates or removals.
See [cloning applications and data](https://cloud.vespa.ai/en/cloning-applications-and-data)
for how to copy documents from one application to another.

Prerequisite: Use the latest version of the [vespa](/en/vespa-cli.html)
command-line client.

## Export documents

To export documents, configure the application to export from,
then select zone, container cluster and schema - example:

```
$ vespa config set application vespa-team.vespacloud-docsearch.default

$ vespa visit --zone prod.aws-us-east-1c --cluster default --selection doc | head
```

Some of the parameters above are redundant if unambiguous.
Here, the application is set up using a template found in
[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
with multiple container clusters.
This example [visit](/en/content/visiting.html)
documents from the `doc` schema.

Use a [fieldset](/en/documents.html#fieldsets) to export document IDs only:

```
$ vespa visit --zone prod.aws-us-east-1c --cluster default --selection doc --field-set '[id]' | head
```

As the name implies, fieldsets are useful to select a subset of fields to export.
Note that this normally does not speed up the exporting process, as the same amount of data is read from the index.
The data transfer out of the Vespa application is smaller with fewer fields.

## Backup

Use the *visit* operations above to extract documents for backup.

To back up documents to your own Google Cloud Storage, see
[backup](https://github.com/vespa-engine/sample-apps/tree/master/examples/google-cloud/cloud-functions#backup---experimental) for a Google Cloud Function example.

## Feed

If a document feed is generated with `vespa visit` (above),
it is already in [JSON Lines](https://jsonlines.org/) feed-ready format by default:

```
$ vespa visit | vespa feed - -t $ENDPOINT
```

Find more examples in [cloning applications and data](https://cloud.vespa.ai/en/cloning-applications-and-data).

A document export generated using [/document/v1](/en/document-v1-api-guide.html)
is slightly different from the .jsonl output from `vespa visit`
(e.g., fields like a continuation token are added).
Extract the `document` objects before feeding:

```
$ gunzip -c docs.gz | jq '.documents[]' | \
  vespa feed - -t $ENDPOINT
```

## Delete

To remove all documents in a Vespa deployment—or a selection of them—run a *deletion visit*.
Use the `DELETE` HTTP method, and fetch only the continuation token from the response:

```
#!/bin/bash

set -x

# The ENDPOINT must be a regional endpoint, do not use '*.g.vespa-app.cloud/'
ENDPOINT="https://vespacloud-docsearch.vespa-team.aws-us-east-1c.z.vespa-app.cloud"
NAMESPACE=open
DOCTYPE=doc
CLUSTER=documentation

# doc.path =~ "^/old/" -- all documents under the /old/ directory:
SELECTION='doc.path%3D~%22%5E%2Fold%2F%22'

continuation=""

while
  token=$( curl -X DELETE -s \
           --cert data-plane-public-cert.pem \
           --key data-plane-private-key.pem \
           "${ENDPOINT}/document/v1/${NAMESPACE}/${DOCTYPE}/docid?selection=${SELECTION}&cluster=${CLUSTER}&${continuation}" \
           | tee >( jq . > /dev/tty ) | jq -re .continuation )
do
  continuation="continuation=${token}"
done
```

Each request will return a response after roughly one minute—change this by specifying *timeChunk* (default 60).

To purge all documents in a document export (above),
generate a feed with `remove`-entries for each document ID, like:

```
$ gunzip -c docs.gz | jq '[ .documents[] | {remove: .id} ]' | head

[
  {
    "remove": "id:open:doc::open/documentation/schemas.html"
  },
  {
    "remove": "id:open:doc::open/documentation/securing-your-vespa-installation.html"
  },
```

Complete example for a single chunk:

```
$ gunzip -c docs.gz | jq '[ .documents[] | {remove: .id} ]' | \
  vespa feed - -t $ENDPOINT
```

## Update

To update all documents in a Vespa deployment—or a selection of them—run an *update visit*.
Use the `PUT` HTTP method, and specify a partial update in the request body:

```
#!/bin/bash

set -x

# The ENDPOINT must be a regional endpoint, do not use '*.g.vespa-app.cloud/'
ENDPOINT="https://vespacloud-docsearch.vespa-team.aws-us-east-1c.z.vespa-app.cloud"
NAMESPACE=open
DOCTYPE=doc
CLUSTER=documentation

# doc.inlinks == "some-url" -- the weightedset<string> inlinks has the key "some-url"
SELECTION='doc.inlinks%3D%3D%22some-url%22'

continuation=""

while
  token=$( curl -X PUT -s \
           --cert data-plane-public-cert.pem \
           --key data-plane-private-key.pem \
           --data '{ "fields": { "inlinks": { "remove": { "some-url": 0 } } } }' \
           "${ENDPOINT}/document/v1/${NAMESPACE}/${DOCTYPE}/docid?selection=${SELECTION}&cluster=${CLUSTER}&${continuation}" \
           | tee >( jq . > /dev/tty ) | jq -re .continuation )
do
  continuation="continuation=${token}"
done
```

Each request will return a response after roughly one minute—change this by specifying *timeChunk* (default 60).

## Using /document/v1/ api

To get started with a document export, find the *namespace* and *document type* by listing a few IDs.
Hit the [/document/v1/](/en/reference/document-v1-api-reference.html) ENDPOINT.
Restrict to one CLUSTER, see [content clusters](/en/reference/services-content.html):

```
$ curl \
  --cert data-plane-public-cert.pem \
  --key data-plane-private-key.pem \
  "$ENDPOINT/document/v1/?cluster=$CLUSTER"
```

For ID export only, use a [fieldset](/en/documents.html#fieldsets):

```
$ curl \
  --cert data-plane-public-cert.pem \
  --key data-plane-private-key.pem \
  "$ENDPOINT/document/v1/?cluster=$CLUSTER&fieldSet=%5Bid%5D"
```

From an ID, like *id:open:doc::open/documentation/schemas.html*, extract
* NAMESPACE: open
* DOCTYPE: doc

Example script:

```
#!/bin/bash

set -x

# The ENDPOINT must be a regional endpoint, do not use '*.g.vespa-app.cloud/'
ENDPOINT="https://vespacloud-docsearch.vespa-team.aws-us-east-1c.z.vespa-app.cloud"
NAMESPACE=open
DOCTYPE=doc
CLUSTER=documentation

continuation=""
idx=0

while
  ((idx+=1))
  echo "$continuation"
  printf -v out "%05g" $idx
  filename=${NAMESPACE}-${DOCTYPE}-${out}.data.gz
  echo "Fetching data..."
  token=$( curl -s \
           --cert data-plane-public-cert.pem \
           --key data-plane-private-key.pem \
           "${ENDPOINT}/document/v1/${NAMESPACE}/${DOCTYPE}/docid?wantedDocumentCount=1000&concurrency=4&cluster=${CLUSTER}&${continuation}" \
           | tee >( gzip > ${filename} ) | jq -re .continuation )
do
  continuation="continuation=${token}"
done
```

If only a few documents are returned per response, *wantedDocumentCount* (default 1, max 1024) can be
specified for a lower bound on the number of documents per response, if that many documents still remain.

Specifying *concurrency* (default 1, max 100) increases throughput, at the cost of resource usage.
This also increases the number of documents per response, and *could* lead to excessive memory usage
in the HTTP container when many large documents are buffered to be returned in the same response.
