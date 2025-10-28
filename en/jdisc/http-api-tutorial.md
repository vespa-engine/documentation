---
# Copyright Vespa.ai. All rights reserved.
title: "Building an HTTP API using request handlers and processors"
---

This tutorial builds a simple application consisting of these pieces:
* A custom REST API - implemented in a *request handler*.* Two pieces of request/response processing logic - implemented as two chained *processors*.* A *component* shared by the above processors.* A custom output format - a *renderer*.

The end result is to process incoming request of the form:

```
http://hostname:port/demo?terms=something%20completely%20different
```

into a nested structure response produced by the processors and serialized by the renderer.
Use the sample application found at
[http-api-using-request-handlers-and-processors](https://github.com/vespa-engine/sample-apps/tree/master/examples/http-api-using-request-handlers-and-processors).

## Request handler

The custom request handler is required to implement a custom API.
In many cases it is not necessary to add a custom handler
as the Processors can access the request data directly.
However, it is needed if e.g. your application wants more control over exactly which parameters
are used to route to a particular processing chain.

In this case, the request handler will simply add the request URI as a property
and then forward to the built-in processing handler for processing.

Review the code in
[DemoHandler.java](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/java/ai/vespa/examples/DemoHandler.java)

## Processors

This application contains two processors,
one for annotating the incoming request (using default values from config) and checking the result,
and one for creating the result using the shared component.

### AnnotatingProcessor

Review the code in
[AnnotatingProcessor.java](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/java/ai/vespa/examples/AnnotatingProcessor.java)

### DataProcessor

The other processor creates some structured Response Data from data handled to it in the request.
This is done in cases where the web service is a processing service.
In cases where the service is implementing some middleware on top of other services,
similar processors will instead make outgoing requests
to downstream web services to produce Response Data.

Review the code in
[DataProcessor.java](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/java/ai/vespa/examples/DataProcessor.java)

Notice how the task of the server is decomposed into separate Processing steps which can be composed
by chaining at configuration time and which communicates through the Request and Response only.
This structure enhances sharing, reuse and modularity
and makes it easy to create variations where some logic encapsulated in a Processor is added, removed or modified.

The order of the processors is decided by the @Before and @After annotations -
refer to [chained components](../components/chained-components.html).

### Custom configuration

The default terms used by the AnnotatingProcessor are placed in user configuration, where the definition is in
[demo.def](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/resources/configdefinitions/demo.def):

```
package=com.mydomain.demo

demo[].term string
```

In other words, a configuration class containing a single array named *demo*,
containing a class Demo which only contains single string named *term*.

## Renderer

The responsibility of the renderer is to serialize the structured result into bytes for transport back to the client.

Rendering works by first creating a single instance of the renderer,
invoking the constructor, then cloning a new renderer for each result set to be rendered.
`init()` will be invoked once on each new clone before `render()` is invoked.

Review the code in
[DemoRenderer.java](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/java/ai/vespa/examples/DemoRenderer.java)

## Shared component

The responsibility of this custom component is to decouple some parts of the application from the Searcher.
This makes it possible to reconfigure the Searcher without rebuilding the potentially costly custom component.

In this case, what the component does is more than a little silly.
More typical use would be an [FSA](/en/operations/tools.html#vespa-makefsa)
or complex, shared helper functionality.

Review the code in
[DemoComponent.java](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/java/ai/vespa/examples/DemoComponent.java)

## Application

Review the application's configuration in
[services.xml](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/application/services.xml)

## Try it!

Build the project, then [run a test](../developer-guide.html),
querying <http://localhost:8080/demo?terms=1%202%203%204> gives:

```
OK
Renderer initialized: 1369733374898
http://localhost:8080/demo?terms=1%202%203%204
1
    2
        3
            4
Rendering finished work: 1369733374902
```
