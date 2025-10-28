---
# Copyright Vespa.ai. All rights reserved.
title: "Page Templates Syntax"
---

This document is a reference to the elements of the Page Template XML format.
Refer to the [Introduction to Page Templates](../page-templates.html).

A page template describes a particular way or set of ways of organizing data from some sources on a page.
It has the following structure:

```
<page id="[id]"> <!-- The top-level section of this page -->
    [page-element]*
</page>
```

…where each `[page-element]` is one of:

<[section](#section)>[page-element]*</section>
:   *A nested section (screen area)*

<[source](#source) name="[source-name]"> [renderer]* [parameter]* </source>
:   *A data source which should be placed in this section*

<[renderer](#renderer) name="[renderer-name]"> [parameter]* </renderer>
:   *The renderer to use for the source or section containing this*

<[choice](#choice)> [map] or [page-element]/[alternative]* </choice>
:   *A choice between alternative page elements resolved at runtime*

<placeholder id="[id]"/>
:   *an element to be replaced by a map item at runtime*

<[include](#include) idref="[page-id]">/>
:   *Include the page elements contained in another page*

where the nested elements above are:

<parameter name="[name]">[value]</parameter>
:   *A parameter of the owning element. Renderer parameters are sent
    as-is to the frontend in the result. Source parameters are sent to
    the source by setting the query
    parameter`source.[sourceName].[name]`.*

<alternative> [page-element]* </alternative>
:   *multiple page elements constituting one choice alternative*

<[map](#map) to="placeholder-id1 placeholder-id2 …"> [page-element]/[item]* </alternative>
:   *a mapping of some page elements to placeholders*

<[item](#item)> [page-element]* </item>
:   *multiple page elements which should all map to one placeholder*

All tags may also include a `description` attribute to document the use of the tag.
Tags and attributes are described in detail in the following.

## id

An id has the format:

```
id        ::= name(:major(.minor(.micro(.qualifier)?)?)?)?
name      ::= identifier
major     ::= integer
minor     ::= integer
micro     ::= integer
qualifier ::= identifier
```

Any omitted numeric version component missing is taken to mean 0,
while a missing qualifier is taken to mean the empty string.

## page

The root tag of a page template. Defines a page, is also its root section.
Attributes and subtags are the same as for [section](#section),
with the exception that the `id` attribute is mandatory for a page.

## section

A representation of an area of screen real-estate.
At runtime a section will contain content from various sources.
The final renderer will render the section with its data items
and/or subsections in an area of screen real-estate determined by its containing tag.

| Attribute | Description | Default |
| --- | --- | --- |
| id | A unique identifier of this section used for referring. | *No id* |
| layout | An identifier. Permissible values are `row`, `column` and any additional layouts supported by the renderer i of the returned page. | `column` |
| region | An identifier. The permissible values, and whether this is mandatory is determined by the particular layout identifier of the containing section (`row` and `column` does not specify any region identifiers). | *None* |
| source A space-separated set of sources permissible within this. This is a shorthand for defining sources as subtags. The total source list of this section consists of both the sources listed here and as subtags. | *All sources are permissible if none are specified.* | |
| max The maximum number of items permissible within this section (including any subsections). Regardless of the blending method used, the most relevant items are kept. | *Unrestricted* | |
| min | The minimum number of items desired within this. | *Unrestricted* |
| order | The method of ordering to use on the items displayed in this container. This may be any [sorting specification](sorting.html) over the fields of the hits, plus the source name and relevance score, for example `[source] -[relevance] category` to group by source, sort each group primarily by decreasing relevance and secondarily by the "category" field. The `[source]` identifier will sort sources by the order in which they are listed in the template in use. |  |

## source

A data source whose data should be placed in the containing section.

| Attribute | Description | Default |
| --- | --- | --- |
| name | The name of this source. | *Mandatory* |
| url | The url of this source. If this is set, the data of this source is *not* fetched, but instead the source tag (with url) will appear in the returned page such that the frontend may fetch it. This is provided primarily as a migration path, as such data can not be inspected and processed to optimize the returned page. | *No url: Fetch this configured source from the container.* |

## renderer

A renderer to use to render a section of a data item (hit) of a particular type.

| Attribute | Description | Default |
| --- | --- | --- |
| name | The name of this renderer. | *Mandatory* |
| for | The name of a hit type or a source this is the renderer for. | *If in a section: This is the renderer for the whole section. If in a source: This is the default renderer for hits from this source.* |

## choice

A choice between multiple alternative (lists of) page elements.
A resolver chooses between the possible alternatives for each request at runtime.
The `alternative` tag is used to enclose an alternative.
If an alternative consists of just one page element tag,
the enclosing alternative tag may be skipped.

| Attribute | Description | Default |
| --- | --- | --- |
| method | the name of the method for making the choice. Must be supported by the optimizer in use. | *Any method* |

### Contained tags

Either:

| Tag | Description | Default |
| --- | --- | --- |
| [page-element] | An alternative consisting of a single page element. | 0-n |
| alternative | An alternative consisting of multiple page elements. | 0-n |

or

| Tag | Description | Default |
| --- | --- | --- |
| [map](#map) | Specify all alternatives as a single mapping function. | 0-1 |

## map

Specify all the alternatives of a choice
as a mapping function of elements to placeholders.
A map is a convenience shorthand of writing many alternatives
in the case where a collection of elements should be mapped to a set of placeholders
with the constraint that each placeholder should get a unique element.
This is useful e.g. in the case where a set of sources are to be mapped to a set of sections.

| Attribute | Description | Default |
| --- | --- | --- |
| to | A space-separated list of the placeholder id's the map values should be mapped to. There cannot be more placeholder id's than there are values in this map (but fewer is ok). |

| Contained Tags | Description | Default |
| --- | --- | --- |
| [page-element] | A map item consisting of a single page element to map to a placeholder. | 0-n |
| item | An item containing multiple page elements to be mapped to a single placeholder. | 0-n |

## include

Includes the page elements contained directly in the `page`
element in the given page template (the page tag itself is not included).
Inclusion works exactly as if the `include` tag was
literally replaced by the content of the included page.

| Attribute | Description | Default |
| --- | --- | --- |
| idref | The id specification of the page to include. Portions of the version may be left unspecified to get the latest matching version. | *(Mandatory)* |
