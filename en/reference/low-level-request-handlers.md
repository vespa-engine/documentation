---
# Copyright Vespa.ai. All rights reserved.
title: "Low-level request handler APIs"
---

This document describes the low-level request handler APIs in Jdisc.
For implementing your own request handlers, please use
[Developing request handlers](../jdisc/developing-request-handlers.html)
instead.

The [com.yahoo.jdisc.service.RequestHandler](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/RequestHandler.html)
interface defines a component that is capable of acting as a handler for a Request.
This document explains how to implement and deploy a custom request handler.

All request processing in a Container application is done by request handlers.
Implementations of the `RequestHandler` interface are bound to one or more URI patterns,
and invoked by [server providers](developing-server-providers.html)
or other request handlers.
Upon receiving a request, the request handler must consume its content, process it,
and then return a response back to the provided `ResponseHandler`.

To implement a request handler, either implement the
[RequestHandler](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/RequestHandler.html) interface directly, or subclass the more convenient
[AbstractRequestHandler](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/AbstractRequestHandler.html).

Please note the following:
* All request handlers need to implement some [request handling logic](#handling-a-request),
  as well as some [response dispatch logic](#dispatching-a-response).
* In case a request handler needs to [dispatch client requests](#dispatching-a-client-request),
  it must also implement [response handling logic](#handling-a-client-response).
* A [request's timeout](#request-timeout) is the maximum allowed time
  from when `handleRequest(Request, ResponseHandler)` is invoked
  until `handleResponse(Response)` must have been called.

## Handling a request

A request handler is invoked by a call to its
`handleRequest(Request, ResponseHandler)` method.
As JDisc enforces no specific threading model,
this call can be run by any thread - even some critical IO thread that
belongs to one of the configured server providers.
Because of this, never
do much work in the body of the `handleRequest(Request, ResponseHandler)` method.
Instead, pass the necessary context to some known thread pool.
The [ThreadedRequestHandler](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/ThreadedRequestHandler.html)
provides an efficient implementation of such handover.

Once invoked, a request handler must create and return a `ContentChannel`
into which the caller can write the request's payload.
In no specific order, the request handler must now:
* [read the content](#reading-from-a-contentchannel) of the request, and
* [dispatch a response](#dispatching-a-response) to the given response handler.

## Reading from a ContentChannel

The [ContentChannel](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/ContentChannel.html) provides an asynchronous interface for `ByteBuffer` handover -
where *handover* implies that the caller will never reuse the buffer.
The buffer may safely be stored and processed at some point in the future.

A content channel is required to be thread-safe.
It is the caller that is expected to do the external synchronization to avoid out-of-order calls -
a second call to `write(ByteBuffer, CompletionHandler)`
will never be initiated before the first call has returned.

The optional (in the sense that it might be `null`)
[CompletionHandler](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/CompletionHandler.html)
provides support for asynchronous notification of the completion or failure of a call to a content channel.
Notice that unless the implementation of the content channel throws an exception during a
`write(ByteBuffer, CompletionHandler)` or `close(CompletionHandler)`,
it is required
that one explicitly calls the corresponding completion handler at some point in the future.

Instead of developing a custom `ContentChannel`, consider using
[BufferedContentChannel](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/BufferedContentChannel.html)
if intending to forward the content without blocking or copying, or
[ReadableContentChannel](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/ReadableContentChannel.html) if intending to access the content yourself.

## Dispatching a response

The [ResponseHandler](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/ResponseHandler.html) is the callback to be invoked once a request has been sufficiently processed.
The response may be dispatched by any thread, and at any time -
even before the call to the request handler returns.

The response handler is the second argument of the request handler's
`handleRequest(Request, ResponseHandler)` method,
and it is commonly a one-off object.

Notice that unless the call to the request handler throws an exception,
it is required that you call the response handler
exactly once at some point in the future.

Once a response has been constructed, it is dispatched by calling
[responseHandler.handleResponse(Response)](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/ResponseHandler.html#handleResponse-com.yahoo.jdisc.Response-).
The returned `ContentChannel` must then be used to asynchronously
[write the content](#writing-to-a-contentchannel) of the response into it.
Notice that unless the call to the response handler threw an exception,
it is required
that you explicitly close the returned content channel at some point in the future.

Instead of explicitly managing the dispatch of a response yourself, consider using the
[ResponseDispatch](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/ResponseDispatch.html) utility class to safely dispatch the response.

## Writing to a ContentChannel

The [ContentChannel](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/ContentChannel.html) provides an asynchronous interface for `ByteBuffer` handover -
where *handover* implies that you may never reuse a buffer that you have written to it.

All content channels are thread-safe, but it is your responsibility to perform the
necessary synchronization to avoid out-of-order calls to it.
A second call to `write(ByteBuffer, CompletionHandler)`
should never be initiated before the first call has returned.

The optional (in the sense you are allowed to pass `null` for it)
[CompletionHandler](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/CompletionHandler.html) provides support for asynchronous notification of the completion
or failure of a call to a content channel.
Unless an exception is thrown in a call to `write(ByteBuffer, CompletionHandler)`
or `close(CompletionHandler)`,
you are guaranteed to have your completion handler called at some point in the future.

Note that it is required to explicitly close all content channels -
regardless of whether some call to it threw an exception
or `failed(Throwable)` was invoked on some completion handler.

## Dispatching a client request

If a request handler decides to create and dispatch a
[child-request](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/Request.html#Request-com.yahoo.jdisc.Request-java.net.URI-),
it is done through the same binding set mechanics that was used to resolve the current request handler.
However, where server providers resolve their dispatch against server-bindings,
request handlers will resolve their dispatch against client-bindings.
Override this behavior by using the
[setServerRequest(boolean)](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/Request.html#setServerRequest-boolean-) method.
Note that the request maintains a reference to the
[CurrentContainer](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/service/CurrentContainer.html),
and that you are required to release the local reference
once the request has been dispatched,
to allow the JDisc Container to cleanly shut down at some point in the future.

Once the child-request and a response handler has been constructed, it is dispatched by calling
[request.connect(ResponseHandler)](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/Request.html#connect-com.yahoo.jdisc.handler.ResponseHandler-).
The returned `ContentChannel` must then be used to asynchronously
[write the content](#writing-to-a-contentchannel) of the request into it.
Note that unless the call to connect threw an exception,
it is required that you explicitly close
the returned content channel at some point in the future.

Instead of explicitly managing the dispatch of a request yourself, consider using the
[RequestDispatch](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/handler/RequestDispatch.html) utility class to safely dispatch requests.

## Handling a client response

As a client provider responds to a request,
the response handler that was part of the request dispatch is invoked.

Because JDisc enforces no specific threading model,
this call may be performed by any thread -
even some critical IO thread that belongs to one of the configured client providers.
Because of this you should never
do much work in the body of the `handleResponse(Response)` method.

Also, because the response may be dispatched at any time,
the response handler may be invoked even before the call to dispatch the request returns.

Once invoked, a response handler must create and return a `ContentChannel`
into which the caller can write the response's payload.
At some point in the future, this payload then needs be
[consumed](#reading-from-a-contentchannel) and acted upon.

## Request timeout

A request may or may not have an assigned timeout.
Such a timeout is the total amount of time that a request handler may spend processing a request
before the corresponding call to `handleResponse(Response)` is made.
If no timeout is assigned to a request, there will be no timeout.
Once the allocated time has expired, unless the response handler has already been called,
the request handler's `handleTimeout(Request, ResponseHandler)` method is invoked.

The `ResponseHandler` passed to the timeout method is the same
`ResponseHandler` that was initially passed to the `handleRequest()` method.
There is a built-in guard against calling the `ResponseHandler` more than once,
so you do not need additional synchronization to prevent a late response from calling the
handler of a request that has already timed out.
The `handleTimeout()` method is called by the timeout manager's own thread.
Any exception thrown in `handleTimeout()` is ignored.

Notice that you are required
to call the given response handler from within `handleTimeout(Request, ResponseHandler)`.
Failure to do so will prevent the JDisc Container from cleanly shutting down.
