---
# Copyright Vespa.ai. All rights reserved.
title: "Documents"
---

Vespa models data as *documents*.
A document has a string identifier, set by the application, unique across all documents.
A document is a set of [key-value pairs](document-api-guide.html).
A document has a schema (i.e. type),
defined in the [schema](schemas.html).

When configuring clusters, a [documents](reference/services-content.html#documents)
element sets what document types a cluster is to store.
This configuration is used to configure the garbage collector if it is enabled.
Additionally, it is used to define default routes for documents sent into the application.
By default, a document will be sent to all clusters having the document type defined.
Refer to [routing](/en/operations-selfhosted/routing.html) for details.

Vespa uses the document ID to distribute documents to nodes.
From the document identifier, the content layer calculates a numeric location.
A bucket contains all the documents,
where a given amount of least-significant bits of the location are all equal.
This property is used to enable co-localized storage of documents -
read more in [buckets](content/buckets.html) and
[content cluster elasticity](elasticity.html).

Documents can be [global](reference/services-content.html#document),
see [parent/child](parent-child.html).

## Document IDs

The document identifiers are URIs, represented by a string,
which must conform to a defined URI scheme for document identifiers.
The document identifier string may only contain *text characters*,
as defined by `isTextCharacter` in
[com.yahoo.text.Text](https://github.com/vespa-engine/vespa/blob/master/vespajlib/src/main/java/com/yahoo/text/Text.java).

### id scheme

Vespa currently has only one defined scheme, the *id scheme*:
`id:<namespace>:<document-type>:<key/value-pair>:<user-specified>`

{% include note.html content='
An example mapping from ID to the URL used in [/document/v1/](document-v1-api-guide.html) is from
`id:mynamespace:mydoctype::user-defined-id` to
`/document/v1/mynamespace/mydoctype/docid/user-defined-id`.
Find examples and tools in [troubleshooting](document-v1-api-guide.html#document-not-found).' %}

Find examples in the [/document/v1/](document-v1-api-guide.html) guide.

| Part | Required | Description |
| --- | --- | --- |
| namespace | Yes | Not used by Vespa, see [below](#namespace). |
| document-type | Yes | Document type as defined in [services.xml](reference/services-content.html#document) and the [schema](reference/schema-reference.html). |
| key/value-pair | Optional | Modifiers to the id scheme, used to configure document distribution to [buckets](content/buckets.html#document-to-bucket-distribution). With no modifiers, the id scheme distributes all documents uniformly. The key/value-pair field contains one of two possible key/value pairs; **n** and **g** are mutually exclusive:  | n=*<number>* | Number in the range [0,2^63-1] - only for testing of abnormal bucket distributions | | g=*<groupname>* | The *groupname* string is hashed and used to select the storage location |  {% include important.html content='This is only useful for document types with [mode=streaming or mode=store-only](reference/services-content.html#document). Do not use modifiers for regular indexed document types.' %} See [streaming search](streaming-search.html). Using modifiers for regular indexed document will cause unpredictable feeding performance, in addition, search dispatch does not have support to limit the search to modifiers/buckets. |
| user-specified | Yes | A unique ID string. |

### Document IDs in search results

The full Document ID (as a string) will often contain redundant
information and be quite long; a typical value may look like
"id:mynamespace:mydoctype::user-specified-identifier" where only the
last part is useful outside Vespa. The Document ID is therefore not
stored in memory, and it **not always present** in
[search results](reference/default-result-format.html#id).
It is therefore recommended to put your own unique identifier
(usually the "user-specified-identifier" above) in a document field,
typically named "myid" or "shortid" or similar:

```
field shortid type string {
    indexing: attribute | summary
}
```

This enables using a
[document-summary](document-summaries.html) with only
in-memory fields while still getting the identifier you actually
care about. If the "user-specified-identifier" is just a simple
number you could even use "type int" for this field for minimal
memory overhead.

### Namespace

The namespace in document ids is useful when you have multiple
document collections that you want to be sure never end up with the
same document id. It has no function in Vespa beyond this, and can
just be set to any short constant value like for example "doc".
Consider also letting synthetic documents used for
testing use namespace "test" so it's easy to detect and remove
them if they are present outside the test by mistake.

Example - if feeding
* document A by `curl -X POST https:.../document/v1/first_namespace/my_doc_type/docid/shakespeare`
* document B by `curl -X POST https:.../document/v1/second_namespace/my_doc_type/docid/shakespeare`

then those will be separate documents, both searchable, with different document IDs.
The document ID differs not in the user specified part (this is `shakespeare` for both documents),
but in the namespace part (`first_namespace` vs `second_namespace`).
The full document ID for document A is `id:first_namespace:my_doc_type::shakespeare`.

The namespace has no relation to other configuration elsewhere, like in *services.xml* or in schemas.
It is just like the user specified part of each document ID in that sense.
Namespace can not be used in queries, other than as part of the full document ID.
However, it can be used for [document selection](reference/document-select-language.html),
where `id.namespace` can be accessed and compared to a given string, for instance.
An example use case is [visiting](visiting.html) a subset of documents.

## Fields

Documents can have fields, see the [schema reference](reference/schema-reference.html#field).

A field can not be defined with a default value.
Use a [choice ('||') indexing statement or a
[document processor](document-processing.html) to assign a default to
document put/update operations.](indexing.html#choice-example)

## Fieldsets

Use *fieldset* to limit the fields that are returned from a read operation,
like *get* or *visit* - see [examples](vespa-cli.html#documents).
Vespa may return more fields than specified if this does not impact performance.

{% include note.html content='Document field sets is a different thing than
[searchable fieldsets](reference/schema-reference.html#fieldset).' %}

There are two options for specifying a fieldset:
* Built-in fieldset
* Name of a document type, then a colon ":", followed by a comma-separated list of fields
  (for example `music:artist,song` to fetch two fields declared in `music.sd`)

Built-in fieldsets:

| Fieldset | Description |
| --- | --- |
| [all] | Returns all fields in the schema (generated fields included) and the document ID. |
| [document] | Returns original fields in the document, including the document ID. |
| [none] | Returns no fields at all, not even the document ID. *Internal, do not use* |
| [id] | Returns only the document ID |
| <document type>:[document] | {% include deprecated.html content="Use `[document]`"%} Same as `[document]` fieldset above: Returns only the original document fields (generated fields not included) together with the document ID. |

If a built-in field set is not used, a list of fields can be specified. Syntax:

```
<document type>:field1,field2,…
```

Example:

```
music:title,artist
```

## Document expiry

To auto-expire documents, use a [selection](reference/services-content.html#documents.selection) with [now](reference/indexing-language-reference.html#now).
Example, set time-to-live (TTL) for *music*-documents to one day, using a field called *timestamp*:

```
{% highlight xml %}



{% endhighlight %}
```

Note: The `selection` expression says which documents to *keep*, not which ones to delete.
The *timestamp* field must have a value in seconds since EPOCH:

```
field timestamp type long {
    indexing: attribute
    attribute {
        fast-access
    }
}
```

When `garbage-collection="true"`, Vespa iterates over the document space to purge expired documents.
Vespa will invoke the configured GC selection for each stored document once every
[garbage-collection-interval](reference/services-content.html#documents.selection) seconds.
It is unspecified when a particular document will be processed within the configured interval.

{% include important.html content="This is a best-effort garbage collection feature to conserve CPU and space.
Use query filters if it is important to exclude documents based on a criterion."%}
* Using a *selection* with *now* can have side effects
  when re-feeding or re-processing documents, as timestamps can be stale.
  A common problem is feeding with too old timestamps,
  resulting in no documents being indexed.
* Normally, documents that are already expired at write time are not persisted.
  When using [create](document-v1-api-guide.html#create-if-nonexistent)
  (Create if nonexistent), it is possible to create documents that are expired and will be removed in next cycle.
* Deploying a configuration where the selection string selects no documents
  will cause all documents to be garbage collected.
  Use [visit](visiting.html) to test the selection string.
  Garbage collected documents are not to be expected to be recoverable.
* The fields that are referenced in the selection expression should be attributes.
  Also, either the fields should be set with *"fast-access"* or the number of
  [searchable copies](reference/services-content.html#searchable-copies) in the content cluster should be the same as
  the [redundancy](reference/services-content.html#redundancy).
  Otherwise, the document selection maintenance will be slow
  and have a major performance impact on the system.
* [Imported fields](reference/schema-reference.html#import-field)
  can be used in the selection string to expire documents, but special care needs to be
  taken when using these.
  See [using imported fields in selections](reference/document-select-language.html#using-imported-fields-in-selections) for more information and restrictions.
* Document garbage collection is a low priority background operation that runs continuously
  unless preempted by higher priority operations.
  If the cluster is too heavily loaded by client feed operations, there's a risk of starving
  GC from running. To verify that garbage collection is not starved, check the
  [vds.idealstate.max_observed_time_since_last_gc_sec.average](operations/metrics.html)
  distributor metric.
  If it significantly exceeds `garbage-collection-interval` it is an indication that GC is starved.

To batch remove, set a selection that matches no documents, like *"not music"*

Use [vespa visit](visiting.html) to test the selection.
Dump the IDs of all documents that would be *preserved*:

```
{% highlight sh %}
$ vespa visit --selection 'music.timestamp > now() - 86400' --field-set "music.timestamp"
{% endhighlight %}
```

Negate the expression by wrapping it in a `not`
to dump the IDs of all the documents that would be *removed* during GC:

```
{% highlight sh %}
$ vespa visit --selection 'not (music.timestamp > now() - 86400)' --field-set "music.timestamp"
{% endhighlight %}
```

## Processing documents

To process documents, use [Document processing](document-processing.html).
Examples are enriching documents (look up data from other sources),
transform content (like linguistic transformations, tokenization),
filter data and trigger other events based on the input data.

See the sample app [album-recommendation-docproc](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing) for use of Vespa APIs like:
* [Document API](document-api-guide.html) -
  work on documents and fields in documents, and create unit tests using the Application framework
* [Document Processing](document-processing.html) -
  chain independent processors with ordering constraints

The sample app [vespa-documentation-search](https://github.com/vespa-cloud/vespa-documentation-search) has examples of processing PUTs or UPDATEs
(using [create-if-nonexistent](document-v1-api-guide.html#create-if-nonexistent)) of documents in
[OutLinksDocumentProcessor](https://github.com/vespa-cloud/vespa-documentation-search/blob/main/src/main/java/ai/vespa/cloud/docsearch/OutLinksDocumentProcessor.java).
It is also in introduction to using [multivalued fields](schemas.html#field)
like arrays, maps and tensors.
Use the [VespaDocSystemTest](https://github.com/vespa-cloud/vespa-documentation-search/blob/main/src/test/java/ai/vespa/cloud/docsearch/VespaDocSystemTest.java) to build code that feeds and tests an instance in the Vespa Developer Cloud / local Docker instance.

Both sample apps also use the Document API to GET/PUT/UPDATE other documents as part of processing,
using asynchronous [DocumentAccess](https://github.com/vespa-engine/vespa/blob/master/documentapi/src/main/java/com/yahoo/documentapi/DocumentAccess.java).
Use this as a starting point for applications that enrich data when writing.
