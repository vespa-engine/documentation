---
# Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa Use Cases"
---

Vespa is a generic platform for Big Data Serving.
Find sample use cases below for popular uses cases for Vespa



## E-commerce: shopping and product catalog
Find a sample application at [E-commerce: shopping and product catalog](/documentation/use-case-shopping.html)

**Highlighted features**
* multiple document types
* partial updates
* custom handlers
* custom document
* processors
* custom configuration
* search using YQL
* grouping
* rank profiles
* rank functions



## Recommendations
Vespa is widely used as a recommendation engine,
recommening personalized articles, ads matching user profile and history, video recommendations, people matching.
Implementations vary from vector dot products to neural nets - both using tensors to represent models and data.

Read more  in the [blog recommendation tutorial](/documentation/tutorials/blog-recommendation.html).

**Highlighted features**
* Machine-learned models
* User profile lookup in Java plugin code



## Social Media
In social media, content is often _user generated_.
A used is hence related to the data elements, like _author_, _owner_ and so on.
This is a good use case for structured data and/or [parent/child](/documentation/parent-child.html).

Example 1: A user writes a comment to an article.
All comments from the same user have the same parent document.
As some users are better writers than others, comments can be ranked based on an author score.
Updating an author score is hence updating one document only.

Example 2: Users tag items.
A document can have a [multivalue field](/documentation/search-definitions.html#multivalue-fields)
like array to struct to save such data as tag value/timestamp/author.

**Highlighted features**
* No de-normalization needed - simplifies data updates (one write) and atomic update into all children
* Search child documents based on properties from parent documents
* Search parent documents only
* Multi-value field types like arrays and maps
* Struct field type



<!--
## Local Search
something here later

position
time
ranking
paid placement
-->



## Text Search
Vespa supports text search and [grouping](/documentation/grouping.html) (aggregation, faceting) - see the 
[blog search tutorial](/documentation/tutorials/blog-search.html).
Implement multi-phase [ranking](/documentation/ranking.html) to spend most resources on the most relevant hits.
Often enhanced withg auto-complete using [n-grams](/documentation/reference/search-definitions-reference.html#gram) 

Rank profiles are just mathematical expressions, to enable almost any kind of computation over a large data set.

For text search using BM25, see the [text search tutorial](/documentation/tutorials/text-search.html)

Use [tensors](/documentation/tensor-intro.html) to represent text embeddings and build a
[real time semantic search engine](/documentation/semantic-qa-retrieval.html).

**Highlighted features**
* Ranking
* Grouping
* ML models
* Tensors
* Auto-complete



## Personal Search
A search engine normally implements indexing structures like reverse indexes to reduce query latency.
It does _indexing_ up-front, so later matching and ranking is quick.
It also normally keeps a copy of the original document for later retrieval / use in search summaries.
Simplified, the engine keeps the original data plus auxiliary data structures to reduce query latency.
This induces both extra work - indexing - as compared to only store the raw data,
and extra static resource usage - disk, memory - to keep these structures.

[Streaming search](/documentation/streaming-search.html) is an alternative to indexed search.
It is useful in cases where the document corpus is statically split into many subsets
and all searches go to just one (or a few) of the small subsets.
The canonical example being personal indexes where a user only searches his own data.

**Highlighted features**
* Streaming search




