---
# Copyright Vespa.ai. All rights reserved.
title: "Java Data Intensive Serving Container - JDisc"
---

Vespa's Java container - JDisc, hosts all application components as well as the stateless logic of Vespa itself.
Which particular components are hosted by a container cluster is configured in services.xml. The main features of
JDIsc are:
* HTTP serving out of the box from an embedded Jetty server,
  and support for plugging in other transport mechanisms.
* Integration with the config system of Vespa which allows components to
  [receive up-to-date config](../configuring-components.html)
  (by constructor injection) resulting from application deployment.
* [Dependency injection based on Guice](injecting-components.html)
  (Felix), but extended for configs and component collections.
* A component model based on [OSGi](../components/bundles.html) which allows
  component to be (re)deployed to running servers, and to control which APIs they expose to others.
* The features above combine to allow application package changes (changes to components, configuration or data)
  to be applied by Vespa without disrupting request serving nor requiring restarts.
* Standard component types exists for
  + [general request handling](developing-request-handlers.html)+ [chained request-response processing](processing.html)+ [processing document writes](../document-processing.html)+ [intercepting queries and results](../searcher-development.html)+ [rendering responses](../result-rendering.html)Application components can be of any other type as well and do not need to reference any Vespa API to
  be loaded and managed by the container.
* A general [chain composition](../components/chained-components.html) mechanism for components.

## Developing Components
* The JDisc container provides a framework for processing requests and responses,
  named *Processing* - its building blocks are:
  + [Chains](../components/chained-components.html)
    of other components that are to be executed serially,
    with each providing some service or transform
  + [Processors](processing.html)
    that change the request and / or the response. They may also
    make multiple forward requests, in series or parallel,
    or manufacture the response content themselves
  + [Renderers](processing.html#response-rendering)
    that are used to serialize a Processor's response before
    returning it to a client
* Application Lifecycle and unit testing:
  + [Configuring components](../configuring-components.html)
    with custom configuration
  + [Component injection](injecting-components.html) allows components
    to access other application components
  + Learn how to [build OSGi bundles](../components/bundles.html) and
    how to [troubleshoot](../components/bundles.html#troubleshooting) classloading issues
  + Using [Libraries for Pluggable Frameworks](pluggable-frameworks.html) from
    a component may result in class loading issues that require extra setup in the application
  + [Unit testing configurable components](../unit-testing.html#unit-testing-configurable-components)
* Handlers and filters:
  + [Http servers and
    security filters](http-server-and-filters.html) for incoming connections on HTTP and HTTPS
  + [Request handlers](developing-request-handlers.html)
    to process incoming requests and generate responses
* Searchers and Document Processors:
  + [Searcher](../searcher-development.html) and
    [search result renderer](../result-rendering.html)
    development
  + [Document processing](../document-processing.html)

## Reference documentation
* [services.xml](../reference/services-container.html)

## Other related documents
* [Designing RESTful web
  services](../developing-web-services.html) as Vespa Components
* [healthchecks](../reference/healthchecks.html) - using the Container with a VIP
* [Vespa Component Reference](../reference/component-reference.html):
  The Container's request processing lifecycle
