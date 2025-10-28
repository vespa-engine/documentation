---
# Copyright Vespa.ai. All rights reserved.
title: "Chained Components"
redirect_from:
- /en/chained-components.html
---

[Processors](../jdisc/processing.html),
[searcher plug-ins](../searcher-development.html) and
[document processors](../document-processing.html)
are chained components.
They are executed serially, with each providing some service or transform,
and other optionally depending on these.
In other words, a chain is a set of components with dependencies.
Javadoc: [com.yahoo.component.chain.Chain](https://javadoc.io/doc/com.yahoo.vespa/chain/latest/com/yahoo/component/chain/Chain.html)

It is useful to read the [federation guide](../federation.html) before this document.

A chained component has three basic differences from a component in general:
* The named services it *provides* to other components in the chain.
* The list of services or checkpoints which the component itself
  should be *before* in a chain, in other words, its dependents.
* The list of services or checkpoints which the component itself
  should be *after* in a chain, in other words, its dependencies.

What a component should be placed before,
what it should be placed after and what itself provides,
may be either defined using Java annotations directly on the component class,
or it may be added specifically to the component declarations
in [services.xml](../reference/services-container.html).
In general, the implementation should have as many of the necessary annotations as practical,
leaving the application specific configuration clean and simple to work with.

## Ordering Components

The execution order of the components in a chain is not defined by the
order of the components in the configuration.
Instead, the order is defined by adding the *ordering constraints* to the components:
* Any component may declare that it `@Provides` some
  named functionality (the names are just labels that have no meaning
  to the container).
* Any component may declare that it must be placed
  `@Before` some named functionality,
* or that it must be placed `@After` some
  functionality.

The container will pick any ordering of a chain consistent with the
constraints of the components in the chain.

Dependencies can be added in two ways. Dependencies which are due to
the code should be added as annotations in the code:

```
import com.yahoo.processing.*;
import com.yahoo.component.chain.dependencies.*;

@Provides("SourceSelection")
@Before("Federation")
@After("IntentModel")
public class SimpleProcessor extends Processor {

    @Override
    public Response process(Request request, Execution execution) {
        //TODO: Implement this
    }
}
```

Multiple functionality names may be specified by using the
syntax `@Provides/Before/After({"A",
"B"})`.

Annotations which do not belong in the code may be added in the
[configuration](../reference/services-container.html):

```
<container version="1.0">

    <processing>
        <processor id="processor1" class="ai.vespa.examples.Processor1" />
        <chain id="default">
            <processor idref="processor1"/>
            <processor id="processor2" class="ai.vespa.examples.Processor2">
                <after>ai.vespa.examples.Processor1</after>
            </processor>
        </chain>
    </processing>

    <nodes>
        <node hostalias="node1" />
    </nodes>
</container>
```

For convenience, components always `Provides` their own
fully qualified class name (the package and simple class name
concatenated, e.g.
`ai.vespa.examples.SimpleProcessor`) and their
simple name (that is, only the class name, like
`SimpleProcessor` in our searcher case), so it is always
possible to declare that one must execute before or after some
particular component. This goes for both general processors, searchers
and document processors.

Finally, note that ordering constraints are just that; in particular
they are not used to determine if a given search chain, or set of
search chains, is “complete”.

## Chain Inheritance

As implied by examples above, chains may inherit other chains
in *services.xml*.

```
{% highlight xml %}















{% endhighlight %}
```

A chain will include all components from the chains named in the
optional `inherits` attribute, exclude from that set all
components named in the also optional
`excludes` attribute and add all the components listed
inside the defining tag. Both `inherits` and
`excludes` are space delimited lists of reference
names.

For search chains, there are two built-in search chains which are especially
useful to inherit from, `native` and `vespa`.
`native` is a basic search chain, containing the
basic functionality most systems will need anyway,
`vespa` inherits from `native` and adds a
few extra searchers which most installations containing Vespa backends will need.

```
{% highlight xml %}












{% endhighlight %}
```

## Unit Tests

A component should be unit tested in a chain containing the components it depends on.
It is not necessary to run the dependency handling framework to achieve that,
as the `com.yahoo.component.chain.Chain` class has several
constructors which are easy to use while testing.

```
Chain<Searcher> c = new Chain(new UselessSearcher("first"),
        new UselessSearcher("second"),
        new UselessSearcher("third"));
Execution e = new Execution(c, Execution.Context.createContextStub(null));
Result r = e.search(new Query());
```

The above is a rather useless test, but it illustrates how the basic
workflow can be simulated. The constructor will create a chain with
supplied searchers in the given order (it will not analyze any annotations).

## Passing Information Between Components

When different searchers or document processors depend on shared classes or field names,
it is good practice defining the name only in a single place.
An [example](../searcher-development.html#passing-information-between-searchers) in the searcher development introduction illustrates an easy way to do that.

## Invoking a Specific Search Chain

The search chain to use can be selected in the request, by adding the request parameter:
`searchChain=myChain`

If no chain is selected in the query, the chain called
`default` will be used. If no chain called
`default` has been configured, the chain called
`native` will be used. The *native* chain is
always present and contains a basic set of searchers needed in most applications.
Custom chains will usually inherit the native chain to include those searchers.

The search chain can also be set in a [query profile](../query-profiles.html).

## Example: Configuration

Annotations which do not belong in the code may be added in the configuration,
here a simple example with
[search chains](../reference/services-search.html#chain):

```
<container version="1.0">
    <search>
        <chain id="default" inherits="vespa">
            <searcher id="simpleSearcher" bundle="the name in artifactId in pom.xml" />
        </chain>
        <searcher id="simpleSearcher"
                  class="ai.vespa.examples.SimpleSearcher"
                  bundle="the name in artifactId in pom.xml" >
            <before>Cache</before>
            <after>Statistics</after>
            <after>Logging</after>
            <provides>SimpleTest</provides>
        </searcher>
    </search>
    <nodes>
        <node hostalias="node1" />
    </nodes>
</container>
```

And for [document processor chains](../reference/services-docproc.html), it becomes:

```
<container version="1.0">
    <document-processing>
        <chain id="default">
            <documentprocessor id="ReplaceInFieldDocumentProcessor">
                <after>TextMetrics</after>
            </documentprocessor>
        </chain>
    </document-processing>
    <nodes>
        <node hostalias="node1"/>
    </nodes>
</container>
```

For searcher plugins the class
[com.yahoo.search.searchchain.PhaseNames](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/searchchain/PhaseNames.html)
defines a set of checkpoints third party searchers may use to help
order themselves when extending the Vespa search chains.

Note that ordering constraints are just that; in particular
they are not used to determine if a given search chain, or set of
search chains, is “complete”.

## Example: Cache with async write

Use case: In a search chain, do early return and do further search asynchronously using
[ExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ExecutorService.html).

Pseudocode: If cache hit (e.g. using Redis), just return cached data.
If cache miss, return null data and let the following searcher finish further query and write back to cache:

```
{% highlight java %}
public Result search(Query query, Execution execution) {
    // cache lookup

    if (cache_hit) {
        return result;
    }
    else {
        execution.search(query);  // invoke async cache update searcher next in chain
        return result;
    }
}
{% endhighlight %}
```
