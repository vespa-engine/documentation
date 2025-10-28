---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa Overview"
---

Vespa is a platform for applications which need low-latency computation over large data sets.
It stores and indexes your structured, text and vector data so that queries, selection and processing
and machine-learned model inference over the data can be performed quickly at serving time at any scale.
Functionality can be customized and extended with application components hosted within Vespa.
This document is an overview of the features and main components of Vespa.

## Introduction

Vespa allows application developers to create applications that scale
to large amounts of data and high loads without sacrificing latency or reliability.
A Vespa application consists of a number of *stateless Java container clusters*
and zero or more *content* clusters storing data.

![Vespa Overview](/assets/img/vespa-overview.svg)

The [stateless **container** clusters](jdisc/) host components
which process incoming data and/or queries and their responses.
These components provide functionality belonging to the platform like indexing
transformations and the global stages of query execution, but can also include the middleware logic of the application.
Application developers can configure their Vespa system with a single stateless cluster which
performs all such functions, or create different clusters for each kind of task.
The container clusters then pass queries and data operations on to the appropriate nodes in the content clusters.
If the application uses data it does not own, you can add components to access data from external services as well.

[**Content** clusters](elasticity.html) in Vespa are responsible for storing data
and execute queries and inferences over the data.
Queries can range from simple data lookups for content serving to complex conditions for selecting the relevant
data, ranking it using machine-learned models, and grouping and aggregating the data across all nodes
participating in the query.
All the operations provided by Vespa scales to more content, more expensive inference, and higher query volume
simply by adding more nodes to the content clusters.

When changing the nodes of a content cluster for scaling or on node failure,
content clusters automatically re-balance data in the background
to maintain a balanced distribution at the configured redundancy level.
Faulty nodes are also automatically removed from the serving path to avoid any impact to queries and
writes (failover).

After intermediate processing in a container cluster, data is written to content clusters.
Writes are persistent and visible in all queries after receiving an ack on the write message,
after a few milliseconds. Each write is guaranteed to either succeed or provide failure information
response within a given time limit, and writes and scale linearly with the available resources, indefinitely.
In addition to rewriting and removing entire documents, writes may selectively modify only individual document fields.
Writes can be sent directly over HTTP/2, or by using a Java client —
refer to the [API documentation](api.html).

Each document instance stored in Vespa are of a type defined in a configured [schema](schemas.html),
which defines the document fields and how to store and index them, as well as the ranking and inference
profiles that belongs to the document type. Applications can contain any number of schemas for different
data types, and configure them to be stored either in the same or multiple content clusters.

Container and content clusters handle all the end user traffic of a Vespa application,
but there's also a third type of cluster, the *admin and config clusters*.
These set up and manage the other clusters in the application according to configuration, and
manages the process of changing the clusters safely without disruption to traffic
when the configuration changed.

A Vespa application is completely specified by an
[*application package*](application-packages.html),
which is a directory structure containing a declaration of the clusters to run as part of the application,
the content schemas, any machine-learned models and Java components,
and other configuration or data files needed by various features.
Application developers create a running application from their application package by
*deploying* it to any node in the config cluster.
Changes to a running application is made in the same way: By changing the application package and deploying again.
Once Vespa is installed and started on a node,
it is managed by the config system such that the entire system can be treated as a single unit,
and application owners do not need to perform any administration tasks locally on the nodes running the application.
It is also possible to configure nodes as *log servers* on Vespa. These will collect logs in real time
from all the nodes of the application. By default, the first node in the config server cluster performs this role.

The rest of this document provides some more detail on the functions Vespa performs.

## Vespa operations

