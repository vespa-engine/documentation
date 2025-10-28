---
# Copyright Vespa.ai. All rights reserved.
title: "services.xml - processing"
---

This document explains the syntax and semantics of the `processing` subelement of the
[`container`](services-container.html) part of `services.xml`.
`processing` is for configuring a pure
[request-response processing](../jdisc/processing.html) application,
with no particular dependency to search or query handling.
The processing block is used to configure [processors](../jdisc/processing.html):

```
processing
    binding
    processor [id, class, bundle, provides, before, after]
        provides
        before
        after
    renderer [id, class, bundle]
    chain [id, inherits, excludes]
        processor [idref, id, class, bundle, provides, before, after]
            provides
            before
            after
        inherits
            chain
            exclude
        phase [id, before, after]
            before
            after
```

Example:

```
<processing>
    <processor id="processor1" class="com.yahoo.test.Processor1" />
    <chain id="default">
        <processor idref="processor1"/>
        <processor id="processor2" class="com.yahoo.test.Processor2"/>
    </chain>
    <renderer id="renderer1" class="com.yahoo.test.Renderer1" />
</processing>
```

## binding

The URI to map the ProcessingHandler to. The default binding is
`http://*/processing/*`. Multiple elements are allowed.
Example:

```
<binding>http://*/processing/*</binding>
```

## processor

The definition of a single processor, for referencing when defining chains.
If a single processor is to be used in multiple chains,
it is cleaner to define it directly under `processing`
and then refer to it with `idref`,
than defining it inline separately for each chain.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The component ID |
| class | optional | string |  | The class of the component, defaults to id |
| bundle | optional | string |  | The bundle to load the component from, defaults to class or id (if no class is given) |
| before | optional | string |  | Space separated list of phases and/or processors which should succeed this processor |
| after | optional | string |  | Space separated list of phases and/or processors which should precede this processor |

Example:

```
<processor id="processor2" class="com.yahoo.test.Processor2"/>
```

## renderer

The definition of a renderer, for use by a Handler.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The component ID |
| class | optional | string |  | The class of the component, defaults to id |
| bundle | optional | string |  | The bundle to load the component from, defaults to class or id (if no class is given) |

Example:

```
<renderer id="renderer1" class="com.yahoo.test.Renderer1" />
```

## processor (in chain)

Reference to or inline definition of a processor in a chain.
If inlining, same as [processor](#processor) - if referring to,
use *idref* attribute:

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| idref |  | string |  | Reference to the definition of this processor. |

Example:

```
<chain id="default">
    <processor idref="processor2" />
</chain>
```

## provides

A name provided by a processor for phases and other processors to use as dependencies. Example:

```
<provides>IntentAnalysis</provides>
```

## chain

An element for defining a chain of
[processors](services-processing.html) /
[searchers](services-search.html)  /
[document processors](services-docproc.html) (i.e. components).
A chain is a set ordered by dependencies.
Dependencies are expressed through phases, which may depend upon other phases, or components.
For an incoming request from the network, the chain named *default* will be invoked.
Refer to [Chained components](../components/chained-components.html) for a guide.
Requires one of *id* or *idref*.

Searcher, Document processing and Processing chains can be modified at runtime without restarts.
Modification includes adding/removing processors in chains and changing names of chains and processors.
Make the change and [deploy](/en/application-packages.html#deploy).
Some changes require a container restart, refer to
[reconfiguring document processing](/en/document-processing.html#reconfiguring-document-processing).

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| idref |  | string |  | A reference to a defined chain. Mutually exclusive with *id*. If *idref* is used, no other attributes apply. |
| id | required | string |  | The chain ID. Required unless *idref* is used |
| inherits | optional | string |  | A space-separated list of chains this chain should include the contents of - see example below. |
| excludes | optional | string |  | A space-separated list of processors (contained in an inherited chain) this chain should not include. The exclusion is done before any consolidation of component references when inheriting chains. Example:   ``` <chain id="demo" inherits="idOfInheritedChain"                  excludes="idOfProc1 idOfProc2">     <processor id="proc2" class="com.yahoo.test.Proc2"/> </chain> ``` |
| class | optional | string |  |  |
| name |  |  |  |  |
| documentprocessors |  |  |  |  |

## inherits

Inherit from one or more parent chain(s).

When a search chain inherits from another search chain, it subsumes the phases
and the *searcher references* (both implicitly and explicitly defined) from the
parent chain.

If two or more inherited component references have the same name, a new component
specification matching those will be used instead. If that is not possible, an
error will be signaled (i.e. if the version specifications can not be
consolidated or if they require component definitions from different chains).

The component references determines which instances are used in the resulting chain instance.

A component reference is a component specification that says: there shall be
exactly one component in this chain with the given name,
and this component must match the version specification.

A component reference *overrides* any inherited
component references with the same name (i.e. the inherited ones are ignored).

If several components match a given component reference, the newest
(as determined by the version) is used.

## exclude

Exclude components from inherited chains.

## phase

Defines a phase, which is a named checkpoint to help order components inside a chain.
Components and other phases may depend on a phase to be able to make assumptions about the order of components.
Refer to the [Chained components](../components/chained-components.html) guide.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| id | required | string |  | The ID, or name, which other phases and processors may depend upon as a [successor](#before) or [predecessor](#after). |
| before | optional | string |  | Space-separated list of phases and/or processors which should succeed this phase |
| after | optional | string |  | Space-separated list of phases and/or processors which should precede this phase |

Optional sub-elements:
* before: same as the attribute
* after: same as the attribute

These are equivalent:

```
<phase id="name">
    <before>phaseName1</before>
    <after>phaseName2</after>
</phase>

<phase id="name" before="phaseName1" after="phaseName2" />
```

Example:

```
<chain id="demo">
    <phase id="CheckpointName">
        <before>IntentAnalysis</before>
        <after>OtherAnalysis</after>
    </phase>
    <processor id="processor2" class="com.yahoo.test.Processor2"/>
</chain>
```

## before

The name of a phase or component which should succeed this phase or component.
Multiple `before` elements can be used
to define multiple components or phases which always should succeed this component or phase in a chain.
In other words, the phase or component defined is placed *before* name in the element.

## after

The name of a phase or component which should precede this phase or component.
Multiple `after` elements can be used
to define multiple component or phases which always should precede this component or phase in a chain.
In other words, the phase or component defined is placed *after* the name in the element.
