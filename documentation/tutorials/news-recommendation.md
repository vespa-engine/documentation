---
# Copyright Verizon Media. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "News Recommendation Tutorial"
---

## Introduction

For blog post: intro to using Vespa as a recommender platform, and something
about Vespa.

The basic function of a recommendation system is to provide items of interest
to any given user. The more we know about the user, the better
recommendations we can provide. We can view recommendation as search where
the user profile is the query. So, in this tutorial we will build upon
the previous news search tutorial by creating user profiles and use 
them to search for relevant news articles.

In this tutorial we'll touch upon quite a few things:

- Creating embeddings to represent user interests and news articles
- Feeding news embeddings as partial updates
- Adding a second document type to represent users
- Creating a custom searcher to modify queries
- Nearest neighbor search - and extending to approximate nearest neighbors
- Approximate nearest neighbors with filters

Let's start with looking at what data the MIND dataset provides for us.

## The MIND dataset

The MIND dataset, for our purposes in this series of tutorials, consists 
of two main files: `news.tsv` and `behaviors.tsv`. We used the former 
in the previous tutorial, as that contains all news article content.

The `behaviors.tsv` file contains a set of impressions. An impression is a
ordered list of news articles that was generated for a user. It includes
which of those articles the user clicked, and conversely, which ones were
not. We designate articles not clicked as "skips". Also included in the
impression is a list of articles the user has previously clicked. An example
is:

```
3       U11552  11/11/2019 1:03:52 PM   N2139   N18390-0 N10537-0 N23967-1
```

Here, user `U11552` was shown three articles: `N18390`, `N10537`, and
`N23967`, of which the user skipped two and clicked the last one. At that
time, the user had previously clicked on article `N2139`. We can
cross-reference with the `news.tsv` and extract the content of these
articles.

We interpret a click as a positive signal for interest, and a skip as
possibly a negative signal for interest. This is called implicit feedback, as
the users haven't explicitly expressed their interests. However, using clicks
and skips we can anyway start to infers the users' interests.

<!-- Perhaps add something about this being a dataset for reranking? -->

## Collaborative filtering in recommendation systems

A simple approach to provide recommendations to the above would be to extract
the categories, subcategories, and/or entities the users have implicitly
interacted with, and store these for each user. We can call this a sparse
user profile, because we store the exact terms of entities or categories. We
could then use traditional information retrieval techniques to search for
more articles with similar content.

However, by doing this we miss out on a lot of information. For instance,
some categories or entities are similar which could be of interest for the
user. Also, users with similar interests tend to click on similar articles.
So, if some type of content was interesting to one user, it would likely be
interesting to similar users.

<!-- Lot of "similar" and "interests" in the above -->

Exploiting this information is called collaborative filtering, and the
classical approach to this is matrix factorization. In this approach we
create a large matrix with users along one axis and news articles along the
other. We'll call this the interaction matrix. Then we factorize this matrix
into two smaller matrices, where the product of these two smaller
approximates the original.

![Matrix factorization](images/mf.png)

In the image above, you can see a user matrix with as many rows as there are
users, and a news matrix with as many columns as there are news articles.
Each user row, or news column, has the same length, signified by the `k`
dimension. The intuition is that the dot product of the `k` length vector for
a user and news pair approximates the interest the user has for the news
article. Since the information is compressed into the `k` vector, this works
across users as well. Thus the "collaborative" filtering.

These `k` length vectors can be extracted from the matrices, and associated
with the user or news article. So, when we want to recommend news articles to
a user, we simply find the user's vector and find the articles with the
highest dot products. In the following we will use this approach to generate
such embeddings for users and news articles.

Please note however, for this problem domain of news recommendation,
this approach would not work very well in practice. The reason is that a
large part of news recommendation is to recommend **new** news articles,
which might not have received any implicit feedback yet. This is called the
"cold start" problem. For such problems we need to use additional content
(often called "side information") of news articles to provide
recommendations. 

We'll tackle this "cold start" problem in the next part of the tutorial
series.

