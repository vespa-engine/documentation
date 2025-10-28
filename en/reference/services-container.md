---
# Copyright Vespa.ai. All rights reserved.
title: "services.xml - container"
category: oss,cloud
---

This is the reference for container cluster configuration:

```
container [version, id]
    http
        server [id, port]
        filtering
    handler [id, class, bundle]
        binding
        component
    server [id, class, bundle]
    clients
        client [id, permissions]
            certificate [file]
            token [id]
    components
    component
    search
        include [dir]
        binding
        searcher
        federation
        provider
        chain
        renderer
        threadpool
        significance
    document-processing
        include [dir]
        documentprocessor
        chain
    processing
        include [dir]
        binding
        processor
        chain
        renderer
    document-api
        abortondocumenterror
        retryenabled
        route
        maxpendingdocs
        maxpendingbytes
        retrydelay
        timeout
        tracelevel
        mbusport
        ignore-undefined-fields
    model-evaluation
        onnx
    document [type, class, bundle]
    accesslog [type, fileNamePattern, symlinkName, rotationInterval, rotationScheme]
        request-content [samples-per-second, path-prefix, max-bytes]
    config
    nodes [allocated-memory, jvm-gc-options, jvm-options]
        environment-variables
        jvm [allocated-memory, options, gc-options]
        node [hostalias]
    secrets
    secret-store [type]
        group [name, environment]
    zookeeper
```

