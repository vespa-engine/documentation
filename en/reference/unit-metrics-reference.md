---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Metric Units Reference"
---

| Unit | Description |
| --- | --- |
| binary | Zero or one. Zero typically indicate "false" while one indicate "true" |
| bucket | A chunk of documents managed by a distributor service |
| buffer | A buffer |
| byte | A collection of 8 bits |
| byte/second | A unit of storage capable of holding 8 bits |
| class | A instance of a Java class |
| connection | A link used for communication between a client and a server |
| context switch | A context switch |
| deployment | A deployment on hosted Vespa |
| document | Vespa document, a collection of fields defined in a schema file |
| documentid | A unique document identifier |
| dollar | US dollar |
| dollar/hour | Total current cost of the cluster in $/hr |
| failure | Failures, typically for requests, operations or nodes |
| file | Data file stored on the disk on a node |
| fraction | A value in the range [0..1]. Higher values can occur for some metrics, but would indicate the value is outside the allowed range. |
| generation | Typically, generation of configuration or application package |
| gigabyte | One billion bytes |
| hit | Document that meets the filtering/restriction criteria specified by a given query |
| hit/query | Number of hits per query over a period of time |
| host | Bare metal computer that contain nodes |
| instance | Typically, tenant or application |
| item | Object or unit maintained in e.g. a queue |
| millisecond | Millisecond, 1/1000 of a second |
| nanosecond | Nanosecond, 1/1000.000.000 of a second |
| node | (Virtual) computer that is part of a Vespa cluster |
| packet | Collection of data transmitted over the network as a single unit |
| operation | A clearly defined task |
| operation/second | Number of operations per second |
| percentage | A number expressed as a fraction of 100, normally in the range [0..100]. |
| query | A request for matching, grouping and/or scoring documents stored in Vespa |
| query/second | Number of queries per second. |
| record | A collection of information, typically a set of key/value, e.g. stored in a transaction log |
| request | A request sent from a client to a server |
| response | A response from a server to a client, typically as a response to a request |
| restart | A service or node restarts |
| routing rotation | Routing rotation |
| score | Relevance score for a document |
| second | Time span of 1 second |
| seconds since epoch | Seconds since Unix Epoch |
| session | A set of operations taking place during one connection or as part of a higher level operation |
| task | Piece of work executed by a server, e.g. to perform back-ground data maintenance |
| tenant | Tenant that owns zero or more applications in a managed Vespa system |
| thread | Computer thread for executing e.g. tasks, operations or queries |
| vcpu | Virtual CPU |
| version | Software or config version |
| wakeup | Computer thread wake-ups for doing some work |
