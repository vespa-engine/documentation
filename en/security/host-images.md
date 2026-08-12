---
title: Vespa Cloud host images
applies_to: cloud
---

Vespa Cloud runs on compute instances, like EC2 in AWS.
The hosts are booted with an image, which is updated regularly.
The hosts run Vespa in an OCI container image - upgrading Vespa means restarting the container with a new image.
This article is about the image running on the hosts, and managing these.



## Host image automation
Vespa.ai releases new host images on a weekly basis - approximately:

* The image is normally released on Tuesdays.
* Use the _Enclave_ Console view to see the _Target_ image name, like _9.0.0.20260724_.
* In the same view, find the host list of your applications, and their update status:

![list of OS images](/assets/img/image-list.png)


### Notes

* New images are released by automation, and not at a fixed schedule.
  For example, high-priority images can be released at any time,
  and a weekly release can be stopped at any time in regression testing.
* The OS update process runs per availability zone (AZ) in a region, until 90% complete.
  This means, normally one AZ is done before moving to the next, but there is overlap.
  Your serving capacity is therefore potentially reduced in a region with concurrent updates across AZs.
  As a rule of thumb, capacity should be built for AZ fail-out plus one node down in remaining AZs.
  * The staggered rollout means that the _Target_ image can vary per AZ - this is visible in the view (above).
* To override the automation (e.g. to pause the update process), contact [Vespa Support](https://support.vespa.ai/),
  or modify block windows (below).
* Hosts converge on the latest image - the _Target_ OS version.
  Large applications might run on multiple images during the process.
* New hosts (replacements for failed hosts, or capacity increases) are always allocated using the _Target_ image.


## Updating host image 
The automated process of updating the image is:

1. Stop the Vespa container image (orchestrated).
2. Stop the host, and start it again with an updated image.
   When the host is stopped, a backup is made, too.

This means, one or more nodes are stopped, orchestrated for availability, and upgraded -
repeated for all hosts.
This takes minutes per host, depending on index sizes.



## Controlling the image updates
The orchestrated restarts cause lower serving capacity while running. 
Use the _maintenance_ attribute in  [block windows](../reference/applications/deployment.html#block-change)
to run the process at times that aligns with your operational processes, e.g. at low hours.

This example blocks maintenance during working hours,
while still allowing application deployments and platform upgrades at any time:

```xml
<block-change maintenance="true"
              revision="false"
              version="false"
              hours="8-15"
              time-zone="America/Los_Angeles"/>
```



## Deployment pipeline 
The OS upgrades are not integrated with the [deployment pipeline](../operations/automated-deployments.html).
However, as the node restarts are orchestrated, deployments can be slowed down due to this.
This because nodes are required to report the config generation for successful deployment -
and restarting a node slows this process down.



## How to run new target images in QA instances first
Application owners might want to deploy new target OS version in a QA instance before the production serving clusters. 
As this process is not pipelined (above), contact [Vespa Support](https://support.vespa.ai/) for options.
