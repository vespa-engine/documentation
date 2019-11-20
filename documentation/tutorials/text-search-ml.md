---
# Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Improving Text Search through ML"
---

## Introduction

In this tutorial, we assume that you have followed the [Text Search Tutorial](text-search.html) and have created and deployed a basic text search app in Vespa and fed it with MS MARCO full document dataset. We are now going to show you how to create a dataset that joins relevance information from MS MARCO with ranking features from Vespa to enable you to train ML models to improve your application.

The first section will describe how to collect rank feature data from Vespa associated with a specific query. After that we will show how to create a dataset from a set of training queries that also contain information about relevant documents associated with each query. To finalize ... TODO.

## Collect rank feature data from Vespa

Vespa's [rank feature set](../reference/rank-features.html) contains a large set of low and high level features that are available to you upon request. Those features are useful to understand the behavior of your app or even to improve your ranking function.

### Default rank features

Vespa always return a particular set of ranking features by default. To access the default set of features we simply need to set the query parameter [`ranking.listFeatures`](../reference/search-api-reference.html#ranking.listFeatures) equal to `true`. For example, below is the body of a post request that sends a specific query in [YQL format](../query-language.html), selects the `bm25` _ranking-profile_ developed in our previous tutorial and returns the rank features associated with each of the results returned by Vespa.

```
body = {
    "yql": 'select * from sources * where (userInput(@userQuery));',
    "userQuery": "what is dad bod",
    "presentation.format": "json",
    "ranking": {"profile": "bm25", "listFeatures": "true"},
}
```

The list of rank features that are returned by default can change in the future but the current list can be checked in [this system test](https://github.com/vespa-engine/system-test/blob/master/tests/search/rankfeatures/dump.txt). For the request specified by the body above we get the following (edited) json back. Each result will contain a field called `rankfeatures` containing the set of default ranking features.

```
{
  "root": {
    "children": [
      ... 
      {
        "fields": {
          "rankfeatures": {
            ...
            "attributeMatch(id).totalWeight": 0.0,
            "attributeMatch(id).weight": 0.0,
            "elementCompleteness(body).completeness": 0.5051413881748072,
            "elementCompleteness(body).elementWeight": 1.0,
            "elementCompleteness(body).fieldCompleteness": 0.010282776349614395,
            "elementCompleteness(body).queryCompleteness": 1.0,
            "elementCompleteness(title).completeness": 0.75,
            "elementCompleteness(title).elementWeight": 1.0,
            "elementCompleteness(title).fieldCompleteness": 1.0,
            "elementCompleteness(title).queryCompleteness": 0.5,
            "elementCompleteness(url).completeness": 0.0,
            "elementCompleteness(url).elementWeight": 0.0,
            "elementCompleteness(url).fieldCompleteness": 0.0,
            "elementCompleteness(url).queryCompleteness": 0.0,
            "fieldMatch(body)": 0.7529285549778888,
            "fieldMatch(body).absoluteOccurrence": 0.065,
            ...
         }
        },
        "id": "index:msmarco/0/811ccbaf9796f92bfa343045",
        "relevance": 37.7705101001455,
        "source": "msmarco"
      },
   ],
    ...
}
```

### Chose and process specific rank features

If instead of returning the default ranking features you want to select a few specific ones from [our list of ranking features](../reference/rank-features.html), you can add a new _ranking-profile_ (let's call it `collect_rank_features`) to our _msmarco.sd_ search definition and disable the default ranking features by adding `ignore-default-rank-features` to the new _ranking-profile_. In addition, we can specify the desired features within the `rank-features` element. In the example below we explicitly configured Vespa to only return `bm25(title)`, `bm25(body)`, `nativeRank(title)` and `nativeRank(body)`. 

```
rank-profile collect_rank_features inherits default {

    first-phase {
        expression: random
    }

    ignore-default-rank-features

    rank-features {
        bm25(title)
        bm25(body)
        nativeRank(title)
        nativeRank(body)
    }

}
```

The `random` global feature is explained in the [Rank Feature Reference](https://docs.vespa.ai/documentation/reference/rank-features.html)  documentation and will be useful in the next section when we describe our data collection process.

After adding the _rank-profile_ `collect_rank_features` to our _msmarco.sd_ file, you should redeploy the app:

<pre data-test="exec">
docker exec vespa-msmarco bash -c '/opt/vespa/bin/vespa-deploy prepare /app/src/main/application && \
    /opt/vespa/bin/vespa-deploy activate'
</pre>

## Create a training dataset

The [MS MARCO](http://msmarco.org) dataset described in [the previous tutorial](text-search.html) provides us with more than 300.000 training queries, each of which is associated with a specific document id that is relevant to the query. In this section we want to combine the information contained in the pairs `(query, relevant_id)` with the information available in the Vespa ranking features to create a dataset that can be used to train ML models to improve the ranking function of our msmarco text app.

Before we move on to describe the collection process in detail, we want to point out that the whole process can be replicated by the following call to the data collection script `collect_training_data.py` available in [this tutorial repository](https://github.com/vespa-engine/sample-apps/tree/master/text-search). 
 
TODO: Make the collect script work with sample data
```
./src/python/collect_training_data.py data/msmarco-doctrain-queries.tsv.gz data/msmarco-doctrain-qrels.tsv.gz data collect_rank_features 99
```

The command above use data contained in the query (data/msmarco-doctrain-queries.tsv.gz) and in the relevance (data/msmarco-doctrain-qrels.tsv.gz) files that are part of the MSMARCO dataset, and send queries to Vespa using the `collect_rank_features` _ranking-profile_ defined in the previous section in order to request 99 randomly selected documents for each query in addition to the relevant document associated with the query. All the data from the request are then parsed and stored in the output folder, which is chosen to be `data` in this case.

### Data collection logic

Since we want to improve the first-phase ranking function of our application, our goal here is to create a dataset that will be used to train models that will generalize well when those models are used in the first-phase ranking of an actual Vespa instance running against possibly unseen queries and documents. This might seem obvious at first but turns out to be easy to neglect when making some data collection decisions.

The logic behind the `collect_training_data.py` can be summarized by the pseudo-code below:

```
hits = get_relevant_hit(query, rank_profile, relevant_id)
if relevant_hit:
    hits.extend(get_random_hits(query, rank_profile, number_random_sample))
    data = annotate_data(hits, query_id, relevant_id)
    append_data(file, data) 
```

For each query, we first send a request to Vespa to get the relevant document associated with the query. If the relevant document is matched by the query, Vespa will return it and we will expand the number of documents associated with the query by sending a second request to Vespa, this time asking Vespa to return a number of random documents sampled from the set of documents that were matched by the query. We then parse the hits returned by Vespa and organize the data into a tabular form containing the rank features and the binary variable indicating if the query-document pair is relevant or not.

We are only interested in collecting documents that are matched by the query because those are the documents that would be presented to the first-phase model. This means that we will likely leave some queries that contain information about relevant documents out of the collected dataset but it will create a dataset that are closer to our stated goal.

### Get relevant hit

The first Vespa request is contained in the function call `get_relevant_hit(query, rank_profile, relevant_id)` where the `query` parameter contains the desired query string, `rank_profile` is set to the `collect_rank_features` defined earlier and `relevant_id` is the document id that is said to be relevant to that specific query.

The body of the request is given by
```
body = {
    "yql": "select id, rankfeatures from sources * where  (userInput(@userQuery));",
    "userQuery": query,
    "hits": 1,
    "recall": "+id:" + str(relevant_id),
    "ranking": {"profile": rank_profile, "listFeatures": "true"},
}
```
where the `yql` and `userQuery` parameters instruct Vespa to return the _id_ of the documents along with the selected _rankfeatures_ defined in the _collect_rank_features_ rank-profile. The `hits` parameter is set to 1 because we know there are only one relevant id for each query, so we set Vespa to return only one document in the result set. The `recall` parameter allow us to specify the exact document _id_ we want to retrieve. The `ranking` parameter specify which _rank_profile_ we want to use and enable the rank features dumping by setting `listFeatures` to `True`.

Note that the parameter `recall` only works if the document is matched by the query, which is exactly the behavior we want in this case, as discussed in the data collection logic. The `recall` syntax to retrieve one document with id equal to 1 is given by `"recall": "+id:1"` and the syntax to retrieve more than one document, say documents with ids 1 and 2 is given by `"recall": "+(id:1 id:2)"`.

### Get random hits

The second Vespa request happens when we want to extend the dataset by adding randomly selected documents from the matched set. The request is contained in the function call `get_random_hits(query, rank_profile, number_random_sample)` where the only new parameter is `number_random_sample`, which specify how many documents we should sample from the matched set.

The body of the request is given by
```
body = {
    "yql": "select id, rankfeatures from sources * where (userInput(@userQuery));",
    "userQuery": query,
    "hits": number_random_sample,
    "ranking": {"profile": collect_features, "listFeatures": "true"},
}
```
where the only changes with respect to the `get_relevant_hit` is that we no longer need to use the `recall` parameter and that we set the number of hits returned by Vespa to be equal the `number_random_sample`. This works as intended because we have used 
```
first-phase {
    expression: random
}
```
in the `collect_rank_features` _rank-profile_ defined earlier in this tutorial. Using `random` as our first-phase ranking function ensures that the top documents returned by Vespa are randomly selected from the set of documents that were matched by the query.

### Anotated data

Once we have both the relevant and the random documents associated with a given query, we parse the Vespa result and store is in a file with the following format:

<html>
<table border="1" class="dataframe">
  <col width="120" align="center">
  <col width="120">
  <col width="120">
  <col width="120">
  <col width="120">
  <col width="120">
  <col width="120">
  <thead>
      <tr style="text-align: right;">
            <th>bm25(body)</th>
            <th>bm25(title)</th>
            <th>nativeRank(body)</th>
            <th>nativeRank(title)</th>
            <th>docid</th>
            <th>qid</th>
            <th>relevant</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>25.792076</td>
            <td>12.117309</td>
            <td>0.322567</td>
            <td>0.084239</td>
            <td>D312959</td>
            <td>3</td>
            <td>1</td>
        </tr>
        <tr>
            <td>22.191228</td>
            <td>0.043899</td>
            <td>0.247145</td>
            <td>0.017715</td>
            <td>D3162299</td>
            <td>3</td>
            <td>0</td>
        </tr>
        <tr>
            <td>13.880625</td>
            <td>0.098052</td>
            <td>0.219413</td>
            <td>0.036826</td>
            <td>D2823827</td>
            <td>3</td>
            <td>0</td>
        </tr>
    </tbody>
</table>
</html>

where the values in the `relevant` column is equal to 1 if document `docid` is relevant to the query `qid` and zero otherwise.

## Data collection sanity check

In the process of writing this tutorial and creating the data collection logic described above, we found it useful to develop a data collection sanity-check to help us catch bugs in our process. There is no unique right answer here but our proposal is to use the dataset to train a model using the same features and functional form used by the baseline you want to improve upon.

...


After collecting the dataset we would split our dataset into training and validation sets. We would then train a linear model containing only the features used 

## Using TensorFlow in a ranking function

### Training the model

### Deploying the model in Vespa

## Conclusion

TODO: Compare with the results obtained in part 1


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
