---
# Copyright Vespa.ai. All rights reserved.
title: "/document/v1 API reference"
---

This is the /document/v1 API reference documentation.
Use this API for synchronous [Document](../documents.html) operations to a Vespa endpoint -
refer to [reads and writes](../reads-and-writes.html) for other options.

The [document/v1 API guide](../document-v1-api-guide.html) has examples and use cases.

{% include note.html content='
Mapping from document IDs to /document/v1/ URLs is found in [document IDs](../documents.html#id-scheme) -
also see [troubleshooting](../document-v1-api-guide.html#troubleshooting).'%}

Some examples use *number* and *group*
[document id](../documents.html#document-ids) modifiers.
These are special cases that only work as expected for document types
with [mode=streaming or mode=store-only](services-content.html#document).
Do not use group or number modifiers with regular indexed mode document types.

## Configuration

To enable the API, add `document-api` in the serving container cluster -
[services.xml](services-container.html):

```
<services>
    <container>
        <document-api/>
```

## HTTP requests

| HTTP request | document/v1 operation | Description |
| --- | --- | --- |
| GET | *Get* a document by ID or *Visit* a set of documents by selection. | |
|  | Get | Get a document:  ``` /document/v1/<namespace>/<document-type>/docid/<document-id> /document/v1/<namespace>/<document-type>/number/<numeric-group-id>/<document-id> /document/v1/<namespace>/<document-type>/group/<text-group-id>/<document-id> ```  Optional parameters:  * [cluster](#cluster) * [fieldSet](#fieldset) * [timeout](#timeout) * [tracelevel](#tracelevel) |
|  | Visit | Iterate over and get all documents, or a [selection](#selection) of documents, in chunks, using [continuation](#continuation) tokens to track progress. Visits are a linear scan over the documents in the cluster.   ``` /document/v1/ ```  It is possible to specify namespace and document type with the visit path:  ``` /document/v1/<namespace>/<document-type>/docid ```  Documents can be grouped to limit accesses to a subset. A group is defined by a numeric ID or string — see [id scheme](../documents.html#id-scheme).  ``` /document/v1/<namespace>/<document-type>/group/<group> /document/v1/<namespace>/<document-type>/number/<number> ```  Mandatory parameters:  * [cluster](#cluster) -   Visits can only retrieve data from *one* content cluster,   so `cluster` **must** be specified   for requests at the root `/document/v1/` level, or when there is ambiguity.   This is required even if the application has only one content cluster.  Optional parameters:  * [bucketSpace](#bucketspace) -   Parent documents are [global](services-content.html#document)   and in the `global` [bucket space](#bucketspace).   By default, visit will visit non-global documents   in the `default` bucket space, unless document type is indicated,   and is a global document type. * [concurrency](#concurrency) -   Use to configure backend parallelism for each visit HTTP request. * [continuation](#continuation) * [fieldSet](#fieldset) * [selection](#selection) * [sliceId](#sliceid) * [slices](#slices) -   Split visiting of the document corpus across more than one HTTP   request—thus allowing the concurrent use of more HTTP containers—use the   `slices` and `sliceId` parameters. * [stream](#stream) -   It's recommended enabling streamed HTTP responses,   with the [stream](#stream) parameter,   as this reduces memory consumption and reduces HTTP overhead. * [timeout](#timeout) * [tracelevel](#tracelevel) * [wantedDocumentCount](#wanteddocumentcount) * [fromTimestamp](#fromtimestamp) * [toTimestamp](#totimestamp) * [includeRemoves](#includeRemoves) |
| POST | *Put* a given document, by ID, or *Copy* a set of documents by selection from one content cluster to another. | |
|  | Put | Write the document contained in the request body in JSON format.  ``` /document/v1/<namespace>/<document-type>/docid/<document-id> /document/v1/<namespace>/<document-type>/group/<group> /document/v1/<namespace>/<document-type>/number/<number> ```  Optional parameters:  * [condition](#condition) -   Use for conditional writes. * [route](#route) * [timeout](#timeout) * [tracelevel](#tracelevel) |
|  | Copy | Write documents visited in source [cluster](#cluster) to the [destinationCluster](#destinationcluster) in the same application. A [selection](#selection) is mandatory — typically the document type. Supported paths (see [visit](#visit) above for semantics):   ``` /document/v1/ /document/v1/<namespace>/<document-type>/docid/ /document/v1/<namespace>/<document-type>/group/<group> /document/v1/<namespace>/<document-type>/number/<number> ```  Mandatory parameters:  * [cluster](#cluster) * [destinationCluster](#destinationcluster) * [selection](#selection)  Optional parameters:  * [bucketSpace](#bucketspace) * [continuation](#continuation) * [timeChunk](#timechunk) * [timeout](#timeout) * [tracelevel](#tracelevel) |
| PUT | *Update* a document with the given partial update, by ID, or *Update where* the given selection is true. | |
|  | Update | Update a document with the partial update contained in the request body in the [document update JSON format](document-json-format.html#update).  ``` /document/v1/<namespace>/<document-type>/docid/<document-id> ```  Optional parameters:  * [condition](#condition) -   use for conditional writes * [create](#create) -   use to create empty documents when updating non-existent ones. * [route](#route) * [timeout](#timeout) * [tracelevel](#tracelevel) |
|  | Update where | Update visited documents in [cluster](#cluster) with the partial update contained in the request body in the [document update JSON format](document-json-format.html#update). Supported paths (see [visit](#visit) above for semantics):   ``` /document/v1/<namespace>/<document-type>/docid/ /document/v1/<namespace>/<document-type>/group/<group> /document/v1/<namespace>/<document-type>/number/<number> ```  Mandatory parameters:  * [cluster](#cluster) * [selection](#selection)  Optional parameters:  * [bucketSpace](#bucketspace) -   See [visit](#visit), `default` or `global` bucket space * [continuation](#continuation) * [stream](#stream) * [timeChunk](#timechunk) * [timeout](#timeout) * [tracelevel](#tracelevel) |
| DELETE | *Remove* a document, by ID, or *Remove where* the given selection is true. | |
|  | Remove | Remove a document.  ``` /document/v1/<namespace>/<document-type>/docid/<document-id> ```  Optional parameters:  * [condition](#condition) * [route](#route) * [timeout](#timeout) * [tracelevel](#tracelevel) |
|  | Delete where | Delete visited documents from [cluster](#cluster). Supported paths (see [visit](#visit) above for semantics):   ``` /document/v1/ /document/v1/<namespace>/<document-type>/docid/ /document/v1/<namespace>/<document-type>/group/<group> /document/v1/<namespace>/<document-type>/number/<number> ```  Mandatory parameters:  * [cluster](#cluster) * [selection](#selection)  Optional parameters:  * [bucketSpace](#bucketspace) -   See [visit](#visit), `default` or `global` bucket space * [continuation](#continuation) * [stream](#stream) * [timeChunk](#timechunk) * [timeout](#timeout) * [tracelevel](#tracelevel) |

## Request parameters

| Parameter | Type | Description |
| --- | --- | --- |
| bucketSpace | String | Specify the bucket space to visit. Document types marked as `global` exist in a separate *bucket space* from non-global document types. When visiting a particular document type, the bucket space is automatically deduced based on the provided type name. When visiting at a root `/document/v1/` level this information is not available, and the non-global ("default") bucket space is visited by default. Specify `global` to visit global documents instead. Supported values: `default` (for non-global documents) and `global`. |
| cluster | String | Name of [content cluster](../content/content-nodes.html) to GET from, or visit. |
| concurrency | Integer | Sends the given number of visitors in parallel to the backend, improving throughput at the cost of resource usage. Default is 1. When `stream=true`, concurrency limits the maximum concurrency, which is otherwise unbounded, but controlled by a dynamic throttle policy. {% include important.html content="Given a concurrency parameter of *N*, the worst case for memory used while processing the request grows linearly with *N*, unless [stream](#stream) mode is turned on. This is because the container currently buffers all response data in memory before sending them to the client, and all sent visitors must complete before the response can be sent." %} |
| condition | String | For test-and-set. Run a document operation conditionally — if the condition fails, a *412 Precondition Failed* is returned. See [example](../document-v1-api-guide.html#conditional-writes). |
| continuation | String | When visiting, a continuation token is returned as the `"continuation"` field in the JSON response, as long as more documents remain. Use this token as the `continuation` parameter to visit the next chunk of documents. See [example](../document-v1-api-guide.html#data-dump). |
| create | Boolean | If `true`, updates to non-existent documents will create an empty document to update. See [create if nonexistent](../document-v1-api-guide.html#create-if-nonexistent). |
| destinationCluster | String | Name of [content cluster](../content/content-nodes.html) to copy to, during a copy visit. |
| dryRun | Boolean | Used by the [vespa-feed-client](../vespa-feed-client.html) using `--speed-test` for bandwidth testing, by setting to `true`. |
| fieldSet | String | A [field set string](../documents.html#fieldsets) with the set of document fields to fetch from the backend. Default is the special `[document]` fieldset, returning all *document* fields. To fetch specific fields, use the name of the document type, followed by a comma-separated list of fields (for example `music:artist,song` to fetch two fields declared in `music.sd`). |
| route | String | The route for single document operations, and for operations generated by [copy](#copy), [update](#update-where) or [deletion](#delete-where) visits. Default value is `default`. See [routes](/en/operations-selfhosted/routing.html). |
| selection | String | Select only a subset of documents when [visiting](../visiting.html) — details in [document selector language](document-select-language.html). |
| sliceId | Integer | The slice number of the visit represented by this HTTP request. This number must be non-negative and less than the number of [slices](#slices) specified for the visit - e.g., if the number of slices is 10, `sliceId` is in the range [0-9]. {% include note.html content="If the number of distribution bits change during a sliced visit, the results are undefined. Thankfully, this is a very rare occurrence and is only triggered when adding content nodes." %} |
| slices | Integer | Split the document corpus into this number of independent slices. This lets multiple, concurrent series of HTTP requests advance the same logical visit independently, by specifying a different [sliceId](#sliceid) for each. |
| stream | Boolean | Whether to stream the HTTP response, allowing data to flow as soon as documents arrive from the backend. This obsoletes the [wantedDocumentCount](#wanteddocumentcount) parameter. The HTTP status code will always be 200 if the visit is successfully initiated. Default value is false. |
| format.tensors | String | Controls how tensors are rendered in the result.   | Value | Description | | --- | --- | | `short` | **Default**. Render the tensor value in an object having two keys, "type" containing the value, and "cells"/"blocks"/"values" ([depending on the type](document-json-format.html#tensor)) containing the tensor content.  Render the tensor content in the [type-appropriate short form](document-json-format.html#tensor). | | `long` | Render the tensor value in an object having two keys, "type" containing the value, and "cells" containing the tensor content.  Render the tensor content in the [general verbose form](document-json-format.html#tensor). | | `short-value` | Render the tensor content directly.  Render the tensor content in the [type-appropriate short form](document-json-format.html#tensor). | | `long-value` | Render the tensor content directly.  Render the tensor content in the [general verbose form](document-json-format.html#tensor). | |
| timeChunk | String | Target time to spend on one chunk of a copy, update or remove visit; with optional ks, s, ms or µs unit. Default value is 60. |
| timeout | String | Request timeout in seconds, or with optional ks, s, ms or µs unit. Default value is 180s. |
| tracelevel | Integer | Number in the range [0,9], where higher gives more details. The trace dumps which nodes and chains the document operation has touched. See [routes](/en/operations-selfhosted/routing.html). |
| wantedDocumentCount | Integer | Best effort attempt to not respond to the client before `wantedDocumentCount` number of documents have been visited. Response may still contain fewer documents if there are not enough matching documents left to visit in the cluster, or if the visiting times out. This parameter is intended for the case when you have relatively few documents in your cluster and where each visit request would otherwise process only a handful of documents.  The maximum value of `wantedDocumentCount` is bounded by an implementation-specific limit to prevent excessive resource usage. If the cluster has many documents (on the order of tens of millions), there is no need to set this value. |
| fromTimestamp | Integer | Filters the returned document set to only include documents that were last modified at a time point equal to or higher to the specified value, in microseconds from UTC epoch. Default value is 0 (include all documents). |
| toTimestamp | Integer | Filters the returned document set to only include documents that were last modified at a time point lower than the specified value, in microseconds from UTC epoch. Default value is 0 (sentinel value; include all documents). If non-zero, must be greater than, or equal to, `fromTimestamp`. |
| includeRemoves | Boolean | Include recently removed document IDs, along with the set of returned documents. By default, only documents currently present in the corpus are returned in the `"documents"` array of the response; when this parameter is set to `"true"`, documents that were recently removed, and whose tombstones still exist, are also included in that array, as entries on the form `{ "remove": "id:ns:type::foobar" }`. See [here](/en/operations-selfhosted/admin-procedures.html#data-retention-vs-size) for specifics on tombstones, including their lifetime. |

## Request body

POST and PUT requests must include a body for single document operations; PUT must
also include a body for [update where](#update-where) visits.
A field has a *value* for a POST and an *update operation object* for PUT.
Documents and operations use the [document JSON format](document-json-format.html).
The document fields must match the [schema](../schemas.html):

```
{% highlight json %}
{
    "fields": {
        "": ""
    }
}
{% endhighlight %}
```
```
{% highlight json %}
{
    "fields": {
        "": {
            "" : ""
        }
    }
}
{% endhighlight %}
```

The *update-operation* is most often `assign` - see
[update operations](document-json-format.html#update-operations) for the full list.
Values for `id` / `put` / `update` in the request body are silently dropped.
The ID is generated from the request path, regardless of request body data - example:

```
{% highlight json %}
{
    "put"   : "id:mynamespace:music::123",
    "fields": {
        "title": "Best of"
    }
}
{% endhighlight %}
```

This makes it easier to generate a feed file that can be used for both the
[vespa-feed-client](../vespa-feed-client.html) and this API.

## HTTP status codes

| Code | Description |
| --- | --- |
| 200 | OK. Attempts to remove or update a non-existent document also yield this status code (see 412 below). |
| 204 | No Content. Successful response to OPTIONS request. |
| 400 | Bad request. Returned for undefined document types + other request errors. See [13465](https://github.com/vespa-engine/vespa/issues/13465) for defined document types not assigned to a content cluster when using PUT. Inspect `message` for details. |
| 404 | Not found; the document was not found. This is only used when getting documents. |
| 405 | Method Not Allowed. HTTP method is not supported by the endpoint. Valid combinations are listed [above](#http-requests) |
| 412 | [condition](#condition) is not met. Inspect `message` for details. This is also the result when a condition if specified, but the document does not exist. |
| 413 | Content too large; used for POST and PUT requests that are above the [request size limit](../document-v1-api-guide.html#request-size-limit). |
| 429 | Too many requests; the document API has too many inflight feed operations, retry later. |
| 500 | Server error; an unspecified error occurred when processing the request/response. |
| 503 | Service unavailable; the document API was unable to produce a response at this time. |
| 504 | Gateway timeout; the document API failed to respond within the given (or default 180s) timeout. |
| 507 | Insufficient storage; the content cluster is out of memory or disk space. |

## HTTP response headers

| Header | Values | Description |
| --- | --- | --- |
| X-Vespa-Ignored-Fields | true | Will be present and set to 'true' only when a put or update contains one or more fields which were [ignored since they are not present in the document type](services-container.html#ignore-undefined-fields). Such operations will be applied exactly as if they did not contain the field operations referencing non-existing fields. References to non-existing fields in field *paths* are not detected. |

## Response format

Responses are in JSON format, with the following fields:

| Field | Description |
| --- | --- |
| pathId | Request URL path — always included. |
| message | An error message — included for all failed requests. |
| id | Document ID — always included for single document operations, including *Get*. |
| fields | The requested document fields — included for successful *Get* operations. |
| documents[] | Array of documents in a visit result — each document has the *id* and *fields*. |
| documentCount | Number of visited and selected documents. If [includeRemoves](#includeRemoves) is `true`, this also includes the number of returned removes (tombstones). |
| continuation | Token to be used to get the next chunk of the corpus - see [continuation](#continuation). |

GET can include a `fields` object if a document was found in a *GET* request

```
{% highlight json %}
{
    "pathId": "",
    "id":     "",
    "fields": {
    }
}
{% endhighlight %}
```

A GET *visit* result can include an array of `documents`
plus a [continuation](#continuation):

```
{% highlight json %}
{
    "pathId":    "",
    "documents": [
        {
            "id":     "",
            "fields": {
            }
        }
    ],
    "continuation": "",
    "documentCount": 123
}
{% endhighlight %}
```

A continuation indicates the client should make further requests to get more data, while lack of a
continuation indicates an error occurred, and that visiting should cease, or that there are no more documents.

A `message` can be returned for failed operations:

```
{% highlight json %}
{
    "pathId":  "",
    "message": ""
}
{% endhighlight %}
```
