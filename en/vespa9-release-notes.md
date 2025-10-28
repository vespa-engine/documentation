---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa 9 Release Notes"
---

This document lists the changes between Vespa major versions 8 and 9.
As documented in [Vespa versions](https://vespa.ai/releases#versions),
new functionality in Vespa is introduced in minor versions,
while major versions are used to mark releases breaking compatibility.
As Vespa 9 does not introduce any new functionality,
it is as safe and mature as the versions of Vespa 8 preceding it.

Note: This is work in progress, Vespa 9 is tentatively planned for
release in Q1 2026.

## Overview

The compatibility breaking changes in Vespa 9 fall into these categories:
* [Changes to default behaviour](#changed-defaults)
* [Application package structure and settings](#application-package-changes) -
  deprecated settings and constructs in e.g. *schemas* and *services.xml* are removed.
* [Java APIs](#java-api-changes) -
  deprecated APIs are removed or revoked from Vespa's
  [public API](https://javadoc.io/doc/com.yahoo.vespa/annotations/latest/com/yahoo/api/annotations/PublicApi.html) surface.
* [Container runtime environment](#container-runtime) -
  incompatible changes to the Java build and runtime environments.
* [HTTP API changes](#removed-http-api-parameters)
* [Removed command line tools](#removed-command-line-tools)
* [Removed or renamed metrics](#removed-or-renamed-metrics)
* [Security related changes](#security)
* [Operating system support](#operating-system)
* [Other changes](#other-changes), not covered by any of the above categories.

To ensure their applications are compatible with Vespa 9, application owners must:
* Review the list of [changes to defaults](#changed-defaults) and add the necessary options
  if you want to preserve behavior from Vespa 8.
* Make sure there are no deprecation warnings when compiling against Vespa 8.
* Review the [application package changes](#application-package-changes) and make sure there
  are no deployment warnings when deploying on Vespa 8.
* Review the list of [HTTP API changes](#removed-http-api-parameters) and update
  any clients of the application.
* Review the remaining sections of this document, and update the application and its environment accordingly.

Usage of deprecated Java APIs produce warnings during compilation, while *deployment warnings*
are produced for application package deprecations and most changes to the container runtime environment.
In hosted Vespa or Vespa Cloud, deployment warnings are shown in the application's console view.
However, for other types of changes, there is no way to emit deprecation warnings,
so these are only described in this document and other Vespa documentation.

The following sections lists all the changes from Vespa 8 to Vespa 9 in detail.

## Changed defaults

These changes may break clients, and impact both performance and user experience.
Applications that are in production and relies on these defaults should
make configuration changes to keep the existing behavior when upgrading to Vespa 8.
This can be done on Vespa 8, *before* upgrading -
using [bucket tests](testing.html#feature-switches-and-bucket-tests) can be useful.

The following defaults have changed:

| Change | Configuration required to avoid change on Vespa 9 |
| --- | --- |

## Application package changes

### Removed settings from schemas

The following settings are removed from
[schema](reference/schema-reference.html):

| Name | Replacement |
| --- | --- |

### Changed semantics in services.xml

The following elements and attributes in services.xml have new semantics:

| Name | Description |
| --- | --- |

### Removed constructs from services.xml

The following elements and attributes are removed from services.xml:

| Parent element | Removed construct | Description |
| --- | --- | --- |

### *searchdefinitions/* folder support removed

Schemas should now be placed in the *schemas/* folder.

## Java API changes

### Removed Java packages

| Package | Description |
| --- | --- |

### Removed Java Classes and methods

Classes and methods that were marked as deprecated in Vespa 8 are removed.
If deprecation warnings are emitted for Vespa APIs when building the application,
these must be fixed before migrating to Vespa 9. The sections below contain only the
most notable changes.

The following classes are no longer public API and have been moved to Vespa internal packages:

| Package | Class | Migration advice |
| --- | --- | --- |
| com.yahoo.search.predicate | *PredicateIndex* + related classes | The Predicate Search Java Library is removed (*com.yahoo.vespa:predicate-search*). Use [predicate fields](predicate-fields.html) in Vespa instead. |

The following methods are removed:

| Method | Migration advice |
| --- | --- |

### Breaking changes to Java APIs

The Javadoc of the deprecated types/members should document the replacement API.
The below list is not exhaustive - some smaller and trivial changes are not listed.

| Type(s) | Description |
| --- | --- |

### Deprecated Java APIs

A few redundant APIs have been deprecated because they have replacements that
provide the same, or better, functionality. We advise you switch to the
replacement to reduce future maintenance cost.

| Type(s) | Replacement |
| --- | --- |

## Container Runtime Environment

### JDK version

Vespa 9 upgrades the JDK version from 17 to 25. Java artifacts built against older JDK versions
will still be compatible with Vespa 9 (JDK 25). The opposite will not be possible - Vespa 8
(JDK 21) is not compatible with newer JVM byte code. It's possible though to use the
*--release* option for *javac* to target an older JDK version.

### Changes to provided maven artifacts

The following Maven artifacts are no longer provided runtime to user application plugins by the Jdisc container:

| Artifact | Notes |
| --- | --- |

Make sure your application OSGi bundle embeds the required artifacts from the above list.
An artifact can be embedded by adding it in scope *compile* to the *dependencies* section in pom.xml.
Typically, these artifacts have until now been used in scope *provided*.
Use `mvn dependency:tree` to check whether any of the listed artifacts are directly or transitively included
as dependencies.

As always, remove any dependencies that are not required by your project. Consult the Maven documentation on
[Dependency Exclusions](https://maven.apache.org/guides/introduction/introduction-to-optional-and-excludes-dependencies.html#dependency-exclusions) for how to remove a transitively included dependency.

An example adding *org.json:json* as a compile scoped dependency:

```
<dependencies>
  ...
  <dependency>
    <groupId>org.json</groupId>
    <artifactId>json</artifactId>
    <version>20211205</version>
    <scope>compile</scope>
  </dependency>
  ...
</dependencies>
```

## Removed HTTP API parameters

The following HTTP API parameters are removed from the [query API](reference/query-api-reference.html):

| Standard API path | Parameter name | Replacement |
| --- | --- | --- |

## Removed command line tools

## Removed or renamed metrics

The following metrics are renamed:

The following metrics are removed:

## Security

## Operating system support for Vespa artifacts

### OCI containers (Docker containers)

## Other changes

### Changes in rankfeatures

Vespa can calculate and return all [rank-features](reference/query-api-reference.html#ranking.listfeatures)
in the `rankfeatures` summary field. Vespa 9 contains some changes to this list:

### Upgrade procedure

See [upgrade procedure](/en/operations-selfhosted/live-upgrade.html) for how to upgrade.
