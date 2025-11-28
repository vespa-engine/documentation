---
# Copyright Vespa.ai. All rights reserved.
title: Deployment patterns 
category: cloud
redirect_from:
- /en/cloud/deployment-patterns
---

<style>
img {
  width: 50%;
}
</style>

Vespa Cloud's [automated deployments](automated-deployments.html)
lets you design CD pipelines for staged rollouts and multi-zone deployments.
This guide documents some of these patterns.



## Two regions, two AZs each, sequenced deployment
This is the simplest pattern, deploy to a set of zones/regions, in a sequence:

![Two regions, two AZs each, sequenced deployment](/assets/img/pipeline-1.png)
```xml
<deployment version="1.0">
    <prod>
        <region>aws-us-east-1c</region>
        <region>aws-use1-az4</region>
        <region>aws-use2-az1</region>
        <region>aws-use2-az3</region>
    </prod>
</deployment>
```



## Two regions, two AZs each, parallel deployment
Same as above, but deploying all zones in parallel:

![Two regions, two AZs each, parallel deployment](/assets/img/pipeline-2.png)
```xml
<deployment version="1.0">
    <prod>
        <parallel>
            <region>aws-us-east-1c</region>
            <region>aws-use1-az4</region>
            <region>aws-use2-az1</region>
            <region>aws-use2-az3</region>
        </parallel>
    </prod>
</deployment>
```



## Two regions, two AZs each, parallel deployment inside region
Deploy to the use1 region first, both AZs in parallel, then the use2 region, both AZs in parallel:

![Two regions, two AZs each, parallel deployment inside region](/assets/img/pipeline-3.png)
```xml
<deployment version="1.0">
    <prod>
        <parallel>
            <region>aws-us-east-1c</region>
            <region>aws-use1-az4</region>
        </parallel>
        <parallel>
            <region>aws-use2-az1</region>
            <region>aws-use2-az3</region>
        </parallel>
    </prod>
</deployment>
```


## Deploy to a test instance first
Deploy to a (downscaled) instance first, and add a delay before propagating to later instances and zones.

![With a canary instance](/assets/img/canary-instance-one-app.png)
```xml
<deployment version="1.0">
    <instance id="canary">
        <prod>
            <region>aws-use2-az1</region>
            <delay hours="1" />
        </prod>
    </instance>
    <instance id="prod">
        <prod>
            <region>aws-use2-az1</region>
        </prod>
    </instance>
</deployment>
```

### Deployment variants 
[Deployment variants](../reference/deployment-variants.html) are useful to set up a downscaled instance.
In [services.xml](../reference/services/services.html), override settings per instance:
```xml
<nodes deploy:instance="canary" count="2">
    <resources vcpu="4" memory="32Gb" disk="100Gb"/>
</nodes>
<nodes deploy:instance="prod" count="32">
    <resources vcpu="16" memory="128Gb" disk="1000Gb"/>
</nodes>
```



## Test and prod instances as separate applications
In the section before, we modeled the test and prod app as one pipeline.
This lets users halt the pipeline (using the delay) before prod propagation.

In some cases, this is better modeled as different applications:
* The CI pipeline is multistep, with approvals and use of different branches

The below uses different _applications_ to model the flow, these are completely separate application instances.
The application owner will model the flow in own tool, and orchestrate deployments to Vespa Cloud as fit:

![canary app](/assets/img/canaryapp.png)
![prod app](/assets/img/prodapp.png)

The important point is, these are two _separate_ deploy commands to Vespa Cloud:

```shell
$ vespa config set application kkraunetenant1.canaryapp
$ vespa prod deploy app
```
```xml
<deployment version="1.0">
    <instance id="canary">
        <prod>
            <region>aws-use2-az1</region>
        </prod>
    </instance>
</deployment>
```

```shell
$ vespa config set application kkraunetenant1.prodapp
$ vespa prod deploy app
```
```xml
<deployment version="1.0">
    <instance id="prod">
        <prod>
            <region>aws-use2-az1</region>
        </prod>
    </instance>
</deployment>
```



## services.xml structure
It is possible to split _services.xml_ to more file using includes:

```xml
<services version="1.0" xmlns:preprocess="properties"  xmlns:deploy="vespa">
    <preprocess:include file="container-cluster.xml" />
    <preprocess:include file="content-cluster.xml" />
</services>
```

Note: The include-feature can not be used in combination with [deployment variants](#deployment-variants). 



## Next reads
* [Environments](environments.html)
* [Zones](zones.html)
* [Routing](endpoint-routing.html)