Contained in [services](services.html), zero or more `container` elements.
The root element of a container cluster definition.
Most elements takes optional [config](config-files.html#generic-configuration-in-services-xml) elements.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| version | required | number |  | 1.0 in this version of Vespa |
| id | required | string |  | logical name of this cluster |

Example:

```
<container id="default" version="1.0">
    <search>
        <chain id="default">
            <searcher id="com.mydomain.SimpleSearcher" bundle="the name in <artifactId> in pom.xml"/>
        </chain>
    </search>
    <nodes>
        <node hostalias="node1"/>
    </nodes>
</container>
```

Each container cluster has a default http server port, unless it contains a
[http](services-http.html) element.
Hence, when running more than one `container` cluster on the same node,
it is necessary to manually assign a port to the http server to all but one cluster.
Otherwise, the application will not deploy. Assigning a port is done by adding a
[server](services-http.html#server) element with an explicit port number:

```
<container id="cluster2" version="1.0">
    <http>
        <server id="myServer" port="8081" />
    </http>
    ...
</container>
```

## handler

The `handler` element holds the configuration of a request handler.
For each `binding` tag, the handler will be bound
to the pertinent JDisc interfaces using the given binding.
* `binding` For JDisc request handlers, add this server binding to this handler.
* [`component`](#component) for injecting another component.
  Must be a declaration of a new component, not a reference.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The component ID |
| class | optional | string |  | The class of the handler, defaults to id |
| bundle | optional | string |  | The bundle to load the handler from: The name in <artifactId> in pom.xml. Defaults to class or id (if no class is given) |

Example:

```
<container id="default" version="1.0">
    <handler id="com.yahoo.search.handler.LegacyBridge">
        <binding>http://*/*</binding>
    </handler>
    <handler bundle="the name in <artifactId> in pom.xml" id="com.mydomain.vespatest.RedirectingHandler"/>
    <handler bundle="the name in <artifactId> in pom.xml" id="com.mydomain.vespatest.ExampleHandler"/>
    <nodes>
        <node hostalias="node1"/>
    </nodes>
</container>
```

## binding

The URI to map a Handler to. Multiple elements are allowed. See example above.

## server

The `server` element holds the configuration of a JDisc server provider.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The component ID |
| class | optional | string |  | The class of the server, defaults to id |
| bundle | optional | string |  | The bundle to load the server from: The name in <artifactId> in the pom.xml. Defaults to class or id (if no class is given). |

Example:

```
<server id="com.mydomain.vespatest.DemoServer">
    <config name="vespatest.demo-server">
        <response>Hello, world!
        </response>
        <port>16889</port>
    </config>
</server>
```

## clients

Vespa Cloud only.
The `clients` element is a parent element for [client](#client) security configuration.
Find details and practical examples in the [security guide](/en/cloud/security/guide.html#configure-tokens).
Example:

```
{% highlight xml %}










{% endhighlight %}
```

## client

Vespa Cloud only.
Child element of [clients](#clients).
Use to configure security credentials for a container cluster,
using [certificate](#certificate) and/or [token](#token).

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The client ID |
| permissions | required | string |  | Permissions, see the [security guide](/en/cloud/security/guide.html#permissions). One of:   * `read` * `write` * `read,write` |

## certificate

Vespa Cloud only.
Child element of [client](#client).
Configure certificates using the *file* attribute.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| file | required | string |  | Path to the certificate file, see the [security guide](/en/cloud/security/guide.html#configuring-mtls). |

## token

Vespa Cloud only.
Child element of [client](#client).
Configure tokens using the *id* attribute.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | Token ID, see the [security guide](/en/cloud/security/guide.html#configure-tokens). |

## components

Contains [component](#component) elements.
Can be used in conjunction with [include](#include) for modular config of components.

## component

The `component` element holds the configuration of a
[generic component](../jdisc/injecting-components.html#special-components).
Must be a declaration of a new component, not a reference.

Nested [`component`](#component) child elements can be added for injecting
specific component instances. This is useful if there is more than one declared component
of the same Java class. Refer to [Injecting
components](../jdisc/injecting-components.html) for details and examples.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The component ID |
| class | optional | string |  | The class of the component, defaults to id |
| bundle | optional | string |  | The bundle to load the component from: The name in <artifactId> in the pom.xml. Defaults to class or id (if no class is given). |

Example:

```
<component id="com.mydomain.demo.DemoComponent" bundle="the name in <artifactId> in pom.xml" />
```

## document-api

Use to enable [Document API](../api.html) operations to a container cluster.
Children elements:

| Name | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| binding | optional | string | http://*/ | The URI to map the document-api handlers to. Multiple bindings are valid. Must end with a '/'. Note that each document-api handler will get its individual binding by adding a suffix, e.g. the feed handler will add 'feed/', the remove handler will add 'remove/' and so on. Example:   ``` <document-api>     <binding>http://*/document-api/</binding>     <binding>https://*/document-api/</binding> </document-api> ```  With these configured bindings, the feed handler will be available at `http://*/document-api/feed/` and `https://*/document-api/feed/`. For other handlers, just replace 'feed/' with the appropriate suffix, e.g. 'get/', 'remove/' etc. |
| abortondocumenterror | optional | true/false | true | Controls whether to abort the entire feed or not if a document-related error occurs, i.e. if a document contains an unknown field. Setting this field to `true` will abort the feed on such errors, while setting it to `false` will cause Vespa to simply skip to the next document in the feed. Note that malformed XML in the input will abort the feed regardless of this setting. |
| maxpendingbytes | optional | number |  | The maximum number of pending bytes. If `<maxpendingdocs>` is 0 and this is set to 0, this defaults to 100 MB. If `<maxpendingdocs>` is more than 0, and this is set to 0, the send-window is only limited by number of messages sent, not the memory footprint. |
| maxpendingdocs | optional | number |  | The maximum number of pending documents the client can have. By default, the client will dynamically adjust the window size based on the latency of the performed operations. If the parameter is set, dynamic window sizing will be turned off in favor of the configured value. |
| mbusport | optional | number |  | Set the MessageBus port |
| retrydelay | optional | double | 1.0 | Delay in seconds between retries |
| retryenabled | optional | true/false |  | Enable or disable retrying documents that have failed. |
| route | optional | string | default | Set the route to feed documents to |
| timeout | optional | double | 180.0 | Set the timeout value in seconds for an operation |
| tracelevel | optional | 0-9 | 0 | Configure the level of which to trace messages sent. The higher the level, the more detailed descriptions. |
| ignore-undefined-fields | optional | true/false | false | Set to true to ignore undefined fields in document API operations and let such operations complete successfully, rather than fail. A [response header is returned](document-v1-api-reference.html#x-vespa-ignored-fields) when field operations are ignored. |

Example:

```
<document-api>
    <binding>http://*/document-api/</binding>
    <binding>https://*/document-api/</binding>
    <abortondocumenterror>false</abortondocumenterror>
    <maxpendingbytes>1048576</maxpendingbytes>
    <maxpendingdocs>1000</maxpendingdocs>
    <mbusport>1234</mbusport>
    <retrydelay>5.5</retrydelay>
    <retryenabled>false</retryenabled>
    <route>default</route>
    <timeout>250.5</timeout>
    <tracelevel>3</tracelevel>
<document-api>
```

## document

[Concrete document type](../concrete-documents.html) bindings for the container. Example:

```
<container id="default" version="1.0">
    <document class="com.mydomain.concretedocs.Vehicle"
              bundle="the name in <artifactId> in pom.xml"
              type="vehicle"/>
    <document class="com.mydomain.concretedocs.Vehicle"
              bundle="the name in <artifactId> in pom.xml"
              type="ship"/>
    <document class="com.mydomain.concretedocs2.Disease"
              bundle="the name in <artifactId> in pom.xml"
              type="disease"/>
    <search/>
    <document-processing>
        <chain id="default">
            <documentprocessor bundle="the name in <artifactId> in pom.xml"
                               id="concretedocs.ConcreteDocDocProc"/>
        </chain>
    </document-processing>
    <nodes>
        <node hostalias="node1"/>
    </nodes>
</container>
```

## accesslog

Configures properties of the accesslog.
The default type is `json` that will give output in (line-based)
[JSON format](../access-logging.html).
See [Access logging](../access-logging.html) for configuration details.
Setting the type to `vespa` gives a classic Apache CLF-like format.

Access logging can be disabled by setting the type to `disabled`.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| type | optional | string | json | The accesslog type: *json*, *vespa* or *disabled* |
| fileNamePattern | required* | string | JsonAccessLog.<container id>.%Y%m%d%H%M%S | File name pattern. * Note: Optional when *type* is *disabled* |
| symlinkName | optional | string | JsonAccessLog.<container id> | Symlink name |
| rotationInterval | optional | string | 0 60 ... | Rotation interval |
| rotationScheme | optional | string | date | Valid values are *date* or *sequence* |

### request-content

The `request-content` element is a child of `accesslog` and configures logging of request content.
Multiple `request-content` elements can be specified to log different request paths with different configurations.

| Element | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| samples-per-second | required | double |  | Probabilistic sample rate per second |
| path-prefix | required | string |  | URI path prefix to match for logging |
| max-bytes | required | integer |  | Maximum size in bytes to log, only prefix will be kept for larger requests |

Example:

```
  <accesslog fileNamePattern="$VESPA_HOME/logs/vespa/access/JsonAccessLog.<container id>.%Y%m%d%H%M%S"
             symlinkName="JsonAccessLog.<container id>"
             rotationInterval="0 1 ..."
             type="json" >
    <request-content>
        <samples-per-second>0.2</samples-per-second>
        <path-prefix>/search</path-prefix>
        <max-bytes>65536</max-bytes>
    </request-content>
  </accesslog>
```

## include

Allows including XML snippets contained in external files.
All files from all listed directories will be included.
All files must have the same outer tag as they were referred from,
i.e. search, document-processing or processing.
The path must be relative to the application package root,
and must never point outside the package.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| dir | required | string |  | The directory to include files from. File inclusion order is undefined. |

Example:

```
<include dir="included_configs/search" />
```

## nodes

The `nodes` element specifies the nodes that comprise this container cluster by adding *node* children.
Also see [nodes](/en/reference/services.html#nodes).

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| allocated-memory | optional | percentage |  | {% include deprecated.html content="See [jvm](#jvm)."%} |
| jvm-options | optional | string |  | {% include deprecated.html content="See [jvm](#jvm)."%} |
| jvm-gc-options | optional | string |  | {% include deprecated.html content="See [jvm](#jvm)."%} |

## environment-variables

Add children elements to `nodes` for environment variables - see example below.
These are set before the services are started on the container node - available for the Container.

## jvm

JVM settings for container nodes:

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| allocated-memory | optional | percentage |  | Memory to allocate to each JVM instance as a percentage of available memory. Must be an integer percentage followed by *%* |
| options | optional | string |  | Generic JVM options |
| gc-options | optional | string |  | JVM GC options. Garbage Collector specific parameters |

Example where 50% of the node total memory is used as the Max heap size of the JVM:

```
<nodes>
    <jvm gc-options="-XX:+UseG1GC -XX:MaxTenuringThreshold=10"
         options="-XX:+PrintCommandLineFlags"
         allocated-memory="50%" />
</nodes>
```

## node

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| hostalias | required | string |  | logical hostname - mapped to hostnames in [hosts.xml](hosts.html) |

Example:

```
<nodes>
    <environment-variables>
        <KMP_SETTING>1</KMP_SETTING>
        <KMP_AFFINITY>granularity=fine,verbose,compact,1,0</KMP_AFFINITY>
    </environment-variables>
    <node hostalias="searchnode1" />
</nodes>
```

## secrets

Use to access secrets configured in Vespa Cloud -
refer to the [secret store](/en/cloud/security/secret-store.html).

## secret-store

The `secret-store` element holds configuration for custom implementations.
Contains one or more `group` elements.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| type | required | string |  | Value: "oath-ckms" |

## group

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| name | required | string |  | Key group name |
| environment | required | string |  | Value one of: "alpha" "corp" "prod" "aws" "aws_stage" |

Example:

```
<secret-store type="my-ckms">
    <group name="[key group]" environment="[environment]"/>
</secret-store>
```

## zookeeper

The *zookeeper* element declares that the container cluster should run ZooKeeper
and configure the necessary components.
This element has no attributes or children.