## Generating embeddings 

A common method for factorizing the interaction matrix is to use Alternating
Least Squares. The idea is to randomly fill the user and news matrices, 
and freeze the parameters of one of the matrices while solving for the other.
By alternating between which matrix is fixed, this can be solved with a 
traditional least squares problem. We can iterate the process until 
convergence.

The goal of this tutorial is to generate embeddings so that the dot product 
between a user and news vector signifies the probability of a click. Using 
this signal we can rank news articles by click probability. To train the
embedding vectors, we will use a stochastic gradient descent approach 
to modify the embeddings so that their dot product followed by the logistic 
function predicts a user click. We use a binary cross-entropy as loss function.

We'll use PyTorch for this. The main PyTorch model class is as follows:

```
class MF(torch.nn.Module):
    def __init__(self, num_users, num_items, embedding_size):
        super(MF, self).__init__()
        self.user_embeddings = torch.nn.Embedding(num_embeddings=num_users,
                                                  embedding_dim=embedding_size)
        self.news_embeddings = torch.nn.Embedding(num_embeddings=num_items,
                                                  embedding_dim=embedding_size)

    def forward(self, users, items):
        user_embeddings = self.user_embeddings(users)
        news_embeddings = self.news_embeddings(items)
        dot_prod = torch.sum(torch.mul(user_embeddings, news_embeddings), 1)
        return torch.sigmoid(dot_prod)
```

We use the PyTorch's `Embedding` class to hold the user and news embeddings.
The forward function is the forward pass of the gradient descent. First, the
the users and items selected for a mini-batch update are extracted from their
embedding tables. Then we take the dot-product with a logistic function and
return the value. This prediction for user and news pairs is then evaluated 
against the click or skip labels:

```
    # forward + backward + optimize
    user_ids, news_ids, labels = batch
    prediction = model(user_ids, news_ids)
    loss = loss_function(prediction.view(-1), labels)
    loss.backward()
    optimizer.step()
```

This is done across a number of epochs. The `batch` here contains a batch of
`user_id`s, `news_id`s, and `label`s used for training a mini-batch. For
instance, from the example impression above, a training example would be
`U11552, N23967, 1`. The code responsible for generating the training data
samples 4 negative examples (skips) for each positive example (click). This
is done across a number of epochs.

The full code can be seen in the sample application (ADD LINK HERE!). 

Let's go ahead and generate the embeddings. Run the following:

<pre data-test="exec">
$ # ./src/python/train_gmf.py mind 10
</pre>

This runs the training code for 10 epochs, and deposits the resulting
user and news vectors in the `mind` directory, where the rest if the 
data is. This outputs something like the following (if run for 100):

```
Total loss after epoch 1: 573.5299682617188 (3.49713397026062 avg)
Total loss after epoch 2: 551.6585083007812 (3.363771438598633 avg)
Total loss after epoch 3: 523.4100952148438 (3.1915249824523926 avg)
...
Total loss after epoch 99: 27.76451301574707 (0.16929581761360168 avg)
Total loss after epoch 100: 27.45075035095215 (0.1673826277256012 avg)
Train: {'auc': 0.9737, 'mrr': 0.7158, 'ndcg@5': 0.8193, 'ndcg@10': 0.842}
Valid: {'auc': 0.5101, 'mrr': 0.2181, 'ndcg@5': 0.224, 'ndcg@10': 0.2874}
```

We can see the loss reduces over the number of epochs. The two final lines
here are ranking metrics run on the training set and validation set. Here,
the `AUC` metric - Area Under the (ROC) Curve - is at `0.974` for the 
training set and `0.51` for the validation set. In this case,
this metric measures the probability of ranking relevant news higher than
non-relevant news. A score of around `0.5` means that it is totally random.
Thus, we haven't learned anything of use for the validation set.

This is not overfitting, but rather an instance of the problem mentioned
earlier. The validation set contains news articles shown to users a period
after the data found in the training set. Thus, most news articles are new,
and their embedding vectors are effectively random. Again, we will address
this in the next part of the tutorials. For now, we have at least trained
some sensible user and news vectors for the training set.

