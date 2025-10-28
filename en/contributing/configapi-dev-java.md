---
# Copyright Vespa.ai. All rights reserved.
title: "Developing with the Java Cloud Config API"
redirect_from:
- /en/cloudconfig/configapi-dev-java.html
---

Assumption: a [def file](configapi-dev.html),
which is the schema for one of your configs, is created and
put in `src/main/resources/configdefinitions/`.

To generate source code for the def-file, invoke the
`config-class-plugin` from *pom.xml*,
in the `<build>`, `<plugins>` section:

```
{% highlight xml %}

  com.yahoo.vespa
  config-class-plugin
  ${vespa.version}


      config-gen

        config-gen




{% endhighlight %}
```

The generated classes will be saved to
`target/generated-sources/vespa-configgen-plugin`, when the
`generate-sources` phase of the build is executed.
The def-file [`motd.def`](configapi-dev.html)
is used in this tutorial, and a class called `MotdConfig`
was generated (in the package `myproject`).
It is a subtype of `ConfigInstance`.

When using only the config system (and not other parts of Vespa or
the JDisc container), pull in that by using this in pom.xml:

```
{% highlight xml %}

  com.yahoo.vespa
  config
  ${vespa.version}
  provided

{% endhighlight %}
```

## Subscribing and getting config

To retrieve the config in the application, create a `ConfigSubscriber`.
A `ConfigSubscriber` is capable of subscribing to one or more configs.
The example shown here uses simplified error handling:

```
{% highlight java %}
ConfigSubscriber subscriber = new ConfigSubscriber();
ConfigHandle handle = subscriber.subscribe(MotdConfig.class, "motdserver2/0");
if (!subscriber.nextConfig()) throw new RuntimeException("Config timed out.");
if (handle.isChanged()) {
  String message = handle.getConfig().message();
  int port = handle.getConfig().port();
}
{% endhighlight %}
```

Note that `isChanged()` always will be true after the first call to `nextConfig()`,
it is included here to illustrate the API.

In many cases one will do this from a thread which loops the
`nextConfig()` call, and reconfigures your application if
`isChanged()` is true.

The second parameter to `subscribe()`, *"motdserver2/0"*,
is the [config id](configapi-dev.html#config-id).

If one `ConfigSubscriber` subscribes to multiple configs,
`nextConfig()` will only return true if the configs are of
the same generation, i.e. they are "in sync".

See the
[com.yahoo.config](https://javadoc.io/doc/com.yahoo.vespa/config-lib) javadoc for details. Example:

```
{% highlight xml %}
ConfigSubscriber subscriber = new ConfigSubscriber();
ConfigHandle motdHandle = subscriber.subscribe(MotdConfig.class, "motdserver2/0");
ConfigHandle anotherHandle = subscriber.subscribe(AnotherConfig.class, "motdserver2/0");
if (!subscriber.nextConfig()) throw new RuntimeException("Config timed out.");
// We now have a synchronized new generation for these two configs.
if (motdHandle.isChanged()) {
  String message = motdHandle.getConfig().message();
  int port = motdHandle.getConfig().port();
}
if (anotherHandle.isChanged()) {
  String myfield = anotherHandle.getConfig().getMyField();
}
{% endhighlight %}
```

## Simplified subscription

In cases like the first example above, where you only subscribe to one config, you may also subscribe using the
`ConfigSubscriber.SingleSubscriber` interface. In this case, you define a `configure()`
method from the interface, and call a special `subscribe()`. The method will start a dedicated config
fetcher thread for you. The method will throw an exception in the user thread if initial configuration fails,
and print a warning in the config thread if it fails afterwards. Example:

```
{% highlight xml %}
public class MyConfigSubscriber implements ConfigSubscriber.SingleSubscriber {

  public MyConfigSubscriber(String configId) {
    new ConfigSubscriber().subscribe(this, MotdConfig.class, configId);
  }

  @Override
  public void configure(MotdConfig config) {
    // configuration logic here
  }
}
{% endhighlight %}
```

The disadvantage to using this is that one cannot implement custom error handling
or otherwise track config changes. If needed, use the generic method above.

## Unit testing config

When instantiating a [ConfigSubscriber](https://javadoc.io/doc/com.yahoo.vespa/config/latest/com/yahoo/config/subscription/ConfigSubscriber.html),
one can give it a [ConfigSource](https://javadoc.io/doc/com.yahoo.vespa/config/latest/com/yahoo/config/subscription/ConfigSource.html).
One such source is a `ConfigSet`. It consists of a set of `Builder`s.
This is an example of instantiating a subscriber using this -
it uses 2 types of config, that were generated from files
`app.def` and `string.def`:

```
ConfigSet myConfigs = new ConfigSet();
AppConfig.Builder a0builder = new AppConfig.Builder().message("A message, 0").times(88);
AppConfig.Builder a1builder = new AppConfig.Builder().message("A message, 1").times(89);
myConfigs.add("app/0", a0builder);
myConfigs.add("app/1", a1builder);
myConfigs.add("bar", new StringConfig.Builder().stringVal("StringVal"));
ConfigSubscriber subscriber = new ConfigSubscriber(myConfigs);
```

To help with unit testing, each config type has a corresponding builder type.
The `Builder` is mutable whereas the `ConfigInstance` is not.
Use this to set up config fixtures for unit tests.
The `ConfigSubscriber` has a `reload()` method
which is used in tests to force the subscriptions into a new
generation. It emulates a `vespa activate` operation after
you have updated the `ConfigSet`.

A full example can be found in
[ConfigSetSubscriptionTest.java](https://github.com/vespa-engine/vespa/blob/master/config/src/test/java/com/yahoo/config/subscription/ConfigSetSubscriptionTest.java).
