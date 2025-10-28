---
# Copyright Vespa.ai. All rights reserved.
title: "Developing Cloud Config Model Plugins"
redirect_from:
- /en/cloudconfig/cloudconfig-model-plugins.html
---

The Cloud Config System (CCS) provides the ability to write custom plugins to the config model.
This allows cloud config consumers to provide a custom syntax for their users to configure the system.

Why create a Plugin?
While creating a config model plugin is not strictly necessary for using CCS,
it increases the usability of the platform.
With a plugin, one can provide custom syntax
that allows the users to configure the system at a higher level of abstraction.

## What problem does it solve

Imagine that you are developing a platform that requires the user to configure
a cluster of servers running some service that can potentially scale to hundreds of servers.
A service may be composed of multiple processes running on the same server,
and those processes might be containers running many components inside them.
The amount of configuration parameters of those processes and components can be huge.
Often, the differences in the configurations might be small,
but just enough that you need to duplicate information
that you later on need to ensure that does not conflict.

Once you have this large amount of configuration parameters,
the logical step is to create some sort of script that automatically generates
a valid configuration based on a few parameters to reduce the amount of human errors.
It is also common to create some form of validation program
that can be run to ensure that the configuration options are valid and does not conflict.
CCS model plugins allows you to take this even further.

In CCS, the configuration is represented as an application package,
which contains various files that can represent the entire system configuration.
However, the configuration is not directly given to the consumer processes and their components.
First, the application package is provided as input to the config server,
which builds a java object model of the system, also known as the *config model*.
The config model is built from a set of *model plugins*
that are able to produce a java object model based on the application package contents.
The object model can then serve the appropriate configuration to a component within a service.

![The config server assembles app config](/assets/img/config-assembly.svg)

### Benefits of writing plugins

The model plugins allows you to create abstractions on top of the low level configuration parameters
that are given to the services.
Here are some specific use cases the model plugins solve:
* The application can be validated to ensure that there are no syntax
  errors in the configuration files
* The configuration files can be checked for conflicting configuration values
* The plugin can allocate resources without the user needing to specify them
  (typically server ports)
* The plugin may support any form of syntax as long as it can generate the object model,
  though using XML allows you to take advantage of many existing library features
  that i.e. make node and port allocation automatic
  or to allow the service to be automatically bootstrapped
* The plugin may provide a high level of abstraction
  that allows the user to change one configuration value,
  while in reality more than one of the configuration values served to the services may change

### Example

Vespa uses CCS with multiple config model plugins.
In Vespa, you can set up a complete system with e.g. this configuration:

```
{% highlight xml %}













    1








{% endhighlight %}
```

The Vespa model plugins ensure that the following is set up based on the above XML:
* A config server cluster
* A log server cluster receiving logs from all the nodes
* A service location broker cluster (vespa-slobrok)
  which maintains the current observed state of all the nodes in the other clusters
* A document processing cluster processing incoming data
* A container cluster set up to receive searches
* A cluster controller cluster which takes singular decisions
  about the current state of nodes in the content cluster
* A distributor cluster managing content distribution
* A search+content cluster storing and searching a partition

In addition, it sets up the wiring between these clusters,
the matching configuration of content and query processing and more.

Going from the simple user-facing config shown above to this complete system specification
is the task of the config model(s).

Technically the models are just Java objects that are instantiated in response
to hitting an element immediately below <services> in *services.xml*
(so the above will create one *admin*, *container* and *content* model),
which are embedded into the config server at runtime
and answers incoming requests for config instances.
During construction of the complete system model
(consisting of multiple such config models),
the models may create additional implicit config models
and exchange information between themselves.
They may also read other files of any format from the application package.

## Building a Model

