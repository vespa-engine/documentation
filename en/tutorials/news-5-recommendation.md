---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "News search and recommendation tutorial - recommendations"
redirect_from:
- /documentation/tutorials/news-5-recommendation.html
---

This is the fifth part of the tutorial series for setting up a Vespa
application for personalized news recommendations. The parts are:  

1. [Getting started](news-1-getting-started.html)
2. [A basic news search application](news-2-basic-feeding-and-query.html) - application packages, feeding, query
3. [News search](news-3-searching.html) - sorting, grouping, and ranking
4. [Generating embeddings for users and news articles](news-4-embeddings.html)
5. [News recommendation](news-5-recommendation.html) - partial updates (news embeddings), ANNs, filtering
6. [News recommendation with searchers](news-6-recommendation-with-searchers.html) - custom searchers, doc processors
7. [News recommendation with parent-child](news-7-recommendation-with-parent-child.html) - parent-child, tensor ranking
8. Advanced news recommendation - intermission - training a ranking model
9. Advanced news recommendation - ML models

In this part, we'll start transforming our application from news search to
recommendation using the embeddings we created in the previous part.
So, we'll start by modifying our application,
so we can feed the embeddings and start using them for searching.

For reference, the final state of this tutorial can be found in the
`app-5-recommendation` sub-directory of the `news` sample application.


## Indexing embeddings

First, we need to modify the `news.sd` search definition to include a field
to hold the embedding and a recommendation rank profile:

<pre data-test="file" data-path="news/my-app/schemas/news.sd">
schema news {
    document news {
        field news_id type string {
            indexing: summary | attribute
            attribute: fast-search
        }
        field category type string {
            indexing: summary | attribute
        }
        field subcategory type string {
            indexing: summary | attribute
        }
        field title type string {
            indexing: index | summary
            index: enable-bm25
        }
        field abstract type string {
            indexing: index | summary
            index: enable-bm25
        }
        field body type string {
            indexing: index | summary
            index: enable-bm25
        }
        field url type string {
            indexing: index | summary
        }
        field date type int {
            indexing: summary | attribute
        }
        field clicks type int {
            indexing: summary | attribute
        }
        field impressions type int {
            indexing: summary | attribute
        }
        field embedding type tensor&lt;float&gt;(d0[51]) {
            indexing: attribute 
            attribute {
                distance-metric: euclidean
            }
        }
    }

    fieldset default {
        fields: title, abstract, body
    }

    rank-profile popularity inherits default {
        function popularity() {
            expression: if (attribute(impressions) &gt; 0, attribute(clicks) / attribute(impressions), 0)
        }
        first-phase {
            expression: nativeRank(title, abstract) + 10 * popularity
        }
    }

    rank-profile recommendation inherits default {
        first-phase {
          expression: closeness(field, embedding)
        }
    }
}
</pre>

