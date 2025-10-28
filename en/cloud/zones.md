---
# Copyright Vespa.ai. All rights reserved.
title: Zones
category: cloud
---

An application is deployed to a *zone*,
which is a combination of an [environment](/en/cloud/environments.html) and a *region*,
like `vespa deploy -z perf.aws-us-east-1c`.

If an application requires zone-specific configuration (e.g., different capacity requirements per zone),
use [environment and region variants](/en/reference/deployment-variants.html#services.xml-variants).
Also see [deployment.xml](/en/reference/deployment.html).

`dev` and `perf` zones for development and performance testing:

| Environment | Region |
| --- | --- |
| [dev](/en/cloud/environments.html#dev) aws-us-east-1c | |
| [dev](/en/cloud/environments.html#dev) aws-euw1-az1 | |
| [dev](/en/cloud/environments.html#dev) azure-eastus-az1 | |
| [dev](/en/cloud/environments.html#dev) gcp-us-central1-f | |
| [perf](/en/cloud/environments.html#perf) aws-us-east-1c | |

`prod` zones for production serving,
with a [CD pipeline](/en/cloud/automated-deployments.html):

| Environment | Region |
| --- | --- |
| [prod](/en/cloud/environments.html#prod) aws-us-east-1c | |
| [prod](/en/cloud/environments.html#prod) aws-use1-az4 | |
| [prod](/en/cloud/environments.html#prod) aws-use2-az1 | |
| [prod](/en/cloud/environments.html#prod) aws-use2-az3 | |
| [prod](/en/cloud/environments.html#prod) aws-us-west-2a | |
| [prod](/en/cloud/environments.html#prod) aws-eu-west-1a | |
| [prod](/en/cloud/environments.html#prod) aws-ap-northeast-1a | |
| [prod](/en/cloud/environments.html#prod) gcp-europe-west3-b | |
| [prod](/en/cloud/environments.html#prod) gcp-us-central1-a | |
| [prod](/en/cloud/environments.html#prod) gcp-us-central1-f | |

The `prod` zones use ephemeral instances for system tests and staging tests,
running in [test](/en/cloud/environments.html#test) and
[staging](/en/cloud/environments.html#staging) environments.
These are internal zones, and never directly deployed to, included here for reference:

| Environment | Region |
| --- | --- |
| [test](/en/cloud/environments.html#test) aws-us-east-1c | |
| [test](/en/cloud/environments.html#test) gcp-us-central1-f | |
| [staging](/en/cloud/environments.html#staging) aws-us-east-1c | |
| [staging](/en/cloud/environments.html#staging) gcp-us-central1-f | |

Contact [Support](https://vespa.ai/support/) to request more zones.