<!-- Add image for loss here ? -->

Next, we'll feed these vectors to Vespa.

## Mapping from inner-product search to Euclidean search

There is one more step we need to do before feeding these vectors 
to Vespa. The vectors have been trained to maximize the inner product.
Find the best news articles given a user vector is called Maximum 
Inner Product Search - or MIPS. Unfortunately, this form isn't 
really suitable for efficient retrieval. We'll get back to this 
later when discussing approximate nearest neighbors.

To facilitate efficient retrieval, we need to map the MIPS problem to a
Euclidean nearest neighbor search problem. We use the technique discussed in
[Speeding Up the Xbox Recommender System Using a Euclidean Transformation for
Inner-Product
Spaces](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/XboxInnerProduct.pdf). 

See [Nearest Neighbor
Search](https://docs.vespa.ai/en/nearest-neighbor-search.html) for more 
information on nearest neighbor search and distance metrics in Vespa. 

To map the embeddings to a Euclidean space and create a feed suitable for
Vespa, run the following:

<pre data-test="exec">
$ ./bin/convert-embeddings.sh
</pre>

We are now ready to feed these vectors to Vespa.

## Feeding embeddings

First, we need to modify the `news.sd` search definition to include a field
to hold the embedding. Add the following field and rank profile:

```
schema news {
  document news {
    ...
    field embedding type tensor<float>(d0[51]) {
        indexing: attribute 
        attribute {
            distance-metric: euclidean
        }
    }
  }
  ...
  rank-profile recommendation {
    first-phase {
      expression: closeness(field, embedding)
    }
  }
}
```

The `embedding` field is a tensor field. Tensors in Vespa are flexible
multi-dimensional data structures, and, as first-class citizens, can be used
in queries, document fields, and constants in ranking. Tensors can be either
dense or sparse or both, and can contain any number of dimensions. Please see
[the tensor user guide](https://docs.vespa.ai/en/tensor-user-guide.html) for
more information.

Here we have defined a dense tensor with a single dimension (`d0` - dimension
0), which represents a vector. The distance metric is euclidean as we 
would like to use this field for nearest neighbor search.

This is seen in the `recommendation` rank profile. Here, we've added 
a ranking expression using the [closeness](https://docs.vespa.ai/en/reference/rank-features.html#closeness(dimension,name)) 
ranking feature, which calculate the euclidean distance and user 
that to rank the news articles.

If you take a look at the file generated for the news embeddings,
`mind/vespa_news_embeddings.json`, you'll see a number of lines with
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

This is called a partial update. So, assuming you already have a system up
and running from the previous search tutorial, you don't need to feed the
entire corpus. With a partial update, you only need to update the fields. So,
after training another set of embeddings you can partially feed them again.
Please refer to [Vespa reads and
writes](https://docs.vespa.ai/en/reads-and-writes.html) for more information
on feeding formats.

We need to add another document type to represent a user. Add 
the following schema in `schemas/user.sd`:

```
schema user {
    document user {
        field user_id type string {
            indexing: summary | attribute
            attribute: fast-search
        }
        field embedding type tensor<float>(d0[51]) {
            indexing: summary | attribute
        }
    }
}
```

This schema is set up so that we can search for a `user_id` and 
retrieve the user's embedding vector. We don't need to set up
any distance metric here, because we are not searching this field.

We also need to let Vespa know we want to use this document type, so we
modify `services.xml` and add it under `documents` in the `content` section:

```
<services version="1.0">
  ...
  <content id='mind' version='1.0'>
    <documents>
      <document type='news' mode="index"/>
      <document type='user' mode="index"/>
    </documents>
    ...
  </content>
  ...
</services>
```

After redeploying with the updates schemas and `services.xml`, feed the user
and news embeddings using the Vespa HTTP client:

<pre data-test="exec">
$ docker exec vespa bash -c 'java -jar /opt/vespa/lib/jars/vespa-http-client-jar-with-dependencies.jar \
    --file /app/mind/vespa_user_embeddings.json --host localhost --port 8080'
$ docker exec vespa bash -c 'java -jar /opt/vespa/lib/jars/vespa-http-client-jar-with-dependencies.jar \
    --file /app/mind/vespa_news_embeddings.json --host localhost --port 8080'
</pre>

Let's go ahead and test the system.

## Testing the application

First, let's find the user `U33527`. We issue a query with the following YQL:

<pre data-test="exec" data-test-assert-contains='"id": "id:user:user::U33527"'>
$ curl -s -H "Content-Type: application/json" --data \
    '{"yql" : "select * from sources user where user_id contains \"U33527\";", "hits": 1}' \
    http://localhost:8080/search/ | python -m json.tool
</pre>

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

Now we can use this vector to query the news articles. You can either write this
query by hand, but we have a convenience script which queries Vespa for you:

<pre data-test="exec" data-test-assert-contains='"id": "id:user:user::U33527"'>
$ ./src/python/user_search.py U33527 10
</pre>

This script first retrieves the user embedding using an HTTP `GET` query to
Vespa. It then parses the tensor containing the embedding vector. Finally, it
issues a `nearestNeighbor` search using a `POST` (however a `GET` would work
just as well). Please see [the documentation for nearest neighbor
operator](https://docs.vespa.ai/en/reference/query-language-reference.html#nearestneighbor)
for more on the syntax for nearest neighbor searches.

<!-- What about the query profile types? -->

When Vespa receives this query, it will scan linearly through all documents
in the system (28603 if you are using the MIND DEMO dataset), and score them
using the ranking profile `recommendation` we set up above. Recall that we
converted the problem from maximum inner product to euclidean distance.
However, Vespa sorts the final results by decreasing rank score. With a
euclidean distance search we want to find the smallest distances. To invert
the rank order, Vespa provides the `closeness` feature which is calculated as
`1 / (1 + distance)`.

Let's test that this works as intended. The sample app provides the 
following script:

<pre data-test="exec">
$ ./src/python/evaluate.py mind
</pre>

This reads both the training and validation set impressions, queries 
Vespa for each impression, and calculates the same metrics we saw 
during training. The result is:

```
Train: {'auc': 0.9737, 'mrr': 0.7158, 'ndcg@5': 0.8193, 'ndcg@10': 0.842}
Valid: {'auc': 0.5101, 'mrr': 0.2181, 'ndcg@5': 0.224, 'ndcg@10': 0.2874}
```

This is exactly the same as the results from the training. So, the conversion 
from inner product space to euclidean space works as intended. The
resulting rank scores are different, but the transformation evidently 
retains the same ordering.

## ANNs

So far, we've been using nearest neighbor search. This is a linear scan 
through all matching documents. For the MIND demo dataset we've been using
this isn't a problem as it only contains roughly 28000 documents, and 
Vespa only uses a few milliseconds to scan through these. However, as 
the index grows, the time spent becomes significant. 

Unfortunately, there are no exact methods for finding the nearest neighbors
efficiently. So we trade accuracy for efficiency in what is called
approximate nearest neighbors (ANN). Vespa provides a unique implementation 
of ANNs which uses the HNSW (hierarchical navigable small world) algorithm, 
while still being compatible with other facets of the search such as filtering.
We'll get back to this in the next section.

If you recall, Vespa returned something like the following when searching 
for single users above (with hits equals to 10):

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

Let's switch to using approximate nearest neighbors. For this, we must 
instruct Vespa to create an index on the field we would like to use.
This is simply a modification to the `embedding` field in `news.sd`:

```
    field embedding type tensor<float>(d0[51]) {
        indexing: attribute | index
        attribute {
            distance-metric: euclidean
        }
    }
```

If you make this change and deploy it, you will get prompted by Vespa that 
a restart is required so that the index can be built. Do this now:

<pre data-test="exec">
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-deploy prepare /app/src/main/application &&  \
    /opt/vespa/bin/vespa-deploy activate'
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-stop-services'
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-start-services'
</pre>

After waiting a bit for Vespa to start, we can query Vespa again:

```
$ ./src/python/user_search.py U33527 10
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
When used in an approximate nearest neighbor search, this graph 
is queried and only the closest points as determined by this graph is 
added to the list. Thus, Vespa can stop searching early.

The particularly observant might have noticed that the result set 
has changed. Indeed, the third result when using exact nearest 
neighbor search was news article `N438`. This was omitted from 
the approximate search. As mentioned, we trade accuracy for efficiency 
when using approximate nearest neighbor search.

It should also be mentioned that searching through this graph comes with a
cost. In our case, since we only have a relatively small amount of documents,
there isn't that much gain in efficient. However, as the number of documents
grow this starts to pay off. See [Approximate nearest neighbor search in
Vespa](https://blog.vespa.ai/approximate-nearest-neighbor-search-in-vespa-part-1/)
for more of a discussion around this.

The implementation of ANN using HNSW in Vespa has some nice features.
Notice that we did not have to re-feed the corpus to enable ANN. Many 
other approaches for ANNs require building an index offline, in a batch job.
HNSW allows for incrementally building this index, which is fully exploited 
in Vespa.

A unique feature of Vespa is that the implementation allows for filtering
during graph traversal, which we'll look at next.

## Filtering

A common case when using approximate nearest neighbors is to combine 
with some additional query filters. For instance, for retail search one
can imagine finding relevant products for a user. In this case, we should 
not recommend products that are out of stock. So an additional query 
filter would be to ensure that `in_stock` is true. 

Now, Most implementations of ANNs come in the form of a library, so they are not
integrated with the search at large. The natural approach is to first perform
the ANN, the *post-filter* the results. Unfortunately, this often leads to
sub-optimal results as relevant documents might not have been recalled. 
See [Using approximate nearest neighbor search in real world applications](https://blog.vespa.ai/using-approximate-nearest-neighbor-search-in-real-world-applications/)
for more of a discussion around this.

In our case, let's assume we want to retrieve 10 `sports` articles for a 
user. It turns out we need to retrieve at least 76 news articles from the 
search to get to 10 `sports` articles:

```
$ ./src/python/user_search.py U33527 10 | grep "category\": \"sports" | wc -l
0
$ ./src/python/user_search.py U33527 76 | grep "category\": \"sports" | wc -l
10
```

On the other hand, if we add a filter specifically:

```
$ ./src/python/user_search.py U33527 10 "AND category contains 'sports'" | \
    grep "category\": \"sports" | wc -l
10
```

Here, we only specify 10 hits and exactly 10 hits of `sports` category are 
returned. Vespa still searches through the graph starting from the query 
point, however the search does not stop when we have 10 hits. In effect, 
the graph search widens until 10 results fulfilling the filters are found.

As a note, very strict filters that filters away a large part of the 
corpus would entail that a lot of candidates in the graph are skipped 
while searching for the results the fulfill the filters. This can take 
an exponential amount of time. For this case, Vespa falls back to 
a linear, brute-force scan for efficiency.


## Addressing the cold start problem

As we saw above, the evaluation metrics for the validation set left 
a lot to be desired. We will address this in the next part of the tutorial.



<pre style="display:none" data-test="after">
$ # docker rm -f vespa
</pre>

<script>
function processFilePREs() {
    var tags = document.getElementsByTagName("pre");

    // copy elements, because the list above is mutated by the insert html below
    var elems = [];
    for (i = 0; i < tags.length; i++) {
        elems.push(tags[i]);
    }

    for (i = 0; i < elems.length; i++) {
        var elem = elems[i];
        if (elem.getAttribute("data-test") === "file") {
            var html = elem.innerHTML;
            elem.innerHTML = html.replace(/<!--\?/g, "<?").replace(/\?-->/g, "?>").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            elem.insertAdjacentHTML("beforebegin", "<pre class=\"filepath\">file: " + elem.getAttribute("data-path") + "</pre>");
        }
    }
};

processFilePREs();

</script>