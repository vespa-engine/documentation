---
# Copyright Vespa.ai. All rights reserved.
title: "Configuring Http Servers and Filters"
---

This document explains how to set up http servers and filters in the Container.
Before proceeding, familiarize with the [Developer Guide](../developer-guide.html).

## Set up Http servers

To accept http requests on e.g. port 8090, add an `http` section with a server to *services.xml*:

```
{% highlight xml%}
xml version="1.0" encoding="utf-8" ?





{% endhighlight %}
```

To verify that the new server is running, check the default handler on the root path,
which will return a list of all http servers:

```
$ curl http://localhost:8090/
```

Adding an `http` section to *services.xml*
**disables the default http server** at port 8080.

Binding to privileged ports (< 1024) is supported.
Note that this **only** works when running as a standalone container,
and **not** when running as a Vespa cluster.

### Configure the HTTP Server

Configuration settings for the server can be modified by setting values for the
`jdisc.http.connector` config inside the `server` element:

```
{% highlight xml%}
xml version="1.0" encoding="utf-8" ?




                false




{% endhighlight %}
```

Note that it is not allowed to set the `listenPort` in the http-server config,
as it conflicts with the port that is set in the *port* attribute in the *server* element.
For a complete list of configuration fields that can be set, refer to the config definition schema in
[jdisc.http.connector.def](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/resources/configdefinitions/jdisc.http.jdisc.http.connector.def).

### TLS

TLS can be configured using either the [ssl](../reference/services-http.html#ssl)
or the [ssl-provider](../reference/services-http.html#ssl-provider) element.

```
{% highlight xml %}




              /path/to/private-key.pem
              /path/to/certificate.pem
              /path/to/ca-certificates.pem
              want

                  TLS_AES_128_GCM_SHA256,
                  TLS_AES_256_GCM_SHA384,
                  TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
                  TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384

              TLSv1.2,TLSv1.3







{% endhighlight %}
```

Refer to the [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA) sample application for an example.

## Set up Filter Chains

There are two main types of filters:
* request filters
* response filters

Request filters run before the handler that processes the request, and response filters run after.
They are used for tasks such as authentication, error checking and modifying headers.

### Using Filter Chains

Filter chains are set up by using the `request-chain` and
`response-chain` elements inside the
[filtering](../reference/services-http.html#filtering) element.
Example setting up two request filter chains, and one response filter chain:

```
{% highlight xml %}



















{% endhighlight %}
```

Filters that should be used in more than one chain,
must be defined directly in the `filtering` element,
as shown with `request-filter1` in the example above.

To actually use a filter chain, add one or more URI [bindings](../reference/services-http.html#binding):

```
{% highlight xml %}




            http://*/*




            http://*/*




{% endhighlight %}
```

These bindings say that both the request chain and the response chain
should be used when the request URI matches `http://*/*`.
So both a request filter chain and a response filter chain can be used on a single request.
However, only one request chain will be used if there are multiple request chains
that have a binding that matches a request.
And vice versa for response chains.
Refer to the [javadoc](https://javadoc.io/doc/com.yahoo.vespa/jdisc_core/latest/com/yahoo/jdisc/application/UriPattern.html) for information about which chain that will be used in such cases.

In order to bind a filter chain to a specific *server*, add the server port to the binding:

```
{% highlight xml %}


    http://*:8080/*
    http://*:9000/*

{% endhighlight %}
```

A request must match a filter chain if any filter is configured. A 403 response is returned for non-matching request.
This semantic can be disabled - see [strict-mode](../reference/services-http.html#filtering).

#### Excluding Filters from an Inherited Chain

Say you have a request filter chain that you are binding to most of your URIs.
Now, you want to run almost the same chain on another URI, but you need to exclude one of the filters.
This is done by adding `excludes`, which takes a space separated list of filter ids,
to the [chain element](../reference/services-http.html#chain).
Example where a security filter is excluded from an inherited chain for *status.html*:

```
{% highlight xml %}

    http://*/status.html

{% endhighlight %}
```

### Creating a custom Filter

Create an [application package](../developer-guide.html)
with artifactId `filter-bundle`.
Create a new file `filter-bundle/components/src/main/java/com/yahoo/demo/TestRequestFilter.java`:

```
{% highlight java %}
package com.yahoo.demo;

import com.yahoo.jdisc.*;
import com.yahoo.jdisc.handler.*;
import com.yahoo.jdisc.http.*;
import com.yahoo.jdisc.http.filter.RequestFilter;

import java.net.*;
import java.nio.ByteBuffer;

public class TestRequestFilter extends AbstractResource implements RequestFilter  {
    @Override
    public void filter(HttpRequest httpRequest, ResponseHandler responseHandler) {
        if (isLocalAddress(httpRequest.getRemoteAddress())) {
            rejectRequest(httpRequest, responseHandler);
        } else {
            httpRequest.context().put("X-NOT-LOCALHOST", "true");
        }
    }

    private boolean isLocalAddress(SocketAddress socketAddress) {
        if (socketAddress instanceof InetSocketAddress) {
            InetAddress address = ((InetSocketAddress)socketAddress).getAddress();
            return address.isAnyLocalAddress() || address.isLoopbackAddress();
        } else {
            return false;
        }
    }

    private void rejectRequest(HttpRequest request, ResponseHandler responseHandler) {
        HttpResponse response = HttpResponse.newInstance(request, Response.Status.FORBIDDEN);
        ContentChannel channel = responseHandler.handleResponse(response);
        channel.write(ByteBuffer.wrap("Not accessible by localhost.".getBytes()), null);
        channel.close(null);
    }
}
{% endhighlight %}
```

Build a bundle, and place it in the [application package](../application-packages.html)'s *components* directory.
