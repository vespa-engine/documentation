---
# Copyright Vespa.ai. All rights reserved.
title: "Cloud Config API"
redirect_from:
- /en/cloudconfig/configapi-dev.html
---

This document describes how to use the C++ and Java versions of the
Cloud config API (the 'config API'). This API is used internally in Vespa, and reading
this document is not necessary in order to use Vespa or to develop
Java components for the Vespa container. For this purpose, please refer to
[Configuring components](../configuring-components.html) instead.

Throughout this document, we will use as example an application serving up a configurable message.

## Creating a Config Definition

The first thing to do when deciding to use the config API is to define
the config you want to use in your application.
This is described in the
[configuration file reference](../reference/config-files.html).
Here we will use the definition `motd.def`
from the complete example at the end of the document:

```
namespace=myproject

message string default="NO MESSAGE"
port int default=1337
```

## Generating Source Code and Accessing Config in Code

Before you can access config in your program
you will need to generate source code for the config definition.
Simple steps for how you can generate API code and use the API are provided for:
* [C++](configapi-dev-cpp.html)
* [Java](configapi-dev-java.html) (see also
  [javadoc](https://javadoc.io/doc/com.yahoo.vespa/config-lib))

We also recommend that you read the [general guidelines](#guidelines)
for examples of advanced usage and recommendations for how to use the API.

## Config ID

The config id specified when requesting config is essentially an
identifier of the component requesting config. The config server
contains a config object model, which maps a request for a given
config name and config id to the correct configproducer instance,
which will merge default values from the config definition with config
from the object model and config set in
`services.xml` to produce the final config instance.

The config id is given to a service via the VESPA_CONFIG_ID environment variable.
The [config sentinel](/en/operations-selfhosted/config-sentinel.html) -
see [bootstrapping](/en/application-packages.html#bootstrapping) -
sets the environment variable to the id given by the config model.
This id should then be used by the service to subscribe for config.
If you are running multiple services,
each of them will be assigned a **unique config id** for that service,
and a service should not subscribe using any config id other than its own.

If you need to get config for a services that is not part of the model
(i.e. it is not specified in the services.xml), but that you want
to specify values for in services.xml, use the config id `client`.

## Schema Compatibility Rules

A schema incompatibility occurs if the config class
(for example `MotdConfig` in the C++ and Java sections above)
was built from a different def-file than the one the server is seeing
and using to serve config.
Some such incompatibilities are automatically handled by the config system,
others lead to error.
This is useful to know during development/testing of a config schema.

Let *S* denote a config definition called *motd* which the server is using,
and *C* denote a config definition also called *motd* which the client is using,
i.e. the one that created `MotdConfig` used when subscribing.
The following is the system's behavior:

| Compatible Changes | These schema mismatches are handled automatically by the configserver:   * C is missing a config value that S has:   The server will omit that value from the response. * C has an additional config value with a default value:   The server will include that value in the response. * C and S both have a config value, but the default values differ:   The server will use C's default value. |
| Incompatible Changes | These schema mismatches are not handled by the config server, and will typically lead to error in the subscription API because of missing values (though in principle some consumers of config may tolerate them):   * C has an additional config value without a default value:   The server will not include anything for that value. * C has the type of a config value changed,   for example from string to int: The server will print an error message,   and not include anything for that value.   The user must use an entirely new name for the config   if such a change must be made. |

As with any data schema, it is wise to be conservative about changing it
if the system will have new versions in the future.
For a `def` schema,
removing a config value constitutes a semantic change
that may lead to problems when an older version of some config subscriber asks for config.
In large deployments, the risk associated with this increases,
because of the higher cost of a full restart of everything.

Consequently, one should prefer creating a new config name,
to removing a config value from a schema.

## The Config Server and Object Model

Currently, the object model in the server is created from a series of
input files (`services.xml`). The model is pluggable, and
can generate config id mappings based on your own custom
syntax. See [Developing Cloud
Config Model plugins](cloudconfig-model-plugins.html) for information on how to create model
plugins.

## Creating a Deployable Application Package

The application package consists of the following files:

```
app/services.xml
app/hosts.xml
```

The services file contains the services that is handled by the config model plugin.
The hosts file contains:

```
{% highlight xml %}


    node0


{% endhighlight %}
```

## Setting Up a Running System

To get a running system, first install the cloudconfig package,
start the config server, then deploy the application:
Prepare the application:

```
$ vespa prepare /path/to/app/folder
```

Activate the application:

```
$ vespa activate /path/to/app/folder
```

Then, start vespa. This will start the application and pass it its config id
via the VESPA_CONFIG_ID environment variable.

## Advanced Usage of the Config API

For a simple application, having only 1 config may suffice.
In a typical server application, however,
the number of config settings can become large.
Therefore, we **encourage** that you split the config settings into multiple logical classes.
This section covers how you can use a ConfigSubscriber to subscribe to multiple configs
and how you should group configs based on their dependencies.
Configs can either be:
* Independent static configs
* Dependent static configs
* Dependent dynamic configs

We will give a few examples of how you can cope with these different scenarios.
The code examples are given in a pseudo format common to C++ and Java,
but they should be easy to convert to their language specific equivalents.

### Independent Static Configs

Independent configs means that it does not matter if one of them is
updated independently of the other.
In this case, you might as well use one ConfigSubscriber for each of the configs,
but it might become tedious to check all of them.
Therefore, the recommended way is to manage all of these configs using one ConfigSubscriber.
In this setup, it is also typical to split the subscription phase
from the config check/retrieval part. The subscribing part:

| C++ | ``` {% highlight xml %} ConfigSubscriber subscriber; ConfigHandle::UP fooHandle = subscriber.subscribe(…); ConfigHandle::UP barHandle = subscriber.subscribe(…); ConfigHandle::UP bazHandle = subscriber.subscribe(…); {% endhighlight %} ``` |
| Java | ``` {% highlight xml %} ConfigSubscriber subscriber; ConfigHandle fooHandle = subscriber.subscribe(FooConfig.class, …); ConfigHandle barHandle = subscriber.subscribe(BarConfig.class, …); ConfigHandle bazHandle = subscriber.subscribe(BazConfig.class, …); {% endhighlight %} ``` |

And the retrieval part:

```
if (subscriber.nextConfig()) {
    if (fooHandle->isChanged()) {
        // Reconfigure foo
    }
    if (barHandle->isChanged()) {
        // Reconfigure bar
    }
    if (bazHandle->isChanged()) {
        // Reconfigure baz
    }
}
```

This allows you to perform the config fetch part either in its own
thread or as part of some other event thread in your application.

### Dependent Static Configs

Dependent configs means that one of your configs depends on the value in another config.
The most common is that you have one config which contains the config id
to use when subscribing to the second config.
In addition, your system may need that the configs are updated
to the same **generation**.

{% include note.html content="A generation is a monotonically increasing number which is increased
each time an application is deployed with `vespa deploy`.
Certain applications may require that all configs are of the same generation to ensure consistency,
especially container-like applications.
All configs subscribed to by a ConfigSubscriber are guaranteed to be of the same generation."%}

The configs are static in the sense that the config id used does not change.
The recommended way to approach this is to use a two phase setup,
where you fetch the initial configs in the first phase,
and then subscribe to both the initial and derived configs
in order to ensure that they are of the same generation.
Assume that the InitialConfig config contains two fields
named *derived1* and *derived2*:

| C++ | ``` {% highlight xml %} ConfigSubscriber initialSubscriber; ConfigHandle::UP initialHandle = subscriber.subscribe(…); while (!subscriber.nextConfig()); // Ensure that we actually get initial config. std::auto_ptr initialConfig = initialHandle->getConfig();  ConfigSubscriber subscriber; … = subscriber.subscribe(…); … = subscriber.subscribe(initialConfig->derived1); … = subscriber.subscribe(initialConfig->derived1);         {% endhighlight %} ``` |
| Java | ``` {% highlight xml %} ConfigSubscriber initialSubscriber; ConfigHandle initialHandle = subscriber.subscribe(InitialConfig.class, …); while (!subscriber.nextConfig()); // Ensure that we actually get initial config. InitialConfig initialConfig = initialHandle.getConfig();  ConfigSubscriber subscriber; … = subscriber.subscribe(InitialConfig.class, …); … = subscriber.subscribe(DerivedConfig.class, initialConfig.derived1); … = subscriber.subscribe(DerivedConfig.class, initialConfig.derived1);         {% endhighlight %} ``` |

You can then check the configs in the same way as for independent static configs,
and be sure that all your configs are of the same generation.
The reason why you need to create a new ConfigSubscriber
is that **once you have called nextConfig(),
you cannot add or remove new subscribers**.

### Dependent Dynamic Configs

Dynamic configs mean that the set of configs that you subscribe for
may change between each deployment.
This is the hardest case to solve,
and how hard it is depends on how many levels of configs you have.
The most common one is to have a set of bootstrap configs,
and another set of configs that may change depending on the bootstrap configs
(typically in an application that has plugins).
To cover this case, you can use a class named `ConfigRetriever`.
Currently, it is **only available in the C++ API**.

The ConfigRetriever uses the same mechanisms as the ConfigSubscriber
to ensure that you get a consistent set of configs.
In addition, two more classes called
`ConfigKeySet` and `ConfigSnapshot` are added.
The ConfigRetriever takes in a set of configs used to bootstrap the system in its constructor.
This set does not change.
It then provides one method, `getConfigs(ConfigKeySet)`.
The method returns a ConfigSnapshot of the next generation of bootstrap configs or derived configs.

To create the ConfigRetriever, you must first populate a set of bootstrap configs:

```
{% highlight xml %}
ConfigKeySet bootstrapKeys;
bootstrapKeys.add(configId);
bootstrapKeys.add(configId);
{% endhighlight %}
```

The bootstrap configs are typically configs that will always be needed by your application.
Once you have defined your set,
you can create the retriever and fetch a ConfigSnapshot of the bootstrap configs:

```
ConfigRetriever retriever(bootstrapKeys);
ConfigSnapshot bootstrapConfigs = retriever.getConfigs();
```

The ConfigSnapshot contains the bootstrap config,
and you may use that to fetch the individual configs.
You need to provide the config id and the type in order for the snapshot to know which config to look for:

```
{% highlight xml %}
if (!bootstrapConfigs.empty()) {
    std::auto_ptr bootstrapFoo = bootstrapConfigs.getConfig(configId);
    std::auto_ptr bootstrapBar = bootstrapConfigs.getConfig(configId);
{% endhighlight %}
```

The snapshot returned is empty if the retriever was unable to get the configs.
In that case, you can try calling the same method again.

Once you have the bootstrap configs, you know the config ids for the
other components that you should subscribe for,
and you can define a new key set.
Let's assume that bootstrapFoo contains an array of config ids we should subscribe for.

```
{% highlight xml %}
ConfigKeySet pluginKeySet;
for (size_t i = 0; i < (*bootstrapFoo).pluginConfigId.size; i++) {
    pluginKeySet.add((*bootstrapFoo).pluginConfigId[i]);
}
{% endhighlight %}
```

In this example we know the type of config requested, but this could
be done in another way letting the plugin add keys to the set.

Now that the derived configs have been added to the pluginKeySet,
we can request a snapshot of them:

```
ConfigSnapshot pluginConfigs = retriever.getConfigs(pluginKeySet);
if (!pluginConfigs.empty()) {
    // Configure each plugin with a config picked from the snapshot.
}
```

And that's it. When calling the method without any key parameters,
the snapshot returned by this method may be empty if **the config
could not be fetched within the timeout**,
or **the generation of configs has changed**.
To check if you should call getBootstrapConfigs() again,
you can use the `bootstrapRequired()` method.
If it returns true, you will have to call getBootstrapConfigs() again,
because the plugin configs have been updated, and you need a new bootstrap generation to match it.
If it returns false, you may call getConfigs() again
to try and get a new generation of plugin configs.

We recommend that you use the retriever API if you have a use case like this.
The alternative is to create your own mechanism using two ConfigSubscriber classes,
but this is **not** recommended.

### Advice on Config Modelling

Regardless of which of these types of configs you have,
it is recommended that you always fetch all the configs you need
**before** you start configuring your system.
This is because the user may deploy multiple different version of the config
that may cause your components to get conflicting config values.
A common pitfall is to treat dependent configs as independent,
thereby causing inconsistency in your application when a config update
for config A arrives before config B.
The ConfigSubscriber was created to minimize the possibility of making this mistake,
by ensuring that all of the configs comes from the same config reload.
**Tip:**
Set up your entire *tree* of configs in one thread to ensure consistency,
and configure your system once all of the configs have arrived.
This also maps best to the ConfigSubscriber, since it is not thread safe.
