---
# Copyright Vespa.ai. All rights reserved.
title: "Features"
category:
---

## What is Vespa?

Vespa is a platform for applications which need low-latency computation over large data sets.
It allows you to write and persist any amount of data, and execute high volumes of queries over
the data which typically complete in tens of milliseconds.

Queries can use both structured filters conditions, text and nearest neighbor vector search to select data.
All the matching data is then ranked according to ranking functions - typically machine learned -
to implement such use cases as search relevance, recommendation, targeting and personalization.

All the matching data can also be grouped into groups and subgroups where data is aggregated
for each group to implement features like graphs, tag clouds, navigational tools, result
diversity and so on.

Application specific behavior can be included by adding Java components for processing
queries, results and writes to the application package.

Vespa is real time. It is architected to maintain constant response times with any data volume by
executing queries in parallel over many data shards and cores, and with added query volume
by executing queries in parallel over many copies of the same data (groups). It is optimized
to return responses in tens of milliseconds. Writes to data becomes visible in a few milliseconds
and can be handled at a rate of thousands to tens of thousands per node per second.

A lot of work has gone into making Vespa easy to set up and operate.
Any Vespa application - from single node systems to systems running on hundreds of nodes in data centers -
are fully configured by a single artifact called an *application package*. Low level configuration of
nodes, processes and components is done by the system itself based on the desired traits specified in the
application package.

Vespa is scalable. System sizes up to hundreds of nodes handling tens of billions of documents,
and tens of thousands of queries per second
are not uncommon, and no harder to set up and modify than single node systems. Since
all system components, as well as stored data is redundant and self-correcting, hardware
failures are not operational emergencies and can be handled by re-adding capacity when convenient.

Vespa is self-repairing and dynamic. When machines are lost or new ones added, data is automatically
redistributed over the machines, while continuing serving and accepting writes to the data.
Changes to configuration and Java components can be made while serving by deploying a changed
application package - no downtime or restarts required.

## Features

This section provides an overview of the main features of Vespa.
The remainder of the documentation goes into full detail.

### Data and writes
* Documents in Vespa may be added, replaced, modified (single fields or any subset) and removed.* Writes are acknowledged back to the client issuing them when they are durable and visible in queries,
    in a few milliseconds.* Writes can be issued at a sustained volume of thousands to tens of thousands per node per second while serving queries.* Data is replicated with a configurable redundancy.* An even data distribution, with the desired redundancy is automatically maintained when nodes are added,
          removed or lost unexpectedly.* Data corruption is automatically repaired from an uncorrupted replica of the data.* Data is written over a simple HTTP/2 API, or (for high volume) using a small, standalone client.* Document data schemas allow fields of any of the usual primitive types as well as collections, structs and tensors.* Any number of data schemas can be used at the same time.* Documents may reference each other and field from referenced documents may be used in queries without performance penalty.* Write operations can be processed by adding custom Java components.* Data can be streamed out of the system for batch reprocessing.

### Queries
* Queries may contain any combination of structured filters, free text and vector search operators.* Queries may contain large tensors and vectors (to represent e.g a user).* Queries choose how results should be ranked and specify how they should be organized (see sections below).* Queries and results may be processed by adding custom Java components - or any HTTP request may be
        turned into a query by custom request handlers.* Query response times are typically in tens of milliseconds and can be maintained given any load
          and data size by adding more hardware.* A *streaming search* mode is available where search/selection is only supported on predefined
            groups of documents (e.g a user's document). In this mode each node can store and serve billions of
            documents while maintaining low response times.

### Ranking and inference
* All results are ranked using a configured ranking function, selected in the query.* A ranking function may be any mathematical function over scalars or tensors (multidimensional arrays).* Scalar functions include an "if" function to express business logic and decision trees.* Tensor functions include a powerful set of primitives and composite functions which
        allows expression of advanced machine-learned ranking functions such as e.g. deep neural nets.* Functions can also refer to ONNX models invoked locally on the content nodes.
        * Multiple ranking phases are supported to allocate more CPU to ranking promising candidates.* A powerful set of text ranking features using positional information from the documents is provided out of the box.* Other ranking features include 2D distance and freshness.

### Organizing data and presenting results
* Matches to a query can be grouped and aggregated according to a specification in the query.* All the matches are included, even though they reside on multiple machines executing in parallel.* Matches can be grouped by a unique value or by a numerical bucket.* Any level of groups and subgroups are supported, and multiple parallel groupings can be specified in one query.* Data can be aggregated (counted, averaged etc.) and selected within each group and subgroup.* Any selection of data from documents can be included with the final result returned to the client.* Search engine style keyword highlighting in matching fields is supported.

## Configuration and operations
* Vespa can be installed using rpm files or a Docker image - on personal laptops, owned datacenters or in AWS.* An application of Vespa is fully specified as a separate buildable artifact: An *application package* -
    individual machines or processes need never be configured individually.* Systems may contain multiple clusters of each type (stateless and stateful), each containing any number of nodes.* Systems of any size may be specified by two short configuration files in the application package.* Document schemas, Java components and ranking functions/models are also configured in the application package.* An application package is deployed as a single unit to Vespa to realizes the system desired by the application.* Most application changes (including Java component changes) can be performed by deploying
              a changed application package - the system will manage its own change process while serving and handling writes.* Most document schema changes (excluding field type changes) can be made while the system is live.* Application package changes are validated on deployment to prevent destructive changes to live systems.* Vespa has no single-point-of-failures and automatically routes around failing nodes.* System logs are collected to a central server in real time.* Selected metrics may be emitted to a third-party metrics/alerting system from all the nodes.
