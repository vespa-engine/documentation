---
# Copyright Vespa.ai. All rights reserved.
title: "Working with chunks"
---

A key technique in RAG applications, and vector search applications in general, is to split longer text into
chunks. This lets you:
* Generate a vector embedding for each chunk rather than for an entire document text, to capture the semantic information
  of the text at a meaningful level.* Select specific chunks to add to the context window in GenAI applications rather than the entire document content.

Vespa contains the following functionality for working with chunks. Each is covered in a section below.
* [Including chunks in documents](#including-chunks-in-documents)
* [Creating vector embeddings from chunks](#creating-vector-embeddings-from-chunks)
* [Searching chunks](#searching-chunks)
* [Ranking with chunks](#ranking-with-chunks)
* [Layered ranking: Selecting chunks to return](#layered-ranking-selecting-chunks-to-return)

## Including chunks in documents

Chunks that belong to the same text should be added to the same document.
The chunks are represented as arrays of string.

You can split text into chunks yourself, using a schema like this:

```
search myDocumentType {
    document myDocumentType {
        field myChunks type array<string> {
            indexing: summary | index
        }
    }
}
```

You can then write your chunks into Vespa using this [document JSON](reference/document-json-format.html):

```
"myChunks": ["My first chunk text", "My second chunk text"]
```

Alternatively you can let Vespa do the chunking for you, by using a synthetic field outside the document:

```
search myDocumentType {
    document myDocumentType {
        field myText type string {
        }
    }
    field myChunks type array<string> {
        indexing: input myText | chunk fixed-length 500 | summary | index
    }
}
```

In the [chunk expression](reference/indexing-language-reference.html#chunk)
you can choose between chunkers provided by Vespa, or plug in your own,
see the [chunking reference documentation](reference/chunking-reference.html).

## Creating vector embeddings from chunks

To add embeddings to your documents, use a tensor field:

```
search myDocumentType {
    document myDocumentType {
        field myEmbedding type tensor<float>(x[384]) {
            indexing: attribute | index
        }
    }
}
```

This lets you add a single embedding to each document, but usually you want to have many.
In Vespa you can do that by adding [mapped dimensions](tensor-user-guide.html#tensor-concepts)
to your tensor:

```
search myDocumentType {
    document myDocumentType {
        field myEmbeddings type tensor<float>(chunk{}, x[384]) {
            indexing: attribute | index
        }
    }
}
```

With this you can feed [tensors in JSON format](reference/document-json-format.html#tensor-short-form-mixed)
as part of your writes, e.g. writing an embedding tensor with chunks numbered 1 and 2:

```
"myEmbeddings": {
    "1":[2.0,3.0,...],
    "2":[4.0,5.0,...]
}
```

You may notice that parsing such JSON consumes a lot of CPU on container clusters. To avoid that you can also feed
embeddings [hex encoded raw data](reference/document-json-format.html#tensor-hex-dump).

You can also let Vespa do the embedding for you, either using a model provided by Vespa,
or one you decide in your application package:

```
search myDocumentType {
    document myDocumentType {
        field myChunks type array<string> {
        }
    }
    field myEmbeddings type tensor<float>(chunk{}, x[384]) {
        indexing: input myChunks | embed | attribute | index
    }
}
```

See the [embedding guide](embedding.html) on how to configure embedders.

You can of course combine this with chunking to have a single text field
chunked and embedded automatically:

```
search myDocumentType {
    document myDocumentType {
        field myText type string {
        }
    }
    field myChunks type array<string> {
        indexing: input myText | chunk sentence | summary | index
    }
    field myEmbeddings type tensor<float>(chunk{}, x[384]) {
        indexing: input myText | chunk sentence | embed | attribute | index
    }
}
```

Some things to note:
* All fields of Vespa documents are stored and here we represent the text both as a single field and as
  chunks of text, won't that consume a lot of unnecessary space? No, thanks to the wonders of modern compression,
  the overhead from this can be ignored.* Why return the chunk array in results and not the full text field? This is because for large text we need to
    select a subset of the text chunks rather than returning the full text.* We are chunking twice here, won't this be inefficient? No, Vespa will reuse the result of the first invocation
      in cases like this.

## Searching chunks

You can search in chunk text (if you added `index`), and in chunk embeddings (if you created embeddings).
Usually, you want to do both ([hybrid search](/en/tutorials/hybrid-search.html))
since text search gives you precise matches, and embedding nearest neighbor search gives you imprecise semantic matching.

A simple hybrid query can look like this:

```
yql=select * from doc where userInput(@query) or ({targetHits:10}nearestNeighbor(myEmbeddings, e))
input.query(e)=embed(@query)
query=Do Cholesterol Statin Drugs Cause Breast Cancer?
```

The `embed` function shown here can be used to embed a query text using the same model(s) as used for chunks.
If embedding outside Vespa you can
[pass the tensor value](https://docs.vespa.ai/en/reference/tensor.html#tensor-literal-form) instead. See the
[nearest neighbor guide](/en/nearest-neighbor-search-guide.html#hybrid-sparse-and-dense-retrieval-methods-with-vespa)
for more.

Text matching works across chunks as if the chunks were re-joined into one text field. However, a proximity
gap is inserted between each chunks so that tokens in different chunks are by default very (infinitely) far away when
evaluating phrase and near matches (however, see
[on configuring this](reference/schema-reference.html#rank-element-gap)).

Nearest neighbor search with many chunks will retrieve the documents where any single chunk embedding
is close to the query embedding.

## Ranking with chunks

Ranking in Vespa is done by [mathematical expressions](ranking-expressions-features.html)
(hand-written or machine-learned) combining rank features. You'll typically want to use features that capture
both how well vector embeddings and textual query terms matched the chunks.

For vector search, the `closeness(dimension,field)` feature will contain the distance between the
query vector and the *closest* chunk embedding. In addition, the `closest(field)`
feature will return a tensor providing the label(s) of the chunk which was closest.

For text matching, all features are available as if the entire chunk array was a single string field, but with
an infinitely large proximity gap between each element to treat each element as independent. When the array elements
are chunks of the same text, you'd prefer to get a relevance contribution from matching adjacent elements since it means
you are matching adjacent words in the source text. To achieve this, configure the elementGap in your chunk array to
a low value (e.g. 0 to 3, depending on how well your chunking strategy identifies semantic transitions):

```
    rank-profile myProfile {
        rank myChunks {
            element-gap: 1
        }
    }
```

Using vector closeness and the normal text match features will help you rank documents mostly based
on the text having the single best match to the query. Sometimes it is also useful to capture how well the
text as a whole matches the query. For vectors, you can do this by computing and aggregating closeness
to each vector using a [tensor expression](https://docs.vespa.ai/en/tensor-user-guide.html#ranking-with-tensors)
in your ranking expression, while for text matching you can use the `elementSimilarity(field)` feature,
or the `elementwise(bm25(field),dimension,cell_type)`
feature which returns a tensor containing the bm25 score of each chunk.

## Layered ranking: Selecting chunks to return

A search result will contain the top ranked documents including all fields you are requesting or
[configuring](https://docs.vespa.ai/en/document-summaries.html#), including all chunks of those documents,
whether relevant or not. This is fine when every document has few chunks, but when they can have many, there
are two problems:
* Putting many irrelevant chunks into the context window of the LLM decreases quality, or may
  make the context window infeasibly large.
* Sending many chunks over the network increases latency and can impacting other queries
  running at the same time.

To solve both of these, we can use
[layered ranking](https://blog.vespa.ai/introducing-layered-ranking-for-rag-applications/):
Rank the chunks in the highest ranked documents, and select only the best ones.

To do this, specify the ranking function that will select the chunks to return,
using `select-elements-by`.
Here's a full example:

```
schema docs {
    document docs {

        field myEmbeddings type tensor<float>(chunk{}, x[386]) {
            indexing: attribute
        }

        field myChunks type array<string> {
            indexing: index | summary
            summary {
                select-elements-by: best_chunks
            }
        }

    }

    rank-profile default {

        inputs {
            query(embedding) tensor<float>(x[386])
        }

        function my_distance() {
            expression: euclidean_distance(query(embedding), attribute(myEmbeddings), x)
        }

        function my_distance_scores() {
            expression: 1 / (1+my_distance)
        }

        function my_text_scores() {
            expression: elementwise(bm25(myChunks), chunk, float)
        }

        function chunk_scores() {
            expression: merge(my_distance_scores, my_text_scores, f(a,b)(a+b))
        }

        function best_chunks() {
            expression: top(3, chunk_scores)
        }

        first-phase {
            expression: sum(chunk_scores())
        }

        summary-features {
            best_chunks
        }

    }
}
```

With this, we can use the powerful ranking framework in Vespa to select the best chunks to provide to the LLM,
without sending any chunks that won't be used over the network.
