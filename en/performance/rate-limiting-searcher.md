---
# Copyright Vespa.ai. All rights reserved.
title: "Rate Limiting Search Requests"
---

To avoid overloading a Vespa content cluster or to limit query load from e.g.
certain clients, the bundled
[Vespa Rate Limiting Searcher](https://github.com/vespa-engine/vespa/blob/master/container-search/src/main/java/com/yahoo/search/searchers/RateLimitingSearcher.java) can be configured to reject incoming requests to a search chain with
[HTTP return code 429](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#429)
if number of requests per second exceed a certain quota.
The counter will reset once the quota is refilled the next second.

## Getting Started

While the rate limiting searcher is bundled with Vespa, it needs to be
explicitly configured in [services.xml](../reference/services.html) before it is loaded.
This example shows how the searcher is configured for the default search chain:

```
{% highlight xml %}







{% endhighlight %}
```

When this configuration is live, the rate limiting searcher is loaded, but not active.
It is enabled on a per-request basis using either parameters directly in your HTTP search request
or by configuring query profiles.
Both approaches are shown below.

## Activate With Query Parameters

The searcher takes these query parameter arguments:

| Argument | Type | Description |
| --- | --- | --- |
| rate.id | String | The id of the client from rate limiting perspective. |
| rate.cost | Double | The cost Double of this query. This is read after executing the query and so can be set by downstream searchers inspecting the result to allow differencing the cost of various queries. Default is 1. |
| rate.quota | Double | The cost per second a particular id is allowed to consume in this system. |
| rate.idDimension | String | The name of the rate-id dimension used when logging metrics. If this is not specified, the metric will be logged without dimensions. |
| rate.dryRun | Boolean | Emit metrics on rejected requests but don't actually reject them. |

In a typical scenario, the application logic constructing the HTTP search
request will set `&rate.id` and `&rate.quota`
in the request depending on where the traffic originated - example:

```
http://localhost:8080/search?query=foo&rate.id=clientA&rate.quota=300
```

## Activate With Query Profiles

If you don't want to add the rate limiting parameters to every request
or don't control the application logic constructing the search requests,
you can enable the rate limiting using [query profiles](../query-profiles.html).
An example default query profile enabling rate limiting in the application package:

```
{% highlight xml %}

    100
    default

{% endhighlight %}
```

### Per Client Quotas

In a shared service scenario, you may want to assign different quota based
on a query parameter passed with the request, e.g. `&clientId`.
The example below will assign different quotas based on the clientId parameter passed with the request:

```
{% highlight xml %}


    clientId


    100
    default
    clientID



        200
        clientA
        clientID




        400
        clientB
        clientID


{% endhighlight %}
```

## Metrics

The searcher will emit the [count metric](../operations/metrics.html)
`requestsOverQuota` with the dimension `[rate.idDimension=rate.id]`.
