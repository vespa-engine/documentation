---
# Copyright Vespa.ai. All rights reserved.
title: "Application Packages"
redirect_from:
- /en/cloudconfig/application-packages.html
- /en/cloudconfig/config-introduction.html
- /en/config-introduction.html
---

An *application package* is a set of files in a specific structure that defines a deployable application.
It contains *all* the configuration, components and machine-learned models that is necessary to deploy
and run the application: No configuration is ever done locally on Vespa nodes or over remote APIs.

The application package is a directory, containing at minimum [services.xml](reference/services.html).
Additionally, *services.xml* might consume other files or directories from the application package -
see the [reference](reference/application-packages-reference.html) for a full list.

A change to code and configuration is atomically *deployed* to running instances.
To ensure code and config consistency, [config definition](configuring-components.html#config-definition)
files are compiled to Java code.
With this code/config discrepancies will make the build fail - this is better than production errors.
Read more in [configuring components](configuring-components.html).

{% include note.html content='
See [automated deployments](https://cloud.vespa.ai/en/automated-deployments)
for how to build a pipeline including tests to fully safeguard a new deployment.'%}

## Deploy

Deploy the application package using [vespa deploy](vespa-cli.html#deployment):

```
{% highlight shell %}
# Deploy an application package from cwd
$ vespa deploy

# Deploy an application package from cwd to a prod zone with CD pipeline in Vespa Cloud using deployment.xml
$ vespa prod deploy
{% endhighlight %}
```

At deployment, the application package is validated, and destructive changes rejected.
Read more on how to handle application package changes in
[validation overrides](reference/validation-overrides.html).

Make changes to [schemas](reference/schema-reference.html#modifying-schemas),
like adding a field, then deploy.
Most such changes do not require restarts or re-indexing, if they do a message with instructions
will be in the deploy response - [read more](reference/schema-reference.html#modifying-schemas).

### Convergence

Refer to the [deploy reference](reference/application-packages-reference.html#deploy)
for detailed steps run when deploying an application.
Use the [deploy API](reference/deploy-rest-api-v2.html)
to validate that the configuration is deployed and activated on all nodes, like
*http://localhost:19071/application/v2/tenant/default/application/default/environment/prod/region/default/instance/default/serviceconverge*
- example output:

```
{% highlight json %}
{
    "services": [
    ],
    "url": "https://localhost:19071/application/v2/tenant/default/application/default/environment/prod/region/default/instance/default/serviceconverge",
    "currentGeneration": 2,
    "wantedGeneration": 2,
    "converged": true
}
{% endhighlight %}
```

### Rollback

To roll back an application package, deploy again with the previous version to roll back to - one of:

1. With automation: Revert the code in the source code repository, and let the automation roll out the new version.
2. Download a previous package from Vespa Cloud: Use the
   [console](https://cloud.vespa.ai/en/automated-deployments.html#source-code-repository-integration)
   to pick the good version, download it and deploy again.
   Hover of the [instance](https://cloud.vespa.ai/en/automated-deployments.html#block-windows)
   (normally called "default") to skip the system and staging test to speed up the deployment, if needed.
3. If not using Vespa Cloud, regenerate the good version from source for new deployment.

For self-hosted applications, also see the [deploy API](/en/reference/deploy-rest-api-v2.html#rollback).

### File distribution

The application package can have components and other large files.
When an app is deployed (or more precisely, when the app is *activated*),
these files are distributed to the nodes:
* Components (i.e bundles)
* Files with type *path* and *url* in config, see
  [Adding files to the component configuration](configuring-components.html#adding-files-to-the-component-configuration)
* Machine learned models
* [Constant tensors](reference/schema-reference.html#constant)

When new components or files specified in config are distributed, the container gets a new file reference,
waits for it to be available and switches to new config when all files are available.

![Nodes get config from a config server cluster](/assets/img/config-delivery.svg)

Use [vespa-status-filedistribution](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-status-filedistribution) to check if files have been distributed to all the hosts.

### Deploying remote models

Most application packages are stored as source code in a code repository.
However, some resources are generated and/or too large to store in a code repository,
like models or an [FSA](/en/operations/tools.html#vespa-makefsa).

Machine learned models in Vespa, either [TensorFlow](tensorflow.html),
[ONNX](onnx.html), [XGBoost](xgboost.html), or
[LightGBM](lightgbm.html),
are stored in the application package under the *models* directory.
This might be inconvenient for some applications,
for instance for models that are frequently retrained on some remote system.
Also, models might be too large to fit within the constraints of the version control system.

The solution is to download the models from the remote location during the application package build.
This is simply implemented by adding a step in *pom.xml*
(see [example](https://github.com/vespa-cloud/cord-19-search/blob/main/pom.xml)):

```
{% highlight xml %}



            org.codehaus.mojo
            exec-maven-plugin
            1.4.0


                    download-model
                    generate-resources

                        exec


                        bin/download_models.sh

                            target/application/models
                            MODEL-URL







{% endhighlight %}
```
*bin/download_model.sh* example:

```
#!/bin/bash

DIR="$1"
URL="$2"

echo "[INFO] Downloading $URL into $DIR"

mkdir -p $DIR
pushd $DIR
    curl -O $URL
popd
```

Any necessary credentials for authentication and authorization should be added to this script,
as well as any unpacking of archives (for TensorFlow models for instance).

Also see the [url](reference/config-files.html#url) config type to download resources to container nodes.

## services.xml
*services.xml* specifies the services that makes the application -
each top-level element specifies one service. Example:

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">

    <container id="default" version="1.0">
        <processing/>      <!-- Request-response processors go here. -->
        <search/>          <!-- Searchers go here. -->
        <docproc/>         <!-- DocumentProcessors go here. -->
        <nodes>            <!-- Nodes in the container cluster -->
            <node hostalias="node1"/>
            <node hostalias="node2"/>
            <node hostalias="node3"/>
        </nodes/>
    </container>

    <content id="my-content" version="1.0">
        <redundancy>1</redundancy>
        <documents>         <!-- Add document schemas here -->
            <document type="my-searchable-type" mode="index"/>
            <document type="my-other-type"      mode="index"/>
        </documents>
        <nodes>             <!-- # nodes in the content cluster -->
            <node hostalias="node4" distribution-key="0" />
            <node hostalias="node5" distribution-key="1" />
            <node hostalias="node6" distribution-key="2" />
        </nodes/>
    </content>

</services>
```

Refer to the [services.xml reference](reference/services.html)
for different service types and configuration.

## Component configuration

The application's custom Java code (in *components*) is configured in *services.xml*.
Example, a configured port number for a remote service:

```
    <container id="default" version="1.0">
        <handler id="com.myapp.vespatest.ConfiguredHandler">
            <config name="vespatest.port">
                <port>12345</port>
            </config>
```

Read more in [configuring components](configuring-components.html).

## Node configuration

The problem of configuring nodes can be divided into three parts,
each addressed by different solutions:
* **Node system level configuration:** Configure OS
  level settings such as time zone as well as user privileges on the node.
* **Package management**: Ensure that the correct
  set of software packages is installed on the nodes.
  This functionality is provided by three tools working together.
* **Vespa configuration:** Starts the configured
  set of processes on each node with their configured startup
  parameters and provides dynamic configuration to the modules run by these services.
  *Configuration* here is any data which:
  + can not be fixed at compile time
  + is static most of the time

Note that by these definitions, this allows all the nodes to
have the same software packages (disregarding version differences, discussed later),
as variations in what services are run on each node and in their behavior
is achieved entirely by using Vespa Configuration.
This allows managing the complexity of node variations completely
within the configuration system, rather than across multiple systems.

Configuring a system can be divided into:
* **Configuration assembly:** Assembly of a complete
  set of configurations for delivery from the inputs provided by the
  parties involved in configuring the system
* **Configuration delivery:** Definition of
  individual configurations, APIs for requesting and accessing
  configuration, and the mechanism for delivering configurations from
  their source to the receiving components

This division allows the problem of reliable configuration delivery in
large distributed systems to be addressed in configuration delivery,
while the complexities of assembling complete configurations
can be treated as a vm-local design problem.

An important feature of Vespa Configuration is the nature of the interface
between the delivery and assembly subsystems.
The assembly subsystem creates as output a (Java) object model of the distributed system.
The delivery subsystem queries this model to obtain concrete configurations
of all the components of the system.
This allows the assembly subsystem to accept higher level, and simpler to use,
abstractions as input and automatically derive detailed configurations with the correct interdependencies.
This division insulates the external interface and the components being configured from changes in each other.
In addition, the system model provides the home for logic
implementing node/component instance variations of configuration.

## Configuration assembly

Config assembly is the process of turning the configuration input sources
into an object model of the desired system,
which can respond to queries for configs given a name and config id.
Config assembly for Vespa systems can become complex,
because it involves merging information owned by multiple parties:
* **Vespa operations**
  own the nodes and controls assignment of nodes to services/applications
* **Vespa service providers**
  own services which hosts multiple applications running on Vespa
* **Vespa applications**
  define the final applications running on nodes and shared services

The current config model assembly procedure uses a single source - the *application package*.
The application package is a directory structure containing defined files
and subdirectories which together completely defines the system -
including which nodes belong in the system,
which services they should run and the configuration of these services and their components.
When the application deployer wants to change the application,
[vespa prepare](#deploy) is issued to a config server,
with the application package as argument.

At this point the system model is assembled and validated
and any feedback is issued to the deployer.
If the deployer decides to make the new configuration active,
a [vespa activate](#deploy) is then issued,
causing the config server cluster to switch to the new system model
and respond with new configs on any active subscriptions
where the new system model caused the config to change.
This ensures that subscribers gets new configs timely on changes,
and that the changes propagated are the minimal set
such that small changes to an application package
causes correspondingly small changes to the system.

![The config server assembles app config](/assets/img/config-assembly.svg)

The config model itself is pluggable, so that service providers may write
plugins for assembling a particular service.
The plugins are written in Java, and is installed together with the Vespa Configuration.
Service plugins define their own syntax for specifying services
that may be configured by Vespa applications.
This allows the applications to be specified in an abstract manner,
decoupled from the configuration that is delivered to the components.

## Configuration delivery

Configuration delivery encompasses the following aspects:
* Definition of configurations
* The component view (API) of configuration
* Configuration delivery mechanism

These aspects work together to realize the following goals:
* Eliminate inconsistency between code and configuration.
* Eliminate inconsistency between the desired configuration and the state on each node.
* Limit temporary inconsistencies after reconfiguration.

The next three subsections discusses the three aspects above,
followed by subsections on two special concerns - bootstrapping and system upgrades.

### Configuration definitions

A *configuration* is a set of simple or array key-values with a name and a type,
which can possibly be nested - example:

```
myProperty "myvalue"
myArray[1]
myArray[0].key1 "someValue"
myArray[0].key2 1337
```

The *type definition* (or class) of a configuration object
defines and documents the set of fields a configuration may contain
with their types and default values.
It has a name as well as a namespace.
For example, the above config instance may have this definition:

```
namespace=foo.bar

# Documentation of this key
myProperty string default="foo"

# etc.
myArray[].key1 string
myArray[].key2 int default=0
```

An individual config typically contains a coherent set of settings regarding some topic,
such as *logging* or *indexing*.
A complete system consists of many instances of many config types.

### Component view

Individual components of a system consumes one or more such configs and
use their values to influence their behavior.
APIs are needed for *requesting* configs
and for *accessing* the values of those configs as they are provided.
*Access* to configs happens through a (Java or C++) class
generated from the config definition file.
This ensures that any inconsistency between the fields declared in a config type
and the expectations of the code accessing it are caught at compile time.
The config definition is best viewed as another class with an alternative
form of source syntax belonging to the components consuming it.
A Maven target is provided for generating such classes from config definition types.

Components may use two different methods for *requesting* configurations
(refer to [Config API](/en/contributing/configapi-dev-cpp.html) for C++ code) -
subscription and dependency injection:
**Subscription:** The component sets up
*ConfigSubscriber*, then subscribes to one or more configs.
This is the simple approach, there are [other ways of](/en/contributing/configapi-dev-java.html)
getting configs too:

```
{% highlight java %}
ConfigSubscriber subscriber = new ConfigSubscriber();
ConfigHandle handle = subscriber.subscribe(MyConfig.class, "myId");
if (!subscriber.nextConfig()) throw new RuntimeException("Config timed out.");
if (handle.isChanged()) {
    String message = handle.getConfig().myKey();
    // ... consume the rest of this config
}
{% endhighlight %}
```
**Dependency injection:** The component declares its
config dependencies in the constructor and subscriptions are set up on its behalf.
When changed configs are available a new instance of the component is created.
The advantage of this method is that configs are immutable throughout the lifetime of the component
such that no thread coordination is required.
This method is currently only available in Java using the [Container](/en/jdisc/index.html).

```
{% highlight java %}
public MyComponent(MyConfig config) {
    String myKey = config.myKey();
    // ... consume the rest of this config
}
{% endhighlight %}
```

For unit testing,
[configs can be created with Builders](/en/contributing/configapi-dev-java.html#unit-testing),
submitted directly to components.

### Delivery mechanism

The config delivery mechanism is responsible for ensuring that a new
config instance is delivered to subscribing components,
each time there is a change to the system model causing that config instance to change.
A config subscription is identified by two parameters,
the *config definition name and namespace*
and the [config id](/en/contributing/configapi-dev.html#config-id)
used to identify the particular component instance making the subscription.

The in-process config library will forward these subscription requests to a node local
[config proxy](/en/operations-selfhosted/config-proxy.html),
which provides caching and fan-in from processes to node.
The proxy in turn issues these subscriptions to a node in the configuration server cluster,
each of which hosts a copy of the system model and resolves config requests by querying the system model.

To provide config server failover,
the config subscriptions are implemented as long-timeout gets,
which are immediately resent when they time out,
but conceptually this is best understood as push subscriptions:

![Nodes get config from a config server cluster](/assets/img/config-delivery.svg)

As configs are not stored as files locally on the nodes,
there is no possibility of inconsistencies due to local edits,
or of nodes coming out of maintenance with a stale configuration.
As configuration changes are pushed as soon as the config server cluster allows,
time inconsistencies during reconfigurations are minimized,
although not avoided as there is no global transaction.

Application code and config is generally pulled from the config server -
it is however possible to use the [url](/en/reference/config-files.html#url)
config type to refer to any resource to download to nodes.

### Bootstrapping

Each Vespa node runs a [config-sentinel](/en/operations-selfhosted/config-sentinel.html) process
which start and maintains services run on a node.

### System upgrades

The configuration server will up/downgrade between config versions on the fly on minor upgrades
which causes discrepancies between the config definitions requested
from those produced by the configuration model.
Major upgrades, which involve incompatible changes to the configuration protocol or the system model,
require a [procedure](/en/operations-selfhosted/config-proxy.html).

## Notes

Find more information for using the Vespa config API in the
[reference doc](/en/contributing/configapi-dev.html).

Vespa Configuration makes the following assumptions about the nodes using it:
* All nodes have the software packages needed to run the
  configuration system and any services which will be configured to run on the node.
  This usually means that all nodes have the same software,
  although this is not a requirement
* All nodes have [VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables) set
* All nodes know their fully qualified domain name

Reading this document is not necessary in order to use Vespa or to develop
Java components for the Vespa container - for this purpose, refer to
[Configuring components](/en/configuring-components.html).

## Further reads
* [Configuration server operations](/en/operations-selfhosted/configuration-server.html)
  is a good resource for troubleshooting.
* Refer to the [bundle plugin](/en/components/bundles.html#maven-bundle-plugin)
  for how to build an application package with Java components.
* During development on a local instance it can be handy to just wipe the state completely and start over:
  1. [Delete all config server state](/en/operations-selfhosted/configuration-server.html#zookeeper-recovery) on all config servers
  2. Run [vespa-remove-index](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-remove-index) to wipe content nodes
