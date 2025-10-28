---
# Copyright Vespa.ai. All rights reserved.
title: "Federation"
---

![Federation example](/assets/img/federation-simple.svg)

The Vespa Container allows multiple sources of data to
be *federated* to a common search service.
The sources of data may be both search clusters belonging to the same application,
or external services, backed by Vespa or any other kind of service.
The container may be used as a pure *federation platform* by
setting up a system consisting solely of container nodes federating to external services.

This document gives a short intro to federation,
explains how to create an application package doing federation
and shows what support is available for choosing the sources given a query,
and the final result given the query and some source specific results.
*Federation* allows users to access data from multiple
sources of various kinds through one interface. This is useful to:
* enrich the results returned from an application with auxiliary
  data, like finding appropriate images to accompany news
  articles.
* provide more comprehensive results by finding data from
  alternative sources in the cases where the application has none,
  like back-filling web results.
* create applications whose main purpose is not to provide access
  to some data set but to provide users or frontend applications a
  single starting point to access many kinds of data from various
  sources. Examples are browse pages created dynamically for any
  topic by pulling together data from external sources.

The main tasks in creating a federation solution are:

1. creating connectors to the various sources
2. selecting the data sources which will receive a given query
3. rewriting the received request to an executable query returning the
   desired data from each source
4. creating the final result by selecting from, organizing and
   combining the returned data from each selected source

