---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa Serving Tuning"
---

This document describes how to tune certain features of an application for high query serving performance,
where the main focus is on content cluster search features;
see [Container tuning](container-tuning.html) for tuning of container clusters.
The [search sizing guide](sizing-search.html) is about *scaling* an application deployment.

## Attribute vs index

The [attribute](../attributes.html) documentation summarizes when to use
[attribute](../reference/schema-reference.html#attribute)
in the [indexing](../reference/schema-reference.html#indexing) statement.
Also see the [procedure](/en/schemas.html#schema-modifications)
for changing from attribute to index and vice-versa.

```
field timestamp type long {
    indexing: summary | attribute
}
```

If both index and attribute are configured for string-type fields,
Vespa will search and match against the index with default match `text`.
All numeric type fields and tensor fields are attribute (in-memory) fields in Vespa.

## When to use fast-search for attribute fields

By default, Vespa does not build any posting list index structures over *attribute* fields.
Adding *fast-search* to the attribute definition as shown below
will add an in-memory B-tree posting list structure
which enables faster search for some cases (but not all, see next paragraph):

```
field timestamp type long {
    indexing:  summary | attribute
    attribute: fast-search
    rank:      filter
}
```

When Vespa runs a query with multiple query items, it builds a query execution plan.
It tries to optimize the plan so that the temporary result set is as small as possible.
To do this, restrictive query tree items (matching few documents) are evaluated early.
The query execution plan looks at hit count estimates for each part of the query tree
using the index and B-tree dictionaries, which track the number of documents in which a given term occurs.

However, for attribute fields without [fast-search](../attributes.html#fast-search)
there is no hit count estimate,
so the estimate becomes the total number of documents (matches all)
and the query tree item is moved to the end of the query evaluation.
A query with only one query term searching an attribute field without `fast-search`
would be a linear scan over all documents and thus expensive:

```
select * from sources * where range(timestamp, 0, 100)
```

But if this query term is *and*-ed with another term that matches fewer documents,
that term will determine the cost instead, and fast-search won't be necessary, e.g.:

```
select * from sources * where range(timestamp, 0, 100) and uuid contains "123e4567-e89b-12d3-a456-426655440000"
```

The general rules of thumb for when to use fast-search for an attribute field are:
* Use *fast-search* if the attribute field is searched without any other query terms
* Use *fast-search* if the attribute field could limit the total number of hits efficiently

Changing fast-search aspect of the attribute is a
[live change](../reference/schema-reference.html#modifying-schemas)
which does not require any re-feeding, so testing the performance with and without is low effort.
Adding or removing *fast-search* requires restart.

Note that *attribute* fields with *fast-search* that are not used in term based
[ranking](../ranking.html) should use *rank: filter*
for optimal performance. See reference [rank: filter](../reference/schema-reference.html#rank).

See optimization for sorting on a *single-value numeric attribute with fast-search* using
[sorting.degrading](../reference/query-api-reference.html#sorting.degrading).

## Tuning query performance for lexical search

Lexical search (or keyword-based search) is a method that matches query terms as they appear in indexed documents.
It relies on the lexical representation of words rather than their meaning, and is one of the two retrieval methods used in
[hybrid search](../tutorials/hybrid-search.html).
Lexical search in Vespa is done by querying string (text) [index](../schemas.html#indexing) fields,
typically using the [weakAnd](../using-wand-with-vespa.html#weakand) query operator with [BM25](../reference/bm25.html) ranking.

The following schema represents a simple article document with *title* and *content* fields,
that can represent Wikipedia articles as an example.
A *default* fieldset is specified such that user queries are matched against both the *title* and *content* fields.
BM25 ranking combines the scores of both fields in the *default* rank profile.
In addition, the *optimized* rank profile specifies tuning parameters to improve query performance:

```
schema article {
    document article {
        field title type string {
            indexing: index | summary
            index: enable-bm25
        }
        field content type string {
            indexing: index | summary
            index: enable-bm25
        }
    }

    fieldset default {
        fields: title, content
    }

    rank-profile default {
        first-phase {
            expression: bm25(title) + bm25(content)
        }
    }

    rank-profile optimized inherits default {
        filter-threshold: 0.05
        weakand {
            stopword-limit: 0.6
            adjust-target: 0.01
        }
    }
}
```

The following shows an example question-answer query against a collection of articles,
using the *weakAnd* query operator and the *optimized* rank profile.
Question-answer queries are often written in full sentences, and as a consequence,
they tend to contain many stopwords that are present in many documents and of less relevance when it comes to ranking.
E.g., terms as "the", "in", and "are" are typically present in more the 60% of the documents:

```
{% highlight json %}
{
  "yql": "select * from article where userQuery()",
  "ranking.profile": "optimized",
  "query": "what are the three highest mountains in the world"
}
{% endhighlight %}
```

The cost of evaluating such a query is primarily linear with the number of matched documents.
The *AND* operator is most effective, but often ends up being too restrictive by not returning enough matches.
The *OR* operator is less restrictive, but has the problem of returning too many matches, which is very costly.
The *weakAnd* operator is somewhere in between the two in cost.

### Posting Lists

To find matching documents, the query operator uses the *posting lists* associated with each query term.
A posting list is part of the inverted index and contains all occurrences of a term within a collection of documents.
It consists of document IDs for documents that contain the term,
and additional information such as the positions of the term within those documents (used for ranking purposes).
For common terms (e.g., stopwords), the posting lists are very large and can be expensive to use during evaluation and ranking.
CPU work is required to iterate them, and I/O work is required to load portions of them from disk to memory with MMAP.
The last part is especially problematic when all posting lists of a disk index cannot fit into physical memory,
and the system must constantly swap parts of them in and out of memory, leading to high I/O wait times.

To improve query performance, the following tuning parameters are available,
as seen used in the *optimized* rank profile.
These are used to make tradeoffs between performance and quality.
* **Use more compact posting lists for common terms**:
  Setting [filter-threshold](../reference/schema-reference.html#filter-threshold) to 0.05
  ensures that all terms that are estimated to occur in more than 5% of the documents are
  handled with [compact posting lists (bitvectors)](../proton.html#index) instead of the full posting lists.
  This makes matching faster at the cost of producing less information for BM25 ranking (only a boolean signal is available).
* **Avoid using large posting lists all together**:
  Setting [stopword-limit](../reference/schema-reference.html#weakand-stopword-limit) to 0.6,
  ensures that all terms that are estimated to occur in more than 60% of the documents are considered stopwords
  and dropped entirely from the query and also from ranking.
* **Reduce the number of hits produced by *weakAnd***:
  Setting [adjust-target](../reference/schema-reference.html#weakand-adjust-target)
  ensures that documents that only match terms that occur very frequently in the documents are not considered hits.
  This also removes the need to calculate *first-phase* ranking for these documents,
  which is beneficial if *first-phase* ranking is more complex and expensive.

### Performance

The tuning parameters used in the *optimized* rank profile have been shown to provide a good tradeoff between performance and quality in testing.
A Wikipedia dataset with [SQuAD](https://nlp.stanford.edu/pubs/rajpurkar2016squad.pdf)
(Stanford Question Answering Dataset) queries was used to analyze performance,
and [trec-covid](https://ir.nist.gov/trec-covid/),
[MS MARCO](https://microsoft.github.io/msmarco/) and
[nfcorpus](https://huggingface.co/datasets/BeIR/nfcorpus) from the BEIR dataset to analyze quality implications.

For instance, the query performance was tripled without any measurable drop in quality with the Wikipedia dataset,
using the tuning parameters in the *optimized* rank profile.
See the blog post [Tripling the query performance of lexical search](https://blog.vespa.ai/tripling-the-query-performance-of-lexical-search/)
for more details.
Note that testing should be conducted on your particular dataset to find the right tradeoff between performance and quality.

## Hybrid TAAT and DAAT query evaluation

Vespa supports **hybrid** query evaluation over inverted indexes,
combining *TAAT* and *DAAT* evaluation to combine the best of both query evaluation techniques.
Hybrid is not enabled per default and is triggered by a run-time query parameter.
* **TAAT:** *Term At A Time* scores documents one query term at a time.
  The entire posting iterator can be read per query term, and the score of a document is accumulated.
  It is CPU cache friendly as posting data is read sequentially without randomly seeking the posting list iterator.
  The downside is that *TAAT* limits the term-based ranking function to be a linear sum of term scores.
  This downside is one reason why most search engines use *DAAT*.
* **DAAT:** *Document At A Time* scores documents completely one at a time.
  This requires multiple seeks in the term posting lists,
  which is CPU cache unfriendly but allows non-linear ranking functions.

Generally, Vespa does *DAAT* (document-at-a-time) query evaluation
and not *TAAT* (term-at-a time) for the reason listed above.

Ranking (score calculation) and matching (does the document match the query logic)
is not fully two separate disjunct phases,
where one first finds matches and calculates the ranking score in a later phase.
Matching and *first-phase* score calculation is interleaved when using *DAAT*.

The *first-phase* ranking score is assigned to the hit when it satisfies the query constraints.
At that point, the term iterators are positioned at the document id
and one can unpack additional data from the term posting lists -
e.g., for term proximity scoring used by the [nativeRank](../nativerank.html) ranking feature,
which also requires unpacking of positions of the term within the document.

The way hybrid query evaluation is done is that *TAAT* is used for sub-branches
of the overall query tree, which is not used for term-based ranking.

Using *TAAT* can speed up query matching significantly (up to 30-50%)
in cases where the query tree is large and complex,
and where only parts of the query tree are used for term-based ranking.
Examples of query tree branches that would require *DAAT*
is using text ranking features like [bm25 or nativeRank](../reference/rank-features.html).
The list of ranking features which can handle *TAAT* is long,
but using [attribute or tensor](../tensor-user-guide.html) features only
can have the entire tree evaluated using *TAAT*.

For example, for a query where there is a user text query from an end user,
one can use *userQuery()* YQL syntax and combine it with application-level constraints.
The application level filter constraints in the query could benefit from using *TAAT*.
Given the following document schema:

```
search news {
    document news {
        field title type string {}
        field body type string{}
        field popularity type float {}
        field market type string {
            rank:filter
            indexing: attribute
            attribute: fast-search
        }
        field language type string {
            rank:filter
            indexing: attribute
            attribute: fast-search
        }
    }
    fieldset default {
        fields: title,body
    }
    rank-profile text-and-popularity {
        first-phase {
            expression: attribute(popularity) + log10(bm25(title)) + log10(bm25(body))
        }
    }
}
```

In this case, the rank profile only uses two ranking features,
the popularity attribute and the [bm25](../reference/bm25.html) score of the userQuery().
These are used in the default fieldset containing the title and body.
Notice how neither *market* nor *language* is used in the ranking expression.

In this query example, there is a language constraint and a market constraint,
where both language and market are queried with a long list of valid values using OR,
meaning that the document should match any of the market constraints and any of the language constraints:

```
{% highlight json %}
{
    "hits": 10,
    "ranking.profile": "text-and-popularity",
    "yql": "select * from sources * where userQuery() and
      (language contains \"en\" or language contains \"br\") and
      (market contains \"us\" or market contains \"eu\" or market contains \"apac\" or market contains \"..\" )",
    "query": "cat video",
    "ranking.matching.termwiselimit": 0.1
}
{% endhighlight %}
```

The language and the market constraints in the query tree are not used in the
ranking score, and that part of the query tree could be evaluated using *TAAT*.
See also [multi lookup set filter](#multi-lookup-set-filtering)
for how to most efficiently search with large set filters.
The subtree result is then passed as a bit vector into the *DAAT* query evaluation,
which could significantly speed up the overall evaluation.

Enabling hybrid *TAAT* is done by passing
`ranking.matching.termwiselimit=0.1` as a request parameter. It's possible to
evaluate the performance impact by changing this limit. Setting the limit to 0 will force
termwise evaluation, which might hurt performance.

One can evaluate if using the hybrid evaluation improves search performance by adding the above parameter.
The limit is compared to the hit fraction estimate of the entire query tree.
If the hit fraction estimate is higher than the limit,
the termwise evaluation is used to evaluate the sub-branch of the query.

## Indexing uuids

When configuring [string](../reference/schema-reference.html#string)
type fields with `index`,
the default [match](../reference/schema-reference.html#match) mode is `text`.
This means Vespa will [tokenize](../linguistics.html#tokenization) the content and index the tokens.

The string representation of an [Universally unique identifier](https://en.wikipedia.org/wiki/Universally_unique_identifier) (UUID) is 32 hexadecimal (base 16) digits,
in five groups, separated by hyphens, in the form 8-4-4-4-12,
for a total of 36 characters (32 alphanumeric characters and four hyphens).

Example: Indexing `123e4567-e89b-12d3-a456-426655440000` with the above document definition,
Vespa will tokenize this into 5 tokens: `[123e4567,e89b,12d3,a456,426655440000]`,
each of which could be matched independently, leading to possible incorrect matches.

To avoid this, change the mode to [match: word](../reference/schema-reference.html#word) to
treat the entire uuid as *one* token/word:

```
field uuid type string {
    indexing: summary | index
    match:    word
    rank:     filter
}
```

In addition, configure the `uuid` as a
[rank: filter](../reference/schema-reference.html#rank) field -
the field will then be represented as efficiently as possible during search and ranking.
The `rank:filter` behavior can also be triggered at query time on a per-query item basis
by the `com.yahoo.prelude.query.Item.setRanked()`
in a [custom searcher](../searcher-development.html).

## Parent child and search performance

When searching imported attribute fields (with `fast-search`) from parent document types,
there is an additional indirection that can be reduced significantly
if the imported field is defined with `rank:filter`
and [visibility-delay](../reference/services-content.html#visibility-delay) is configured to > 0.
The [rank:filter](../reference/schema-reference.html#rank) setting impacts posting list granularity
and `visibility-delay` enables a cache for the indirection between the child and parent document.

## Ranking and ML Model inferences

Vespa [scales](sizing-search.html) with the number of hits the query retrieves per node/search thread,
and which needs to be evaluated by the first-phase ranking function.
Read more on [phased ranking](../phased-ranking.html).
Phased ranking enables using more resources during the second phase ranking step than in the first phase.
The first phase should focus on getting decent recall (retrieving relevant documents in the top k),
while the second phase should tune precision.

For [text search](../nativerank.html) applications,
consider using the [WAND](../using-wand-with-vespa.html) query operator -
WAND can efficiently (sublinear) find the top-k documents using an inner scoring function.

## Multi Lookup - Set filtering

Several real-world search use cases are built around limiting or filtering based on a set filter.
If the contents of a field in the document match any of the values in the query set, it should be retrieved.
E.g., searching data for a set of users:

```
select * from sources * where user_id = 1 or user_id = 2 or user_id = 3 or user_id = 3 or user_id = 4 or user_id 5 ...
```

For OR filters over the same field, it is strongly recommended to use the
[in query operator](../reference/query-language-reference.html#in) instead.
It has considerably better performance than plain OR for set filtering:

```
select * from sources * where user_id in (1, 2, 3, 4, 5)
```

{% include note.html content='
Large sets can slow down YQL-parsing of the query -
see [parameter substitution](../reference/query-language-reference.html#parameter-substitution)
for how to send the set in a compact, performance-effective way.'%}

Attribute fields used like the above without other stronger query terms,
should have `fast-search` and `rank: filter`.
If there is a large number of unique values in the field,
it is also faster to use `hash` dictionary instead of `btree`,
which is the default data structure for dictionaries for attribute fields with `fast-search`:

```
field user_id type long {
    indexing:   summary | attribute
    attribute:  fast-search
    dictionary: hash
    rank:       filter
}
```

For `string` fields, we also need to include [match](/en/reference/schema-reference.html#match)
settings if using the `hash` dictionary:

```
field user_id_str type string {
    indexing:   summary | attribute
    attribute:  fast-search
    match:      cased
    rank:       filter
    dictionary {
        hash
        cased
    }
}
```

If having 10M unique user_ids in the dictionary and searching for 1000 users per query,
the *btree* dictionary would be 1000 lookup times log(10M),
while *hash* based would be 1000 lookups times O(1). Still, the *btree* dictionary
offers more flexibility in terms of [match](/en/reference/schema-reference.html#match) settings.

The `in` query set filtering approach can be used in combination with hybrid *TAAT*
evaluation to further improve performance. See the [hybrid TAAT/DAAT](#hybrid-taat-daat) section.

Also see the [dictionary schema reference](../reference/schema-reference.html#dictionary).

{% include note.html content='
For most use cases, the time spent on dictionary traversal is negligible compared to the time spent on
query evaluation (matching and ranking). If the query is very selective, for example, using
vespa as a key-value lookup store with ranking support, the dictionary traversal time can be significant.'%}

## Document summaries - hits

If queries request many (thousands) of hits from a content cluster with few content nodes,
increasing the [summary cache](caches-in-vespa.html) might reduce latency and cost.

Using [explicit document summaries](../document-summaries.html),
Vespa can support memory-only summary fetching if all fields referenced in the document summary are
**all** defined with `attribute`. Dedicated in-memory summaries avoid (potential)
disk read and summary chunk decompression.
Vespa document summaries are stored using compressed
[chunks](../reference/services-content.html#summary-store-logstore-chunk).
See also the [practical
search performance guide on hits fetching](practical-search-performance-guide.html#hits-and-summaries).

## Boolean, numeric, text attribute

When using the attribute field type, considering performance, this is a rule of thumb:

1. Use boolean if a field is a boolean (max two values)
2. Use a string attribute if there is a set of values - only unique strings are stored
3. Use a numeric attribute for range searches
4. Use a numeric attribute if the data really is numeric; don't replace numeric with string numeric

Refer to [attributes](../attributes.html) for details.

## Tensor ranking

The ranking workload can be significant for large tensors -
it is important to understand both the potential memory and computational cost for each query.

### Memory

Assume the dot product of two tensors with 1000 values of 8 bytes each, as in
`tensor<double>(x[1000])`.
With one query tensor and one document tensor,
the dot product is `sum(query(tensor1) * attribute(tensor2))`.
Given a Haswell CPU architecture, where the theoretical upper memory bandwidth is 68 GB/sec,
this gives 68 GB/sec / 8 KB = 9M ranking evaluations/sec.
In other words, for a 1 M index, 9 queries per second before being memory bound.

See below for using smaller [cell value types](#cell-value-types), and read more about
[quantization](https://blog.vespa.ai/from-research-to-production-scaling-a-state-of-the-art-machine-learning-system/#model-quantization).

### Compute

When using tensor types with at least one mapped dimension (sparse or mixed tensor),
[attribute: fast-rank](../reference/schema-reference.html#attribute)
can be used to optimize the tensor attribute for ranking expression evaluation at the cost of using more memory.
This is a good tradeoff if benchmarking indicates significant latency improvements with `fast-rank`.

When optimizing ranking functions with tensors, try to avoid temporary objects.
Use the [Tensor Playground](https://docs.vespa.ai/playground/) to evaluate what the expressions map to,
using the execution details

to list the detailed steps - find examples below.

### Multiphase ranking

To save both memory and compute resources, use [multiphase ranking](../phased-ranking.html).
In short, use less expensive ranking evaluations to find the most promising candidates,
then a high-precision evaluation for the top-k candidates.

The blog post series on [Building Billion-Scale Vector Search](https://blog.vespa.ai/building-billion-scale-vector-search/) is a good read.

### Cell value types

| Type | Description |
| --- | --- |
| double | The default tensor cell type is the 64-bit floating-point `double` format. It gives the best precision at the cost of high memory usage and somewhat slower calculations. Using a smaller value type increases performance, trading off precision, so consider changing to one of the cell types below before scaling the application. |
| float | The 32-bit floating-point format `float` should usually be used for all tensors when scaling for production. Note that some frameworks like TensorFlow prefer 32-bit floats. A vector with 1000 dimensions, `tensor<float>(x[1000])` uses approximately 4K memory per tensor value. |
| bfloat16 | This type has the range as a normal 32-bit float but only 8 bits of precision and can be thought of as a "float with lossy compression" - see [Wikipedia](https://en.wikipedia.org/wiki/Bfloat16_floating-point_format). If memory (or memory bandwidth) is a concern, change the most space-consuming tensors to use the `bfloat16` cell type. Some careful analysis of the data is required before using this type.  When doing calculations, `bfloat16` will act as if it was a 32-bit float, but the smaller size comes with a potential computational overhead. In most cases, the `bfloat16` needs conversion to a 32-bit float before the actual calculation can occur, adding an extra conversion step.  In some cases, having tensors with `bfloat16` cells might bypass some built-in optimizations (like matrix multiplication) that will be hardware-accelerated only if the cells are of the same type. To avoid this, use the [cell_cast](../reference/ranking-expressions.html#cell_cast) tensor operation to make sure the cells are of the right type before doing the more expensive operations. |
| int8 | If using machine learning to generate a model with data quantization, one can target the `int8` cell value type, which is a signed integer with a range from -128 to +127 only. This is also treated like a "float with limited range and lossy compression" by the Vespa tensor framework, and gives results as if it were a 32-bit float when any calculation is done. This type is also suitable when representing boolean values (0 or 1). {% include note.html content='If the input for an `int8` cell is not directly representable, the resulting cell value is undefined, so take care to only input numbers in the `[-128,127]` range.' %} It's also possible to use `int8` representing binary data for [hamming distance](../reference/schema-reference.html#distance-metric) Nearest-Neighbor search. Refer to [billion-scale-knn](https://blog.vespa.ai/billion-scale-knn/) for example use. |

### Inner/outer products

The following is a primer into inner/outer products and execution details:

| tensor a | tensor b | product | sum | comment |
| --- | --- | --- | --- | --- |
| tensor(x[3]):[1.0, 2.0, 3.0] | tensor(x[3]):[4.0, 5.0, 6.0] | tensor(x[3]):[4.0, 10.0, 18.0] | 32 | [Playground example](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEMSybIiFIAXA2gZywAnABQAPRAGYAugEo4iAIzEwAJmXTIrCAF9W20hmrlcDIgbaU0WugwBGLGpg5Qe-IWMmz5AFmUBWZQA2KU1HXQx9ViNME04zawp8aPJ6TlhzR3YGRgAqe2tw1EjDBNjCBwsk6whIVKhoAFdaAGMKzOdIPgaAW2Fc2xlQmkKdFCkQbSA). The dimension name and size are the same in both tensors - this is an inner product with a scalar result. |
| tensor(x[3]):[1.0, 2.0, 3.0] | tensor(y[3]):[4.0, 5.0, 6.0] | tensor(x[3],y[3]):[ [4.0, 5.0, 6.0], [8.0, 10.0, 12.0], [12.0, 15.0, 18.0] ] | 90 | [Playground example](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEMSybIiFIAXA2gZywAnABQAPRAGYAugEo4iAIzEwAJmXTIrCAF9W20hmrlcDIgbaU0WugwBGLGpg5Qe-IWMmz5AFmUBWZQA2KU1HXQx9ViNME04zawp8aPJ6TlhzR3YGRgAqe2tw1EjDBNjCBwsk6whIVKhoAFdaAGMKzOdIPgaAW2Fc2xlQmkKdFCkQbSA). The dimension size is the same in both tensors, but dimensions have different names -> this is an outer product; the result is a two-dimensional tensor. |
| tensor(x[3]):[1.0, 2.0, 3.0] | tensor(x[2]):[4.0, 5.0] | undefined |  | [Playground example](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEMSybIiFIAXA2gZywAnABQAPRAGYAugEo4iAIzEwAJmXTIrCAF9W20hmrlcDIgbaU0WugwBGLGpg5Qe-IWMQrZ8gCzKArFKajroY+qxGmCacZtYU+JHk9Jyw5o7sDIwAVPbWoajhhnHRhA4WCdYQkMlQ0ACutADGZenOkHx1ALbC2bYywTT5OihSINpAA). Two tensors in the same dimension but with different lengths -> undefined. |
| tensor(x[3]):[1.0, 2.0, 3.0] | tensor(y[2]):[4.0, 5.0] | tensor(x[3],y[2]):[ [4.0, 5.0], [8.0, 10.0], [12.0, 15.0] ] | 54 | [Playground example](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEMSybIiFIAXA2gZywAnABQAPRAGYAugEo4iAIzEwAJmXTIrCAF9W20hmrlcDIgbaU0WugwBGLGpg5Qe-IcICeiFbPkAWZQBWKU1HXQx9ViNME04zawp8aPJ6TlhzR3YGRgAqe2tw1EjDBNjCBwsk6whIVKhoAFdaAGMKzOdIPgaAW2Fc2xlQmkKdFCkQbSA). Two tensors with different names and dimensions -> this is an outer product; the result is a two-dimensional tensor. |

Inner product - observe optimized into `DenseDotProductFunction`
with no temporary objects:

```
{% highlight json %}
[ {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::DenseDotProductFunction",
    "symbol": "vespalib::eval::(anonymous namespace)::my_cblas_double_dot_product_op(vespalib::eval::InterpretedFunction::State&, unsigned long)"
  } ]
{% endhighlight %}
```

Outer product, parsed into a tensor multiplication (`DenseSimpleExpandFunction`),
followed by a `Reduce` operation:

```
{% highlight json %}
[ {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::DenseSimpleExpandFunction",
    "symbol": "void vespalib::eval::(anonymous namespace)::my_simple_expand_op, true>(vespalib::eval::InterpretedFunction::State&, unsigned long)"
  },
  {
    "class": "vespalib::eval::tensor_function::Reduce",
    "symbol": "void vespalib::eval::instruction::(anonymous namespace)::my_full_reduce_op >(vespalib::eval::InterpretedFunction::State&, unsigned long)"
  } ]
{% endhighlight %}
```

Note that an inner product can also be run on mapped tensors
([Playground example](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEMSybIiFIAXA2gZywAnABQAPYAF8AlHGCiAjHHnEwogExw1K0QGY4OiZFYQJrCaQzVyuBkQttKaY3QYAjFjUwcoPfkLGSMnKKACwAdAAM2hoArJHaegBskYbOphjmrFaYNpx2zhT42eT0nACWtLQEgjiCWAAmAK4AxlwenoQMjABU7mlmKAC6IBJAA)):

```
{% highlight json %}
[ {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::SparseFullOverlapJoinFunction",
    "symbol": "void vespalib::eval::(anonymous namespace)::my_sparse_full_overlap_join_op, true>(vespalib::eval::InterpretedFunction::State&, unsigned long)"
  } ]
{% endhighlight %}
```

### Mapped lookups

`sum(model_id * models, m_id)`

| tensor name | tensor type |
| --- | --- |
| model_id | `tensor(m_id{})` |
| models | `tensor(m_id{}, x[3])` |

Using a mapped dimension to select an indexed tensor can be considered a
[mapped lookup](../tensor-examples.html#using-a-tensor-as-a-lookup-structure).
This is similar to creating a slice but optimized into a single `MappedLookup` -
see [Tensor Playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gFssATAgGwH0BLFksmpCIJIAFwK0AzlgBOACkY8WwAL4BKOMEYAmOAEYAdAAYVkARBUCVpDNXK4GRG4MppzdBszbtJ-GpmEocSlZBSVVYgAPRABmAF0NLT04RAAWY2IwAFYMsAA2YzjMnRSAdlyADlyATkLTd0sMawE7TAcRJ3cKfFbyehFJAFdGBVYOJTAAKjAvDklipTU-f0IGIZHZrl4pmbGfBd4lhqtnCF6odtXTzFdziEh+qEl2bgBjTpXVkVHvSUnNxZaJRwHT1fyNVDNWxdS5CZbkW7ue6PJgAQxwOAILE47CwWAA1oMcJwZFjBu94YJApBSSxyQQfnN-nslMR1sRFIczOCrCg4iAVEA) example.

```
{% highlight json %}
[ {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::MappedLookup",
    "symbol": "void vespalib::eval::(anonymous namespace)::my_mapped_lookup_op(vespalib::eval::InterpretedFunction::State&, unsigned long)"
  } ]
{% endhighlight %}
```

### Three-way dot product - mapped

`sum(query(model_id) * model_weights * model_features)`

| tensor name | tensor type |
| --- | --- |
| query(model_id) | `tensor(model{})` |
| model_weights | `tensor(model{}, feature{})` |
| model_features | `tensor(feature{})` |

Three-way mapped (sparse) dot product:
[Tensor Playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKAWywBMCAGwD6AS34BKEmRqQiCSABcCtAM5Y2AHmhCsAQyUA+XgOHAAvpLjAeABjgBGC5FkQLsi6QzVyuBkTecpRobnQMfIKiAO4EYgDmABZKajI0mApQKuqaOnqGJpHmXmDQBIbMbASW1sBgADq0tmZCcPbEpeVKlQRw0HYWTsSNzVFtdh1lFVV9znAATMNNRa08jpNdPX0DcADMS6PCbeud073QcwAsYC5hHhhesr6Y-oqBYRT4z+T0iisiU26VVSQXS8gY2Q02l0BmMXEBPRqNn6cAArJNHHAAGy3dL3VCPHwfV6ENLBL5hCCQX5QFjsbj-CSSMAAKjA-1iCWSalZ7JaAM2wLJYMyTFYnFMUXEUl5HLiSRSsv5CKFd08oNCYJJ4I1VJC33CijUzB4XDpEsZMrZcq5iutysFBDU0l1GQYxtN5oZ-KZSqlnIVPPtUpVTukaoeKAAuiALEA)

```
{% highlight json %}
[ {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::Sparse112DotProduct",
    "symbol": "void vespalib::eval::(anonymous namespace)::my_sparse_112_dot_product_op(vespalib::eval::InterpretedFunction::State&, unsigned long)"
  } ]
{% endhighlight %}
```

### Three-way dot product - mixed

`sum(query(model_id) * model_weights * model_features)`

| tensor name | tensor type |
| --- | --- |
| query(model_id) | `tensor(model{})` |
| model_weights | `tensor(model{}, feature[2])` |
| model_features | `tensor(feature[2])` |

Three-way mapped (mixed) dot product:
[Tensor Playground](https://docs.vespa.ai/playground/#N4KABGBEBmkFxgNrgmUrWQPYAd5QFNIAaFDSPBdDTAO30gEcBXAgJwE8AKAWywBMCAGwD6AS34BKEmRqQiCSABcCtAM5Y2AHmhCsAQyUA+XgOHAAvpLjAeABjgBGC5FkQLsi6QzVyuBkTecpRobnQMfIKiAO4EYgDmABZKajI0mApQKuqaOnqGJpHmXmDQBIbMbASIAEwAutbAYAA6tLZmQnD2xKXlSpUEcHYWTsSt7VFddj1lFVVOIzVjbUWdPI4zfQNDIwDMyxPCXRu9c4POcAAsYC5hHhhesr6Y-oqBYRT4z+T0iqsis36VVSQXS8gY2Q02l0BmMXEBA1qDTgiAArMQAGx1Vzpe6oR4+D6vQhpYJfMIQSC-KAsdjcf4SSRgABUYH+sQSyTULLZHQBW2BpLBmSYrE4pii4ikPPZcSSKRlfIRgrunlBoTBxPB6spIW+4UUamYPC4tPFDOlrNlnIVVqVAoIamkOoyDCNJrN9L5jMVko58u5dslysd0lVDxQdRAFiAA)

```
{% highlight json %}
[ {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::tensor_function::Inject",
    "symbol": ""
  },
  {
    "class": "vespalib::eval::Mixed112DotProduct",
    "symbol": "void vespalib::eval::(anonymous namespace)::my_mixed_112_dot_product_op(vespalib::eval::InterpretedFunction::State&, unsigned long)"
  } ]
{% endhighlight %}
```
