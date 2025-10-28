---
# Copyright Vespa.ai. All rights reserved.
title: "Developing request handlers"
---

This document explains how to implement and deploy a custom request handler.

In most cases, implementing your own request handlers is unnecessary, as both searchers
and processors can access the request data directly. However, there are a few cases
where custom request handlers are useful:

1. You need to implement a custom REST API.
2. Your application needs to control which parameters
   are used to route requests to a particular search or processing chain.

## Implementing a request handler

Upon receiving a request, the request handler must consume its content, process it,
and then return a response.
The most convenient way to implement a request handler is by subclassing the
[ThreadedHttpRequestHandler](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/container/jdisc/ThreadedHttpRequestHandler.html).

This utility base class uses a synchronous API and a multithreaded execution model.
It also implements a lot of functionality that is needed by most request handlers:
* queries are automatically written to the access log
* an HTTP date header is added to the response
  (if your own code adds a date header, it will not be overwritten, though)
* logging of exceptions and queries that time out
* automatic shutdown when an Error is thrown

### Example request handler implementations

The [Vespa sample apps](https://github.com/vespa-engine/sample-apps) on GitHub contains
a few example request handler implementations:

| Handler | Description |
| --- | --- |
| [DemoHandler](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/java/ai/vespa/examples/DemoHandler.java) | A handler that modifies a request before dispatching it to the `ProcessingHandler`. This handler is also used in the [HTTP API tutorial](http-api-tutorial.html). Note that since this depends on ProcessingHandler you must add <processing/> to your <container> tag to use it. If you want to issue Queries instead, have com.yahoo.search.searchchain.ExecutionFactory injected instead and use it to create executions and call search/fill on them. |

## Deploying a request handler

To deploy a request handler in an application,
use the [handler](../reference/services-container.html#handler) element in *services.xml*:

```
<container id="default" version="1.0">
    <handler id="my.package.MyRequestHandler" bundle="the name in <artifactId> in your pom.xml">
        <binding>http://*/*</binding>
    </handler>
```

A request handler may be bound to zero or more URI patterns by adding a
[binding](../reference/services-container.html#binding) element for each pattern.
