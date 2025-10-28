---
# Copyright Vespa.ai. All rights reserved.
title: "Indexing paged vectors"
---

Most of the data of a vector (tensor) index is the vectors themselves.
The vector data must be accessed to calculate true distances both when querying the index and when adding vectors to it,
and due to the high dimensionality these accesses are effectively random.
While it is viable to [page](attributes.html#paged-attributes)
indexed vector attributes to disk for *queries* if somewhat higher latency can be tolerated,
it does not allow a large vector index to be built at reasonable speed: To create a high quality index,
each vector insert must make many distance calculations, which results in low write throughput
when the vectors in the index do not reside in RAM.

To build vector indexes larger than available memory efficiently the procedure described here can be used.
This is suitable when:
* You want to build an index for vector retrieval (not just store the vectors for ranking/brute force NN),
  with a vector data set that doesn't fit in memory across the content nodes you want to deploy for it.
* The vector data in question is mostly write-once (frequent writes to other fields is fine),
  and rescaling of the content cluster will not be necessary.

## Steps

1. Declare the vector field(s) to be indexed as `paged`.

   ```
       schema docs {
           document docs {
               field myVectors type tensor<bfloat16>(chunk{}, x[384]) {
                   indexing: attribute | index
                   attribute: paged
               }
           }
       }
   ```
2. Calculate how much data you can fit in memory:

   Calculate your attribute raw data size (taking just the vector is close enough unless you have many other attribute fields),
   multiply by the number of [searchable-copies](reference/services-content.html#searchable-copies) you want,
   multiply by 1.2 to add room for the index over the vectors,
   divide by 0.65 to leave room for working memory,
   multiply by your total number of documents.

   This gives you the total memory needed across all the nodes in your content cluster (or across one group if you have multiple).
   **Example** with the type above with 1B documents and 10 chunks average per document:
   10 * 384*2 bytes * 2 * 1.2 / 0.65 * 1B = 14.178 Gb total cluster memory.
3. Create one document type per data subset which fits in memory under the calculation above.
   **Example:** Suppose you want to create a vector index over four years worth of documents of type `docs`
   and that you only want to allocate enough memory to fit 25% of the vector data across the cluster.
   Create four subtypes of `docs`, one for each year: docs2021, docs2022, docs2023 and docs 2024,
   in four different schema files. Each of these can inherit the parent type and otherwise be empty:

   ```
       schema docs2021 inherits docs {
           document docs2021 inherits docs {
           }
       }
   ```

   You can of course also add time-period-specific fields and ranking here.
4. Add all the subtypes to the content cluster you want in services.xml:

   ```
       <content id="myClusterId" version="1.0">
           <documents>
               <document type="docs2021" mode="index" />
               <document type="docs2022" mode="index" />
               ...
           </documents>
   ```
5. Feed each of the types completely one by one, without applying queries at the same time.- Once all the types are written, you can apply query traffic. Vespa will search across all the types by default,
     but it is possible to restrict to a subset using the
     [restrict](reference/query-api-reference.html#model.restrict) query parameter.
