---
# Copyright Vespa.ai. All rights reserved.
title: "services.xml - http"
---

This is the reference for the `http` subelement of
[container](services-container.html) in [services.xml](services.html).
The http block is used to configure http servers and filters -
when this element is present, the default http server is disabled.

```
http
    server [id, port]
        ssl
            private-key-file
            certificate-file
            ca-certificates-file
            client-authentication
            protocols
            cipher-suites
        ssl-provider [class, bundle]
    filtering
        filter [id, class, bundle, provides, before, after]
          provides
          before
          after
          filter-config
        request-/response-chain [id, inherits, excludes]
          binding
          filter [id, class, bundle, provides, before, after]
              provides
              before
              after
              filter-config
          inherits
              chain
              exclude
          phase [id, before, after]
              before
              after
```

Most elements takes optional [config](config-files.html#generic-configuration-in-services-xml) elements,
see example in [server](#server).

Note: To bind the search handler port (i.e. queries),
refer to [search bindings](services-search.html#binding).

Example:

```
<http>
    <server id="server1" port="8080" />
    <server id="server2" port="9000" />

    <filtering>
        <filter id="request-filter1" class="com.yahoo.test.RequestFilter1" />
        <filter id="response-filter1" class="com.yahoo.test.ResponseFilter1" />

        <request-chain id="test-request-chain">
            <binding>http://*/*</binding>
            <filter id="request-filter1"/>
            <filter id="request-filter2" class="com.yahoo.test.RequestFilter2" />
        </request-chain>

        <response-chain id="test-response-chain">
            <binding>http://*:8080/*</binding>
            <binding>http://*:9000/path</binding>
            <filter id="response-filter1"/>
            <filter id="response-filter2" class="com.yahoo.test.ResponseFilter2" />
        </response-chain>
    </filtering>
</http>
```

## server

The definition of a http server.
Configure the server using
[jdisc.http.connector.def](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/resources/configdefinitions/jdisc.http.jdisc.http.connector.def).

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The component ID |
| port | optional | number | The web services port of the [environment variables](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables) | Server port |
| default-request-chain | optional | string |  | The default request chain to use for unmatched requests |
| default-response-chain | optional | string |  | The default response chain to use for unmatched requests |

Example:

```
<server id="server1" port="8080">
    <config name="jdisc.http.connector">
        <idleTimeout>90</idleTimeout>
    </config>
</server>
```

## ssl

Setup TSL on HTTP server using credentials provided in PEM format.

## private-key-file

Path to private key file in PEM format.

## certificate-file

Path to certificate file in PEM format.

## ca-certificates-file

Path to CA certificates file in PEM format.

## client-authentication

Client authentication. Supported values: *disabled*, *want* or *need*.

## protocols

Comma-separated list of TLS protocol versions to enable. Example: *TLSv1.2,TLSv1.3*.

## cipher-suites

Comma-separated list of TLS cipher suites to enable. The specified ciphers must be supported by JDK installation. Example: *TLS_AES_256_GCM_SHA384,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384*.

## ssl-provider

Setup TLS on the HTTP server through a programmatic Java interface.
The specified class must implement the
[SslProvider](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/jdisc/http/SslProvider.html) interface.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| class | required | string |  | The class name |
| bundle | required | string |  | The bundle name |

## filtering

`filtering` is for configuring http filter chains. Sub-elements:
* [filter](#filter)
* [request-chain](#chain)
* [response-chain](#chain)

Example:

```
<filtering>
    <filter id="request-filter1" class="com.yahoo.test.RequestFilter1" />
    <filter id="response-filter1" class="com.yahoo.test.ResponseFilter1" />

    <request-chain id="test-request-chain">
        <binding>http://*/</binding>
        <filter id="request-filter1"/>
        <filter id="request-filter2" class="com.yahoo.test.RequestFilter2" />
    </request-chain>

    <response-chain id="test-response-chain">
        <binding>http://*/</binding>
        <filter id="response-filter1"/>
        <filter id="response-filter2" class="com.yahoo.test.ResponseFilter2" />
    </response-chain>
</filtering>
```

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| strict-mode | optional | boolean | true | When set to true, all requests must match a filter. For any requests not matching, an HTTP 403 response is returned. |

## binding

Specifies that requests/responses matching the given URI pattern
should be sent through the [request-chain/response-chain](#chain).

## filter

The definition of a single filter, for referencing when defining chains.
If a single filter is to be used in different chains,
it is cleaner to define it directly under `http`
and then refer to it with `id`,
than defining it inline separately for each chain.
The following filter types are supported:
* RequestFilter
* ResponseFilter
* SecurityRequestFilter
* SecurityResponseFilter

Security[Request/Response]Filters are automatically wrapped in Security[Request/Response]FilterChains.
This makes them behave like regular Request/Response filters with respect to chaining.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The component ID |
| class | optional | string | id | The class of the component, defaults to id |
| bundle | optional | string | id or class | The bundle to load the component from, defaults to class or id (if no class is given) |
| before | optional | string |  | Space separated list of phases and/or filters which should succeed this phase |
| class | optional | string | id | Space separated list of phases and/or filters which should precede this phase |

Sub-elements:
* [provides](#provides)
* [before](#before)
* [after](#after)
* [filter-config](#filter-config)

Example:

```
<filter id="filter2" class="com.yahoo.test.Filter2"/>
```

## provides

A name provided by a filter for phases and other filters to use as dependencies.
Contained in [filter](#filter)
and [filter](#filter) (in chain).

## before

The name of a phase or filter which should succeed this phase or filter.
`before` tags may be used if it is necessary to define filters or phases
which always should succeed this filter or phase in a chain.
In other words, the phase or filter defined is placed *before* name in the tag.
Contained in [filter](#filter),
[filter](#filter) (in chain)
and [phase](#phase).

## after

The name of a phase or filter which should precede this phase or filter.
`after` tags may be used if it is necessary to define filters or phases
which always should precede this filter or phase in a chain.
In other words, the phase or filter defined is placed
*after* the name in the tag.
Contained in [filter](#filter),
[filter](#filter) (in chain)
and [phase](#phase). Example:

```
<filter id="filterauth" class="com.yahoo.test.auth">
    <provides>Authorization</provides>
    <before>LastFilters</before>
    <after>Earlyfilters</after>
</filter>
```

## filter-config

Only used to configure filters that are configured with
`com.yahoo.jdisc.http.filter.security.FilterConfig`.
This is the case for all filters provided in JDisc bundles.

## request-chain/response-chain

Defines a chain of request filters or response filters respectively.
A chain is a set ordered by dependencies.
Dependencies are expressed through phases, which may depend upon other phases, or filters.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| inherits |  | string |  | A space separated list of chains this chain should include the contents of |
| excludes |  | string |  | A space separated list of filters (contained in an inherited chain) this chain should not include |

Sub-elements:
* [binding](#binding)
* [filter](#filter). Refer to or define a filter.
  *config* or *filter-config* can not be added to references, only filter definitions.
* [inherits](#inherits)
* [phase](#phase)

Examples:

```
<request-chain id="default-request-filters">
    <binding>http://*/*</binding>
    <filter id="com.yahoo.test.RequestFilter"/>
</request-chain>
<response-chain id="response-filters">
    <binding>http://*:8080/*</binding>
    <binding>http://*:9000/path</binding>
    <filter id="com.yahoo.test.ResponseFilter"/>
</response-chain>
```

## inherits

Wrapper element for information about which chains, if any, a chain should inherit, and how.
Contained in [request-chain](#chain) and
[response-chain](#chain).
Sub-elements:
* (inherited) [chain](#inheritedchain)
* [exclude](#exclude)

## (inherited) chain

The ID of a chain which this chain should inherit, i.e. include all filters and phases from.
Use multiple `chain` tags if it is necessary to combine the filters from multiple chains.
Contained in [inherits](#inherits).

## exclude

A filter the chain under definition should exclude from the chain or chains it inherits from.
Use multiple `exclude` tags to exclude multiple filters.
Contained in [inherits](#inherits). Example:

```
<request-chain id="demo">
    <inherits>
        <chain>idOfSomeInheritedChain</chain>
        <exclude>idOfUnwantedFilter</exclude>
        <exclude>idOfYetAnotherUnwantedFilter</exclude>
    </inherits>
    <filter id="filter2" class="com.yahoo.test.Filter2"/>
</request-chain>
```

## phase

Defines a phase, which is a checkpoint to help order filters.
Filters and other phases may depend on a phase to be able to make assumptions about the order of filters.
Contained in [chain](#chain).

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The ID, or name, which other phases and filters may depend upon as a [successor](#before) or [predecessor](#after) |
| before | optional | string |  | Space separated list of phases and/or filters which should succeed this phase |
| after | optional | string |  | Space separated list of phases and/or filters which should precede this phase |

Sub-elements:
* [before](#before)
* [after](#after)

Example:

```
<request-chain id="demo">
    <phase id="CheckpointName">
        <before>Authorization</before>
    </phase>
    <filter id="filter2" class="com.yahoo.test.Filter2"/>
</request-chain>
```
