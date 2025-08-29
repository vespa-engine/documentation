---
# Copyright Vespa.ai. All rights reserved.
title: Node Resources
category: cloud
---

This guide goes through the following aspects of node resource configuration:

1. Independent configuration of resource dimensions
2. Using automated resource suggestions
3. Deployment automation for rapid optimization cycles
4. Automated instance type migration for optimal performance over time


## Independent resource dimensions
In Vespa Cloud, a node's `resources` is configured like:

```xml
<nodes count="8">
    <resources vcpu="4" memory="16Gb" disk="300Gb"/>
</nodes>
```

With this, you specify the dimensions independently.
E.g., one can double the CPU, keeping all other dimensions constant.

This is important when tuning for the optimal price/performance point,
as the pieces of an application has different sweet spots.
For example, the product search cluster of an application can be more CPU bound than product recommendations;
the latter might need relatively more memory.

{% include note.html content='the above is a simplified example,
there are more resource dimensions like GPU use, or CPU architecture, available.' %}

Optimizing for cost/performance is therefore easy.
Simplified, applications can be CPU, disk, or memory bound.
A general rule of thumb is to be bound by the most expensive component, often CPU.
Refer to the node resource [reference](/en/reference/services.html#resources) for all dimensions.


## Resource suggestions
Applications change over time:

* Data size growth
* Query rate growth
* Write rate growth
* Schema changes, like new fields or binarized embeddings

Finding the optimal node configuration is an iterative process.
It is simplified by using the Resource Suggestions view in the Vespa Console:

![Resource Suggestions](/assets/img/resource-suggestions-1.png)

Vespa Cloud tracks usage over time and suggests node configuration
and [topology](/en/cloud/topology-and-resizing.html) changes based on last week's load.
In the example above, observe a suggestion that doubles the memory relative to CPU.

This simplifies _what_ to configure, and one can roll out isolated changes while
observing latency and other business metrics like relevance quality.  



## Automated resource configuration deployment
Resource configuration is part of the [application package](/en/application-packages.html).
To change a cluster's resources, deploy the new version of the application package to Vespa Cloud
and wait for the changes to apply:

1. Changes to stateless Vespa Container clusters are almost instant,
   dependent on the cloud provider's provisioning latency.
2. Changes to stateful Vespa Content clusters (where the document indices are stored) take more time,
   as data is redistributed for uniform load:
   1. Changing the node `count` will modify the existing cluster.
   2. Changing the `resources` configuration will set up a parallel cluster and migrate data to it.
      This is generally slower than changing the node count, as more data moves.  

{% include important.html content='Vespa Cloud is designed for online changes.
All of the above changes can be deployed to a running system, with zero to minimal disruption.
See [content cluster elasticity](/en/elasticity.html) for details.' %}

Making changes to the resource specifications is hence fully automated.
The quickest way to the sweet spot is to initially deploy with enough capacity
and do daily re-tuning to cut cost.

Vespa Cloud provides performance dashboards with the relevant metrics in this phase:

![performance dashboard](/assets/img/dashboard.png)

Eventually, the application has its optimal price/performance characteristics,
without lengthy benchmarking activities.


## Automated instance type migration
Resource configurations map to the cloud provider's real resources, like AWS EC2 compute instances.
The instance inventory develops over time, like:

* _r7g_4xlarge (Graviton3)_
* _r8g_4xlarge (Graviton4)_

Both have 16 vCPU and 128G RAM, but _r8g_4xlarge_ is of a newer generation,
and has presumably higher performance:
_"R8g instances deliver around 30% higher performance over R7g instances, ..."_

{% include important.html content='As the `resources` configuration is general and independent of instance types,
Vespa Cloud will automatically migrate load to more cost-effective compute instances over time.' %}

This means, Vespa Cloud applications will migrate to more recent instance types of the same configuration,
with **zero manual interventions**.
This keeps the total cost in check, and performance tracking advances in hardware.  



## Next reads
* [The practical search performance guide](/en/performance/practical-search-performance-guide.html)
* [Autoscaling](/en/cloud/autoscaling.html)

<!-- Read more in TBD blogpost -->
