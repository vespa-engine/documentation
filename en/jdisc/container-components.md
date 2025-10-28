---
# Copyright Vespa.ai. All rights reserved.
title: "Container Components"
---

This document explains the common concepts necessary to develop all types of Container components.
A basic knowledge of the Vespa Container is required.

All components must extend a base class from the Container code module.
For example, searchers must extend the class `com.yahoo.search.Searcher`.
The main available component types are:
* [processors](processing.html)
* [searchers](../searcher-development.html)
* [document processors](../document-processing.html)
* [search result renderers](../result-rendering.html)
* [provider components](injecting-components.html#special-components).

Searchers and document processors belong to a subclass of components
called [chained components](../components/chained-components.html).
For an introduction to how the different component types interact,
refer to the [overview of component types](../reference/component-reference.html#component-types).

The components of the search container are usually deployed as part of
an [OSGi bundle](../components/bundles.html).
Build the bundles using maven and the [bundle plugin](../components/bundles.html#maven-bundle-plugin).
Refer to the [multiple-bundles sample app](https://github.com/vespa-engine/sample-apps/tree/master/examples/multiple-bundles) for a multi-bundle example.

## Concurrency

Components will be executed concurrently by multiple threads.
This places an important constraint on all component classes:
*non-final instance variables are not safe.*
They must be eliminated, or made thread-safe somehow.

## Resource management

Components that use threads, file handles or other native resources
that needs to be released when the component falls out of scope,
must override a method called `deconstruct`.
Here is an example implementation from a component that uses a thread pool named 'executor':

```
@Override
public void deconstruct() {
    super.deconstruct();
    try {
        executor.shutdown();
        executor.awaitTermination(10, TimeUnit.SECONDS);
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
}
```

Note that it is always advisable to call the super-method first.
Also see [SharedResource.java](https://github.com/vespa-engine/vespa/blob/master/jdisc_core/src/main/java/com/yahoo/jdisc/SharedResource.java) for how to configure [debug options](../reference/services-container.html#jvm)
for use in tools like YourKit.
This can be used to track component lifetime / (de)construction issues, e.g.:

```
<nodes>
    <jvm options="-Djdisc.debug.resources=true"/>
</nodes>
```

Read more in [container profiling](../performance/profiling.html#profiling-the-query-container).

## Dependency injection

The components might need to access resources, such as other components or config.
These are injected directly into the constructor.
The following types of constructor dependencies are allowed:
* [Config objects](../configuring-components.html)
* [Other components](injecting-components.html)
* [The Linguistics library](../linguistics.html)
* [System info](#the-systeminfo-injectable-component)

The [Component Reference](../reference/component-reference.html#injectable-components) contains a
complete list of built-in injectable components.

If your component class needs more than one public constructor,
the one to be used by the container must be annotated with `@com.yahoo.component.annotation.Inject` from
[annotations](https://search.maven.org/artifact/com.yahoo.vespa/annotations).

### The SystemInfo Injectable Component

This component provides information about the environment that the component is running in,
for example
* The zone in the Vespa Cloud, if applicable.
* The number of nodes in the container cluster, and their indices.
* The index of the node this is running on.

The two latter can be used e.g. for [bucket testing](../testing.html#feature-switches-and-bucket-tests)
new features on a subset of nodes.
Please note that the node indices are not necessarily contiguous or starting from zero.

## Deploying a Component

The container will create one or more instances of the component,
as specified in [the application package](#adding-component-to-application-package).
The container will create a new instance of this component
only when it is reconfigured,
so any data needed by the component can be read and prepared from a constructor in the component.

See the full API available to components at the
[Container Javadoc](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/container/package-summary.html).

Once the component passes unit tests, it can be deployed.
The steps involved are building the component jar file,
adding it to the Vespa application package and deploying the application package.
These steps are described in the following sections, using a searcher as example.

### Building the Plugin .jar

To build the plugin jar, call `mvn install` in the project directory.
It can then be found in the target directory, and will have the suffix *-deploy.jar*.

Assume for the rest of the document that the artifactId
is `com.yahoo.search.example.SimpleSearcher` and the version is `1.0`.
The plugin built will then have the name *com.yahoo.search.example.SimpleSearcher-1.0-deploy.jar*.

### Adding the Plugin to the Vespa Application Package

The previous step should produce a plugin jar file,
which may now be deployed to Vespa by adding it to
an [application package](../application-packages.html):
A directory containing at minimum *hosts.xml* and *services.xml*.
* put `com.yahoo.search.example.SimpleSearcher-1.0-deploy.jar`
  in the `components/` directory under the application package root
* modify [services.xml](../reference/services.html) to include the Searcher

To include the searcher, define a search chain and add the searcher to it. Example:

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">

    <admin version="2.0">
        <adminserver hostalias="node1" />
        </configservers>
        <logserver hostalias="node1" />
    </admin>

    <container version="1.0">
        <search>
            <chain id="default" inherits="vespa">
                <searcher id="com.yahoo.search.example.SimpleSearcher" bundle="the name in <artifactId> in your pom.xml" />
            </chain>
        </search>
        <nodes>
            <node hostalias="node1" />
        </nodes>
    </container>

</services>
```

The searcher id above is resolved to the plugin jar we added by the `Bundle-SymbolicName`
([a field in the manifest of the jar file](../components/bundles.html)),
which is determined by the `artifactId`,
and to the right class within the bundle by the class name.
By keeping the `searcher id`, `class name`
and `artifactId` the same, we keep things simple,
but more advanced use where this is possible is also supported.
This will be explained in later sections.

For a reference to these tags,
see [the search chains reference](../reference/services-search.html#chain).

Example `hosts.xml`:

```
<?xml version="1.0" encoding="utf-8" ?>
<hosts>
    <host name="localhost">
        <alias>node1</alias>
    </host>
</hosts>
```

By creating a directory containing this `services.xml`,
`hosts.xml` and `components/com.yahoo.search.example.SimpleSearcher-1.0-deploy.jar`,
that directory becomes a complete application package containing a bundle, which can now be deployed.

### Deploying the Application Package

Set up a Vespa instance using the [quick start](../vespa-quick-start.html).
Once the component and the config are added to the application package,
it can be [deployed](../application-packages.html#deploy)
by running `vespa deploy`.
These steps will copy any changed bundles to the nodes in the cluster which needs them
and switch queries over to running the new component versions.

This works safely without requiring any processes to be restarted,
even if the application package contains changes to classes which are already running queries.
The switch is atomic from the point of view of the query -
all queries will execute to completion,
either using only the components of the last version of the application package or only the new ones,
so interdependent changes in multiple searcher components can be deployed without problems.

#### JNI requires restart

The exception to the above is bundles containing JNI packages.
There can only be one instance of the native library, so such bundles cannot reload.
Best practice is to load the JNI library in the constructor,
as this will cause the new bundle *not* to load, but continue on the current version.
A subsequent restart will load the new bundle.
This will hence not cause failures.
Alternatively, if the JNI library is initialized lazily (e.g. on first invocation),
bundle reloads will succeed, but subsequent invocations of code using the JNI library will fail.
Hence, the new version will run, but fail.

A warning is issued in the log when deploying rather than the normal
*Switching to the latest deployed set of handlers* - example:

```
[2016-09-21 14:22:05.387] WARNING : container        stderr     Cannot load mylib native library
```

To minimize restarts, it is recommended to put JNI components in minimal, separate bundles.
This will prevent reload of the JNI-bundles, unless the JNI-bundle itself is changed.

#### Monitoring the active Application

All containers also provide a built-in handler that outputs JSON formatted information about the active application,
including its components and chains (it can also be configured to show
[a user-defined version](../reference/application-packages-reference.html#versioning-application-packages)).
The handler answers to requests with the path `/ApplicationStatus`.
For example, if 'localhost' runs a container with HTTP configured on port 8080:

```
http://localhost:8080/ApplicationStatus
```

### Including third-party libraries

External dependencies [can be included into the bundle](../components/bundles.html#maven-bundle-plugin).

### Exporting, importing and including packages in bundles

[OSGi features information hiding -
by default all the classes used inside a bundle are invisible from the outside.](../components/bundles.html)

### Global and exported packages

The JDisc Container has one set of *global* packages.
These are packages that are available with no import,
and constitutes the supported API of the JDisc Container.
Backwards incompatible changes are not made to these packages.

There is also a set of *exported* packages.
These are available for import, and includes all legacy packages,
plus extension packages which are not part of the core API.
Note that these are not considered to be "public" APIs, as global packages are,
and backwards incompatible changes *can* be made to these packages,
or they may be removed.

The list of exported and global packages is available in the
[container-core
pom.xml](https://github.com/vespa-engine/vespa/blob/master/container-core/pom.xml), in `project/properties/exportedPackages`
and `project/properties/globalPackages`.

### Versions

All the elements of the search container which may be referenced by an
id may be *versioned*, that includes chains, components and query profiles.
This allows multiple versions of these elements to be used at the same time,
including multiple versions of the same classes,
which is handy for [bucket testing](../testing.html#feature-switches-and-bucket-tests) new versions.

An id or id reference may include a version by using the following syntax: `name:version`.
This works with ids in search requests, services.xml, code and query profiles.

A version has the format:

```
major.minor.micro.qualifier
```

where major, minor and micro are integers and qualifier is a string.
Any right-hand portion of the version string may be skipped.
In *versions*, skipped values mean "0" (and *empty* for the qualifier).
In *version references* skipped values means "unspecified".
Any unspecified number will be matched to the highest number available,
while a qualifier specified *must* be matched exactly if it is specified
(qualifiers are rarely used).

To specify the version of a bundle, specify version in pom.xml
(we recommend not using *qualifier*):

```
<groupId>com.yahoo.example</groupId>
<artifactId>MyPlugin</artifactId>
<version>major.minor.micro</version>
```

This will automatically be used to set the `Bundle-Version` in the bundle manifest.

For more details, see [component versioning](../reference/component-reference.html#component-versioning).

## Troubleshooting

### Container start

If there is some error in the application package,
it will usually be detected during the `vespa prepare` step and cause an error message.
However, some classes of errors are only detected once the application is deployed.
When redeploying an application, it is therefore recommended watching the vespa log by running:

```
vespa-logfmt -N
```

The new application is active after the INFO message:

```
Switched to the latest deployed set of handlers...;
```

If this message does not appear after a reasonable amount of time
after completion of `vespa activate`,
one will see some errors or warnings instead, that will help debug the application.

### Component load

At deployment or container start, components are constructed.
Construction can fail - to debug, enable more logging (replace "container" as needed with container id):

```
$ vespa-logctl container:com.yahoo.container.di.componentgraph.core.ComponentNode debug=on
  .com.yahoo.container.di.componentgraph.core.ComponentNode   ON  ON  ON  ON  ON  ON  ON OFF
```

Look for "Constructing" and "Finished constructing" in *vespa.log* -
this identifies components that did not construct.

Model downloading failures look like the below and are caused by a fail to download the model to the container:

```
ERROR   container        Container.com.yahoo.jdisc.core.StandaloneMain    JDisc exiting: Throwable caught:
exception=
java.lang.RuntimeException: Not able to create config builder for payload '{
  "tokenizerPath": "\\"\\" https://huggingface.co/Snowflake/snowflake-arctic-embed-l/raw/main/tokenizer.json \\"\\"",
  "transformerModel": "\\"\\" https://huggingface.co/Snowflake/snowflake-arctic-embed-l/resolve/main/onnx/model_int8.onnx \\"\\"",
  "transformerMaxTokens": 512,
  "transformerInputIds": "input_ids",
  "transformerAttentionMask": "attention_mask",
  "transformerTokenTypeIds": "token_type_ids",
  "transformerOutput": "last_hidden_state",
  "normalize": true,
  "poolingStrategy": "cls",
  "transformerExecutionMode": "sequential",
  "transformerInterOpThreads": 1,
  "transformerIntraOpThreads": -4,
  "transformerGpuDevice": 0
}
```

Check urls / names, and that the model can be downloaded in the network the Vespa Container is running.
