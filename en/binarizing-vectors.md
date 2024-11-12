---
# Copyright Vespa.ai. All rights reserved.
title: "Binarizing Vectors"
---

<style>
        /* Table styling */
        table {
            width: 100%;
        }
        th, td {
            padding: 5px;
        }
</style>

Binarization in this context is mapping numbers in a vector (embedding) to bits (reducing the value range),
and representing the vector of bits efficiently using the `int8` data type. Examples:

| input vector                                     | binarized floats                         |  pack_bits (to INT8) |
|--------------------------------------------------|------------------------------------------|---------------------:|
| [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]         | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] |                   -1 |
| [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]         | [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] |                    0 |
| [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0] | [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] |                    0 |
| [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]         | [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] |                 -128 |
| [2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]         | [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0] |                 -127 |

Binarization is key to reducing memory requirements and, therefore, cost.
Binarization can also improve feeding performance, as the memory bandwidth requirements go down accordingly.

Refer to [embedding](/en/embedding.html) for more details on how to create embeddings from text.


## Summary
This guide maps all the steps required to run a successful binarization project using Vespa only -
there is no need to re-feed data.
This makes a project feasible with limited incremental resource usage and man-hours required.

Approximate Nearest Neighbor vector operations are run using an HNSW index in Vespa, with online data structures.
The cluster is operational during the procedure, gradually building the required data structures.

