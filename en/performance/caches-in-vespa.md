---
# Copyright Vespa.ai. All rights reserved.
title: "Caches"
---

## Content node summary cache

The summary cache caches summary requests and is enabled by
[proton tuning configuration](../reference/services-content.html#summary).
When enabling a proton summary cache,
one should also change the way proton reads summary data from mmap to directio as done below.
The summary cache saves IO and cpu spent on decompressing of chunked blocks (default 64 KB) of summary data.

Note that the summary cache is shared across multiple document types.

By default, the cache is enabled, using up to 5% of available memory - configuration example:

```
{% highlight xml %}







              directio



                5








{% endhighlight %}
```

{% include note.html content="If the requested document-summary only contains fields that are
[attributes](../attributes.html), the summary store (and cache) is not used." %}

## Protocol phases caches
*ranking.queryCache* and *groupingSessionCache*
described in the [Query API reference](../reference/query-api-reference.html)
are only caching data in between phases for a given a query,
so other queries do not get any benefits,
but these caches saves container - content node(s) round-trips for a *given* query.
