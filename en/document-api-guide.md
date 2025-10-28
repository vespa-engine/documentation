---
# Copyright Vespa.ai. All rights reserved.
title: "Document API"
---

This is an introduction to how to build and compile Vespa clients using the Document API.
It can be used for feeding, updating and retrieving documents,
or removing documents from the repository. See also the
[Java reference](https://javadoc.io/doc/com.yahoo.vespa/documentapi).

Use the [VESPA_CONFIG_SOURCES](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
environment variable to set config servers to interface with.

The most common use case is using the async API in a
[document processor](document-processing.html) - from the sample apps:
* Async GET in
  [LyricsDocumentProcessor.java](https://github.com/vespa-engine/sample-apps/blob/master/examples/document-processing/src/main/java/ai/vespa/example/album/LyricsDocumentProcessor.java)
* Async UPDATE in
  [ReviewProcessor.java](https://github.com/vespa-engine/sample-apps/blob/master/use-case-shopping/src/main/java/ai/vespa/example/shopping/ReviewProcessor.java)

## Documents

All data fed, indexed and searched in Vespa are instances of the `Document` class.
A [document](documents.html) is a composite object that consists of:
* A `DocumentType` that defines the set of fields that
  can exist in a document. A document can only have a single
  *document type*, but document types can inherit the content of another.
  All fields of an inherited type is available in all its descendants.
  The document type is defined in the
  [schema](reference/schema-reference.html),
  which is converted into a configuration file to be read by the
  `DocumentManager`.

  All registered document types are instantiated and stored within
  the document manager. A reference to these objects can be
  retrieved using the `getDocumentType()` method by
  supplying the name and the version of the wanted document type.

  `DocumentManager` initialization is done automatically
  by the Document API by subscribing to the appropriate
  configuration.
* A `DocumentId` which is a unique document identifier.
  The document distribution uses the document identifier,
  see the [reference](content/buckets.html#distribution) for details.
* A set of `(Field, FieldValue)` pairs, or
  "fields" for short. The `Field` class has
  methods for getting its name, data type and internal
  identifier. The field object for a given field name can be
  retrieved using the `getField(<fieldname>)`
  method in the `DocumentType`.

Use [DocumentAccess](https://javadoc.io/doc/com.yahoo.vespa/documentapi/latest/com/yahoo/documentapi/DocumentAccess.html) javadoc. Sample app:

```
<dependencies>
    <dependency>
        <groupId>com.yahoo.vespa</groupId>
        <artifactId>documentapi</artifactId>
        <version>{{site.variables.vespa_version}}</version> <!-- Find latest version at search.maven.org/search?q=g:com.yahoo.vespa%20a:documentapi -->
    </dependency>
<dependencies>
```
```
import com.yahoo.document.DataType;
import com.yahoo.document.Document;
import com.yahoo.document.DocumentId;
import com.yahoo.document.DocumentPut;
import com.yahoo.document.DocumentType;
import com.yahoo.document.DocumentUpdate;
import com.yahoo.document.datatypes.StringFieldValue;
import com.yahoo.document.datatypes.WeightedSet;
import com.yahoo.document.update.FieldUpdate;
import com.yahoo.documentapi.DocumentAccess;
import com.yahoo.documentapi.SyncParameters;
import com.yahoo.documentapi.SyncSession;

public class DocClient {

    public static void main(String[] args) {

        // DocumentAccess is injectable in Vespa containers, but not in command line tools, etc.
        DocumentAccess access = DocumentAccess.createForNonContainer();
        DocumentType type = access.getDocumentTypeManager().getDocumentType("music");
        DocumentId id = new DocumentId("id:namespace:music::0");
        Document docIn = new Document(type, id);
        SyncSession session = access.createSyncSession(new SyncParameters.Builder().build());

        // Put document with a1,1
        WeightedSet<StringFieldValue> wset = new WeightedSet<>(DataType.getWeightedSet(DataType.STRING));
        wset.put(new StringFieldValue("a1"), 1);
        docIn.setFieldValue("aWeightedset", wset);
        DocumentPut put = new DocumentPut(docIn);
        System.out.println(docIn.toJson());
        session.put(put);

        // Update document with a1,10 and a2,20
        DocumentUpdate upd1 = new DocumentUpdate(type, id);
        WeightedSet<StringFieldValue> wset1 = new WeightedSet<>(DataType.getWeightedSet(DataType.STRING));
        wset1.put(new StringFieldValue("a1"), 10);
        wset1.put(new StringFieldValue("a2"), 20);
        upd1.addFieldUpdate(FieldUpdate.createAddAll(type.getField("aWeightedset"), wset1));
        System.out.println(upd1.toString());
        session.update(upd1);

        Document docOut = session.get(id);
        System.out.println("document get:" + docOut.toJson());

        session.destroy();
        access.shutdown();
    }
}
```

To test using the [sample apps](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation),
enable more ports for client to connect to config server and other processes on localhost - change docker command:

```
$ docker run --detach --name vespa --hostname localhost --privileged \
  --volume $VESPA_SAMPLE_APPS:/vespa-sample-apps --publish 8080:8080 \
  --publish 19070:19070 --publish 19071:19071 --publish 19090:19090 --publish 19099:19099 --publish 19101:19101 --publish 19112:19112 \
  vespaengine/vespa
```

## Fields

Examples:

```
doc.setFieldValue("aByte", (byte)1);
doc.setFieldValue("aInt", (int)1);
doc.setFieldValue("aLong", (long)1);
doc.setFieldValue("aFloat", 1.0);
doc.setFieldValue("aDouble", 1.0);
doc.setFieldValue("aBool", new BoolFieldValue(true));
doc.setFieldValue("aString", "Hello Field!");

doc.setFieldValue("unknownField", "Will not see me!");

Array<IntegerFieldValue> intArray = new Array<>(doc.getField("aArray").getDataType());
intArray.add(new IntegerFieldValue(11));
intArray.add(new IntegerFieldValue(12));
doc.setFieldValue("aArray", intArray);

Struct pos = PositionDataType.valueOf(1,2);
       pos = PositionDataType.fromString("N0.000002;E0.000001");  // two ways to set same value
doc.setFieldValue("aPosition", pos);

doc.setFieldValue("aPredicate", new PredicateFieldValue("aLong in [10..20]"));

byte[] rawBytes = new byte[100];
for (int i = 0; i < rawBytes.length; i++) {
    rawBytes[i] = (byte)i;
}
doc.setFieldValue("aRaw", new Raw(ByteBuffer.wrap(rawBytes)));

Tensor tensor = Tensor.Builder.of(TensorType.fromSpec("tensor<float>>(x[2],y[2])")).
        cell().label("x", 0).label("y", 0).value(1.0).
        cell().label("x", 0).label("y", 1).value(2.0).
        cell().label("x", 1).label("y", 0).value(3.0).
        cell().label("x", 1).label("y", 1).value(5.0).build();
doc.setFieldValue("aTensor", new TensorFieldValue(tensor));

MapFieldValue<StringFieldValue, StringFieldValue> map = new MapFieldValue<>(new MapDataType(DataType.STRING, DataType.STRING));
map.put(new StringFieldValue("key1"), new StringFieldValue("foo"));
map.put(new StringFieldValue("key2"), new StringFieldValue("bar"));
doc.setFieldValue("aMap", map);

WeightedSet<StringFieldValue> wset = new WeightedSet<>(DataType.getWeightedSet(DataType.STRING));
wset.put(new StringFieldValue("strval 1"), 5);
wset.put(new StringFieldValue("strval 2"), 10);
doc.setFieldValue("aWeightedset", wset);
```

## Document updates

A document update is a request to modify a document, see [reads and writes](reads-and-writes.html).

Primitive, and some multivalue fields (WeightedSet and Array<primitive>), are updated using a
[FieldUpdate](https://javadoc.io/doc/com.yahoo.vespa/document/latest/com/yahoo/document/update/FieldUpdate.html).

Complex, multivalue fields like Map and Array<struct> are updated using
[AddFieldPathUpdate](https://javadoc.io/doc/com.yahoo.vespa/document/latest/com/yahoo/document/fieldpathupdate/AddFieldPathUpdate.html),
[AssignFieldPathUpdate](https://javadoc.io/doc/com.yahoo.vespa/document/latest/com/yahoo/document/fieldpathupdate/AssignFieldPathUpdate.html) and
[RemoveFieldPathUpdate](https://javadoc.io/doc/com.yahoo.vespa/document/latest/com/yahoo/document/fieldpathupdate/RemoveFieldPathUpdate.html).
Field path updates are only supported on non-attribute
[fields](reference/schema-reference.html#field),
[index](reference/schema-reference.html#index) fields,
or fields containing
[struct field](reference/schema-reference.html#struct-field) attributes.
If a field is both an index field and an attribute, then the document is updated in the document store,
the index is updated, but the attribute is not updated.
Thus, you can get old values in document summary requests and old values being used in ranking and grouping.
A [field path](reference/document-field-path.html) string identifies fields to update - example:

```
upd.addFieldPathUpdate(new AssignFieldPathUpdate(type, "myMap{key2}", new StringFieldValue("abc")));
```
*FieldUpdate* examples:

```
// Simple assignment
Field intField = type.getField("aInt");
IntegerFieldValue intFieldValue = new IntegerFieldValue(2);
FieldUpdate assignUpdate = FieldUpdate.createAssign(intField, intFieldValue);
upd.addFieldUpdate(assignUpdate);

// Arithmetic
FieldUpdate addUpdate = FieldUpdate.createIncrement(type.getField("aLong"), 3);
upd.addFieldUpdate(addUpdate);

// Composite - add one array element
upd.addFieldUpdate(FieldUpdate.createAdd(type.getField("aArray"),
        new IntegerFieldValue(13)));

// Composite - add two array elements
upd.addFieldUpdate(FieldUpdate.createAddAll(type.getField("aArray"),
        List.of(new IntegerFieldValue(14), new IntegerFieldValue(15))));

// Composite - add weightedset element
upd.addFieldUpdate(FieldUpdate.createAdd(type.getField("aWeightedset"),
        new StringFieldValue("add_me"),101));

// Composite - add set to set
WeightedSet<StringFieldValue> wset = new WeightedSet<>(DataType.getWeightedSet(DataType.STRING));
wset.put(new StringFieldValue("a1"), 3);
wset.put(new StringFieldValue("a2"), 4);
upd.addFieldUpdate(FieldUpdate.createAddAll(type.getField("aWeightedset"), wset));

// Composite - update array element
upd.addFieldUpdate(FieldUpdate.createMap(type.getField("aArray"),
        new IntegerFieldValue(1), // array index
        new AssignValueUpdate(new IntegerFieldValue(2))));  // value at index

// Composite - increment weight
upd3.addFieldUpdate(FieldUpdate.createIncrement(type.getField("aWeightedset"),
        new StringFieldValue("a1"), 1));

// Composite - add to set
upd.addFieldUpdate(FieldUpdate.createMap(type.getField("aWeightedset"),
        new StringFieldValue("element1"), // value
        new AssignValueUpdate(new IntegerFieldValue(30))));
```
*FieldPathUpdate* examples:

```
// Add an element to a map
Array stringArray = new Array(DataType.getArray(DataType.STRING));
stringArray.add(new StringFieldValue("my-val"));
AddFieldPathUpdate addElement = new AddFieldPathUpdate(type, "aMap{key1}", stringArray);
upd.addFieldPathUpdate(addElement);

// Modify an element in a map
upd.addFieldPathUpdate(new AssignFieldPathUpdate(type, "aMap{key2}", new StringFieldValue("abc")));
```

### Update reply semantics

Sending in an update for which the system can not find a corresponding
document to update is *not* considered an error.
These are returned with a successful status code
(assuming that no actual error occurred during the update processing). Use
[UpdateDocumentReply.wasFound()](https://javadoc.io/doc/com.yahoo.vespa/documentapi/latest/com/yahoo/documentapi/UpdateResponse.html#wasFound()) to check if the update was known to have been applied.

If the update returns with an error reply, the update *may or may not* have been applied,
depending on where in the platform stack the error occurred.

## Document Access

The starting point of for passing documents and updates to Vespa
is the `DocumentAccess` class.
This is a singleton (see `get()` method) session factory
(see `createXSession()` methods),
that provides three distinct access types:
* **Synchronous random access**:
  provided by the class `SyncSession`.
  Suitable for low-throughput proof-of-concept applications.
* [**Asynchronous random access**](#asyncsession):
  provided by the class `AsyncSession`.
  It allows for document repository writes and random access with **high throughput**.
* [**Visiting**](#visitorsession):
  provided by the class `VisitorSession`.
  Allows a set of documents to be accessed in order decided by the document repository,
  which gives higher read throughput than random access.

### AsyncSession

This class represents a session for asynchronous access to a document repository.
It is created by calling
`myDocumentAccess.createAsyncSession(myAsyncSessionParams)`,
and provides document repository writes and random access with high throughput.
The usage pattern for an asynchronous session is like:

1. `put()`, `update()`, `get()`
   or `remove()` is invoked on the session,
   and it returns a synchronous `Result` object that indicates
   whether the request was successful or not.
   The `Result` object also contains a *request identifier*.
2. The client polls the session for a `Response` through
   its `getNext()` method.
   Any operation accepted by an asynchronous session will produce
   exactly one response within the configured timeout.
3. Once a response is available, it is matched to the request by
   inspecting the response's request identifier.
   The response may also contain data, either a retrieved document or a failed document put
   or update that needs to be handled.
4. Note that the client must process the response queue or your JVM will run into garbage collection issues,
   as the underlying session keeps track of all responses
   and unless they are consumed they will be kept alive and not be garbage collected.

Example:

```
import com.yahoo.document.*;
import com.yahoo.documentapi.*;

public class MyClient {

    // DocumentAccess is injectable in Vespa containers, but not in command line tools, etc.
    private final DocumentAccess access = DocumentAccess.createForNonContainer();
    private final AsyncSession session = access.createAsyncSession(new AsyncParameters());
    private boolean abort = false;
    private int numPending = 0;

    /**
     * Implements application entry point.
     *
     * @param args Command line arguments.
     */
    public static void main(String[] args) {
        MyClient app = null;
        try {
            app = new MyClient();
            app.run();
        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            if (app != null) {
                app.shutdown();
            }
        }
        if (app == null || app.abort) {
            System.exit(1);
        }
    }

    /**
     * This is the main entry point of the client. This method will not return until all available documents
     * have been fed and their responses have been returned, or something signaled an abort.
     */
    public void run() {
        System.out.println("client started");
        while (!abort) {
            flushResponseQueue();

            Document doc = getNextDocument();
            if (doc == null) {
                System.out.println("no more documents to put");
                break;
            }
            System.out.println("sending doc " + doc);

            while (!abort) {
                Result res = session.put(doc);
                if (res.isSuccess()) {
                    System.out.println("put has request id " + res.getRequestId());
                    ++numPending;
                    break; // step to next doc.
                } else if (res.type() == Result.ResultType.TRANSIENT_ERROR) {
                    System.out.println("send queue full, waiting for some response");
                    processNext(9999);
                } else {
                    res.getError().printStackTrace();
                    abort = true; // this is a fatal error
                }
            }
        }
        if (!abort) {
            waitForPending();
        }
        System.out.println("client stopped");
    }

    /**
     * Shutdown the underlying api objects.
     */
    public void shutdown() {
        System.out.println("shutting down document api");
        session.destroy();
        access.shutdown();
    }

    /**
     * Returns the next document to feed to Vespa. This method should only return null when the end of the
     * document stream has been reached, as returning null terminates the client. This is the point at which
     * your application logic should block if it knows more documents will eventually become available.
     *
     * @return The next document to put, or null to terminate.
     */
    public Document getNextDocument() {
        return null; // TODO: Implement at your discretion.
    }

    /**
     * Processes all immediately available responses.
     */
    void flushResponseQueue() {
        System.out.println("flushing response queue");
        while (processNext(0)) {
            // empty
        }
    }

    /**
     * Wait indefinitely for the responses of all sent operations to return. This method will only return
     * early if the abort flag is set.
     */
    void waitForPending() {
        while (numPending != 0) {
            if (abort) {
                System.out.println("waiting aborted, " + numPending + " still pending");
                break;
            }
            System.out.println("waiting for " + numPending + " responses");
            processNext(9999);
        }
    }

    /**
     * Retrieves and processes the next response available from the underlying asynchronous session. If no
     * response becomes available within the given timeout, this method returns false.
     *
     * @param timeout The maximum number of seconds to wait for a response.
     * @return True if a response was processed, false otherwise.
     */
    boolean processNext(int timeout) {
        Response res;
        try {
            res = session.getNext(timeout);
        } catch (InterruptedException e) {
            e.printStackTrace();
            abort = true;
            return false;
        }
        if (res == null) {
            return false;
        }
        System.out.println("got response for request id " + res.getRequestId());
        --numPending;
        if (!res.isSuccess()) {
            System.err.println(res.getTextMessage());
            abort = true;
            return false;
        }
        return true;
    }
}
```

### VisitorSession

This class represents a session for sequentially visiting documents with high throughput.

A visitor is started when creating the `VisitorSession`
through a call to `createVisitorSession`.
A visitor target, that is a receiver of visitor data,
can be created through a call to `createVisitorDestinationSession`.
The `VisitorSession` is a receiver of visitor data.
See [visiting reference](visiting.html) for details.
The `VisitorSession`:
* Controls the operation of the visiting process
* Handles the data resulting from visiting data in the system

Those two different tasks may be set up to be handled by
a `VisitorControlHandler` and
a `VisitorDataHandler` respectively.
These handlers may be supplied to the `VisitorSession` in
the `VisitorParameters` object,
together with a set of other parameters for visiting.
Example: To increase performance, let more separate visitor destinations handle
visitor data, then specify the addresses to remote data handlers.

The default `VisitorDataHandler` used by
the `VisitorSession` returned from
`DocumentAccess` is `VisitorDataQueue` which
queues up incoming documents and implements a polling API.
The documents can be extracted by calls to the
session's `getNext()` methods and can be ack-ed by
the `ack()` method.
The default `VisitorControlHandler` can be accessed through the
session's `getProgress()`,
`isDone()`, and `waitUntilDone()` methods.

Implement custom `VisitorControlHandler`
and `VisitorDataHandler` by subclassing them and supplying
these to the `VisitorParameters` object.

The `VisitorParameters` object controls how and what data will be visited -
refer to the [javadoc](https://javadoc.io/doc/com.yahoo.vespa/documentapi/latest/com/yahoo/documentapi/VisitorParameters.html).
Configure the
[document selection](reference/document-select-language.html) string
to select what data to visit - the default is all data.

You can specify what fields to return in a result by specifying a
[fieldSet](https://javadoc.io/doc/com.yahoo.vespa/documentapi/latest/com/yahoo/documentapi/VisitorParameters.html) -
see [document field sets](documents.html#fieldsets). Specifying only the fields you need may improve performance
a lot, especially if you can make do with only in-memory fields or if you have large fields you don't need returned.

Example:

```
import com.yahoo.document.Document;
import com.yahoo.document.DocumentId;
import com.yahoo.documentapi.DocumentAccess;
import com.yahoo.documentapi.DumpVisitorDataHandler;
import com.yahoo.documentapi.ProgressToken;
import com.yahoo.documentapi.VisitorControlHandler;
import com.yahoo.documentapi.VisitorParameters;
import com.yahoo.documentapi.VisitorSession;

import java.util.concurrent.TimeoutException;

public class MyClient {

    public static void main(String[] args) throws Exception {
        VisitorParameters params = new VisitorParameters("true");
        params.setLocalDataHandler(new DumpVisitorDataHandler() {

            @Override
            public void onDocument(Document doc, long timeStamp) {
                System.out.print(doc.toXML(""));
            }

            @Override
            public void onRemove(DocumentId id) {
                System.out.println("id=" + id);
            }
        });
        params.setControlHandler(new VisitorControlHandler() {

            @Override
            public void onProgress(ProgressToken token) {
                System.err.format("%.1f %% finished.\n", token.percentFinished());
                super.onProgress(token);
            }

            @Override
            public void onDone(CompletionCode code, String message) {
                System.err.println("Completed visitation, code " + code + ": " + message);
                super.onDone(code, message);
            }
        });
        params.setRoute(args.length > 0 ? args[0] : "[Storage:cluster=storage;clusterconfigid=storage]");
        params.setFieldSet(args.length > 1 ? args[1] : "[document]");

        // DocumentAccess is injectable in Vespa containers, but not in command line tools, etc.
        DocumentAccess access = DocumentAccess.createForNonContainer();
        VisitorSession session = access.createVisitorSession(params);
        if (!session.waitUntilDone(0)) {
            throw new TimeoutException();
        }
        session.destroy();
        access.shutdown();
    }
}
```

The first optional argument to this client is the [route](/en/operations-selfhosted/routing.html) of the cluster to visit.
The second is the [fieldset](documents.html#fieldsets) set to retrieve.
