---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa Serving Scaling Guide"
---

*Vespa can scale in multiple scaling dimensions:*
* Scale document volume and write volume
* Scale query throughput
* Scale serving latency to meet service level agreements (SLA)

The question one tries to answer during a sizing exercise is:
*What the total cost would be to serve a use case using Vespa?*.

This document helps sizing an application correctly with as low cost as possible.
Vespa is used to implement many use cases, and this document is relevant for all of them:
* Serving a [text ranking](../nativerank.html) use case
  or a [recommendation](../tutorials/news-1-getting-started.html) use case
* Serving a machine learned model, e.g., a [Tensorflow](../tensorflow.html),
  [ONNX](../onnx.html), [XGBoost](../xgboost.html), or
  [LightGBM](../lightgbm.html) model

With Vespa, it is possible to do benchmarking on a few nodes
to infer the overall performance and cost of the chosen deployment architecture,
and as Vespa supports [live resizing](../elasticity.html),
it is easy to scale from a prototype to a full production size deployment.

This document covers sizing and capacity planning for serving,
see [feed performance sizing](sizing-feeding.html) for feed performance sizing
and [Vespa serving feature tuning](feature-tuning.html).
It also covers the following topics:
* [Data distribution](#data-distribution) in Vespa and how it impacts serving
* [Scaling Serving Latency and Throughput](#content-cluster-scalability-model) in Vespa
* [Scaling Data Volume](#scaling-document-volume-per-node) in Vespa

## Data distribution in Vespa - flat versus grouped

The basic element in the Vespa search architecture is a content node, which is part of a content cluster.
A Vespa deployment can have several content clusters, which can be scaled independently.

A content node holds a fraction of the entire data corpus.
Data is distributed to nodes using a [distribution algorithm](../content/idealstate.html),
which goal is to uniformly distribute data over the set of nodes.
The goal is also to avoid distribution skew,
while at the same time supporting re-distribution of data,
with minimal data movement,
if the size of the content cluster changes.
Read [content cluster elasticity](../elasticity.html) to learn
how data is distributed across nodes, and how adding or removing nodes works.
See also [Vespa's consistency model](../content/consistency.html) documentation.

### Flat content distribution

![Flat content distribution](/assets/img/flat-content-distribution.svg)

With a flat distribution, the content is distributed to content nodes using the
[ideal state distribution algorithm](../content/idealstate.html).
A query is dispatched in parallel from a container instance to
**all** content nodes in the content cluster.
Each content node searches the *active* part of the *ready* sub-database.
The above figure illustrates a deployment using 4 nodes with *redundancy* 2 and *searchable-copies* 2 -
see the [availability](#high-data-availability) section.

When using flat data distribution, the only way to scale query throughput is to reduce the search latency.
Given a fixed occupancy (users, load clients),
this relationship between query throughput and latency is described by
[Little's law](https://en.wikipedia.org/wiki/Little%27s_law) -
more on this in [content cluster scalability model](#content-cluster-scalability-model) section.

### Grouped content distribution

![Grouped content distribution](/assets/img/grouped-content-distribution.svg)

With a grouped distribution, content is distributed to a configured set of *groups*,
such that the entire document collection is contained in each group.
A *group* contains a set of content nodes where the content is
distributed using the [distribution algorithm](../content/idealstate.html).
In the above illustration, there are 4 nodes in total, 2 groups with 2 nodes in each group.
*redundancy* is 2 and *searchable-copies* is also 2.
As can be seen from the figure with this grouped configuration,
the content nodes only have a populated ready sub-database.
A query is dispatched in parallel to all nodes in **one group** at a time
using a [dispatch-policy](../reference/services-content.html#dispatch-policy).
The default policy is *adaptive*, which load balances over the set of groups, aiming at even latency.

### High Data Availability

Ideally, the data is available and searchable at all times, even during node failures.
High availability costs resources due to data replication.
How many replicas of the data to configure
depends on what kind of availability guarantees the deployment should provide.
Configure availability vs cost:

| [redundancy](../reference/services-content.html#redundancy) | Defines the total number of copies of each piece of data the cluster will store and maintain to avoid data loss. Example: with a redundancy of 2, the system tolerates 1 node failure before any further node failures may cause data to become unavailable. |
| [searchable-copies](../reference/services-content.html#searchable-copies) | Configures how many of the copies (as configured with *redundancy*) to be indexed (*ready*) at any time. Configuring *searchable-copies* to be less than *redundancy* saves resources (memory, disk, cpu), as not all copies are indexed (*ready*). In case of node failure, the remaining nodes needs to index the *not ready* documents which belonged to the failed node. In this transition period, the search has reduced search coverage. |

### Content node database

![Content node databases](/assets/img/proton-databases.svg)

The above figure illustrates the three
[sub-databases](../proton.html#sub-databases) inside a Vespa content node.
* The documents in the **Ready** DB are indexed,
  but only the documents in **Active** state are searchable.
  In a flat distributed system there is only one active instance of the same document,
  while with grouped distribution there is one active instance per group.
* The documents in the **Not Ready** DB are stored but not indexed.
* The documents in the **Removed** DB are stored but blocklisted, hidden from search.
  The documents are permanently deleted from storage by
  [Proton maintenance jobs](../proton.html#proton-maintenance-jobs).

If the availability guarantees tolerate temporary search coverage loss during node
failures (e.g. *searchable-copies*=1), this is by far the most optimal for serving performance -
the query work per node is less, as index structures like posting lists are smaller.
The index structures only contains documents in *Active* state,
not including *Not Active* documents.

With *searchable-copies*=2 and *redundancy*=2,
each replica is fully indexed on separate content nodes.
Only the documents in *Active* state are searchable,
the posting lists for a given term are (up to) doubled as compared to *searchable-copies*=1.

See [Content cluster Sizing example deployments](sizing-examples.html)
for examples using grouped and flat data distribution.

## Life of a query in Vespa

Find an overview in [query execution](../query-api.html#query-execution):

![Query execution - from query to response](/assets/img/query-to-response.svg)

Vespa executes a query in two protocol phases
(or more if using [result grouping features](../grouping.html))
to optimize the network footprint of the parallel query execution.
The first protocol phase executes the query in parallel over content nodes in a group to find the global top hits,
the second protocol phase fetches the data of the global top hits.

During the first phase,
content nodes match and [rank](../ranking.html) documents using the selected rank-profile/model.
The hits are returned to the stateless container for merging
and potentially blending when multiple content clusters are involved.

When the global top ranking documents are found,
the second protocol phase fetch the summary data for the global best hits
(e.g. summary snippets, the original field contents, and ranking features).
By doing the query in two protocol
phases one avoids transferring summary data for hits which will not make it into the global best hits.

Components Involved in query execution:
* **Container**
  + Parses the [API](../query-api.html) request
    and the [query](../query-language.html) and run time context features.
  + Modifies the query according to the schema specification (stemming, etc.) for a text search application
    or creating run time query or user context tensors for an ML serving application.
  + Invokes chains of custom [container components/plugins](../jdisc/container-components.html)
    which can work on the request and query input and also the results.
  + Dispatching of query to content nodes in the content cluster(s) for parallel execution.
    With flat distribution queries are dispatched to all content nodes,
    while with a grouped distribution the query is dispatched to all content nodes within a group
    and the queries are load-balanced between the groups using a
    [dispatch-policy](../reference/services-content.html#dispatch-policy).
  + Blending of global top ranking results from cluster(s).
  + Fetching the top ranking results with document summaries from cluster(s).
  + Result processing and possible top-k re-ranking and finally rendering of results back to client.
* **Content node (Proton)**
  + Finding all documents matching the [query specification](../query-api.html).
    For an ML serving use case, the selection might be a subset of the content pool
    (e.g. limit the model to only be evaluated for content-type video documents),
    while for a text ranking application it might be a
    [WAND](../using-wand-with-vespa.html) text matching query.
  + Calculating the score (which might be a text ranking relevancy score or
    the inferred score of a Machine Learned model) of each hit,
    using the chosen rank-profile. See [ranking with Vespa](../ranking.html).
  + Aggregating information over all the generated hits using [result grouping](../grouping.html).
  + Sorting hits on relevancy score (text ranking) or inference score (e.g. ML model serving),
    or on attribute(s).
    See *max-hits-per-partition* and *top-k-probability* in
    [dispatch tuning](../reference/services-content.html#dispatch-tuning)
    for how to tune how many hits to return.
  + Processing and returning the document summaries of the selected top hits
    (during summary fetch phase after merging and blending has happened on levels above).

The detailed execution inside Proton during the matching and ranking first protocol phase is:

1. Build up the query tree from the serialized network representation.
2. Lookup the query terms in the index and B-tree dictionaries
   and estimate the number of hits each term and parts of the query tree will produce.
   Terms which search attribute fields without [fast-search](../attributes.html#fast-search)
   will be given a hit count estimate to the total number of documents.
3. Optimize and re-arrange the query tree for most efficient performance, trying to move terms or
   operators with the lowest hit ratio estimate first in the query tree.
4. Prepare for query execution, by fetching posting lists from the index and B-tree structures.
5. Multithreaded execution per search starts using the above information.
   Each thread will do its own thread local setup.
6. Each search thread will evaluate the query over its document space.
7. The search threads complete first phase and agree which hits will continue to second phase ranking
   (if enabled per the used rank-profile).
   The threads operate over a shared heap with the global top ranking hits.
8. Each thread will the complete second phase and grouping/aggregation/sorting.
9. Merge all threads results and return up to the container.

[Container](../jdisc/) clusters are stateless and easy to scale horizontally,
and don't require any data distribution during re-sizing.
The set of stateful content nodes can be scaled independently
and [re-sized](../elasticity.html) which requires re-distribution of data.
Re-distribution of data in Vespa is supported and designed to be done without significant serving impact.
Altering the number of nodes or groups in a Vespa content cluster does not require re-feeding of the corpus,
so it's easy to start out with a sample prototype and scale it to production scale workloads.

## Content cluster scalability model

Vespa is a parallel computing platform
where the work of matching and ranking is parallelized across a set of nodes and processors.
The speedup one can get by altering the number of nodes in a Vespa content group follows
[Amdahl's law](https://en.wikipedia.org/wiki/Amdahl%27s_law),
which is a formula used to find the maximum improvement possible by improving a particular part of a system.
In parallel computing, *Amdahl's law* is mainly used to predict the theoretical
maximum speedup for program processing using multiple processors.
In Vespa, as in any parallel computing system,
there is work which can be parallelized and work which cannot.
The relationship between these two work types determine how to best scale the system,
using a flat or grouped distribution.

|  |  |
| --- | --- |
| **static query work** | Portion of the query work on a content node that does not depend on the number of documents indexed on the node. This is an administrative overhead caused by system design and abstractions, e.g. number of memory allocations per query term. Typically, a large query tree means higher static work, and this work cannot be parallelized over multiple processors, threads or nodes. The static query work portion is described in step 1 to 4 and step 9 in the detailed life of a query explanation above. |
| **dynamic query work** | Portion of the query work on a content node that depends on the number of documents indexed and active on the node. This portion of the work scales mostly linearly with the number of matched documents. The dynamic query work can be parallelized over multiple processors and nodes. Referenced later as *DQW*. The *DQW* also depends on the phase two protocol summary fill where the actual contents of the global best documents is fetched from the content nodes which produced the hit in the first protocol phase. |
| **Total query work** | The total query work is given as the dynamic query work (*DQW*) + static query work (*SQW*). |

Adding content nodes to a content cluster (keeping the total document volume fixed) with flat distribution
reduces the dynamic query work per node (*DQW*),
but does not reduce the static query work (*SQW*).
The overall system cost also increases as you need to rent another node.

Since *DQW* depends and scales almost linearly with the number of documents on the content nodes,
one can try to distribute the work over more nodes.
*Amdahl's law* specifies that the maximum speedup one achieve by parallelizing the
dynamic work (*DQW*) is given by the formula:

$$\text{max_speedup}_{\text{group}} = \frac{1}{1 - \frac{DQW}{SQW+DQW}}$$

For example, if one by inspecting [metrics](#metrics-for-vespa-sizing) see that the *DQW* = 0.50,
the maximum speedup one can get by increasing parallelism by using more nodes and decreasing *DQW* is 2.
With fixed occupancy (number of users, clients or load),
[Little's Law'](https://en.wikipedia.org/wiki/Little%27s_law)
tells us that one could achieve two times the throughput if one is able to speed up the latency by a factor of two:

$$\frac{1}{1 - \frac{0.5}{0.5+0.5}} = 2$$

When *SQW* is no longer significantly less than *DQW*,
adding more nodes in a flat distributed cluster just increases the overall system cost.
This without any serving performance gain,
except increasing overall supported feed throughput,
which increases almost linearly with number of nodes.

Two different *DQW/(DQW+SQW)* factors are illustrated in the figures below.
The overall query work *TQW* is the same for both cases (10 ms),
but the *DQW* portion of the *TQW* is different.
The throughput (QPS) is a function of the latency ([Little's Law](https://en.wikipedia.org/wiki/Little%27s_law))
and the number of cpu cores * nodes.
Using 1 node with 24 v-cpu cores and 10 ms service time (*TQW*),
one can expect reaching close to 2400 QPS at 100% utilization
(unless there are other bottlenecks like network or stateless container processing).

![Scaling throughput/latency where DQW/(SQW+DQW)=0.5](/assets/img/ScalingLatencyFactor0.5.svg)
![Scaling throughput/latency where DQW/(SQW+DQW)=0.9](/assets/img/ScalingLatencyFactor0.005.svg)

In the first figure the overall latency is 10 ms,
but the dynamic query work (latency) is only 50%
and given *Amdahl's law* it follows that the maximum speedup one can get is two.
This is true regardless of how many processors or nodes the dynamic query work is parallelized over.
No matter how many nodes one adds, one don't get above 4800 queries/s.
The only thing one achieve by adding more nodes
is increasing the cost without *any* performance benefits.

In the second figure there is a system where the dynamic work portion is much higher (0.9),
and the theoretical maximum speedup becomes bound by 10x as given by *Amdahl's law*.
Note that both figures are with a single flat distributed content cluster with a fixed document volume.

Given the theory, one can derive two rules of thumb for scaling throughput and latency:

| Add nodes in a flat distribution | When DQW/TQW is large (close to 1.0), throughput QPS can be scaled by just adding more content nodes in a system using flat distribution. This will reduce the number of documents per node, and thus reduce the *DQW* per node. |
| Add groups using grouped distribution | When DQW/TQW is low, one can no longer just add more content nodes to scale throughput and must instead use a grouped distribution to scale throughput. |

## Scaling latency in a content group

Irrespective of using single group (flat distribution) or multiple groups,
the serving latency depends on the factors already described; *DQW* and *SQW*.
For use cases where *DQW* dominates the total query work *TQW*,
one can effectively scale latency down by parallelizing the *DQW* over more nodes per group.

It is important to decide on a latency service level agreement (SLA)
before sizing the Vespa deployment for the application and query features.
A latency SLA is often specified as a latency percentile at a certain throughput level - example:
* SLA Example 1: 95.0 percentile < 100 ms @ 2000 QPS
* SLA Example 2: 95.0 percentile < 40 ms @ 8000 QPS

Different use cases might have different performance characteristics,
depending on how the dynamic work query portion is compared to the static query work portion.
This graph illustrates the relationship between overall latency versus number of documents indexed per node for two
different use cases.

![Latency vs document count per node](/assets/img/latency-documents.svg)
* For the yellow use case the measured latency is almost independent of the total document volume.
  This is called sublinear latency scaling, which calls for scaling up using better flavor
  specification instead of scaling out.

  The observed latency at 10M documents per node is almost the same as with 1M documents per node.
  Such a use case would be most cost-effective by storing as many documents as possible
  (within the memory/disk/feeding constrains set by the concurrency settings and node flavor)
  and scale throughput by using a grouped distribution.
  Efficient query operators which are sublinear has scaling properties
  like the yellow case. Example of such query operators include
  the [wand operators](../using-wand-with-vespa.html), and [approximate nearest neighbor search operator](../approximate-nn-hnsw.html)
* For the blue use case the measured latency shows a clear correlation with the document volume.
  This is a case where the dynamic query work portion is high,
  and adding nodes to the flat group will reduce the serving latency.
  The sweet spot is found where targeted latency SLA is achieved.
  This sweet spot depends on which model or ranking features are in use,
  e.g. how expensive the model is per retrieved or ranked document.

  For example, a [GBDT xgboost model](../xgboost.html) with 3000 trees
  might breach the targeted latency SLA already at 200K documents,
  while a 300 tree model might be below the SLA at 2M documents.
  Using exact [nearest neighbor search](../nearest-neighbor-search.html)
  has scaling properties like the blue case.
  See also [feature tuning](feature-tuning.html).

### Reduce latency with multithreaded per-search execution

It is possible to reduce latency of queries
where the [dynamic query work](#dynamic-query-work) portion is high.
Using multiple threads per search for a use case where the static query work is high
will be as wasteful as adding nodes to a flat distribution.

![Content node search latency vs threads per search](/assets/img/Threads-per-search.svg)

Using more threads per search will reduce latency as long as the dynamic portion of the query cost is high
compared to the static query cost. The reduction in latency comes with the cost of higher cpu utilization.

A search request with four threads will occupy all four threads until the last thread has completed,
and the intra-node per thread document space partitioning must be balanced to give optimal results.

For rank profiles with second phase ranking, see [phased ranking](../phased-ranking.html),
the hits from first-phase ranking are rebalanced so that each matching thread scores about
the same amount of hits using the second phase ranking expression.

From the above examples with the blue and yellow use case it follows that
* Linear exact nearest neighbor search latency can be reduced by using more threads per search
* Sublinear approximate nearest neighbor search latency does not benefit from using more threads per search

By default the number of threads per search is one,
as that gives the best resource usage measured as CPU resources used per query.
The optimal threads per search depends on the query use case,
and should be evaluated by benchmarking.

The threads per search settings globally is tuned by
[persearch](../reference/services-content.html#requestthreads-persearch).
This can be overridden to a lower value in
[rank profiles](../reference/schema-reference.html#num-threads-per-search)
so that different query use cases can use different number of threads per search.
Using multiple threads per search allows better utilization of
multicore cpu architectures for low query volume applications.
The persearch number in services should always be equal to the highest num-threads-per-search in your rank profiles.
Setting it higher leaves threads unused.

#### Thread configuration

To get started, set `search` to be 2x number of CPU cores.
`persearch` should never be more than number of cores.
`summary` should be equal to number of cores.
Start with the default value of 1 for `persearch` and only increase it for lower query latency,
as it will reduce throughput and efficiency.

## Scaling the size of the retrievable unit

Retrieving units that are too small or too large can have a drastic impact on both the quality and
performance of your search. Consider an example where we want to search in PDF files: Creating one
document per PDF file seems like a logical solution, and with Vespa this is possible - up to a point.
But as system architects we must consider the potential edge cases: some files may be entire books,
or long reports with many hundreds or even thousands of pages.

The current max document size is limited by the max protobuf message size of 2 GB, but we advise
staying well below this limit, at least < 200MB and ideally < 1MB for even, predictable performance.
For reference to scale, the complete text of the bible is about 4MB.
*Split too-large documents into smaller units for better search quality and performance!*
Natural subdivisions like chapters, parts or sections are good candidates for splitting into separate
Vespa documents.

### When documents are too large If each document is a complete PDF file and some are very large, what problems could we run into? **Usefulness of the result** - knowing that there are relevant parts *somewhere* in several hundred pages of text is not very helpful to the user. As of 2025, this is still true also if the "user" is an LLM in a RAG or agentic workflow. We can improve the usefulness by providing [dynamic snippets](/en/document-summaries.html#dynamic-snippets) or returning per-chunk similarity scores as [feature values](/en/ranking-expressions-features.html#accessing-feature-function-values-in-results) to be able to identify the most relevant portions of the returned summary. **Performance** - Returning large document values in the query response over HTTP has a significant cost, both in CPU time spent in rendering the response, compression, and network transfer time. This can easily become the largest contribution to the total end-to-end latency. Large documents can also contribute to poor performance in indexing and query execution, or greatly increase the amount of temporary memory required for complex ranking expressions like multi-dimensional ColBert maxsim. As document are processed, indexed, stored and ranked as individual units, working on a few very large documents at a time may not offer the system enough opportunity to parallelize and result in poor, uneven utilization of resources, and even a small fraction of very large documents may impact your mean (and especially higher percentile) latencies both for processing and query execution.When documents are too small What problems can occur if documents are very small? Consider indexing small fragments of text, like a single sentence or even a word. **Granularity** - As the size of text fragments decrease, we are less likely to find good matches for queries as the relevant terms or context is spread across multiple documents. The response may not contain enough information to resolve the user information need, or to even judge if it is likely to resolve the need if the source is examined in full. This problem is described both in [traditional information retrieval literature](https://nlp.stanford.edu/IR-book/html/htmledition/choosing-a-document-unit-1.html) and has also been a popular topic in recent years as "chunking" for semantic search. **Overhead** - splitting a document into very small pieces means that more resources will be spent on per-document overhead. Shared metadata like e.g. the abstract or access permissions of a document will be replicated many times, and updates/deletes to the source document or its metadata must fan-out to all the sub-documents, increasing write load. Unlike too-large documents, having a fraction of very small documents is fine, what matters for efficiency is that the average size is not too small.Scaling document volume per node One want to fit as many documents as possible into a node given the node constrains (e.g. available cpu, memory, disk) while maintaining: * The targeted search latency SLA * The targeted feed and update rate, and feed latency With the latency SLA in mind, benchmark with increasing number of documents per node and watch system level metrics and Vespa metrics. If latency is within the stated latency SLA and the system meets the targeted sustained feed rate, overall cost is reduced by fitting more documents into each node (e.g. by increasing memory, cpu and disk constraints set by the node flavor). With larger fan-out using more nodes to partition the data also overcomes higher tail latency as search waits for all results from all nodes. Therefore, the overall execution time depends on the slowest node at the time of the query. In such cases with large fan-out, using [adaptive timeout](../reference/services-content.html#coverage) is recommended to keep tail latency in check. Vespa will block feed operations if [resource limits](../reference/services-content.html#resource-limits) have been reached. Disk usage sizing Disk usage of a content node increases as the document volume increases: The disk usage per document depends on various factors like the number of schemas, the number of indexed fields and their settings, and most important the size of the fields that are indexed and stored. The simplest way to determine the disk usage is to simply index documents and watch the disk usage along with the relevant metrics. The *redundancy* (number of copies) impact the disk usage footprint, obviously. Note that [content node maintenance jobs](../proton.html#proton-maintenance-jobs) temporarily increases disk usage. E.g. *index fusion* is an example, where new index files are written, causing an increase in used disk space while running. Space used depends on configuration and data - headroom must include the temporary usage. See [metrics for capacity planning](#metrics-for-vespa-sizing). Memory usage sizing The memory usage on a content node increases as the document volume increases. The memory usage increases almost linearly with the number of documents. The vespa-proton-bin process (content node) uses the full 64-bit virtual address space, so the virtual memory usage reported might be high, as both index and summary files are mapped into memory using mmap and pages are paged into memory as needed. The memory usage per document depends on the number of fields, the raw size of the documents and how many of the fields are defined as [attributes](../attributes.html). Also see [metrics for capacity planning](#metrics-for-vespa-sizing). Scaling Throughput As seen in the previous sections, when the static query work (*SQW*) becomes large, scale throughput using grouped distribution. Regardless, if throughput is scaled by grouped distribution for use cases with high static query work portion or a flat distribution for high dynamic query work portion, one should identify how much throughput the total system supports. Finding where the latency starts climbing exponentially versus throughput is important in order to make sure that the deployed system is scaled well below this throughput threshold. Also, that it has capacity to absorb load increases over time, as well as having sufficient capacity to sustain node outages during peak traffic. At some throughput level some resource(s) in the system will be fully saturated, and requests will be queued up causing latency to spike up, as requests are spending more time waiting for the saturated resource. This behaviour is illustrated in the figure below: Latency vs throughput A small increase in serving latency is observed as throughput increases, until saturated at approximately 2200 QPS. Pushing more queries than this only increases queueing time, and latency increases sharply. Scaling for failures and headroom It is important to also measure behaviour under non-ideal circumstances, to avoid getting too good results. E.g., by simulating node failures or node replacements, verifying feeding concurrency versus search and serving. See [Serving availability tuning](sizing-examples.html#serving-availability-tuning). Generally, the higher utilization a system has in production, the more fragile it becomes when changing query patterns or ranking models. The target system utilization should be kept sufficiently low for the response times to be reasonable and within latency SLA, even with some extra traffic occurring at peak hours. See also [graceful degradation](../graceful-degradation.html). Also see [sizing write versus read](sizing-feeding.html#feed-vs-search). Metrics for Vespa Sizing The relevant [Vespa Metrics](../operations/metrics.html) for measuring the cost factors, in addition to system level metrics like cpu util, are: *Metric capturing static query work (SQW) at content nodes* ``` content.proton.documentdb.matching.rank_profile.query_setup_time ``` *Metric capturing dynamic query work (DQW) at content nodes* ``` content.proton.documentdb.matching.rank_profile.query_latency ``` By sampling these metrics, one can calculate the theoretical speedup we can achieve by increasing number of nodes using flat distribution, by using *Amdahl's law*: $$\text{max_speedup}_{\text{}} = \frac{1}{1 - \frac{match\_time}{query\_setup\_time+match\_time}}$$ In addition, the following metrics are used to find number of matches per query, per node: ``` content.proton.documentdb.matching.rank_profile.docs_matched content.proton.documentdb.matching.rank_profile.queries ``` **Disk usage**: * documentdb: *vespa.content.proton.documentdb.disk_usage.last* * transaction log: *vespa.content.proton.transactionlog.disk_usage.last* **Memory usage**: * documentdb: *vespa.content.proton.documentdb.memory_usage.allocated_bytes.last*
