---
# Copyright Vespa.ai. All rights reserved.
title: "Page Templates"
---

When multiple kinds of data is fetched for a request, the application
must decide how to lay out the data to return to the user.
*Page templates* allows such page layouts to be defined as XML
configuration files - one file per layout, corresponding to one use case.

The layouts are *structural* - they do not specify widths
and heights, colors and similar, but define the various boxed
components that will make up the page, and their ordering and nesting.
It is also assumed that the complete application includes a *frontend*
which is capable of rendering finished pages from result laid out by a template.

Page layouts may contain *choices* which specify alternative
versions of the template. The choices in a template are taken by
a *resolver* component at run time. Given an optimizing
resolver the system can then learn to make the right choices given
each particular query and result. An optimizing resolver is not
bundled with the platform but must be added as a component.

This document describes how to get started,
explains the [page template language](#introduction)
and [how to add a choice resolver](#using-choice-resolvers).
A complete reference of all the permissible content of page templates is found in the
[page template reference](reference/page-templates-syntax.html).

## Getting Started

A page template is an XML file which is placed in the
directory `search/page-templates/` in
the [application package](application-packages.html).
To start using page templates:
* Create template XML files as
  shown [below](#introduction)
  in `[app-package]/page-templates/`
* Add the searcher
  [com.yahoo.search.pagetemplates.PageTemplateSearcher](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/pagetemplates/PageTemplateSearcher.html)
  to the default [search chain](reference/services-search.html) in *services.xml*.
* [deploy](application-packages.html#deploy)
  the application package.
* Add these query parameters: `page.id=[comma-separated list of page id's]`
  and `presentation.format=page`.

The results returned will be as defined by the page template selected for each query.

The source names used in page templates are the same as those defined
in the [federation](federation.html) setup,
and/or of any internal search clusters defined in the application.

A presentation layer (frontend) which understands the results created
by the page templates in use must be set up or created to produce rendered pages.
That is beyond the scope of this document.

## Introduction to Page Templates

A page template is an XML file which contains
a `<page>` tag at the top level. The page element
must have an `id` attribute, where the file name is the
same as the id, followed by *.xml*. If the id
is *default*, this template will be used whenever no template
is specified in the query. The templates may also be versioned,
see [Component Versioning](reference/component-reference.html#component-versioning).

A page template consist of nested *sections* which correspond
to screen areas in the final layout. The top level section is defined
by the page itself, while further sections can be defined by explicit
<section> tags. Each section may set a layout which will be
used by the frontend renderer to lay out its content
- `column` and `row` must be supported by
all renderers, while some renderers may specify additional layouts.
Each section may also specify sources of data which should be placed
in the section. Renderers must be able to render multiple data items
from different sources in a section.

For example, this template creates a page consisting of four equally large regions containing one source each:

```
<page id="fourSquare" layout="column">
    <section layout="row">
        <section source="news"/>
        <section source="web"/>
    </section>
    <section layout="row">
        <section source="image"/>
        <section source="video"/>
    </section>
</page>
```

To use this template, save it as *[application-package]/page-templates/fourSquare.xml*.

Suppose we want to extend this template to be able to also show blogs in the "news" section.
This can be done as follows:

```
<page id="fourSquare" layout="column">
    <section layout="row">
        <section source="news blog"/>
        <section source="web"/>
    </section>
    <section layout="row">
        <section source="image"/>
        <section source="video"/>
    </section>
</page>
```

Data items from each possible source has a rendering implemented by the frontend.
These renderers are used when nothing is specified in the template.
If some alternative rendering is desired, this can be
specified by a `renderer` tag. The same is true for
rendering of the sections themselves. Here we specify a different
renderer for blog data items (hits), as well as for the entire
*news/blog* section.

```
<page id="fourSquare" layout="column">
    <section layout="row">
        <section source="news">
            <renderer name="blueSection">
            <source name="blog">
                <renderer name="newBlogHitStyle"/>
            </source>
        <section/>
        <section source="web"/>
    </section>
    <section layout="row">
        <section source="image"/>
        <section source="video"/>
    </section>
</page>
```

Note that in order to add a renderer subelement, we now specify the
blog source by a tag rather than by an attribute. These two forms are
equivalent - the attribute variant is just a shorthand syntax.

Sources and renderers can be given arbitrary key-value parameters
- see the [reference](reference/page-templates-syntax.html) for details.

But what if we want to choose either news or blogs, but not both?
This can be achieved using a choice:

```
<page id="fourSquare" layout="column">
    <section layout="row"> <section;>
    <renderer name="blueSection">
            <choice>
                <source name="news"/>
                <source name="blog">
                    <renderer name="newBlogHitStyle"/>
                </source>
            </choice>
        <section/>
        <section source="web"/>
    </section>
    <section layout="row">
        <section source="image"/>
        <section source="video"/>
    </section>
</page>
```

We can insert choices anywhere in a template, for example choose to
show either the first or the second row rather than both:

```
<page id="fourSquare" layout="column">
    <choice>
        <section layout="row">
            <section;>
                <renderer name="blueSection">
                <choice>
                    <source name="news"/>
                    <source name="blog">
                        <renderer name="newBlogHitStyle"/>
                    </source>
                </choice>
            <section/>
            <section source="web"/>
        </section>
        <section layout="row">
            <section source="image"/>
            <section source="video"/>
        </section>
    </choice>
</page>
```

If we wanted to choose between two groups of multiple sections (or sources),
this can be done by adding an enclosing `alternative` tag around each group.
For the common special case of assigning a set of elements to a set of placeholders,
a choice can contain a `map` tag instead of a list of alternatives.
See the [reference](reference/page-templates-syntax.html) for details.

## Using Choice Resolvers

If templates including choices are used, some component must resolve
those choices given each query and result. The system includes some
resolvers for demo and testing purposes, but a proper optimizing
resolver must be deployed as part of the application.
This section describes how to create, deploy and choose a resolver to use at runtime.

### Writing a Resolver

Resolvers are subclasses of
[com.yahoo.search.pagetemplates.engine.Resolver](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/pagetemplates/engine/Resolver.html).
This API defines a method which accepts the page template in use
(which contains the choices), the Query/Result pair and returns a Resolution.
It is called at runtime once for every query which uses a page template.

There are also some helper methods which makes it simple to write
resolvers which make each choice independently. Here is an example
resolver which makes all choices by random using this helper methods:

```
package com.yahoo.search.pagetemplates.engine.resolvers;

import com.yahoo.search.Query;
import com.yahoo.search.Result;
import com.yahoo.search.pagetemplates.engine.*;
import com.yahoo.search.pagetemplates.model.*;

import java.util.*;

/** A resolver which makes all choices by random. */
public class RandomResolver extends Resolver {

    private Random random=new Random(System.currentTimeMillis()); // Use of this is multithread safe

    /** Chooses the last alternative of any choice */
    @Override
    public void resolve(Choice choice, Query query, Result result, Resolution resolution) {
        resolution.addChoiceResolution(choice,random.nextInt(choice.alternatives().size()));
    }

    /** Chooses a mapping which is always by the literal order given in the source template */
    @Override
    public void resolve(MapChoice choice,Query query,Result result,Resolution resolution) {
        Map<String, List<PageElement>> mapping=new HashMap<String, List<PageElement>>();
        // Draw a random element from the value list on each iteration and assign it to a placeholder
        List<String> placeholderIds=choice.placeholderIds();
        List<List<PageElement>> valueList=new ArrayList<List<PageElement>>(choice.values());
        for (String placeholderId : placeholderIds)
            mapping.put(placeholderId,valueList.remove(random.nextInt(valueList.size())));
        resolution.addMapChoiceResolution(choice,mapping);
    }

}
```

### Deploying a Resolver

Resolvers must be packaged as [OSGI bundles](https://en.wikipedia.org/wiki/Osgi#Bundles) for deployment,
see [container components](jdisc/container-components.html).

The packaged component is added to the `components/`
directory of the [application package](application-packages.html).

The page template searcher must be configured with a list of the
resolvers which should be available. This is done by expanding the
page template searcher configuration with a *components* configuration:

```
<searcher id="com.yahoo.search.pagetemplates.PageTemplateSearcher" bundle="the name in <artifactId> in your pom.xml" >
    <config name="container.components">
        <component index="0">
            <id>default</id>
            <classId>com.yahoo.my.Resolver1</classId>
            <bundle>myBundleSymbolicName</bundle>
        </component>

        <component index="1">
            <id>mySecondResolver</id>
            <classId>com.yahoo.my.Resolver2</classId>
            <bundle>myBundleSymbolicName</bundle>
        </component>
    </config>
</searcher>
```

With this, the application is
[deployed](application-packages.html#deploy) as usual.

### Choosing a Resolver

The resolver to use is determined by setting the query property
`page.resolver` to the id (and optionally version) of the resolver component -
either in the request, in a query profile or programmatically.

Two templates suitable for testing purposes are always available:
`native.random`, which makes each choice by random,
and `native.deterministic` which selects the last
alternative of each choice.

If the `page.resolver` parameter is not set, the resolver having the
id `default` is used. If no default resolver is deployed
the random resolver is used.

## Examples

This section contains a few complete examples of page templates.

A blending search result page:

```
<page id="slottingSerp" layout="mainAndRight">
    <section layout="column" region="main" source="*"/>
    <section layout="column" region="right" source="ads"/>
</page>
```

A richer search result page:

```
<page id="richSerp" layout="mainAndRight">
    <section layout="row" placement="main">
        <section layout="column" description="left main pane">
            <section layout="row" max="5" description="Bar of images, from one of two possible sources">
                <choice>
                    <source name="images"/>
                    <source name="flickr"/>
                </choice>
            </section>
        <section max="1" source="local map video ticker weather"
                    description="A single relevant graphically rich element"/>
        <section max="10" source="web news"
                    description="Various kinds of traditional search results"/>
        </section>
            <section layout="column" order="[source]" source="answers blogs twitter"
                        description="right main pane, ugc stuff, grouped by source"/>
        </section>
    <section layout="column" source="ads" region="right"/>
</page>
```

A mapping of multiple source modules to places on the page:

```
<page id="MapSourcesToSections" layout="column" description="4 sources are assigned to a section each">

    <section layout="row" description="row 1">
        <section id="box1"><placeholder id="box1source"/></section>
        <section id="box2"><placeholder id="box2source"/></section>
    </section>
    <section layout="row" description="row 2">
        <section id="box3"><placeholder id="box3source"/></section>
        <section id="box4"><placeholder id="box4source"/></section>
    </section>

    <choice method="myMethod">
        <map to="box1source box2source box3source box4source">
            <source name="source1"/>
            <source name="source2"/>
            <source name="source3"/>
            <source name="source4"/>
        </map>
    </choice>

</page>
```
