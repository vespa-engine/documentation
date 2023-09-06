---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Use Case - shopping"
redirect_from:
- /documentation/use-case-shopping.html
---

The [e-commerce, or shopping, use case](https://github.com/vespa-engine/sample-apps/tree/master/use-case-shopping)
is an example of an e-commerce site complete with sample data and a web front
end to browse product data and reviews. To quick start the application, follow
the instructions in the
[README](https://github.com/vespa-engine/sample-apps/blob/master/use-case-shopping/README.md)
in the sample app.

<img src="/assets/img/shopping-1.png" alt="Shopping sample app screenshot" width="700" height="auto"/>

To browse the application, navigate to
<a href="http://localhost:8080/site" data-proofer-ignore>localhost:8080/site</a>.
This site is implemented through a custom [request handler](jdisc/developing-request-handlers.html)
and is meant to be a simple example of creating a front end / middleware that
sits in front of the Vespa back end. As such it is fairly independent of Vespa
features, and the code is designed to be fairly easy to follow and as
non-magical as possible. All the queries against Vespa are sent as HTTP
requests, and the JSON results from Vespa are parsed and rendered.

This sample application is built around the Amazon product data set found at
[https://cseweb.ucsd.edu/~jmcauley/datasets.html](https://cseweb.ucsd.edu/~jmcauley/datasets.html).
A small sample of this data is included in the sample application, and full
data sets are available from the above site. This sample application contains
scripts to convert from the data set format to Vespa format:
[convert_meta.py](https://github.com/vespa-engine/sample-apps/blob/master/use-case-shopping/convert_meta.py) and
[convert_reviews.py](https://github.com/vespa-engine/sample-apps/blob/master/use-case-shopping/convert_reviews.py).
See [README](https://github.com/vespa-engine/sample-apps/tree/master/use-case-shopping#readme) for example use.

When feeding reviews, there is a custom [document processor](document-processing.html)
that intercepts document writes and updates the parent item with the review rating,
so the aggregated review rating is kept stored with the item -
see [ReviewProcessor](https://github.com/vespa-engine/sample-apps/blob/master/use-case-shopping/src/main/java/ai/vespa/example/shopping/ReviewProcessor.java).
This is more an example of a custom document processor than a recommended way to do this,
as feeding the reviews more than once will result in inflated values.
To do this correctly, one should probably calculate this offline so a re-feed does not cause unexpected results.



### Highlighted features

* [Multiple document types](schemas.html)

    Vespa models data as documents, which are configured in schemas
    that defines how documents should be stored, indexed, ranked, and searched.
    In Vespa, you can have multiple documents types, which can be defined in
    `services.xml` how these should be distributed around the content clusters.
    This application uses three document types that are stored in the same
    content cluster: item, review and query. Search is done on items, but reviews
    refer to a single parent item and are rendered on the item page. The query
    document type is used to power auto-suggest functionality.

* [Custom document processor](document-processing.html)

    In Vespa, you can set up custom document processors to perform any type of
    extra processing during document feeding. One example is to enrich the
    document with extra information, and another is to precalculate values of
    fields to avoid unnecessary computation during ranking. This application
    uses a document processor to intercept reviews and update the parent item's
    review rating.

* [Custom searcher processor](searcher-development.html)

    In Vespa, you can set up custom searchers to perform any type of
    extra processing during querying.
    In the sample app there is a single custom searcher which builds the query for auto-suggestions,
    using a combination of [fuzzy matching](reference/query-language-reference.html#fuzzy)
    and [prefix search](text-matching.html#prefix-match).

* [Custom handlers](jdisc/developing-request-handlers.html)

    With Vespa, you can set up general request handlers to handle any type of request.
    This example site is implemented with a single such request handler,
    [SiteHandler](https://github.com/vespa-engine/sample-apps/blob/master/use-case-shopping/src/main/java/ai/vespa/example/shopping/site/SiteHandler.java)
    which is set up in
    [services.xml](https://github.com/vespa-engine/sample-apps/blob/master/use-case-shopping/src/main/application/services.xml)
    to be bound to `/site`.
    Note that this handler is for example purposes and is designed to be independent of Vespa.
    Most applications would serve this through a dedicated setup.

* [Custom configuration](configuring-components.html)

    When creating custom components in Vespa, for instance document processors,
    searchers or handlers, one can use custom configuration to inject config
    parameters into the components. This involves defining a config definition
    (a `.def` file), which creates a config class. You can instantiate this
    class with data in `services.xml` and the resulting object is dependency
    injected to the component during construction. This application uses custom
    config to set up the Vespa host details for the handler.

* [Partial update](reference/document-json-format.html#update)

    With Vespa, you can make changes to an existing document without submitting
    the full document. Examples are setting the value of a single field, adding
    elements to an array, or incrementing the value of a field without knowing
    the field value beforehand. This application contains an example of a
    partial update, in the voting of whether a review is helpful or not.  The
    `SiteHandler` receives the request and the `ReviewVote` class sends a
    partial update to increment the `up`- or `downvotes` field.

* [Search using YQL](query-language.html)

    In Vespa, you search for documents using YQL. In this application, the
    classes responsible for retrieving data from Vespa (in the `data` package
    beneath the `SiteHandler`) set up the YQL queries which are used to query
    Vespa over HTTP.

* [Grouping](grouping.html)

    Grouping is used to group various fields of query results together.  For
    this application, many of the queries to Vespa include grouping requests.
    The home page uses grouping to dynamically extract the first 3 levels of
    categories from the stored items. The search page groups results matching
    the query into categories, brands, item rating and price ranges. The order
    which the groups are rendered are determined by both counting and the
    relevance of the hits. This enables query-contextualized navigation. 

* [Rank profiles](ranking.html)

    Rank profiles are profiles containing instructions on how to score
    documents for a given query. The most important part of rank profiles are
    the ranking expressions. The schemas for the item and review
    document types contain different rank profiles to sort or score the
    data. The item ranking is using a hybrid combination of keyword and vector matching.

* [Native embedders](embedding.html)

    Native embedders are used to map the textual query and document representations 
    into dense high dimensional vectors which are used for semantic search. The application
    uses an open-source embedding model and inference is performed using 
    [stateless model evaluation](stateless-model-evaluation.html), both during
    document and query processing. 

* [Vector search](nearest-neighbor-search.html)

    The default retrieval uses approximate nearest neighbor search in combination with traditional
    lexical matching. Both the keyword and vector matching is constrained by the filters such as brand, price or
    category. 

* [Ranking functions](reference/schema-reference.html#function-rank)

    Ranking functions are contained in rank profiles and can be referenced
    as part of any ranking expression from either first-phase, second-phase, global-phase or
    other functions.
