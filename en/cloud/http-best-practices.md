---
# Copyright Vespa.ai. All rights reserved.
title: HTTP Best Practices
category: cloud
---

## Always re-use connections
As connections to a JDisc container cluster are terminated at the individual container nodes,
the cost of connection overhead will impact their serving capability.
This is especially important for HTTPS/TLS as full TLS handshakes are expensive in terms of CPU cycles.
A handshake also entails multiple network round-trips that certainly degrades request latency for new connections.
A client instance should therefore re-use HTTPS connections if possible for subsequent requests.

Note that some client implementation may not re-use connections by default.
For instance *Apache HttpClient (Java)* 
[will by default not re-use connections when configured with a client X.509 certificate](https://stackoverflow.com/a/13049131/1615280).
Most programmatic clients require the response content to be fully consumed/read for a connection to be reused.

## Use multiple connections
Clients performing feed/query must use sufficient number of connections to spread the load evenly among all containers in a cluster.
This is due to container clusters being served through a layer 4 load balancer (*Network Load Balancer*).
Too few connections overall may result in an unbalanced workload, and some containers may not receive any traffic at all.
This aspect is particular relevant for applications with large container clusters and/or few client instances.

## Be aware of server-initiated connection termination
Vespa Cloud will terminate idle connections after a timeout and active connections after a max age threshold is exceeded.
The latter is performed gracefully through mechanisms in the HTTP protocol.
* *HTTP/1.1*: A `Connection: close` header is added to the response for the subsequent request received after timeout.
* *HTTP/2*: A `GOAWAY` frame with error code `NO_ERROR (0x0)` is returned for the subsequent request received after timeout.
  Be aware that some client implementation may not handle this scenario gracefully.

Both the idle timeout and max age threshold are aggressive to regularly rebalanced traffic.
This ensures that new container nodes quickly receives traffic from existing client instances,
for example when new resources are introduced by the [autoscaler](autoscaling.html).

## Prefer HTTP/2
We recommend *HTTP/2* over *HTTP/1.1*. *HTTP/2* multiplexes multiple concurrent requests over a single connection,
and its binary protocol is more compact and efficient.
See Vespa's documentation on [HTTP/2](https://docs.vespa.ai/en/performance/http2.html) for more details.

## Be deliberate with timeouts and retries 
Make sure to configure your clients with sensible timeouts and retry policies.
Too low timeouts combined with aggressive retries may cause havoc on your Vespa application if latency increases due to overload.

Only retry requests on *server errors* - not on *client errors*.
A client should typically not retry requests after receiving a `400 Bad Request` response,
or retry a TLS connection after handshake fails with client's X.509 certificate being expired.

Handle *transient failures* and *partial failures* through a retry strategy with backoff, for instance *capped exponential backoff* with a random *jitter*.
Consider implementing a [*circuit-breaker*](https://martinfowler.com/bliki/CircuitBreaker.html) for failures persisting over a longer time-span.

For more general advise on retries and timeouts see *Amazon Builder's Library*'s
[excellent article](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) on the subject.