The `embedding` field is a tensor field. Tensors in Vespa are flexible
multi-dimensional data structures, and, as first-class citizens, can be used
in queries, document fields, and constants in ranking. Tensors can be either
dense or sparse or both, and can contain any number of dimensions. Please see
[the tensor user guide](https://docs.vespa.ai/en/tensor-user-guide.html) for
more information.

Here we have defined a dense tensor with a single dimension (`d0` - dimension
0), which represents a vector. The distance metric is euclidean as we would
like to use this field for nearest-neighbor search.

This is seen in the `recommendation` rank profile. Here, we've added a
ranking expression using the
[closeness](https://docs.vespa.ai/en/reference/rank-features.html#closeness(dimension,name))
ranking feature, which calculates the euclidean distance and uses that to rank
the news articles. This depends on using the `nearestNeighbor` search operator,
which we'll get back to below when searching. But for now, this expects 
a tensor in the query to be used as the initial search point.

If you take a look at the file generated for the news embeddings,
`mind/vespa_news_embeddings.json`, you'll see several lines with
something like this:

```
{
    "update": "id:news:news::N13390", 
    "fields": {
        "embedding": {
            "assign": { 
                "values": [9.871717,-0.403103,...]
            } 
        }
    }
}
```

This is a [partial update](../partial-updates.html).
So, assuming you already have a system up and running from the previous search tutorial,
you don't need to feed the entire corpus.
With a partial update, you only need to update the necessary fields.
So, after training another set of embeddings you can partially feed them again.
Please refer to [Vespa reads and writes](https://docs.vespa.ai/en/reads-and-writes.html)
for more information on feeding formats.

We need to add another document type to represent a user.
Add this schema in `schemas/user.sd`:

<pre data-test="file" data-path="news/my-app/schemas/user.sd">
schema user {
    document user {
        field user_id type string {
            indexing: summary | attribute
            attribute: fast-search
        }
        field embedding type tensor&lt;float&gt;(d0[51]) {
            indexing: summary | attribute
        }
    }
}
</pre>

This schema is set up so that we can search for a `user_id` and 
retrieve the user's embedding vector. 

We also need to let Vespa know we want to use this document type,
so we modify `services.xml` and add it under `documents` in the `content` section:

<pre data-test="file" data-path="news/my-app/services.xml">
&lt;?xml version="1.0" encoding="UTF-8"?&gt;
&lt;services version="1.0"&gt;

    &lt;container id="default" version="1.0"&gt;
        &lt;search&gt;&lt;/search&gt;
        &lt;document-api&gt;&lt;/document-api&gt;
        &lt;nodes&gt;
            &lt;node hostalias="node1"&gt;&lt;/node&gt;
        &lt;/nodes&gt;
    &lt;/container&gt;

    &lt;content id="mind" version="1.0"&gt;
        &lt;redundancy&gt;1&lt;/redundancy&gt;
        &lt;documents&gt;
            &lt;document type="news" mode="index"/&gt;
            &lt;document type="user" mode="index"/&gt;
        &lt;/documents&gt;
        &lt;nodes&gt;
            &lt;node hostalias="node1" distribution-key="0" /&gt;
        &lt;/nodes&gt;
    &lt;/content&gt;

&lt;/services&gt;
</pre>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app 
</pre>
</div>

<!-- Sometimes a query timeout, increase stability of auto testing -->
<pre data-test="exec" style="display:none">
$ sleep 20
</pre>

After redeploying with the updates schemas and `services.xml`,
feed `mind/vespa_user_embeddings.json` and `mind/vespa_news_embeddings.json`: 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --file mind/vespa_user_embeddings.json --endpoint http://localhost:8080
$ ./vespa-feed-client-cli/vespa-feed-client \
  --verbose --file mind/vespa_news_embeddings.json --endpoint http://localhost:8080
</pre>
</div>

Once the feeding jobs finishes our index is ready to be used, we can verify that we have 
28,603 news documents and 5000 user documents:

<!-- Sometimes a query timeout, increase stability of auto testing -->
<pre data-test="exec" style="display:none">
$ sleep 20
</pre>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='28603'>
$ vespa query -v 'yql=select * from news where true' 'hits=0'
</pre>
</div>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='5000'>
$ vespa query -v 'yql=select * from user where true' 'hits=0'
</pre>
</div>

## Query profiles and query profile types

Before we can test the application, we need to add a query profile type. The
`recommendation` rank profile above requires a tensor to be sent along with
the query. For Vespa to bind the correct types, it needs to know 
the expected type of this query parameter. That is called a query profile type.

[Query profiles](../query-profiles.html) are named sets of search request parameters
that can be set as default, so you don't have to pass them along with the query.
We don't use this in this sample application. Still we need to set up a default 
query profile to set up the types of query parameters we expect to pass. 

So, write the following to `news/my-app/search/query-profiles/default.xml`:

<pre data-test="file" data-path="news/my-app/search/query-profiles/default.xml">
&lt;query-profile id="default" type="root" /&gt;
</pre>

To set up the query profile types, write them to the file
`search/query-profiles/types/root.xml`:

<pre data-test="file" data-path="news/my-app/search/query-profiles/types/root.xml">
&lt;query-profile-type id="root" inherits="native"&gt;
    &lt;field name="ranking.features.query(user_embedding)" type="tensor&amp;lt;float&amp;gt;(d0[51])" /&gt;
&lt;/query-profile-type&gt;
</pre>

This configures Vespa to expect a float tensor with dimension `d0[51]` when the
query parameter `ranking.features.query(user_embedding)` is passed.
We'll see how this works together with the `nearestNeighbor` search operator below.

{% include important.html content="Setting up this query profile type is required when sending a tensor as a query parameter.
A common pitfall is to forget the default query profile,
but that is required to successfully set up the query profile type." %}

Deploy the updates to query profiles:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>

## Testing the application

We can now query Vespa using embeddings.
First, let's find the user `U33527`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='U33527'>
$ vespa query -v 'yql=select user_id, embedding from user where user_id contains "U33527"' 'hits=1'
</pre>
</div>

This returns the document containing the user's embedding:

```
{
  "root": {
    ...
    "children": [
      {
        "id": "id:user:user::U33527",
        "fields": {
          "sddocname": "user",
          "user_id": "U33527",
          "embedding": {
            "cells": [
              { "address": { "d0": "0" }, "value": 0.0 },
              { "address": { "d0": "1" }, "value": 1.0250849723815918 },
              ...
            ]
          }
        }
      }
    ]
  }
}
```
It's also possible to emit the tensor field using short format: 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='U33527'>
$ vespa query -v 'yql=select user_id, embedding from user where user_id contains "U33527"' \
 'hits=1' 'format.tensors=short'
</pre>
</div>


Now we can use this vector to query the news articles. You can either write this
query by hand, but we've added a convenience script which queries Vespa:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"documents": 28603'>
$ ./src/python/user_search.py U33527 10
</pre>
</div>

This script first retrieves the user embedding using an HTTP `GET` query to
Vespa. It then parses the tensor containing the embedding vector. Finally, it
issues a `nearestNeighbor` search using a `POST` (however a `GET` would work
just as well). Please see [the documentation for nearest-neighbor
operator](https://docs.vespa.ai/en/reference/query-language-reference.html#nearestneighbor)
for more on the syntax for nearest-neighbor searches. The `nearestNeighbor`
search looks like this:

```
{
    "hits": 10,
    "yql": "select * from sources news where (nearestNeighbor(embedding, user_embedding))',
    "ranking.features.query(user_embedding)": "{ ... }" ,
    "ranking.profile": "recommendation"
}
```

Here, you can see the `nearestNeighbor` search operator being set up 
so that the query parameter `user_embedding` will be searched against 
the `embedding` document field. The tensor for the `user_embedding` is 
in the `ranking.features.query(user_embedding)` parameter. Recall from 
above that we set a query profile type for this exact query parameter 
so Vespa knows what to expect here.

When Vespa receives this query, it will scan linearly through all documents
in the system (28603 if you are using the MIND DEMO dataset), and score them
using the `recommendation` rank profile we set up above. Recall that we
converted the problem from maximum inner product to euclidean distance.

However, Vespa sorts the final results by decreasing rank score. With a
euclidean distance search, we want to find the smallest distances. To invert
the rank order, Vespa provides the `closeness` feature which is calculated as
`1 / (1 + distance)`.

Let's test that this works as intended. The sample app provides the 
following script:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./src/python/evaluate.py mind 1000
</pre>
</div>

This reads both the training and validation set impressions, queries Vespa
for 1000 randomly drawn impressions, and calculates the same metrics we saw
during training. The result is something like:

```
Train: {'auc': 0.8774, 'mrr': 0.5115, 'ndcg@5': 0.5842, 'ndcg@10': 0.6345}
Valid: {'auc': 0.6308, 'mrr': 0.2935, 'ndcg@5': 0.3203, 'ndcg@10': 0.3789}
```

This is in line with the results from the training. So, the conversion 
from inner product space to euclidean space works as intended. The
resulting rank scores are different, but the transformation evidently 
retains the same ordering.


## Approximate Nearest Neighbor Search 

So far, we've been using exact nearest-neighbor search. This is a linear scan 
through all documents. For the MIND demo dataset we've been using,
this isn't a problem as it only contains roughly 28000 documents, and 
Vespa only uses a few milliseconds to scan through these. However, as 
the index grows, the time (and computional cost) becomes significant. 

Unfortunately, there are no exact methods for finding the nearest-neighbors
efficiently. So we trade accuracy for efficiency in what is called
approximate nearest-neighbors (ANN). Vespa provides a unique implementation 
of ANNs that uses the HNSW (hierarchical navigable small world) algorithm, 
while still being compatible with other facets of the search such as filtering.
We'll get back to this in the next section.

If you recall, Vespa returned something like the following when searching 
for single users above (with `targetHits` equals to 10):

```
  "root": {
    "id": "toplevel",
    "relevance": 1.0,
    "fields": {
      "totalCount": 95
    },
    "coverage": {
      "coverage": 100,
      "documents": 28603,
      "full": true,
      "nodes": 1,
      "results": 1,
      "resultsFull": 1
    },
    ...
```

Here, `coverage` shows that Vespa did scan through all 28603 documents. The 
interesting piece here is the `totalCount`. This number is the number of 
times a document has been put in the top 10 results during this linear scan.

Let's switch to using approximate nearest-neighbors by adding `index` to the embedding field in `news.sd`:

<pre data-test="file" data-path="news/my-app/schemas/news.sd">
schema news {
    document news {
        field news_id type string {
            indexing: summary | attribute
            attribute: fast-search
        }
        field category type string {
            indexing: summary | attribute
        }
        field subcategory type string {
            indexing: summary | attribute
        }
        field title type string {
            indexing: index | summary
            index: enable-bm25
        }
        field abstract type string {
            indexing: index | summary
            index: enable-bm25
        }
        field body type string {
            indexing: index | summary
            index: enable-bm25
        }
        field url type string {
            indexing: index | summary
        }
        field date type int {
            indexing: summary | attribute
            attribute: fast-search
        }
        field clicks type int {
            indexing: summary | attribute
        }
        field impressions type int {
            indexing: summary | attribute
        }
        field embedding type tensor&lt;float&gt;(d0[51]) {
            indexing: attribute | index
            attribute {
                distance-metric: euclidean
            }
        }
    }

    fieldset default {
        fields: title, abstract, body
    }

    rank-profile popularity inherits default {
        function popularity() {
            expression: if (attribute(impressions) &gt; 0, attribute(clicks) / attribute(impressions), 0)
        }
        first-phase {
            expression: nativeRank(title, abstract) + 10 * popularity
        }
    }

    rank-profile recommendation inherits default {
        first-phase {
          expression: closeness(field, embedding)
        }
    }
}
</pre>

If you make this change and deploy it, you will get prompted by Vespa that a
restart is required so that the index can be built:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>

Introducing the HNSW `index` requires a content node restart, in this case we restart all services:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker exec vespa /usr/bin/sh -c \
  '/opt/vespa/bin/vespa-stop-services &amp;&amp; /opt/vespa/bin/vespa-start-services'
</pre>
</div>

<!-- Give the container some time to reindex -->
<pre data-test="exec" style="display:none">
$ vespa status --wait 300 
</pre>


After doing this and waiting a bit for Vespa to start, we can query Vespa again:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ ./src/python/user_search.py U33527 10
</pre>
</div>

```
{
  "root": {
    "id": "toplevel",
    "relevance": 1.0,
    "fields": {
      "totalCount": 10
    },
    "coverage": {
      "coverage": 100,
      "documents": 28603,
      "full": true,
      "nodes": 1,
      "results": 1,
      "resultsFull": 1
    },
```

Here, `coverage` is still 100%, but the `totalCount` has been reduced to 
10 - the same number of hits we requested. By adding the index to this 
field, Vespa built a HNSW graph structure for the values in this field.
When used in an approximate nearest-neighbor search, this graph 
is queried and only the closest points as determined by this graph is 
added to the list. 

The particularly observant might have noticed that the result set 
has changed. Indeed, the third result when using exact nearest 
neighbor search was news article `N438`. This was omitted from 
the approximate search. As mentioned, we trade accuracy for efficiency 
when using approximate nearest-neighbor search.

It should also be mentioned that searching through this graph comes with a
cost. In our case, since we only have a relatively small amount of documents,
there isn't that much gain in efficiency. However, as the number of documents
grow, this starts to pay off. See [Approximate nearest neighbor search in
Vespa](https://blog.vespa.ai/approximate-nearest-neighbor-search-in-vespa-part-1/)
for more of a discussion around this. 
See also [Billion-scale vector search with Vespa - part one](https://blog.vespa.ai/billion-scale-knn/)
and [Billion-scale vector search with Vespa - part two](https://blog.vespa.ai/billion-scale-knn-part-two/)
which covers the many trade-offs related to approximate nearest neighbor search.

The implementation of ANN using HNSW in Vespa has some nice features.
Notice that we did not have to re-feed the corpus to enable ANN. Many 
other approaches for ANNs require building an index offline in a batch job.
HNSW allows for incrementally building this index, which is fully exploited 
in Vespa.

A unique feature of Vespa is that the implementation allows for filtering
during graph traversal, which we'll look at next.


## Filtering

A common case when using approximate nearest-neighbors is to combine 
with some additional query filters. For instance, for retail search, one
can imagine finding relevant products for a user. In this case, we should 
not recommend products that are out of stock. So an additional query 
filter would be to ensure that `in_stock` is true. 

Now, most implementations of ANNs come in the form of a library, so they are
not integrated with the search at large. The natural approach is to first
perform the ANN, the *post-filter* the results. Unfortunately, this often
leads to sub-optimal results as relevant documents might not have been
recalled. See [Using approximate nearest-neighbor search in real world
applications](https://blog.vespa.ai/using-approximate-nearest-neighbor-search-in-real-world-applications/)
for more of a discussion around this.

In our case, let's assume we want to retrieve 10 `sports` articles for a 
user. It turns out we need to retrieve at least 278 news articles from the 
search to get to 10 `sports` articles for this user:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ ./src/python/user_search.py U63195  10 | grep "category\": \"sports\"" | wc -l
$ ./src/python/user_search.py U63195 278 | grep "category\": \"sports\"" | wc -l
</pre>
</div>

On the other hand, if we add a filter specifically:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" >
$ ./src/python/user_search.py U63195 10 "AND category contains 'sports'" | \
    grep "category\": \"sports" | wc -l
</pre>
</div>

Here, we only specify 10 hits and exactly 10 hits of `sports` category are 
returned. Vespa still searches through the graph starting from the query 
point, however the search does not stop when we have 10 hits. In effect, 
the graph search widens until 10 results fulfilling the filters are found.

As a note, strict filters that filter away a large part of the 
corpus would entail that many candidates in the graph are skipped 
while searching for the results that fulfill the filters. This can take 
an exponential amount of time. For this case, Vespa falls back to 
a linear, brute-force search over the few documents which matches the filter for efficiency.


## Conclusion

We now have a basic recommendation system up and running. We can query 
for a user, retrieve the embedding vector and use that for querying
the news articles. Right now, this means two calls to Vespa. In 
the [next part of the tutorial](news-6-recommendation-with-searchers.html), we will introduce `searchers` which 
allows for custom logic during query processing inside the Vespa cluster, so we only 
need one client - vespa endpoint pass.

<script src="/js/process_pre.js"></script>
