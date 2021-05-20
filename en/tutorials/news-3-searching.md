---
# Copyright Verizon Media. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "News search and recommendation tutorial - searching"
---

<!-- Temporary - for doc testing - display is "none" -->
<pre style="display:none" data-test="exec" >
$ git clone https://github.com/vespa-engine/sample-apps.git
$ cd sample-apps/news
$ ./bin/download-mind.sh demo
$ python3 src/python/convert_to_vespa_format.py mind
$ docker run -m 10G --detach --name vespa --hostname vespa-tutorial \
    --volume `pwd`:/app --publish 8080:8080 vespaengine/vespa
</pre>
<pre style="display:none" data-test="exec" data-test-wait-for="200 OK">
$ docker exec vespa bash -c 'curl -s --head http://localhost:19071/ApplicationStatus'
</pre>
<pre style="display:none" data-test="exec">
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-deploy prepare /app/app-3-searching && /opt/vespa/bin/vespa-deploy activate'
</pre>
<pre style="display:none" data-test="exec" data-test-wait-for="200 OK">
$ curl -s --head http://localhost:8080/ApplicationStatus
</pre>
<pre style="display:none" data-test="exec" >
$ docker exec vespa bash -c 'java -jar /opt/vespa/lib/jars/vespa-http-client-jar-with-dependencies.jar \
    --verbose --file /app/mind/vespa.json --host localhost --port 8080'
</pre>
<pre style="display:none" data-test="exec"  data-test-wait-for='"content.proton.documentdb.documents.active.last":28603'>
$ docker exec vespa bash -c 'curl -s http://localhost:19092/metrics/v1/values' | tr "," "\n" | grep content.proton.documentdb.documents.active
</pre>


## Introduction

This is the third part of the tutorial series for setting up a Vespa
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
10. [Models hot swap](news-10-models-hot-swap.html) - atomic model updates

In the previous part, we converted the [Microsoft News
Dataset](https://msnews.github.io/) (MIND) to Vespa, and fed it to our
application. In this part, we'll issue searches in this content and 
look at sorting, grouping, and ranking the results.

For reference, the final state of this tutorial can be found in the
`app-3-searching` sub-directory of the `news` sample application.

Conceptually, Vespa has two stages when determining the exact result to
return. This first is "matching", where all the documents that match the
query are found. This is a binary decision; either the document matches or it
doesn't. For instance, when searching for a word, all documents that contain
it are selected as candidates in this stage.

The next stage determines the ordering of the results. We can think of the 
results being ordered either by:

- a fixed value, or attribute, in the document
- a function calculating a score

Ordering by an attribute is called [sorting](../reference/sorting.html). For
instance, we can sort by decreasing `date`.
[Grouping](../reference/grouping-syntax.html) also works on attributes. An 
example is to group the results by a `category` attribute.

Calculating a score to order by is generally called "ranking". As these 
scores are usually dependent upon both query and document, they can also 
be called "relevance". Such expressions can be arbitrarily complex, 
but in general, require some form of computation to find this score. Ranking 
can be divided into multiple phases as well.

We'll start by looking at attribute-based sorting and grouping before 
moving on to ranking.

## What is an attribute?

We saw multiple examples of attributes in the `news.sd` schema, for instance:

    field date type int {
        indexing: summary | attribute
    }

Note that this `date` field has been defined as an `int` here, and when
feeding document, we convert the date to the format `YYYYMMDD`.

An [_attribute_](../attributes.html) is an in-memory field - this is different
from  _index_ fields, which may be moved to a disk-based index as more
documents are added and the index grows.  Since attributes are kept in memory,
they are excellent for fields that require fast access, e.g., fields used for
sorting or grouping query results.  The downside is higher memory usage.  

<p class="alert alert-success"> 
By default, no index is generated for attributes, and search over these defaults
to a linear scan - to build an index for an attribute field, include
<code>attribute: fast-search</code> in the field definition.
</p>

### Example queries using attribute field

    {"yql" : "select * from sources * where default contains \"20191110\";"}

This is a single-term query for the term _20191110_ in the `default` field
set. In the search definition, the field `date` is not included in the
`default` fieldset, so no results are found.

    {"yql" : "select * from sources * where date contains \"20191110\";"}

To get documents that were created 10 November 2019, and whose `date` field is
_20191110_, replace `default` with `date` in the YQL query string.  Note that
since `date` has not been defined with `attribute:fast-search`, searching will
be done by scanning _all_ documents.

    {"yql" : "select * from sources * where default contains \"weather\" AND date contains \"20191110\";"}

This is a query with two terms; a search in the `default` field set for the term
"weather" combined with a search in the `date` field for the value _20191110_.
This search will be faster than the previous example, as the term "weather" is
for a field where there is an index. The search core will evaluate this 
term first.

### Range searches

The examples above searched over `date` just as any other field, and requested
documents where the value was exactly _20191110_.  Since the field is of type
_int_, however, we can use it for _range searches_ as well, using the "less
than" and "greater than" operators (`<` and `>`, or `%3C` and `%3E` URL
encoded if using GET-queries). The query

    {"yql" : "select * from sources * where date < 20191110;"}

