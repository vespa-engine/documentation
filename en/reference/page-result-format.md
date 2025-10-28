---
# Copyright Vespa.ai. All rights reserved.
title: "The Vespa Search API - Page result format"
---

This document describes the `page` result format returned by Vespa.
This result format is used when [presentation.format](query-api-reference.html#presentation.format)
is set to `page`.
This format is usually used with [page templates](../page-templates.html).

The tags of the format are described below.
Subtags will be rendered in the order listed here.
The format is *open*,
all parsers must ignore tags may contain attributes and child tags not mentioned here.

## <page>

The root tag of a page result: The single top-level section of the page.

| Attribute | Description | Present |
| --- | --- | --- |
| version | The version of this format - currently 1.0. | Always |
| layout | The name of the top-level layout to use for this page. | If specified in the page template used. |

For regular permissible subtags, refer to [section](#section).

## <section>

A layout "box" in a page.

| Attribute | Description | Present |
| --- | --- | --- |
| id | The id of this section. | If specified in the page template used. |
| layout | The name of the top-level layout to use for this page. | If specified in the page template used. |
| region | The id of the region in the layout of the parent section where this should be placed. | If specified in the page template used. |

| Subtag | Description | Present |
| --- | --- | --- |
| [section](#section) | A nested section of this page | Zero or more. |
| [renderer](#renderer) | The name of the rendering to use for this section. | Zero or more. |
| [source](#source) | Used to specify where to fetch the content of this section if it is not sent with this page in a content tag. | One or zero. |
| [content](#content) | Contains some "payload" of this page - a set of [hit](#hit) instances | One if this section has inlined content, zero otherwise. |

## <renderer>

The way this section, or some of its content should be rendered.

| Attribute | Description | Present |
| --- | --- | --- |
| for The name of the content source which should use this renderer If this is not present, the renderer should be used for the entire section. | | |

| Subtag | Description | Present |
| --- | --- | --- |
| parameter A parameter to this renderer Zero or more | | |

## <source>

The source to be used to fetch the content of a section,
if it is not sent as inline [content](#content).

| Attribute | Description | Present |
| --- | --- | --- |
| url The url at which the content should be fetched. Always. | | |

| Subtag | Description | Present |
| --- | --- | --- |
| parameter A parameter to use when fetching this content. Zero or more | | |

## <content>

The content to render in a section.

| Subtag | Description | Present |
| --- | --- | --- |
| [hit](#hit) A content hit. Zero or more. | | |
| [group](#group) A group of content hits. Zero or more. | | |

## <hit>

A single result content item.

| Attribute | Description | Present |
| --- | --- | --- |
| relevance The relevance of this item - usually a normalized number between 0 and 1. Always | | |
| source The name of the source producing this hit. Always | | |
| type A space-separated list of type identifiers of this hit. If a type is set in the hit. | | |

Subtags:

Hits have one subtag for every field they contain,
where the field name is the name of the tag and the toString of the field content is the content of the tag.

## <group>

A [hit](#hit) which contains nested hits. Used to organize hits hierarchically.
Has the name attributes and subtags as [hit](#hit),
but may also contain nested [hit](#hit) and [group](#group) tags.

## Example

A page which should be rendered with two columns on top.

```
<page version="1.0">

    <renderer name="two-column"/>

    <section region="left">
        <source url="http://host:port/resource/[news article id]"/>
        <renderer name="articleBodyRenderer">
            <parameter name="color">blue</parameter>
        </renderer>
    </section>

    <section region="right">
        <renderer name="multi-item-column">
            <parameter name="items">3</parameter>
        </renderer>
        <section region="1">
            <renderer for="newsImage" name="newsImageRenderer"/>
            <renderer for="news" name="articleRenderer"/>
            <renderer for="image" name="imageRenderer"/>
            <content>
                <hit relevance="1.0" source="news">
                    <id>news-1</id>
                </hit>
                <hit relevance="0.5" source="news">
                    <id>news-2</id>
                </hit>
            </content>
        </section>
        <section region="2">
            <source url="http://host:port/consumption-widget"/>
            <renderer name="identityRenderer"/>
        </section>
        <section region="3">
            <renderer name="htmlRenderer"/>
            <content>
                <hit relevance="1.0" source="htmlSource">
                    <id>htmlSource-1</id>
                </hit>
            </content>
        </section>
    </section>
</page>
```
