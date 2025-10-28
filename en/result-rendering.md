---
# Copyright Vespa.ai. All rights reserved.
title: "Result Renderers"
---

Vespa provides a default JSON format for query results.
*Renderers* can be configured to implement custom formats,
like binary and text format.
Renderers should not be used to implement business logic -
that should go in [Searchers](searcher-development.html),
[Handlers](jdisc/developing-request-handlers.html) or
[Processors](jdisc/processing.html).
This guide assumes familiarity with the [Developer Guide](developer-guide.html).

Renderers are implemented by subclassing one of:
* [com.yahoo.search.rendering.Renderer](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/rendering/Renderer.html)
* [com.yahoo.search.rendering.SectionedRenderer](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/rendering/SectionedRenderer.html)
* [com.yahoo.processing.rendering.AsynchronousSectionedRenderer<Result>](https://javadoc.io/doc/com.yahoo.vespa/container-core/latest/com/yahoo/processing/rendering/AsynchronousSectionedRenderer.html)

SectionedRenderer differs from Renderer by providing each part to be rendered in separate steps.
It is therefore easier to implement a SectionedRenderer than a regular Renderer.
AsynchronousSectionedRenderer has a similar API to SectionedRenderer,
but supports asynchronously fetched hit contents,
so if supporting slow clients or backends is a priority, this offers some advantages.
AsynchronousSectionedRenderer also exposes an OutputStream instead of a Writer,
so if the backend data contains data encoded the same way as the output from the container
(often UTF-8), performance gains are possible.

All renderers are [components](jdisc/container-components.html).
They are built and deployed like all other container components,
and supports [custom config](configuring-components.html).

Renderers do *not* need to be thread safe -
they can safely use and store state during rendering in member variables.
The container supports this by cloning the renderers just before rendering the search result.
To support cloning correctly, the renderers are required to obey the following contract:

1. At construction time, only final members shall be initialized,
   and these must refer to immutable data only.
2. State mutated during rendering shall be initialized in the init method.

To enable a renderer, add to [services.xml](reference/services-container.html):

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">
    …
    <container version="1.0">
        <search>
            <renderer id="MyRenderer"
                      class="com.yahoo.mysearcher.MyRenderer"
                      bundle="the name in <artifactId> in pom.xml" />
        </search>
        …
    </container>
    …
</services>
```

To use the renderer, add [&presentation.format=[id]](reference/query-api-reference.html#presentation.format)
to queries - in this case `&presentation.format=MyRenderer`.

## Renderer

The simplest form of a renderer is extending `Renderer`.
The `render` method does all the work -
the derived class is expected to extract all the entities of interest itself and render them.
Simple example:

```
{% highlight java%}
public class SimpleRenderer extends Renderer {
    @Override
    public void render(Writer writer, Result result) throws IOException {
        writer.write("The result contains " + result.getHitCount() + " hits.");
    }

    @Override
    public String getEncoding() {
        return "utf-8";
    }

    @Override
    public String getMimeType() {
        return "text/plain";
    }
}
{% endhighlight %}
```

More complex example:

```
{% highlight java%}
/**
 * Render result sets as plain text. First line is whether an error occurred,
 * second rendering initialization time stamp, then each line is the ID of each
 * document returned, and the last line is time stamp for when the renderer was finished.
 */
public class DemoRenderer extends Renderer {
    private String heading;

    /**
     * No global, shared state to set.
     */
    public DemoRenderer() {
    }

    @Override
    protected void render(Writer writer, Result result) throws IOException {
        if (result.hits().getErrorHit() == null) {
            writer.write("OK\n");
        } else {
            writer.write("Oops!\n");
        }
        writer.write(heading + "\n");
        renderHits(writer, result.hits());
        writer.write("Rendering finished work: " + System.currentTimeMillis() + "\n");
    }

    private void renderHits(Writer writer, HitGroup hits) throws IOException {
        for (Iterator i = hits.deepIterator(); i.hasNext();) {
            Hit h = i.next();
            if (h.types().contains("summary")) {
                String id = h.getDisplayId();
                if (id != null) {
                    writer.write(id + "\n");
                }
            }
        }
    }

    @Override
    public String getEncoding() {
        return "utf-8";
    }

    @Override
    public String getMimeType() {
        return "text/plain";
    }

    /**
     * Initialize mutable, per-result set state here.
     */
    @Override
    public void init() {
        long time = System.currentTimeMillis();
        heading = "Renderer initialized: " + time;
    }

}
{% endhighlight %}
```

## SectionedRenderer

To create a SectionedRenderer, subclass it and implement all its abstract methods.
For each non-compound entity such as regular hits and query contexts,
there are an associated method with the same name:

```
{% highlight java %}
public class DemoRenderer extends SectionedRenderer<Writer> {

    @Override
    public void hit(Writer writer, Hit hit) throws IOException {
        writer.write("Hit: " + hit.getField("documentid") + "\n");
    }
}
{% endhighlight %}
```

For each compound entity, such as hit groups and the result itself,
there are pairs of methods, named `begin<name>` and `end<name>`:

```
{% highlight java %}
public class DemoRenderer extends SectionedRenderer<Writer> {

    private int indentation;

    @Override
    public void beginHitGroup(PrintWriter writer, HitGroup hitGroup) throws IOException {
        writer.write("Begin hit group:" + hitGroup.getId() + "\n");
        ++indentation;
    }

    @Override
    public void endHitGroup(PrintWriter writer, HitGroup hitGroup) throws IOException {
        --indentation;
        writer.write("End hit group:" + hitGroup.getId() + "\n");
    }
}
{% endhighlight %}
```

For a compound entity, a method will be called for each of its members after its `begin`-method
and before its `end`-method has been called:

```
                          Call sequence
                          -------------------
Result {                  1. beginResult()
    HitGroup {            2. beginHitGroup()
        Hit               3. hit()
        Hit               4. hit()
        Hit               5. hit()
    }                     6. endHitGroup()
}                         7. endResult()
```

For [grouping results](grouping.html), there is a dedicated set of callbacks available:
* `beginGroup()` / `endGroup()`* `beginGroupList()` / `endGroupList()`* `beginHitList()` / `endHitList()`

All of `Group`, `GroupList` and `HitList` are subclasses of `HitGroup`,
and the default implementation of the above methods is provided that calls
`beginHitGroup()` and `endHitGroup()`, respectively.
Furthermore, since all the attributes of those classes are regular fields
as defined by the root `Hit` class,
output is made by simply implementing `beginHitGroup()`,
`endHitGroup()`, and `hit()`.

### JSON example

Read the [default JSON result format](reference/default-result-format.html)
before implementing custom JSON renderers.
Example: Render a set of fields containing JSON data as a JSON array.
In other words, dump a variable length array containing all available data,
ignore everything else and silently ignore error states (i.e. good for prototyping):

```
{% highlight java %}
package com.yahoo.mysearcher;

import com.yahoo.search.Result;
import com.yahoo.search.query.context.QueryContext;
import com.yahoo.search.rendering.SectionedRenderer;
import com.yahoo.search.result.ErrorMessage;
import com.yahoo.search.result.Hit;
import com.yahoo.search.result.HitGroup;

import java.io.IOException;
import java.io.Writer;
import java.util.Collection;

public class MyRenderer extends SectionedRenderer {
    /**
     * A marker variable for the hit rendering to know whether
     * the hit being rendered is the first one that is rendered.
     */
    boolean firstHit;

    public void init() {
        firstHit = true;
    }

    @Override
    public String getEncoding() {
        return "utf-8";
    }

    @Override
    public String getMimeType() {
        return "application/json";
    }

    @Override
    public void beginResult(Writer writer, Result result) throws IOException {
        writer.write("[");
    }

    @Override
    public void endResult(Writer writer, Result result) throws IOException {
        writer.write("]");
    }

    @Override
    public void error(Writer writer, Collection errorMessages) throws IOException {
        // swallows errors silently
    }

    @Override
    public void emptyResult(Writer writer, Result result) throws IOException {
        //write nothing.
    }

    @Override
    public void queryContext(Writer writer, QueryContext queryContext) throws IOException {
        //write nothing.
    }

    @Override
    public void beginHitGroup(Writer writer, HitGroup hitGroup) throws IOException {
        //write nothing.
    }

    @Override
    public void endHitGroup(Writer writer, HitGroup hitGroup) throws IOException {
        //write nothing.
    }

    @Override
    public void hit(Writer writer, Hit hit) throws IOException {
        if (!firstHit) {
            writer.write(",\n");
        }
        writer.write(hit.toString());
        firstHit = false;
    }
}
{% endhighlight %}
```

## AsynchronousSectionedRenderer<Result>

This is the same as for the [processing framework](jdisc/processing.html#response-rendering).
It is conceptually similar to SectionedRenderer,
but has no special cases for search results as such.
The utility method getResponse() has a parametrized return type, though,
so templating the renderer on `Result` takes away some of the hassle.

Find an example in [DemoRenderer.java](https://github.com/vespa-engine/sample-apps/blob/master/examples/http-api-using-request-handlers-and-processors/src/main/java/ai/vespa/examples/DemoRenderer.java).
