---
# Copyright Vespa.ai. All rights reserved.
title: "/document/v1 API guide"
---

Use the */document/v1/* API to read, write, update and delete documents.

Refer to the [document/v1 API reference](reference/document-v1-api-reference.html) for API details.
[Reads and writes](reads-and-writes.html) has an overview of alternative tools and APIs
as well as the flow through the Vespa components when accessing documents.
See [getting started](#getting-started) for how to work with the */document/v1/ API*.

Examples:

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| GET | |  |  | | --- | --- | | Get | ``` $ curl http://localhost:8080/document/v1/my_namespace/music/docid/love-id-here-to-stay ``` | | Visit | [Visit](visiting.html) all documents with given namespace and document type:  ``` $ curl http://localhost:8080/document/v1/namespace/music/docid ```  Visit all documents using continuation:  ``` $ curl http://localhost:8080/document/v1/namespace/music/docid?continuation=AAAAEAAAAAAAAAM3AAAAAAAAAzYAAAAAAAEAAAAAAAFAAAAAAABswAAAAAAAAAAA ```  Visit using a *selection*:  ``` $ curl http://localhost:8080/document/v1/namespace/music/docid?selection=music.genre=='blues' ```  Visit documents across all *non-global* document types and namespaces stored in content cluster `mycluster`:  ``` $ curl http://localhost:8080/document/v1/?cluster=mycluster ```  Visit documents across all *[global](reference/services-content.html#document)* document types and namespaces stored in content cluster `mycluster`:  ``` $ curl http://localhost:8080/document/v1/?cluster=mycluster&bucketSpace=global ```  Read about [visiting throughput](#visiting-throughput) below. | |
| POST | Post data in the [document JSON format](reference/document-json-format.html).   ``` $ curl -X POST -H "Content-Type:application/json" --data '   {       "fields": {           "artist": "Coldplay",           "album": "A Head Full of Dreams",           "year": 2015       }   }' \   http://localhost:8080/document/v1/mynamespace/music/docid/a-head-full-of-dreams ``` |
| PUT | Do a [partial update](partial-updates.html) for a document.   ``` $ curl -X PUT -H "Content-Type:application/json" --data '   {       "fields": {           "artist": {               "assign": "Warmplay"           }       }   }' \   http://localhost:8080/document/v1/mynamespace/music/docid/a-head-full-of-dreams ``` |
| DELETE | Delete a document by ID:   ``` $ curl -X DELETE http://localhost:8080/document/v1/mynamespace/music/docid/a-head-full-of-dreams ```  Delete all documents in the `music` schema:  ``` $ curl -X DELETE \   "http://localhost:8080/document/v1/mynamespace/music/docid?selection=true&cluster=my_cluster" ``` |

## Conditional writes

A *test-and-set* [condition](reference/document-select-language.html)
can be added to Put, Remove and Update operations. Example:

```
$ curl -X PUT -H "Content-Type:application/json" --data '
  {
      "condition": "music.artist==\"Warmplay\"",
      "fields": {
          "artist": {
              "assign": "Coldplay"
          }
      }
  }' \
  http://localhost:8080/document/v1/mynamespace/music/docid/a-head-full-of-dreams
```

{% include important.html content="Use *documenttype.fieldname* (e.g. music.artist) in the condition,
not only *fieldname*." %}

If the condition is not met, a *412 Precondition Failed* is returned:

```
{% highlight json %}
{
    "pathId": "/document/v1/mynamespace/music/docid/a-head-full-of-dreams",
    "id": "id:mynamespace:music::a-head-full-of-dreams",
    "message": "[UNKNOWN(251013) @ tcp/vespa-container:19112/default]: ReturnCode(TEST_AND_SET_CONDITION_FAILED, Condition did not match document nodeIndex=0 bucket=20000000000000c4 ) "
}
{% endhighlight %}
```

Also see the [condition reference](reference/document-json-format.html#test-and-set).

## Create if nonexistent

### Upserts

Updates to nonexistent documents are supported using
[create](reference/document-json-format.html#create).
This is often called an *upsert* — insert a document if it does not already exist, or update it if it exists.
An empty document is created on the content nodes, before the update is applied.
This simplifies client code in the case of multiple writers. Example:

```
$ curl -X PUT -H "Content-Type:application/json" --data '
  {
      "fields": {
          "artist": {
              "assign": "Coldplay"
          }
      }
  }' \
  http://localhost:8080/document/v1/mynamespace/music/docid/a-head-full-of-thoughts?create=true
```

### Conditional updates and puts with create

Conditional updates and puts can be combined with [create](reference/document-json-format.html#create).
This has the following semantics:
* If the document already exists, the condition is evaluated against the most recent document version available.
  The operation is applied if (and only if) the condition matches.
* Otherwise (i.e. the document does not exist or the newest document version is a tombstone),
  the condition is *ignored* and the operation is applied as if no condition was provided.

Support for conditional puts with create was added in Vespa 8.178.

```
$ curl -X POST -H "Content-Type:application/json" --data '
  {
      "fields": {
          "artist": {
              "assign": "Coldplay"
          }
      }
  }' \
  http://localhost:8080/document/v1/mynamespace/music/docid/a-head-full-of-thoughts?create=true&condition=music.title%3D%3D%27best+of%27
```

{% include warning.html content="If all existing replicas of a document are missing
when an operation with `\"create\": true` is executed, a new document will always be created.
This happens even if a condition has been given.
If the existing replicas become available later,
their version of the document will be overwritten by the newest update since it has a higher timestamp." %}
{% include note.html content="See [document expiry](documents.html#document-expiry)
for auto-created documents — it is possible to create documents that do not match the selection criterion." %}
{% include note.html content="Specifying *create* for a Put operation *without* a
condition has no observable effect, as unconditional Put operations will always write
a new version of a document regardless of whether it existed already." %}

## Data dump

To iterate over documents, use [visiting](visiting.html) — sample output:

```
{% highlight json %}
{
    "pathId": "/document/v1/namespace/doc/docid",
    "documents": [
        {
            "id": "id:namespace:doc::id-1",
            "fields": {
                "title": "Document title 1",
            }
        }
    ],
    "continuation": "AAAAEAAAAAAAAAM3AAAAAAAAAzYAAAAAAAEAAAAAAAFAAAAAAABswAAAAAAAAAAA"
}
{% endhighlight %}
```

Note the *continuation* token — use this in the next request for more data.
Below is a sample script dumping all data using [jq](https://stedolan.github.io/jq/) for JSON parsing.
It splits the corpus in 8 slices by default;
using a number of slices at least four times the number of container nodes is recommended for high throughput.
Timeout can be set lower for benchmarking.
(Each request has a maximum timeout of 60s to ensure progress is saved at regular intervals)

```
{% highlight sh %}
#!/bin bash
set -eo pipefail

if [ $# -gt 2 ]
then
  echo "Usage: $0 [number of slices, default 8] [timeout in seconds, default 31536000 (1 year)]"
  exit 1
fi

endpoint="https://my.vespa.endpoint"
cluster="db"
selection="true"
slices="${1:-8}"
timeout="${2:-31516000}"
curlTimeout="$((timeout > 60 ? 60 : timeout))"
url="$endpoint/document/v1/?cluster=$cluster&selection=$selection&stream=true&timeout=$curlTimeout&concurrency=8&slices=$slices"
auth="--key my-key --cert my-cert -H 'Authorization: my-auth'"
curl="curl -sS $auth"
start=$(date '+%s')
doom=$((start + timeout))

## auth can be something like auth='--key data-plane-private-key.pem --cert data-plane-public-cert.pem'
curl="curl -sS $auth"

function visit {
  sliceId="$1"
  documents=0
  continuation=""
  while
    printf -v filename "data-%03g-%012g.json.gz" $sliceId $documents
    json="$(eval "$curl '$url&sliceId=$sliceId$continuation'" | tee >( gzip > $filename ) | jq '{ documentCount, continuation, message }')"
    message="$(jq -re .message <<< $json)" && echo "Failed visit for sliceId $sliceId: $message" >&2 && exit 1
    documentCount="$(jq -re .documentCount <<< $json)" && ((documents += $documentCount))
    [ "$(date '+%s')" -lt "$doom" ] && token="$(jq -re .continuation <<< $json)"
  do
    echo "$documentCount documents retrieved from slice $sliceId; continuing at $token"
    continuation="&continuation=$token"
  done
  time=$(($(date '+%s') - start))
  echo "$documents documents total retrieved in $time seconds ($((documents / time)) docs/s) from slice $sliceId" >&2
}

for ((sliceId = 0; sliceId < slices; sliceId++))
do
  visit $sliceId &
done
wait
{% endhighlight %}
```

### Visiting throughput

Note that visit with selection is a linear scan over all the music documents
in the request examples at the start of this guide.
Each complete visit thus requires the selection expression to be evaluated for all documents.
Running concurrent visits with selections that match disjoint subsets of the document corpus
is therefore a poor way of increasing throughput,
as work is duplicated across each such visit.
Fortunately, the API offers other options for increasing throughput:
* Split the corpus into any number of smaller [slices](reference/document-v1-api-reference.html#slices),
  each to be visited by a separate, independent series of HTTP requests.
  This is by far the most effective setting to change,
  as it allows visiting through all HTTP containers simultaneously,
  and from any number of clients—either of which is
  typically the bottleneck for visits through */document/v1*.
  A good value for this setting is at least a handful per container.
* Increase backend [concurrency](reference/document-v1-api-reference.html#concurrency)
  so each visit HTTP response is promptly filled with documents.
  When using this together with slicing (above),
  take care to also stream the HTTP responses (below),
  to avoid buffering too much data in the container layer.
  When a high number of slices is specified, this setting may have no effect.
* [Stream](reference/document-v1-api-reference.html#stream) the HTTP responses.
  This lets you receive data earlier, and more of it per request, reducing HTTP overhead.
  It also minimizes memory usage due to buffering in the container,
  allowing higher concurrency per container.
  It is recommended to always use this, but the default is not to, due to backwards compatibility.

## Getting started

Pro-tip: It is easy to generate a `/document/v1` request by using the [Vespa CLI](vespa-cli.html),
with the `-v` option to output a generated `/document/v1` request - example:

```
$ vespa document -v ext/A-Head-Full-of-Dreams.json

  curl -X POST -H 'Content-Type: application/json'
  --data-binary @ext/A-Head-Full-of-Dreams.json
  http://127.0.0.1:8080/document/v1/mynamespace/music/docid/a-head-full-of-dreams

  Success: put id:mynamespace:music::a-head-full-of-dreams
```

See the [document JSON format](reference/document-json-format.html) for creating JSON payloads.

This is a quick guide into dumping random documents from a cluster to get started:

1. To get documents from a cluster,
   look up the content cluster name from the configuration,
   like in the [album-recommendation](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation/app/services.xml) example: `<content id="music" version="1.0">`.
2. Use the cluster name to start dumping document IDs (skip `jq` for full json):

   ```
   $ curl -s 'http://localhost:8080/document/v1/?cluster=music&wantedDocumentCount=10&timeout=60s' | \
     jq -r .documents[].id
   ```
```
   id:mynamespace:music::love-is-here-to-stay
   id:mynamespace:music::a-head-full-of-dreams
   id:mynamespace:music::hardwired-to-self-destruct
   ```

   `wantedDocumentCount` is useful to let the operation run longer to find documents,
   to avoid an empty result.
   This operation is a scan through the corpus,
   and it is normal to get empty result and the [continuation token](#data-dump).
3. Look up the document with id `id:mynamespace:music::love-is-here-to-stay`:

   ```
   $ curl -s 'http://localhost:8080/document/v1/mynamespace/music/docid/love-is-here-to-stay' | jq .
   ```
```
   {% highlight json %}
   {
       "pathId": "/document/v1/mynamespace/music/docid/love-is-here-to-stay",
       "id": "id:mynamespace:music::love-is-here-to-stay",
       "fields": {
           "artist": "Diana Krall",
           "year": 2018,
           "category_scores": {
               "type": "tensor(cat{})",
               "cells": {
                   "pop": 0.4000000059604645,
                   "rock": 0,
                   "jazz": 0.800000011920929
               }
           },
           "album": "Love Is Here To Stay"
       }
   }
   {% endhighlight %}
   ```
4. Read more about [document IDs](documents.html).

## Troubleshooting
* When troubleshooting documents not found using the query API,
  use [vespa visit](vespa-cli.html#documents) to export the documents.
  Then compare the `id` field with other user-defined `id` fields in the query.

  ```
  $ vespa visit
  ```
```
  {% highlight json %}
  {
      "id": "id:mynamespace:music::when-we-all-fall-asleep-where-do-we-go",
      "fields": {
          "artist": "Billie Eilish",
          "doc_id": 12345
      }
  }
  {% endhighlight %}
  ```

  Find more details on the components of the [document ID](documents.html#id-scheme).
* Document not found responses look like:

  ```
  $ curl http://127.0.0.1:8080/document/v1/mynamespace/music/docid/non-existing-doc
  ```
```
  {% highlight json %}
  {
    "pathId": "/document/v1/mynamespace/music/docid/non-existing-doc",
    "id": "id:mynamespace:music::non-existing-doc"
  }
  {% endhighlight %}
  ```

  This might look like an empty document, use `-v` for more output:

  ```
  $ curl -v http://127.0.0.1:8080/document/v1/mynamespace/music/docid/non-existing-doc

  > GET /document/v1/mynamespace/music/docid/non-existing-doc HTTP/1.1
  > Host: 127.0.0.1:8080
  > User-Agent: curl/7.88.1
  > Accept: */*
  >
  < HTTP/1.1 404 Not Found
  < Date: Fri, 26 May 2023 08:53:20 GMT
  < Content-Type: application/json;charset=utf-8
  < Content-Length: 108
  ```
```
  {% highlight json %}
  {
    "pathId": "/document/v1/mynamespace/music/docid/non-existing-doc",
    "id": "id:mynamespace:music::non-existing-doc"
  }
  {% endhighlight %}
  ```

  Observe the *404 Not Found*.
  Using the [Vespa CLI](vespa-cli.html#documents) is great for troubleshooting - use
  `-v` for verbose output, this prints an equivalent `curl` command:

  ```
  $ vespa document get -v id:mynamespace:music::non-existing-doc
  curl -X GET http://127.0.0.1:8080/document/v1/mynamespace/music/docid/non-existing-doc
  Error: Invalid document operation: 404 Not Found
  ```
```
  {% highlight json %}
  {
      "pathId": "/document/v1/mynamespace/music/docid/non-existing-doc",
      "id": "id:mynamespace:music::non-existing-doc"
  }
  {% endhighlight %}
  ```
* Query results can have results like:

  ```
  {% highlight json %}
  {
      "id": "index:mydoctype/3/399f8030300282ca93929939",
      "relevance": 0,
      "source": "test",
      "fields": {
          "sddocname": "testdoc",
          "myfield": 12
      }
  }
  {% endhighlight %}
  ```

  [Query result IDs](reference/default-result-format.html#id) are not the same as Document IDs.
  Use a separate field for the document ID, if needed.
* Delete *all* documents in *music* schema, with security credentials:

  ```
  $ curl -X DELETE \
    --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
    "http://localhost:8080/document/v1/mynamespace/music/docid?selection=true&cluster=my_cluster"
  ```

## Request size limit

Starting from version 8.577.16, Vespa returns 413 (Content too large) as a response to POST and PUT requests that are above the request size limit.
To avoid this, automatically check document size and truncate or split large documents before feeding.
For optimal performance, it is recommended to keep the document size below 10 MB.

## Backpressure

Vespa returns response code 429 (Too Many Requests) as a backpressure signal whenever client feed throughput exceeds system capacity.
Clients should implement retry strategies as described in the [HTTP best practices](cloud/http-best-practices.html) document.

Instead of implementing your own retry logic, consider using Vespa's feed clients which automatically handle retries and backpressure.
See the [feed command](vespa-cli.html#documents) of the Vespa CLI and the [vespa-feed-client](vespa-feed-client.html).

The `/document/v1` API includes a configurable operation queue that by default is tuned to balance latency, throughput and memory.
Applications can adjust this balance by overriding the parameters defined in the
[document-operation-executor](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/document-operation-executor.def)
config definition.

To optimize for higher throughput at the cost of increased latency and higher memory usage on the container,
increase any of the `maxThrottled` (maximum queue capacity in number of operations),
`maxThrottledAge` (maximum time in queue in seconds),
and `maxThrottledBytes` (maximum memory usage in bytes) parameters.
This allows the container to buffer more operations during temporary spikes in load,
reducing the number of 429 responses while increasing request latency.
Make sure to increase operation and client timeouts to accommodate for the increased latency.

See the [config definition](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/document-operation-executor.def) for a detailed explanation of each parameter.

Set the values to `0` for the opposite effect, i.e. to optimize for latency.
Operations will be dispatched directly,
and failed out immediately if the number of pending operations exceeds the dynamic window size of the document processing pipeline.
*Example: overriding the default value of all 3 parameters to `0`.*

```
<container id="feed" version="1.0">
    <document-api/>

    <config name="com.yahoo.document.restapi.document-operation-executor">
        <maxThrottled>0</maxThrottled>
        <maxThrottledAge>0</maxThrottledAge>
        <maxThrottledBytes>0</maxThrottledBytes>
    </config>

</container>
```

The effective operation queue configuration is logged when the container starts up, see below example.

```
INFO    container        Container.com.yahoo.document.restapi.resource.DocumentV1ApiHandler   Operation queue: max-items=256, max-age=3000 ms, max-bytes=100 MB
```

You can observe the state of the operation queue through the metrics
`httpapi_queued_operations`,
`httpapi_queued_bytes` and
`httpapi_queued_age`.

## Using number and group id modifiers

Do not use group or number modifiers with regular indexed mode document types.
These are special cases that only work as expected for document types
with [mode=streaming or mode=store-only](reference/services-content.html#document).
Examples:

|  |  |
| --- | --- |
| Get | Get a document in a group:  ``` $ curl http://localhost:8080/document/v1/mynamespace/music/number/23/some_key ```  ``` $ curl http://localhost:8080/document/v1/mynamespace/music/group/mygroupname/some_key ``` |
| Visit | Visit all documents for a group:  ``` $ curl http://localhost:8080/document/v1/namespace/music/number/23/ ```  ``` $ curl http://localhost:8080/document/v1/namespace/music/group/mygroupname/ ``` |
