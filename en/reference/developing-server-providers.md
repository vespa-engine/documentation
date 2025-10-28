---
# Copyright Vespa.ai. All rights reserved.
title: "Developing server providers"
---

The [com.yahoo.jdisc.service.ServerProvider](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/service/ServerProvider.html)
interface defines a component that is capable of acting as a server for an external client.
This document explains how to implement and deploy a custom server provider.

All requests that are processed in a JDisc application are created by server providers.
These are the parts of the JDisc Container that accept incoming connections.
Upon accepting a request from an external client,
the server provider must create and dispatch a corresponding `com.yahoo.jdisc.Request` instance.
Upon receiving the `com.yahoo.jdisc.Response`,
the server needs to respond back to the client.
To implement a server provider, either implement the
[ServerProvider](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/service/ServerProvider.html) interface directly, or subclass the more convenient
[AbstractServerProvider](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/service/AbstractServerProvider.html).
Please note the following:
* All server providers require a local reference to `CurrentContainer`.
  Declare that as a constructor argument (which triggers [injection](../jdisc/injecting-components.html)),
  and store it locally.
* All requests dispatched by a server provider should be "server" requests
  (i.e. requests whose `isServerRequest()` method returns `true`).
  To create such a request, use
  [this constructor](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/Request.html#Request-com.yahoo.jdisc.service.CurrentContainer-java.net.URI-).
* The code necessary to dispatch a request and write its content into the returned `ContentChannel`
  is the same as for [dispatching a client request](low-level-request-handlers.html#dispatching-a-client-request) from a request handler.
* The code necessary to handle the response and its content is the same as for
  [handling a client response](low-level-request-handlers.html#handling-a-client-response)
  in a request handler.

To install a server provider in a container,
use the [server](../reference/services-container.html#server)
element in *services.xml*, e.g.:

```
<container id="default" version="1.0">
    <server id="my.package.MyServerProvider" bundle="the name in <artifactId> in pom.xml" />
    <nodes>
        <node hostalias="node1" />
    </nodes>
</container>
```
