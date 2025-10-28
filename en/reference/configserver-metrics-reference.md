---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "ConfigServer Metrics"
---

| Name | Unit | Description |
| --- | --- | --- |
| configserver.requests | request | Number of requests processed |
| configserver.failedRequests | request | Number of requests that failed |
| configserver.latency | millisecond | Time to complete requests |
| configserver.cacheConfigElems | item | Time to complete requests |
| configserver.cacheChecksumElems | item | Number of checksum elements in the cache |
| configserver.hosts | node | The number of nodes being served configuration from the config server cluster |
| configserver.tenants | instance | The number of tenants being served configuration from the config server cluster |
| configserver.applications | instance | The number of applications being served configuration from the config server cluster |
| configserver.delayedResponses | response | Number of delayed responses |
| configserver.sessionChangeErrors | session | Number of session change errors |
| configserver.unknownHostRequests | request | Config requests from unknown hosts |
| configserver.newSessions | session | New config sessions |
| configserver.preparedSessions | session | Prepared config sessions |
| configserver.activeSessions | session | Active config sessions |
| configserver.inactiveSessions | session | Inactive config sessions |
| configserver.addedSessions | session | Added config sessions |
| configserver.removedSessions | session | Removed config sessions |
| configserver.rpcServerWorkQueueSize | item | Number of elements in the RPC server work queue |
| maintenanceDeployment.transientFailure | operation | Number of maintenance deployments that failed with a transient failure |
| maintenanceDeployment.failure | operation | Number of maintenance deployments that failed with a permanent failure |
| maintenance.successFactorDeviation | fraction | Configserver: Maintenance Success Factor Deviation |
| maintenance.duration | millisecond | Configserver: Maintenance Duration |
| configserver.zkConnectionLost | connection | Number of ZooKeeper connections lost |
| configserver.zkReconnected | connection | Number of ZooKeeper reconnections |
| configserver.zkConnected | node | Number of ZooKeeper nodes connected |
| configserver.zkSuspended | node | Number of ZooKeeper nodes suspended |
| configserver.zkZNodes | node | Number of ZooKeeper nodes present |
| configserver.zkAvgLatency | millisecond | Average latency for ZooKeeper requests |
| configserver.zkMaxLatency | millisecond | Max latency for ZooKeeper requests |
| configserver.zkConnections | connection | Number of ZooKeeper connections |
| configserver.zkOutstandingRequests | request | Number of ZooKeeper requests in flight |
| orchestrator.lock.acquire-latency | second | Time to acquire zookeeper lock |
| orchestrator.lock.acquire-success | operation | Number of times zookeeper lock has been acquired successfully |
| orchestrator.lock.acquire-timedout | operation | Number of times zookeeper lock couldn't be acquired within timeout |
| orchestrator.lock.acquire | operation | Number of attempts to acquire zookeeper lock |
| orchestrator.lock.acquired | operation | Number of times zookeeper lock was acquired |
| orchestrator.lock.hold-latency | second | Time zookeeper lock was held before it was released |
| nodes.active | node | The number of active nodes in a cluster |
| nodes.nonActive | node | The number of non-active nodes in a cluster |
| nodes.nonActiveFraction | node | The fraction of non-active nodes vs total nodes in a cluster |
| nodes.exclusiveSwitchFraction | fraction | The fraction of nodes in a cluster on exclusive network switches |
| nodes.emptyExclusive | node | The number of exclusive hosts that do not have any nodes allocated to them |
| nodes.expired.deprovisioned | node | The number of deprovisioned nodes that have expired |
| nodes.expired.dirty | node | The number of dirty nodes that have expired |
| nodes.expired.inactive | node | The number of inactive nodes that have expired |
| nodes.expired.provisioned | node | The number of provisioned nodes that have expired |
| nodes.expired.reserved | node | The number of reserved nodes that have expired |
| cluster.cost | dollar_per_hour | The cost of the nodes allocated to a certain cluster, in $/hr |
| cluster.load.ideal.cpu | fraction | The ideal cpu load of a certain cluster |
| cluster.load.ideal.memory | fraction | The ideal memory load of a certain cluster |
| cluster.load.ideal.disk | fraction | The ideal disk load of a certain cluster |
| cluster.load.peak.cpu | fraction | The peak cpu load in the period considered of a certain cluster |
| cluster.load.peak.memory | fraction | The peak memory load in the period considered of a certain cluster |
| cluster.load.peak.disk | fraction | The peak disk load in the period considered of a certain cluster |
| zone.working | binary | The value 1 if zone is considered healthy, 0 if not. This is decided by considering the number of non-active nodes vs the number of active nodes in a zone |
| cache.nodeObject.hitRate | fraction | The fraction of cache hits vs cache lookups for the node object cache |
| cache.nodeObject.evictionCount | item | The number of cache elements evicted from the node object cache |
| cache.nodeObject.size | item | The number of cache elements in the node object cache |
| cache.curator.hitRate | fraction | The fraction of cache hits vs cache lookups for the curator cache |
| cache.curator.evictionCount | item | The number of cache elements evicted from the curator cache |
| cache.curator.size | item | The number of cache elements in the curator cache |
| wantedRestartGeneration | generation | Wanted restart generation for tenant node |
| currentRestartGeneration | generation | Current restart generation for tenant node |
| wantToRestart | binary | One if node wants to restart, zero if not |
| wantedRebootGeneration | generation | Wanted reboot generation for tenant node |
| currentRebootGeneration | generation | Current reboot generation for tenant node |
| wantToReboot | binary | One if node wants to reboot, zero if not |
| retired | binary | One if node is retired, zero if not |
| wantedVespaVersion | version | Wanted vespa version for the node, in the form MINOR.PATCH. Major version is not included here |
| currentVespaVersion | version | Current vespa version for the node, in the form MINOR.PATCH. Major version is not included here |
| wantToChangeVespaVersion | binary | One if node want to change Vespa version, zero if not |
| hasWireguardKey | binary | One if node has a WireGuard key, zero if not |
| wantToRetire | binary | One if node wants to retire, zero if not |
| wantToDeprovision | binary | One if node wants to be deprovisioned, zero if not |
| failReport | binary | One if there is a fail report for the node, zero if not |
| suspended | binary | One if the node is suspended, zero if not |
| suspendedSeconds | second | The number of seconds the node has been suspended |
| activeSeconds | second | The number of seconds the node has been active |
| numberOfServicesUp | instance | The number of services confirmed to be running on a node |
| numberOfServicesNotChecked | instance | The number of services supposed to run on a node, that has not checked |
| numberOfServicesDown | instance | The number of services confirmed to not be running on a node |
| someServicesDown | binary | One if one or more services has been confirmed to not run on a node, zero if not |
| numberOfServicesUnknown | instance | The number of services the config server does not know is running on a node |
| nodeFailerBadNode | binary | One if the node is failed due to being bad, zero if not |
| downInNodeRepo | binary | One if the node is registered as being down in the node repository, zero if not |
| numberOfServices | instance | Number of services supposed to run on a node |
| lockAttempt.acquireMaxActiveLatency | second | Maximum duration for keeping a lock, ending during the metrics snapshot, or still being kept at the end or this snapshot period |
| lockAttempt.acquireHz | operation_per_second | Average number of locks acquired per second the snapshot period |
| lockAttempt.acquireLoad | operation | Average number of locks held concurrently during the snapshot period |
| lockAttempt.lockedLatency | second | Longest lock duration in the snapshot period |
| lockAttempt.lockedLoad | operation | Average number of locks held concurrently during the snapshot period |
| lockAttempt.acquireTimedOut | operation | Number of locking attempts that timed out during the snapshot period |
| lockAttempt.deadlock | operation | Number of lock grab deadlocks detected during the snapshot period |
| lockAttempt.errors | operation | Number of other lock related errors detected during the snapshot period |
| hostedVespa.docker.totalCapacityCpu | vcpu | Total number of VCPUs on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.docker.totalCapacityMem | gigabyte | Total amount of memory on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.docker.totalCapacityDisk | gigabyte | Total amount of disk space on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.docker.freeCapacityCpu | vcpu | Total number of free VCPUs on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.docker.freeCapacityMem | gigabyte | Total amount of free memory on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.docker.freeCapacityDisk | gigabyte | Total amount of free disk space on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.docker.allocatedCapacityCpu | vcpu | Total number of allocated VCPUs on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.docker.allocatedCapacityMem | gigabyte | Total amount of allocated memory on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.docker.allocatedCapacityDisk | gigabyte | Total amount of allocated disk space on tenant hosts managed by hosted Vespa in a zone |
| hostedVespa.pendingRedeployments | task | The number of hosted Vespa re-deployments pending |
| hostedVespa.docker.skew | fraction | A number in the range 0..1 indicating how well allocated resources are balanced with availability on hosts |
| hostedVespa.activeHosts | host | The number of managed hosts that are in state "active" |
| hostedVespa.breakfixedHosts | host | The number of managed hosts that are in state "breakfixed" |
| hostedVespa.deprovisionedHosts | host | The number of managed hosts that are in state "deprovisioned" |
| hostedVespa.dirtyHosts | host | The number of managed hosts that are in state "dirty" |
| hostedVespa.failedHosts | host | The number of managed hosts that are in state "failed" |
| hostedVespa.inactiveHosts | host | The number of managed hosts that are in state "inactive" |
| hostedVespa.parkedHosts | host | The number of managed hosts that are in state "parked" |
| hostedVespa.provisionedHosts | host | The number of managed hosts that are in state "provisioned" |
| hostedVespa.readyHosts | host | The number of managed hosts that are in state "ready" |
| hostedVespa.reservedHosts | host | The number of managed hosts that are in state "reserved" |
| hostedVespa.activeNodes | host | The number of managed nodes that are in state "active" |
| hostedVespa.breakfixedNodes | host | The number of managed nodes that are in state "breakfixed" |
| hostedVespa.deprovisionedNodes | host | The number of managed nodes that are in state "deprovisioned" |
| hostedVespa.dirtyNodes | host | The number of managed nodes that are in state "dirty" |
| hostedVespa.failedNodes | host | The number of managed nodes that are in state "failed" |
| hostedVespa.inactiveNodes | host | The number of managed nodes that are in state "inactive" |
| hostedVespa.parkedNodes | host | The number of managed nodes that are in state "parked" |
| hostedVespa.provisionedNodes | host | The number of managed nodes that are in state "provisioned" |
| hostedVespa.readyNodes | host | The number of managed nodes that are in state "ready" |
| hostedVespa.reservedNodes | host | The number of managed nodes that are in state "reserved" |
| overcommittedHosts | host | The number of hosts with over-committed resources |
| spareHostCapacity | host | The number of spare hosts |
| throttledHostFailures | host | Number of host failures stopped due to throttling |
| throttledNodeFailures | host | Number of node failures stopped due to throttling |
| nodeFailThrottling | binary | Metric indicating when node failure throttling is active. The value 1 means active, 0 means inactive |
| clusterAutoscaled | operation | Number of times a cluster has been rescaled by the autoscaler |
| clusterAutoscaleDuration | second | The currently predicted duration of a rescaling of this cluster |
| deployment.prepareMillis | millisecond | Duration of deployment preparations |
| deployment.activateMillis | millisecond | Duration of deployment activations |
| throttledHostProvisioning | binary | Value 1 if host provisioning is throttled, 0 if not |
