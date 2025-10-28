---
# Copyright Vespa.ai. All rights reserved.
title: "Request-Response Processing"
---

*Processing* makes it easy to create low-latency
request/response processing applications. It is the recommended way
of creating such applications on top of JDisc, but can also be used independently of JDisc.
Processing lets you define application behavior by combining Processors performing simple tasks.
Processors use a synchronous call model, but the underlying IO may be asynchronous.

Javadoc:
[com.yahoo.processing.Processor](https://javadoc.io/doc/com.yahoo.vespa/processing/latest/com/yahoo/processing/Processor.html)
[com.yahoo.processing.rendering.Renderer](https://javadoc.io/doc/com.yahoo.vespa/processing/latest/com/yahoo/processing/rendering/Renderer.html)

## Using processing

To use processing, add this dependency to *pom.xml*:

```
<dependency>
  <groupId>com.yahoo.vespa</groupId>
  <artifactId>container</artifactId>
  <version>{{site.variables.vespa_version}}</version> <!-- Find latest version at search.maven.org/search?q=g:com.yahoo.vespa%20a:container -->
  <scope>provided</scope>
</dependency>
```

Or read [how to start a deployable project from scratch](../developer-guide.html).

## Processors

A *processor* subclasses Processor and implements a single method:

```
package com.mydomain.example;

import com.yahoo.processing.*;
import com.yahoo.processing.execution.Execution;
import com.yahoo.processing.test.ProcessorLibrary.StringData;

public class ExampleProcessor extends Processor {

    @Override
    public Response process(Request request, Execution execution) {
        // Process the Request:
        request.properties().set("foo","bar");

        // Pass on to the next processor in the chain
        Response response=execution.process(request);

        // process the response
        response.data().add(new StringData(request,"Hello, world!"));

        return response;
    }

}
```

Processors may work on both the request and response, pass on the
request one or more times to further processors or create the result
data internally or by contacting a remote service. The result data may
be a nested composite structure where content is contributed by
multiple processors.

## Chaining Processors

Processors should carry out a single task and are combined into complete
applications. This is achieved using Chains:

```
Chain<Processor> myChain=new Chain<Processor>(new ExampleProcessor(),
                                              new FooProcessor(),
                                              new BarProcessor());
Response response=new Execution(myChain).process(request); // execute this chain
```

This executes the three processors in order. The Execution keeps track
of the execution state so the same processor instances may be used in
many chains at the same time. When the execution reaches the end of
the chain, the execution returns an empty Response to the processor
calling it. An AsyncExecution class is provided as a convenience to
perform an execution in a separate thread instead.

In most cases it is more convenient to configure chains and processor
instances using external configuration. Chains of processors may be
specified in
a [processing](../reference/services-processing.html)
element in
the *[services.xml](../application-packages.html#services.xml)*
file in the application package. The compiled processors are added to
the application package as
[OSGi components](container-components.html). Chain
configuration allows chains to be defined as *sets* of
processors with ordering constraints, such that the global ordering of
processors can be figured out by the framework, and set operations con
chains can be used to define extensions and variants of chains.

## Asynchronous Results

In some cases it is useful to return a Response before all the data in
it is available. This allows returning a partial response to clients
with low latency even though the complete response contains some data
arriving more slowly. The slow data can be added to the Response as a
placeholder where actual data will arrive later. The processing
framework allows waiting or listening for such completion events as
[Guava ListenableFutures.](https://guava.dev/releases/snapshot/api/docs/com/google/common/util/concurrent/ListenableFuture.html)

If *all* data is added to the Response as future placeholders
the processing framework becomes completely non-blocking.

## Dependency Injection

Processors in real applications will typically depend on some
configuration and/or other components to run. Such dependencies
should be declared as straightforward constructor arguments to allow
them to be injected at construction time.

The container runtime used to host the processing framework uses a
dependency injection framework based in Guice, see
[container components](container-components.html).

As a processor may participate in many processing executions at one
time, field values in a processing class should usually be immutable
after construction is completed.

## Response Rendering

A *Renderer* is used to serialize the Response for return to a
client. Renderers are subclasses of
`com.yahoo.processing.rendering.Renderer`. A convenience
superclass which handles waiting for future data in the asynchronous
case is provided as
`com.yahoo.processing.rendering.AsynchronousSectionedRenderer`.
The default renderer, which renders in a simple JSON format is
[com.yahoo.processing.rendering.ProcessingRenderer](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/processing/rendering/ProcessingRenderer.java)
and can be subclassed to customize rendering of each kind of Data item.

Processors are
regular [components](container-components.html) which are
added to the application package in
the [renderer
section](../reference/services-processing.html#renderer) of the *services.xml* file. A renderer is selected
in the request by setting the `format` parameter in the request
to the renderer id.

## Subclassing of Processing

The Processing framework is meant to be generic and minimal. In some
domains it is useful to employ a richer model of Processors, Requests,
Responses and Executions targeted to that domain. An example is the
[Search
domain](../searcher-development.html), where Searchers, Queries and Results subclass
Processors, Requests and Responses.
The Processing framework is designed to allow such subclassing to build richer frameworks on top.

## Testing Processors with an Application

A processor can be tested running inside a container.
We create a JDisc from *services.xml*:

```
import com.yahoo.application.container.JDisc;
import com.yahoo.application.Networking;

import com.yahoo.processing.Request;
import com.yahoo.processing.Response;

import com.yahoo.component.ComponentSpecification;

import org.junit.Test;

import static org.junit.Assert.assertThat;
import static org.junit.matchers.JUnitMatchers.containsString;

public class ContainerTest {
    @Test
    public void testSearch() {
        String servicesXml =
                "<container version=\"1.0\">" +
                "  <processing>" +
                "    <chain id=\"default\">" +
                "      <processor id=\"com.mydomain.example.ExampleProcessor\" />" +
                "    </chain>" +
                "  </processing>" +
                "</container>";
        try (JDisc container = JDisc.fromServicesXml(servicesXml, Networking.disable)) {
            Response response = container.processing().process(ComponentSpecification.fromString("default"), new Request());
            assertThat(response.data().get(0).toString(), containsString("Hello, world!"));
        }

    }
}
```

We can also examine which processors are in a chain and their ordering:

```
ChainRegistry<Processor> chains = container.processing().getChains();
Chain<Processor> defaultChain = chains.getComponent("default");

boolean foundExampleProcessor = false;
for (Processor processor: defaultChain.components()) {
    if ("ExampleProcessor".equals(processor.getClassName()))
        foundExampleProcessor = true;
}

assertTrue("No instance of ExampleProcessor found in the default chain", foundExampleProcessor)
```

## Selecting a Non-default Processor Chain

A complete application will usually be composed of several processor chains,
which may or may not invoke each other. To select a chain configured with
another `id` than "default", add the chain ID as a GET
parameter named `chain`.

In other words, given a chain named "testbed", as in:

```
<container version="1.0">
  <processing>
    <chain id="testbed">
      <processor id="com.yahoo.example.ExampleProcessor" />
    </chain>
  </processing>
</container>
```

The chain testbed could be tested from the command line by doing:

```
$ curl http://hostname:port/processing/?chain=testbed
```

## References
* [Developing web services](../developing-web-services.html).* [com.yahoo.processing](https://javadoc.io/doc/com.yahoo.vespa/processing/latest/com/yahoo/processing/package-summary.html) javadoc
  * [Guava Javadoc](https://guava.dev/releases/snapshot/api/docs/).

## Common tasks with processing

This section contains a collection of "how do I" explanations with processing.
Most of these pertains to the jDisc binding of Processing, but note that Processing is independent of
jDisc and may be invoked programmatically in any environment.

### Accessing the HTTP request from Processors

Processors which interface with the network layer may need to access the network level
request to access headers or request data, or to make outgoing calls through jDisc.
The jDisc request is available through request properties:

```
httpRequest = (com.yahoo.container.jdisc.HttpRequest)processingRequest.properties().get("jdisc.request");
```

### Setting response headers from Processors

Response headers may be added to any Response by adding instances of
`com.yahoo.processing.handler.ResponseHeaders` to the Response
(ResponseHeaders is a kind of response Data).
Multiple instances of this may be added to the Response, and the complete set of headers returned
is the superset of all such objects. Example Processor:

```
import com.yahoo.processing.Processor;
import com.yahoo.processing.Request;
import com.yahoo.processing.Response;
import com.yahoo.processing.handler.ResponseHeaders;
import com.yahoo.processing.execution.Execution;

import java.util.Collections;
import java.util.Map;
import java.util.List;

public class ResponseHeaderSetter extends Processor {

   private final Map<String,List<String>> responseHeaders;

   public ResponseHeaderSetter(Map<String,List<String>> responseHeaders) {
       this.responseHeaders = Collections.unmodifiableMap(responseHeaders);
   }

   @Override
   public Response process(Request request, Execution execution) {
       Response response = execution.process(request);
       response.data().add(new ResponseHeaders(responseHeaders, request));
       return response;
   }

}
```

## Example Processors

This section lists a few example processors which shows some use cases
for the asynchronous aspects of the API.

```
import com.yahoo.component.chain.Chain;
import com.yahoo.processing.Processor;
import com.yahoo.processing.Request;
import com.yahoo.processing.Response;
import com.yahoo.processing.execution.AsyncExecution;
import com.yahoo.processing.execution.Execution;
import com.yahoo.processing.response.FutureResponse;

import java.util.*;

/**
 * Call a number of chains in parallel
 */
public class Federator extends Processor {

    private final List<Chain<? extends Processor>> chains;

    public Federator(Chain<? extends Processor> … chains) {
        this.chains= Arrays.asList(chains);
    }

    @Override
    public Response process(Request request, Execution execution) {
        List<FutureResponse> futureResponses=new ArrayList<FutureResponse>(chains.size());
        for (Chain<? extends Processor> chain : chains) {
            futureResponses.add(new AsyncExecution(chain,execution).process(request));
        }
        Response response=execution.process(request);
        AsyncExecution.waitForAll(futureResponses,1000);
        for (FutureResponse futureResponse : futureResponses) {
            Response federatedResponse=futureResponse.get();
            response.data().add(federatedResponse.data());
            response.mergeWith(federatedResponse);
        }
        return response;
    }
}
```
```
import com.yahoo.processing.*;
import com.yahoo.processing.execution.Execution;
import com.yahoo.processing.response.*;
import com.yahoo.processing.test.ProcessorLibrary.StringData;

/**
 * A data producer which producer data which will receive asynchronously.
 * This is not a realistic, thread safe implementation as only the incoming data
 * from the last created incoming data can be completed.
 */
public class AsyncDataProducer extends Processor {

    private IncomingData incomingData;

    @Override
    public Response process(Request request, Execution execution) {
        DataList dataList = ArrayDataList.createAsync(request); // Default implementation
        incomingData=dataList.incoming();
        return new Response(dataList);
    }

    /** Called by some other data producing thread, later */
    public void completeLateData() {
        incomingData.addLast(new StringData(incomingData.getOwner().request(),
                                            "A late hello, world!"));
    }

}
```
```
import com.google.common.util.concurrent.MoreExecutors;
import com.yahoo.component.chain.Chain;
import com.yahoo.processing.*;
import com.yahoo.processing.execution.*;

/**
 * A processor which registers a listener on the future completion of
 * asynchronously arriving data to perform another chain at that point.
 */
public class AsyncDataProcessingInitiator extends Processor {

    private final Chain<Processor> asyncChain;

    public AsyncDataProcessingInitiator(Chain<Processor> asyncChain) {
        this.asyncChain=asyncChain;
    }

    @Override
    public Response process(Request request, Execution execution) {
        Response response=execution.process(request);
        response.data().complete().addListener(new RunnableExecution(request,
                new ExecutionWithResponse(asyncChain, response, execution)),
                MoreExecutors.sameThreadExecutor());
        return response;
    }

}
```
