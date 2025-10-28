---
# Copyright Vespa.ai. All rights reserved.
title: "Component Injection"
---

The Container (a.k.a. JDisc container) implements a dependency injection framework that allows
components to declare arbitrary dependencies on configuration and other components in the application.
This document explains how to write a container component that depends on another component.
See the [reference](../reference/component-reference.html#injectable-components)
for a list of injectable components.

The container relies on auto-injection instead of Guice modules.
All components declared in the container cluster are available for injection,
and the dependent component only needs to declare the dependency as a constructor parameter.
In general, dependency injection involves at least three elements:
* a dependent consumer,
* a declaration of a component's dependencies,
* an injector that creates instances of classes that implement a given dependency on request.

Notes:
* The dependent object describes what software component it depends on to do its work.
  The injector decides what concrete classes satisfy the requirements of the dependent object,
  and provides them to the dependent
* The Container encapsulates the injector, and the consumer and all its
  dependencies are considered to be components.
* The Container only supports constructor injection
  (i.e. all dependencies must be declared in a component's constructor).
* Circular dependencies is not supported.

Refer to the [multiple-bundles sample app](https://github.com/vespa-engine/sample-apps/tree/master/examples/multiple-bundles) for a practical example.

## Depending on another component

A component that depends on another is considered to be a *consumer*.
A component's dependencies is whatever its `@Inject`-annotated
constructor declares as arguments. E.g. the component:

```
package com.yahoo.example;
import com.yahoo.component.annotation.Inject;

public class MyComponent {

    private final MyDependency dependency;

    @Inject
    public MyComponent(MyDependency dependency) {
        this.dependency = dependency;
    }
}
```

has a dependency on the class `com.yahoo.example.MyDependency`.
To deploy `MyComponent`, register `MyDependency` in `services.xml`:

```
<container version="1.0">
    <component id="com.yahoo.example.MyComponent" />
    <component id="com.yahoo.example.MyDependency" />
</container>
```

Upon deployment, the Container will first instantiate `MyDependency`,
and then pass that instance to the constructor of `MyComponent`.
Multiple consumers can take the same dependency.
One can also [inject configuration](../configuring-components.html) to components.

{% include note.html content="A component will be reconstructed only when one of its dependencies,
configuration, or its class changes -
all which only occurs when you re-deploy your application package.
Reconstruction is transitive; if component A depends on component B,
and component B depends on component C,
then a reconfiguration of component B causes a reconfiguration of A, but not of C.
Reconfiguration of C causes a reconstruction of both A and B."%}

### Extending components

When injecting two components when one extends the other,
the dependency injection code does not know which of the two to use as the argument for the parent class.
To resolve this, inject a `ComponentRegistry` (see below), and look up its entries,
like `getComponent(XXX.class.getName())`.

### Specify the bundle

The example above assumes the bundle name can be deducted from the class name.
This is not always the case, and you will get class loading problems like:

```
Caused by: java.lang.IllegalArgumentException: Could not create a component with id
'com.yahoo.example.My'.
Tried to load class directly, since no bundle was found for spec:
com.yahoo.example.Dependency
```

To remedy, specify the jar file (i.e. bundle) with the component:

```
<container version="1.0">
    <component id="com.yahoo.example.MyDependency" bundle="the name in <artifactId> in your pom.xml" />
</container>
```

## Depending on all components of a specific type

Consider the use-case where a component chooses between various strategies,
and each strategy is implemented as a separate component.
Since the number and type of strategies is unknown when implementing the consumer,
it is impossible to make a constructor that lists all of them.
This is where the `ComponentRegistry` comes into play. E.g. the following component:

```
package com.yahoo.example;

public class MyComponent {

    private final ComponentRegistry<Strategy> strategies;

    @Inject
    public MyComponent(ComponentRegistry<Strategy> strategies) {
        this.strategies = strategies;
    }
}
```

declares a dependency on the set of all components registered in `services.xml`
that are instances of the class `Strategy` (including subclasses).
The `ComponentRegistry` class provides accessors for components based
on their [component id](../reference/services-container.html#component).

## Special Components

There are cases where a component cannot be directly injected to its consumers - example:
* The component must be instantiated via a factory method instead of its constructor
* Each consumer must have a unique instance of the dependency class
* The component uses native resources that must be cleaned up
  when the component goes out of scope

For these situations, JDisc supports injection, and optional deconstruction,
via its `Provider` interface:

```
public interface Provider<T> {
    T get();
    void deconstruct();
}
```

`get()` is called by JDisc each time it needs to instantiate the specific component type.
`deconstruct()` is only called after reconfiguring the system with a new application,
where the current provider instance is either removed or replaced due to modified dependencies.

Following the earlier example, declare a provider for the `MyDependency` class,
that returns a new instance for each consumer:

```
package com.yahoo.example;
import com.yahoo.container.di.componentgraph.Provider;

public class MyDependencyProvider implements Provider<MyDependency> {

    @Override
    public MyDependency get() {
        return new MyDependency();
    }

    @Override
    public void deconstruct() { }
}
```

Using this provider, `services.xml` has two instances of `MyComponent`,
each getting a unique instance of `MyDependency`:

```
<container version="1.0">
    <component id="com.yahoo.example.MyDependencyProvider" />
    <component id="my-component-1" class="com.yahoo.example.MyComponent" />
    <component id="my-component-2" class="com.yahoo.example.MyComponent" />
</container>
```

Upon deployment, the Container will first instantiate `MyDependencyProvider`,
and then invoke `MyDependencyProvider.get()` for each instantiation of `MyComponent`.

A provider can declare constructor dependencies, just like any other component.
