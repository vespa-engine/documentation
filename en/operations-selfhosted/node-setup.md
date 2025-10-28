---
# Copyright Vespa.ai. All rights reserved.
title: "Node and network setup"
category: oss
redirect_from:
- /en/node-setup.html
- /en/operations/node-setup.html
---

Vespa is composed of services that communicate and interact with each other.
These services can be partitioned onto any amount of actual hardware for scaling,
or they can all coexist on a single environment for development.
To achieve this flexibility,
some requirements must be met for the environment where the services will run.

## Node

A *node* in this context is the environment where some Vespa services are running.
This can be an actual machine like a server in a datacenter,
or a laptop for development and testing of Vespa configuration.
It can also be a Virtual Machine or a Docker container,
so one can run multiple nodes on a single piece of hardware.

The different Vespa services that run on nodes will mostly communicate with each other via the network.
This means that all nodes must have an IP address and have network connectivity to all other nodes.
Both IPv4 and IPv6 protocols are supported.
Note that the same framework is used even when running the entire Vespa stack on a single node.

## Memory settings

In the [getting started guides](/en/getting-started.html)
and [sample applications](https://github.com/vespa-engine/sample-apps),
memory settings are always the minimum to run the guides.
This to make it easy to set up and explore Vespa features.
The [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA) application has examples for even tighter settings,
just to be able to test a larger application on a small host.

It is important to note that these are
not the recommended Vespa memory settings.
Finding the optimal node configuration is covered in the [performance guides](/en/performance/index.html).
There are many ways to configure, feed and use Vespa, it is not possible to have a general, recommended setting.

{% include important.html content='Vespa is a multiprocess application,
and can be configured to run multiple services per node - see [config sentinel](/en/operations-selfhosted/config-sentinel.html).
Out-of-memory can cause a range of problems hard to diagnose -
the Vespa team recommends testing with larger nodes in these cases.' %}

As a rule of thumb, start with an 8 GB node,
just to make sure the application is functionally correct - then optimize later.

Review system defaults.
A common issue is too low default for `vm.max_map_count`
which makes apps run into memory mapping assertions,
especially if the [paged](/en/attributes.html#paged-attributes) option
has been enabled for a lot of attribute fields -
symptoms of this can be like:

```
vespalib::alloc::MemoryAllocator::PtrAndSize vespalib::alloc::MmapFileAllocator::alloc(size_t) const: Assertion buf!=MAP_FAILED
```
```
'terminate called after throwing an instance of 'std::runtime_error' 'what(): mmap of file '/opt/vespa/var/db/vespa/search/cluster.abc/n12/documents/xyz/0.ready/index/index.fusion.43/field123/boolocc.bdat' with flags '1' failed with error: 'Cannot allocate memory'
```

## Hostname

When Vespa services are started on a node, the node must identify
itself to the configuration system to get configuration (including which services to run).
This requires a unique identifier for the node in the config server.
Since it is already a requirement that the node has a *hostname* that the config server knows,
Vespa uses the same *hostname* when a node identifies itself to get its configuration.
See [config sentinel](/en/operations-selfhosted/config-sentinel.html) for details.

In order to find the IP address of a node and connect to it,
the node must have a *hostname* that identifies it and which maps to its IP address.
Actual machines on a network will usually have a *Fully Qualified Domain Name* (FQDN) in DNS,
which should be used as the host name for this purpose.

Note that it is a *requirement* that the host name,
configured in [hosts.xml](/en/reference/hosts.html),
can be used to look up the IP address of the node (see workaround using `VESPA_HOSTNAME` below).
The configuration server use this host name to create URLs
to be used to open network connections to Vespa services running on that node.
If the nodes use IP addresses which don't have DNS names, one *must* have *all*
those IP addresses with corresponding host names in
`/etc/hosts` on *all* nodes in the Vespa installation.
We recommend using names that can be used as FQDNs also in this case,
in case of moving to using a DNS server instead of publishing `/etc/hosts`.

This means that the node *must* know its own hostname (FQDN),
and be in agreement with the config server about what exactly the host name is.
Usually this is achieved by just running the `hostname` command.
If `hostname` is set to the FQDN of the node, then everything should Just Work.

As an alternative to modifying `/etc/hosts`,
set [VESPA_HOSTNAME](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
on the hosts.
[vespa-ip-vs-hostname](https://www.jocas.lt/journal/articles/vespa-ip-vs-hostname/)
is a great post on how to do this.

## Simple single-node development environment

When testing a Vespa configuration on a single-node setup,
one can usually avoid the setup hassle by overriding the hostname with the value "localhost".
Try this command for that purpose:

```
$ echo "override VESPA_HOSTNAME localhost" >> $VESPA_HOME/conf/vespa/default-env.txt
```

Running Java unit tests won't pick up settings in `default-env.txt`
and will default to "localhost" if `VESPA_HOSTNAME` isn't set in the environment.
