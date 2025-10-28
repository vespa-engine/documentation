---
# Copyright Vespa.ai. All rights reserved.
title: "Healthchecks"
---

This is the reference for loadbalancer healthchecks to [containers](../jdisc).

By default, a container configures an instance of
[VipStatusHandler](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/container/handler/VipStatusHandler.java) to serve `/status.html`.
This will respond with status code 200 and text *OK* if content clusters are UP.
See [VipStatus.java](https://github.com/vespa-engine/vespa/blob/master/container-core/src/main/java/com/yahoo/container/handler/VipStatus.java) for details.

Applications with multiple content clusters should implement custom handlers for healthchecks,
if the built-in logic is inadequate for the usage.
Also refer to [federation](../federation.html) for how to manage data sources.

## Override using a status file

Use `container.core.vip-status` to make `VipStatusHandler` use a file for health status:

```
<container>
    <config name="container.core.vip-status">
        <accessdisk>true</accessdisk>
        <statusfile>/full-path-to/status-response.html</statusfile>
    </config>
```

If the file exists, its contents will be served on `/status.html`,
otherwise an error message will be generated.
To remove a container from service, delete or rename the file to serve.

## Alternative / multiple paths

`VipStatusHandler` only looks at a single file path by default.
As it is independent of the URI path,
it is possible to configure multiple handler instances to serve alternative or custom messages - example:

```
<handler id="vipFreshness" class="com.yahoo.container.handler.VipStatusHandler">
    <binding>http://*:*/docproc/freshness-data.xml</binding>
    <config name="container.core.vip-status">
        <accessdisk>true</accessdisk>
        <statusfile>/full-path-to/freshness-data.xml</statusfile>
    </config>
</handler>
<handler id="vipClustering" class="com.yahoo.container.handler.VipStatusHandler">
    <binding>http://*:*/docproc/ClusteringDocproc.status</binding>
    <config name="container.core.vip-status">
        <accessdisk>true</accessdisk>
        <statusfile>/full-path-to/ClusteringDocproc.status</statusfile>
    </config>
</handler>
```

The paths `/docproc/freshness-data.xml` and
`/docproc/ClusteringDocproc.status` serves the files located at
`/full-path-to/freshness-data.xml` and
`/full-path-to/ClusteringDocproc.status`, respectively.
As the handler instances are independent,
a container can be taken out of one type of rotation without affecting another.
