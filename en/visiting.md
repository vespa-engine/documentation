---
# Copyright Vespa.ai. All rights reserved.
title: "Visiting"
redirect_from:
- /en/content/visiting.html
---

Visiting is a feature to efficiently get or process a set of documents, identified by a
[document selection expression](reference/document-select-language.html).

Visiting is often used to back up or migrate applications,
[cloning applications and data](https://cloud.vespa.ai/en/cloning-applications-and-data)
is a good guide for this.

Use the [Vespa CLI](vespa-cli.html) to run visit -
example, using the [quick start](vespa-quick-start.html):

```
$ vespa visit
```
```
{% highlight json %}
{
    "id": "id:mynamespace:music::love-is-here-to-stay",
    "fields": {
        "artist":"Diana Krall",
        "year":2018,
        "category_scores": {
            "type": "tensor(cat{})",
            "cells": {
                "pop": 0.4000000059604645,
                "rock": 0.0,
                "jazz": 0.800000011920929
            }
        },
        "album": "Love Is Here To Stay"
    }
}
...
{% endhighlight %}
```

Typically, the visit use cases are not time sensitive, like data reprocessing,
and document dump for backup and cluster clone -
[cloning applications and data](https://cloud.vespa.ai/en/cloning-applications-and-data)
is a good read for more details.

Visiting does not have snapshot isolation—it returns the state of documents as they
were when iterated over. Iteration order is implementation-specific.
See [the consistency documentation](content/consistency.html#read-consistency) for more details.

{% include note.html content='Due to the bucket iteration, visiting is normally a high-latency iteration.
Even an empty content cluster is pre-partitioned into many data buckets to enable scaling.
Dumping just one document requires iteration over all data buckets,
unless *location*-specific selections are used.
To test visiting performance, use larger data sets; do not extrapolate from small.
Use the [query API](query-api.html) or
[`vespa document get`](vespa-cli.html#documents)
for low latency operations on small result sets.' %}

See [request handling](#request-handling) for details on how visiting works.
Also see the internal [vespa-visit](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-visit) tool.
For programmatic access, see the [visitor session API](document-api-guide.html#visitorsession).

## Visiting from pyvespa

The [pyvespa library](https://vespa-engine.github.io/pyvespa/reads-writes.html#visiting)
provides a convenient Python interface for visiting documents.

## Data export

Export data to stdout:

```
$ vespa visit
```

To export a subset, `--slices 100 --slice-id 0` exports 1% of the corpus by efficiently iterating
over only 1/100th of the data space.
For a given number of `--slices`,
it's possible to visit the entire corpus (possibly in parallel) with non-overlapping output
by visiting with all `--slice-id` values from (and including) 0 up to (and excluding) `--slices`:

```
$ vespa visit --slices 100 --slice-id 0
```

{% include note.html content='If the application has
[global document types](reference/services-content.html#document),
use `--bucket-space global` to visit these documents.
By default, visiting only iterates over non-global documents.' %}

### Performance note: feeding data exported via visiting

Vespa uses hashing to distribute documents pseudo-randomly across many
[buckets](/en/content/buckets.html). The operations in an incoming document stream are
expected to be distributed evenly across both the set of all buckets and the content nodes
storing them. This parallelizes the load and efficiently utilizes the hardware resources in the cluster.

Visiting iterates over the buckets in the cluster, returning all documents stored in
a bucket before moving on to the next bucket (often processing many buckets in parallel).
As a consequence there's a direct correlation between the internal document-to-bucket
distribution and the document output ordering of the visiting process.

If the output of visiting is fed directly back into a content cluster, this correlation
means that the stream of documents is no longer uniformly distributed across buckets and/or
content nodes. Prior to Vespa 8.349 this is likely to greatly reduce feeding performance due
to increased contention around backend bucket-level write locks and indexing threads. Vespa
8.349 and beyond contains optimizations that bring re-feeding performance much closer to
that of initial feeding.

A simple strategy to avoid this problem is to *shuffle* the visiting output prior to
re-feeding it. This removes any correlation between feed operations and the underlying
data distribution.

## Selection

To select (i.e. filter) which documents to visit, use a
[document selection expression](reference/document-select-language.html).
See the [Vespa CLI cheat sheet](vespa-cli.html#cheat-sheet) for more examples.

```
$ vespa visit --selection "id = 'id:mynamespace:music::love-is-here-to-stay'"
$ vespa visit --selection "year = 2018"
```

## Fields

To select which fields to output, use a [fieldset](documents.html#fieldsets).
See [examples](vespa-cli.html#documents) - common use cases are using a comma-separated list of fields
or the *[document]* / *[all]* shorthand.

```
$ vespa visit --field-set=[all]
$ vespa visit --field-set=music:id,year
```

## Timestamp ranges

Both the [Document V1 API](reference/document-v1-api-reference.html)
and the [Vespa CLI](vespa-cli.html) have options for returning documents
last modified within a particular timestamp range.
Either—or both—of the *from* and *to* parts of the requested timestamp range
can be specified:
* For Document V1, specify the range using the `fromTimestamp` and
  `toTimestamp` HTTP request parameters (in microseconds).* For `vespa visit`, specify the range using `--from` and
    `--to` (in seconds).

Setting a timestamp range is only a *filter* on the document set that would otherwise
be returned by a visitor without a timestamp range. It does *not* imply snapshot isolation.
The returned set of documents may be affected by concurrent modifications to documents, as any
modification updates the document timestamp.

## Reprocessing

Reprocessing is used to solve these use cases:
* To change the document type used in ways that will not be
  backward compatible, define a new type, and reprocess to change all
  the existing documents.
* Document identifiers can be changed to a new scheme.
* Search documents can be reindexed after indexing steps have been changed.

This example illustrates how one can identify a subset of the
documents in a content cluster, reprocess these, and write them back.
It is assumed that a Vespa cluster is set up, with data.

### 1. Set up a document reprocessing cluster

This example document processor:
* deletes documents with an *artist* field whose value contains *Metallica*
* uppercases *title* field values of all other documents

```
{% highlight java %}
import com.yahoo.docproc.Arguments;
import com.yahoo.docproc.DocumentProcessor;
import com.yahoo.docproc.Processing;
import com.yahoo.docproc.documentstatus.DocumentStatus;
import com.yahoo.document.DocumentOperation;
import com.yahoo.document.DocumentPut;
import com.yahoo.document.Document;

/**
 * Example of using a document processor will modify and/or delete
 * documents in the context of a reprocessing use case.
 */
public class ReProcessor extends DocumentProcessor {
    private String deleteFieldName;
    private String deleteRegex;
    private String uppercaseFieldName;

    public ReProcessor() {
        deleteFieldName = "artist";
        deleteRegex = ".*Metallica.*";
        uppercaseFieldName = "title";
    }

    public Progress process(Processing processing) {
        Iterator it = processing.getDocumentOperations().iterator();
        while (it.hasNext()) {
            DocumentOperation op = it.next();
            if (op instanceof DocumentPut) {
                Document doc = ((DocumentPut) op).getDocument();

                // Delete the current document if it matches:
                String deleteValue = (String) doc.getValue(deleteFieldName);
                if (deleteValue != null) {
                    if (deleteValue.matches(deleteRegex)) {
                        it.remove();
                        continue;
                    }
                }

                // Uppercase the other field:
                String uppercaseValue = doc.getValue(uppercaseFieldName).toString();
                if (uppercaseValue != null) {
                    doc.setValue(uppercaseFieldName, uppercaseValue.toUpperCase());
                }
            }
        }
        return Progress.DONE;
    }
}
{% endhighlight %}
```

To compile this processor, see the [Developer Guide](developer-guide.html).
For more information on document processing, refer
to [Document processor Development](document-processing.html).
After having changed the Vespa setup, reload config:

```
$ vespa deploy music
```

Restart nodes as well to activate.

### 2. Select documents

Define a selection criteria for the documents to be reprocessed.
(To reprocess *all* documents, skip this).
For this example, assume all documents where the field *year* is greater than 1995.
The selection string *music.year > 1995* does this.

### 3. Set route

The visitor sends documents to a [Messagebus route](/en/operations-selfhosted/routing.html) - examples:
* **default** - Documents are sent to the *default*
  route.
* **indexing** - Documents are sent to *indexing*.
* **<clustername>/chain.<chainname>**:
  Documents are sent to the document processing chain *chainname* running in
  cluster *clustername*.

Assume you have a container cluster with id *reprocessing*
containing a docproc chain with id *reprocessing-chain*.
This example route sends documents from the content node,
into the document reprocessing chain, and ultimately, into indexing:

```
reprocessing/chain.reprocessing-chain indexing
```

Details: [Message Bus Routing Guide](/en/operations-selfhosted/routing.html).

### 4. Reprocess

Start reprocessing:

```
$ vespa-visit -v --selection "music AND music.year > 1995" \
  --datahandler "reprocessing/chain.reprocessing-chain indexing"
```

The '-v' option emits progress information on standard error.

## Analyzing field values

Use *visit* to list ids of documents meeting criteria like empty fields -
example, find unset or empty "name" field:

```
$ vespa visit \
    --pretty-json \
    --cluster default \
    --selection 'restaurant AND (restaurant.name == "" OR restaurant.name == null)' \
    --field-set "[id]"
```

Note the first part of the selection string "restaurant AND ..." -
this is to ensure that the selection restricts to the *restaurant* document type (i.e. schema).

Also see count and list [fields with NaN](/en/grouping.html#count-fields-with-nan).

## Request handling

In short, *visit* iterates over all, or a set of, [buckets](content/buckets.html)
and sends documents to (a set of) targets.
The target is normally the visit client
(like [vespa-visit](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-visit)),
but can be set a set of targets that act like sinks for the documents -
see [vespa-visit-target](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-visit-target).

### Client

If the selection criteria managed to map the visitor to a specific set of buckets,
these will be used when sending distributor visit requests.
If not, the visit client will iterate the entire bucket space,
typically at the minimum split-level required to decide correct distributor.

The distributors will receive the requests and look at what buckets it has
that are contained by the requested bucket.
If more than one, the distributor will only start a limited number of bucket visitors at the same time.
Once it has processed the first ones,
it will reply to the visitor client with the last bucket processed.

As all buckets have a natural order, the client can use the returned bucket as a progress counter.
Thus, after a distributor request has returned, the client knows one of the following:
* All buckets contained within the bucket sent have been visited
* All buckets contained within the bucket sent,
  up to this specific bucket in the order, have been visited
* No buckets existed that was contained within the requested bucket

The client can decide whether to visit in strict order,
allowing only one bucket to be pending at a time,
or whether to start visiting many buckets at a time, allowing great throughput.

### Distributor

The distributors receive visit requests from clients for a given bucket,
which may map to none, one or many buckets within the distributor.
It picks one or more of the first buckets in the order,
picks out one content node copy of each
and passes the request on to the content nodes.

Once all the content node requests have been responded to,
the distributor will reply to the client with the last bucket visited,
to be used as a progress counter.

Subsequent client requests to the distributor will have the progress counter set,
letting the distributor ignore all the buckets prior to that point in the ordering.

Bucket splitting and joining does not alter the ordering,
and does thus not affect visiting much as long as the buckets are consistently split.
If two buckets are joined, where the first one have already been visited,
a visit request has to be sent to the joined bucket.
The content layer use the progress counter to avoid revisiting documents already processed in the bucket.

If the distributor only starts one bucket visitor at a time,
it can ensure the visitor order is kept.
Starting multiple buckets at a time may improve throughput and decrease latency,
but progress tracking will be less fine-grained,
so a bit more documents may need to be revisited when continued after a failure.

### Content node

The content node receives visit requests for single buckets for which they store documents.
It may receive many in parallel, but their execution is independent of each other.

The visitor layer in the content node picks up the visit requests.
There it is assigned a visitor thread,
and an instance of the processor type is created for that visitor.
The processor will set up an iterator in the backend
and send one or more requests for documents to the backend.

The document selection specified in the visitor client is sent through to the backend,
allowing it to filter out unwanted data at the lowest level possible.

Once documents are retrieved from the backend, back up to the visitor layer,
the visit processor will process the data.

The default is one iterator request is pending to the backend at any time.
By sending many small iterator requests, having several pending at a time,
the processing may occur in parallel with the document fetching.

## Troubleshooting

### Not exporting all documents

Normally all documents share the same [bucket space](content/buckets.html#bucket-space)—documents
for multiple schemas are co-located.
When using [parent/child](parent-child.html), global documents are stored in a separate bucket space.
Use the [bucket-space](reference/document-v1-api-reference.html#bucketspace) parameter
to visit the `default` or `global` space.
This is a common problem when dumping all documents and dumped count is not the expected count.

### Visiting performance is poor

When visiting, all content nodes may push data to the visitor *client* in parallel.
Therefore, the client is often the bottleneck. Slow data processing implicitly slows down
the entire visiting process. In particular, large floating point tensor fields are very
expensive to render as JSON.

To verify if client-side rendering is the bottleneck,
run [vespa-visit](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-visit) with
your usual selection criteria and field set,
but add the `--nullrender` argument (available from Vespa 8.134).
This receives and processes documents as usual, but completely skips rendering.

If you are redirecting the output of visiting to any custom business logic (such as running
`jq` on the stream of documents), make sure you are not accidentally buffering up
data internally—this goes for both input and output. To verify if processing the visitor output
is the bottleneck, run visiting with `stdout` redirected to `/dev/null`
and compare the time taken.

If the client is not the bottleneck, it is possible visiting performance is limited by disk
performance. Non-attribute fields are not memory backed and must be fetched from disk when
evaluating selections. This includes document IDs, which must always be returned for matching
documents. To see if any fields are particularly expensive to fetch or return, run visiting
with a selection and/or field set that does *not* include potentially expensive fields.

### Visitor operations are hanging

A visit operation might stall/hang if the content cluster is in an inconsistent
state—replicas are still merging between nodes.

### Handshake failed

Running vespa visit via the [/document/v1](document-v1-api-guide.html) API:

```
[HANDSHAKE_FAILED @ localhost]: An error occurred while resolving version of recipient(s)
[tcp/container0:37227/visitor-1-1682523227698 at tcp/container0:37227] from host 'content0'
```

The visit client in this case is the Vespa Container node with the /document/v1 interface.
A visit is a relatively long-lived operation -
the client starts a visitor operation on each Content node,
that connects back to the client (here `tcp/container0:37227`) to send data.
This might sound a bit odd - why connect back?

The idea is that results of the visitor operation might be pushed to multiple destinations for increased throughput -
see [request handling](#request-handling).
This explains why it connects back on a random port,
and why one cannot see the port in [vespa-model-inspect](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect) - it is temporary.

This also means, Vespa-nodes must be able to intercommunicate on all ports,
see [Docker containers](/en/operations-selfhosted/docker-containers.html).

Check [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
for an example - a Docker network is used for all containers - also see "network" in
[docker-compose.yaml](https://github.com/vespa-engine/sample-apps/blob/master/examples/operations/multinode-HA/docker-compose.yaml).

Another source of this error can be an unresponsive container instance, e.g. during overload.
