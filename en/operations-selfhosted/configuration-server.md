---
# Copyright Vespa.ai. All rights reserved.
title: "Configuration Servers"
category: oss
redirect_from:
- /en/cloudconfig/configuration-server.html
- /en/operations/configuration-server.html
---

Vespa Configuration Servers host the endpoint where application packages are deployed -
and serves generated configuration to all services -
see the [overview](/en/overview.html)
and [application packages](/en/application-packages.html) for details.
I.e. one cannot configure Vespa without config servers, and services cannot run without it.

It is useful to understand the [Vespa start sequence](/en/operations-selfhosted/config-sentinel.html).
Refer to the sample applications
[multinode](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode) and
[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
for practical examples of multi-configserver configuration.

Vespa configuration is set up using one or more configuration servers (config servers).
A config server uses [Apache ZooKeeper](https://zookeeper.apache.org/)
as a distributed data storage for the configuration system.
In addition, each node runs a config proxy to cache configuration data -
find an overview at [services start](/en/operations-selfhosted/config-sentinel.html).

## Status and config generation

Check the health of a running config server using (replace localhost with hostname):

```
$ curl http://localhost:19071/state/v1/health
```

Note that the config server is a service is itself, and runs with file-based configuration.
The application packages deployed will not change the config server -
the config server serves this configuration to all other Vespa nodes.
This will hence always be config generation 0:

```
$ curl http://localhost:19071/state/v1/config
```

Details in [start-configserver](https://github.com/vespa-engine/vespa/blob/master/configserver/src/main/sh/start-configserver).

## Redundancy

The config servers are defined in
[VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables),
[services.xml](/en/reference/services.html) and [hosts.xml](/en/reference/hosts.html):

```
$ VESPA_CONFIGSERVERS=myserver0.mydomain.com,myserver1.mydomain.com,myserver2.mydomain.com
```
```
{% highlight xml %}









{% endhighlight %}
```
```
{% highlight xml %}


        admin0


        admin1


        admin2


{% endhighlight %}
```

[VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
must be set on all nodes.
This is a comma- or whitespace-separated list with the hostname of all config servers,
like *myhost1.mydomain.com,myhost2.mydomain.com,myhost3.mydomain.com*.

When there are multiple config servers, the [config proxy](/en/operations-selfhosted/config-proxy.html)
will pick a config server randomly (to achieve load balancing between config servers).
The config proxy is fault-tolerant and will switch to another config server (if there is more than one)
if the one it is using becomes unavailable or there is an error in the configuration it receives.

For the system to tolerate *n* failures,
[ZooKeeper](#zookeeper) by design requires using *(2*n)+1* nodes.
Consequently, only an odd numbers of nodes is useful,
so you need minimum 3 nodes to have a fault-tolerant config system.

Even when using just one config server, the application will work if the server goes down
(but deploying application changes will not work).
Since the *config proxy* runs on every node and caches configs,
it will continue to serve config to the services on that node.
However, restarting a node when config servers are unavailable
means that services on the node will be unable to start since the cache will be destroyed when restarting the config proxy.

Refer to the [admin model reference](/en/reference/services-admin.html#configservers)
for more details on *services.xml*.

## Start sequence

To bootstrap a Vespa application instance, the high-level steps are:
* Start config servers
* Deploy config
* Start Vespa nodes

[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
is a great guide on how to start a multinode Vespa application instance - try this first.
Detailed steps for config server startup:

1. Set [VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
   on all nodes, using fully qualified hostnames and the same value on all nodes, including the config servers.
2. Start the config server on the nodes configured in *services/hosts.xml*.
   Make sure the startup is successful by inspecting
   [/state/v1/health](/en/reference/state-v1.html#state-v1-health), default on port 19071:

   ```
   $ curl http://localhost:19071/state/v1/health
   ```
```
   {% highlight json %}
   {
       "time" : 1651147368066,
       "status" : {
           "code" : "up"
       },
       "metrics" : {
           "snapshot" : {
               "from" : 1.651147308063E9,
               "to" : 1.651147367996E9
           }
       }
   }
   {% endhighlight %}
   ```

   If there is no response on the health API, two things can have happened:
   * The config server process did not start - inspect logs using `vespa-logfmt`,
     or check *$VESPA_HOME/logs/vespa/vespa.log*, normally */opt/vespa/logs/vespa/vespa.log*.
   * The config server process started, and is waiting for [Zookeeper quorum](#zookeeper):

   ```
   $ vespa-logfmt -S configserver
   ```
```
   configserver     Container.com.yahoo.vespa.zookeeper.ZooKeeperRunner	Starting ZooKeeper server with /opt/vespa/var/zookeeper/conf/zookeeper.cfg. Trying to establish ZooKeeper quorum (members: [node0.vespanet, node1.vespanet, node2.vespanet], attempt 1)
   configserver     Container.com.yahoo.container.handler.threadpool.ContainerThreadpoolImpl	Threadpool 'default-pool': min=12, max=600, queue=0
   configserver     Container.com.yahoo.vespa.config.server.tenant.TenantRepository	Adding tenant 'default', created 2022-04-28T13:02:24.182Z. Bootstrapping in PT0.175576S
   configserver     Container.com.yahoo.vespa.config.server.rpc.RpcServer	Rpc server will listen on port 19070
   configserver     Container.com.yahoo.container.jdisc.state.StateMonitor	Changing health status code from 'initializing' to 'up'
   configserver     Container.com.yahoo.jdisc.http.server.jetty.Janitor	Creating janitor executor with 2 threads
   configserver     Container.com.yahoo.jdisc.http.server.jetty.JettyHttpServer	Threadpool size: min=22, max=22
   configserver     Container.org.eclipse.jetty.server.Server	jetty-9.4.46.v20220331; built: 2022-03-31T16:38:08.030Z; git: bc17a0369a11ecf40bb92c839b9ef0a8ac50ea18; jvm 11.0.14.1+1-
   configserver     Container.org.eclipse.jetty.server.handler.ContextHandler	Started o.e.j.s.ServletContextHandler@341c0dfc{19071,/,null,AVAILABLE}
   configserver     Container.org.eclipse.jetty.server.AbstractConnector	Started configserver@3cd6d147{HTTP/1.1, (http/1.1, h2c)}{0.0.0.0:19071}
   configserver     Container.org.eclipse.jetty.server.Server	Started @21955ms
   configserver     Container.com.yahoo.container.jdisc.ConfiguredApplication	Switching to the latest deployed set of configurations and components. Application config generation: 0
   ```

   It will hang until quorum is reached, and the second highlighted log line is emitted.
   Root causes for missing quorum can be:
   * No connectivity between the config servers.
     Zookeeper logs the members like `(members: [node0.vespanet, node1.vespanet, node2.vespanet], attempt 1)`.
     Verify that the nodes running config server can reach each other on port 2181.
   * No connectivity can be wrong network config.
     [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
     uses a docker network, make sure there are no underscores in the hostnames.
3. Once all config servers return `up` on *state/v1/health*,
   an application package can be deployed.
   This means, if deploy fails, it is always a good idea to verify the config server health first -
   if config servers are up, and deploy fails, it is most likely an issue with the application package -
   if so, refer to [application packages](/en/application-packages.html).
4. A successful deployment logs the following, for the *prepare* and *activate* steps:

   ```
   Container.com.yahoo.vespa.config.server.ApplicationRepository	Session 2 prepared successfully.
   Container.com.yahoo.vespa.config.server.deploy.Deployment	Session 2 activated successfully using no host provisioner. Config generation 2. File references: [file '9cfc8dc57f415c72']
   Container.com.yahoo.vespa.config.server.session.SessionRepository	Session activated: 2
   ```
5. Start the Vespa nodes.
   Technically, they can be started at any time.
   When troubleshooting, it is easier to make sure the config servers are started successfully,
   and deployment was successful - before starting any other nodes.
   Refer to the [Vespa start sequence](/en/operations-selfhosted/config-sentinel.html)
   and [Vespa start / stop / restart](/en/operations-selfhosted/admin-procedures.html#vespa-start-stop-restart).

Make sure to look for logs on all config servers when debugging.

## Scaling up

Add a config server node for increased fault tolerance or when replacing a node.
Read up on [ZooKeeper configuration](#zookeeper-configuration) before continuing.
Although it is *possible* to add more than one config server at a time,
doing it one by one is recommended, to keep the ZooKeeper quorum intact.

Due to the ZooKeeper majority vote, use one or three config servers.

1. Install *vespa* on new config server node.
2. Append the config server node's hostname to VESPA_CONFIGSERVERS on all nodes, then (re)start
   all config servers in sequence to update the ZooKeeper config. By appending, the current
   config server nodes keep their current ZooKeeper index. Restart the existing config server(s)
   first. Config server will log which servers are configured when starting up to vespa log.
3. Update *services.xml* and *hosts.xml* with the new set of config servers,
   then *vespa prepare* and *vespa activate*.
4. Restart other nodes one by one to start using the new config servers.
   This will let the vespa nodes use the updated set of config servers.

The config servers will automatically redistribute the application data to new nodes.

## Scaling down

This is the inverse of scaling up, and the procedure is the same.
Remove config servers from the end of *VESPA_CONFIGSERVERS*,
and here one can remove two nodes in one go, if going from three to one.

## Replacing nodes
- Make sure to replace only one node at a time.
- If you have only one config server you need to first scale up with a new node, then scale down by removing the old node.
- If you have 3 or more you can replace one of the old nodes in VESPA_CONFIGSERVERS with the new one instead of adding one, otherwise same procedure as
  in [Scaling up](#scaling-up). Repeat for each node you want to replace.

## Tools

Tools to access config:
* [vespa-get-config](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-get-config)
* [vespa-configproxy-cmd](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-configproxy-cmd)
* [Config API](/en/reference/config-rest-api-v2.html)

## ZooKeeper

[ZooKeeper](https://zookeeper.apache.org/)
handles data consistency across multiple config servers.
The config server Java application runs a ZooKeeper server,
embedded with an RPC frontend that the other nodes use.
ZooKeeper stores data internally in *nodes* that can have *sub-nodes*,
similar to a file system.

At [vespa prepare](/en/application-packages.html#deploy), the application's files,
along with global configurations, are stored in ZooKeeper.
The application data is stored under */config/v2/tenants/default/sessions/[sessionid]/userapp*.
At [vespa activate](/en/application-packages.html#deploy),
the newest application is activated *live*
by writing the session id into */config/v2/tenants/default/applications/default:default:default*.
It is at that point the other nodes get configured.

Use *vespa-zkcli* to inspect state, replace with actual session id:

```
$ vespa-zkcli ls  /config/v2/tenants/default/sessions/sessionid/userapp
$ vespa-zkcli get /config/v2/tenants/default/sessions/sessionid/userapp/services.xml
```

The ZooKeeper server logs to *$VESPA_HOME/logs/vespa/zookeeper.configserver.0.log (files are rotated with sequence number)*

### ZooKeeper configuration

The members of the ZooKeeper cluster is generated based on the contents of
[VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables).
*$VESPA_HOME/var/zookeeper/conf/zookeeper.cfg* is written when (re)starting the config server.
Hence, config server(s) must all be restarted when `VESPA_CONFIGSERVERS` changes.

The order of the nodes is used to create indexes in *zookeeper.cfg*, do not change node order.

### ZooKeeper recovery

If the config server(s) should experience data corruption,
for instance a hardware failure, use the following recovery procedure.
One example of such a scenario is if *$VESPA_HOME/logs/vespa/zookeeper.configserver.0.log*
says *java.io.IOException: Negative seek offset at java.io.RandomAccessFile.seek(Native Method)*,
which indicates ZooKeeper has not been able to recover after a full disk.
There is no need to restart Vespa on other nodes during the procedure:

1. [vespa-stop-configserver](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-stop-configserver)
2. [vespa-configserver-remove-state](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-configserver-remove-state)
3. [vespa-start-configserver](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-start-configserver)
4. [vespa](/en/vespa-cli.html#deployment) prepare <application path>
5. [vespa](/en/vespa-cli.html#deployment) activate

This procedure completely cleans out ZooKeeper's internal data snapshots and deploys from scratch.

Note that by default the [cluster controller](../content/content-nodes.html#cluster-controller)
that maintains the state of the content cluster will use the shared same ZooKeeper instance,
so the content cluster state is also reset when removing state.
Manually set state will be lost (e.g. a node with user state *down*).
It is possible to run cluster-controllers in standalone zookeeper mode -
see  [standalone-zookeeper](/en/reference/services-admin.html#cluster-controllers).

### ZooKeeper barrier timeout

If the config servers are heavily loaded, or the applications being deployed are big,
the internals of the server may time out when synchronizing with the other servers during deploy.
To work around, increase the timeout by setting:
[VESPA_CONFIGSERVER_ZOOKEEPER_BARRIER_TIMEOUT](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
to 600 (seconds) or higher, and restart the config servers.

## Configuration

To access config from a node not running the config system
(e.g. doing feeding via the Document API),
use the environment variable
[VESPA_CONFIG_SOURCES](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables):

```
$ export VESPA_CONFIG_SOURCES="myadmin0.mydomain.com:19071,myadmin1.mydomain.com:19071"
```

Alternatively, for Java programs, use the system property *configsources*
and set it programmatically or on the command line with the *-D* option to Java.
The syntax for the value is the same as for *VESPA_CONFIG_SOURCES*.

### System requirements

The minimum heap size for the JVM it runs under is 128 Mb and max heap size is 2 GB
(which can be changed with a [setting](/en/performance/container-tuning.html#config-server-and-config-proxy)).
It writes a transaction log that is regularly purged of old items, so little disk space is required.
Note that running on a server that has a lot of disk I/O
will adversely affect performance and is not recommended.

### Ports

The config server RPC port can be changed by setting
[VESPA_CONFIGSERVER_RPC_PORT](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
on all nodes in the system.

Changing HTTP port requires changing the port in
*$VESPA_HOME/conf/configserver-app/services.xml*:

```
{% highlight xml %}



{% endhighlight %}
```

When deploying, use the *-p* option, if port is changed from the default.

## Troubleshooting

| Problem | Description |
| --- | --- |
| Health checks | Verify that a config server is up and running using [/state/v1/health](/en/reference/state-v1.html#state-v1-health), see [start sequence](#start-sequence). Status code is `up` if the server is up and has finished bootstrapping.  Alternatively, use <http://localhost:19071/status.html> which will return response code 200 if server is up and has finished bootstrapping.  Metrics are found at [/state/v1/metrics](/en/reference/state-v1.html#state-v1-metrics). Use [vespa-model-inspect](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect) to find host and port number, port is 19071 by default. || Consistency | When having more than one config server, consistency between the servers is crucial. <http://localhost:19071/status> can be used to check that settings for config servers are the same for all servers.  [vespa-config-status](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-config-status) can be used to check config on nodes.  <http://localhost:19071/application/v2/tenant/default/application/default> displays active config generation and should be the same on all servers, and the same as in response from running [vespa deploy](/en/vespa-cli.html#deployment) |
| Bad Node | If running with more than one config server and one of these goes down or has hardware failure, the cluster will still work and serve config as usual (clients will switch to use one of the good servers). It is not necessary to remove a bad server from the configuration.  Deploying applications will take longer, as [vespa deploy](/en/vespa-cli.html#deployment) will not be able to complete a deployment on all servers when one of them is down. If this is troublesome, lower the [barrier timeout](#zookeeper-barrier-timeout) - (default value is 120 seconds).  Note also that if you have not configured [cluster controllers](/en/reference/services-admin.html#cluster-controller) explicitly, these will run on the config server nodes and the operation of these might be affected. This is another reason for not trying to manually remove a bad node from the config server setup. |
| Stuck filedistribution | The config system distributes binary files (such as jar bundle files) using [file-distribution](/en/application-packages.html#file-distribution) - use [vespa-status-filedistribution](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-status-filedistribution) to see detailed status if it gets stuck. |
| Memory | Insufficient memory on the host / in the container running the config server will cause startup or deploy / configuration problems - see [Docker containers](/en/operations-selfhosted/docker-containers.html). |
| ZooKeeper | The following can be caused by a full disk on the config server, or clocks out of sync:   ``` at com.yahoo.vespa.zookeeper.ZooKeeperRunner.startServer(ZooKeeperRunner.java:92) Caused by: java.io.IOException: The accepted epoch, 10 is less than the current epoch, 48 ```   Users have reported that "Copying the currentEpoch to acceptedEpoch fixed the problem". |
