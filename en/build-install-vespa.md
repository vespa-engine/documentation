---
# Copyright Vespa.ai. All rights reserved.
title: "Build / install Vespa"
---

To develop with Vespa, follow the
[guide](https://github.com/vespa-engine/vespa#building)
to set up a development environment on AlmaLinux 8 using Docker.

Build Vespa Java artifacts with Java >= 17 and Maven >= 3.6.3.
Once built, Vespa Java artifacts are ready to be used and one can build a Vespa application
using the [bundle plugin](components/bundles.html#maven-bundle-plugin).

```
$ export MAVEN_OPTS="-Xms128m -Xmx1024m"
$ ./bootstrap.sh java && mvn install
```

See [vespa.ai releases](https://vespa.ai/releases).

## Container images

| Image | Description |
| --- | --- |
| [docker.io/vespaengine/vespa](https://hub.docker.com/r/vespaengine/vespa)  [ghcr.io/vespa-engine/vespa](https://github.com/orgs/vespa-engine/packages/container/package/vespa) | Container image for running Vespa. |
| [docker.io/vespaengine/vespa-build-almalinux-8](https://hub.docker.com/r/vespaengine/vespa-build-almalinux-8) | Container image for building Vespa on AlmaLinux 8. |
| [docker.io/vespaengine/vespa-dev-almalinux-8](https://hub.docker.com/r/vespaengine/vespa-dev-almalinux-8) | Container image for development of Vespa on AlmaLinux 8. Used for incremental building and system testing. |

## RPMs

Dependency graph:

![RPM overview](/assets/img/rpms.svg)

Installing Vespa on AlmaLinux 8:

```
$ dnf config-manager \
  --add-repo https://raw.githubusercontent.com/vespa-engine/vespa/master/dist/vespa-engine.repo
$ dnf config-manager --enable powertools
$ dnf install -y epel-release
$ dnf install -y vespa
```

Package repository hosting is graciously provided by [Cloudsmith](https://cloudsmith.com) which is a fully hosted, cloud-native
and universal package management solution:
[![OSS hosting by Cloudsmith](https://img.shields.io/badge/OSS%20hosting%20by-cloudsmith-blue?logo=cloudsmith&style=flat-square)](https://cloudsmith.com)

{% include important.html content="Please note that the retention of released RPMs in the repository is limited to the latest 50 releases.
Use the Docker images (above) for installations of specific versions older than this.
Any problems with released rpm packages will be fixed in subsequent releases,
please [report any issues](https://vespa.ai/support) -
troubleshoot using the [install example](/en/operations-selfhosted/multinode-systems.html#aws-ec2-singlenode)." %}

Refer to [vespa.spec](https://github.com/vespa-engine/vespa/blob/master/dist/vespa.spec).
Build RPMs for a given Vespa version X.Y.Z:

```
$ git clone https://github.com/vespa-engine/vespa
$ cd vespa
$ git checkout vX.Y.Z
$ docker run --rm -ti -v $(pwd):/wd:Z -w /wd  \
         docker.io/vespaengine/vespa-build-almalinux-8:latest \
         make -f .copr/Makefile rpms outdir=/wd
$ ls *.rpm | grep -v debug
vespa-{{site.variables.vespa_version}}-1.el8.src.rpm
vespa-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-ann-benchmark-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-base-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-base-libs-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-clients-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-config-model-fat-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-jars-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-libs-{{site.variables.vespa_version}}.el8.x86_64.rpm
vespa-malloc-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-node-admin-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
vespa-tools-{{site.variables.vespa_version}}-1.el8.x86_64.rpm
```

Find most utilities in the vespa-x.y.z*.rpm - other RPMs:

| RPM | Description |
| --- | --- |
| vespa-tools | Tools accessing Vespa endpoints for query or document operations:  * [vespa-destination](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-destination) * [vespa-fbench](/en/operations/tools.html#vespa-fbench) * [vespa-feeder](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-feeder) * [vespa-get](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-get) * [vespa-query-profile-dump-tool](/en/operations/tools.html#vespa-query-profile-dump-tool) * [vespa-stat](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-stat) * [vespa-summary-benchmark](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-summary-benchmark) * [vespa-visit](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-visit) * [vespa-visit-target](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-visit-target) |
| vespa-malloc | Vespa has its own memory allocator, *vespa-malloc* - refer to */opt/vespa/etc/vespamalloc.conf* |
| vespa-clients | *vespa-feed-client.jar* - see [vespa-feed-client](vespa-feed-client.html) |
