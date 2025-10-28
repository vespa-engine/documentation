---
# Copyright Vespa.ai. All rights reserved.
title: "services.xml"
category: oss,cloud
---

*services.xml* is the primary configuration file in an
[application package](../application-packages.html). Elements:

```
services [version]
  container [version]
  content   [version]
  admin     [version]
  routing   [version]
```

## services

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| version | required | number |  | 1.0 in this version of Vespa |

Optional subelements (one or more of *container*, *content*
or *service* is required):
* [admin](services-admin.html)
* [content](services-content.html)
* [container](services-container.html)
* [routing](/en/operations-selfhosted/routing.html#routing-services)

Example Vespa Cloud:

```
{% highlight xml %}









        2








{% endhighlight %}
```

Example Self-managed:

```
{% highlight xml %}









        2









{% endhighlight %}
```

## nodes

The *nodes* element and its attributes/content/children configures the number of nodes used in a cluster.
*nodes* is a child element of [container](/en/reference/services-container.html) and
[content](/en/reference/services-content.html).
It is different in Vespa Cloud and self-managed:
* Vespa Cloud: *nodes* are specified by the *count* attribute
  and a [resource](#resources) child element.
  *count* is an integer or range (see below), and is the number of nodes of the cluster.
* Self-managed: *nodes* have *node* child elements,
  see [content node](/en/reference/services-content.html#node) and
  [container node](/en/reference/services-container.html#node).
  A node referred to in *services.xml* must be defined in
  [hosts.xml](hosts.html) using *hostalias*.

| Attribute | type | Default | Description |
| --- | --- | --- | --- |
| **count** | integer or range |  | Vespa Cloud: The number of nodes of the cluster. |
| **exclusive** | boolean | false | Optional. Vespa Cloud: If true these nodes will never be placed on shared hosts even when this would otherwise be allowed (which is only for content nodes in some environments). When nodes are allocated exclusively, the resources must match the resources of the host exactly. |
| **groups** | integer or range |  | Vespa Cloud content nodes only, optional: Integer or range. Sets the number of groups into which content nodes should be divided. Each group will have an equal share of the nodes and redundancy copies of the corpus, and each query will be routed to just one group - see [grouped distribution](/en/elasticity.html#grouped-distribution). This allows [scaling](/en/performance/sizing-examples.html) to a higher query load than within a single group. |
| **group-size** | integer or range |  | Vespa Cloud content nodes only, optional: Integer or range where either value can be skipped (replaced by an empty string) to create a one-sided limit. If this is set, the group sizes used will always be within these limits (inclusive). |

If neither *groups* nor *group-size* is set, all nodes will always be placed in a single group.
Read more in [topology](/en/cloud/topology-and-resizing.html).

The attributes above specified as a range will be autoscaled by the system.
Ranges are expressed by the syntax `[lower-limit, upper-limit]`; Both limits are inclusive.

When a new cluster (or application) is deployed it will initially be configured with the minimal resources given by the ranges.
When autoscaling is turned on for an existing cluster (by configuring a range),
it will continue unchanged until autoscaling determines that a change is beneficial.
Examples:

```
{% highlight xml %}



{% endhighlight %}
```
```
{% highlight xml %}



{% endhighlight %}
```

Read the [autoscaling guide](/en/cloud/autoscaling.html) to learn more.

See [index bootstrap](/en/cloud/index-bootstrap.html) for how to set node count in a step-by-step procedure,
estimating settings by feeding smaller subsets at a time.
Note that autoscaling of content clusters involves data redistribution and normally does not speed up bootstrapping.

## resources

Contained in the [nodes](#nodes) element, specifies the resources available on each node.
This element is used in Vespa Cloud configuration only.
The resources must match a node flavor at
[AWS](https://cloud.vespa.ai/en/reference/aws-flavors.html),
[GCP](https://cloud.vespa.ai/en/reference/gcp-flavors.html), or both,
depending on which zones you are deploying to.
Exception: If you use remote disk, you can specify any number lower than the max size.

Any element not specified will be assigned a default value.
**Subelements:** [gpu](#gpu)

| Attribute | type | Default | Description |
| --- | --- | --- | --- |
| **vcpu** | float or range | 2 | CPU, virtual threads |
| **memory** | float or range, each followed by a byte unit, such as "Gb" | 16 - content nodes 8 - container nodes | Memory |
| **disk** | float or range, each followed by a byte unit, such as "Gb" | 300 - content nodes | Disk space. To fit core dumps/heap dumps, the disk space should be larger than 3 x memory size for content nodes, 2 x memory size for container nodes. |
| **storage-type** (optional) string (enum) | `any` | The type of storage to use. This is useful to specify local storage when network storage provides insufficient io operations or too noisy io performance:  * `local`: Node-local storage is required. * `remote`: Network storage must be used. * `any`: Both remote or local storage may be used. | |
| **disk-speed** (optional) string (enum) | `fast` | The required disk speed category:  * `fast`: SSD-like disk speed is required * `slow`: This is sized for spinning disk speed * `any`Performance does not depend on disk speed (often suitable for container clusters). | |
| **architecture** (optional) | string (enum) | `any` | Node CPU architecture:  * `x86_64` * `arm64` * `any`: Use any of the available architectures. |

A resource specified as a range will be autoscaled by the system.
Ranges are expressed by the syntax `[lower-limit, upper-limit]`; Both limits are inclusive.

When a new cluster (or application) is deployed it will initially be configured with the minimal resources given by the ranges.
When autoscaling is turned on for an existing cluster (by configuring a range),
it will continue unchanged until autoscaling determines that a change is beneficial.
Example:

```
{% highlight xml %}



{% endhighlight %}
```

See [index bootstrap](/en/cloud/index-bootstrap.html) for how to set resources in a step-by-step procedure,
estimating settings by feeding smaller subsets at a time.
Note that autoscaling of content clusters involves data redistribution and normally does not speed up bootstrapping.

You can use ranges on any combination of resource attributes -
read the [autoscaling guide](/en/cloud/autoscaling.html) to learn more.

## gpu

Declares GPU resources to provision. Limitations:
* Available in AWS zones only
* Valid for container clusters only
* Only one *resources* and *gpu* configuration is supported, see example below.
  The example configuration will provision a node with a NVIDIA T4 GPU.
**Subelements:** None

| Attribute | type | Description |
| --- | --- | --- |
| **count** | integer | Number of GPUs |
| **memory** | integer, followed by a byte unit, such as "Gb" | Amount of memory per GPU. Total amount of GPU memory available is this number multiplied by `count`. |

Example:

```
{% highlight xml %}





{% endhighlight %}
```

## Generic configuration using <config>

Most elements in *services.xml* accept a sub-element named *config*.
*config* elements can be included on different levels in the XML structure
and the lower-level ones will override values in the higher-level ones (example below).
The *config* element must include the attribute *name*,
which gives the full name of the configuration option in question, including the namespace.
The name can either refer to configuration definitions that are shipped with Vespa
or ones that are part of the [application package](config-files.html). For a
complete example on generic configuration see the
[application package](config-files.html#generic-configuration-in-services-xml) reference.

```
{% highlight xml %}



            configured string



{% endhighlight %}
```

## Modular Configuration

Some features are configurable using XML files in subdirectories of the application package.
This means that the configuration found in these XML files
will be used as if it was inlined in *services.xml*.
This is supported for [search chains](services-search.html#chain),
[docproc chains](services-docproc.html) and
[routing tables](/en/operations-selfhosted/routing.html#routing-services).