finds all documents where the value of `date` is less than _20191110_, i.e.,
all documents from before 10 November 2019, while

    {"yql" : "select * from sources * where date <= 20191110 AND date >= 20191108;"}

finds all news articles from 8 November 2019 to 10 November 2019, inclusive.

### Sorting

The first feature we will look at is how an attribute can be used to change the
hit order.  By now, you have probably noticed that hits are returned in order
of descending relevance, i.e., how well the document matches the query — if
not, take a moment to verify this. You might ask how Vespa does this since 
we haven't even touched upon ranking yet. The answer is that
Vespa uses its [nativeRank](../nativerank.html) score unless anything else 
is defined. We'll get back to this later.

Now try to send the following query to Vespa, and look at the order of the
hits:

<pre data-test="exec" data-test-assert-contains='"coverage": 100'>
$ curl -s -H "Content-Type: application/json" --data '{"yql" : "select * from sources * where default contains \"music\" AND default contains \"festival\" order by date;"}' \
http://localhost:8080/search/ | python -m json.tool
</pre>

By default, sorting is done in ascending order. This can also be specified by
appending `asc` after the sort attribute name. Use `desc` to sort the  in
descending order:

    $ curl -s -H "Content-Type: application/json" --data '{"yql" : "select * from sources * where default contains \"music\" AND default contains \"festival\" order by date desc;"}' \
    http://localhost:8080/search/ | python -m json.tool

So, sorting is simply defined by the `order by` statement in YQL.

### Query time data grouping

[Grouping](../grouping.html) is the concept of looking through all matching
documents at query-time and then performing operations with specified fields
across all the documents — some common use cases include:

- Find all the unique values for a given field, make **one group per unique
  value**, and return the count of documents per group.
- **Group documents by time and date** in fixed-width or custom-width buckets.
  An example of fixed-width buckets could be to group all documents by year,
  while an example of custom buckets could be to sort bug tickets by date of
  creation into the buckets _Today_, _Past Week_, _Past Month_, _Past Year_,
  and _Everything else_.
- Calculate the **minimum/maximum/average value** for a given field.

Displaying such groups and their sizes (in terms of matching documents per
group) on a search result page, with a link to each such group, is a common way
to let users refine searches.  For now we will only do a very simple grouping
query to get a list of unique values for `category` ordered by the number of
documents they occur in and top 3 is shown:

<pre data-test="exec" data-test-assert-contains='"coverage": 100'>
$ curl -s -H "Content-Type: application/json" --data '{"yql" : "select * from sources * where sddocname contains \"news\" limit 0 | all(group(category) max(3) order(-count())each(output(count())));"}' \
http://localhost:8080/search/ | python -m json.tool
</pre>

Note that expression after the pipe (`|`): this is the grouping expression that
determines how grouping will be performed. You can read more about the grouping 
syntax in the [grouping reference documentation](../reference/grouping-syntax.html).

For this query, you will get something like the following:

    {
        "root": {
            "children": [
                {
                    "children": [
                        {
                            "children": [
                                {
                                    "fields": {
                                        "count()": 9115
                                    },
                                    "id": "group:string:news",
                                    "relevance": 1.0,
                                    "value": "news"
                                },
                                {
                                    "fields": {
                                        "count()": 6765
                                    },
                                    "id": "group:string:sports",
                                    "relevance": 0.6666666666666666,
                                    "value": "sports"
                                },
                                {
                                    "fields": {
                                        "count()": 1886
                                    },
                                    "id": "group:string:finance",
                                    "relevance": 0.3333333333333333,
                                    "value": "finance"
                                }
                            ],
                            "continuation": {
                                "next": "BGAAABEBGBC"
                            },
                            "id": "grouplist:category",
                            "label": "category",
                            "relevance": 1.0
                        }
                    ],
                    "continuation": {
                        "this": ""
                    },
                    "id": "group:root:0",
                    "relevance": 1.0
                }
            ],
            "coverage": {
                "coverage": 100,
                "documents": 28603,
                "full": true,
                "nodes": 1,
                "results": 1,
                "resultsFull": 1
            },
            "fields": {
                "totalCount": 28603
            },
            "id": "toplevel",
            "relevance": 1.0
        }
    }

So, the three most common unique values of `category` among the indexed documents
(for the demo data set) are:

- `news` with 9115 articles
- `sports` with 6765 articles
- `finance` with 1886 articles

Try to change the filter part of the YQL+ expression — the `where` clause — to
a text match of "weather", or restrict `date` to be less than 20191110, and see
how the list of unique values changes as the set of matching documents for your
query changes.  If you try to search for a single term that is *not* present in
the document set, you will see that the list of groups is empty as no
documents have been matched.

Please refer to the [grouping guide](../grouping.html) for more information 
and examples on grouping.

### Attribute limitations

Before we move on to ranking, it's important to know that use attributes 
has some limitations.

#### Memory usage

