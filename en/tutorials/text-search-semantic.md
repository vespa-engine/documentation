---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Semantic Text Search: Quick start "
redirect_from:
- /documentation/tutorials/text-search-semantic.html
---

The main goal of this tutorial is to add out-of-the-box semantic search capabilities to text applications
with as little application specific tuning as possible.
In order to do that, we will first describe the data used,
the metrics of interest and important baselines that will be used to judge our results. 

Once that is done, we will show how to use pre-trained text embeddings to match documents
based on the distance between query and document embeddings
by using the Vespa operator that implements nearest neighbor search.
It is shown that the pre-trained embeddings indeed carry significant information about query-document relevance. 

However, in an unexpected turn of events,
our analysis start to show that the [MS MARCO dataset](https://microsoft.github.io/msmarco/)
is more biased toward term-matching signals than we thought was the case at the beginning of our experiments.
We try our best to show the evidence we found to support this claim
and are open to discuss and get feedback from the research community.

We then show how an efficient Vespa implementation of the WAND algorithm called
[weakAND](../using-wand-with-vespa.html#weakand) is extremely effective
when dealing with datasets biased towards term-matching signals.
We conclude that,
although pre-trained semantic vectors indeed show promising results for out-of-the-box semantic search,
we ideally want to investigate their power and limitations on datasets
that are less biased towards term-matching signals.



## A note on the data

This tutorial uses a sample of the [MS MARCO dataset](https://microsoft.github.io/msmarco/).
The main reason was to allow others to follow the same steps in their local machines,
as the different embeddings used will increase the disk, memory and processing required for the application.

The entire dataset as well as the code to process it were described in the first part of our
[text search tutorial](text-search.html#dataset).
For the sample used here, we randomly selected 1.000 queries and 100.000 documents.
The relevant documents to the queries are guaranteed to be in the corpus used.



## A note on metrics

We will use three metrics on the experiments reported here. They are: 

1. Matched docs: The total number of documents matched by the query.
2. Recall @ 100: The number of relevant documents retrieved in the first 100 positions divided by the number of queries.
3. MRR @ 100: The [mean reciprocal rank metric](https://en.wikipedia.org/wiki/Mean_reciprocal_rank)
   computed by considering the first 100 documents returned by each query.

If we think about an end-to-end application we probably care the most about the `Matched docs` and `MRR @ 100`.
The smaller the `Matched docs` the faster and cheaper our application is.
The higher the `MRR @ 100` the better we are placing the relevant documents right at the top where we want them. 

However, assuming that we can deploy a multi-phased ranking system with cheaper 1st phase and more elaborate 2nd phase,
we will also focus here on the relationship between `Matched docs` and `Recall @ 100`
and assume that we could come up with a more accurate 2nd phase
that correlates well with the 1st phase being experimented.



## Baselines

Before we proceed to more elaborate experiments we need to establish some obvious baselines.
Here are the results obtained by using query terms to match documents
and [BM25](../reference/bm25.html) as 1st phase ranking:

<table class="table">
<thead>
<tr>
  <th>Match operator</th><th>1st ranking</th><th>Matched docs</th><th>Recall @100</th><th>MRR @100</th>
</tr>
</thead>
<tbody>
<tr>
  <td>AND</td><td>BM25</td><td>0.0012</td><td>0.4820</td><td>0.4001</td>
</tr>
<tr>
  <td>OR</td><td>BM25</td><td>0.8482</td><td>0.9580</td><td>0.6944</td>
</tr>
</tbody>
</table>

The match operator `AND` means that we are only matching documents that contain all the query terms
either in the title or in the body of the document.
A sample query looks like:

```json
{
    "yql": "select * from sources * where (userInput(@userQuery))",
    "userQuery": "what types of plate boundaries cause deep sea trenches",
    "ranking": {
        "profile": "bm25",
        "listFeatures": true
    }
}
```

The match operator `OR` means that we are matching documents that contain any of the query terms
either in the title or in the body.
The only difference is the inclusion of the `{grammar: "any"}` in the
[YQL](../reference/query-language-reference.html#grammar) expression:

```json
{
    "yql": "select * from sources * where ({grammar: \"any\"}userInput(@userQuery))"
}
```

The baselines are two obvious choices that also represent two extremes that are interesting to analyze.
The `AND` operator is too restrictive, matching few documents.
The consequence is that it ends up missing the relevant documents in the first 100 positions
for approximately half of the queries.
The `OR` operator on the other hand, matches the majority of the documents in the corpus
and recalls the relevant document for most of the queries.



## Pre-trained vector embeddings

While performing the experiments reported here, we evaluated different types of pre-trained vectors,
all publicly available. They were:
1. Word2Vec (available via [TensorFlow Hub](https://tfhub.dev/google/Wiki-words-500-with-normalization/2))
2. Universal sentence encoder (available via [TensorFlow Hub](https://tfhub.dev/google/universal-sentence-encoder/4))
3. Sentence BERT (available via the python [sentence-transformers library](https://github.com/UKPLab/sentence-transformers))

The approach used was to create one vector for the title and one vector for the body for each document
and to create one query vector for each query.
It might not make sense to use large texts such as the body of the documents
to create embedding vectors based on sentence models.
However, testing how far we can go without tailoring the application too much is part of our experiment goals.
In order words, the goal is to find out how well we can create out of the box text applications
by adding semantic search capabilities for arbitrary chunks of text,
with as little pre-processing as possible.



## From text to embeddings methodology

We follow the examples available in the model's repositories and libraries to create the query and document vectors.
We do not claim that this is the best way to construct them,
but we believe that this is what most people replicating this would do based on the information available to them.
Improving on text to embedding construction could be a nice topic to explore elsewhere.

For example, this is how it is presented at
[the Universal Sentence Encoder page](https://tfhub.dev/google/universal-sentence-encoder/4) in TensorFlow Hub:

```python
From tensorflow hub

import tensorflow as tf

embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
embeddings = embed([
    "The quick brown fox jumps over the lazy dog.",
    "I am a sentence for which I would like to get its embedding"])

print embeddings
```

The following comes from the
[sentence-transformers library](https://github.com/UKPLab/sentence-transformers#getting-started):

```python
From sentence-transformers library

from sentence_transformers import SentenceTransformer
model = SentenceTransformer("bert-base-nli-mean-tokens")

sentences = ["This framework generates embeddings for each input sentence",
    "Sentences are passed as a list of string.", 
    "The quick brown fox jumps over the lazy dog."]
sentence_embeddings = model.encode(sentences)
```

We have followed a similar pattern when creating the embeddings used here.



## Approximate Nearest Neighbor (ANN) operator

Vespa can match documents based on distance metrics between query and document vectors.
This feature makes it possible to implement strategies like semantic search at scale
due to techniques such as Approximate Nearest Neighbor (ANN).
Discussing ANN theory and implementation is beyond the scope of this tutorial.
Instead, we want to show how it can be used for semantic search.

There are only two steps required to perform ANN with embeddings in Vespa:
* Define the document embedding fields in the schema.
* Define the query embedding field in a query profile type.

Once that is done, we can feed document embeddings to Vespa,
use the ANN operator to match documents based on the distance between document
and query embeddings and use the embeddings in ranking functions.



### Schema

The document embeddings can be defined by adding the following fields in
`src/main/application/schemas/msmarco.sd`:

```
field title_bert type tensor<float>(x[768]) {
    indexing: attribute
}

field body_bert type tensor<float>(x[768]) {
    indexing: attribute
}
```

The code above defines one field for the title embedding and one for the text body embedding.
Both are tensors of type float with indexed dimension of size 768, similar to the query embedding.
The `indexing: attribute` indicates that the tensor fields above will be
[kept in memory](../schemas.html#indexing) to be used by the matching and the ranking framework.

At this point, it is already possible to match documents
based on the distance between the query and document tensors via the `nearestNeighbor` operator
that will be discussed in the next section.
However, it could be interesting to use those tensors to rank the documents as well.
This can be accomplished by defining a [rank-profile](../ranking.html):

```
rank-profile bert_title_body_all inherits default {
    inputs {
        query(tensor_bert) tensor&lt;float&gt;(x[768])
    }    
    function dot_product_title() {
        expression: sum(query(tensor_bert)*attribute(title_bert))
    }
    function dot_product_body() {
        expression: sum(query(tensor_bert)*attribute(body_bert))
    }
    first-phase {
        expression: dot_product_title() + dot_product_body()
    }
}
```

The [rank-profile](../reference/schema-reference.html#rank-profile) `bert_title_body_all` will sort all the
matched documents according to the sum of the dot-products between query and title and query and body vectors.
Different rank-profiles can be defined for experimentation.


### Query

We can send the query embeddings via the `input.query(tensor_bert)` parameter:

```json
{
  "yql": "...",
  "input.query(tensor_bert)": "[0.013267785266013195, -0.021684982513878254, ..., -0.007751454443551412]"
}
```



### ANN operator

Once that query and document tensors as well as rank-profiles that use them are all defined,
it is possible to use the embeddings to match and to rank the documents by using the `nearestNeighbor` operator
together with the appropriate rank-profile:

```json
{
    "yql": "select * from sources * where ({targetHits: 1000, label: \"nns\"}nearestNeighbor(title_bert, tensor_bert))",
    "userQuery": "what types of plate boundaries cause deep sea trenches",
    "ranking": {
        "profile": "bert_title_body_all",
        "listFeatures": true
    },
    "input.query(tensor_bert)": "[0.05121087115032622, -0.0035218095295999675, ..., 0.05303904445092506]"
}
```

The query above uses the `nearestNeighbor` operator to match documents based on the euclidean distance
between the title embedding (`title_bert`) and the query embedding (`tensor_bert`).
It is possible to annotate the `nearestNeighbor` with properties such as `targetHits`
that defines the target number of documents to be matched.
In addition, we specify that the matched documents will be ranked by the `bert_title_body_all` rank-profile. 


## ANN results

The table below shows results obtained by matching the closest 1.000 document vectors
to the query vector in terms of the Euclidean distance.
Even though Vespa supports approximate nearest neighbor search,
we set the method to be brute force to remove the approximation error from the analysis in this tutorial.
This means that the documents matched were indeed the closest ones to the query.
The `ANN(title, bert)` in the table below means that we matched documents
by comparing the document title embedding to the query embedding
where the embeddings were created by the sentence BERT model. 

All the results involving embeddings in this tutorial are generated via the sentence BERT model.
The results obtained with the Universal Sentence Encoder model were similar and therefore omitted.
On the other hand, the results obtained with the Word2Vec model were way worse than expected
and were left out of this tutorial
since they might require more pre-processing than the sentence models to give sensible results.

<table class="table">
<thead>
<tr>
  <th>Match operator</th><th>1st ranking</th><th>Matched docs</th><th>Recall @100</th><th>MRR @100</th>
</tr>
</thead>
<tbody>
<tr>
  <td>ANN(title, bert)</td><td>dotProd(title, query, bert) + dotProd(body, query, bert)</td><td>0.0625</td><td>0.7460</td><td>0.4622</td>
</tr>
<tr>
  <td>ANN(body, bert)</td><td>dotProd(title, query, bert) + dotProd(body, query, bert)</td><td>0.0563</td><td>0.7180</td><td>0.4471</td>
</tr>
</tbody>
</table>

In addition to matching documents based on the distance between document and query vectors,
we also ranked the matched documents using the semantic vectors
by having the 1st phase ranking function be the dot-product between query and title
plus the dot-product between the query and body.
All embedding vectors are normalized to have length (L2-norm) equal to 1.

The results obtained are promising with respect to the relationship between matched documents and recall.
We retrieved only around 6% of the documents which is more than the `AND` operator
but much less than the `OR` operator while we increased the recall from 48% (obtained with `AND`) to 75%,
which is great, although we still have a good way to go to reach 96% (obtained with the `OR`).

Since it is often mentioned that semantic search works better when combined with term-matching,
it would be wise for us to check the metrics obtained when combining both.
But first, let's see some useful features related to term-matching that are available in Vespa.



## weakAND operator and its effectiveness

The [weakAnd](../using-wand-with-vespa.html) implementation scores documents by a simplified scoring function,
which uses two core text rank features [term(n).significance](../reference/rank-features.html#term(n).significance)
and [term(n).weight](../reference/rank-features.html#term(n).weight).

Below is a query example that uses the `weakAND` operator
with an annotation that sets the target number of documents to be 1.000:

```json
{
    "yql": "select * from sources * where ({targetHits: 1000}weakAnd(default contains \"what\", default contains \"types\", default contains \"of\", default contains \"plate\", default contains \"boundaries\", default contains \"cause\", default contains \"deep\", default contains \"sea\", default contains \"trenches\"))",
    "userQuery": "what types of plate boundaries cause deep sea trenches",
    "ranking": {
        "profile": "bm25",
        "listFeatures": true
    }
}
```

Remember that the `default` is the fieldset that includes both the `title` and the `body` fields. 

```
fieldset default {
    fields: title, body
}
```

It was surprising to see the effectiveness of the WAND operator in this case:

<table class="table">
<thead>
<tr>
  <th>Match operator</th><th>1st ranking</th><th>Matched docs</th><th>Recall @100</th><th>MRR @100</th>
</tr>
</thead>
<tbody>
<tr>
  <td>weakAND</td><td>BM25</td><td>0.1282</td><td>0.9460</td><td>0.6946</td>
</tr>
</tbody>
</table>

It matched much fewer documents than the `OR` operator (12.5% versus 85% respectively)
while keeping a similar recall metric (92% versus 96% respectively). 

If you are detail oriented, you might be wondering why the `weakAND` operator matched 12.5% of the documents
if we set `targetHits` to be 1.000.
The reason for that is that the algorithm starts with an initial list of 1.000 candidates
and starts to add new ones that are better than the documents already in the list.
That way the 1.000 ends up being the lower bound of the documents matched.
The same is true for the `nearestNeighbor` operator.



## ANN and weakAND: Little improvement

The second surprise was to see how little the pre-trained sentence embeddings contributed
in addition to what was delivered by WAND.
The table below shows that we are indeed matching documents that wouldn't be matched by the `weakAND` operator alone
(16% matched documents by adding `ANN` vs. 12% by `weakAND` alone.).
However, we see almost no improvement for Recall and MRR:

<table class="table">
<thead>
<tr>
  <th>Match operator</th><th>1st ranking</th><th>Matched docs</th><th>Recall @100</th><th>MRR @100</th>
</tr>
</thead>
<tbody>
<tr>
  <td>weakAND</td><td>BM25</td><td>0.1282</td><td>0.9460</td><td>0.6946</td>
</tr>
<tr>
  <td>weakAND + ANN(title, bert)</td><td>BM25</td><td>0.1645</td><td>0.9460</td><td>0.6943</td>
</tr>
<tr>
  <td>weakAND + ANN(body, bert)</td><td>BM25</td><td>0.1594</td><td>0.9460</td><td>0.6943</td>
</tr>
<tr>
  <td>weakAND + ANN(title, bert) + ANN(body, bert)</td><td>BM25</td><td>0.1837</td><td>0.9460</td><td>0.6941</td>
</tr>
</tbody>
</table>

It could be argued that the articles retrieved by `ANN` does not necessarily contain
the query terms in the title nor the body of the document, leading to zero `BM25` scores.
To address that we can add the (unscaled) dot-product in the 1st phase ranking.
The results below show that we had a marginal reduction in Recall and a marginal increase in MRR:

<table class="table">
<thead>
<tr>
  <th>Match operator</th><th>1st ranking</th><th>Matched docs</th><th>Recall @100</th><th>MRR @100</th>
</tr>
</thead>
<tbody>
<tr>
  <td>weakAND + ANN(title, bert)</td><td>BM25 +<br/>dotProd(title, query, bert) +<br/>dotProd(body, query, bert)</td><td>0.1645</td><td>0.9440</td><td>0.6990</td>
</tr>
<tr>
  <td>weakAND + ANN(body, bert)</td><td>BM25 +<br/>dotProd(title, query, bert) +<br/>dotProd(body, query, bert)</td><td>0.1594</td><td>0.9440</td><td>0.6986</td>
</tr>
<tr>
  <td>weakAND + ANN(title, bert) + ANN(body, bert)</td><td>BM25 +<br/>dotProd(title, query, bert) +<br/>dotProd(body, query, bert)</td><td>0.1837</td><td>0.9440</td><td>0.6992</td>
</tr>
</tbody>
</table>

Another issue that must be addressed is that we should scale the BM25 scores and the embedding dot-products
so that we take into consideration that they might have completely different scales.
In order to do that,
we need to collect a training dataset that that takes into account the appropriate match phase
and fit a model (linear in our case) according to a listwise loss function,
as described in the [text search tutorial with ML](text-search-ml.html)
and summarized in this [blog post](https://medium.com/vespa/learning-to-rank-with-vespa-9928bbda98bf).

<table class="table">
<thead>
<tr>
  <th>Match operator</th><th>1st ranking</th><th>Matched docs</th><th>Recall @100</th><th>MRR @100</th>
</tr>
</thead>
<tbody>
<tr>
  <td>weakAND + ANN(title, bert) + ANN(body, bert)</td><td>0.90 * BM25(title) +<br/>2.20 * BM25(body) +<br/>0.13 * dotProd(title, query, bert) +<br/>0.58 * dotProd(body, query, bert)</td><td>0.1837</td><td>0.9420</td><td>0.7063</td>
</tr>
</tbody>
</table>

The table above shows that we obtained a slight improvement in MRR
and that the model increased the relative weight associated with the BM25 scores,
even though the magnitude of the BM25 scores are much bigger than the magnitude of the dot-product scores,
as we will see in the next section.
This again points towards the importance of term-match signals relative to the semantic search signals.



## MSMARCO: A biased dataset?

The results obtained so far led us to investigate why the `weakAND` operator was so effective
and why semantic vectors were not complementing it as we thought they would, in the context of the MSMARCO dataset.
We would of course expect a significant intersection between term-matching and semantic signals
since both should contain information about query document relevance.
However, the semantic signals need to complement the term-matching signals for it to be valuable,
given that they are more expensive to store and compute.
This means that they should match relevant documents that would not otherwise be matched by term-matching signals. 

The results discussed so far did not show any significant improvement by adding (pre-trained) semantic vectors
in addition to the term-matching signals.
The important question is why not?
One possibility is to say that the pre-trained semantic vectors are not informative enough in this context.
However, the graph below indicates otherwise.
The blue histogram shows the empirical distribution of embedding dot-product scores
for the general population of (query, document) pairs.
The red histogram shows the empirical distribution of embedding dot-product scores
for the population of (query, relevant_document) pairs.
So the dot-product scores are significantly higher for documents relevant to the query
than they are for random documents:

<div style="text-align:center">
<img src="/assets/img/tutorials/dotP_hist.png"
     style="width: 60%; margin-right: 1%; margin-bottom: 0.5em;"
     alt="Plot with dot-product scores - relevant to the query vs. random documents." />
</div>

This confirms the results we obtained when only using `nearestNeighbor` operator to match the documents
and the dot-product scores to rank them
and shows that pre-trained embedding indeed carries relevant information about query document relevance.
If that is the case, there is also the possibility that the dataset being used,
MS MARCO dataset in our case, is biased towards term-matching signals.
The next graph supports this hypothesis by showing that the empirical distribution of the relevant documents (red)
is significantly higher in bm25 score than the distribution of random documents:

<div style="text-align:center">
<img src="/assets/img/tutorials/bm25_hist.png"
     style="width: 60%; margin-right: 1%; margin-bottom: 0.5em;"
     alt="Plot with relevant and random documents" />
</div>

In other words, there are few documents that would not be matched by term-matching approaches.
This explains why the results obtained with the `weakAND` operator were outstanding.
MS MARCO dataset turns out to be a favorable environment for this kind of algorithm.
That also means that after accounting for term-matching
there are almost no relevant documents left to be matched by semantic signals.
This is true even if the semantic embeddings are informative. 

The best we can hope for in a biased dataset
is for the bm25 scores and the embedding dot-product scores to be positively correlated,
showing that both carry information about document relevance.
This seems indeed to be the case in the scatter plot below
that shows a much stronger correlation between bm25 scores and embedding scores for the relevant documents (red)
than between the scores of the general population (black):

<div style="text-align:center">
<img src="/assets/img/tutorials/bm25_dotP_scatter.png"
     style="width: 60%; margin-right: 1%; margin-bottom: 0.5em;"
     alt="Plot with stronger correlation between bm25 scores and embedding scores" />
</div>

To be clear, there is no claim being made that the results and conclusions described here
are valid across different NLP datasets and tasks.
However, this problem might be more common than we would like to admit given the nature of how the datasets are created.
For example, according to the MS MARCO dataset paper [^1], they built the dataset by:

1. Sampling queries from Bing’s search logs.
2. Filtering out non question queries.
3. Retrieve relevant documents for each question using Bing from its large-scale web index.
4. Automatically extract relevant passages from those documents
5. Human editors then annotate passages that contain useful and necessary information for answering the questions

Looking at steps 3 and 4 (and maybe 5), it is not surprising to find bias in the dataset.
To be fair, this bias is recognized as an issue in the literature,
but it was a bit surprising to see the degree of the bias
and how this might affect experiments involving semantic search.



## Fine-tuning sentence embeddings: advantages and disadvantages

At this point a reasonable observation would be that we are talking about pre-trained embeddings
and that we could get better results if we fine-tuned the embeddings to the specific application at hand.
This might well be the case,
but there are at least two important considerations to be taken into account, cost and overfitting.
The resource/cost consideration is important but more obvious to be recognized.
You either have the money to pursue it or not.
If you do, you still should check to see if the improvement you get is worth the cost. 

The main issue in this case relates to overfitting.
It is not easy to avoid overfitting when using big and complex models
such as Universal Sentence Encoder and sentence BERT.
Even if we use the entire MS MARCO dataset,
which is considered a big and important recent development to help advance the research around NLP tasks,
we only have around 3 million documents and 300 thousand labeled queries to work with.
This is not necessarily big relative to such massive models. 

Another important observation is that BERT-related architectures have dominated
[the MSMARCO leaderboards](https://microsoft.github.io/msmarco/) for quite some time.
Anna Rogers [wrote a good piece](https://hackingsemantics.xyz/2019/leaderboards/)
about some of the challenges involved on the current trend of using leaderboards
to measure model performance in NLP tasks.
The big takeaway is that we should be careful when interpreting those results
as it becomes hard to understand if the performance comes from architecture innovation
or excessive resources (read overfitting) being deployed to solve the task.

But despite all those remarks,  the most important point here is that
if we want to investigate the power and limitations of semantic vectors (pre-trained or not),
we should ideally prioritize datasets that are less biased towards term-matching signals. 

[^1]: Bajaj, Payal and Campos, Daniel and Craswell, Nick and Deng, Li and Gao, Jianfeng and Liu, Xiaodong and Majumder, Rangan and McNamara, Andrew and Mitra, Bhaskar and Nguyen, Tri and others, 2018. MS MARCO: A human generated machine reading comprehension dataset.

<script src="/js/process_pre.js"></script>
