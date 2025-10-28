---
# Copyright Vespa.ai. All rights reserved.
title: "Administrative Procedures"
category: oss
redirect_from:
- /en/operations/admin-procedures.html
---

## Install

Refer to the [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA) sample application for a primer on how to set up a cluster -
use this as a starting point.
Try the [Multinode testing and observability](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode) sample app to get familiar with interfaces and behavior.

## Vespa start / stop / restart

Start and stop all services on a node:

```
$ $VESPA_HOME/bin/vespa-start-services
$ $VESPA_HOME/bin/vespa-stop-services
```

Likewise, for the config server:

```
$ $VESPA_HOME/bin/vespa-start-configserver
$ $VESPA_HOME/bin/vespa-stop-configserver
```

There is no *restart* command, do a *stop* then *start* for a restart.
Learn more about which processes / services are started at [Vespa startup](/en/operations-selfhosted/config-sentinel.html),
read the [start sequence](/en/operations-selfhosted/configuration-server.html#start-sequence)
and find training videos in the vespaengine [YouTube channel](https://www.youtube.com/@vespaai).

Use [vespa-sentinel-cmd](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-sentinel-cmd)
to stop/start individual services.

{% include important.html content="Running *vespa-stop-services* on a content node will call
[prepareRestart](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-proton-cmd) to optimize restart time,
and is the recommended way to stop Vespa on a node." %}

See [multinode](multinode-systems.html#aws-ec2) for *systemd* /*systemctl* examples.
[Docker containers](/en/operations-selfhosted/docker-containers.html) has relevant start/stop information, too.

### Content node maintenance mode

When stopping a content node *temporarily* (e.g. for a software upgrade), consider manually setting the node into
[maintenance mode](../reference/cluster-v2.html#maintenance) *before* stopping the node to prevent
automatic redistribution of data while the node is down. Maintenance mode must be manually removed once the node has
come back online. See also: [cluster state](#cluster-state).

Example of setting a node with [distribution key](../reference/services-content.html#node) 42 into
`maintenance` mode using [vespa-set-node-state](vespa-cmdline-tools.html#vespa-set-node-state),
additionally supplying a reason that will be recorded by the cluster controller:

```
  $ vespa-set-node-state --type storage --index 42 maintenance "rebooting for software upgrade"
```

After the node has come back online, clear maintenance mode by marking the node as `up`:

```
  $ vespa-set-node-state --type storage --index 42 up
```

Note that if the above commands are executed *locally* on the host running the services for node 42,
`--index 42` can be omitted; `vespa-set-node-state` will use the distribution key of
the local node if no `--index` has been explicitly specified.

## System status
* Use [vespa-config-status](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-config-status)
  on a node in [hosts.xml](../reference/hosts.html) to verify all services run with updated config
* Make sure [VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables) is set and identical on all nodes in hosts.xml
* Use the *cluster controller* status page (below)
  to track the status of search/storage nodes.
* Check [logs](../reference/logs.html)
* Use performance graphs, System Activity Report (*sar*)
  or [status pages](#status-pages) to track load
* Use [query tracing](../reference/query-api-reference.html#trace.level)
* Disk and/or memory might be exhausted and block feeding - recover from
  [feed block](/en/operations/feed-block.html)

## Status pages

All Vespa services have status pages, for showing health, Vespa version, config, and metrics.
Status pages are subject to change at any time - take care when automating. Procedure:

1. **Find the port:**
   The status pages runs on ports assigned by Vespa. To find status page ports,
   use [vespa-model-inspect](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect)
   to list the services run in the application.

   ```
   $ vespa-model-inspect services
   ```

   To find the status page port for a specific node for a specific service,
   pick the correct service and run:

   ```
   $ vespa-model-inspect service [Options] <service-name>
   ```
2. **Get the status and metrics:**
   *distributor*, *storagenode*, *searchnode* and
   *container-clustercontroller* are content services with status pages.
   These ports are tagged HTTP. The cluster controller have multiple ports tagged HTTP,
   where the port tagged STATE is the one with the status page.
   Try connecting to the root at the port, or /state/v1/metrics.
   The *distributor* and *storagenode* status pages are available at `/`:

   ```
   $ vespa-model-inspect service searchnode

     searchnode @ myhost.mydomain.com : search
     search/search/cluster.search/0
     tcp/myhost.mydomain.com:19110 (STATUS ADMIN RTC RPC)
     tcp/myhost.mydomain.com:19111 (FS4)
     tcp/myhost.mydomain.com:19112 (TEST HACK SRMP)
     tcp/myhost.mydomain.com:19113 (ENGINES-PROVIDER RPC)
     tcp/myhost.mydomain.com:19114 (HEALTH JSON HTTP)
     $ curl http://myhost.mydomain.com:19114/state/v1/metrics
     ...
     $ vespa-model-inspect service distributor
     distributor @ myhost.mydomain.com : content
     search/distributor/0
     tcp/myhost.mydomain.com:19116 (MESSAGING)
     tcp/myhost.mydomain.com:19117 (STATUS RPC)
     tcp/myhost.mydomain.com:19118 (STATE STATUS HTTP)
     $ curl http://myhost.mydomain.com:19118/state/v1/metrics
     ...
     $ curl http://myhost.mydomain.com:19118/
     ...
   ```
3. **Use the cluster controller status page**:
   A status page for the cluster controller is available at the status port at
   `http://hostname:port/clustercontroller-status/v1/<clustername>`.
   If *clustername* is not specified, the available clusters will be listed.
   The cluster controller leader status page will show if any nodes are operating with differing cluster state versions.
   It will also show how many data buckets are pending merging (document set reconciliation)
   due to either missing or being out of sync.

   ```
   $ vespa-model-inspect service container-clustercontroller | grep HTTP
   ```

   With multiple cluster controllers, look at the one with a "/0" suffix in its config ID;
   it is the preferred leader.

   The cluster state version is listed under the *SSV* table column.
   Divergence here usually points to host or networking issues.

## Cluster state

Cluster and node state information is available through the
[/cluster/v2 API](../reference/cluster-v2.html).
This API can also be used to set a *user state* for a node - alternatively use:
* [vespa-get-cluster-state](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-get-cluster-state)
* [vespa-get-node-state](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-get-node-state)
* [vespa-set-node-state](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-set-node-state)

Also see the cluster controller [status page](#status-pages).

State is persisted in a ZooKeeper cluster, restarting/changing a cluster controller preserves:
* Last cluster state version number, for new cluster controller handover at restarts
* User states, set by operators - i.e. nodes manually set to down / maintenance

In case of state data lost, the cluster state is reset - see
[cluster controller](../content/content-nodes.html#cluster-controller) for implications.

## Cluster controller configuration

It is recommended to run cluster controllers on the same hosts as
[config servers](/en/operations-selfhosted/configuration-server.html),
as they share a zookeeper cluster for state and deploying three nodes is best practise for both.
See the [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
sample app for a working example.

To configure the cluster controller, use
[services.xml](../reference/services-content.html#cluster-controller) and/or add
[configuration](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def) under the *services* element - example:

```
<services version="1.0">
    <config name="vespa.config.content.fleetcontroller">
        <min_time_between_new_systemstates>5000</min_time_between_new_systemstates>
    </config>
```

A broken content node may end up with processes constantly restarting.
It may die during initialization due to accessing corrupt files,
or it may die when it starts receiving requests of a given type triggering a node local bug.
This is bad for distributor nodes,
as these restarts create constant ownership transfer between distributors,
causing windows where buckets are unavailable.

The cluster controller has functionality for detecting such nodes.
If a node restarts in a way that is not detected as a controlled shutdown, more than
[max_premature_crashes](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def),
the cluster controller will set the wanted state of this node to be down.

Detecting a controlled restart is currently a bit tricky.
A controlled restart is typically initiated by sending a TERM signal to the process.
Not having any other sign,
the content layer has to assume that all TERM signals are the cause of controlled shutdowns.
Thus, if the process keep being killed by kernel due to using too much memory,
this will look like controlled shutdowns to the content layer.

## Monitor distance to ideal state

Refer to the [distribution algorithm](../content/idealstate.html).
Use distributor [status pages](#status-pages) to inspect state metrics,
see [metrics](../content/content-nodes.html#metrics).
`idealstate.merge_bucket.pending` is the best metric to track,
it is 0 when the cluster is balanced - a non-zero value indicates buckets out of sync.

## Cluster configuration
* Running `vespa prepare` will not change served
  configuration until `vespa activate` is run.
  `vespa prepare` will warn about all config changes that require restart.
* Refer to [schemas](../schemas.html) for how to add/change/remove these.
* Refer to [elasticity](../elasticity.html)
  for how to add/remove capacity from a Vespa cluster, procedure below.
* See [chained components](../components/chained-components.html)
  for how to add or remove searchers and document processors.
* Refer to the [sizing examples](../performance/sizing-examples.html)
  for changing from a *flat* to *grouped* content cluster.

## Add or remove a content node

1. **Node setup:**
   Prepare the node by installing software, set up the file systems/directories
   and set [VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables).
   [Start](#vespa-start-stop-restart) the node.
2. **Modify configuration:**
   Add/remove a [node](../reference/services-content.html#node)-element in *services.xml*
   and [hosts.xml](../reference/hosts.html).
   Refer to [multinode install](multinode-systems.html).
   Make sure the *distribution-key* is unique.
3. **Deploy**: [Observe metrics](#monitor-distance-to-ideal-state) to track progress as the cluster redistributes documents.
   Use the [cluster controller](../content/content-nodes.html#cluster-controller)
   to monitor the state of the cluster.
4. **Tune performance (optional):**
   Use [maxpendingidealstateoperations](https://github.com/vespa-engine/vespa/blob/master/storage/src/vespa/storage/config/stor-distributormanager.def) to tune concurrency of bucket merge operations from distributor nodes.
   Likewise, tune [merges](../reference/services-content.html#merges) -
   concurrent merge operations per content node. The tradeoff is speed of bucket replication vs
   use of resources, which impacts the applications' regular load.
5. **Finish:**
   The cluster is done redistributing when `idealstate.merge_bucket.pending`
   is zero on all distributors.

Do not remove more than *redundancy*-1 nodes at a time, to avoid data loss.
Observe `idealstate.merge_bucket.pending` to know bucket replica status,
when zero on all distributor nodes, it is safe to remove more nodes.
If [grouped distribution](../elasticity.html#grouped-distribution)
is used to control bucket replicas, remove all nodes in a group
if the redundancy settings ensure replicas in each group.

To increase bucket redundancy level before taking nodes out,
[retire](../content/content-nodes.html) nodes.
Again, track `idealstate.merge_bucket.pending` to know when done.
Use the [/cluster/v2 API](../reference/cluster-v2.html) or
[vespa-set-node-state](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-set-node-state)
to set a node to the *retired* state.
The [cluster controller's](../content/content-nodes.html#cluster-controller)
status page lists node states.

An alternative to increasing cluster size is building a new cluster, then migrate documents to it.
This is supported using [visiting](../visiting.html).

To *merge* two content clusters, add nodes to the cluster like above, considering:
* [distribution-keys](../reference/services-content.html#node) must be unique.
  Modify paths like *$VESPA_HOME/var/db/vespa/search/mycluster/n3* before adding the node.
* Set [VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables), then start the node.

## Topology change

Read [changing topology first](/en/elasticity.html#changing-topology),
and plan the sequence of steps.

Make sure to not change the `distribution-key`
for nodes in *services.xml*.

It is not required to restart nodes as part of this process

## Add or remove services on a node

It is possible to run multiple Vespa services on the same host.
If changing the services on a given host,
stop Vespa on the given host before running `vespa activate`.
This is because the services are dynamically allocated port numbers,
depending on what is running on the host.
Consider if some of the services changed are used by services on other hosts.
In that case, restart services on those hosts too. Procedure:

1. Edit *services.xml* and *hosts.xml*
2. Stop Vespa on the nodes that have changes
3. Run `vespa prepare` and `vespa activate`
4. Start Vespa on the nodes that have changes

## Troubleshooting

Also see the [FAQ](../faq.html).

|  |  |
| --- | --- |
| No endpoint | Most problems with the quick start guides are due to Docker out of memory. Make sure at least 6G memory is allocated to Docker:   ``` $ docker info | grep "Total Memory" or $ podman info | grep "memTotal" ```  OOM symptoms include  ``` INFO: Problem with Handshake localhost:8080 ssl=false: localhost:8080 failed to respond ```  The container is named *vespa* in the guides, for a shell do:  ``` $ docker exec -it vespa bash ``` |
| Log viewing | Use [vespa-logfmt](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-logfmt) to view the vespa log - example:   ``` $ /opt/vespa/bin/vespa-logfmt -l warning,error ``` |
| Json | For json pretty-print, append   ``` | python -m json.tool ```  to commands that output json - or use [jq](https://stedolan.github.io/jq/). |
| Routing | Vespa lets application set up custom document processing / indexing, with different feed endpoints. Refer to [indexing](../indexing.html) for how to configure this in *services.xml*.  [#13193](https://github.com/vespa-engine/vespa/issues/13193) has a summary of problems and solutions. |
| Tracing | Use [tracelevel](../reference/document-v1-api-reference.html#request-parameters) to dump the routes and hops for a write operation - example:   ``` $ curl -H Content-Type:application/json --data-binary @docs.json \   $ENDPOINT/document/v1/mynamespace/doc/docid/1?tracelevel=4 | jq .  {     "pathId": "/document/v1/mynamespace/doc/docid/1",     "id": "id:mynamespace:doc::1",     "trace": [         { "message": "[1623413878.905] Sending message (version 7.418.23) from client to ..." },         { "message": "[1623413878.906] Message (type 100004) received at 'default/container.0' ..." },         { "message": "[1623413878.907] Sending message (version 7.418.23) from 'default/container.0' ..." },         { "message": "[1623413878.907] Message (type 100004) received at 'default/container.0' ..." },         { "message": "[1623413878.909] Selecting route" },         { "message": "[1623413878.909] No cluster state cached. Sending to random distributor." } ``` |

## Clean start mode

There has been rare occasions were Vespa stored data that was internally inconsistent.
For those circumstances it is possible to start the node in a
[validate_and_sanitize_docstore](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/proton.def) mode.
This will do its best to clean up inconsistent data.
However, detecting that this is required is not easy, consult the Vespa Team first.
In order for this approach to work, all nodes must be stopped before enabling this feature -
this to make sure the data is not redistributed.

## Content cluster configuration

| Availability vs resources | Keeping index structures costs resources. Not all replicas of buckets are necessarily searchable, unless configured using [searchable-copies](../reference/services-content.html#searchable-copies). As Vespa indexes buckets on-demand, the most cost-efficient setting is 1, if one can tolerate temporary coverage loss during node failures. |
| Data retention vs size | When a document is removed, the document data is not immediately purged. Instead, *remove-entries* (tombstones of removed documents) are kept for a configurable amount of time. The default is two weeks, refer to [removed-db prune age](../reference/services-content.html#removed-db-prune-age). This ensures that removed documents stay removed in a distributed system where nodes change state. Entries are removed periodically after expiry. Hence, if a node comes back up after being down for more than two weeks, removed documents are available again, unless the data on the node is wiped first. A larger *prune age* will grow the storage size as this keeps document and tombstones longer.  **Note:** The backend does not store remove-entries for nonexistent documents. This to prevent clients sending wrong document identifiers from filling a cluster with invalid remove-entries. A side effect is that if a problem has caused all replicas of a bucket to be unavailable, documents in this bucket cannot be marked removed until at least one replica is available again. Documents are written in new bucket replicas while the others are down - if these are removed, then older versions of these will not re-emerge, as the most recent change wins. |
| Transition time | See [transition-time](../reference/services-content.html#transition-time) for tradeoffs for how quickly nodes are set down vs. system stability. |
| Removing unstable nodes | One can configure how many times a node is allowed to crash before it will automatically be removed. The crash count is reset if the node has been up or down continuously for more than the [stable state period](../reference/services-content.html#stable-state-period). If the crash count exceeds [max premature crashes](../reference/services-content.html#max-premature-crashes), the node will be disabled. Refer to [troubleshooting](#troubleshooting). |
| Minimal amount of nodes required to be available | A cluster is typically sized to handle a given load. A given percentage of the cluster resources are required for normal operations, and the remainder is the available resources that can be used if some of the nodes are no longer usable. If the cluster loses enough nodes, it will be overloaded:   * Remaining nodes may create disk full situation.   This will likely fail a lot of write operations, and if disk is shared with OS,   it may also stop the node from functioning. * Partition queues will grow to maximum size.   As queues are processed in FIFO order, operations are likely to get long latencies. * Many operations may time out while being processed,   causing the operation to be resent, adding more load to the cluster. * When new nodes are added, they cannot serve requests   before data is moved to the new nodes from the already overloaded nodes.   Moving data puts even more load on the existing nodes,   and as moving data is typically not high priority this may never actually happen.  To configure what the minimal cluster size is, use [min-distributor-up-ratio](../reference/services-content.html#min-distributor-up-ratio) and [min-storage-up-ratio](../reference/services-content.html#min-storage-up-ratio). |
