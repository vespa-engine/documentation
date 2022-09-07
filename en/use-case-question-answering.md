---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Use Case - open-domain question-answering"
redirect_from:
- /documentation/use-case-question-answering.html
---

The [open-domain question-answering use
case](https://github.com/vespa-engine/sample-apps/tree/master/dense-passage-retrieval-with-ann)
is an example of an end-to-end question-answering application. Taking a textual
question, it returns a plain-text answer to the question. To start the
application, please follow the instructions in the
[README](https://github.com/vespa-engine/sample-apps/blob/master/dense-passage-retrieval-with-ann/README.md).

This sample application is an implementation of the [Dense Passage
Retriever](https://github.com/facebookresearch/DPR) system. Its full
version contains 21 million passages from Wikipedia that are retrieved using
either a sparse retrieval ([BM25](reference/bm25.html))
or a dense retrieval ([ANN](approximate-nn-hnsw.html)).
It then uses a BERT model to re-rank the passages and extract the most probable correct
answer.

After deploying the application, you can ask questions like this:

```
http://localhost:8080/search/?query=what+is+the+boiling+point+of+ethanol%3F
```

And Vespa will return the exact answer: `78.37 C`. This application uses the
[Natural Questions dataset](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00276/43518/Natural-Questions-A-Benchmark-for-Question).

### Highlighted features

* [Approximate nearest neighbors using an HNSW index](approximate-nn-hnsw.html)

    Vespa supports approximate nearest neighbors (ANN) by using Hierarchical
    Navigable Small World (HNSW) indexes. This allows for efficient similarity
    search in large collections. Vespa implements a modified HNSW index that
    allows for index building during feeding, so one does not have to build the
    index offline. It also supports additional query filters directly, thus
    avoiding the sub-optimal filtering after the ANN search.

* [Ranking with Transformer models](onnx.html)

    The Transformer architecture has revolutionized multiple fields after its
    introduction, starting with natural language understanding (NLU). This
    application uses two BERT models: one to transform the question to a
    representation vector for ANN search, the other to re-rank and extract the
    actual answer to the question.

* [ONNX model evaluation](onnx.html)

    The Transformer models are exported from [HuggingFace's Transformers
    library](https://huggingface.co/docs/transformers/index.html) to ONNX models.
    The [Open Neural Network Exchange](https://onnx.ai/) (ONNX) is an open
    standard for distributing machine-learned models between different systems.
    Vespa imports ONNX models and evaluates them using ONNX Runtime, ensuring
    efficient and correct inference.

* [Container components](jdisc/container-components.html)

    In Vespa, you can set up custom document or search processors to perform
    any extra processing during document feeding or during a query. This
    application uses this feature to generate token sequences from a WordPiece
    tokenizer. During feeding of a passage, its text is converted to a token
    sequence, which is stored along with the document. Likewise, the text of a
    query is converted to a token representation, which is used as input to the
    Transformer ONNX model inference.

* [Custom configuration](configuring-components.html)

    When creating custom components in Vespa, for instance, document processors,
    searchers, or handlers, one can use custom configuration to inject config
    parameters into the components. This involves defining a config definition
    (a `.def` file), which creates a config class. You can instantiate this
    class with data in `services.xml`, and the resulting object is dependency
    injected to the component during construction. This application uses custom
    config to set up the token vocabulary used in tokenization.

* [Multiple threads per query](reference/services-content.html#requestthreads)

    Vespa supports using multiple threads per query. This means that the
    ranking computation for handling a query can be split into multiple threads.
    This is useful for cases where ranking is computationally expensive. Vespa
    takes care of balancing the load between available threads.

    Note that this is different from multi-threaded ranking, where multiple
    queries are processed in parallel.

* [Text retrieval with BM25](reference/bm25.html)

    In addition to dense retrieval using ANN, this application shows, for
    comparison, text retrieval using BM25. The fields that have enabled
    a BM25 index (`enable-bm25`) use this index for retrieval.

* [Multi-phased ranking](phased-ranking.html)

    Vespa supports ranking over multiple phases. This is useful for expensive
    computation in ranking, for instance, when evaluating a large machine-learned
    model. In these cases, one can perform a fast first phase ranking and only
    perform the expensive computation on a smaller subset. This application first
    uses a euclidean score from the ANN and only evaluates the large
    Transformer model on the top 10 candidates.

* [Summary features](reference/schema-reference.html#summary-features)

    Summary features allow for customizing what is included with each hit.
    This application uses this to return the start and end indexes of the
    potential answer to a custom searcher component that extracts the most
    probably answer substring.
