---
# Copyright Vespa.ai. All rights reserved.
title: "Testing"
---

See [automated deployments](https://cloud.vespa.ai/en/automated-deployments.html)
for how to implement system, staging and production verification tests using Vespa Cloud.

## Unit testing using Application

The [Application](https://javadoc.io/doc/com.yahoo.vespa/application/latest/com/yahoo/application/Application.html) class is useful when writing unit tests.
Application uses the application package configuration and set up a container instance for testing.
The [JDisc](https://javadoc.io/doc/com.yahoo.vespa/application/latest/com/yahoo/application/container/JDisc.html) class that is accessed by
the test through [app.getJDisc(clusterName)](https://javadoc.io/page/com.yahoo.vespa/application/latest/com/yahoo/application/Application.html#getJDisc-java.lang.String-) -
this class has methods for using all common [component types](reference/component-reference.html).

Refer to [MetalSearcherTest.java](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation-java/src/test/java/ai/vespa/example/album/MetalSearcherTest.java) for example use.
Notice how the test disables the network layer in order to run tests in parallel.

{% include note.html content="`Application` does not set up *content* nodes, only *container*.
It is hence fully stateless, and intended for unit testing the functionality of application components.
The *ClusterSearcher* will not find any content nodes and log errors if invoked.
Write a *System Test* to test end-to-end features like search."%}

For prototyping, enable the network interface,
instantiate the Container and run requests using a browser:

```
{% highlight java%}
public class ApplicationMain {
  @Test
  public static void main(String[] args) throws Exception {
    try (com.yahoo.application.Application app = com.yahoo.application.Application.fromApplicationPackage(
        FileSystems.getDefault().getPath("src/main/application"),
        Networking.enable)) {
      app.getClass();
      Thread.sleep(Long.MAX_VALUE);
    }
  }
}
{% endhighlight %}
```

## Unit Testing Configurable Components

How to programmatically build configuration instances for unit testing.
Read the [Developer Guide](developer-guide.html) first.

To be able to write self-contained unit tests using configuration classes
generated from a schema, it is necessary to instantiate the configuration
without the use of for instance an external services file. Configuration classes
contain their own builders which are useful for solving exactly this problem. By
using builders, the configuration will be created as an immutable, type-safe
object, exactly the same as used during deployment.

### Configuration schema

Assume the config definition file `demo.def` with the following schema:

```
package=com.mydomain.demo

toplevel[].term string
toplevel[].number int
toplevel[].largenumber long
toplevel[].secondlevel[].name string
toplevel[].secondlevel[].magnitude double

simplename string
simplenumber int
simplevaluearray[] string

coordinate.x double
coordinate.y double
coordinate.name string
```

In other words, the configuration class will be `com.mydomain.demo.DemoConfig`,
and it will contain an array of structures,
a couple of top-level primitives (*simplename* and *simplenumber*),
an array of primitive values (*simplevaluearray*) and a structure (*coordinate*).

### Using configuration builders

All structured objects in the cloud configuration system have their own
Builder as a nested class. So, in the above example, one would get
`DemoConfig.Builder` for the complete configuration class,
`DemoConfig.Toplevel.Builder` for the top-level array,
`DemoConfig.Toplevel.Secondlevel.Builder` for the inner array, and
`DemoConfig.Coordinate.Builder` for the structure.

A configuration object, or substructure, is easiest instantiated using a
constructor accepting the corresponding *Builder* class, an array of structures
should use the constructor accepting an array of *Builder* instances, and an
array of primitive values simply accepts a java.util.Collection of the
corresponding primitive value class:

```
package com.mydomain.demo;

import static org.junit.Assert.*;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.junit.Test;

import static com.mydomain.demo.DemoConfig.Toplevel;
import static com.mydomain.demo.DemoConfig.Toplevel.Secondlevel;
import static com.mydomain.demo.DemoConfig.Coordinate;

public class DemoTest {

    /**
     * An example showing how to build a relatively complex, mixed type
     * configuration including arrays of primitive elements, nested arrays and
     * arrays of structures and so on.
     */
    @Test
    public final void test() {
        // We need use builders to safely create the graph of immutable
        // configuration objects. Each generated configuration class contains
        // the builder for creating an instance of itself. This pattern is
        // repeated for structures. So, in our case, we have four structured
        // levels. The complete configuration class, DemoConfig, the top-level,
        // nested array, Toplevel, the contained array, Secondlevel and the
        // structure Coordinate. This leaves us with using four distinct
        // builder classes: DemoConfig.Builder, Toplevel.Builder,
        // Secondlevel.Builder and Coordinate.Builder.

        // Chained setters are the most used pattern for the builders:
        DemoConfig forTesting = new DemoConfig(new DemoConfig.Builder()
                .simplename("basic chained setter for the string simplename")
                .simplenumber(42)
                .toplevel(buildTopLevelArray())
                .simplevaluearray(
                        Arrays.asList(new String[] { "primitive", "arrays",
                                "are", "easier", "to", "build", "than",
                                "arrays", "of", "structures" }))
                .coordinate(
                        new Coordinate.Builder()
                                .name("have no idea what to call this one")
                                .x(1e300d).y(1e-300d)));
        assertTrue(forTesting != null); // ;)
    }

    /**
     * It is often the more readable solution to use helper methods to build
     * configuration arrays.
     *
     * @return a list of Toplevel.Builder instances
     */
    private List<Toplevel.Builder> buildTopLevelArray() {
        // Note how the Builder classes tend to work on Collection classes and
        // mutable objects, while the config ready for use is bolted down and
        // immutable:
        List<Toplevel.Builder> configArray = new ArrayList<Toplevel.Builder>(3);
        String[] configStrings = new String[] { "a", "b", "c" };
        int[] configNumbers = new int[] { 1, 2, 3 };
        long[] configLargeNumbers = new long[] { 1L + (long) Integer.MAX_VALUE,
                2L + (long) Integer.MAX_VALUE, 3L + (long) Integer.MAX_VALUE };
        for (int i = 0; i < configStrings.length; ++i) {
            configArray.add(new Toplevel.Builder().number(configNumbers[i])
                    .largenumber(configLargeNumbers[i]).term(configStrings[i])
                    .secondlevel(buildSecondLevelArray(2)));
        }
        return configArray;
    }

    /**
     * Once again, the building of an array is delegated to a helper method
     *
     * @param subelements
     *            the length of the returned list
     * @return a list of SecondLevel.Builder
     */
    private List<Secondlevel.Builder> buildSecondLevelArray(int subelements) {
        List<Secondlevel.Builder> builders = new ArrayList<Secondlevel.Builder>(
                subelements);
        for (int i = 0; i < subelements; ++i) {
            builders.add(new Secondlevel.Builder().name(String.valueOf(i))
                    .magnitude((double) i));
        }
        return builders;
    }

}
```
