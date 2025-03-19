---
# Copyright Vespa.ai. All rights reserved.
title: Topology and Resizing
---

Vespa has features to optimize cost, query latency and throughput,
at the same time making tradeoffs for availability.
This guide goes through various topologies by example, highlighting the most relevant tradeoffs
and discusses operational events like node stop and changing the topology.

Use cases for using a grouped topology is found in the
[elasticity](https://docs.vespa.ai/en/elasticity.html#grouped-distribution) guide.
E.g., query latency can dictate the maximum number of document per node and hence how many node are needed in a group -
if query latency is at maximum tolerated for 1M documents,
6 nodes are needed in a group for a 6M index.

{% include note.html content="Vespa Cloud supports a one-level grouped topology -
a group of groups is hence not supported."%}

Content nodes are stateful, holding replicas of the documents to be queried.
Content nodes can be deployed in different topologies - example using 6 nodes:

<img src="/assets/img/grouped-topology.svg" width="698px" height="auto" alt="4 different topologies" />

Vespa Cloud requires a redundancy of at least 2.
In this guide, it is assumed that redundancy, configured as
[min-redundancy](https://docs.vespa.ai/en/reference/services-content.html#min-redundancy), is set to n=3.
Redundancy is a function of data availability / criticality and cost, and varies from application to application.

Redundancy is for storing a document replica on a node.
Not all replicas are searchable -
read [Proton](https://docs.vespa.ai/en/proton.html) for a detailed understanding of sub-databases.



## Out of the box: 1x6
Most applications should be configured without a grouped topology, until optimizing for a use case -
see the elasticity guide linked above.
Therefore, start with a _flat_ configuration, like:
<div class="row">
  <div class="col-1-2">
    <img src="/assets/img/1x6.svg" alt="1x6" width="433" height="auto"/>
  </div>
  <div class="col-1-2">
<pre>
&lt;min-redundancy&gt;3&lt;/min-redundancy&gt;
&lt;nodes count="6"&gt;
    &lt;resources .../&gt;
&lt;/nodes&gt;
</pre>
  </div>
</div>
This means, the corpus is spread over 6 nodes, with 17% of documents active in queries each.
This topology is called 1x6 in this guide.

This is important to remember when benchmarking for latency, normally done on a single node with n=1.
In the 6-node system with n=3, more memory and disk space is used for the redundant replicas -
more on that later.

This topology is the default topology, and works great:

* When a node is stopped (unplanned, or planned like a software upgrade),
  there are 5 other nodes to serve queries, where each of the 5 will have 1/5 larger corpus to serve
* Adding capacity, say 17% is done by increasing node count to 7

{% include note.html content="This topology is the default, and what most applications should start with."%}



## 3-row topology: 3x2
Some applications, particularly the ones with extreme low-latency serving,
will find that queries are dominated by the static part of query execution.
This means, reducing number of documents queried does not lower latency.

The flip side is, increasing document count does not increase the latency much, either - consider 3x2:
<div class="row">
  <div class="col-1-2">
    <img src="/assets/img/3x2.svg" alt="3x2" width="185" height="auto"/>
  </div>
  <div class="col-1-2">
<pre>
&lt;min-redundancy&gt;3&lt;/min-redundancy&gt;
&lt;nodes count="6" groups="3"&gt;
    &lt;resources .../&gt;
&lt;/nodes&gt;
</pre>
  </div>
</div>

Here we have configured 3 groups, with n=3.
This means, the other node in the row does not have a replica - redundancy is between the rows.

Each node now has 3x the number of documents per query (compared to 1x6), but query capacity is also tripled,
as each row has the full document corpus.
This can be a great way to scale query throughput!
Notes:
* At planned/unplanned node stop, the full row is eliminated from query serving -
  there are four nodes total left, in two rows.
  Query capacity is hence down to 67%.
* Feeding requirements is the same as in 1x6 - every document write is written to 3 replicas.
* Document reconciliation is independent of topology -
  replicas from all nodes are used when rebuilding nodes after a node stop.



## 6-row topology: 6x1
Maximizing number of documents per node is good for cases where the query latency is still within requirements,
and less total work is done, as fewer nodes in a row calculates candidates in ranking.
The extreme case is all documents on a single node replicated with 6 groups.
This is a quite common configuration due to high throughput and simplicity:

<div class="row">
  <div class="col-1-2">
    <img src="/assets/img/6x1.svg" alt="6x1" width="140" height="auto"/>
  </div>
  <div class="col-1-2">
<pre>
&lt;min-redundancy&gt;6&lt;/min-redundancy&gt;
&lt;nodes count="6" groups="6"&gt;
    &lt;resources .../&gt;
&lt;/nodes&gt;
</pre>
  </div>
</div>

Notes:
* Feeding _total work_ is higher - with n=6, six replicas are written (compared to three above).
  See [feeding latency](#feeding) notes below.



## 2-row topology: 2x3
In this case, the application has a redundancy of 2 - it must be the same as number of rows:

<div class="row">
  <div class="col-1-2">
    <img src="/assets/img/2x3.svg" alt="2x3" width="248" height="auto"/>
  </div>
  <div class="col-1-2">
<pre>
&lt;min-redundancy&gt;2&lt;/min-redundancy&gt;
&lt;nodes count="6" groups="2"&gt;
    &lt;resources .../&gt;
&lt;/nodes&gt;
</pre>
  </div>
</div>

This is a configuration most applications do not use:
When a node stops (and it does daily for Vespa upgrades),
the full row stops serving, which is 50% of the capacity out.

{% include important.html content="Use this topology with care -
  it has few/no benefits over the alternatives, and is included here for completeness."%}



## Topology migration
Migrating from one topology to another is easy, as Vespa Cloud will auto-migrate documents:

* All rows must have same node count, meaning `count / groups` must be an integer.
* When changing topology, Vespa Cloud will provision new nodes as needed to ensure no coverage loss.
  An increased node count is hence normal in the transition phase,
  superfluous nodes are de-provisioned after data migration.
* Topology migration is therefore a safe operation and makes it easy to optimize for best price/performance.

<!-- ToDo: Add group autoscaling note / how to set minimum row size -->



## Feeding
Documents are fed to Vespa Cloud using the
[&lt;document-api&gt;](https://docs.vespa.ai/en/reference/document-v1-api-reference.html#configuration) endpoint.
This means, one Vespa Container node forwards document writes to all the replicas, in parallel.
As all groups have a replica, adding a group will not add feed _latency_ in theory due to the parallelism.
However, there will be an increase in practise as more nodes means more latency variation,
and the slowest node sets the end latency.
