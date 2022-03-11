---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "News Recommendation Tutorial - parent child and tensor ranking"
redirect_from:
- /documentation/tutorials/news-7-recommendation-with-parent-child.html
---



This is the seventh part of the tutorial series for setting up a Vespa
application for personalized news recommendations. The parts are:  

1. [Getting started](news-1-getting-started.html)
2. [A basic news search application](news-2-basic-feeding-and-query.html) - application packages, feeding, query
3. [News search](news-3-searching.html) - sorting, grouping, and ranking
4. [Generating embeddings for users and news articles](news-4-embeddings.html)
5. [News recommendation](news-5-recommendation.html) - partial updates (news embeddings), ANNs, filtering
6. [News recommendation with searchers](news-6-recommendation-with-searchers.html) - custom searchers, doc processors
7. [News recommendation with parent-child](news-7-recommendation-with-parent-child.html) - parent-child, tensor ranking
8. Advanced news recommendation - intermission - training a ranking model
9. Advanced news recommendation - ML models

In this part of the series, we'll introduce a new ranking signal: category
click-through rate (CTR). The idea is that we can recommend popular content
for users that don't have a click history yet. Rather than just recommending
based on articles, we recommend based on categories. However, these global
CTR values can often change continuously, so we need an efficient way to
update this value for all documents. We'll do that by introducing
parent-child relationships between documents in Vespa. We will also use
sparse tensors directly in ranking.

