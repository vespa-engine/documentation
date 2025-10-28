---
# Copyright Vespa.ai. All rights reserved.
title: "HTTP/2"
---

This document contains HTTP/2 performance considerations on the container—see
[Container tuning](container-tuning.html) for general tuning of container clusters.

## Enabling HTTP/2 on container

HTTP/2 is enabled by default on a container for all connectors.
We recommend HTTP/2 with TLS, both for added security, but also for a more robust connection upgrade mechanism.
Web browsers will typically only allow HTTP/2 over TLS.

### HTTP/2 with TLS

Both HTTP/1.1 and HTTP/2 will be served over the same connector using the
[TLS ALPN Extension](https://datatracker.ietf.org/doc/html/rfc7301).
The Application-Layer Protocol Negotiation (ALPN) extension allows the client to send a list of supported protocols
during TLS handshake.
The container selects a supported protocol from that list.

The [HTTP/2 specification](https://datatracker.ietf.org/doc/html/rfc7540)
dictates multiple requirements for the TLS connection.
Vespa may enforce some or all of these restrictions.
See the HTTP/2 specification for the full list. The most significant are listed below:
* Client must use at least TLSv1.2.
* Client must provide target domain with the TLS Server Name Indication (SNI) Extension.
* Client must not use any of the banned
  [TLSv1.2 ciphers](https://datatracker.ietf.org/doc/html/rfc7540#appendix-A).

### HTTP/2 without TLS

The jdisc container supports both mechanism for HTTP/2 without TLS - see [testing](#testing):

1. Upgrading to HTTP/2 from HTTP/1
2. HTTP/2 with prior knowledge

## Feeding over HTTP/2

One of the major improvements with HTTP/2 is multiplexing of multiple concurrent requests over a single TCP connection.
This allows for high-throughput feeding through the
[/document/v1/](../reference/document-v1-api-reference.html) HTTP API,
with a simple one-operation–one-request model,
but without the overhead of hundreds of parallel connections that HTTP/1.1 would require for sufficient concurrency.

`vespa feed` in the [Vespa CLI](../vespa-cli.html#documents)
and [vespa-feed-client](../vespa-feed-client.html) use /document/v1/ over HTTP/2.

## Performance tuning

### Client

The number of multiple concurrent requests per connection is typically adjustable in HTTP/2 clients/libraries.
Document v1 API is designed for high concurrency and can easily handle thousands of concurrent requests.
Its implementation is asynchronous and max concurrency is not restricted by a thread pool size,
so configure your client to allow enough concurrent requests/streams to saturate the feed container.
Other APIs such as the [Query API](../query-api.html) is backed by a synchronous implementation,
and max concurrency is restricted by the
[underlying thread pool size](container-tuning.html#container-worker-threads).
Too many concurrent streams may result in the container rejecting requests with 503 responses.

There are also still some reasons to use multiple TCP connections—even with HTTP/2:
* **Utilize multiple containers**.
  A single container may not saturate the content layer.
  A client may have to use more connections than container nodes if the containers are behind a load balancer.
* **Higher throughput**.
  Many clients allow only for a single thread to operate each connection.
  Multiple connections may be required for utilizing several CPU cores.

## Client recommendations

Use [vespa-feed-client](../vespa-feed-client.html) for feeding through Document v1 API (JDK8+).

We recommend the [h2load benchmarking tool](https://nghttp2.org/documentation/h2load-howto.html) for load testing.
[vespa-fbench](/en/operations/tools.html#vespa-fbench) does not support HTTP/2 at the moment.

For Java there are 4 good alternatives:

1. [Jetty Client](https://javadoc.jetty.org/jetty-11/org/eclipse/jetty/client/HttpClient.html)- [OkHttp](https://square.github.io/okhttp/)
   - [Apache HttpClient 5.x](https://hc.apache.org/httpcomponents-client-5.1.x/)
   - [java.net.http.HttpClient (JDK11+)](https://docs.oracle.com/en/java/javase/11/docs/api/java.net.http/java/net/http/HttpClient.html)

## Testing

The server does not perform a protocol upgrade if a request contains content (POST, PUT, PATCH with payload).
This might be a limitation in Jetty, the HTTP server used in Vespa.
Any client should assume HTTP/2 supported - example using `curl --http2-prior-knowledge`:

```
$ curl -i --http2-prior-knowledge \
  -X POST -H 'Content-Type: application/json' \
  --data-binary @ext/A-Head-Full-of-Dreams.json \
  http://127.0.0.1:8080/document/v1/mynamespace/music/docid/a-head-full-of-dreams

HTTP/2 200
date: Tue, 06 Dec 2022 11:04:13 GMT
content-type: application/json;charset=utf-8
vary: Accept-Encoding
content-length: 122
```
