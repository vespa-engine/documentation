---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: FAQ - frequently asked questions
style: faq
redirect_from:
- /documentation/faq.html
---

Refer to [Vespa Support](https://vespa.ai/support) for more support options.

<style>
  ul.toc-list {
    list-style-type: none;
    padding-inline-start: 0;
  }

  ul.toc-list > li {
    margin-bottom: 15px;
    font-weight: bold;
  }

  [id^=toc-] {
    min-width: 400px;
  }
</style>

<!-- ToDo: script FAQ TOC once final design is settled -->
<div class="row">
  <div class="col-6-12">
    <div id="toc-0" class="box m-10 p-10">
    </div>
  </div>
  <div class="col-6-12">
    <div id="toc-1" class="box m-10 p-10">
    </div>
  </div>
</div>

<div class="row">
  <div class="col-6-12">
    <div id="toc-2" class="box m-10 p-10">
    </div>
  </div>
  <div class="col-6-12">
    <div id="toc-3" class="box m-10 p-10">
    </div>
  </div>
</div>

<div class="row">
  <div class="col-6-12">
    <div id="toc-4" class="box m-10 p-10">
    </div>
  </div>
  <div class="col-6-12">
    <div id="toc-5" class="box m-10 p-10">
    </div>
  </div>
</div>

<div class="row">
  <div class="col-6-12">
    <div id="toc-6" class="box m-10 p-10">
    </div>
  </div>
  <div class="col-6-12">
    <div id="toc-7" class="box m-10 p-10">
    </div>
  </div>
</div>

---



{:.faq-section}
### Ranking

#### Does Vespa support a flexible ranking score?
[Ranking](ranking.html) is maybe the primary Vespa feature -
we like to think of it as scalable, online computation.
A rank profile is where the application's logic is implemented,
supporting simple types like `double` and complex types like `tensor`.
Supply ranking data in queries in query features (e.g. different weights per customer),
or look up in a [Searcher](searcher-development.html).
Typically, a document (e.g. product) "feature vector"/"weights" will be compared to a user-specific vector (tensor).

#### Where would customer specific weightings be stored?
Vespa doesn't have specific support for storing customer data as such.
You can store this data as a separate document type in Vespa and look it up before passing the query,
or store this customer meta-data as part of the other meta-data for the customer
(i.e. login information) and pass it along the query when you send it to the backend.
Find an example on how to look up data in
[album-recommendation-docproc](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing).

#### How to create a tensor on the fly in the ranking expression?
Create a tensor in the ranking function from arrays or weighted sets using `tensorFrom...` functions -
see [document features](reference/rank-features.html#document-features).

#### How to set a dynamic (query time) ranking drop threshold?
Pass a ranking feature like `query(threshold)` and use an `if` statement in the ranking expression -
see [retrieval and ranking](getting-started-ranking.html#retrieval-and-ranking). Example:
<pre>
rank-profile drop-low-score {
   function my_score() {
     expression: ..... #custom first phase score
   }
   rank-score-drop-limit:0.0
   first-phase {
     if(my_score() < query(threshold), -1, my_score())
   }
}
</pre>

#### Does Vespa support early termination of matching and ranking?
Yes, this can be accomplished by configuring [match-phase](reference/schema-reference.html#match-phase) in the ranking profile,  or by adding a range query item using *hitLimit* to the query tree, 
see [capped numeric range search](reference/query-language-reference.html#numeric).  
Both methods require an *attribute* field with *fast-search*. The capped range query is faster but beware that if there are other restrictive filters in the query one might end up with 0 hits. 
The additional filters are applied as a post filtering 
step over the hits from the capped range query. *match-phase* on the other hand is safe to use with filters or other query terms, and also supports diversification which the capped range query term 
does not support.  



{:.faq-section}
### Documents

#### What limits apply to json document size?
There is no hard limit.
Vespa requires a document to be able to load into memory in serialized form.
Vespa is not optimized for huge documents.

#### Can a document have lists (key value pairs)?
E.g. a product is offered in a list of stores with a quantity per store.
Use [multivalue fields](schemas.html#field) (array of struct) or [parent child](parent-child.html).
Which one to chose depends on use case, see discussion in the latter link.

#### Does a whole document need to be updated and re-indexed?
E.g. price and quantity available per store may often change vs the actual product attributes.
Vespa supports [partial updates](reads-and-writes.html) of documents.
Also, the parent/child feature is implemented to support use-cases where child elements are updated frequently,
while a more limited set of parent elements are updated less frequently.

#### What ACID guarantees if any does Vespa provide for single writes / updates / deletes vs batch operations etc?
See the [Vespa Consistency Model](content/consistency.html).
Vespa is not transactional in the traditional sense, it doesn't have strict ACID guarantees.
Vespa is designed for high performance use-cases with eventual consistency
as an acceptable (and to some extent configurable) trade-off.

#### Does vespa support wildcard fields? 
Wildcard fields are not supported in vespa.
Workaround would be to use maps to store the wildcard fields.
Map needs to be defined with indexing attribute and hence will be stored in memory.
Refer to [map](reference/schema-reference.html#type:map).

#### Is there any size limitation in multivalued fields?
No limit, except memory.

#### Can we set a limit for the number of elements that can be stored in an array?
Implement a [document processor](document-processing.html) for this.

#### How to auto-expire documents / set up garbage collection?
Set a selection criterion on the `document` element in `services.xml`.
The criterion selects documents <span style="text-decoration: underline">to keep</span>.
I.e. to purge documents "older than two weeks", the expression should be "newer than two weeks".
Read more about [document expiry](documents.html#document-expiry).



{:.faq-section}
### Query

#### Is hierarchical facets supported?
Facets is called <a href="grouping.html">grouping</a> in Vespa.
Groups can be multi-level.

#### Is filters supported?
Add filters to the query using [YQL](query-language.html)
using boolean, numeric and [text matching](text-matching-ranking.html).

#### How to query for similar items?
One way is to describe items using tensors and query for the
[nearest neighbor](reference/query-language-reference.html#nearestneighbor) -
using full precision or approximate (ANN) - the latter is used when the set is too large for an exact calculation.
Apply filters to the query to limit the neighbor candidate set.
Using [dot products](multivalue-query-operators.html) or [weak and](using-wand-with-vespa.html) are alternatives.

#### Stop-word support?
Vespa does not have a stop-word concept inherently.
See the [sample app](https://github.com/vespa-engine/sample-apps/pull/335/files)
for how to use [filter terms](reference/query-language-reference.html#annotations).

#### How to extract more than 400 hits / query and get ALL documents?
Trying to request more than 400 hits in a query, getting this error:
`{'code': 3, 'summary': 'Illegal query', 'message': '401 hits requested, configured limit: 400.'}`.

* To increase max result set size,
  configure `maxHits` in a [query profile](reference/query-api-reference.html#queryProfile),
  e.g. `<field name="maxHits">500</field>` in `search/query-profiles/default.xml` (create as needed).
  Query timeout can be increased, but it will still be costly and likely impact other queries -
  large limit more so than a large offset.
  It can be made cheaper by using a smaller [document summary](document-summaries.html),
  and avoiding fields on disk if possible.
* Using _visit_ in the [document/v1/ API](document-v1-api-guide.html)
  is usually a better option for dumping all the data.

#### How to make a sub-query to get data to enrich the query, like get a user profile?
See the [UserProfileSearcher](https://github.com/vespa-engine/sample-apps/blob/master/news/app-6-recommendation-with-searchers/src/main/java/ai/vespa/example/UserProfileSearcher.java)
for how to create a new query to fetch data -
this creates a new Query, sets a new root and parameters - then `fill`s the Hits.

#### How to create a cache that refreshes itself regularly
<!-- ToDo: Maybe a bit long for the FAQ and such a component could be added to a sample app instead later -->
See the sub-query question above, in addition add something like:
```java
public class ConfigCacheRefresher extends AbstractComponent {
...
    private final ScheduledExecutorService configFetchService = Executors.newSingleThreadScheduledExecutor();
    private Chain<Searcher> searcherChain;
...
    void initialize() {
        Runnable task = () -> refreshCache();
        configFetchService.scheduleWithFixedDelay(task, 1, 1, TimeUnit.MINUTES);
        searcherChain = executionFactory.searchChainRegistry().getChain(new ComponentId("configDefaultProvider"));
    }
...
    public void refreshCache() {
        Execution execution = executionFactory.newExecution(searcherChain);
        Query query = createQuery(execution);
...
    public void deconstruct() {
        super.deconstruct();
        try {
            configFetchService.shutdown();
            configFetchService.awaitTermination(1, TimeUnit.MINUTES);
...
}
```

#### Is it possible to query Vespa using a list of document ids?
The best article on the subject is
[multi-lookup set filtering](https://docs.vespa.ai/en/performance/feature-tuning.html#multi-lookup-set-filtering).
Refer to the [weightedset-example](multivalue-query-operators.html#weightedset-example) -
also see [weightedset](reference/query-language-reference.html#weightedset)
for writing a YQL query to select multiple IDs.
The ID must be a field in the document type.

#### How to count hits / all documents without returning results?
Count all documents using a query like [select * from doc where true](query-language.html) -
this counts all documents from the "doc" source.
Using `select * from doc where true limit 0` will return the count and no hits,
alternatively add [hits=0](reference/query-api-reference.html#hits).
Pass [ranking.profile=unranked](reference/query-api-reference.html#ranking.profile)
to make the query less expensive to run.
If an _estimate_ is good enough, use [hitcountestimate=true](reference/query-api-reference.html#hitcountestimate).



{:.faq-section}
### Feeding

#### How to debug document processing chain configuration?
This configuration is a combination of content and container cluster configuration,
see [indexing](indexing.html) and [feed troubleshooting](operations/admin-procedures.html#troubleshooting).

#### I feed documents with no error, but they are not in the index
This is often a problem if using [document expiry](documents.html#document-expiry),
as documents already expired will not be persisted, they are silently dropped.
Feeding stale test data with old timestamps can cause this.



{:.faq-section}
### Text Search

#### Does Vespa support addition of flexible NLP processing for documents and search queries?
E.g. integrating NER, word sense disambiguation, specific intent detection.
Vespa supports these things well:
- [Query (and result) processing](searcher-development.html)
- [Document processing](document-processing.html)
  and [annotations](annotations.html) on document processors working on semantic annotations of text

#### Does Vespa support customization of the inverted index?
E.g. instead of using terms or n-grams as the unit, we might use terms with specific word senses -
e.g. bark (dog bark) vs. bark (tree bark), or BCG (company) vs. BCG (vaccine name).
Creating a new index <em>format</em> means changing the core.
However, for the examples above, one just need control over the tokens which are indexed (and queried).
That is easily done in some Java code.
The simplest way to do this is to plug in a [custom tokenizer](linguistics.html).
That gets called from the query parser and bundled linguistics processing [Searchers](searcher-development.html)
as well as the [Document Processor](document-processing.html)
creating the annotations that are consumed by the indexing operation.
Since all that is Searchers and Docprocs which you can replace and/or add custom components before and after,
you can also take full control over these things without modifying the platform itself.

#### Does vespa provide any support for named entity extraction?
It provides the building blocks but not an out-of-the-box solution.
We can write a [Searcher](searcher-development.html) to detect query-side entities and rewrite the query, 
and a [DocProc](document-processing.html) if we want to handle them in some special way on the indexing side.

#### Does vespa provide support for text extraction?
You can write a document processor for text extraction, Vespa does not provide it out of the box.



{:.faq-section}
### Programming Vespa

#### Is Python plugins supported / is there a scripting language?
Plugins have to run in the JVM - [jython](https://www.jython.org/) might be an alternative,
however Vespa Team has no experience with it.
Vespa does not have a language like
[painless](https://www.elastic.co/guide/en/elasticsearch/reference/master/modules-scripting-painless.html) -
it is more flexible to write application logic in a JVM-supported language, using
[Searchers](searcher-development.html) and [Document Processors](document-processing.html).

<!-- How to add custom code to a Vespa application? -->

<!--p id="programming-vespa-3" style="margin-bottom: 0px;"><strong>Is there a way to check if this component is alive or not?
<a href="jdisc/container-components.html">Component</a> lifecycle:
<ol>
  <li>Old components are alive</li>
  <li>Deployment occurs</li>
  <li>New components are constructed</li>
  <li>Old components are deconstructed</li>
  <li>Deployment is complete</li>
  <li>Only new components are alive</li>
</ol-->
<!-- ToDo: move this to the doc itself and link from here - and add something useful ... -->



{:.faq-section}
### Performance

#### What is the latency of documents being ingested vs indexed and available for search?
Vespa has a near real-time indexing core with typically sub-second latencies from document ingestion to being indexed.
This depends on the use-case, available resources and how the system is tuned.
Some more examples and thoughts can be found in the [scaling guide](performance/sizing-search.html).

#### Is there a batch ingestion mode, what limits apply?
Vespa does not have a concept of "batch ingestion"
as it contradicts many of the core features that are the strengths of Vespa,
including [serving elasticity](elasticity.html) and sub-second indexing latency.
That said, we have numerous use-cases in production
that do high throughput updates to large parts of the (sometimes entire) document set.
In cases where feed throughput is more important than indexing latency, you can tune this to meet your requirements.
Some of this is detailed in the [feed sizing guide](performance/sizing-feeding.html).

#### Can the index support up to 512 GB index size in memory?
Yes. The [content node](proton.html) is implemented in C++
and not memory constrained other than what the operating system does.

#### Get request for a document when document is not in sync in all the replica nodes? 
If the replicas are in sync the request is only sent to the primary content node.
Otherwise, it's sent to several nodes, depending on replica metadata.
Example: if a bucket has 3 replicas A, B, C and A & B both have metadata state X and C has metadata state Y,
a request will be sent to A and C
(but not B since it has the same state as A and would therefore not return a potentially different document).

<!--How to optimise feeding from a Grid? -->



{:.faq-section}
### Administration

#### Can one do a partial deploy to the config server / update the schema without deploying all the node configs?
Yes, deployment is using this web service API,
which allows you to create an edit session from the currently deployed package,
make modifications, and deploy (prepare+activate) it: [deploy-rest-api-v2.html](cloudconfig/deploy-rest-api-v2.html).
However, this is only useful in cases where you want to avoid transferring data to the config server unnecessarily.
When you resend everything, the config server will notice that you did not actually change e.g. the node configs
and avoid unnecessary noop changes.

#### Deployment fails / nothing is listening on 19071
Make sure all [Config servers](operations/configuration-server.html#troubleshooting) are started,
and are able to establish ZooKeeper quorum (if more than one) -
see the [multinode](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode) sample application.
Validate that the container has [enough memory](operations/docker-containers.html).

#### Startup problems in multinode Kubernetes cluster - readinessProbe using 19071 fails
The Config Server cluster with 3 nodes fails to start.
The ZooKeeper cluster the Config Servers use waits for hosts on the network,
the hosts wait for ZooKeeper in a catch 22 -
see [sampleapp troubleshooting](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations#troubleshooting).

#### Starting Vespa using Docker on M1 fails
Using an M1 MacBook Pro / AArch64 makes the Docker run fail:
```
WARNING: The requested image’s platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
and no specific platform was requested
```
Refer to [sampleapp troubleshooting](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations#troubleshooting).

#### How fast can nodes be added and removed from a running cluster?
[Elasticity](elasticity.html) is a core Vespa strength -
easily add and remove nodes with minimal (if any) serving impact.
The exact time needed depends on how much data will need to be migrated in the background
for the system to converge to [ideal data distribution](content/idealstate.html).

#### Should Vespa API search calls be load balanced or does Vespa do this automatically?
You will need to load balance incoming requests between the nodes running the
[stateless Java container cluster(s)](overview.html).
This can typically be done using a simple network load balancer available in most cloud services.
This is included when using [Vespa Cloud](https://cloud.vespa.ai/),
with an HTTPS endpoint that is already load balanced - both locally within the region and globally across regions.

#### Supporting index partitions
[Search sizing](performance/sizing-search.html) is the intro to this.
Topology matters, and this is much used in the high-volume Vespa applications to optimise latency vs. cost.

#### Can a running cluster be upgraded with zero downtime?
With [Vespa Cloud](https://cloud.vespa.ai/),
we do automated background upgrades daily without noticeable serving impact.
If you host Vespa yourself, you can do this, but need to implement the orchestration logic necessary to handle this.
The high level procedure is found in [live-upgrade](operations/live-upgrade.html).

#### Can Vespa be deployed multi-region?
[Vespa Cloud](https://cloud.vespa.ai/en/reference/zones) has integrated support - query a global endpoint.
Writes will have to go to each zone. There is no auto-sync between zones.

#### Can Vespa serve an Offline index?
Building indexes offline requires the partition layout to be known in the offline system,
which is in conflict with elasticity and auto-recovery
(where nodes can come and go without service impact).
It is also at odds with realtime writes.
For these reasons, it is not recommended, and not supported.

#### Does vespa give us any tool to browse the index and attribute data?
No. Use [visiting](content/visiting.html) to dump all or a subset of documents.
See [dumping-data](https://cloud.vespa.ai/en/dumping-data) for a sample script.

#### What is the response when data is written only on some nodes and not on all replica nodes (Based on the redundancy count of the content cluster)? 
Failure response will be given in case the document is not written on some replica nodes.

#### When the doc is not written to some nodes, will the document become available due to replica reconciliation?
Yes, it will be available, eventually.
Also try [Multinode testing and observability](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode).

#### Does vespa provide soft delete functionality?
Yes just add a `deleted` attribute, add [fast-search](attributes.html#fast-search) on it
and create a searcher which adds an `andnot deleted` item to queries.

#### Can we configure a grace period for bucket distribution so that buckets are not redistributed as soon as a node goes down? 
You can set a [transition-time](reference/services-content.html#transition-time) in services.xml
to configure the cluster controller how long a node is to be kept in maintenance mode
before being automatically marked down.

#### What is the recommended redundant/searchable-copies config when using grouping distribution?
Grouped distribution is used to reduce search latency.
Content is distributed to a configured set of groups,
such that the entire document collection is contained in each group.
Setting the redundancy and searchable-copies equal to the number of groups
ensures that data can be queried from all groups.

#### How to set up for disaster recovery / backup?
Refer to [#17898](https://github.com/vespa-engine/vespa/issues/17898) for a discussion of options.


<script type="application/javascript">
  function createTOC() {
    let i = 0;
    for (const h3Item of document.querySelectorAll("H3")) {
      writeCategory("toc-"+i++, h3Item);
    }
  }

  function writeCategory(tocId, h3) {
    let header = document.createElement("H3");
    header.innerText = h3.innerText;
    let category = document.getElementById(tocId);
    category.appendChild(header);
    let questions = document.createElement("UL");
    questions.classList.add("toc-list");
    let elem = h3;
    while (elem = elem.nextSibling) {
      if (elem.nodeName === "H3") break;
      if (elem.nodeName === "H4") {
        let question = document.createElement("LI");
        let a = document.createElement("A");
        a.href = "#" + elem.id;
        a.innerText = elem.innerText;
        question.appendChild(a);
        questions.appendChild(question);
      }
    }
    category.appendChild(questions);
  }

  document.addEventListener("DOMContentLoaded", createTOC);
</script>