Vespa accepts the following operations:
* Writes: Put (add and replace) and remove documents, and update fields in these.
* Lookup of a document (or some subset of it) by id.
* [Queries](query-api.html):
  [*Select*](query-language.html) documents
  whose fields match conditions, which search
  free-text fields, structured data or [vector spaces (ANN)](nearest-neighbor-search.html).
  Any number of such conditions can be combined freely in boolean trees to
  define the full query to be executed.
  Vespa will compute a query plan over the conditions which executes them
  efficiently with any number of conditions such as e.g. filters combined with ANN conditions.
  Matches to a query can be passed through an inference step which can compute
  any business logic or machine-learned model expressed as a
  [ranking expression](reference/ranking-expressions.html) or [ONNX model](onnx.html).
  Optionally, the highest scoring matches can also run through a second stage of this,
  to spend more computational resources on promising candidates.
  The final documents are ordered according to their score from these inferences ([*ranking*](ranking.html)),
  or by explicit [*sorting*](reference/sorting.html).
  Matches to queries can be [*grouped*](grouping.html)
  hierarchically by field values,
  where each group can contain aggregated values over the data in the group
  This can be used to calculate values for, e.g., navigation aids, tag clouds,
  graphs or for clustering in a distributed fashion
  without having to transfer the distributed to a single container node.
* Data dumps: Content matching some criterion can be streamed out for background reprocessing,
  backup, etc., by using the [*visit*](visiting.html) operation.
* [Any other custom network request](reference/component-reference.html)
  which can be handled by application components deployed on a container cluster.

## The stateless container

[Container clusters](jdisc/) host the application components
which employ the operations listed above and process their return data.
Vespa provides a set of components out of the box, together with component infrastructure:
dependency injection,
with added support for injection of config from the admin server or the application package;
a component model based on OSGi;
a shared mechanism to chain components into handler chains for modularity
as well as metrics and logging.
The container also provides the network layer for handling and issuing remote requests -
HTTP is provided out of the box,
and other protocols/transports can be transparently plugged in as components.

Developers can make changes to components (and of course their configuration)
simply by redeploying their application package -
the system takes care of copying the components to the nodes of the cluster
and loading/unloading components impacting request serving or restarting nodes.

## Content clusters

[Content clusters](elasticity.html) store data
and maintain distributed indices of data for searches and selects.
Data is replicated over multiple nodes, with a number of copies specified by the application,
such that the cluster can automatically repair itself on loss of a node or a disk.
Using the same mechanism, clusters can also be grown or shrunk while online,
simply by changing the set of available nodes declared in the application package.

Lookup of an individual document is routed directly to a node storing that document,
while queries are spread over a subset of nodes which contain the queried documents.
Complex queries are performed as distributed algorithms with multiple steps back and
forth between the container and the content nodes; this is to achieve the low latency
which is one of the main design goals of Vespa.

## Administration clusters and developer support

The [single configuration cluster](/en/application-packages.html)
controls all the other clusters of the system.
A config server derives the low level configuration of each individual cluster, node and process,
such that the application developer can specify the desired system on a higher level
without worrying about its detailed realization.
Whenever the application package is redeployed,
the system will compute the necessary changes in configuration and manage the process
of moving safely from the current to the new configuration without disrupting queries or writes.

Other admin clusters in Vespa are the cluster controller cluster (controls one or more content clusters),
logserver cluster (logserver holds log archive for logs from all nodes in the application)
and service location brokers (slobroks, which are a name service used by some services in Vespa).

### Application packages

Application packages may be [changed, redeployed](reference/deploy-rest-api-v2.html)
and [inspected](reference/config-rest-api-v2.html) over an HTTP REST API,
or through a [command line interface](application-packages.html#deploy).
The administration cluster runs over [ZooKeeper](https://zookeeper.apache.org)
to make changes to configuration singular and consistent, and to avoid having a single point of failure.

An application package looks the same, and is deployed the same way,
whether it specifies a large system with hundreds of nodes or a single node running all services.
The only change needed is to the lists of nodes making up the cluster.
The container clusters may also be started within a single Java VM by "deploying" the
application package from a method call.
This is useful for testing applications in an IDE and in unit tests.
Application packages with components can be [developed](developer-guide.html)
in an IDE using Maven starting from sample applications.

## Summary

Vespa allows functionally rich and highly available applications to be developed to scale and perform to
high standards without burdening developers with the considerable low level complexity this requires.
It allows developers to evolve and grow their applications over time without taking the system offline,
and lets them avoid complex data and page precomputing schemes
which lead to stale data that cannot be personalized,
since this often requires complex queries to complete in real user time
over data which is constantly changing at the same time.

For more details, read [Vespa Features](features.html).
Go to [Getting Started](getting-started.html) for next steps.