The container aids with these tasks by providing a way to
organize a federated execution as a set of search chains which can be
configured through the application package.
Read the [Container intro](jdisc/) and
[Chained components](components/chained-components.html) before proceeding.
Read about using [multiple schemas](schemas.html#multiple-schemas).
Refer to the `com.yahoo.search.federation`
[Javadoc](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/federation/package-summary.html).

## Configuring Providers

A *provider* is a search chain that produces
data (in the form of a Result) from a data source.
The provider must contain a Searcher which connects to
the data source and produces a Result from the returned data.
Configure a provider as follows:

```
<search>
    <provider id="my-provider">
        <searcher id="MyDataFetchingSearcher"
                  bundle="the name in artifactId in pom.xml" />
    </provider>
</search>
```

You can add multiple searchers in the provider just like in other chains.

Search chains that provide data from some content cluster in the same application
are also *providers*. To explicitly configure a provider talking to internal
content clusters, set the attribute type="local" on the provider. That will automatically
add the searchers necessary to talk to internal content clusters to the search chain.
Example: querying this provider will not lowercase / stem terms:

```
<provider id="myProvider"
          type="local"
          cluster="mydocs"
          excludes="com.yahoo.prelude.searcher.BlendingSearcher
              com.yahoo.prelude.querytransform.StemmingSearcher
              com.yahoo.search.querytransform.VespaLowercasingSearcher">
```

## Configuring Sources

A single provider may be used to produce multiple kinds of results.
To implement and present each kind of result, we can use *sources*.
A *source* is a search chain that provides a specific kind of result
by extending or modifying the behavior of one or more providers.

Suppose that we want to retrieve two kinds of results from
my-provider: Web results and java API documentation:

```
<search>
    <provider id="my-provider">
        <searcher id="MyDataFetchingSearcher"
                  bundle="the name in artifactId in pom.xml" />
        <source id="web" />
        <source id="java-api">
            <searcher id="com.yahoo.example.JavaApiSearcher"
                      bundle="the name in artifactId in pom.xml" />
        </source>
    </provider>
```

This results in two *source search chains* being created,
`web@my-provider` and `java-api@my-provider`.
Each of them constitutes a source,
namely `web` and `java-api` respectively.
As the example suggests, these search chains are named
after the source and the enclosing provider.
The @-sign in the name should be read as *in*,
so `web@my-provider` should for example be read as *web in my-provider*.

The JavaApiSearcher is responsible for modifying the query so that we
only get hits from the java API documentation. We added this searcher
directly inside the source element; source search chains and providers
are both instances of search chains. All the options for configuring
regular search chains are therefore also available for them.

How does the `web@my-provider`
and `java-api@my-provider` source search chains use the
`my-provider` provider to send queries to the external
service? Internally, the source search chains *inherit* from
the enclosing provider. Since the provider contains searchers that
know how to talk to the external service, the sources will also
contain the same searchers. As an example, consider the "web" search
chain; It will contain exactly the same searcher instances as the
`my-provider` search chain. By organizing chains for talking
to data providers, we can reuse the same connections and logic
for talking to remote services ("providers") for multiple purposes ("sources").

The provider search chain `my-provider` is *not modified* by adding sources.
To verify this, try to send queries to the three search chains
`my-provider`, `web@my-provider` and `java-api@my-provider`.

### Multiple Providers per Source

You can create a source that consists of source search chains from
several providers. Effectively, this lets you vary which provider
should be used to satisfy each request to the source:

```
<search>
    <provider id="my-provider">
        <searcher id="MyDataFetchingSearcher"
                  bundle="the name in artifactId in pom.xml" />
        <source id="common-search" />
    </provider>

    <provider id="news-search">
        <searcher id="MyNewsDataFetchingSearcher"
                  bundle="the name in artifactId in pom.xml" />
        <source idref="common-search" />
    </provider>
```

Here, the two source search chains `common-search@news-search` and
`common-search@my-provider` constitutes a single source `common-search`.
The source search chains using the `idref` attribute are
called participants, while the ones using the `id` attribute are called leaders.
Each source must consist of a single leader and zero or more participants.

Per default, only the leader search chain is used when *federating* to a source.
To use one of the participants instead,
use [sources](reference/query-api-reference.html#model.sources) and *source*:

```
http://[host]:[port]/?sources=common-search&source.common-search.provider=news-search
```

## Federation

Now we can search both the web and the java API documentation at the
same time, and get a combined result set back.
We achieve this by setting up a *federation* searcher:

```
<search>
    <provider id="my-provider">
        <searcher id="MyDataFetchingSearcher"
                  bundle="the name in artifactId in pom.xml" />
        <source id="web" />
        <source id="java-api">
            <searcher id="com.yahoo.example.JavaApiSearcher"
                      bundle="the name in artifactId in pom.xml" />
        </source>
    </provider>
    <chain id="combined">
        <federation id="combinator">
            <source idref="web" />
            <source idref="java-api" />
        </federation>
    </chain>
```

Inside the Federation element, we list the sources we want to use.
Do not let the name *source* fool you;
If it behaves like a source, then you can use it as a source
(i.e. all types of search chains including providers are accepted).
As an example, try replacing the *web* reference with *my-provider*.

When searching, select a subset of the sources specified in the federation element
by specifying the [sources](reference/query-api-reference.html#model.sources) query parameter.

## Built-in Federation

The built-in search chains *native* and
*vespa* contain a federation searcher named *federation.*
This searcher has been configured to federate to:
* All sources
* All providers that does not contain a source

If configuring your own federation searcher, you are not limited to a subset of these sources -
you can use any provider, source or search chain.

## Inheriting default Sources

To get the same sources as the built-in federation searcher, inherit the default source set:

```
<search>
    <chain id="my-chain">
        <federation id="combinator">
            <source-set inherits="default" />
            ...
        </federation>
    </chain>
</search>
```

## Changing content cluster chains

With the information above, we can create a configuration where we modify
the search chain sending queries to and receiving queries form a single content cluster
(here, removing a searcher and adding another):

```
<search>
    <chain id="default" inherits="vespa">
        <federation id="federationSearcher">
            <source id="local"/>
        </federation>
    </chain>
    <provider cluster="my_content" id="local" type="local"
              excludes="com.yahoo.search.querytransform.NGramSearcher">
        <searcher id="ai.vespa.example.OrNGramSearcher"
                  bundle="the name in artifactId in pom.xml"/>
    </provider>
</search>
```

## Timeout behavior

What if we want to limit how much time a provider is allowed to use to answer a query?

```
<search>
    <provider id="my-provider">
        <federationoptions timeout="100 ms" />
        <searcher id="MyDataFetchingSearcher"
                  bundle="the name in artifactId in pom.xml" />
        <source id="web" />
        <source id="java-api">
            <searcher id="com.yahoo.example.JavaApiSearcher"
                      bundle="the name in artifactId in pom.xml" />
        </source>
    </provider>
```

The provider search chain will then be limited to use 100 ms to execute each query.
The Federation layer allows all providers to continue until the
non-optional provider with the longest timeout is finished or canceled.

In some cases it is useful to be able to keep executing the request to a provider
longer than we are willing to wait for it in that particular query.
This allows us to populate caches inside sources
which can only meet the timeout after caches are populated.
To use this option, specify a [request timeout](reference/services-search.html#federationoptions)
for the provider:

```
<search>
    <provider id="my-provider">
        <federationoptions timeout="100 ms" requestTimeout="10000ms" />
        ...
    </provider>
```

Also see [Searcher timeouts](searcher-development.html#timeouts).

## Non-essential Providers

Now let us add a provider that retrieves ads:

```
<search>
    <provider id="ads">
        <searcher id="MyAdFetcher"
                  bundle="the name in artifactId in pom.xml" />
    </provider>
```

Suppose that it is more important to return the result to the user as
fast as possible, than to retrieve ads.
To signal this, we mark the ads provider as *optional*:

```
<search>
    <provider id="ads">
        <federationoptions optional="true" />
        <searcher id="MyAdFetcher"
                  bundle="the name in artifactId in pom.xml" />
    </provider>
```

The Federation searcher will then only wait for ads as long as it waits for mandatory providers.
If the ads are available in time, they are used, otherwise they are dropped.

If only optional providers are selected for Federation, they will all be treated as mandatory.
Otherwise, they would not get a chance to return any results.

## Federation options inheritance

The sources automatically use the same Federation options as the enclosing provider.
*override* one or more of the federation options in the sources:

```
<search>
    <provider id="my-provider">
        <federationoptions timeout="100ms" />
        <searcher id="MyDataFetchingSearcher"
                  bundle="the name in artifactId in pom.xml" />
        <source id="web">
            <federationoptions timeout="200ms" />
        </source>
        <source id="java-api">
            <searcher id="com.yahoo.example.JavaApiSearcher"
                      bundle="the name in artifactId in pom.xml" />
        </source>
    </provider>
```

You can use a single source in different Federation searchers.
If you send queries with different cost to the same source from different federation searchers,
you might also want to *override* the federation options for when they are used:

```
<search>
    <provider id="my-provider">
        <federationoptions timeout="100ms" />
        <searcher id="MyDataFetchingSearcher"
                  bundle="the name in artifactId in pom.xml" />
        <source id="web">
            <federationoptions timeout="200ms" />
        </source>
        <source id="java-api">
            <searcher id="com.yahoo.example.JavaApiSearcher"
                      bundle="the name in artifactId in pom.xml" />
        </source>
    </provider>
    <chain id="combined">
        <federation id="combinator">
            <source idref="web">
                <federationoptions timeout="2.5s" />
            </source>
            <source idref="java-api" />
        </federation>
    </chain>
```

## Selecting Search Chains programmatically

If we have complicated rules for when a search chain should be used,
we can select search chains programmatically instead of setting up sources under federation in services.xml.
The selection code is implemented as a
[TargetSelector](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/federation/selection/TargetSelector.html). This TargetSelector is used by registering it on a federation searcher.

```
{% highlight java %}
package com.yahoo.example;

import com.google.common.base.Preconditions;
import com.yahoo.component.chain.Chain;
import com.yahoo.processing.execution.chain.ChainRegistry;
import com.yahoo.search.Query;
import com.yahoo.search.Result;
import com.yahoo.search.result.Hit;
import com.yahoo.search.Searcher;
import com.yahoo.search.federation.selection.FederationTarget;
import com.yahoo.search.federation.selection.TargetSelector;
import com.yahoo.search.searchchain.model.federation.FederationOptions;

import java.util.Arrays;
import java.util.Collection;

class MyTargetSelector implements TargetSelector {

    @Override
    public Collection> getTargets(Query query,
                                                           ChainRegistry searcherChainRegistry) {
        Chain searchChain = searcherChainRegistry.getComponent("my-chain");
        Preconditions.checkNotNull(searchChain, "No search chain named 'my-chain' exists in services.xml");

        return Arrays.asList(new FederationTarget<>(searchChain, new FederationOptions(), null));
    }

    @Override
    public void modifyTargetQuery(FederationTarget target, Query query) {
        query.setHits(10);
    }

    @Override
    public void modifyTargetResult(FederationTarget target, Result result) {
        for (Hit hit: result.hits()) {
            hit.setField("my-field", "hello-world");
        }
    }

}
{% endhighlight %}
```

The target selector chooses search chains for the federation searcher.
In this example, MyTargetSelector.getTargets returns a single chain named "my-chain"
that has been set up in `services.xml`.

Before executing each search chain, the federation searcher allows the target selector
to modify the query by calling modifyTargetQuery.
In the example, the number of hits to retrieve is set to 10.

After the search chain has been executed, the federation searcher allows the target selector
to modify the result by calling modifyTargetResult.
In the example, each hit gets a field called "my-field" with the value "hello-world".

Configure a federation searcher to use a target selector in `services.xml`.
Only a single target selector is supported.

```
<search>
    <chain id="my-chain">
      <federation id="my-federation">
          <target-selector id="com.yahoo.example.MyTargetSelector"
                           bundle="the name in artifactId in pom.xml" />
      </federation>
    </chain>
```

We can also set up both a target-selector and normal sources.
The federation searcher will then send queries both to programmatically selected sources
and those that would normally be selected without the target selector:

```
<search>
    <chain id="my-chain">
        <federation id="my-federation">
            <target-selector id="com.yahoo.example.MyTargetSelector"
                             bundle="the name in artifactId in pom.xml" />
            <source idref="java-api" />
            <source-set inherits="default" />
            ...
        </federation>
    </chain>
```

## Example: Setting up a Federated Service

A federation application is created by providing custom searcher
components performing the basic federation tasks and combining these
into chains in a federation setup in
[services.xml](application-packages.html#services.xml).
For example, this is a complete configuration which sets up a cluster of
container nodes (having 1 node) which federates to the another Vespa
service (news) and to some web service:

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">
    <admin version="2.0">
        <adminserver hostalias="node1"/>
    </admin>

    <container id="test" version="1.0">
        <nodes>
            <node hostalias="node1"/>
        </nodes>
        <search>
            <provider id="news">
                <searcher id="com.yahoo.example.NewsCustomerIdSearcher"
                          bundle="the name in artifactId in pom.xml" />
            </provider>
            <provider id="webService">
                <searcher id="com.yourdomain.WebProviderSearcher"
                          bundle="the name in artifactId in pom.xml" />
            </provider>
        </search>
    </container>
</services>
```

This creates a configuration of search chains like:

![Federation example](/assets/img/federation.svg)

Each provider *is* a search chain ending in a Searcher
forwarding the query to a remote service.
In addition, there is a main chain (included by default) ending in a FederationSearcher,
which by default forwards the query to all the providers in parallel.
The provider chains returns their result upwards to the federation searcher
which merges them into a complete result which is returned up the main chain.

This services file, an implementation of the `example` classes (see below),
and *[hosts.xml](reference/hosts.html)*
listing the container nodes, is all that is needed to set up and
[deploy](application-packages.html#deploy)
an application federating to multiple sources.
For a reference to these XML sections,
see the [chains reference](reference/services-search.html#chain).

The following sections outlines how this can be elaborated into a
solution producing more user-friendly federated results.

### Selecting Sources

To do the best possible job of bringing relevant data to the user,
we should send every query to all sources, and decide what data to
include when all the results are available, and we have as much information as possible at hand.
In general this is not advisable because of the resource cost involved,
so we must select a subset based on information in the query.
This is best viewed as a probabilistic optimization problem:
The selected sources should be the ones having a high enough probability of being useful
to offset the cost of querying it.

Any Searcher which is involved in selecting sources or processing the
entire result should be added to the main search chain,
which was created implicitly in the examples above.
To do this, the main chain should be created explicitly:

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">
    <admin version="2.0">
        <adminserver hostalias="node1"/>
    </admin>
    <container id="test" version="1.0">
        <nodes>
            <node hostalias="node1"/>
        </nodes>
        <search>
            <chain id="default" inherits="native">
                <searcher id="com.yahoo.example.ResultBlender"
                          bundle="the name in artifactId in pom.xml" />
            </chain>
            <provider id="news">
                <searcher id="com.yahoo.example.NewsCustomerIdSearcher"
                          bundle="the name in artifactId in pom.xml" />
            </provider>
            <provider id="webService">
                <searcher id="com.yahoo.example.ExampleProviderSearcher"
                          bundle="the name in artifactId in pom.xml" />
            </provider>
        </search>
    </container>
</services>
```

This adds an explicit main chain to the configuration
which has two additional searchers in addition to those inherited
from the `native` chain, which includes the FederationSearcher.
Note that if the full Vespa functionality is needed,
the `vespa` chain should be inherited rather than `native`.

The chain called `default` will be invoked if no
searchChain parameter is given in the query.

To learn more about creating Searcher components,
see [searcher development](searcher-development.html).

### Rewriting Queries to Individual Providers

The *provider* searchers are responsible for accepting a Query object,
translating it to a suitable request to the backend in question
and deserializing the response into a Result object.
There is often a need to modify the query to match the particulars of a provider before passing it on:
* To get results from the provider which matches the determined
  interpretation and intent as well as possible, the query may need
  to be rewritten using detailed information about the provider
* Parameters beyond the basic ones supported by each provider
  searcher may need to be translated to the provider
* There may be a need for provider specific business rules

These query changes may range in complexity from setting a query parameter,
applying some source specific information to the query
or transferring all the relevant query state into a new object
representation which is consumed by the provider searcher.

This example shows a searcher adding a customer id to the `news` request:

```
{% highlight java %}
package com.yahoo.example;

import com.yahoo.search.searchchain.Execution;
import com.yahoo.search.*;

public class NewsCustomerIdSearcher extends Searcher {

    @Override
    public Result search(Query query, Execution execution) {
        String customerId="provider.news.custid";
        if (query.properties().get(customerId) == null)
            query.properties().set(customerId, "yahoo/test");
        if (query.getTraceLevel() >= 3)
            query.trace("News provider: Will use "
                + customerId + "=" + query.properties().get(customerId), false, 3);
        return execution.search(query);
    }

}
{% endhighlight %}
```

This searcher should be added to the `news` source chain as shown above.

You may have noticed that we have referred to the search chains
talking to a service as a **provider**
while referring to selection of **sources**.
The reason for making this distinction is that it is sometimes useful to treat different kinds of
processing of queries and results to/from the same service as different sources.
Hence, it is possible to create `source` search chains
in addition to the provider chains in *services.xml*.
Each such source will refer to a provider (by inheriting the provider chain)
but include some searchers specific to that source.
Selection and routing of the query from the federation searchers is always to sources, not providers.
By default, if no source tags are added in the provider,
each provider implicitly creates a source by the same name.

### Processing Results

When we have selected the sources, created queries fitting to get
results from each source and executed those queries,
we have produced a result which contains a HitGroup per source
containing the list of hits from that source.
These results may be returned in XML as is,
preserving the structure as XML, by requesting
the [page](reference/page-result-format.html) result format:

```
http://[host]:[port]/search/?query=test&presentation.format=page
```

However, this is not suitable for presenting to the user in most cases.
What we want to do is select the subset of the hits having the highest probable utility to the user,
organized in a way that maximizes the user experience.
This is not an easy task, and we will not attempt to solve it here,
other than noting that any solution should make use of both the information in the intent model
and the information within the results from each source,
and that this is a highly connected optimization problem
because the utility of including some data in the result depends on what other data is included.

Here we will just use a searcher which shows how this is done in principle,
this searcher flattens the news and web service hit groups into a single list of hits,
where only the highest ranked news ones are included:

```
{% highlight java %}
package com.yahoo.example;

import com.yahoo.search.*;
import com.yahoo.search.result.*;
import com.yahoo.search.searchchain.Execution;

public class ResultBlender extends Searcher {

    @Override
    public Result search(Query query,Execution execution) {
        Result result = execution.search(query);
        HitGroup news = (HitGroup)result.hits().remove("source:news");
        HitGroup webService = (HitGroup)result.hits().remove("source:webService");
        if (webService == null) return result;
        result.hits().addAll(webService.asList());
        if (news == null) return result;
        for (Hit hit : news.asList())
            if (shouldIncludeNewsHit(hit))
                result.hits().add(hit);
        return result;
    }

    private boolean shouldIncludeNewsHit(Hit hit) {
        if (hit.isMeta()) return true;
        if (hit.getRelevance().getScore() > 0.7) return true;
        return false;
    }

}
{% endhighlight %}
```

The optimal result to return to the user is not necessarily one flattened list.
In some cases it may be better to keep the source organization, or to pick some other organization.
The [page result format](reference/page-result-format.html)
requested in the query above is able to represent any hierarchical organization as XML.
A more realistic version of this searcher will use that to choose between some
predefined layouts which the frontend in question knows how to handle,
and choose some way of grouping the available hits suitable for the selected layout.

This searcher should be added to the main (`default`) search chain in
*services.xml* together with the SourceSelector (the order does not matter).

### Unit Testing the Result Processor

Unit test example for the Searcher above:

```
{% highlight java %}
package com.yahoo.search.example.test;

import org.junit.Test;
import com.yahoo.search.searchchain.*;
import com.yahoo.search.example.ResultBlender;
import com.yahoo.search.*;
import com.yahoo.search.result.*;

public class ResultBlenderTestCase {

    @Test
    public void testBlending() {
        Chain chain = new Chain(new ResultBlender(), new MockBackend());
        Context context = Execution.Context.createContextStub(null);
        Result result = new Execution(chain, context).search(new Query("?query=test"));
        assertEquals(4, result.hits().size());
        assertEquals("webService:1", result.hits().get(0).getId().toString());
        assertEquals("news:1", result.hits().get(1).getId().toString());
        assertEquals("webService:2", result.hits().get(2).getId().toString());
        assertEquals("webService:3", result.hits().get(3).getId().toString());
    }

    private static class MockBackend extends Searcher {

        @Override
        public Result search(Query query,Execution execution) {
            Result result = new Result(query);
            HitGroup webService = new HitGroup("source:webService");
            webService.add(new Hit("webService:1",0.9));
            webService.add(new Hit("webService:2",0.7));
            webService.add(new Hit("webService:3",0.5));
            result.hits().add(webService);
            HitGroup news = new HitGroup("source:news");
            news.add(new Hit("news:1",0.8));
            news.add(new Hit("news:2",0.6));
            news.add(new Hit("news:3",0.4));
            result.hits().add(news);
            return result;
        }
    }

}
{% endhighlight %}
```

This shows how a search chain can be created programmatically,
with a mock backend producing results suitable for exercising
the functionality of the searcher being tested.
