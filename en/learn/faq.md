---
# Copyright Vespa.ai. All rights reserved.
title: FAQ - frequently asked questions
redirect_from:
  - /en/faq
---
Refer to [Vespa Support](https://vespa.ai/support) for more support options.

<style>
.subpage h2 {
    margin-top: 90px;
}
.subpage h3 {
    margin-top: 60px;
}
</style>



{:.faq-section}
## Ranking

### Does Vespa support a flexible ranking score?
[Ranking](../basics/ranking.html) is maybe the primary Vespa feature -
we like to think of it as scalable, online computation.
A rank profile is where the application's logic is implemented,
supporting simple types like `double` and complex types like `tensor`.
Supply ranking data in queries in query features (e.g. different weights per customer),
or look up in a [Searcher](../applications/searchers.html).
Typically, a document (e.g. product) "feature vector"/"weights" will be compared to a user-specific vector (tensor).

### Where would customer specific weightings be stored?
Vespa doesn't have specific support for storing customer data as such.
You can store this data as a separate document type in Vespa and look it up before passing the query,
or store this customer meta-data as part of the other meta-data for the customer
(i.e. login information) and pass it along the query when you send it to the backend.
Find an example on how to look up data in
[album-recommendation-docproc](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing).

### How to create a tensor on the fly in the ranking expression?
Create a tensor in the ranking function from arrays or weighted sets using `tensorFrom...` functions -
see [document features](../reference/rank-features.html#document-features).

### How to set a dynamic (query time) ranking drop threshold?
Pass a ranking feature like `query(threshold)` and use an `if` statement in the ranking expression -
see [retrieval and ranking](../ranking/ranking-intro#retrieval-and-ranking). Example:
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

### Are ranking expressions or functions evaluated lazily?
<p>Rank expressions are not evaluated lazily.  No, this would require lambda arguments.
  Only doubles and tensors are passed between functions.

   Example:</p>
<pre>
function inline foo(tensor, defaultVal) {
    expression: if (count(tensor) == 0, defaultValue, sum(tensor))
}

function bar() {
    expression: foo(tensor, sum(tensor1 * tensor2))
}
</pre>

### Does Vespa support early termination of matching and ranking?
Yes, this can be accomplished by configuring [match-phase](../reference/schema-reference.html#match-phase) 
in the rank profile,  or by adding a range query item using *hitLimit* to the query tree,
see [capped numeric range search](../reference/query-language-reference.html#numeric).
Both methods require an *attribute* field with *fast-search*. The capped range query is faster, but beware that if 
there are other restrictive filters in the query, one might end up with 0 hits.
The additional filters are applied as a post filtering
step over the hits from the capped range query. *match-phase* on the other hand, is safe to use with filters or other query terms,
and also supports diversification which the capped range query term does not support.

### What could cause the relevance field to be -Infinity
The returned [relevance](../reference/default-result-format.html#relevance) for a hit can become "-Infinity" instead
of a double. This can happen in two cases:

- The [ranking](../basics/ranking.html) expression used a feature which became `NaN` (Not a Number). For example, `log(0)` would produce
-Infinity. One can use [isNan](../reference/ranking-expressions.html#isnan-x) to guard against this.
- Surfacing low scoring hits using [grouping](../querying/grouping.html), that is, rendering low ranking hits with `each(output(summary()))` that are outside of what Vespa computed and caches on a heap. This is controlled by the [keep-rank-count](../reference/schema-reference.html#keep-rank-count).

### How to pin query results?
To hard-code documents to positions in the result set,
see the [pin results example](../ranking/multivalue-query-operators.html#pin-results-example).


{:.faq-section}
## Documents

### What limits apply to document size?
There is a [maximum document size](../reference/services/content.html#max-document-size) of 128 MiB,
which is configurable per content cluster in services.xml.

### Is there any size limitation for multivalued fields?
No enforced limit, except resource usage (memory).

### Can a document have lists (key value pairs)?
E.g. a product is offered in a list of stores with a quantity per store.
Use [multivalue fields](../searching-multi-valued-fields.html) (array of struct) or [parent child](../schemas/parent-child.html).
Which one to chose depends on use case, see discussion in the latter link.

### Does a whole document need to be updated and re-indexed?
E.g. price and quantity available per store may often change vs the actual product attributes.
Vespa supports [partial updates](../writing/reads-and-writes.html) of documents.
Also, the parent/child feature is implemented to support use-cases where child elements are updated frequently,
while a more limited set of parent elements are updated less frequently.

### What ACID guarantees if any does Vespa provide for single writes / updates / deletes vs batch operations etc?
See the [Vespa Consistency Model](../content/consistency).
Vespa is not transactional in the traditional sense, it doesn't have strict ACID guarantees.
Vespa is designed for high performance use-cases with eventual consistency
as an acceptable (and to some extent configurable) trade-off.

### Does vespa support wildcard fields?
Wildcard fields are not supported in vespa.
Workaround would be to use maps to store the wildcard fields.
Map needs to be defined with <code>indexing: attribute</code> and hence will be stored in memory.
Refer to [map](../reference/schema-reference.html#map).

### Can we set a limit for the number of elements that can be stored in an array?
Implement a [document processor](../applications/document-processors.html) for this.

### How to auto-expire documents / set up garbage collection?
Set a selection criterion on the `document` element in `services.xml`.
The criterion selects documents <span style="text-decoration: underline">to keep</span>.
I.e. to purge documents "older than two weeks", the expression should be "newer than two weeks".
Read more about [document expiry](../schemas/documents.html#document-expiry).

### How to increase redundancy and track data migration progress?
Changing redundancy is a live and safe change
(assuming there is headroom on disk / memory - e.g. from 2 to 3 is 50% more).
The time to migrate will be quite similar to what it took to feed initially -
a bit hard to say generally, and depends on IO and index settings, like if building an HNSW index.
To monitor progress, take a look at the
[multinode](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode)
sample application for the _clustercontroller_ status page - this shows buckets pending, live.
Finally, use the `.idealstate.merge_bucket.pending` metric to track progress -
when 0, there are no more data syncing operations - see
[monitor distance to ideal state](../operations/self-managed/admin-procedures.html#monitor-distance-to-ideal-state).
Nodes will work as normal during data sync, and query coverage will be the same.

### How does namespace relate to schema?
It does not,
_namespace_ is a mechanism to split the document space into parts that can be used for document selection -
see [documentation](../schemas/documents.html#namespace). The namespace is not indexed and cannot
be searched using the query api, but can be used by [visiting](../writing/visiting.html).

### Visiting does not dump all documents, and/or hangs.
There are multiple things that can cause this, see [visiting troubleshooting](../writing/visiting.html#troubleshooting).

### How to find number of documents in the index?
Run a query like `vespa query "select * from sources * where true"` and see the `totalCount` field.
Alternatively, use metrics or `vespa visit` - see [examples](../writing/batch-delete.html#example).

### Can I define a default value for a field?

Not in the field definition, but it's possible to do this with the [choice](../writing/indexing.html#choice-example)
expression in an indexing statement.


{:.faq-section}
## Query

### Are hierarchical facets supported?
Facets is called <a href="../grouping.html">grouping</a> in Vespa.
Groups can be multi-level.

### Are filters supported?
Add filters to the query using [YQL](../querying/query-language.html)
using boolean, numeric and [text matching](../querying/text-matching.html). Query terms can be annotated
as filters, which means that they are not highlighted when bolding results.

### How to query for similar items?
One way is to describe items using tensors and query for the
[nearest neighbor](../reference/query-language-reference.html#nearestneighbor) -
using full precision or approximate (ANN) - the latter is used when the set is too large for an exact calculation.
Apply filters to the query to limit the neighbor candidate set.
Using [dot products](../ranking/multivalue-query-operators.html) or [weak and](../ranking/wand.html) are alternatives.

### Does Vespa support stop-word removal?
Vespa does not have a stop-word concept inherently.
See the [sample app](https://github.com/vespa-engine/sample-apps/pull/335/files)
for how to use [filter terms](../reference/query-language-reference.html#annotations).
[Tripling the query performance of lexical search](https://blog.vespa.ai/tripling-the-query-performance-of-lexical-search/)
it s good blog post on this subject.

### How to extract more than 400 hits / query and get ALL documents?
Trying to request more than 400 hits in a query, getting this error:
`{'code': 3, 'summary': 'Illegal query', 'message': '401 hits requested, configured limit: 400.'}`.

* To increase max result set size (i.e. allow a higher [hits](../reference/query-api-reference.html#hits)),
  configure `maxHits` in a [query profile](../reference/query-api-reference.html#queryprofile),
  e.g. `<field name="maxHits">500</field>` in `search/query-profiles/default.xml` (create as needed).
  The [query timeout](../reference/query-api-reference.html#timeout) can be increased,
  but it will still be costly and likely impact other queries -
  large limit more so than a large offset.
  It can be made cheaper by using a smaller [document summary](../querying/document-summaries.html),
  and avoiding fields on disk if possible.
* Using _visit_ in the [document/v1/ API](../writing/document-v1-api-guide.html)
  is usually a better option for dumping all the data.

### How to make a sub-query to get data to enrich the query, like get a user profile?
See the [UserProfileSearcher](https://github.com/vespa-engine/sample-apps/blob/master/news/app-6-recommendation-with-searchers/src/main/java/ai/vespa/example/UserProfileSearcher.java)
for how to create a new query to fetch data -
this creates a new Query, sets a new root and parameters - then `fill`s the Hits.

### How to create a cache that refreshes itself regularly
<!-- ToDo: Maybe a bit long for the FAQ and such a component could be added to a sample app instead later -->
See the sub-query question above, in addition add something like:
<pre>{% highlight java%}

public class ConfigCacheRefresher extends AbstractComponent {

    private final ScheduledExecutorService configFetchService = Executors.newSingleThreadScheduledExecutor();
    private Chain<Searcher> searcherChain;

    void initialize() {
        Runnable task = () -> refreshCache();
        configFetchService.scheduleWithFixedDelay(task, 1, 1, TimeUnit.MINUTES);
        searcherChain = executionFactory.searchChainRegistry().getChain(new ComponentId("configDefaultProvider"));
    }

    public void refreshCache() {
        Execution execution = executionFactory.newExecution(searcherChain);
        Query query = createQuery(execution);

    public void deconstruct() {
        super.deconstruct();
        try {
            configFetchService.shutdown();
            configFetchService.awaitTermination(1, TimeUnit.MINUTES);
        }catch(Exception e) {..}
    }
}
{% endhighlight %}</pre>

### Is it possible to query Vespa using a list of document ids?
Yes, using the [in query operator](../reference/query-language-reference.html#in). Example:
```
select * from data where user_id in (10, 20, 30)
```
The best article on the subject is
[multi-lookup set filtering](../performance/feature-tuning.html#multi-lookup-set-filtering).
Refer to the [in operator example](../ranking/multivalue-query-operators.html#in-example)
on how to use it programmatically in a [Java Searcher](../applications/searchers.html).

### How to query documents where one field matches any values in a list? Similar to using SQL IN operator
Use the [in query operator](../reference/query-language-reference.html#in). Example:
```
select * from data where category in ('cat1', 'cat2', 'cat3')
```
See [multi-lookup set filtering](#is-it-possible-to-query-vespa-using-a-list-of-document-ids)
above for more details.


### How to count hits / all documents without returning results?
Count all documents using a query like [select * from doc where true](../querying/query-language.html) -
this counts all documents from the "doc" source.
Using `select * from doc where true limit 0` will return the count and no hits,
alternatively add [hits=0](../reference/query-api-reference.html#hits).
Pass [ranking.profile=unranked](../reference/query-api-reference.html#ranking.profile)
to make the query less expensive to run.
If an _estimate_ is good enough, use [hitcountestimate=true](../reference/query-api-reference.html#hitcountestimate).

### Must all fields in a fieldset have compatible type and matching settings?
Yes - a deployment warning with _This may lead to recall and ranking issues_ is emitted
when fields with conflicting tokenization are put in the same
[fieldset](../reference/schema-reference.html#fieldset).
This is because a given query item searching one fieldset is tokenized just once,
so there's no right choice of tokenization in this case.
If you have user input that you want to apply to multiple fields with different tokenization,
include the userInput multiple times in the query:
```
select * from sources * where ({defaultIndex: 'fieldsetOrField1'}userInput(@query)) or ({defaultIndex: 'fieldsetOrField2'}userInput(@query))
```
More details on [stack overflow](https://stackoverflow.com/questions/72784136/why-vepsa-easily-warning-me-this-may-lead-to-recall-and-ranking-issues).

### How is the query timeout computed?
Find query timeout details in the [Query API Guide](../querying/query-api.html#timeout)
and the [Query API Reference](../reference/query-api-reference.html#timeout).

### How does backslash escapes work?
Backslash is used to escape special characters in YQL.
For example, to query with a literal backslash, which is useful in regexpes,
you need to escape it with another backslash: \\.
Unescaped backslashes in YQL will lead to "token recognition error at: '\'".

In addition, Vespa CLI unescapes double backslashes to single
(while single backslashes are left alone),
so if you query with Vespa CLI you need to escape with another backslash: \\\\.
The same applies to strings in Java.

Also note that both log messages and JSON results escape backslashes, so any \ becomes \\.

### Is it possible to have multiple SELECT statements in a single call (subqueries)?
E.g. two select queries with slightly different filtering condition and have a limit operator for each of the subquery.
This makes it impossible to do via OR conditions to select both collection of documents - something equivalent to:

    SELECT 1 AS x
    UNION ALL
    SELECT 2 AS y;

This isn’t possible, need to run 2 queries.
Alternatively, split a single incoming query into two running in parallel in a [Searcher](../applications/searchers.html) - example:
```java
FutureResult futureResult = new AsyncExecution(settings).search(query);
FutureResult otherFutureResult = new AsyncExecution(settings).search(otherQuery);
```
### Is it possible to query for the number of elements in an array
There is no index or attribute data structure that allows efficient _searching_ for documents where
an array field has a certain number of elements or items.
The _grouping language_ has a [size()](../reference/grouping-syntax.html#list-expressions) operator that can be used in queries.

### Is it possible to query for fields with NaN/no value set/null/none
The [visiting](../writing/visiting.html#analyzing-field-values) API using document selections supports it, with a linear scan over all documents.
If the field is an _attribute_ one can query using grouping to identify Nan Values,
see count and list [fields with NaN](../querying/grouping.html#count-fields-with-nan).

### How to retrieve random documents using YQL? Functionality similar to MySQL "ORDER BY rand()"
See the [random.match](../reference/rank-features.html#random.match) rank feature - example:
```
rank-profile random {
    first-phase {
        expression: random.match
    }
}
```
Run queries, seeding the random generator:
```
$ vespa query 'select * from music where true' \
  ranking=random \
  rankproperty.random.match.seed=2
```

### Some of the query results have too many hits from the same source, how to create a diverse result set?
See [result diversity](../querying/result-diversity) for strategies on how to create result sets from different sources.

### How to find most distant neighbor in a embedding field called clip_query_embedding?
If you want to search for the most dissimilar items,
you can with angular distance multiply your `clip_query_embedding` by the scalar -1.
Then you are searching for the points that are closest to the point
which is the farthest away from your `clip_query_embedding`.

Also see a [pyvespa example](https://pyvespa.readthedocs.io/en/latest/examples/pyvespa-examples.html#Neighbors).


{:.faq-section}
## Feeding

### How to debug a feeding 400 response?
The best option is to use `--verbose` option, like `vespa feed --verbose myfile.jsonl` -
see [documentation](../clients/vespa-cli.html#documents).
A common problem is a mismatch in schema names and [document IDs](../schemas/documents.html#document-ids) - a schema like:
```
schema article {
    document article {
        ...
    }
}
```
will have a document feed like:
```
{"put": "id:mynamespace:article::1234", "fields": { ... }}
```
Note that the [namespace](glossary.html#namespace) is not mentioned in the schema,
and the schema name is the same as the document name.

### How to debug document processing chain configuration?
This configuration is a combination of content and container cluster configuration,
see [indexing](../writing/indexing.html) and [feed troubleshooting](../operations/self-managed/admin-procedures.html#troubleshooting).

### I feed documents with no error, but they are not in the index
This is often a problem if using [document expiry](../schemas/documents.html#document-expiry),
as documents already expired will not be persisted, they are silently dropped and ignored.
Feeding stale test data with old timestamps in combination with document-expiry can cause this
behavior.

### How to feed many files, avoiding 429 error?
Using too many HTTP clients can generate a 429 response code.
The Vespa sample apps use [vespa feed](../clients/vespa-cli.html#documents) which uses HTTP/2 for high throughput -
it is better to stream the feed files through this client.

### Can I use Kafka to feed to Vespa?
Vespa does not have a Kafka connector.
Refer to third-party connectors like [kafka-connect-vespa](https://github.com/vinted/kafka-connect-vespa).



{:.faq-section}
## Text Search

### Does Vespa support addition of flexible NLP processing for documents and search queries?
E.g. integrating NER, word sense disambiguation, specific intent detection.
Vespa supports these things well:
- [Query (and result) processing](../applications/searchers.html)
- [Document processing](../applications/document-processors.html)
  and document processors working on semantic annotations of text

### Does Vespa support customization of the inverted index?
E.g. instead of using terms or n-grams as the unit, we might use terms with specific word senses -
e.g. bark (dog bark) vs. bark (tree bark), or BCG (company) vs. BCG (vaccine name).
Creating a new index <em>format</em> means changing the core.
However, for the examples above, one just need control over the tokens which are indexed (and queried).
That is easily done in some Java code.
The simplest way to do this is to plug in a [custom tokenizer](../linguistics/linguistics.html).
That gets called from the query parser and bundled linguistics processing [Searchers](../applications/searchers.html)
as well as the [Document Processor](../applications/document-processors.html)
creating the annotations that are consumed by the indexing operation.
Since all that is Searchers and Docprocs which you can replace and/or add custom components before and after,
you can also take full control over these things without modifying the platform itself.

### Does vespa provide any support for named entity extraction?
It provides the building blocks but not an out-of-the-box solution.
We can write a [Searcher](../applications/searchers.html) to detect query-side entities and rewrite the query,
and a [DocProc](../applications/document-processors.html) if we want to handle them in some special way on the indexing side.

### Does vespa provide support for text extraction?
You can write a document processor for text extraction, Vespa does not provide it out of the box.

### How to do Text Search in an imported field?
[Imported fields](../schemas/parent-child.html) from parent documents are defined as [attributes](../content/attributes.html),
and have limited text match modes (i.e. `indexing: index` cannot be used).
[Details](https://stackoverflow.com/questions/71936330/parent-child-mode-cannot-be-searched-by-parent-column).



{:.faq-section}
## Semantic search

### Why is closeness 1 for all my vectors?

If you have added vectors to your documents and queries, and see that the rank feature
closeness(field, yourEmbeddingField) produces 1.0 for all documents, you are likely using
[distance-metric](../reference/schema-reference.html#distance-metric): innerproduct/prenormalized-angular,
but your vectors are not normalized, and the solution is normally to switch to
[distance-metric: angular](../reference/schema-reference.html#angular)
or use
[distance-metric: dotproduct](../reference/schema-reference.html#dotproduct)
(available from {% include version.html version="8.170.18" %}).

With non-normalized vectors, you often get negative distances, and those are capped to 0,
leading to closeness 1.0.
Some embedding models, such as models from sbert.net, claim to output normalized vectors but might not.



{:.faq-section}
## Programming Vespa

### Is Python plugins supported / is there a scripting language?
Plugins have to run in the JVM - [jython](https://www.jython.org/) might be an alternative,
however Vespa Team has no experience with it.
Vespa does not have a language like
[painless](https://www.elastic.co/guide/en/elasticsearch/reference/current/modules-scripting-painless.html) -
it is more flexible to write application logic in a JVM-supported language, using
[Searchers](../applications/searchers.html) and [Document Processors](../applications/document-processors.html).

### How can I batch-get documents by ids in a Searcher
A [Searcher](../applications/searchers.html) intercepts a query and/or result.
To get a number of documents by id in a Searcher or other component like a [Document processor](../applications/document-processors.html),
you can have an instance of [com.yahoo.documentapi.DocumentAccess](../reference/component-reference.html#injectable-components)
injected and use that to get documents by id instead of the HTTP API.

<!-- How to add custom code to a Vespa application? -->

<!--p id="programming-vespa-3" style="margin-bottom: 0px;"><strong>Is there a way to check if this component is alive or not?
<a href="jdisc/components.html">Component</a> lifecycle:
<ol>
  <li>Old components are alive</li>
  <li>Deployment occurs</li>
  <li>New components are constructed</li>
  <li>Old components are deconstructed</li>
  <li>Deployment is complete</li>
  <li>Only new components are alive</li>
</ol-->
<!-- ToDo: move this to the doc itself and link from here - and add something useful ... -->

### Does Vespa work with Java 20?
Vespa uses Java 17 - it will support 20 some time in the future.

### How to write debug output from a custom component?
Use `System.out.println` to write text to the [vespa.log](../reference/logs.html).



{:.faq-section}
## Performance

### What is the latency of documents being ingested vs indexed and available for search?
Vespa has a near real-time indexing core with typically sub-second latencies from document ingestion to being indexed.
This depends on the use-case, available resources and how the system is tuned.
Some more examples and thoughts can be found in the [scaling guide](../performance/sizing-search.html).

### Is there a batch ingestion mode, what limits apply?
Vespa does not have a concept of "batch ingestion"
as it contradicts many of the core features that are the strengths of Vespa,
including [serving elasticity](../content/elasticity.html) and sub-second indexing latency.
That said, we have numerous use-cases in production
that do high throughput updates to large parts of the (sometimes entire) document set.
In cases where feed throughput is more important than indexing latency, you can tune this to meet your requirements.
Some of this is detailed in the [feed sizing guide](../performance/sizing-feeding.html).

### Can the index support up to 512 GB index size in memory?
Yes. The [content node](../content/proton.html) is implemented in C++
and not memory constrained other than what the operating system does.

### Get request for a document when document is not in sync in all the replica nodes?
If the replicas are in sync the request is only sent to the primary content node.
Otherwise, it's sent to several nodes, depending on replica metadata.
Example: if a bucket has 3 replicas A, B, C and A & B both have metadata state X and C has metadata state Y,
a request will be sent to A and C
(but not B since it has the same state as A and would therefore not return a potentially different document).

### How to keep indexes in memory?
[Attribute](../content/attributes.html) (with or without `fast-search`) is always in memory,
but does not support tokenized matching.
It is for structured data.
[Index](../basics/schemas.html#document-fields) (where there’s no such thing as fast-search since it is always fast)
is in memory to the extent there is available memory and supports tokenized matching.
It is for unstructured text.

It is possible to guarantee that fields that are defined with `index`
have both the dictionary and the postings in memory by changing from `mmap` to `populate`,
see [index > io > search](../reference/services/content.html#index-io-search).
Make sure that the content nodes run on nodes with plenty of memory available,
during index switch the memory footprint will 2x.
Familiarity with Linux tools like `pmap` can help diagnose what is mapped and if it’s resident or not.

Fields that are defined with `attribute` are in-memory,
fields that have both `index` and `attribute` have separate data structures,
queries will use the default mapped on disk data structures that supports `text` matching,
while grouping, summary and ranking can access the field from the `attribute` store.

A Vespa query is executed in two phases as described in [sizing search](../performance/sizing-search.html),
and summary requests can touch disk (and also uses `mmap` by default).
Due to their potential size there is no populate option here,
but one can define [dedicated document summary](../querying/document-summaries.html#performance)
containing only fields that are defined with `attribute`.

The [practical performance guide](../performance/practical-search-performance-guide)
can be a good starting point as well to understand Vespa query execution,
difference between `index` and `attribute` and summary fetching performance.

### Is memory freed when deleting documents?
Deleting documents, by using the [document API](../writing/reads-and-writes.html)
or [garbage collection](../schemas/documents.html#document-expiry) will increase the capacity on the content nodes.
However, this is not necessarily observable in system metrics -
this depends on many factors, like what kind of memory that is released,
when [flush](../content/proton.html#proton-maintenance-jobs) jobs are run and document [schema](../basics/schemas.html).

In short, Vespa is not designed to release memory once used.
It is designed for sustained high throughput, low latency,
keeping <span style="text-decoration: underline">maximum</span> memory used under control
using features like [feed block](../writing/feed-block.html).

When deleting documents, one can observe a slight <span style="text-decoration: underline">increase</span> in memory.
A deleted document is represented using a [tombstone](../operations/self-managed/admin-procedures.html#content-cluster-configuration),
that will later be removed, see [removed-db-prune-age](../reference/services/content.html#removed-db-prune-age).
When running garbage collection,
the summary store is scanned using mmap and both VIRT and page cache memory usage increases.

Read up on [attributes](../content/attributes.html) to understand more of how such fields are stored and managed.
[Paged attributes](../content/attributes.html#paged-attributes) trades off memory usage vs. query latency
for a lower max memory usage.

### What is the best practice for scaling Vespa for day vs night?
[Autoscaling](../operations/autoscaling.html) is the best guide to understand how to size and autoscale the system.
Container clusters are stateless and can be autoscaled more quickly than content clusters.

### We can spike 8x in 5 minutes in terms of throughput requirements.
It is not possible to autoscale content clusters for 8x load increase in 5 minutes,
as this requires both provisioning and data migration.
Such use cases are best discussed with the Vespa Team to understand the resource bottlenecks,
tradeoffs and mitigations.
Also read [Graceful Degradation](../performance/graceful-degradation.html).

### How much lower-level configuration do we need to do? For example, do we need to alter the number of threads per container?
It depends. Vespa aims to adapt to resources (like auto thread config based on virtual node thread count)
and actual use (when to run maintenance jobs like compaction),
but there are tradeoffs that applications owners can/should make.
Start off by reading the [Vespa Serving Scaling Guide](../performance/sizing-search.html),
then run [benchmarks](../performance/benchmarking-cloud.html) and use the [dashboards](../operations/monitoring.html).


{:.faq-section}
## Administration

### Self-managed: Can one do a partial deploy to the config server / update the schema without deploying all the node configs?
Yes, deployment is using this web service API,
which allows you to create an edit session from the currently deployed package,
make modifications, and deploy (prepare+activate) it: [deploy-rest-api-v2.html](../reference/deploy-rest-api-v2.html).
However, this is only useful in cases where you want to avoid transferring data to the config server unnecessarily.
When you resend everything, the config server will notice that you did not actually change e.g. the node configs
and avoid unnecessary noop changes.

### How fast can nodes be added and removed from a running cluster?
[Elasticity](../content/elasticity.html) is a core Vespa strength -
easily add and remove nodes with minimal (if any) serving impact.
The exact time needed depends on how much data will need to be migrated in the background
for the system to converge to [ideal data distribution](../content/idealstate.html).

### Should Vespa API search calls be load balanced or does Vespa do this automatically?
You will need to load balance incoming requests between the nodes running the
[stateless Java container cluster(s)](overview.html).
This can typically be done using a simple network load balancer available in most cloud services.
This is included when using [Vespa Cloud](https://cloud.vespa.ai/),
with an HTTPS endpoint that is already load balanced - both locally within the region and globally across regions.

### Supporting index partitions
[Search sizing](../performance/sizing-search.html) is the intro to this.
Topology matters, and this is much used in the high-volume Vespa applications to optimise latency vs. cost.

### Can a running cluster be upgraded with zero downtime?
With [Vespa Cloud](https://cloud.vespa.ai/),
we do automated background upgrades daily without noticeable serving impact.
If you host Vespa yourself, you can do this, but need to implement the orchestration logic necessary to handle this.
The high level procedure is found in [live-upgrade](../operations/self-managed/live-upgrade.html).

### Can Vespa be deployed multi-region?
[Vespa Cloud](https://cloud.vespa.ai/en/reference/zones) has integrated support - query a global endpoint.
Writes will have to go to each zone. There is no auto-sync between zones.

### Can Vespa serve an Offline index?
Building indexes offline requires the partition layout to be known in the offline system,
which is in conflict with elasticity and auto-recovery
(where nodes can come and go without service impact).
It is also at odds with realtime writes.
For these reasons, it is not recommended, and not supported.

### Does vespa give us any tool to browse the index and attribute data?
Use [visiting](../writing/visiting.html) to dump all or a subset of the documents.
See [data-management-and-backup](https://cloud.vespa.ai/en/data-management-and-backup) for more information.

### What is the response when data is written only on some nodes and not on all replica nodes (Based on the redundancy count of the content cluster)?
Failure response will be given in case the document is not written on some replica nodes.

### When the doc is not written to some nodes, will the document become available due to replica reconciliation?
Yes, it will be available, eventually.
Also try [Multinode testing and observability](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode).

### Does vespa provide soft delete functionality?
Yes just add a `deleted` attribute, add [fast-search](../content/attributes.html#fast-search) on it
and create a searcher which adds an `andnot deleted` item to queries.

### Can we configure a grace period for bucket distribution so that buckets are not redistributed as soon as a node goes down?
You can set a [transition-time](../reference/services/content.html#transition-time) in services.xml
to configure the cluster controller how long a node is to be kept in maintenance mode
before being automatically marked down.

### What is the recommended redundant/searchable-copies config when using grouping distribution?
Grouped distribution is used to reduce search latency.
Content is distributed to a configured set of groups,
such that the entire document collection is contained in each group.
Setting the redundancy and searchable-copies equal to the number of groups
ensures that data can be queried from all groups.

### How to set up for disaster recovery / backup?
Refer to [#17898](https://github.com/vespa-engine/vespa/issues/17898) for a discussion of options.

### Self-managed: How to check Vespa version for a running instance?
Use [/state/v1/version](../reference/state-v1.html#state-v1-version) to find Vespa version.

### Deploy rollback
See [rollback](../applications/deployment.html#rollback) for options.


{:.faq-section}
## Troubleshooting

### Deployment fails with response code 413
If deployment fails with error message "Deployment failed, code: 413 ("Payload Too Large.")"
you might need to increase the config server's JVM heap size. The config server has a default
JVM heap size of 2 Gb. When deploying an app with e.g. large models this might not be enough,
try increasing the heap to e.g. 4 Gb when executing 'docker run ...' by adding an environment
variable to the command line:

```
docker run --env VESPA_CONFIGSERVER_JVMARGS=-Xmx4g <other options> <image>
```

### The endpoint does not come up after deployment
When deploying an application package, with some kind of error, the endpoints might fail, like:
```
$ vespa deploy --wait 300

Uploading application package ... done

Success: Deployed target/application.zip

Waiting up to 5m0s for query service to become available ...
Error: service 'query' is unavailable: services have not converged
```
Another example:
```
[INFO]     [03:33:48]  Failed to get 100 consecutive OKs from endpoint ...
```
There are many ways this can fail, the first step is to check the Vespa Container:
```
$ docker exec vespa vespa-logfmt -l error

[2022-10-21 10:55:09.744] ERROR   container
Container.com.yahoo.container.jdisc.ConfiguredApplication
Reconfiguration failed, your application package must be fixed, unless this is a JNI reload issue:
Could not create a component with id 'ai.vespa.example.album.MetalSearcher'.
Tried to load class directly, since no bundle was found for spec: album-recommendation-java.
If a bundle with the same name is installed,
there is a either a version mismatch or the installed bundle's version contains a qualifier string.
...
```
[Bundle plugin troubleshooting](../applications/bundles.html#bundle-plugin-troubleshooting) is a good resource
to analyze Vespa container startup / bundle load problems.



### Starting Vespa using Docker on M1 fails
Using an M1 MacBook Pro / AArch64 makes the Docker run fail:
```
WARNING: The requested image’s platform (linux/amd64) does not match the detected host platform (linux/arm64/v8)
and no specific platform was requested
```
Make sure you are running a recent version of the Docker image, do `docker pull vespaengine/vespa`.
<!-- ToDo: remove this soon -->

### Deployment fails / nothing is listening on 19071
Make sure all [Config servers](../operations/self-managed/configuration-server.html#troubleshooting) are started,
and are able to establish ZooKeeper quorum (if more than one) -
see the [multinode](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode) sample application.
Validate that the container has [enough memory](../operations/self-managed/docker-containers.html).

### Startup problems in multinode Kubernetes cluster - readinessProbe using 19071 fails
The Config Server cluster with 3 nodes fails to start.
The ZooKeeper cluster the Config Servers use waits for hosts on the network,
the hosts wait for ZooKeeper in a catch 22 -
see [sampleapp troubleshooting](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations#troubleshooting).

### How to display vespa.log?
Use [vespa-logfmt](../reference/tools-self-managing.html#vespa-logfmt) to dump logs.
If Vespa is running in a local container (named "vespa"), run `docker exec vespa vespa-logfmt`.

### How to fix encoding problems in document text?
See [encoding troubleshooting](../linguistics/troubleshooting-encoding.html)
for how to handle and remove control characters from the document feed.



## Login, Tenants and Plans

### How to get started?
[Deploy an application](../basics/deploy-an-application.html) to create a tenant and start your 
[free trial](https://vespa.ai/free-trial).
This tenant can be your personal tenant, or shared with others.
It can not be renamed.

### How to create a company tenant?
If the tenant is already created, add more users to it.
Click the "account" button in the Vespa Cloud Console (top right in the tenant view), then "users".
From this view you can manage users in the tenant, and their roles -
from here, you can add/set tenant admins.

### How to accept Terms of Service?
When starting the free trial, you are asked to accept Terms of Service.
For paid plans, this is covered by the contract.

### How do I switch from free trial to a paid plan?
Click "account", then "billing" in the console to enter information required for billing.
Use [Vespa Support](https://vespa.ai/support/) if you need to provide this information without console login.

### Does Vespa Cloud support Single Sign-On (SSO)?
Yes, contact [Vespa Support](https://vespa.ai/support/) to set it up.



## Vespa Cloud Operations

### How can I change the cost of my Vespa Cloud usage?
See [node resources](../performance/node-resources) to assess current and auto-suggested resources
and [autoscaling](../operations/autoscaling.html) for how to automate.

### How can I manually modify resources used?
Managing resources is easy, as most changes are automated.
Adding / removing / changing nodes starts automated data migration,
see [elasticity](../content/elasticity.html).

### How to modify a schema?
Schema changes might require data reindexing, which is automated, but takes some time.
Other schema changes require data refeed - [details](../reference/schema-reference.html#modifying-schemas)
<!-- ToDo: we should really have a "managing resources" guide for Vespa Cloud -->

### How to evaluate how much memory a field is using?
Use the [Memory Visualizer](../performance/memory-visualizer.html) to evaluate how memory is allocated to the fields.
Fields can be `index`, `attribute` and `summary`, and combinations of these,
with settings like `fast-search` that affects memory usage.
[Attributes](../content/attributes.html) is a great read for understanding Vespa memory usage.

### Archive access failed with Permission 'serviceusage.services.use' denied
Listing archived objects can fail,
e.g. `gsutil -u my_project ls gs://vespa-cloud-data-prod-gcp-us-central1-f-12345f/my_tenant` can fail with
`AccessDeniedException: 403 me@mymail.com does not have serviceusage.services.use access to the Google Cloud project.
Permission \'serviceusage.services.use\' denied on resource (or it may not exist).`
This can be due to missing rights on your Google project (my_project in the example above)
\- from the Google documentation:
_"The user account accessing the Cloud Storage Bucket must be granted the Service Usage Consumer role
(see [https://cloud.google.com/service-usage/docs/access-control](https://cloud.google.com/service-usage/docs/access-control))
in order to charge the specified user project for the bucket usage cost"_

### How do I integrate with my current monitoring infrastructure?
Vespa Cloud applications have a Prometheus endpoint.
Find guides for how to integrate with Grafana and AWS Cloudwatch at [monitoring](../operations/monitoring.html).

### What is the best way to monitor instantaneously what is happening in Vespa? CPU usage? Memory usage? htop? Cloudwatch metrics?
Vespa Cloud has detailed dashboards linked from the _monitoring_ tab in the Console,
one for each zone the instance is deployed to.

### How are Vespa versions upgrades handled - only for new deploys?
Vespa is normally upgraded daily. There are exceptions, like holidays and weekends.
During upgrades, nodes are stopped one-by-one per cluster.
As all clusters have one redundant node, serving and write traffic is not impacted by upgrades.
Before the upgrade, the application's [system and staging tests](../operations/automated-deployments.html) are run,
halting the upgrade if they fail.
Documents are re-migrated to the upgraded node before doing the next node,
see [Elastic Vespa](../content/elasticity.html) for details.

### How do we get alerted to issues like Feed Block? Searchable copy going offline?
Issues like Feed Blocked, Deployment and Deprecation warnings show up in the console.
There are no warnings on redundancy level / searchable copies,
as redundant document buckets are activated for queries automatically,
and auto data-migration kicks in for node failures / replacements.

### What actions are needed when deploying schema changes?
* Schema changes that [require service restart](../reference/schema-reference.html#changes-that-require-restart-but-not-re-feed)
  are handled automatically by Vespa Cloud. A deployment job involves waiting for these to complete.
* Schema changes that [require reindexing](../reference/schema-reference.html#changes-that-require-reindexing)
  of data require a validation override, and will trigger automatic reindexing. Status can be tracked in the console application view.
  Vespa Cloud also periodically re-indexes all data, with minimal resource usage, to account for changes in linguistics libraries.
* Schema changes that [require refeeding](../reference/schema-reference.html#changes-that-require-re-feed)
  data require a validation override, and the user must refeed the data after deployment.

### What are the Vespa Cloud data retention policies?
The management of data stored in an application running on Vespa Cloud is the responsibility of the
application owner and, as such, Vespa Cloud does not have any retention policy for this data as
long as it is stored by the application.

The following data retention policies applies to Vespa Cloud:
* After a node previously allocated to an application has been deallocated (e.g. due to
  application being deleted by application owner), all application data will be deleted within
  _four hours_.
* All application log data will be deleted from Vespa servers after no more than _30 days_ (most
  often sooner) dependent on log volume, allocated disk resources, etc. *PLEASE NOTE:* This is
  the theoretical maximum retention time - see [archive guide](../cloud/archive-guide.html) for how to ensure
  access to your application logs.



### Is Vespa Cloud certified for ISO 27001 or SOC II?
Yes, Vespa.ai has a SOC 2 attestation: [Trust Center](https://trust.vespa.ai).

### Is Vespa Cloud GDPR compliant?
Read more in [GDPR](https://cloud.vespa.ai/en/gdpr).

### Does Vespa store information from the information sources with which it is integrated?
Vespa is most often used for queries in data written from the information sources,
although it can also be used without data, e.g. for model serving.
It is the application owner that writes the integration with Vespa Cloud to write data.

### What is the encryption algorithm used at rest?
Vespa Cloud uses the following Cloud providers:
* AWS EC2 instances, with local or remote storage
* GCP Compute instances, with local or remote storage
* Azure Compute instances, with local or remote storage

The storage devices are encrypted per Cloud provider, at rest.

### Does the Vespa console have audit trails/logs module and can it be accessed by an Admin user?
See the [security guide](../security/guide.html) for roles and permissions.
The Vespa Cloud Console has a log view tool,
and logs / access logs can be exported to the customer's AWS account easily.
Deployment operations are tracked in the deployment view, with a history.
Vespa Cloud Operators do not have node access, unless specifically granted by the customer, audit logged.

### Once the service purchased with Vespa is terminated, is there a secure deletion procedure for the information collected from the customer?
At termination, all application instances are removed, with data, before the tenant can be deactivated.

### Why is the CPU usage for my application above 100%?
In `dev` zones we use shared resources hence have more than one node on each host/instance.
In order to provide a best possible overall responsiveness we do not restrict CPU resources for the individual application nodes.
