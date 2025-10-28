---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa API and interfaces"
---

## Deployment and configuration
* [Deploy API](reference/deploy-rest-api-v2.html):
  Deploy [application packages](application-packages.html)
  to configure a Vespa application
* [Config API](reference/config-rest-api-v2.html):
  Get and Set configuration
* [Tenant API](reference/application-v2-tenant.html):
  Configure multiple tenants in the config servers

## Document API
* [Reads and writes](reads-and-writes.html):
  APIs and binaries to read and update documents
* [/document/v1/](reference/document-v1-api-reference.html):
  REST API for operations based on document ID (get, put, remove, update)
* [Feeding API](vespa-feed-client.html):
  High performance feeding API, the recommended API for feeding data
* [JSON feed format](reference/document-json-format.html):
  The Vespa Document format
* [Vespa Java Document API](document-api-guide.html)

## Query and grouping
* [Query API](query-api.html),
  [Query API reference](reference/query-api-reference.html)
* [Query Language](query-language.html),
  [Query Language reference](reference/query-language-reference.html),
  [Simple Query Language reference](reference/simple-query-language-reference.html),
  [Predicate fields](predicate-fields.html)
* [Vespa Query Profiles](query-profiles.html)
* [Grouping API](grouping.html),
  [Grouping API reference](reference/grouping-syntax.html)

## Processing
* [Vespa Processing](jdisc/processing.html):
  Request-Response processing
* [Vespa Document Processing](document-processing.html):
  Feed processing

## Request processing
* [Searcher API](searcher-development.html)
* [Federation API](federation.html)
* [Web service API](developing-web-services.html)

## Result processing
* [Custom renderer API](result-rendering.html)

## Status and state
* [Health and Metric APIs](operations/metrics.html)
* [/cluster/v2 API](reference/cluster-v2.html)
