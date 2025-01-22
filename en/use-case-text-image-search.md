---
# Copyright Vespa.ai. All rights reserved.
title: "Use Case - Text-Image Search"
---

The [text-image use case](https://github.com/vespa-engine/sample-apps/tree/master/text-image-search/) is an example
of a text-to-image search application.
Taking a textual query, such as "two people bicycling", it will return images containing two people on bikes.
This application is built using [CLIP (Contrastive Language-Image
Pre-Training)](https://github.com/openai/CLIP) which enables "zero-shot prediction".
This means that the system can return sensible results for images it hasn't
seen during training, allowing it to process and index any image. In this
use case, we use the [Flickr8k](https://github.com/jbrownlee/Datasets/blob/master/Flickr8k_Dataset.names)
dataset, which was not used during training of the CLIP model.


To start the application, follow the instructions in the
[README](https://github.com/vespa-engine/sample-apps/blob/master/text-image-search/README.md).
After deploying the application, you can ask questions like:

```
http://localhost:8080/search/?input=two+people+bicylcing
```

### Highlighted features


* [Approximate nearest neighbors using an HNSW index](approximate-nn-hnsw.html)

    Vespa supports approximate nearest neighbors (ANN) by using Hierarchical
    Navigable Small World (HNSW) indexes. This allows for efficient similarity
    search in large collections. Vespa implements a modified HNSW index that
    allows for index building during feeding, so one does not have to build the
    index offline. It also supports additional query filters directly, thus
    avoiding the suboptimal filtering after the ANN search.

* [Stateless model evaluation](stateless-model-evaluation.html)

    The Vespa application uses a Transformer model to create an embedding
    representation of the input. This is done in a custom searcher to
    transform the text to the representation before sending it to the backend
    for the ANN search.

* [Container components](jdisc/container-components.html)

    In Vespa, you can set up custom document or search processors to perform
    extra processing during document feeding or a query. This application uses
    this feature to create embedding representations by first tokenizing the
    input string using a Byte-Pair Encoding (BPE) tokenizer.

* [Custom configuration](configuring-components.html)

    When creating custom components in Vespa, for instance, document processors,
    searchers, or handlers, one can use custom configuration to inject config
    parameters into the components. This involves defining a config definition
    (a `.def` file), which creates a config class. You can instantiate this
    class with data in `services.xml`, and the resulting object is dependency
    injected to the component during construction. This application uses custom
    config to set up the token vocabulary used in tokenization.
