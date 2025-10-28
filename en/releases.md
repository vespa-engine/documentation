---
# Copyright Vespa.ai. All rights reserved.
title: "Releases"
---

Vespa is released every Monday through Thursday. Each public release has passed all
functional and performance tests, and is already running the applications on our
public cloud service.



For each Vespa release, the following artifacts are provided:
* [Java artifacts for building Vespa applications on Maven Central](https://search.maven.org/artifact/com.yahoo.vespa/parent)
* [Vespa RPMs on Fedora Copr](https://copr.fedorainfracloud.org/coprs/g/vespa/vespa/)
* [Container images on Docker Hub](https://hub.docker.com/repository/docker/vespaengine/vespa)



Releases:
* [Vespa 7](/en/vespa7-release-notes.html)
* [Vespa 8](/en/vespa8-release-notes.html)



Use the [Vespa Factory](https://factory.vespa.ai/releases)
to inspect the commits in each release:

![Screenshot of commit list diff per release](/assets/commits-release.png)

## Versions

Vespa uses [semantic versioning](https://semver.org/).
Each release is backwards compatible and supports live migration on running systems, provided they
are running a version which is less than 2 months old.
It is therefore a minor version number change. All new features are released on such minor versions.
Every second year or so we make a major version change which removes previously deprecated
functionality.

Java APIs, web service APIs and all application package constructs are supported through a major release
and only removed on a new release if they are already marked deprecated.

Use of deprecated Java APIs will cause a warning on compilation,
and use of deprecated application package constructs will cause a deprecation warning on deployment.
Note that Java APIs come in two categories:
* *Public APIs* carry the compatibility guarantee and are visible from your code
  as well as in the javadoc
* *Exported APIs* are also visible from your code,
  but is not in the public Javadoc and carry no compatibility guarantee

Check the Javadoc list to verify that you are using public packages.

In addition, some public Java classes and methods are marked with the com.yahoo.api.annotations.Beta tag.
These are under development and may still change before they stabilize.

## Stored Data

Data written to Vespa is compatible between adjacent releases.
For self-hosted systems, it may be necessary to upgrade through each
minor release rather than in larger leaps to ensure Vespa can read existing data.
This is a good practice in any case.
