---
# Copyright Vespa.ai. All rights reserved.
title: "Docker containers"
category: oss
redirect_from:
- /en/docker-containers-in-production.html
- /en/operations/docker-containers.html
---

This document describes tuning and adaptions for running Vespa Docker containers,
for developer use on laptop, and in production.

## Mounting persistent volumes

The [quick start](/en/vespa-quick-start.html)
and [AWS ECS multinode](/en/operations-selfhosted/multinode-systems.html#aws-ecs) guides
show how to run Vespa in Docker containers.
In these examples, all the data is stored inside the container - the data is lost if the container is deleted.
When running Vespa inside Docker containers in production,
volume mappings to the parent host should be added to persist data and logs.
* /opt/vespa/var
* /opt/vespa/logs

```
$ mkdir -p /tmp/vespa/var;  export VESPA_VAR_STORAGE=/tmp/vespa/var
$ mkdir -p /tmp/vespa/logs; export VESPA_LOG_STORAGE=/tmp/vespa/logs
$ docker run --detach --name vespa --hostname vespa-container \
  --volume $VESPA_VAR_STORAGE:/opt/vespa/var \
  --volume $VESPA_LOG_STORAGE:/opt/vespa/logs \
  --publish 8080:8080 \
  vespaengine/vespa
```

## Start Vespa container with Vespa user

You can start the container directly as the *vespa* user.
The *vespa* user and group within the container
are configured with user id *1000* and group id *1000*.
The vespa user and group must be the owner of the */opt/vespa/var*
and */opt/vespa/logs* volumes that are mounted in the container for Vespa to start.
This is required for Vespa to create the required directories and files within those directories.

The start script will check that the correct owner uid and gid are set
and fail if the wrong user or group is set as the owner.

When using an isolated user namespace for the Vespa container, you must set the uid and gid of the
directories on the host to the subordinate uid and gid, depending on your mapping.
See the [Docker documentation](https://docs.docker.com/engine/security/userns-remap/) for more details.

```
$ mkdir -p /tmp/vespa/var;  export VESPA_VAR_STORAGE=/tmp/vespa/var
$ mkdir -p /tmp/vespa/logs; export VESPA_LOG_STORAGE=/tmp/vespa/logs
$ sudo chown -R 1000:1000 $VESPA_VAR_STORAGE $VESPA_LOG_STORAGE
$ docker run --detach --name vespa --user vespa:vespa --hostname vespa-container \
  --volume $VESPA_VAR_STORAGE:/opt/vespa/var \
  --volume $VESPA_LOG_STORAGE:/opt/vespa/logs \
  --publish 8080:8080 \
  vespaengine/vespa
```

## System limits

When Vespa starts inside Docker containers, the startup scripts will set
[system limits](/en/operations-selfhosted/files-processes-and-ports.html#vespa-system-limits).
Make sure that the environment starting the Docker engine is set up in such a way
that these limits can be set inside the containers.

For a CentOS/RHEL base host, Docker is usually started by
[systemd](https://www.freedesktop.org/software/systemd/man/systemd.exec.html).
In this case, `LimitNOFILE`, `LimitNPROC` and `LimitCORE`
should be set to meet the minimum requirements in
[system limits](/en/operations-selfhosted/files-processes-and-ports.html#vespa-system-limits).

In general, when using Docker or Podman to run Vespa, the `--ulimit` option should be used
to set limits according to [system limits](/en/operations-selfhosted/files-processes-and-ports.html#vespa-system-limits).
The `--pids-limit` should be set to unlimited (`-1` for Docker and `0` for Podman).

## Transparent Huge Pages

Vespa performance improves significantly by enabling
[Transparent Huge Pages (THP)](https://www.kernel.org/doc/html/latest/admin-guide/mm/transhuge.html),
especially for memory-intensive applications with large dense tensors with concurrent query and write workloads.

One application improved query p99 latency from 950 ms to 150 ms during concurrent query and write by enabling THP.
Using THP is even more important when running in virtualized environments like AWS and GCP due to nested page tables.

When running Vespa using the container image, *THP* settings must be set on the base host OS (Linux).
The recommended settings are:

```
$ echo 1 >      /sys/kernel/mm/transparent_hugepage/khugepaged/defrag
$ echo always > /sys/kernel/mm/transparent_hugepage/enabled
$ echo never >  /sys/kernel/mm/transparent_hugepage/defrag
```

To verify that the setting is active, one should see that *AnonHugePages* is non-zero,
In this case, 75 GB has been allocated using AnonHugePages.

```
$ cat /proc/meminfo |grep AnonHuge

  AnonHugePages:  75986944 kB
```

Note that the Vespa container needs to be restarted after modifying the base host OS settings
to make the changes effective.
Vespa uses `MADV_HUGEPAGE` for memory allocations done by the
[content node process (proton)](/en/proton.html).

## Controlling which services to start

The Docker image *vespaengine/vespa*'s
[start script](https://github.com/vespa-engine/docker-image/blob/master/include/start-container.sh)
takes a parameter that controls which services are started inside the container.

Starting a *configserver* container:

```
$ docker run <other arguments> \
  --env VESPA_CONFIGSERVERS=<comma separated list of config servers> \
  vespaengine/vespa configserver
```

Starting a *services* container (configserver will not be started):

```
$ docker run <other arguments> \
  --env VESPA_CONFIGSERVERS=<comma separated list of config servers> \
  vespaengine/vespa services
```

Starting a container with *both configserver and services*:

```
$ docker run <other arguments> \
  --env VESPA_CONFIGSERVERS=<comma separated list of config servers> \
  vespaengine/vespa configserver,services
```

This is required in the case where the configserver container should run other services
like an adminserver or logserver (see [services.html](/en/reference/services.html))

If the [VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
environment variable is not specified, it will be set to the container hostname,
also see [node setup](/en/operations-selfhosted/node-setup.html#hostname).

Use the [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
sample application as a blueprint for how to set up config servers and services.

## Graceful stop

Stopping a running *vespaengine/vespa* container triggers a graceful shutdown,
which saves time when starting the container again
(i.e., data structures are flushed).
If the container is shut down forcefully,
the content nodes might need to restore the state from the transaction log, which might be time-consuming.
There is no chance of data loss or data corruption as the data is always written and synced to persistent storage.

The default timeout for the Docker daemon to wait for the shutdown
might be too low for larger number of documents per node.
Below stop will wait at least 120 seconds before terminating the running container forcefully,
if the stop is successfully performed before the timeout has passed, the command takes less than the timeout:

```
$ docker stop name -t 120
```

It is also possible to configure the default Docker daemon timeout,
see [--shutdown-timeout](https://docs.docker.com/reference/cli/dockerd/).

A clean content node shutdown looks like:

```
[2025-05-02 10:07:52.052] EVENT   searchnode       proton.node.server   stopping/1 name="storagenode" why="Stopped"
[2025-05-02 10:07:52.056] EVENT   searchnode       proton       stopping/1 name="servicelayer" why="clean shutdown"
[2025-05-02 10:07:52.056] INFO    searchnode       proton.proton.server.rtchooks        shutting down monitoring interface
[2025-05-02 10:07:52.058] INFO    searchnode       proton.searchlib.docstore.logdatastore      Flushing. Disk bloat is now at 0 of 8832 at 0.00 percent
[2025-05-02 10:07:52.059] INFO    searchnode       proton.searchlib.docstore.logdatastore      Flushing. Disk bloat is now at 0 of 8832 at 0.00 percent
[2025-05-02 10:07:52.060] INFO    searchnode       proton.searchlib.docstore.logdatastore      Flushing. Disk bloat is now at 0 of 8840 at 0.00 percent
[2025-05-02 10:07:52.066] INFO    searchnode       proton.transactionlog.server Stopping TLS
[2025-05-02 10:07:52.066] INFO    searchnode       proton.transactionlog.server TLS Stopped
[2025-05-02 10:07:52.071] EVENT   searchnode       proton       stopping/1 name="proton" why="clean shutdown"
[2025-05-02 10:07:52.078] EVENT   config-sentinel  sentinel.sentinel.service    stopped/1 name="searchnode" pid=354 exitcode=0
```

## Memory

The [sample applications](https://github.com/vespa-engine/sample-apps)
and [getting started guides](/en/getting-started.html)
indicates the minimum memory requirements for the Docker containers.

{% include note.html content="Too little memory is a very common problem when testing Vespa in Docker containers.
Use the below to troubleshoot before making a support request, and also see the [FAQ](/en/faq.html)."%}

As a rule of thumb, a single-node Vespa application requires a minimum of 4 GB for the Docker container.
Using `docker stats` can be useful to track memory usage:

```
$ docker stats

CONTAINER ID   NAME      CPU %     MEM USAGE / LIMIT    MEM %     NET I/O           BLOCK I/O        PIDS
589bf5801b22   node0     213.25%   697.3MiB / 3.84GiB   17.73%    14.2kB / 11.5kB   617MB / 976MB    253
e108dde84679   node1     213.52%   492.7MiB / 3.84GiB   12.53%    15.7kB / 12.7kB   74.3MB / 924MB   252
be43aacd0bbb   node2     191.22%   497.8MiB / 3.84GiB   12.66%    19.6kB / 21.6kB   64MB / 949MB     261
```

It is not necessarily easy to verify that Vespa has started all services successfully.
Symptoms of errors due to insufficient memory vary, depending on where it fails.
Example: Inspect restart logs in a container named *vespa*,
running the [quickstart](/en/vespa-quick-start.html) with only 2G:

```
$ docker exec -it vespa sh -c "/opt/vespa/bin/vespa-logfmt -S config-sentinel -c sentinel.sentinel.service"

INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 2.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 6.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 14.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 30.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: will delay start by 25.173 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 62.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 126.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: will delay start by 119.515 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 254.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 510.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: will delay start by 501.026 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 1022.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: incremented restart penalty to 1800.000 seconds
INFO    : config-sentinel  sentinel.sentinel.service	container: will delay start by 1793.142 seconds
```

Observe that the *container* service restarts in a loop, with increasing pause.

A common problem is [config servers](/en/operations-selfhosted/configuration-server.html)
not starting or running properly due to a lack of memory.
This manifests itself as nothing listening on 19071, or deployment failures.

Some guides/sample applications have specific configurations to minimize resource usage.
Example from [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA):

```
$ docker run --detach --name node0 --hostname node0.vespanet \
    -e VESPA_CONFIGSERVERS=node0.vespanet,node1.vespanet,node2.vespanet \
    -e VESPA_CONFIGSERVER_JVMARGS="-Xms32M -Xmx128M"  \
    -e VESPA_CONFIGPROXY_JVMARGS="-Xms32M -Xmx32M" \
    --network vespanet \
    --publish 19071:19071 --publish 19100:19100 --publish 19050:19050 --publish 20092:19092 \
    vespaengine/vespa
```

Here [VESPA_CONFIGSERVER_JVMARGS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
and [VESPA_CONFIGPROXY_JVMARGS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
are tweaked to the minimum for a functional test only.

{% include important.html content="For production use,
do not reduce memory settings in `VESPA_CONFIGSERVER_JVMARGS` and `VESPA_CONFIGPROXY_JVMARGS`
unless you know what you are doing -
the Vespa defaults are set for regular production use, and rarely need changing."%}

Container memory setting are done in *services.xml*, example from
[multinode-HA](https://github.com/vespa-engine/sample-apps/blob/master/examples/operations/multinode-HA/services.xml):

```
<container id="query" version="1.0">
    <nodes>
        <jvm options="-Xms32M -Xmx128M"/>
        <node hostalias="node6" />
        <node hostalias="node7" />
```

Make sure that the settings match the Docker container Vespa is running in.

Also see [node memory settings](/en/operations-selfhosted/node-setup.html#memory-settings) for more settings.

## Network

Vespa processes communicate over both fixed and ephemeral ports -
in general, all ports must be accessible.
See [example ephemeral use](/en/visiting.html#handshake-failed).

Find an example application using a Docker network in
[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA).

## Resource usage

Note that CPU usage will not be zero even if there are zero documents and zero queries.
Starting the *vespaengine/vespa* container image means starting the
[configuration server](/en/operations-selfhosted/configuration-server.html)
and the [configuration sentinel](/en/operations-selfhosted/config-sentinel.html).
When deploying an application, the sentinel starts the configured service processes,
and they all listen to work to do, changes in the config, and so forth.

Therefore, an "idle" container instance consumes CPU and memory.

## Troubleshooting

The Vespa documentation examples use `docker`.
The Vespa Team has good experience with using `podman`, too,
in the examples just change from `docker` to `podman`.
We recommend using Podman v5,
see the [release notes](https://github.com/containers/podman/blob/main/RELEASE_NOTES.md).
[emulating-docker-cli-with-podman](https://podman-desktop.io/docs/migrating-from-docker/emulating-docker-cli-with-podman)
is a useful resource.

Many startup failures are caused by a failed Vespa Container start due to configuration or download errors.
Use `docker logs vespa` to show the log (this example assumes a Docker container named `vespa`,
use `docker ps` to list containers).

### Docker image

Make sure to use a recent Vespa release (check [releases](https://factory.vespa.ai/releases))
and validate the downloaded image:

```
$ docker images
REPOSITORY                   TAG         IMAGE ID      CREATED       SIZE
docker.io/vespaengine/vespa  latest      8cfb0da22c01  35 hours ago  1.2 GB
```

### Model download failures

If the application package depends on downloaded models,
look for `RuntimeException: Not able to create config builder for payload` -
[details](/en/jdisc/container-components.html#component-load).
