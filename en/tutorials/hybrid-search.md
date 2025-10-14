---
title: Hybrid Text Search Tutorial
---

# Hybrid Text Search Tutorial

Hybrid search combines different retrieval methods to improve search quality. This tutorial distinguishes between two core components of search:

* **Retrieval**: Identifying a subset of potentially relevant documents from a large corpus. Traditional lexical methods like [BM25](../reference/bm25.html) excel at this, as do modern, embedding-based [vector search](../vector-search.html) approaches.
* **Ranking**: Ordering retrieved documents by relevance to refine the results. Vespa's flexible [ranking framework](../ranking.html) enables complex scoring mechanisms.

This tutorial demonstrates building a hybrid search application with Vespa that leverages the strengths of both lexical and embedding-based approaches. We'll use the [NFCorpus](https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/) dataset from the [BEIR](https://github.com/beir-cellar/beir) benchmark and explore various hybrid search techniques using Vespa's query language and ranking features.

The main goal is to set up a text search app that combines simple text scoring features such as [BM25](../reference/bm25.html) with vector search in combination with text-embedding models. We demonstrate how to obtain text embeddings within Vespa using Vespa's [embedder](../embedding.html#huggingface-embedder) functionality. In this guide, we use [snowflake-arctic-embed-xs](https://huggingface.co/Snowflake/snowflake-arctic-embed-xs) as the text embedding model. It is a small model that is fast to run and has a small memory footprint.

