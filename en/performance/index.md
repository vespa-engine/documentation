---
# Copyright Vespa.ai. All rights reserved.
title: "Performance"
---

## Practical search performance guide

See [practical search performance guide](practical-search-performance-guide.html).
The guide walks through a music search use case and gives a practical introduction to Vespa search performance.

## Sizing and capacity planning

Sizing and capacity planning involves figuring out how many nodes are needed
and what kind of hardware flavor best fits the use case:
* [Sizing Vespa search](sizing-search.html): How to size a Vespa search cluster
* [Caching in Vespa](caches-in-vespa.html): How to enable caches in Vespa
* [Attributes and memory usage](../attributes.html):
  How attributes impact the memory footprint, find attribute memory usage
* [Proton maintenance jobs](../proton.html#proton-maintenance-jobs): Impact on resource usage
* [Coverage degradation](../graceful-degradation.html): Timeout handling and Degraded Coverage

## Benchmarking and tuning

Benchmarking is important both during sizing and for testing new features.
What tools to use for benchmarking and how to tune system aspects of Vespa:
* [Benchmarking Vespa](vespa-benchmarking.html):
  Test Vespa performance
* [Search features and performance](feature-tuning.html)
* [Feed performance](sizing-feeding.html)* [Container Http performance testing using Gatling](container-http.html)
  * [Container tuning](container-tuning.html): JVM, container, docproc
  * [vespa-fbench](/en/operations/tools.html#vespa-fbench): Reference documentation
  * [HTTP/2](http2.html): improve HTTP performance using HTTP/2

## Profiling

Do a deep performance analysis - how to profile the application as well as Vespa:
* [Profiling](profiling.html): Generic profiling tips.
* [Valgrind](valgrind.html): Run Vespa with Valgrind
