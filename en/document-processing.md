---
# Copyright Vespa.ai. All rights reserved.
title: "Document Processing"
---

This document describes how to develop and deploy *Document Processors*,
often called *docproc* in this documentation.
Document processing is a framework to create [chains](components/chained-components.html)
of configurable [components](jdisc/container-components.html),
that read and modify document operations.

The input source splits the input data into logical units called [documents](documents.html).
A [feeder application](reads-and-writes.html) sends the documents into a document processing chain.
This chain is an ordered list of document processors.
Document processing examples range from language detection,
HTML removal and natural language processing to mail attachment processing,
character set transcoding and image thumbnailing.
At the end of the processing chain, extracted data will typically be set in some fields in the document.

The motivation for document processing is that code and configuration is atomically deployed,
as like all Vespa components.
It is also easy to build components that access data in Vespa as part of processing.

To get started, see the
[sample application](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing).
Read [indexing](indexing.html) to understand deployment and routing.
As document processors are chained components just like Searchers,
read [Searcher Development](searcher-development.html).
For reference, see the [Javadoc](https://javadoc.io/doc/com.yahoo.vespa/docproc),
and [services.xml](reference/services-docproc.html).

![Document Processing component in Vespa overview](/assets/img/vespa-overview-docproc.svg)

## Deploying a Document Processor

Refer to[album-recommendation-docproc](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing) to get started,
[LyricsDocumentProcessor.java](https://github.com/vespa-engine/sample-apps/blob/master/examples/document-processing/src/main/java/ai/vespa/example/album/LyricsDocumentProcessor.java) is a document processor example.
Add the document processor in [services.xml](reference/services-docproc.html),
and then add it to a [chain](#chains).
The type of processing done by the processor dictates what chain it should be part of:
* If it does general data-processing, such as populating some document fields from others,
  looking up data in external services, etc., it should be added to a general docproc chain.
* If, and only if, it does processing required for *indexing*
  - or requires this to have already been run —
  it should be added to a chain which inherits the *indexing* chain,
  and which is used for indexing by a content cluster.

An example that adds a general document processor to the "default" chain,
and an indexing related processor to the chain for a particular content cluster:

```
<services>
    <container version="1.0" id="default">
        <document-processing>
            <chain id="default">
                <documentprocessor id="ai.vespa.example.album.LyricsDocumentProcessor"
                                   bundle="albums-docproc"/>
            </chain>
            <chain id="my-indexing" inherits="indexing">
                <documentprocessor id="ai.vespa.example.album.PostIndexingDocumentProcessor"
                                   bundle="albums-docproc"/>
            </chain>
        </document-processing>
    </container>

    <content version="1.0" id="content">
        <documents>
            ...
            <document-processing cluster="default" chain="my-indexing" />
        </documents>
    </content>
</services>
```

The "default" chain, if it exists, is run by default, before the chain used for indexing.
The default indexing chain is called "indexing",
and *must* be inherited by any chain that is to replace it.

To run through any chain, specify a [route](/en/operations-selfhosted/routing.html) which includes the chain.
For example, the route `default/chain.my-chain indexing` would route feed operations
through the chain "my-chain" in the "default" container cluster, and then to the "indexing" hop,
which resolves to the specified indexing chain for each content cluster the document should be sent to.
More details can be found in [indexing](/en/operations-selfhosted/routing.html#document-processing):

## Document Processors

A document processor is a component extending `com.yahoo.docproc.DocumentProcessor`.
All document processors must implement `process()`:

```
public Progress process(Processing processing);
```

When the container receives a document operation,
it will create a new `Processing`, and add the `DocumentPut`s,
`DocumentUpdate`s or `DocumentRemove`s to the `List`
accessible through `Processing.getDocumentOperations()`.
The latter is useful also where a processing should be stopped
by doing `Processing.getDocumentOperations().clear()` before `Progress.DONE`,
say for blocklist use, to stop a `DocumentPut/Update`.

Furthermore, the call stack of the document processing chain in question will
be *copied* to `Processing.callStack()`,
so that document processors may freely modify the flow of control for this processing
without affecting all other processings going on.
After creation, the `Processing` is added to an internal queue.

A worker thread will retrieve a `Processing` from the input queue,
and run its document operations through its call stack.
A minimal, no-op document processor implementation is thus:

```
{% highlight java %}
import com.yahoo.docproc.*;

public class SimpleDocumentProcessor extends DocumentProcessor {
    public Progress process(Processing processing) {
        return Progress.DONE;
    }
}
{% endhighlight %}
```

The `process()` method should loop through all
document operations in `Processing.getDocumentOperations()`, do
whatever it sees fit to them, and return a `Progress`:

```
{% highlight java %}
public Progress process(Processing processing) {
    for (DocumentOperation op : processing.getDocumentOperations()) {
        if (op instanceof DocumentPut) {
            DocumentPut put = (DocumentPut) op;
            // TODO do something to 'put here
        } else if (op instanceof DocumentUpdate) {
            DocumentUpdate update = (DocumentUpdate) op;
            // TODO do something to 'update' here
        } else if (op instanceof DocumentRemove) {
            DocumentRemove remove = (DocumentRemove) op;
            // TODO do something to 'remove' here
        }
    }
    return Progress.DONE;
}
{% endhighlight %}
```

| Return code | Description |
| --- | --- |
| `Progress.DONE` | Returned if a document processor has successfully processed a `Processing`. |
| `Progress.FAILED` | Processing failed and the input message should return a *fatal* failure back to the feeding application, meaning that this application will not try to re-feed this document operation. Return an error message/reason by calling `withReason()`:  This result is represented as a `500 Internal Server Error` response in [Document v1](document-v1-api-guide.html).   ``` {% highlight java %} if (op instanceof DocumentPut) {     return Progress.FAILED.withReason("PUT is not supported"); } {% endhighlight %} ``` |
| `Progress.INVALID_INPUT` | Available since 8.584.  Processing failed due to invalid input, like a malformed document operation.  This result is represented as a `400 Bad Request` response in [Document v1](document-v1-api-guide.html). |
| `Progress.LATER` | See [execution model](#execution-model). The document processor wants to release the calling thread and be called again later. This is useful if e.g. calling an external service with high latency. The document processor may then save its state in the `Processing` and resume when called again later. There are no guarantees as to *when* the processor is called again with this `Processing`; it is simply appended to the back of the input queue.  By the use of `Progress.LATER`, this is an asynchronous model, where the processing of a document operation does not need to consume one thread for its entire lifespan. Note, however, that the document processors themselves are shared between all processing operations in a chain, and must thus be implemented [thread-safe](#state). |

| Exception | Description |
| --- | --- |
| `com.yahoo.docproc.TransientFailureException` | Processing failed and the input message should return a *transient* failure back to the feeding application, meaning that this application *may* try to re-feed this document operation. |
| `RuntimeException` | Throwing any other `RuntimeException` means same behavior as for `Progress.FAILED`. |

## Chains

The call stack mentioned above is another name for a *document processor chain*.
Document processor chains are a special case of the general
[component chains](components/chained-components.html) -
to avoid confusion some concepts are explained here as well.
A document processor chain is nothing more than a list of document processor instances,
having an id, and represented as a stack.
The document processor chains are typically not created for every processing,
but are part of the configuration.
Multiple ones may exist at the same time,
the chain to execute will be specified by the message bus destination of the incoming message.
The same document processor instance may exist in multiple document processor chains,
which is why the `CallStack` of the `Processing`
is responsible for knowing the next document processor to invoke in a particular message.

The execution order of the document processors in a chain are not ordered explicitly,
but by [ordering constraints](components/chained-components.html#ordering-components)
declared in the document processors or their configuration.

## Execution model

The Document Processing Framework works like this:

1. A thread from the message bus layer appends an incoming message to an internal priority queue,
   shared between all document processing chains configured on a node.
   The priority is set based on the message bus priority of the message.
   Messages of the same priority are ordered FIFO.
2. One worker thread from the docproc thread pool picks one message
   from the head of the queue, deserializes it, copies the call stack
   (chain) in question, and runs it through the document processors.
3. Processing finishes if **(a)** the document(s) has
   passed successfully through the whole chain,
   or **(b)** a document processor in the chain has
   returned `Progress.FAILED` or thrown an exception.
4. The same thread passes the message on to the message bus layer for
   further transport on to its destination.

There is a single instance of each document processor chain.
In every chain, there is a single instance of each document processor -
unless a chain is configured with multiple, identical document processors - this is a rare case.

As is evident from the model above,
multiple worker threads execute the document processors in a chain concurrently.
Thus, many threads of execution can be going through `process()` in a
document processor, at the same time.

This model places an important constraint on document processor classes:
*instance variables are not safe.*
They must be eliminated, or made thread-safe somehow.

Also see [Resource management](jdisc/container-components.html#resource-management),
use `deconstruct()` in order to not leak resources.

### Asynchronous execution

The execution model outlined above also shows one important restriction:
If a document processor performs any high-latency operation in its process() method,
a docproc worker thread will be occupied.
With all *n* worker threads blocking on an external resource,
throughput will be limited.
This can be fixed by saving the state in the Processing object,
and returning `Progress.LATER`.
A document processor doing a high-latency operation should use a pattern like this:

1. Check a self-defined context variable in Processing for status.
   Basically, *have we seen this Processing before?*
2. If no:
   1. We have been given a Processing object fresh off the network,
      we have not seen this before.
      Process it up until the high-latency operation.
   2. Start the high-latency operation (possibly in a separate thread).
   3. Save the state of the operation in a self-defined context variable in the Processing.
   4. Return `Progress.LATER`.
      This Processing is the appended to the back of the input queue,
      and we will be called again later.
3. If yes:
   1. Retrieve the reference that we set in our self-defined context variable in Processing.
   2. Is the high-latency operation done? If so, return `Progress.DONE`.
   3. Is it not yet done? Return `Progress.LATER` again.

As is evident, this will let the finite set of document processing threads to do more work at the same time.

## State

Any state in the document processor for the particular Processing
should be kept as local variables in the process method,
while state which should be shared by all Processings should be kept as member variables.
As the latter kind will be accessed by multiple threads at any one time,
the state of such member variables must be *thread-safe*.
This critical restriction is similar to those of e.g. the Servlet API.
Options for implementing a multithread-safe document processor with instance variables:

1. Use immutable (and preferably final) objects:
   they never change after they are constructed;
   no modifications to their state occurs after the DocumentProcessor constructor returns.
2. Use a single instance of a thread-safe class.
3. Create a single instance and synchronize access to it across all threads
   (but this will severely limit scalability).
4. Arrange for each thread to have its own instance, e.g. with a `ThreadLocal`.

### Processing Context Variables

`Processing` has a map `String -> Object`
that can be used to pass information between document processors.
It is also useful when using `Progress.LATER` to save the state of a processing - see
[Processing.java](https://github.com/vespa-engine/vespa/blob/master/docproc/src/main/java/com/yahoo/docproc/Processing.java) for `get/setVariable` and more.

The [sample application](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing) uses such context variables, too.

## Operation ordering

### Feed ordering

Ordering of feed operations is not guaranteed.
Operations on different documents will be done concurrently and are therefore not ordered.
However, Vespa guarantees that operations on the same document are processed in the order they were fed
if they enter vespa at the *same* feed endpoint.

### Document processing ordering

Document operations that are produced inside a document processor obey the same rules as at feed time.
If you either split the input into other documents or into multiple operations to the same document,
Vespa will ensure that operations to the same document id are sequenced and are delivered in the order they enter.

## (Re)configuring Document Processing

Consider the following configuration:

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">
    <container version="1.0" id="default">
        <document-processing>
            <chain id="default">
                <documentprocessor id="SomeDocumentProcessor">
                    <config name="foo.something">
                        <variable>value</variable>
                    </config>
                </documentprocessor>
            </chain>
        </document-processing>
    </container>
</services>
```

Changing chain ids, components in a chain, component configuration and schema mapping all takes effect after
[vespa activate](application-packages.html#deploy) -
no restart required.
Changing a *cluster name* (i.e. the container id)
requires a restart of docproc services after *vespa activate*.

Note when adding or modifying a processing chain in a running cluster;
if at the same time deploying a *new* document processor
(i.e. a document processor that was unknown to Vespa at the time the cluster was started),
the container must be restarted:

```
$ vespa-sentinel-cmd restart container
```

## Class diagram

![Document processing core class diagram](/assets/img/document-processing-class-diagram.svg)
