---
# Copyright Vespa.ai. All rights reserved.
title: "Using the C++ Cloud config API"
redirect_from:
- /en/cloudconfig/configapi-dev-cpp.html
---

This document describes how to use the C++ cloud config API.
We are assuming you have created a
[config definition file](configapi-dev.html) (def file),
which is the schema for one of your configs.
Developing with the C++ Cloud Config API requires you to
* Generate C++ code from your config definitions
* Subscribe to the config using the API

## Generating Config

In my example application, I have the following hierarchy related to config:

```
src/config-defs/motd.def
```

Generate code while standing in the `src/` folder:

```
$ make-config.pl $(pwd) $(pwd)/config-defs/motd.def
```

This will generate a *config-defs/config-motd.h* and *config-defs/config-motd.cpp*.
These classes are immutable pure data objects that you can use to configure your application.
The objects may be copied.
In this example, the class MotdConfig is the generated config object.

## Subscribing and Getting Config

To retrieve the config in your application, create a ConfigSubscriber.
A ConfigSubscriber is capable of subscribing to one or more configs.
The subscribe method takes an optional parameter as well, a timeout.
If the ConfigSubscriber was unable to subscribe within the timeout,
it will throw a ConfigRuntimeException.
To use the API, you must include the header of the generated classes
as well as the header shown in the example below.
The config API resides in the `config` namespace:

```
{% highlight cpp %}
#include

using namespace config;

…

ConfigSubscriber s;
try {
    std::unique_ptr> handle = s.subscribe("my.config.id");
} catch (ConfigRuntimeException & exception) {
    // Handle exception
}
{% endhighlight %}
```

Note that a ConfigSubscriber is **NOT thread safe**.
It is up to the API user to ensure that the ConfigSubscriber is not used by multiple threads.

Once you have subscribed to all the configs you need,
you may invoke the nextConfig() call on the ConfigSubscriber:

```
s.nextConfig(1000);
```

Given N subscriptions, the nextConfig call will wait up to 1 second for 1 to N configs to change.
If they have changed, it returns true. If not, it returns false.
See [config API guidelines](configapi-dev.html#guidelines)
for a more advanced usage of the ConfigSubscriber.

{% include important.html content="One **can not** subscribe or
unsubscribe to more configs once nextConfig() is called.
This means that in order to change the set of subscribed configs,
one must create a new ConfigSubscriber with the new set."%}

Having called nextConfig(), the ConfigHandle can be asked for the current config:

```
{% highlight xml %}
std::unique_ptr cfg = handle->getConfig();
{% endhighlight %}
```

This will retrieve the currently available config.
If the subscribe calls succeeded and valid configs was returned by the config server,
you are guaranteed that it will give you a correct config.
For getting updates, the `nextConfig` method can be used like:

```
{% highlight xml %}
if (s.nextConfig(3000)) {
    std::unique_ptr cfg = handle->getConfig();
}
{% endhighlight %}
```

The method ensures that whatever getConfig() returns next will be the latest config available.
nextConfig has a timeout parameter, and will return false if timeout was reached,
or true if a new generation of configs was deployed, and at least 1 of them changed.

When subscribing to multiple configs, a natural use case is to check which of the configs changed.
Therefore, the ConfigHandle class also contains a `isChanged` method.
This method returns true if the previous call to nextConfig() resulted in a change, false if not.

### Selecting Config Source

The ConfigSubscriber constructor may also be passed a `ConfigContext` object.
A context can be used to share resources with multiple ConfigSubscriber objects
and select the config source.
The context is passed a `SourceSpec` parameter, which specifies the source of the config.
The different spec types are:
* `ServerSpec`, the default spec
* `ConfigSet`, used for subscribing to a set of config objects
* `DirSpec`, used for subscribing to config files in a directory
* `FileSpec`, used for subscribing to a single file
* `RawSpec`, used for subscribing to a config value specified directly

Most users will use the default ServerSpec, or ConfigSet.

## Unit Testing

To help with unit testing, each config type has a corresponding builder type.
For instance, given `FooConfig and BarConfig` generated config classes,
`FooConfigBuilder and BarConfigBuilder` should also be available as mutable versions.
The builders can then be added to a `ConfigSet`:

```
ConfigSet set;
FooConfigBuilder fooBuilder;
BarConfigBuilder barBuilder;
set.addBuilder("id1", &fooBuilder);
set.addBuilder("id1", &barBuilder);
fooBuilder.foobar = 13;
barBuilder.barfoo = 12;
```

Having populated the set and set values on the builders,
one must create a context containing the set:

```
IConfigContext::SP ctx(new ConfigContext(set));
```

Once the context is created, it can be passed to the ConfigSubscriber:

```
{% highlight xml %}
ConfigSubscriber subscriber(ctx);
ConfigHandle::UP fooHandle =
subscriber.subscribe("id1");
ConfigHandle::UP barHandle =
subscriber.subscribe("id1");
subscriber.nextConfig() // returns true first time
{% endhighlight %}
```

Once having subscribed, nextConfig and nextGeneration methods will work as normal.
If you need to update a field to test reload,
you can change the field of one of the builders and call reload on the context:

```
subscriber.nextConfig() // should return false if called before
fooBuilder.foobar = 188;
ctx->reload();
subscriber.nextConfig() // should return true now
```

How the config id relates to the application package deployed is
covered in the main [Config API](configapi-dev.html) document.

We also provide some helper classes such as the `ConfigGetter`
to test the config itself.

{% include note.html content="When using builders for unit testing,
there is an underlying assumption that the configured application have subscribed to all configs
before the builders are mutated.
Otherwise, the application may try to retrieve an inconsistent configuration.
In general, try to design the application so that one can verify configuration changes in tests."%}

## Printing Config

All config objects can be printed, and the API supports several ways of doing so.
To print config, you need to include <config/print.h>.
Config can be printed with any class implementing the `ConfigWriter` interface.
A `ConfigWriter` has a write method that takes any config class as input,
and writes it somewhere.
The following classes are provided:
* `FileConfigWriter` - Can write a config to a file
* `OstreamConfigWriter` - Can write a config to a C++ ostream

A `ConfigWriter` also supports another parameter in the write method,
a `ConfigFormatter`. Currently, we provide two formatters:
* `FileConfigFormatter` - Formats the config as the old
  config payload format. This is the **default** formatter
* `JsonConfigFormatter` - Formats the config as JSON

The `FileConfigFormatter` is the default formatter if none is specified.

Example: Writing the config `MyConfig` to a file as JSON:

```
MyConfig foo;
FileConfigWriter writer("myfile.json");
writer.write(foo, JsonConfigFormatter());
```
