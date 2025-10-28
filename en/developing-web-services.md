---
# Copyright Vespa.ai. All rights reserved.
title: "Developing Web Service Applications"
---

This document explains how to develop (REST) web service type applications on the container -
design options, accessing the request path, returning a status code etc.
There are two types of web service APIs:
* Fine-grained APIs with closed semantics – for example *return the
  number of stars of an article*
* Coarse-grained APIs with open semantics – for example *return a page
  containing the most relevant mixture of stuff for this user and action*

With coarse-grained APIs, the container can help handle the complexity typically
involved in the implementation of such APIs
by providing a way to compose and federate components contributing to processing the request
and provide and modify the returned data,
and a way to allow such requests to start returning
before they are finished to reduce latency with large responses.
This is the [processing](jdisc/processing.html) framework
(or, in the case of search-like application,
the [searcher](searcher-development.html) specialization).

In addition, the [container](reference/component-reference.html#component-types)
features a generic mechanism allowing a
[request handler](jdisc/developing-request-handlers.html)
to be [bound](reference/component-reference.html#binding) to a URI pattern
and invoked to handle all requests matching that pattern.
This is useful where there is no need to handle complexity and/or federation
of various kinds of data in the response. Both the approaches above are
actually implemented as built-in request handlers.

A custom request handler may be written to parse the url path/method
and dispatch to an appropriate chain of processing components.
A "main" processing chain may be written
to do the same by dispatching to other chains.
The simplest way to invoke a specific chain of processors
is to forward a query to the `ProcessingHandler`
with the request property `chain` set to the name of the chain to invoke:

```
import com.yahoo.component.annotation.Inject;

public class DemoHandler extends com.yahoo.container.jdisc.ThreadedHttpRequestHandler {

...

    @Inject
    public DemoHandler(Executor executor, ProcessingHandler processingHandler) {
        super(executor);
        this.processingHandler = processingHandler;
    }

...

    @Override
    public HttpResponse handle(HttpRequest request) {
        HttpRequest processingRequest = new HttpRequest.Builder(request)
                .put(com.yahoo.processing.Request.CHAIN, "theProcessingChainIWant")
                .createDirectRequest();
        HttpResponse r = processingHandler.handle(processingRequest);
        return r;
    }

...

}
```

## Accessing the HTTP request

Custom [request handlers](jdisc/developing-request-handlers.html),
are given a
[com.yahoo.container.jdisc.HttpRequest](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/container/jdisc/HttpRequest.html),
with direct access to associated properties and request data.

In [Processing](jdisc/processing.html),
the Processors are given a
[com.yahoo.processing.Request](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/processing/Request.html)
containing the HTTP URL parameters:

```
// url parameters are added to properties
String urlParameter = request.properties().get("urlParameterName");

// jdisc request context is added with prefix context
Object contextValue = request.properties().get("context.contextKey");
```

If needed, a Processor can retrieve the entire HTTP request via a utility function:

```
import com.yahoo.container.jdisc.HttpRequest;
...

// Retrieve the underlying HTTP request:
Optional<HttpRequest> httpRequest = HttpRequest.getHttpRequest(request);

if (httpRequest.isPresent()) {
    // The POST data input stream:
    InputStream in = httpRequest.get().getData();
    // The HTTP method:
    Method method = httpRequest.get().getMethod();
}
```

### Setting the HTTP status and HTTP headers

In Processing, the return status can be set by adding a special Data item to the Response:

```
response.data().add(new com.yahoo.processing.handler.ResponseStatus(404, request));
```

If no such data element is present, the status will be determined by the container.
If it contains data able to render, it will be 200,
otherwise it will be determined by any ErrorMessage present in the response.

### Setting response headers from Processors

Response headers may be added to any Response by adding instances of
`com.yahoo.processing.handler.ResponseHeaders` to the Response
(ResponseHeaders is a kind of response Data).
Multiple instances of this may be added to the Response,
and the complete set of headers returned is the superset of all such objects.
Example Processor:

```
processingResponse.data().add(new com.yahoo.processing.handler.ResponseHeaders(myHeaders, request));
```

Request handlers may in general set their return status,
and manipulate headers directly on the HttpRequest.

## Queries

Sometimes all that is needed is letting the standard query framework
reply for more paths than standard.
This is possible by adding extra [binding](reference/services-search.html#binding)s
inside the `<search>` element in `services.xml`.
Writing a custom [request handler](jdisc/developing-request-handlers.html)
is recommended if the application is a standalone HTTP API,
and especially if there are properties used with the same name as those in the
[Query API](reference/query-api-reference.html).
A request handler may query the search components running in the same container
without any appreciable overhead:

### Invoking Vespa queries from a component

To invoke Vespa queries from a component, have an instance of
[ExecutionFactory](https://github.com/vespa-engine/vespa/blob/master/container-search/src/main/java/com/yahoo/search/searchchain/ExecutionFactory.java) injected in the constructor and use its API to construct and issue the query.
The container this runs in must include the `<search>` tag for the ExecutionFactory to be available.
Example:

```
import com.yahoo.component.annotation.Inject;
import com.yahoo.component.ComponentId;
import com.yahoo.search.Query;
import com.yahoo.search.Result;
import com.yahoo.component.Chain;
import com.yahoo.search.searchchain.Execution;
import com.yahoo.search.searchchain.ExecutionFactory;

public class MyComponent {

    private final ExecutionFactory executionFactory;

    @Inject
    public MyComponent(ExecutionFactory executionFactory) {
        this.executionFactory = executionFactory;
    }

    Result executeQuery(Query query, String chainId) {
        Chain<Search> searchChain = executionFactory.searchChainRegistry().getChain(new ComponentId(chainId));
        Execution execution = executionFactory.newExecution(searchChain);
        query.getModel().setExecution(execution);
        return execution.search(query);
    }

}
```

ExecutionFactory depends on the search chains,
so it cannot be injected into any component which is part of the search chains.
But from within a Searcher it is not needed as the Execution passed gives what is needed:
* Access the search chains: execution.context().searchChainRegistry().
* Create a new Execution: new Execution(mySearchChain, execution.context())

This is the right way since it ties that execution to the one you're in.

One hence cannot execute a search chain from the search chain component constructor to e.g. refresh a cache.
It is impossible since the search chains can't be constructed until this constructor returns.
An alternative is to extract the refreshing into a separate component
which has both the client and execution factory injected into it.