In this section, we will build a plugin for a simple echo service.
First, we must have a config to serve.
An echo server just needs to know which port it must listen to.
To keep the initial example simple,
we ignore bootstrap and which host the node should run on for now
(see [bootstrapping services](#bootstrapping-services) for an extended example).
The following config is created and stored in
`src/main/resources/configdefinitions` in the plugin source tree:

```
namespace=echo
port int
```

See [Using the Cloud config API](configapi-dev.html)
and the [Configuration File Reference](../reference/config-files.html)
for more information on config definition files.
The service will be configured using:

```
{% highlight xml %}


    1337


{% endhighlight %}
```

To deal with your custom syntax, you first need to create a parser.
The parser class must extend `ConfigModelBuilder`.
The builder is required to specify which XML tags it can handle
via the `handlesElements` method,
and must hook the model into a subclass of `ConfigModel` object
in the `doBuild` method.
Its constructor must forward the class of the model
in order for the superclass to instantiate the correct class and pass it to doBuild:

```
{% highlight xml %}
public class EchoModelBuilder extends ConfigModelBuilder {
    public EchoModelBuilder() {
        super(EchoModel.class);
    }
    @Override
    public List handlesElements() {
        return Arrays.asList(ConfigModelId.fromName("echo"));
    }
    @Override
    public void doBuild(EchoModel configModel, Element spec, ConfigModelContext modelContext) {
        int port = Integer.parseInt(XML.getValue(XML.getChild(spec, "port")));
        configModel.addServer(new EchoServer(configModel.getConfigProducer(), port));
    }
}
{% endhighlight %}
```

The config model represents the model that serves config when requested.
The `ConfigModel` object does not itself serve config,
but is used to proxy request to the appropriate config producers for that model.
For the echo service, the model is simple:

```
{% highlight xml %}
public class EchoModel extends ConfigModel {
    private final List servers = new ArrayList();
    public EchoModel(ConfigModelContext modelContext) {
        super(modelContext);
    }
    public void addServer(EchoServer server) {
        servers.add(server);
    }
    public int numServers() {
        return servers.size();
    }
}
{% endhighlight %}
```

The `EchoServer` is the actual object producing the config,
and is a subclass of the `AbstractConfigProducer` class,
which automatically hooks it into the parent node in the tree,
and causes config requests to be relayed to this producer:

```
public class EchoServer extends AbstractConfigProducer implements EchoConfig.Producer {
    private final int port;
    public EchoServer(AbstractConfigProducer parent, int port) {
        super(parent, "server");
        this.port = port;
    }
    public void getConfig(EchoConfig.Builder builder) {
        builder.port(port);
    }
}
```

The `EchoConfig` class is the one generated
from the config definition file we specified earlier.

Now we have a complete plugin that is able to serve the `echo` config
to anyone who asks with the appropriate *config id*.
The config id of a config producer is relative to its parent.
In this example, the root producers has the id `echo`,
while the server has the id `echo/server`.

## Depending on other models

To create a modular system and facilitate code reuse,
it is possible to depend on and use other models when building your own model.
For instance, if we have a `EchoProxyModel` that handled a `<echoproxy>` tag,
and which is dependent on the `EchoModel` being built first,
we can add it as a constructor argument to signal the dependency
and also allow us to access the `EchoModel` when building the `EchoProxyModel`.

```
public class EchoProxyModel extends ConfigModel {
    public EchoProxyModel(ConfigModelContext context, EchoModel echoModel) {
        // Store away model for use in builder.
    }
}
```

## Unit Testing

Creating a unit test for your plugin is easy.
Mock classes acting as the config model is available and can be used in unit tests:

```
{% highlight xml %}
public class EchoModelTest {
    @Test
    public void testEchoModel() {
        EchoModelBuilder builder = new EchoModelBuilder();
        assertThat(builder.handlesElements().size(), is(1));
        assertThat(builder.handlesElements().get(0).getName(), is("echo"));
        String xml = ""
                   + "1337"
                   + ""
        TestDriver testDriver = new TestDriver().addBuilder(builder);
        TestRoot root = testDriver.buildModel(xml);
        EchoConfig config = root.getConfig(EchoConfig.class, "server");
        assertThat(config.port(), is(1337));

        EchoModel model = testDriver.getConfigModels(EchoModel.class).get(0);
        assertThat(model.numServers(), is(1));
    }
}
{% endhighlight %}
```

The `ConfigModelTester` is a helper class
designed to make unit testing config model builders a breeze.
Any builders required to parse the xml is added to the tester using the `addBuilder` method.
To build the entire model, with all dependencies resolved,
call `buildModel` with either *services.xml*
or an `ApplicationPackage` as input.
The result is a `TestRoot` object which can be used to inspect the entire model.
The config retrieved from the `TestRoot`
is the same as you would get from the config server in a production system.

The MockRoot class mocks the config model producer tree,
and can be used to retrieve the config once the producers have been added to the tree.
Before using it, however, the topology must be frozen by calling
`freezeModelTopology`.

Use [vespa-get-config](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-get-config)
to retrieve in the payload format:

```
$ vespa-get-config -n echo.echo -i echo/server -a path/to/echo.def
```

## Bootstrapping Services

To ease the bootstrapping of services that must be run,
Vespa provides helper classes that help define which hosts a service should run on,
and which performs automatic start/stop of those services based on the config.
We will now extend the echo service to support specifying clusters of echo servers
that are automatically bootstrapped and run on multiple nodes.

In CCS, the term *node* is used about any machine capable of running the services.
It can be an alias for physical host, a VM
or simply a set of parameters describing the resource requirements,
and CCS will acquire a node.
In this example, a traditional host alias specification is used.

First, the XML syntax must be changed in order to support the new requirements
and for the helper classes to recognize them:

```
{% highlight xml %}







{% endhighlight %}
```

This syntax says "Run two echoservers on node0 using port 1337 and 1338, respectively.
Run one echoserver on node1 using port 1337".

Now we need to change the plugin (only shows methods that we have changed):

```
{% highlight xml %}
public class EchoModelBuilder extends ConfigModelBuilder {
    …
    @Override
    public void doBuild(EchoModel configModel, Element spec, ConfigModelContext modelContext) {
        configModel.setCluster(new EchoServerClusterBuilder().build(configModel.getConfigProducer(), spec));
    }
    …
}
{% endhighlight %}
```
```
public class EchoModel extends ConfigModel {
    private EchoServerCluster cluster;
    public EchoModel(ConfigModelContext modelContext) {
        super(modelContext);
    }
    public void setCluster(EchoServerCluster cluster) {
        this.cluster = cluster;
    }
}
```
```
{% highlight xml %}
public class EchoServerClusterBuilder extends DomConfigProducerBuilder {
    @Override
    protected EchoServerCluster doBuild(AbstractConfigProducer ancestor, Element producerSpec) {
        final Element repeatElement = XML.getChild(producerSpec, "repeat");
        final int repeat = repeatElement != null ? Integer.parseInt(XML.getValue(repeatElement)) : -1;

        final EchoServerCluster cluster = new EchoServerCluster(ancestor, "echocluster", repeat);
        for (Element server : XML.getChildren(producerSpec, "server")) {
            EchoServerBuilder builder = new EchoServerBuilder(cluster.numServers());
            cluster.addServer(builder.build(cluster, server));
        }
        return cluster;
    }
}
{% endhighlight %}
```
```
{% highlight xml %}
public class EchoServerCluster extends AbstractConfigProducer implements EchoConfig.Producer {
    private final List echoServers = new ArrayList();
    private final int repeat;
    public EchoServerCluster(AbstractConfigProducer parent, String subId, int repeat) {
        super(parent, subId);
        this.repeat = repeat;
    }
    public void addServer(EchoServer server) {
        echoServers.add(server);
    }
    public int numServers() {
        return echoServers.size();
    }
    @Override
    public void getConfig(EchoConfig.Builder builder) {
        if (repeat >= 0)
            builder.repeat(repeat);
    }
}
{% endhighlight %}
```
```
{% highlight xml %}
public class EchoServerBuilder extends DomConfigProducerBuilder {
    private final int serverNumber;
    public EchoServerBuilder(int serverNumber) {
        this.serverNumber = serverNumber;
    }
    @Override
    protected EchoServer doBuild(AbstractConfigProducer parent, Element element) {
        int port = Integer.valueOf(element.getAttribute("port"));
        return new EchoServer(parent, "server." + serverNumber, port);
    }
}
{% endhighlight %}
```
```
public class EchoServer extends AbstractService implements EchoConfig.Producer {
    private final int port;
    public EchoServer(AbstractConfigProducer parent, String name, int port) {
        super(parent, name);
        this.port = port;
    }
    @Override
    public String getStartupCommand() {
        return "/mydir/bin/echoserver";
    }
    public void getConfig(EchoConfig.Builder builder) {
        builder.port(port);
    }
}
```

By using the helper classes, there is a minimal amount of extra code,
but the gain is huge.
Using CCS, all the echoservers will automatically start when Vespa is run on their respective nodes,
and they will get their appropriate config id passed as an environment variable.
See [Using the Cloud config API](configapi-dev.html)
for examples of how the echo server can subscribe and use the config.

In addition to host management,
the `DomConfigProducerBuilder` class supports parsing config overrides as well.

## Installing model plugins

To make use of the model plugins,
they must be installed on the configserver host before the config server is started.
The default folder for model plugins is `$VESPA_HOME/lib/jars/config-models`.

Having installed the model plugin, the configserver needs to be instructed to load the plugin.
To load the example `EchoModelBuilder`,
add the following to `$VESPA_HOME/conf/configserver-app/config-models/echomodel.xml`

```
{% highlight xml %}



{% endhighlight %}
```