Attributes are kept in memory, as opposed to normal indexes where
the data is mostly kept on disk.  Even with large content nodes, one will notice
that it is not practical to define all the document type fields as
attributes, as it will heavily restrict the number of documents per search
node.  Some Vespa applications have more than 1 billion documents per node —
having megabytes of text in memory per document is not cost-effective.

#### Matching

Another limitation is the way *matching* is done for attributes.  Consider the
`title` field from our schema, and the document for the article with title "A
little snow causes a big mess, more than 100 crashes on Minnesota roads". In
the original input, the value for `title` is a string built of up the 14 words,
with a single white space character between them. How should we be able to
search this field?

For normal index fields, Vespa [tokenizes](../linguistics.html#tokenization)
the string.  In our case this means that the string above is split into the 14
tokens, enabling Vespa to match this document for:

- the single-term queries such as "Michigan", "snow" and "roads", 
- the exact phrase query "A little snow causes a big mess, more than 100 crashes on Minnesota roads", 
- a query with two or more tokens in either order (e.g. "minnesota crashes"). 

This is how we all have come to expect normal free text search to work.

However, there is a limitation in Vespa when it comes to attribute fields and
matching; string attributes do not support normal token-based matching — only *exact
matching* or *prefix matching*. Exact matching is the default, and, as the name
implies, it requires you to search for the exact contents of the field in order
to get a match.

#### When to use attributes

There are both advantages and drawbacks of using attributes — it enables
sorting and grouping, but requires more memory and gives limited matching
capabilities. When to use attributes depends on the application; in general,
use attributes for:

- fields used for sorting, e.g., a last-update timestamp,
- fields used for grouping, e.g., problem severity, and
- fields that are not long string fields.

Finally, all numeric fields should always be attributes.

## Relevance and Ranking

[Ranking](../ranking.html) and relevance were briefly mentioned above; what is
really the relevance of a hit? How can one change the relevance
calculations? It is time to introduce _rank profiles_ and _rank expressions_ —
simple, yet powerful methods for tuning the relevance.

Relevance is a measure of how well a given document matches a query.  The
default relevance is calculated by a formula that takes several factors into
consideration. It computes, in essence, how well the document matches the
terms in the query.  Some use cases for tweaking the relevance calculations:

- Personalize search results based on some property; age, nationality,
  language, friends and friends of friends.
- Rank fresh (age) documents higher, while still considering other relevance measures.
- Rank documents by geographical location, searching for relevant resources nearby.

Vespa allows creating any number of _rank profiles_: named collections of
ranking and relevance calculations that one can choose from at query time.  A
number of built-in functions and expressions are available to create highly
specialized rank expressions.

### News article popularity signal

During the conversion of the news dataset, the conversion script counted both the
number of times a news article was shown (impressions) and how many
clicks it received. A high number of clicks relative to impressions indicates
that the news article was generally popular. We can use this signal in our
ranking.

We can do this by including a `popularity` rank profile below at the bottom of
`schemas/news.sd`:

    rank-profile popularity inherits default {
        function popularity() {
            expression: if (attribute(impressions) > 0, attribute(clicks) / attribute(impressions), 0)
        }
        first-phase {
            expression: nativeRank(title, abstract) + 10 * popularity
        }
    }

- `rank-profile popularity inherits default`

  This configures Vespa to create a new rank profile named `popularity`,
  which inherits all the properties of the default rank-profile;
  only properties that are explicitly defined, or overridden, will differ
  from those of the default rank-profile.

- `first-phase`

  Relevance calculations in Vespa are two-phased. The calculations done in the
  first phase are performed on every single document matching your query,
  while the second phase calculations are only done on the top `n` documents
  as determined by the calculations done in the first phase.

- `function popularity()`

  This sets up a function that can be called from other expressions. This
  function calculates the number of clicks divided by impressions for indicating
  popularity. However, this isn't really the best way of calculating this as an
  article with a low number of impressions can score high on such a value, even
  though uncertainty is high.

- `expression: nativeRank + 100 * popularity`

  This expression is used to rank documents. Here, the default ranking
  expression — the `nativeRank` of the `default` fieldset — is included to
  make the query relevant, while the second term calls
  the `popularity` function. The weighted sum of these two terms is the 
  final relevance for each document. Note that the weight here, `100`, 
  is set by observation. A better approach would be to learn such values 
  using machine learning, which we'll get back to later in the tutorial.

More information can be found in the [schema
reference](../reference/schema-reference.html#rank-profile).

After you deploy the configuration, you can run a query such as:

<pre data-test="exec" data-test-assert-contains='"coverage": 100'>
$ curl -s -H "Content-Type: application/json" --data '{"yql" : "select * from sources * where default contains \"music\";", "ranking" : "popularity"}' \
http://localhost:8080/search/ | python -m json.tool
</pre>

and find documents with high `popularity` values at the top. Note that
we must specify the ranking profile to use with the `ranking` parameter.

## Conclusion

After completing this part of the tutorial, you should now have a basic
understanding of how you can load data into Vespa and effectively search for
content. In the [next part of the tutorial](news-4-embeddings.html), we'll
start with the basics for transforming this into a recommendation system.

<pre style="display:none" data-test="after">
$ docker rm -f vespa
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