For reference, the final state of this tutorial can be found in the
[app-7-parent-child](https://github.com/vespa-engine/sample-apps/tree/master/news/app-7-parent-child)
directory of the `news` sample application.


## Parent-child relationships in Vespa

Recall that most features come from either attributes in the document or
parameters passed with the query when ranking a document. Parent-child
relationships introduce the option of using attributes found in other
documents. Parent-child relationships work as a form of scalable document
joins.

For instance, assume we have a global CTR value for the sports category of `0.2`. 
If we want to use this value during ranking, we could have a field in each 
news article holding this value. However, when we need to update this value, we 
need to issue a partial update to all documents, which seems wasteful.

Another way would be to take inspiration from our `UserProfileSearcher`, where 
we retrieved the tensor embedding for a user in a search before passing that with 
the news article query. We could have a single document holding all global values
and retrieve that with each query. However, that isn't particularly efficient.

For these cases, Vespa introduced the [parent-child relationship](../parent-child.html).
Parents are global documents, which are automatically distributed to all 
content nodes. Other documents can reference these parents and "import" values for 
use in ranking. The benefit is that the global category CTR values only need to 
be written to one place: the global document.

Please see the [guide on parent-child relationships](../parent-child.html) for more
information and examples.

## Setting up a global category CTR document

So, let's set this up for our application. First we need to add a new document 
type to hold the CTR values. We introduce the `category_ctr` document type, 
which we add in `schemas/category_ctr.sd`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
schema category_ctr {
    document category_ctr {
        field ctrs type tensor&lt;float&gt;(category{}) {
            indexing: attribute
            attribute: fast-search
        }
    }
}
</pre>
</div>

This document holds a single field: a [tensor](../tensor-user-guide.html) of type
`tensor<float>(category{})`. This is a tensor with a single sparse dimension, which
is slightly different from the tensors we have seen so far. Sparse tensors have strings
as dimension addresses rather than a numeric index. More concretely, an example of 
such a tensor is (using the [tensor literal form](../reference/tensor.html#tensor-literal-form)):

```
{
    {category: entertainment}: 0.2 }, 
    {category: news}: 0.3 },
    {category: sports}: 0.5 },
    {category: travel}: 0.4 },
    {category: finance}: 0.1 },
    ...
}
```

This tensor holds all the CTR scores for all the categories. When updating this tensor,
we can update individual cells if we don't need to update the whole tensor.
This is called [tensor modify](../reference/document-json-format.html#tensor-modify) and 
can be helpful when you have large tensors.

To use this document, we need to add it to `services.xml`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
  &lt;content id="mind" version="1.0"&gt;
    ...
    &lt;documents&gt;
      &lt;document type="news" mode="index"/&gt;
      &lt;document type="user" mode="index"/&gt;
      &lt;document type="category_ctr" mode="index" global="true"/&gt;
    &lt;/documents&gt;
    ...
  &lt;/content&gt;
</pre>
</div>

Notice that we've set `global="true"`, which instructs Vespa to keep a copy 
of these documents on all content nodes. This is required for using it in a 
parent-child relationship.


## Importing parent values in child documents

To use the `category_ctr` tensor when ranking `news` documents, we need to
"import" the tensor. There are two things we need to set up: the reference to
the parent document, and which fields to import. We modify our
`schemas/news.sd`:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
schema news {
    document news {
        ...
        field category_ctr_ref type reference&lt;category_ctr&gt; {
            indexing: attribute
        }
        ...
    }
    import field category_ctr_ref.ctrs as global_category_ctrs {}
}
</pre>
</div>

The field `category_ctr_ref` is a field of type `reference` of a
`category_ctr` document type. When feeding this field, Vespa expects the
fully qualified document id. For instance, if our global CTR document has the
id `id:category_ctr:category_ctr::global`, that is what this field must be 
set to. Usually, there are many parent documents that children can reference,
but our application will only hold one.

You can think of the reference field as holding a foreign key
to the parent document, and the import as performing a real-time 
join between the child and parent document using this foreign key.
The imported values are usable as if they were stored with the child.

The `import` statement defines that we should import the `ctrs` field from
the document referenced in the `category_ctr_ref` field. We name this as
`global_category_ctrs`, and we can reference this as
`attribute(global_category_ctrs)` during ranking.


## Tensor expressions in ranking

Up until this point, we've only used tensors as storage. We used tensors to
hold news and user embeddings, and Vespa used these tensors to calculate the
euclidean distances in our nearest-neighbor search.

However, Vespa has a [rich language](../tensor-user-guide.html#ranking-with-tensors)
to perform calculations with tensors. We'll exploit that by 
looking up the `news` article's category in the global CTR tensor and using that 
as a feature in ranking.

Our `news` document has a field currently that holds the `category` as a string. 
Unfortunately, tensor expressions only work on tensors, so we need to add a 
new field to hold the category tensor:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
    field category_tensor type tensor&lt;float&gt;(category{}) {
        indexing: attribute
    }
</pre>
</div>

Using a tensor in this way also enables a document to have multiple categories, 
but our dataset only has a single category per article. For instance, we 
can represent the `finance` category of a `news` article like this:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
    {category: finance}: 1.0 }
</pre>
</div>

Since this is a sparse tensor, we don't need to mention the other categories.
Now, we can use this tensor to calculate the global CTR score for an article's
category:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
    attribute(category_tensor) * attribute(global_category_ctrs)
</pre>
</div>

Given the global category CTR example above, this would result in the value
`0.1`. How did we arrive at this? Recall that the value for the cell
`finance` in the `category` dimension of the example above had a value of
`0.1`. The multiplication of these two tensors is conceptually an "inner
join", so you can take the matching cells and multiply them together. Due to
the sparseness of the tensor, only the `finance` cell matches, and that value
is multiplied by the `1.0` in this document. So in this case, this would
effectively work as a lookup.

{% include note.html content="Much more complex operations are available,
please refer to [the tensor user guide](../tensor-user-guide.html#ranking-with-tensors) for more information." %}

Let's add a new ranking profile to perform this calculation:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
rank-profile recommendation_with_global_category_ctr inherits recommendation {
    function category_ctr() {
        expression: sum(attribute(category_tensor) * attribute(global_category_ctrs))
    }
    function nearest_neighbor() {
        expression: closeness(field, embedding)
    }
    first-phase {
        expression: nearest_neighbor * category_ctr
    }
    summary-features {
        attribute(category_tensor)
        attribute(global_category_ctrs)
        category_ctr
        nearest_neighbor
    }
}
</pre>
</div>

Here, we've added a first phase ranking expression that multiplies the nearest-neighbor 
score with the category CTR score, implemented with the functions `nearest_neighbor` 
and `category_ctr`, respectively. We've added a `sum` function around the `category_ctr` 
expression - this is simply to unbox the single-value tensor to a double value suitable 
for use in the first phase expression.

Note that, as a first attempt, we just multiply the nearest-neighbor with the category CTR
score. This is not necessarily the correct way to combine these values, but we'll get back
to that in a bit.

We've added a section for [summary features](../reference/schema-reference.html#summary-features).
This is simply a list of features that will be returned with the hit when using this 
rank profile. Recall that we can specify which features should be returned in the summary 
with the `indexing: summary` statement with each field. The `summary-features` can also include
the result of functions as well. This is a helpful debugging tool, and we'll see how this looks
after feeding some data.


## Feeding parent and child updates

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-expect="BUILD SUCCESS" data-test-timeout="300">
$ cd ../app-7-parent-child
$ mvn package
</pre>
</div>

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Success">
$ vespa deploy --wait 300
</pre>
</div>

After deploying the application, we are ready to feed a global CTR document.
For convenience, we've added a script that reads the MIND content and
impression data to calculate CTR scores for each category:

<pre>
$ ./src/python/create_category_ctrs.py mind
</pre>

This produces two files in the `mind` directory:

1. `mind/global_category_ctr.json` - a feed file for the global CTR document containing CTR 
   score for each category.
2. `mind/news_category_ctr_update.json` - a feed file for partially updating the `news` 
   articles with the reference to the global CTR document as well as the category tensor. 

These files can now be fed to Vespa, but note that the
`mind/global_category_ctr.json` need to be fed first because the global
document needs to exist before the child documents can reference it.

<pre data-test="exec">
$ cd ..
$ ./src/python/create_category_ctrs.py mind
$ ./vespa-feed-client-cli/vespa-feed-client \
--verbose --file mind/global_category_ctr.json --endpoint http://localhost:8080
$ ./vespa-feed-client-cli/vespa-feed-client \
--verbose --file mind/news_category_ctr_update.json --endpoint http://localhost:8080
</pre>


## Testing the application

After feeding the above files, we can now test the application with a query:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="N25904">
$ vespa query 'user_id=U33527' 'ranking.profile=recommendation_with_global_category_ctr' 'hits=1' 
</pre>
</div>

Note that we specify the ranking profile to use. The first result of this query is something like
the following:

```
...
"fields": {
    "title": "Matthew Stafford's status vs. Bears uncertain, Sam Martin will play",
    "abstract": "abstract": "Stafford's start streak could be in jeopardy, according to Ian Rapoport.",
    "category": "sports",
    ...
    "summary-features": {
        "attribute(category_tensor)": {"cells": [{"address": { "category": "sports"}, "value":1.0 }]},
        "attribute(global_category_ctrs)": {"cells": [
            ...
            { "address": { "category": "sports" }, "value": 0.05611187964677811 },
            ...
        ]},
        "rankingExpression(category_ctr)": 0.05611187964677811,
        "rankingExpression(nearest_neighbor)": 0.14914761220236453,
    }
    ...
    "relevance": 0.008368952865503413,
}
```

This is clearly a sports article. The global CTR document is also listed here, and the CTR score
for the `sports` category is `0.0561`. Thus, the result of the `category_ctr` function is 
`0.0561` as intended. The `nearest_neighbor` score is `0.149`, and the resulting relevance 
score is `0.00836`. So, this worked as expected.

If we were to feed another value to the global CTR document, this updated value is 
immediately available. As such, the system responds quickly to changes in the global 
parameters.

Now, a simple multiplication between these features might not give us what we
want. For instance, these features have different average values different
standard deviations. Particularly, if we add multiple additional features,
just multiplying them together will probably not give a great user
experience.

To remedy this, we will try to learn a suitable weighting between features. We'll 
address this in the next part of this series.


## Conclusion

This tutorial introduced parent-child relationships and demonstrated it
through a global CTR feature we used in ranking. As this feature was based on
tensors, we also introduced ranking with tensor expressions. In the next part
of the tutorial, we will start using a machine-learned model in ranking.

<script src="/js/process_pre.js"></script>
