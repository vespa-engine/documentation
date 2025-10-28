---
# Copyright Vespa.ai. All rights reserved.
title: "Config sentinel"
category: oss
redirect_from:
- /en/config-sentinel.html
- /en/operations/config-sentinel.html
---

The config sentinel starts and stops services -
and restart failed services unless they are manually stopped.
All nodes in a Vespa system have at least these running processes:

| Process | Description |
| --- | --- |
| [config-proxy](/en/operations-selfhosted/config-proxy.html) | Proxies config requests between Vespa applications and the configserver node. All configuration is cached locally so that this node can maintain its current configuration, even if the configserver shuts down. |
| config-sentinel | Registers itself with the *config-proxy* and subscribes to and enforces node configuration, meaning the configuration of what services should be run locally, and with what parameters. |
| [vespa-logd](../reference/logs.html#logd) | Monitors *$VESPA_HOME/logs/vespa/vespa.log*, which is used by all other services, and relays everything to the [log-server](/en/reference/logs.html#log-server). |
| [metrics-proxy](/en/operations-selfhosted/monitoring.html#metrics-proxy) | Provides APIs for metrics access to all nodes and services. |

![Vespa node configuration, startup and logs](/assets/img/config-sentinel.svg)

Start sequence:

1. *config server(s)* are started and application config is deployed to them -
   see [config server operations](/en/operations-selfhosted/configuration-server.html).
2. *config-proxy* is started.
   The environment variables [VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
   and [VESPA_CONFIGSERVER_RPC_PORT](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
   are used to connect to the [config-server(s)](/en/operations-selfhosted/configuration-server.html).
   It will retry all config servers in case some are down.
3. *config-sentinel* is started,
   and subscribes to node configuration (i.e. a service list) from *config-proxy*
   using its hostname as the [config id](/en/contributing/configapi-dev.html#config-id).
   See [Node and network setup](/en/operations-selfhosted/node-setup.html) for
   details about how the hostname is detected and how to override it.
   The config for the config-sentinel (the service list)
   lists the processes to be started, along with the *config id* to assign to each,
   typically the logical name of that service instance.
4. *config-proxy* subscribes to node configuration from *config-server*,
   caches it, and returns the result to *config-sentinel*
5. *config-sentinel* starts the services given in the node configuration,
   with the config id as argument.
   See example output below, like *id="search/qrservers/qrserver.0"*.
   *logd* and *metrics-proxy* are always started, regardless of configuration.
   Each service:
   1. Subscribes to configuration from *config-proxy*.
   2. *config-proxy* subscribes to configuration from *config-server*,
      caches it and returns result to the service.
   3. The service runs according to its configuration,
      logging to *$VESPA_HOME/logs/vespa/vespa.log*.
      The processes instantiate internal components,
      each assigned the same or another config id, and instantiating further components.Also see [cluster startup](#cluster-startup) for a minimum nodes-up start setting.

When new config is deployed to *config-servers*
they propagate the changed configuration to nodes subscribing to it.
In turn, these nodes reconfigure themselves accordingly.

## User interface

The config sentinel runs an RPC service which can be used to list,
start and stop the services supposed to run on that node.
This can be useful for testing and debugging.
Use [vespa-sentinel-cmd](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-sentinel-cmd)
to trigger these actions.
Example output from `vespa-sentinel-cmd list`:

```
vespa-sentinel-cmd 'sentinel.ls' OK.
container state=RUNNING mode=AUTO pid=27993 exitstatus=0 id="default/container.0"
container-clustercontroller state=RUNNING mode=AUTO pid=27997 exitstatus=0 id="admin/cluster-controllers/0"
distributor state=RUNNING mode=AUTO pid=27996 exitstatus=0 id="search/distributor/0"
logd state=RUNNING mode=AUTO pid=5751 exitstatus=0 id="hosts/r6-3/logd"
logserver state=RUNNING mode=AUTO pid=27994 exitstatus=0 id="admin/logserver"
searchnode state=RUNNING mode=AUTO pid=27995 exitstatus=0 id="search/search/cluster.search/0"
slobrok state=RUNNING mode=AUTO pid=28000 exitstatus=0 id="admin/slobrok.0"
```

To learn more about the processes and services,
see [files and processes](/en/operations-selfhosted/files-processes-and-ports.html).
Use [vespa-model-inspect host *hostname*](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect) to list services running on a node.

## Cluster startup

The config sentinel will not start services on a node unless it has connectivity to a minimum of other nodes,
default 50%.
Find an example of this feature in the
[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA#start-the-admin-server) example application.
Example configuration:

```
{% highlight xml %}



            20
            1


{% endhighlight %}
```

Example: `minOkPercent 10` means that services will be started only if
more than or equal to 10% of nodes are up.
If there are 11 nodes in the application,
the first node started will not start its services -
when the second node is started, services will be started on both.

`maxBadCount` is for connectivity checks where the other node is up,
but we still do not have proper two-way connectivity.
Normally, one-way connectivity means network configuration is broken and needs looking into,
so this may be set low (1 or even 0 are the recommended values). If there are some
temporary problems (in the example below non-responding DNS which leads to various
issues at startup) the config sentinel will loop and retry, so the service startup will just
be slightly delayed.

Example log:

```
[2021-06-15 14:33:25] EVENT   : starting/1 name="sbin/vespa-config-sentinel -c hosts/le40808.ostk (pid 867)"
[2021-06-15 14:33:25] EVENT   : started/1 name="config-sentinel"
[2021-06-15 14:33:25] CONFIG  : Sentinel got 4 service elements [tenant(footest), application(bartest), instance(default)] for config generation 1001
[2021-06-15 14:33:25] CONFIG  : Booting sentinel 'hosts/le40808.ostk' with [stateserver port 19098] and [rpc port 19097]
[2021-06-15 14:33:25] CONFIG  : listening on port 19097
[2021-06-15 14:33:25] CONFIG  : Sentinel got model info [version 7.420.21] for 35 hosts [config generation 1001]
[2021-06-15 14:33:25] CONFIG  : connectivity.maxBadCount = 3
[2021-06-15 14:33:25] CONFIG  : connectivity.minOkPercent = 40
[2021-06-15 14:33:28] INFO    : Connectivity check details: 2086533.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le01287.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le23256.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le23267.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le23297.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le23312.ostk -> connect OK, but reverse check FAILED
[2021-06-15 14:33:28] INFO    : Connectivity check details: le23317.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le23319.ostk -> connect OK, but reverse check FAILED
[2021-06-15 14:33:28] INFO    : Connectivity check details: le30550.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le30553.ostk -> connect OK, but reverse check FAILED
[2021-06-15 14:33:28] INFO    : Connectivity check details: le30556.ostk -> unreachable from me, but up
[2021-06-15 14:33:28] INFO    : Connectivity check details: le30560.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le30567.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40387.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40389.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40808.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40817.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40833.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40834.ostk -> unreachable from me, but up
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40841.ostk -> connect OK, but reverse check FAILED
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40858.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40860.ostk -> unreachable from me, but up
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40863.ostk -> connect OK, but reverse check FAILED
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40873.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40892.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40900.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40905.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: le40914.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: sm02318.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: sm02324.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: sm02340.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: zt40672.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: zt40712.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: zt40728.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] INFO    : Connectivity check details: zt41329.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:28] WARNING : 8 of 35 nodes up but with network connectivity problems (max is 3)
[2021-06-15 14:33:28] WARNING : Bad network connectivity (try 1)
[2021-06-15 14:33:30] WARNING : slow resolve time: 'le30556.ostk' -> '1234:5678:90:123::abcd' (5.00528 s)
[2021-06-15 14:33:30] WARNING : slow resolve time: 'le40834.ostk' -> '1234:5678:90:456::efab' (5.00527 s)
[2021-06-15 14:33:30] WARNING : slow resolve time: 'le40860.ostk' -> '1234:5678:90:789::cdef' (5.00459 s)
[2021-06-15 14:33:31] INFO    : Connectivity check details: le23312.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:31] INFO    : Connectivity check details: le23319.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:31] INFO    : Connectivity check details: le30553.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:31] INFO    : Connectivity check details: le30556.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:31] INFO    : Connectivity check details: le40834.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:31] INFO    : Connectivity check details: le40841.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:31] INFO    : Connectivity check details: le40860.ostk -> connect OK, but reverse check FAILED
[2021-06-15 14:33:31] INFO    : Connectivity check details: le40863.ostk -> OK: both ways connectivity verified
[2021-06-15 14:33:31] INFO    : Enough connectivity checks OK, proceeding with service startup
[2021-06-15 14:33:31] EVENT   : starting/1 name="searchnode"
...
```