\{% include pre-req.html memory="4 GB" extra-reqs='

* Python3
* `curl`

' %\}

### Installing vespa-cli and ir\_datasets

This tutorial uses [Vespa-CLI](../vespa-cli.html) to deploy, feed, and query Vespa. We also use [ir-datasets](https://ir-datasets.com/) to obtain the NFCorpus relevance dataset.

```
$ pip3 install --ignore-installed vespacli ir_datasets ir_measures requests
```

We can quickly look at a document from [nfcorpus](https://ir-datasets.com/beir.html#beir/nfcorpus):

```
$ ir_datasets export beir/nfcorpus docs --format jsonl | head -1
```

Which outputs:

```
```

The NFCorpus documents have four fields:

* The `doc_id` and `url`
* The `text` and the `title`

We are interested in the title and the text, and we want to be able to search across these two fields. We also need to store the `doc_id` to evaluate [ranking](../ranking.html) accuracy. We will create a small script that converts the above output to [Vespa JSON document](../reference/document-json-format.html) format. Create a `convert.py` file:

```
```

With this script, we convert the document dump to Vespa JSON format. Use the following command to convert the entire dataset to Vespa JSON format:

```
$ ir_datasets export beir/nfcorpus docs --format jsonl | python3 convert.py > vespa-docs.jsonl
```

Now, we will create the Vespa application package and schema to index the documents.

### Create a Vespa Application Package

A [Vespa application package](../application-packages.html) is a set of configuration files and optional Java components that together define the behavior of a Vespa system. Let us define the minimum set of required files to create our hybrid text search application: `doc.sd` and `services.xml`.

```
$ mkdir -p app/schemas
```

#### Schema

A [schema](../schemas.html) is a document-type configuration; a single Vespa application can have multiple schemas with document types. For this application, we define a schema `doc`, which must be saved in a file named `schemas/doc.sd` in the application package directory.

Write the following to `app/schemas/doc.sd`:

```
schema doc {
    document doc {
        field language type string {
            indexing: "en" | set_language 
        }
        field doc_id type string {
            indexing: attribute | summary
            match: word
        }
        field title type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
        field text type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
    }
    fieldset default {
        fields: title, text
    }
field embedding type tensor&lt;bfloat16&gt;(v[384]) {    indexing: input title." ".input text | embed | attribute    attribute {        distance-metric: angular    }}rank-profile bm25 {    first-phase {        expression: bm25(title) + bm25(text)    }}rank-profile semantic {    inputs {        query(e) tensor&lt;bfloat16&gt;(v[384])    }    first-phase {        expression: closeness(field, embedding)    }}
}
```

A lot is happening here; let us go through it in detail.

**Document type and fields**

The `document` section contains the fields of the document, their types, and how Vespa should index and [match](../reference/schema-reference.html#match) them.

The field property `indexing` configures the _indexing pipeline_ for a field. For more information, see [schemas - indexing](../schemas.html#indexing). The [string](../reference/schema-reference.html#string) data type represents both unstructured and structured texts, and there are significant differences between [index and attribute](../text-matching.html#index-and-attribute). The above schema includes default `match` modes for `attribute` and `index` property for visibility.

Note that we are enabling [BM25](../reference/bm25.html) for `title` and `text` by including `index: enable-bm25`. The language field is the only field that is not the NFCorpus dataset. We hardcode its value to "en" since the dataset is English. Using `set_language` avoids automatic language detection and uses the value when processing the other text fields. Read more in [linguistics](../linguistics.html).

**Fieldset for matching across multiple fields**

[Fieldset](../reference/schema-reference.html#fieldset) allows searching across multiple fields. Defining `fieldset` does not add indexing/storage overhead. String fields grouped using fieldsets must share the same [match](../reference/schema-reference.html#match) and [linguistic processing](../linguistics.html) settings because the query processing that searches a field or fieldset uses _one_ type of transformation.

**Embedding inference**

Our `embedding` vector field is of [tensor](../tensor-user-guide.html) type with a single named dimension (`v`) of 384 values.

```
field embedding type tensor<bfloat16>(v[384]) {
    indexing: input title." ".input text | embed arctic | attribute
    attribute {
        distance-metric: angular
    }
}
```

The `indexing` expression creates the input to the `embed` inference call (in our example the concatenation of the title and the text field). Since the dataset is small, we do not specify `index` which would build [HNSW](../approximate-nn-hnsw.html) data structures for faster (but approximate) vector search. This guide uses [snowflake-arctic-embed-xs](https://huggingface.co/Snowflake/snowflake-arctic-embed-xs) as the text embedding model. The model is trained with cosine similarity, which maps to Vespa's `angular` [distance-metric](../reference/schema-reference.html#distance-metric) for nearestNeighbor search.

**Ranking to determine matched documents ordering**

You can define many [rank profiles](../ranking.html), named collections of score calculations, and ranking phases.

In this starting point, we have two simple rank-profile's:

* a `bm25` rank-profile that uses [BM25](../reference/bm25.html). We sum the two field-level BM25 scores using a Vespa [ranking expression](../ranking-expressions-features.html).
* a `semantic` rank-profile which is used in combination Vespa's nearestNeighbor query operator (vector search).

Both profiles specify a single [ranking phase](../phased-ranking.html).

#### Services Specification

The [services.xml](../reference/services.html) defines the services that make up the Vespa application — which services to run and how many nodes per service. Write the following to `app/services.xml`:

```
```

Some notes about the elements above:

* `<container>` defines the [container cluster](../jdisc/index.html) for document, query and result processing.
* `<search>` sets up the [query endpoint](../query-api.html). The default port is 8080.
* `<document-api>` sets up the [document endpoint](../reference/document-v1-api-reference.html) for feeding.
* `<component>` with type `hugging-face-embedder` configures the embedder in the application package. This includes where to fetch the model files from, the prepend instructions, and the pooling strategy. See [huggingface-embedder](../embedding.html#huggingface-embedder) for details and other embedders supported.
* `<content>` defines how documents are stored and searched.
* `<min-redundancy>` denotes how many copies to keep of each document.
* `<documents>` assigns the document types in the _schema_ to content clusters.

### Deploy the application package

Once we have finished writing our application package, we can deploy it. We use settings similar to those in the [Vespa quick start guide](../vespa-quick-start.html).

Start the Vespa container:

```
$ docker run --detach --name vespa-hybrid --hostname vespa-container \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa
```

Notice that we publish two ports: 8080 is the data-plane where we write and query documents, and 19071 is the control-plane where we can deploy the application. Note that the data-plane port is inactive before deploying the application.

Configure the Vespa CLI to use the local container:

```
$ vespa config set target local
```

Starting the container can take a short while. Make sure that the configuration service is running by using `vespa status`.

```
$ vespa status deploy --wait 300 
```

Now, deploy the Vespa application from the `app` directory:

```
$ vespa deploy --wait 300 app
```

### Feed the data

The data fed to Vespa must match the document type in the schema. This step performs embed inference inside Vespa using the snowflake arctic embedding model. Remember the `component` definition in `services.xml` and the `embed` call in the schema.

```
$ vespa feed -t http://localhost:8080 vespa-docs.jsonl
```

The output should look like this (rates may vary depending on your machine HW):

```
```

Notice:

* `feeder.ok.rate` which is the throughput (Note that this step includes embedding inference). See [embedder-performance](../embedding.html#embedder-performance) for details on embedding inference performance. In this case, embedding inference is the bottleneck for overall indexing throughput.
* `http.response.code.counts` matches with `feeder.ok.count`. The dataset has 3633 documents. Note that if you observe any `429` responses, these are harmless. Vespa asks the client to slow down the feed speed because of resource contention.

### Sample queries

We can now run a few sample queries to demonstrate various ways to perform searches over this data using the [Vespa query language](../query-language.html).

```
$ ir_datasets export beir/nfcorpus/test queries --fields query_id text | head -1
```

```
PLAIN-2	Do Cholesterol Statin Drugs Cause Breast Cancer?
```

If you see a pipe related error from the above command, you can safely ignore it.

Here, `PLAIN-2` is the query id of the first test query. We'll use this test query to demonstrate querying Vespa.

#### Lexical search with BM25 scoring

The following query uses [weakAnd](../using-wand-with-vespa.html) and where `targetHits` is a hint of how many documents we want to expose to configurable [ranking phases](../phased-ranking.html). Refer to [text search tutorial](text-search.html#querying-the-data) for more on querying with `userInput`.

```
$ vespa query \
  'yql=select * from doc where {targetHits:10}userInput(@user-query)' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'hits=1' \
  'language=en' \
  'ranking=bm25'
```

Notice that we choose `ranking` to specify which rank profile to rank the documents retrieved by the query. This query returns the following [JSON result response](../reference/default-result-format.html):

```
```

The query retrieves and ranks `MED-10` as the most relevant document—notice the `totalCount` which is the number of documents that were retrieved for ranking phases. In this case, we exposed about 50 documents to first-phase ranking, it is higher than our target, but also fewer than the total number of documents that match any query terms.

In the example below, we change the grammar from the default `weakAnd` to `any`, and the query matches 1780, or almost 50% of the indexed documents.

```
$ vespa query \
  'yql=select * from doc where {targetHits:10, grammar:"any"}userInput(@user-query)' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'hits=1' \
  'language=en' \
  'ranking=bm25'
```

The bm25 rank profile calculates the relevance score (\~25.521), which is configured in the schema as:

```
rank-profile bm25 {
    first-phase {
        expression: bm25(title) + bm25(text)
    }
}
```

So, in this case, `relevance` is the sum of the two BM25 scores. The retrieved document looks relevant; we can look at the graded judgment for this query `PLAIN-2`. The following exports the query relevance judgments (we grep for the query id that we are interested in):

```
$ ir_datasets export beir/nfcorpus/test qrels | grep "PLAIN-2 "
```

The following is the output from the above command. Notice line two, the `MED-10` document retrieved above, is judged as very relevant with the grade 2 (perfect) for the query\_id PLAIN-2. This dataset has graded relevance judgments where a grade of 1 is less relevant than 2. Documents retrieved by the system without a relevance judgment are assumed to be irrelevant (grade 0).

```
PLAIN-2 0 MED-2427 2
PLAIN-2 0 MED-10 2
PLAIN-2 0 MED-2429 2
PLAIN-2 0 MED-2430 2
PLAIN-2 0 MED-2431 2
PLAIN-2 0 MED-14 2
PLAIN-2 0 MED-2432 2
PLAIN-2 0 MED-2428 1
PLAIN-2 0 MED-2440 1
PLAIN-2 0 MED-2434 1
PLAIN-2 0 MED-2435 1
PLAIN-2 0 MED-2436 1
PLAIN-2 0 MED-2437 1
PLAIN-2 0 MED-2438 1
PLAIN-2 0 MED-2439 1
PLAIN-2 0 MED-3597 1
PLAIN-2 0 MED-3598 1
PLAIN-2 0 MED-3599 1
PLAIN-2 0 MED-4556 1
PLAIN-2 0 MED-4559 1
PLAIN-2 0 MED-4560 1
PLAIN-2 0 MED-4828 1
PLAIN-2 0 MED-4829 1
PLAIN-2 0 MED-4830 1
```

#### Dense search using text embedding

Now, we turn to embedding-based retrieval, where we embed the query text using the configured text-embedding model and perform an exact `nearestNeighbor` search. We use [embed query](../embedding.html#embedding-a-query-text) to produce the input tensor `query(e)`, defined in the `semantic` rank-profile in the schema.

```
$ vespa query \
  'yql=select * from doc where {targetHits:10}nearestNeighbor(embedding,e)' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'input.query(e)=embed(@user-query)' \
  'hits=1' \
  'ranking=semantic'
```

This query returns the following [JSON result response](../reference/default-result-format.html):

```
```

The result of this vector-based search differed from the previous sparse keyword search, with a different relevant document at position 1. In this case, the relevance score is 0.606 and calculated by the `closeness` function in the `semantic` rank-profile. Note that more documents were retrieved than the `targetHits`.

```
rank-profile semantic {
        inputs {
          query(e) tensor<bfloat16>(v[384])
        }
        first-phase {
            expression: closeness(field, embedding)
        }
    }
```

Where [closeness(field, embedding)](../reference/rank-features.html#attribute-match-features-normalized) is a ranking feature that calculates the cosine similarity between the query and the document embedding. This returns the inverted of the distance between the two vectors. Small distance = higher closeness. This because Vespa sorts results in descending order of relevance. Descending order means the largest will appear at the top of the ranked list.

Note that similarity scores of embedding vectors are often optimized via contrastive or ranking losses, which make them difficult to interpret.

### Evaluate ranking accuracy

The previous section demonstrated how to combine the Vespa query language with rank profiles to implement two different retrieval and ranking strategies.

In the following section we evaluate all 323 test queries with both models to compare their overall effectiveness, measured using [nDCG@10](https://en.wikipedia.org/wiki/Discounted_cumulative_gain). `nDCG@10` is the official evaluation metric of the BEIR benchmark and is an appropriate metric for test sets with graded relevance judgments.

For this evaluation task, we need to write a small script. The following script iterates over the queries in the test set, executes the query against the Vespa instance, and reads the response from Vespa. It then evaluates and prints the metric. The overall effectiveness is measured using the average of each query `nDCG@10` metric.

<pre><code>
import requests
import ir_datasets
from ir_measures import calc_aggregate, nDCG, ScoredDoc
from enum import Enum
from typing import List
class RModel(Enum):
SPARSE = 1
DENSE = 2
HYBRID = 3
def parse_vespa_response(response:dict, qid:str) -> List[ScoredDoc]:
result = []
hits = response['root'].get('children',[])
for hit in hits:
doc_id = hit['fields']['doc_id']
relevance = hit['relevance']
result.append(ScoredDoc(qid, doc_id, relevance))
return result
def search(query:str, qid:str, ranking:str,
hits=10, language="en", mode=RModel.SPARSE) -> List[ScoredDoc]:
yql = "select doc_id from doc where ({targetHits:100}userInput(@user-query))"
if mode == RModel.DENSE:
yql = "select doc_id from doc where ({targetHits:10}nearestNeighbor(embedding, e))"
elif mode == RModel.HYBRID:
yql = "select doc_id from doc where ({targetHits:100}userInput(@user-query)) OR ({targetHits:10}nearestNeighbor(embedding, e))"
query_request = {
'yql': yql,
'user-query': query,
'ranking.profile': ranking,
'hits' : hits,
'language': language
}
if mode == RModel.DENSE or mode == RModel.HYBRID:
query_request['input.query(e)'] = "embed(@user-query)"
response = requests.post("http://localhost:8080/search/", json=query_request)if response.ok:    return parse_vespa_response(response.json(), qid)else:  print("Search request failed with response " + str(response.json()))  return []
def main():
import argparse
parser = argparse.ArgumentParser(description='Evaluate ranking models')
parser.add_argument('--ranking', type=str, required=True, help='Vespa ranking profile')
parser.add_argument('--mode', type=str, default="sparse", help='retrieval mode, valid values are sparse, dense, hybrid')
args = parser.parse_args()
mode = RModel.HYBRID
if args.mode == "sparse":
mode = RModel.SPARSE
elif args.mode == "dense":
mode = RModel.DENSE
dataset = ir_datasets.load("beir/nfcorpus/test")
results = []
metrics = [nDCG@10]
for query in dataset.queries_iter():
qid = query.query_id
query_text = query.text
results.extend(search(query_text, qid, args.ranking, mode=mode))
metrics = calc_aggregate(metrics, dataset.qrels, results)
print("Ranking metric NDCG@10 for rank profile {}: {:.4f}".format(args.ranking, metrics[nDCG@10]))
<strong>if name == "main":
</strong>main(){% endhighlight %}
</code></pre>

Then execute the script:

```
$ python3 evaluate_ranking.py --ranking bm25 --mode sparse
```

The script will produce the following output:

```
Ranking metric NDCG@10 for rank profile bm25: 0.3210 
```

Now, we can evaluate the dense model using the same script:

```
$ python3 evaluate_ranking.py --ranking semantic --mode dense
```

```
Ranking metric NDCG@10 for rank profile semantic: 0.3077
```

Note that the _average_ `nDCG@10` score is computed across all the 327 test queries. You can also experiment beyond a single metric and modify the script to calculate more [measures](https://ir-measur.es/en/latest/measures.html), for example, including precision with a relevance label cutoff of 2:

```
metrics = [nDCG@10, P(rel=2)@10]
```

Also note that the exact nDCG@10 values may vary slightly between runs.

### Hybrid Search & Ranking

We demonstrated and evaluated two independent retrieval and ranking strategies in the previous sections. Now, we want to explore hybrid search techniques where we combine:

* traditional lexical keyword matching with a text scoring method (BM25)
* embedding-based search using a text embedding model

With Vespa, there is a distinction between retrieval (matching) and configurable [ranking](../ranking.html).

In the Vespa ranking phases, we can express arbitrary scoring complexity with the full power of the Vespa [ranking](../ranking.html) framework. Meanwhile, top-k retrieval relies on simple built-in functions associated with Vespa's top-k query operators.\
These top-k operators aim to avoid scoring all documents in the collection for a query by using a simplistic scoring function to identify the top-k documents.

These top-k query operators use `index` structures to accelerate the query evaluation, avoiding scoring all documents using heuristics. In the context of hybrid text search, the following Vespa top-k query operators are relevant:

* YQL `{targetHits:k}nearestNeighbor()` for dense representations (text embeddings) using a configured [distance-metric](../reference/schema-reference.html#distance-metric) as the scoring function.
* YQL `{targetHits:k}userInput(@user-query)` which by default uses [weakAnd](../using-wand-with-vespa.html) for sparse representations.

We can combine these operators using boolean query operators like AND/OR/RANK to express a hybrid search query. Then, there is a wild number of ways that we can combine various signals in [ranking](../ranking.html).

#### Define our first simple hybrid rank profile

First, we can add our first simple hybrid rank profile that combines the dense and sparse components using multiplication to combine them into a single score.

```
closeness(field, embedding) * (1 + bm25(title) + bm25(text))
```

* the [closeness(field, embedding)](../reference/rank-features.html#attribute-match-features-normalized) rank-feature returns a normalized score in the range 0 to 1 inclusive
* Any of the per-field BM25 scores are in the range of 0 to infinity

We add a bias constant (1) to avoid the overall score becoming 0 if the document does not match any query terms, as the BM25 scores would be 0. We also add `match-features` to be able to debug each of the scores.

```
schema doc {
    document doc {
        field language type string {
            indexing: "en" | set_language 
        }
        field doc_id type string {
            indexing: attribute | summary
            match: word
        }
        field title type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
        field text type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
    }
    fieldset default {
        fields: title, text
    }
field embedding type tensor&lt;bfloat16&gt;(v[384]) {  indexing: input title." ".input text | embed | attribute  attribute {    distance-metric: angular  }}rank-profile hybrid {    inputs {      query(e) tensor&lt;bfloat16&gt;(v[384])    }    first-phase {        expression: closeness(field, embedding) * (1 + (bm25(title) + bm25(text)))    }    match-features: bm25(title) bm25(text) closeness(field, embedding)}
}
```

Now, re-deploy the Vespa application from the `app` directory:

```
$ vespa deploy --wait 300 app
```

After that, we can start experimenting with how to express hybrid queries using the Vespa query language.

#### Hybrid query examples

The following demonstrates combining the two top-k query operators using the Vespa query language. In a later section, we will show how to combine the two retrieval strategies using the Vespa ranking framework. This section focuses on the top-k retrieval part that exposes matched documents to the Vespa [ranking](../ranking.html) phase(s).

**Hybrid query using the OR operator**

The following query exposes documents to ranking that match the query using _either (OR)_ the sparse or dense representation.

```
$ vespa query \
  'yql=select * from doc where ({targetHits:10}userInput(@user-query)) or ({targetHits:10}nearestNeighbor(embedding,e))' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'input.query(e)=embed(@user-query)' \
  'hits=1' \
  'language=en' \
  'ranking=hybrid'
```

The documents retrieved into ranking is scored by the \`hybrid\` rank-profile. Note that both top-k query operators might expose more than the the \`targetHits\` setting.

The above query returns the following [JSON result response](../reference/default-result-format.html):

```
```

What is going on here is that we are combining the two top-k query operators using a boolean OR (disjunction). The `totalCount` is the number of documents retrieved into ranking (About 90, which is higher than 10 + 10). The `relevance` is the score assigned by `hybrid` rank-profile. Notice that the `matchfeatures` field shows all the feature scores. This is useful for debugging and understanding the ranking behavior, also for feature logging.

**Hybrid query with AND operator**

The following combines the two top-k operators using AND, meaning that the retrieved documents must match both the sparse and dense top-k operators:

```
$ vespa query \
  'yql=select * from doc where ({targetHits:10}userInput(@user-query)) and ({targetHits:10}nearestNeighbor(embedding,e))' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'input.query(e)=embed(@user-query)' \
  'hits=1' \
  'language=en' \
  'ranking=hybrid'
```

For the sparse keyword query matching, the \`weakAnd\` operator is used by default and it requires that at least one term in the query matches the document (fieldset searched).

**Hybrid query with rank query operator**

The following combines the two top-k operators using the [rank](../reference/query-language-reference.html#rank) query operator, which allows us to retrieve using only the first operand of the rank operator, but where the remaining operands allow computing (match) features that can be used in ranking phases.

This query is meaningful because we can use the computed features in the ranking expressions but retrieve only by the dense representation. This is usually the most resource-effective way to combine the two representations.

```
$ vespa query \
  'yql=select * from doc where rank(({targetHits:10}nearestNeighbor(embedding,e)), ({targetHits:10}userInput(@user-query)))' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'input.query(e)=embed(@user-query)' \
  'hits=1' \
  'language=en' \
  'ranking=hybrid'
```

We can also invert the order of the operands to the \`rank\` query operator that retrieves by the sparse representation but uses the dense representation to compute features for ranking. This is very useful in cases where we do not want to build HNSW indexes (adds memory and slows down indexing), but still be able to use semantic signals in ranking phases.

```
$ vespa query \
  'yql=select * from doc where rank(({targetHits:10}userInput(@user-query)),({targetHits:10}nearestNeighbor(embedding,e)))' \
  'user-query=Do Cholesterol Statin Drugs Cause Breast Cancer?' \
  'input.query(e)=embed(@user-query)' \
  'hits=1' \
  'language=en' \
  'ranking=hybrid'
```

This way of performing hybrid retrieval allows retrieving only by the sparse representation and uses the dense vector representation to compute features for ranking.

### Hybrid ranking

In the previous section, we demonstrated combining the two top-k query operators using boolean query operators.

This section will show combining the two retrieval strategies using the Vespa ranking framework. We can first start evaluating the effectiveness of the hybrid rank profile that combines the two retrieval strategies.

```
$ python3 evaluate_ranking.py --ranking hybrid --mode hybrid
```

Which outputs

```
Ranking metric NDCG@10 for rank profile hybrid: 0.3287
```

The `nDCG@10` score is slightly higher than the profiles that only use one of the ranking strategies.

Now, we can experiment with more complex ranking expressions that combine the two retrieval strategies. We add a few more rank profiles to the schema that combine the two retrieval strategies in different ways.

```
schema doc {
    document doc {
        field language type string {
            indexing: "en" | set_language 
        }
        field doc_id type string {
            indexing: attribute | summary
            match: word
        }
        field title type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
        field text type string {
            indexing: index | summary
            match: text
            index: enable-bm25
        }
    }
    fieldset default {
        fields: title, text
    }
field embedding type tensor&lt;bfloat16&gt;(v[384]) {  indexing: input title." ".input text | embed | attribute  attribute {    distance-metric: angular  }}rank-profile hybrid {    inputs {      query(e) tensor&lt;bfloat16&gt;(v[384])    }    first-phase {        expression: closeness(field, embedding) * (1 + (bm25(title) + bm25(text)))    }    match-features: bm25(title) bm25(text) closeness(field, embedding)}rank-profile hybrid-sum inherits hybrid {    first-phase {        expression: closeness(field, embedding) + ((bm25(title) + bm25(text)))    }}rank-profile hybrid-normalize-bm25-with-atan inherits hybrid {        function scale(val) {        expression: 2*atan(val/8)/(3.14159)    }    function normalized_bm25() {        expression: scale(bm25(title) + bm25(text))     }    function cosine() {        expression: cos(distance(field, embedding))    }    first-phase {        expression: normalized_bm25 + cosine    }    match-features {        normalized_bm25         cosine         bm25(title)        bm25(text)    }}rank-profile hybrid-rrf inherits hybrid-normalize-bm25-with-atan{    function bm25_score() {        expression: bm25(title) + bm25(text)    }    global-phase {        rerank-count: 100        expression: reciprocal_rank(bm25_score) + reciprocal_rank(cosine)    }    match-features: bm25(title) bm25(text) bm25_score cosine}rank-profile hybrid-linear-normalize inherits hybrid-normalize-bm25-with-atan{    function bm25_score() {        expression: bm25(title) + bm25(text)    }    global-phase {        rerank-count: 100        expression: normalize_linear(bm25_score) + normalize_linear(cosine)    }    match-features: bm25(title) bm25(text) bm25_score cosine}
}

```

Now, re-deploy the Vespa application from the `app` directory:

```
$ vespa deploy --wait 300 app
```

Let us break down the new rank profiles:

* `hybrid-sum` combines the two retrieval strategies using addition. This is a simple way to combine the two strategies. But since the BM25 scores are not normalized (unbound) and the closeness score is normalized (0-1), the BM25 scores will dominate the closeness score.
* `hybrid-normalize-bm25-with-atan` combines the two strategies using a normalized BM25 score and the cosine similarity. The BM25 scores are normalized using the `atan` function.
* `hybrid-rrf` combines the two strategies using the reciprocal rank feature. This is a way to combine the two strategies using a reciprocal rank feature.
* `hybrid-linear-normalize` combines the two strategies using a linear normalization function. This is a way to combine the two strategies using a linear normalization function.

The two last profiles are using `global-phase` to rerank the top 100 documents using the reciprocal rank and linear normalization functions. This can only be done in the global phase as it requires access to all the documents that are retrieved into ranking and in a multi-node setup, this requires communication between the nodes and knowledge of the score distribution across all the nodes. In addition, each ranking phase can only order the documents by a single score.

#### Evaluate the new rank profiles

Adding new rank-profiles is a hot change. Once we have deployed the application, we can evaluate the new hybrid profiles using the script:

```
$ python3 evaluate_ranking.py --ranking hybrid-sum --mode hybrid
```

```
Ranking metric NDCG@10 for rank profile hybrid-sum: 0.3244
```

```
$ python3 evaluate_ranking.py --ranking hybrid-normalize-bm25-with-atan --mode hybrid
```

```
Ranking metric NDCG@10 for rank profile hybrid-normalize-bm25-with-atan: 0.3410
```

```
$ python3 evaluate_ranking.py --ranking hybrid-rrf --mode hybrid
```

```
Ranking metric NDCG@10 for rank profile hybrid-rrf: 0.3207
```

```
$ python3 evaluate_ranking.py --ranking hybrid-linear-normalize --mode hybrid
```

```
Ranking metric NDCG@10 for rank profile hybrid-linear-normalize: 0.3387
```

On this particular dataset, the `hybrid-normalize-bm25-with-atan` rank profile performs the best, but the difference is small. This also demonstrates that hybrid search and ranking is a complex problem and that the effectiveness of the hybrid model depends on the dataset and the retrieval strategies.

These results (which is the best) might not transfer to your specific retrieval use case and dataset, so it is important to evaluate the effectiveness of a hybrid model on your specific dataset.

See [Improving retrieval with LLM-as-a-judge](https://blog.vespa.ai/improving-retrieval-with-llm-as-a-judge/) for more information on how to collect relevance judgments for your dataset.

#### Summary

We showed how to express hybrid queries using the Vespa query language and how to combine the two retrieval strategies using the Vespa ranking framework. We also showed how to evaluate the effectiveness of the hybrid ranking model using one of the datasets that are a part of the BEIR benchmark. We hope this tutorial has given you a good understanding of how to combine different retrieval strategies using Vespa, and that there is not a single silver bullet for all retrieval problems.

### Cleanup

```
$ docker rm -f vespa-hybrid
```
