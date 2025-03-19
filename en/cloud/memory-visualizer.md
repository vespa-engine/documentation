---
# Copyright Vespa.ai. All rights reserved.
title: Memory Visualizer
category: cloud
---

The [schema](https://docs.vespa.ai/en/schemas.html) defines fields, types of fields and settings per field, e.g.

```
schema product {

    document product {

        field productId type long {
            indexing: summary | attribute
            attribute: fast-search
            rank: filter
        }

        field description type string {
            indexing: summary | index
        }

        ...
    }
}
```

The field types are often given by the application's data, but the _usage_ of the fields is also important - examples:

{:.list}
* high-speed updates to documents can be achieved by using attributes for memory-writes only,
  even though the field could be a summary or indexed field, use case permitting
* string fields can be faster than numeric, if the access is equality (not range like "price < 100")

In short, there are functional, performance and cost tradeoffs.
There are guides to help estimate resource use, see [attributes](https://docs.vespa.ai/en/attributes.html),
but often one does not know factors like number of unique values in the data.
It might as well be easier to feed the data to Vespa Cloud and do schema changes online and observe the effect.
Vespa Cloud has two features that accelerates this process - the Memory Visualizer and Automated Reindexing:

![Memory Visualizer](/assets/img/memory-visualizer-1.png)

The Memory Visualizer lets you browse the attribute fields and observe absolute and relative size.
This can help find the cost drivers for memory-bound applications, and identify bottlenecks for optimizations.

The Memory Visualizer is found in the "services" view in the console for an application.
Click a node of type "documentation (type: search)" and use the _Memory visualizer_ link.



## Adding or changing fields
Use the Memory Visualizer to track memory when adding a field.
Attribute, index and summary fields have different behavior when it comes to empty fields and memory use,
depending on data type - here, the tool indicates headroom for more data to assist in the evaluation.

Use the [field change procedure](https://docs.vespa.ai/en/operations/procedure-change-attribute-index.html)
to plan the schema changes for data availability in the transition.
The Console will display reindexing progress:

![Reindex progress](/assets/img/reindex-progress.png)

This makes it easy to estimate when the reindexing is complete.
Note that attribute memory usage might require a node restart for all data structures to drain,
take note of this when using the Memory Visualizer again.

<!-- ToDo: check with @geirst / link to how to trigger node restart, or just wait for next upgrade -->



## Using the visualizer
Some fields have a different color code.
To understand the types of fields,
read more about the [content node data structures](https://docs.vespa.ai/en/proton.html) - in short:

{:.list}
* `Ready` are indexed documents that might or might not be included in queries
* `Not Ready` are document replicas stored on the nodes that might be indexed later
* `Removed` are deleted documents, either by the application,
  or the document replica has been moved to another node
* `Documentmetastore` is the document ID mapping -
  see [attributes](https://docs.vespa.ai/en/attributes.html#document-meta-store)
