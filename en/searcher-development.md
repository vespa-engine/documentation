---
# Copyright Vespa.ai. All rights reserved.
title: "Searcher Development"
---

The *Container* is the home for all global processing of
user actions (represented as queries) and their results.
It provides a development and hosting environment for processing
[components](jdisc/container-components.html),
and a model for composing such components developed by multiple development teams into a functional whole.

This document describes how to develop and deploy Searcher components.
To get started with development,
see the [Developer Guide](developer-guide.html).
For reference, see the [Container javadoc](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/package-summary.html),
and the [services.xml reference](reference/services-processing.html#chain).

Best practise for queries is submitting the user-generated query as-is to Vespa,
then use Searcher components to implement additional logic.
Refer to the [Query HTTP API](query-api.html#http).

![Searcher component in Vespa overview](/assets/img/vespa-overview-searcher.svg)

## Searchers

The components of the search container are called *Searchers*.
A searcher is a component - usually deployed as part of an OSGi bundle -
which extends the class `com.yahoo.search.Searcher`.
All Searchers must implement a single method:

```
{% highlight java %}
public Result search(Query query, Execution execution);
{% endhighlight %}
```

When the container receives a request, it will create a Query representing it
and execute a configured list of such Searcher components.
This is done by calling the `search()` method on the first searcher in the list.
That searcher is responsible for passing the call to the next searcher in the list (or not, as it sees fit).
This is done by calling `search()` on the Executor given,
which keeps track of where we are in the list of Searchers.
Hence, this is a noop searcher implementation:

```
{% highlight java %}
public Result search(Query query, Execution execution) {
    return execution.search(query);
}
{% endhighlight %}
```

Eventually the search call will reach the end of the list of searchers.
The last searcher in the list may create a Result (somehow),
which is now passed back up the call chain until it reaches the top.
The container will then translate that Result back to a response to the incoming request.

As is evident from this description, this is a synchronous model,
where each request is processed in a dedicated worker thread until the result is returned.
This synchronous model is implemented with [multi-threading of individual searchers](#keeping-state-in-searchers).

The single searcher method is sufficient to express all kinds of functionality, e.g.:
* A *query processor* will modify the query, then pass it on
  to the next searcher.
* A *result processor* will pass the query on to get the
  result, then modify the result before returning it.
* A *result producer* which produces a result by some
  internal lookup or (more typically) by sending a network request
  to a backend will translate the query to the desired execution and
  instantiate and return a Result holding the outcome.
* A *workflow* might pass the query on multiple times in a
  loop and gradually build up a Result for return from the Results
  received from each Query execution, or choose to pass a particular
  Query in an if-else loop etc.

## Queries and Results

The **Query** in the search container is the container of all the
information needed to create a result to the request, including:
* The parameters received in the request, including the user's query
  string, or chosen action.
* The parameters in the chosen [query
  profile](query-profiles.html), if any.
* The desired execution, including the boolean query tree. This
  information is gradually created from the request and query
  profile by Searcher components.
* Any objects of any type containing information created by
  Searchers along the way.

The **Result** encapsulates all the data generated from a Query.
The Result contains a composite tree of Hit objects organized in lists called HitGroups
(the Result points to the topmost group).
Each Hit contains some particular data item which is deemed relevant to the Query.
The Hit objects has a general key-value storage,
but are also polymorphic to support representing more structured information.
See the  [inspecting
structured data](reference/inspecting-structured-data.html) documentation for details about handling structured information in a Searcher.

As Hits may be hierarchically organized into hit lists,
the Result object is capable of representing any organization of the results.
For example, in a federated system the hits are initially organized in one hit group per source.
Upstream searchers may reorganize this into something that fits the user's need better,
e.g a single blended group, or one group per likely interpretation of the query etc.

## Search Chains

The lists of searchers mentioned above are called *search chains*.
Search chains are a special case of the  [general component chains](components/chained-components.html).
A search chain is nothing more than a list of searcher instances having an id.
The search chains are typically not created for every query but are part of the configuration.
Multiple ones may exist at the same time, the chain to execute may be specified in the request.
If nothing is specified, a default one is used.
The same Searcher instance may exist in multiple search chains,
which is why the Execution object is responsible for knowing the next Searcher to invoke in a particular request.

Search chains may also be executed programmatically (typically from a Searcher),
synchronously or asynchronously:

```
{% highlight java %}
// Get a chain by id
SearchChain myChain = execution.searchChainRegistry().getComponent("myChain");

// Execute it in the same thread
Result result = new Execution(myChain, execution.context()).search(query);

// ... or in another thread
Execution settings = new Execution(myChain, execution.context());
FutureResult futureResult = new AsyncExecution(settings).search(query);
FutureResult otherFutureResult = new AsyncExecution(settings).search(otherQuery);
{% endhighlight %}
```

Asynchronous execution is useful in cases like [federation](federation.html),
where a searcher forks a Query to multiple search chains in parallel,
each getting results from a particular source.
Also, as in the example, it is allowed to use the same Execution instance to construct
multiple AsyncExecution instances, as the state is only copied from the constructor argument.

The execution order of the searchers in a chain are not ordered explicitly,
but by [ordering constraints](components/chained-components.html)
declared in the searchers or their configuration.
Also read the [search reference](reference/services-search.html).

### Writing a Searcher

Example of a complete searcher:

```
{% highlight java %}
package com.yahoo.search.example;

import com.yahoo.search.*;
import com.yahoo.search.result.Hit;
import com.yahoo.search.searchchain.Execution;

/**
 * A searcher adding a new hit.
 */
public class SimpleSearcher extends Searcher {

    public Result search(Query query, Execution execution) {
        Result result = execution.search(query); // Pass on to the next searcher to get results
        Hit hit = new Hit("test");
        hit.setField("message", "Hello world");
        result.hits().add(hit);
        return result;
    }

}
{% endhighlight %}
```

The container will create one or more instances of this class
and place it in the desired search chain(s) to serve queries, as specified in
 [the configuration](jdisc/container-components.html#adding-component-to-application-package).
The first line in this searcher forwards the query to whatever is the next searcher in the chain this is a part of.
This will eventually produce a Result, which is modified and then passed back to the previous searcher in this chain.
The container will create a new instance of this searcher only when it is reconfigured,
so any data needed by the searcher can be read and prepared from a constructor in the searcher.
Constructors may also accept [configuration](jdisc/container-components.html#dependency-injection),
as any other pluggable component.

Find the full API available to searchers in the
[Search Container Javadoc](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/package-summary.html).

### Testing a Searcher

Before there is any point in testing a searcher in a real system,
it should pass a set of unit tests which test it in isolation
or together with the few searchers it interacts with.
To do this, we can write unit tests which programmatically
sets up a search chain containing the searcher to be tested, the searchers it interacts with (if any)
and a searcher which produces mock results appropriate for the tests.
Here is a simple example testing the Searcher above:

```
{% highlight java %}
package com.yahoo.search.example.test;

import com.yahoo.search.*;
import com.yahoo.search.searchchain.*;
import com.yahoo.search.example.SimpleSearcher;

public class SimpleSearcherTestCase extends junit.framework.TestCase {

    public void testBasics() {
        // Create chain
        Chain searchChain = new Chain(new SimpleSearcher());

        // Create an empty context, in a running container this would be
        // populated with settings used by different searcher. Tests must
        // set this according to their own requirements.
        Execution.Context context = Execution.Context.createContextStub(null);
        Execution execution = new Execution(searchChain, context);

        // Execute it
        Result result = execution.search(new Query("search/?query=some test query"));

        // Assert the result has the expected hit by scanning for the ID
        assertNotNull(result.hits().get("test"));
    }

}
{% endhighlight %}
```

In this case, no searcher producing mock results is needed
because the searcher we are testing does not care what the Result contains.
If the search chain ends with a searcher which produces no result,
the framework will simply return an empty result, which is what happens in this case.
A test adding a mock searcher producing results are shown in
[federation](federation.html#unit-testing-the-result-processor).

To write unit tests of the whole application package,
see the [Developer Guide](developer-guide.html).

### Deploying a Searcher

Once the searcher passes unit tests, it can be deployed to the Vespa system hosting it.
The procedure is the same as described in
[deploying a component](jdisc/container-components.html#deploying-a-component).
First [build the component jar](jdisc/container-components.html#building-the-plugin-jar).
To include the searcher in *services.xml*, define a search chain and add the searcher to it - example:

```
{% highlight xml %}
xml version="1.0" encoding="utf-8" ?
















{% endhighlight %}
```

This defines the search chain `default`,
which will be used in queries when no other chain is explicitly specified.
The searcher id above is resolved to the component bundle jar we added by the symbolic name in the manifest,
and to the right class within the bundle by the class name.
By keeping all these three the same, we keep things simple,
but more advanced use where this is possible is also supported, see later sections.

See the [search chains reference](reference/services-search.html#chain).

Example *hosts.xml*:

```
{% highlight xml %}
xml version="1.0" encoding="utf-8" ?


        node1


{% endhighlight %}
```

By creating a directory containing *services.xml*,
*hosts.xml* and *components/Simplesearcher.jar*,
that directory becomes a complete application package containing a bundle,
which can now be deployed to a Vespa instance.

After deployment, query the application:
[http://localhost:8080/search?query=best](http://localhost:8080/search/?query=best).

### Testing a Searcher with an Application

A searcher can also be tested running inside a container.
Create an instance from the *container* part of the *services.xml* file above:

```
{% highlight java %}
import com.yahoo.component.ComponentSpecification;
import com.yahoo.application.container.JDisc;
import com.yahoo.application.Networking;

import com.yahoo.search.Query;
import com.yahoo.search.Result;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertNotNull;

public class ContainerTest {
    @Test
    public void testSearch() {
        String servicesXml =
                "" +
                "  " +
                "    " +
                "      " +
                "    " +
                "  " +
                "";
        try (JDisc container = JDisc.fromServicesXml(servicesXml, Networking.disabled)) {
            Result result = container.search().process(ComponentSpecification.fromString("default"),
                                                       new Query("search/?query=test+query"));
            assertNotNull(result.hits().get("test"));
        }

    }
}
{% endhighlight %}
```

Examine which searchers are in a chain and their ordering:

```
{% highlight java %}
ChainRegistry chains = container.searching().getChains();
Chain defaultChain = chains.getComponent("default");

boolean foundSimpleSearcher = false;
for (Searcher searcher: defaultChain.components()) {
    if ("com.yahoo.search.example.SimpleSearcher".equals(searcher.getClassName()))
        foundSimpleSearcher = true;
}

assertTrue("No instance of SimpleSearcher found in the default chain", foundSimpleSearcher);
{% endhighlight %}
```

## Passing information between Searchers

The query object is used to pass information between searchers.
A part of the query is a general property store which may hold any object.
Any values set in the request or in the query profile is available through these properties,
but in addition searchers may add any objects they create.
This is useful when some searcher component is producing information later consumed by some other. Example:

```
{% highlight java %}
import com.yahoo.search.*;
import com.yahoo.search.searchchain.*;

@Provides(SomeObject.NAME)
public class ProducerSearcher extends Searcher {

    public Result search(Query query, Execution execution) {
        SomeObject.setTo(query.properties(), new SomeObject(query));
        return execution.search(query); // Pass to next in chain
    }
}
{% endhighlight %}
```
```
{% highlight java %}
import com.yahoo.search.*;
import com.yahoo.search.searchchain.*;

@After(SomeObject.NAME)
public class ConsumerSearcher extends Searcher {

    public Result search(Query query, Execution execution) {
        SomeObject someObject = SomeObject.getFrom(query.properties());
        ...
        return execution.search(query); // Pass to next in chain
    }
}
{% endhighlight %}
```
```
{% highlight java %}
import com.yahoo.search.query.Properties;

public final class SomeObject {
    public static final String NAME = "SomeObject";

    public static void setTo(Properties properties, SomeObject value) {
        properties.set(NAME, value);
    }

    @SuppressWarnings("unchecked")
    public static SomeObject getFrom(Properties properties) {
        return (SomeObject) properties.get(NAME);
    }
}
{% endhighlight %}
```

This code illustrates two idioms such searchers should follow when exchanging data:
* The key to an object should be exactly the same as the short name
  of the object stored.
* The searcher should declare that it *provides* exactly the
  same name (and of course the consumers must declare that they need
  to be *after* the object is provided).

When it does not cause unwanted dependencies,
it is recommended to wrap the property get and put in a (static)
`getFrom` and `setTo` method in the stored object,
to allow storage and lookup without having to mention the key unnecessarily outside the object.

Note that the objects are passed as regular in-memory references,
so there is no noticeable overhead in this.
However, in some situations (like when federating to multiple sources) the query will need to be cloned.
The query will then attempt to clone the added properties.
Those that implement Cloneable will have clone called, the rest will be copied by reference.

{% include important.html content="It is important that objects added to the query which contains mutable state
are **deep cloned** to avoid bugs."%}

On the other hand, cloning objects which should not change is wasteful,
they should be copied by reference.
Hence, the guidelines are:
* Objects which should not be modified downstream should enforce
  immutability when added to the Query, either by not offering any
  mutator methods, or by being *frozen* (in a state where any
  mutator call causes an exception). Objects which *enforces*
  mutability should either not implement Cloneable or should implement a shallow clone.
* Objects which should support downstream modifications **must**
  implement Cloneable and offer a clone method which performs deep copying.

### Query Context

In some cases there is a need for passing information between searchers beyond those who see the same Query object.
For this purpose, the Query provides a QueryContext object which provides a
shared data view to all Searchers working on the same request.
The context provides (among other things) a facility for setting properties (named objects).
The context can be accessed safely from all the threads working on a request
without incurring synchronization overhead (with some caveats),
but provides linear, not constant lookup time.
To set and retrieve such properties, use:

```
{% highlight java %}
{query|result}.getContext(true).setProperty(name, value)
{query|result}.getContext(true).getProperty(name)
{% endhighlight %}
```

## Parametrizing Searchers

It is easy to pass arguments to searchers -
any key-value looked up in the query properties in the searcher can be passed as is in the request,
or in a query profile. Example:

```
{% highlight java %}
String myParameter = query.properties().getString("my.parameter", "defaultValue");
{% endhighlight %}
```

This value can be set by adding `&my.parameter=myValue` to the request. Guidelines:
* Names should use camelCase with the first letter in small caps
* Dots are used for nesting and have a special meaning
  in [query profiles](query-profiles.html).
  They exist to aid organization of the space of parameters, which easily grows
  quite large. Usually, the right thing to do is to create a
  separate name space for each searcher - i.e. use the same
  dotted prefix for all parameters,
  as in `myfeature.a`, `myfeature.b` etc.
  In addition to helping keep the search API clean, this allows various
  query profiles containing settings for all values in
  `myfeature` to be defined and selected at run time,
  which is often useful.
* To make such parameter APIs easier to use, one should also consider creating a
  [query profile
  type](query-profiles.html#query-profile-types) defining the valid parameters. This will be in the form
  of an XML file accompanying the bundle. This allows checking and
  optionally enforcement of validity of request parameter and query
  profile settings of the parameters.

Parameters should be used for all query state which it is reasonable
and just as cheap to assume may change with every query.
Good candidates are e.g. numerical values to algorithms and switches to business logic.

## Execution model

In broad strokes, the Container works like this:

1. The main thread picks up one of the requests waiting in the queue of the input socket
2. This thread selects the search chain to be used to answer this request,
   and hands off the actual execution of the chain to a worker thread (there are many such worker threads)
3. The worker thread calls all searchers in the search chain in turn, starting with the first one
4. Each searcher returns results
5. Results are eventually rendered (maybe using a template) into the buffer of the output socket

There is a single instance of each search chain.
In every chain, there is a single instance of each searcher.
(Unless a chain is configured with multiple, identical searchers - this is a rare case.)

When simultaneous requests arrive for the same search chain,
multiple worker threads execute the searchers in that chain.
A searcher can therefore be executed concurrently by multiple threads;
many threads of execution can be going through the `search()` method, concurrently.

This model places an important constraint on searcher classes:
*instance variables are not safe.* They must be eliminated, or made thread-safe somehow.

## Keeping state in Searchers

As the passing of queries and results happen on the call stack,
the container will allocate many worker threads to execute queries,
using one thread per query until the result is returned.

This means that any state we wish to keep along in the searcher for this particular query
until the result is returned should be kept as local variables in the search method,
while state which should be shared by all queries should be kept as member variables.
As the latter kind will be accessed by multiple threads at any one time,
the state of such member variables must be *multithread safe*.

This critical restriction is similar to those of e.g. the Servlet API.
A quick example should drive the point home:

```
{% highlight java %}
public class SafeSearcher extends Searcher {

    public Result search(Query query, Execution execution) {
        long count = (Long) query.properties().get("Count");
        count++;
        return execution.search(query);
    }
}

public class UnsafeSearcher extends Searcher {
    private long count;

    public Result search(Query query, Execution execution) {
        count = (Long) query.properties().get("Count");
        count++; // unsafe
        return execution.search(query);
    }
}
{% endhighlight %}
```

The second example uses an instance variable,
which will be accessed concurrently by multiple threads.
Without proper concurrency controls (such as synchronization),
such access is inherently unsafe and may yield inconsistent results, and/or data corruption.

Options for implementing a multithread-safe searcher with instance variables:

1. Use immutable objects: they never change after they are constructed;
   no modifications to their state occurs after the Searcher constructor returns.
2. Use a single instance of a thread-safe class.
3. Create a single instance and synchronize access to it across all threads
   (but this will severely limit your scalability).
4. Arrange for each thread to have its own instance, e.g. with a `ThreadLocal`.

## Multiphase searching

The model of a single pass fetching results from a Query described in
this document is sometimes too simplistic to produce good performance.
The search container supports *multiphase searching* to address such cases.
With multiphase searching, the hits of the result is first filled with some minimal information.
This minimally filled result is sent up the search chain where some of the hits are hopefully removed.
When more information is needed, a second fill request is sent down the search chain
to fetch more data for just those hits remaining in the result.
This can happen in repeated stages, working on progressively smaller sets of hits
containing progressively more expensive information.

The container supports this by offering `fill` methods on execution,
which may be called to request more information added to the hits of the result from a searcher.
In addition, the backends and backend providers must support multiphase searching
(this is currently only the case for internal Vespa clusters).

Any searchers should assume they are operating in a multiphase setup, meaning:
* Searchers which changes the query or contain workflows do not need to do anything
* Searchers which accesses field information (not just id and
  relevance) from hits should **always** call
  either `fill()` to get the default set of fields for
  each hit type or `fill(summaryClassName)` to get a
  particular collection of fields known to exist in the backend(s) in question.
  Calling fill on a result which contains already-filled hits is cheap.
* Federating searchers should implement both the
  regular `search` method and the `fill` method.
  The fill method must request filling down the source
  branches which has remaining hits in the result.
* Backend searchers, which wish to support multiphase searching,
  should initially deliver unfilled hits
  and implement a `fill` method which fills the hits in the given
  result belonging to that backend with information from the backend.

## Error handling

If your searcher encounters a problem and wants to signal an error,
set an error hit in the result object by calling `result.hits().addError(errorMsg)`.

See the FAQ for [timeouts](faq.html#how-is-the-query-timeout-computed).

## Timeouts

How to gracefully handle a timeout inside a Searcher?
`Result result = execution.search(query)` can result in a timeout - when printed:

```
Container.com...vespa.Searcher result: Result: Source 'top-chain': 12: Timed out: Error in execution of chain 'top-chain': Chain timed out.
```

When having a tree of chains (see [federation](federation.html#timeout-behavior)),
where the main chain calls one chain per source,
and in this case, one of the source chains times out (e.g. does not return a Result within its deadline),
this can happen.

It is not generally possible to prevent this from ever happening,
but searchers can check `query.getTimeLeft` before doing time-consuming stuff,
and pass `query.getTimeLeft() - a_little` as timeout
to processes they initiate (such as network calls) that are able to take a deadline themselves.

## WordItem

In a Searcher, one often will use
[WordItem](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/prelude/query/WordItem.html)
to modify the current query, or create a new query based on input query terms, or results from the current query.
To keep linguistic settings (e.g. stemming) from the parent query, set `isFromQuery` to true -
[example](https://github.com/vespa-cloud/vespa-documentation-search/blob/main/src/main/java/ai/vespa/cloud/docsearch/DocumentationSearcher.java).
