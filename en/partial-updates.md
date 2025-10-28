---
# Copyright Vespa.ai. All rights reserved.
title: "Partial Updates"
---

A partial update is an update to one or more fields in a document.
It also includes updating all index structures so the effect of the
partial update is immediately observable in queries. See
[document update JSON format](reference/document-json-format.html#update)
for full details on the various possible partial update operations.

![Attribute is an in-memory data structure](/assets/img/attributes-update.svg)

In Vespa, all fields can be partially updated by default.
A field is index, attribute or summary or a combination of these,
and both index and attribute fields can be queried.
* For [index](proton.html#index) and summary fields,
  an update means a read-modify-write to the
  [document store](proton.html#document-store)
  and limits throughput.
* Most [attribute](attributes.html) fields do not
  require the document store read-modify-write, increasing write
  throughput by orders of magnitude.
  The following attribute types require a read-modify-write to the document store:
  + [array of struct](reference/schema-reference.html#array)
  + [map of primitive and struct](reference/schema-reference.html#map)
  + [predicate](reference/schema-reference.html#predicate)
  + [reference](reference/schema-reference.html#reference)

{% include important.html content="For highest possible write throughput for field updates,
use attributes to write at memory speed." %}

| Field Setting | Searchable | Fast searchable | Matching | Ranking | Display in results |
| --- | --- | --- | --- | --- | --- |
| index | Y | Y | Text and Exact matching | Y | N |
| attribute | Y | Y with attribute:fast-search | Exact matching | Y | Y |
| summary | N | N | N | N | Y |

Examples:

|  |  |
| --- | --- |
| ``` field user type string {     indexing: summary | index } ``` | Summary + index field. The field is stored in the document store, a partial update to the field will trigger read + write. |
| ``` field user type string {     indexing: attribute } ``` | Attribute only field. The field is stored in the attribute (in-memory) and a partial update will update the document in-place and will be visible for queries, ranking, grouping and sorting immediately. |

## Use cases

Partial updates have many use cases.
*Functionally*, it enables updating a document without anything else than the ID,
simplifying logic in the upper levels of the serving stack.
*Performance-wise*, partial updates enables applications with a real-time update flow
in tens of thousands updates per second. Examples:

| Use case | Description |
| --- | --- |
| Filtering | Inventory updates | Update product price and inventory count in real time. Do not show items out of stock. |
| Update relations | Add a "this person likes me" to the "likes me" [set](reference/query-language-reference.html#weightedset) - display candidates based on sets of likes/dislikes/other relations. |
| Ranking |  | Update click / views / non-clicks: Feed usage data to use in ranking - rank popular items higher. |

## Write pipeline

Refer to [proton](proton.html) for an overview of the write-pipeline
and the Transaction Log Server (TLS).

| Field Setting | Description |
| --- | --- |
| index | For all [indexed fields](reference/schema-reference.html#index), a memory index is used for the recent changes, implemented using B-trees. This is periodically [flushed](proton.html#memory-index-flush) to a disk-based posting list index. Disk-based indexes are subsequently [merged](proton.html#disk-index-fusion).  Updating the in-memory B-trees is lock-free, implemented using copy-on-write semantics. This gives high performance, with a predictable steady-state CPU/memory use. The driver for this design is the requirement for a sustained, high change rate, with stable, predictable read latencies and small temporary increases in CPU/memory. This compared to index hierarchies, merging smaller real-time indices into larger, causing temporary hot-spots.  When updating an indexed field, the document is read from the [document store](proton.html#document-store), the field is updated, and the full document is written back to the store. At this point, the change is searchable, and an ACK is returned to the client. Use [attributes](attributes.html) to avoid such document disk accesses and increase performance for partial updates. Find more details in [feed performance](performance/sizing-feeding.html). |
| attribute | Attribute fields are in-memory fields, see [attributes](attributes.html). This makes updates inexpensive and fast. Attribute data is periodically flushed, see [attribute-flush](proton.html#attribute-flush). Note that operations are persisted to the Transaction Log Service (TLS), in the rare case of a power failure or unclean shutdown, the operations are synced from the TLS.  Note there is no transactional support for updates across fields. To support high rate, there is no coordination between threads - example:   ``` {% highlight json %} {     "update" : "id:namespace:doctype::1",     "fields" : {         "firstName" : { "assign" : "John" },         "lastName"  : { "assign" : "Smith" }     } } {% endhighlight %} ```   Above, the attributes *firstName* and *lastName* are updated in the same operation from the client, whereas the update in the search core is non-transactional. This is a throughput vs consistency tradeoff that enables the extreme update rates without being a practical limitation for many applications. More details in [attributes](attributes.html).  Updating [multivalue](schemas.html#field) attributes (arrays, maps, sets, tensors) means reading the current value, making the update and writing it back:   * [Array of primitive types](reference/schema-reference.html#array),   [weightedsets](reference/schema-reference.html#weightedset) and   [tensors](reference/schema-reference.html#tensor) are in memory and therefore fast,   see [attribute data structures](attributes.html#data-structures) for performance considerations. * If the attribute field is an [array of struct](reference/schema-reference.html#array) or   [map](reference/schema-reference.html#map),   values are written in the document store and update rates are hence lower -   refer to [#10892 updates of array of map/struct](https://github.com/vespa-engine/vespa/issues/10892).   Query execution time can be improved by adding an in-memory B-tree posting list structure using [fast-search](performance/feature-tuning.html#when-to-use-fast-search-for-attribute-fields). This increases work when updating, as both the value and the posting list is updated and hence decreases update throughput.  See [sizing-feeding](performance/sizing-feeding.html#attribute-store) for how to ensure an attribute is in memory on all nodes with a replica (searchable-copies or fast-access). |
| summary | An update to the [document store](proton.html#document-store) is read the current version, modify and write back a new blob. Refer to [document summaries](document-summaries.html).  Attribute fields that are also in summary get their values from the memory structures, not the document store. Use [summary class](reference/schema-reference.html#document-summary) with attributes only for applications with high write/query rates using memory only. |

## Further reading
* [reads and writes](reads-and-writes.html) - functional overview of the Document API
* [sizing-feeding](performance/sizing-feeding.html) - troubleshooting
* [attributes](attributes.html) - to understand all aspects of attributes
* [proton](proton.html) - this should have the full write pipeline, go here for this
* [parent-child](parent-child.html) - how to use parent attributes for even higher update rates
