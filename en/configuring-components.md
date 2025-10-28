---
# Copyright Vespa.ai. All rights reserved.
title: "Configuring Java components"
---

Any Java component might require some sort of configuration,
be it simple strings or integers, or more complex structures.
Because of all the boilerplate code that commonly goes into classes to hold such configuration,
this often degenerates into a collection of key-value string pairs
(e.g. [javax.servlet.FilterConfig](https://docs.oracle.com/javaee/6/api/javax/servlet/FilterConfig.html)).
To avoid this, Vespa has custom, type-safe configuration to all [Container](jdisc/) components.
Get started with the [Developer Guide](developer-guide.html),
try the [album-recommendation-java](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation-java) sample application.

Configurable components in short:
* Create a [config definition](reference/config-files.html#config-definition-files) file
* Use the Vespa [bundle plugin](components/bundles.html#maven-bundle-plugin)
  to generate a config class from the definition
* Inject config objects in the application code

The application code is interfacing with config through the generated code — code and config is always in sync.
This configuration should be used for all state which is assumed to stay constant
for the *lifetime of the component instance*.
Use [deploy](application-packages.html) to push and activate code and config changes.

## Config definition

Write a [config definition](reference/config-files.html#config-definition-files)
file and place it in the application's `src/main/resources/configdefinitions/` directory,
e.g. `src/main/resources/configdefinitions/my-component.def`:

```
package=com.mydomain.mypackage

myCode     int     default=42
myMessage  string  default=""
```

## Generating config classes

Generating config classes is done by the *bundle plugin*:

```
$ mvn generate-resources
```

The generated the config classes are written to `target/generated-sources/vespa-configgen-plugin/`.
In the above example, the config definition file was named *my-component.def*
and its package declaration is *com.mydomain.mypackage*.
The full name of the generated java class will be *com.mydomain.mypackage.MyComponentConfig*

It is a good idea to generate the config classes first,
*then* resolve dependencies and compile in the IDE.

## Using config in code

The generated config class is now available for the component through
[constructor injection](jdisc/injecting-components.html),
which means that the component can declare the generated class as one of its constructor arguments:

```
package com.mydomain.mypackage;

public class MyComponent {

    private final int code;
    private final String message;

    @Inject
    public MyComponent(MyComponentConfig config) {
        code = config.myCode();
        message = config.myMessage();
    }
}
```

The Container will create and inject the config instance.
To override the default values of the config,
[specify](reference/config-files.html#generic-configuration-in-services-xml)
values in `src/main/application/services.xml`, like:

```
<container version="1.0">
    <component id="com.mydomain.mypackage.MyComponent">
        <config name="com.mydomain.mypackage.my-component">
            <myCode>132</myCode>
            <myMessage>Hello, World!</myMessage>
        </config>
    </component>
</container>
```

and the deployed instance of `MyComponent` is constructed using a
corresponding instance of `MyComponentConfig`.

## Unit testing configurable components

The generated config class provides a builder API
that makes it easy to create config objects for unit testing.
Example that sets up a unit test for the `MyComponent` class from the example above:

```
import static com.mydomain.mypackage.MyComponentConfig.*;

public class MyComponentTest {

    @Test
    public void requireThatMyComponentGetsConfig() {
        MyComponentConfig config = new MyComponentConfig.Builder()
                                           .myCode(668)
                                           .myMessage("Neighbour of the beast")
                                           .build();
        MyComponent component = new MyComponent(config);
        …
   }
}
```

The config class used here is simple — see a separate example of
[building a complex configuration object](unit-testing.html#unit-testing-configurable-components).

## Adding files to the component configuration

This section describes what to do if the component needs larger configuration objects that are stored in files,
e.g. machine-learned models, [automata](/en/operations/tools.html#vespa-makefsa) or large tables.
Before proceeding, take a look at how to create
[provider components](jdisc/injecting-components.html#special-components) —
instead of integrating large objects into e.g. a searcher or processor, it might be better to
split the resource-demanding part of the component's configuration into a separate provider component.
The procedure described below can be applied to any component type.

Files can be transferred using either
[file distribution](application-packages.html#file-distribution)
or URL download.
File distribution is used when the files are added to the application package.
If for some reason this is not convenient, e.g. due to size,
origin of file or update frequency, Vespa can download the file and make it available for the component.
Both types are set up in the config definition file.
File distribution uses the `path` config type, and URL downloading the `url` type.
You can also use the `model` type for machine-learned models that can be referenced by both
model-id, used on Vespa Cloud, and url/path, used on self-hosted deployments.
See [the config file reference](reference/config-files.html) for details.

In the following example we will show the usage of all three types.
Assume this config definition, named `my-component.def`:

```
package=com.mydomain.mypackage

myFile path
myUrl url
myModel model
```

The file must reside in the application package, and the path (relative to
the application package root) must be given in the component's configuration in `services.xml`:

```
<container version="1.0">
    <component id="com.mydomain.mypackage.MyComponent">
        <config name="com.mydomain.mypackage.my-component">
            <myFile>my-files/my-file.txt</myFile>
            <myUrl>https://docs.vespa.ai/en/reference/query-api-reference.html</myUrl>
            <myModel model-id="id-provided-by-Vespa-Cloud" url/path="as-above"/>
        </config>
    </component>
</container>
```

An example component that uses these files:

```
package com.mydomain.mypackage;
import java.io.File;

public class MyComponent {
    private final File fileFromFileDistribution;
    private final File fileFromUrlDownload;

    public MyComponent(MyComponentConfig config) {
        pathFromFileDistribution = config.myFile();
        fileFromUrlDownload      = config.myUrl();
        modelFilePath            = config.myModel();
    }
}
```

The `myFile()` and `myModel()` getter returns a `java.nio.Path` object,
while the `myUrl()` getter returns a `java.io.File` object.
The container framework guarantees that these files are fully present at the given location before the component
constructor is invoked, so they can always be accessed right away.

When the client asks for config that uses the `url` or `model` config
type with a URL, the content will be downloaded and cached on the nodes that need it. If
you want to change the content, the application package needs to be updated with a new URL
for the changed content and the application [deployed](application-packages.html),
otherwise the cached content will still be used. This avoids unintended changes to the
application if the content of a URL changes.