This guide is useful to map the steps and tradeoffs made for a successful vector binarization.
Other relevant articles on how to reduce vector size in memory are:
* [Exploring the potential of OpenAI Matryoshka 🪆 embeddings with Vespa](https://blog.vespa.ai/matryoshka-embeddings-in-vespa/)
* [Matryoshka 🤝 Binary vectors: Slash vector search costs with Vespa](https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/)

Adding to this, using algorithms like SPANN can solve problems with huge vector data sizes,
read more in [Billion-scale vector search using hybrid HNSW-IF](https://blog.vespa.ai/vespa-hybrid-billion-scale-vector-search/).

A binarization project normally involves iteration over different configuration settings,
measuring quality loss for each iteration - this procedure it built with that in mind.


## Converters
Vespa’s built-in indexing language [converters](https://docs.vespa.ai/en/reference/indexing-language-reference.html#converters)
`binarize` and `pack_bits` let you easily generate binarized vectors.
Example schema definitions used to generate the vectors in the table above:

```
schema doc {

    document doc {
        field doc_embedding type tensor<float>(x[8]) {
            indexing: summary | attribute
        }
    }

    field doc_embedding_binarized_floats type tensor<float>(x[8]) {
        indexing: input doc_embedding | binarize | attribute
    }

    field doc_embedding_binarized type tensor<int8>(x[1]) {
        indexing: input doc_embedding | binarize | pack_bits | attribute
    }
}
```

We see that the `binarize` function itself will not compress vectors to a smaller size,
as the output cell type is the same as the input - it is only the values that are mapped to 0 or 1.
Above, the vectors are binarized using a threshold value of 0, the Vespa default -
any number > 0 will map to 1 - this threshold is configurable.

`pack_bits` reads binarized vectors and represents them using int8. In the example above:

* `tensor<float>(x[8])` is 8 x sizeof(float) = 8 x 32 bits = 256 bits = 32 bytes
* `tensor<int8>(x[1])` is 1 x sizeof(int8) = 1 x 8 bits = 8 bits = 1 byte

In other words, a compression factor of 32, which is expected, mapping a 32 bit float into 1 bit.

As memory usage often is the cost driver for applications, this has huge potential.
However, there is a loss of precision, so the tradeoff must be evaluated.
Read more in [billion-scale-knn](https://blog.vespa.ai/billion-scale-knn/) and
[combining-matryoshka-with-binary-quantization-using-embedder](https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/). 


## Binarizing an existing embedding field
In the example above, we see that `doc_embedding` has the original embedding data,
and the fields `doc_embedding_binarized_floats` and `doc_embedding_binarized` are generated from `doc_embedding`.
This is configured through the `indexing: input …` statement,
and defining the generated fields outside the `document { … }` block.

{% include note.html content='The `doc_embedding_binarized_floats` field is just for illustration purposes,
as input to the `doc_embedding_binarized` field, which is the target binarized and packed field with low memory requirements.
From here, we will call this the binarized embedding.' %}

This is a common case for many applications - how to safely binarize and evaluate the binarized data for subsequent use.
The process can be broken down into:
* Pre-requisites.
* Define the new binarized embedding, normally as an addition to the original field.
* Deploy and re-index the data to populate the binarized embedding.
* Create new ranking profiles with the binarized embeddings.
* Evaluate the quality of the binarized embedding.
* Remove the original embedding field from memory to save cost.


## Pre-requisites
Adding a new field takes resources, on disk and in memory.
A new binarized embedding field is smaller - above, it is 1/32 of the original field.
Also note that embedding fields often have an index configured, like:

```
field doc_embeddings type tensor<float>(x[8]) {
    indexing: summary | attribute | index
    attribute {
        distance-metric: angular
    }
    index {
        hnsw {
            max-links-per-node: 16
            neighbors-to-explore-at-insert: 100
        }
    }
}
```

The index is used for approximate nearest neighbor (ANN) searches, and also consumes memory.

Use the Vespa Cloud console to evaluate the size of original fields and size of indexes to make sure that there is room for the new embedding field, possibly with an index.

{% include note.html content='The size of an index is a function of the number of documents, regardless of tensor type.
In this context, this means that adding a new field with and index,
the new index will have the same size as the index of the existing embedding field.' %}

Use status pages to find the index size in memory - example:

https://api-ctl.vespa-cloud.com/application/v4/tenant/\
TENANT_NAME/application/APP_NAME/instance/INSTANCE_NAME/environment/prod/region/REGION/\
service/searchnode/NODE_HOSTNAME/\
state/v1/custom/component/documentdb/SCHEMA/subdb/ready/attribute/ATTRIBUTE_NAME

### Example
<pre>
tensor: {
    compact_generation: 33946879,
    ref_vector: {
        memory_usage: {
            used: 1402202052,
            dead: 0,
            allocated: 1600126976,
            onHold: 0
        }
    },
    tensor_store: {
        memory_usage: {
            used: 205348904436,
            dead: 10248636768,
            allocated: <span class="pre-hilite">206719921232</span>,
            onHold: 0
        }
    },
    nearest_neighbor_index: {
        memory_usage: {
            all: {
                used: 10452397992,
                dead: 360247164,
                allocated: <span class="pre-hilite">13346516304</span>,
                onHold: 0
            }
</pre>

In this example, the index is 13G, the tensor data is 206G, so the index is 6.3% of the tensor data.
The original tensor is of type `bfloat16`, a binarized version is 1/16 of this and hence 13G.
As an extra index is 13G, the temporal incremental memory usage is approximately 26G during the procedure.

<!-- ToDo: There must be an easy way to guesstimate the HNSW index size from number of vectors? -->


## Define the binarized embedding field
The new field is _added_ to the schema, example schema, before:
```
schema doc {

    document doc {
        field doc_embedding type tensor<float>(x[8]) {
            indexing: summary | attribute
        }
    }
}
```

After:
```
schema doc {

    document doc {
        field doc_embedding type tensor<float>(x[8]) {
            indexing: summary | attribute
        }
    }

    field doc_embedding_binarized type tensor<int8>(x[1]) {
        indexing: input doc_embedding | binarize | pack_bits | attribute
    }
}
```

The above are simple examples, with no ANN settings on the fields.
Following is a more complex example - schema before:

```
schema doc {

    document doc {
        field doc_embedding type tensor<float>(x[8]) {
            indexing: summary | attribute | index
            attribute {
                distance-metric: angular
            }
            index {
                hnsw {
                    max-links-per-node: 16
                    neighbors-to-explore-at-insert: 200
                }
            }
        }
    }
}
```

Schema after:
```
schema doc {

    document doc {
        field doc_embedding type tensor<float>(x[8]) {
            indexing: summary | attribute | index
            attribute {
                distance-metric: angular
            }
            index {
                hnsw {
                    max-links-per-node: 16
                    neighbors-to-explore-at-insert: 200
                }
            }
        }
    }

    field doc_embedding_binarized type tensor<int8>(x[1]) {
        indexing: input doc_embedding | binarize | pack_bits | attribute | index
        attribute {
            distance-metric: hamming
        }
        index {
            hnsw {
                max-links-per-node: 16
                neighbors-to-explore-at-insert: 200
            }
        }
    }
}
```

Note that we replicate the index settings to the new field.


## Deploy and reindex the binarized embedding field
Deploying the field will trigger a reindexing on Vespa Cloud to populate the binarized embedding, fully automated.

Self-hosted, the `deploy` operation will output the below - [trigger a reindex](/en/operations/reindexing.html).

```
$ vespa deploy

Uploading application package... done

Success: Deployed '.' with session ID 3
WARNING Change(s) between active and new application that may require re-index:
reindexing: Consider re-indexing document type 'doc' in cluster 'doc' because:
    1) Document type 'doc': Non-document field 'doc_embedding_binarized' added; this may be populated by reindexing
```

Depending on the size of the corpus and resources configured, the reindexing process takes time.
<!-- TODO: how to observe this -->


## Create new ranking profiles and queries using the binarized embeddings
After reindexing, you can query using the new, binarized embedding field.
Assuming a query using the doc_embedding field:

```
$ vespa query \
    'yql=select * from doc where {targetHits:5}nearestNeighbor(doc_embedding, q)' \
    'input.query(q)=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]' \
    'ranking=app_ranking'
```

The same query, with a binarized query vector, to the binarized field:

```
$ vespa query \
    'yql=select * from doc where {targetHits:5}nearestNeighbor(doc_embedding_binarized, q)' \
    'input.query(q)=[-119]' \
    'ranking=app_ranking_bin'
```

See [tensor-hex-dump](https://docs.vespa.ai/en/reference/document-json-format.html#tensor-hex-dump)
for more information about how to create the int8-typed tensor.


### Quick Hamming distance intro
Example embeddings:

| document embedding                               | binarized floats                           | pack_bits (to INT8) |
|--------------------------------------------------|--------------------------------------------|--------------------:|
| [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0] | [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   |                   0 |
| **query embedding**                              | **binarized floats**                       |         **to INT8** |
| [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]         | [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]   |                -119 |


Use [matchfeatures](https://docs.vespa.ai/en/reference/schema-reference.html#match-features)
to debug ranking (see ranking profile `app_ranking_bin` below):
```json
"matchfeatures": {
    "attribute(doc_embedding_binarized)": {
    "type": "tensor<int8>(x[1])",
    "values": [ 0 ]
    },
    "distance(field,doc_embedding_binarized)": 3.0,
    "query(q)": {
        "type": "tensor<int8>(x[1])",
        "values": [ -119 ]
    }
}
```

See distance calculated to 3.0, which is the number of bits different in the binarized vectors, which is the hamming distance.


## Rank profiles and queries
Assuming a rank profile like:

```
rank-profile app_ranking {
    match-features {
        distance(field, doc_embedding)
        query(q)
        attribute(doc_embedding)
    }
    inputs {
        query(q) tensor<float>(x[8])
    }
    first-phase {
        expression: closeness(field, doc_embedding)
    }
}
```

Query:
```
$ vespa query \
    'yql=select * from doc where {targetHits:5}nearestNeighbor(doc_embedding, q)' \
    'input.query(q)=[2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]' \
    'ranking=app_ranking'
```

A binarized version is like:

```
rank-profile app_ranking_bin {
    match-features {
        distance(field, doc_embedding_binarized)
        query(q)
        attribute(doc_embedding_binarized)
    }
    inputs {
        query(q) tensor<int8>(x[1])
    }
    first-phase {
        expression: closeness(field, doc_embedding_binarized)
    }
}
```

Query:

```
$ vespa query \
    'yql=select * from doc where {targetHits:5}nearestNeighbor(doc_embedding_binarized, q)' \
    'input.query(q_bin)=[-119]' \
    'ranking=app_ranking_bin'
```

Query with full-precision query vector, against a binarized vector - rank profile:

```
rank-profile app_ranking_bin_full {
    match-features {
        distance(field, doc_embedding_binarized)
        query(q)
        query(q_bin)
        attribute(doc_embedding_binarized)
    }
    function unpack_to_float() {
        expression: 2*unpack_bits(attribute(doc_embedding_binarized), float)-1
    }
    function dot_product() {
        expression: sum(query(q) * unpack_to_float)
    }
    inputs {
        query(q)     tensor<float>(x[8])
        query(q_bin) tensor<int8>(x[1])
    }
    first-phase {
        expression: closeness(field, doc_embedding_binarized)
    }
    second-phase {
        expression: dot_product
    }
}
```

Notes:
* The first-phase ranking is as the binarized query above.
* The second-phase ranking is using the full-precision query vector query(q)
  with a bit-precision vector casted to float for type match.
* Both query vectors must be supplied in the query.

Note the differences when using full values in the query tensor, see the relevance score for the results:
```
$ vespa query \
    'yql=select * from music where {targetHits:5}nearestNeighbor(doc_embedding_binarized, q_bin)' \
    'input.query(q)=[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]' \
    'input.query(q_bin)=[-119]' \
    'ranking=app_ranking_bin_full'

...

"relevance": 3.0
```

```
$ vespa query \
    'yql=select * from music where {targetHits:5}nearestNeighbor(doc_embedding_binarized, q_bin)' \
    'input.query(q)=[2.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]' \
    'input.query(q_bin)=[-119]' \
    'ranking=app_ranking_bin_full'

"relevance": 4.0
```

Read the [closeness](https://docs.vespa.ai/en/reference/rank-features.html#closeness(dimension,name)) reference documentation.


### TargetHits for ANN
Given the lower precision with binarization, it might be a good idea to increase the `{targetHits:5}` annotation in the query,
to generate more candidates for later ranking phases.


## Evaluate the quality of the binarized embeddings
This exercise is about evaluating a lower-precision retrieval phase,
using the original full-sized (here we use floats) query-result pairs as reference.
Experiments, query-document precision:
1. float-float
2. binarized-binarized
3. float-binarized
4. float-float, with binarized retrieval

To evaluate the precision, compute the differences for each query @10, like:
```python
def compute_list_differences(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    return len(set1 - set2)


list1 = [1, 3, 5, 7, 9, 11, 13, 15, 17, 20]
list2 = [2, 3, 5, 7, 9, 11, 14, 15, 18, 20]
num_hits = compute_list_differences(list1, list2)
print(f"Hits different: {num_hits}")
```


## Remove the original embedding field from memory
The purpose of the binarization is reducing memory footprint.
Given the results of the evaluation above, store the full-precision embeddings on disk or remove them altogether.
Example with paging the attribute to disk-only:
```
schema doc {

    document doc {
        field doc_embedding type tensor<float>(x[8]) {
            indexing: summary | attribute | index
            attribute: paged
        }
    }

    field doc_embedding_binarized type tensor<int8>(x[1]) {
        indexing: input doc_embedding | binarize | pack_bits | attribute | index
        attribute {
            distance-metric: hamming
        }
        index {
            hnsw {
                max-links-per-node: 16
                neighbors-to-explore-at-insert: 200
            }
        }
    }
}
```

This example only indexes the binarized embedding, with data binarized before indexing:

```
schema doc {

    document doc {
        field doc_embedding_binarized type tensor<int8>(x[1]) {
            indexing: input doc_embedding | binarize | pack_bits | attribute | index
            attribute {
                distance-metric: hamming
            }
            index {
                hnsw {
                    max-links-per-node: 16
                    neighbors-to-explore-at-insert: 200
                }
            }
        }
    }
}
```



## Appendix: Binarizing from text input
To generate the embedding from other data types, like text,
use the [converters](https://docs.vespa.ai/en/reference/indexing-language-reference.html#converters) - example:

```
    field doc_embedding type tensor<int8>(x[1]) {
        indexing: (input title || "") . " " . (input content || "") | embed | attribute
        attribute {
            distance-metric: hamming
        }
    }
```

Find examples in [Matryoshka 🤝 Binary vectors: Slash vector search costs with Vespa](https://blog.vespa.ai/combining-matryoshka-with-binary-quantization-using-embedder/).


## Appendix: conversion to int8
Find examples of how to binarize values in code:

```python
import numpy as np


def floats_to_bits(floats):
    if len(floats) != 8:
        raise ValueError("Input must be a list of 8 floats.")
    bits = [1 if f > 0 else 0 for f in floats]
    return bits


def bits_to_int8(bits):
    bit_string = ''.join(str(bit) for bit in bits)
    int_value = int(bit_string, 2)
    int8_value = np.int8(int_value)
    return int8_value


def floats_to_int8(floats):
    bits = floats_to_bits(floats)
    int8_value = bits_to_int8(bits)
    return int8_value


floats = [0.5, -1.2, 3.4, 0.0, -0.5, 2.3, -4.5, 1.2]
int8_value = floats_to_int8(floats)
print(f"The int8 value is: {int8_value}")
```


```python
import numpy as np


def binarize_tensor(tensor: torch.Tensor) -> str:
    """
    Binarize a floating-point 1-d tensor by thresholding at zero
    and packing the bits into bytes. Returns the hex str representation of the bytes.
    """
    if not tensor.is_floating_point():
        raise ValueError("Input tensor must be of floating-point type.")
    return (
        np.packbits(np.where(tensor > 0, 1, 0), axis=0).astype(np.int8).tobytes().hex()
    )
```


Multivector example, from
[ColPali: Efficient Document Retrieval with Vision Language Models](https://pyvespa.readthedocs.io/en/latest/examples/colpali-document-retrieval-vision-language-models-cloud.html):

```python
import numpy as np
from typing import Dict, List
from binascii import hexlify


def binarize_token_vectors_hex(vectors: List[torch.Tensor]) -> Dict[str, str]:
    vespa_tensor = list()
    for page_id in range(0, len(vectors)):
        page_vector = vectors[page_id]
        binarized_token_vectors = np.packbits(
            np.where(page_vector > 0, 1, 0), axis=1
        ).astype(np.int8)
        for patch_index in range(0, len(page_vector)):
            values = str(
                hexlify(binarized_token_vectors[patch_index].tobytes()), "utf-8"
            )
            if (
                values == "00000000000000000000000000000000"
            ):  # skip empty vectors due to padding of batch
                continue
            vespa_tensor_cell = {
                "address": {"page": page_id, "patch": patch_index},
                "values": values,
            }
        vespa_tensor.append(vespa_tensor_cell)

    return vespa_tensor
```
