---
# Copyright Vespa.ai. All rights reserved.
title: Operations and Support for Vespa Cloud Enclave
category: cloud
---

Vespa Cloud Enclave requires that resources provisioned within the VPC are wholly
managed by the Vespa Cloud orchestration services, and must not be manually
managed by tenant operations. Changing or removing the resources created by the
Configuration Servers will negatively impact your Vespa application and may
prevent Vespa Cloud from properly managing the applications as well as Vespa
engineers from support it.

The Terraform modules might see occasional backwards compatible updates. It is
recommended that the tenant applies updates to their system on a regular basis.
For more information, see the Terraform documentation on
[using Terraform in automation](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform).

The network access granted to Vespa Hosts must be in place for the Vespa
application to operate properly. If network access is restricted the Vespa
application might stop working.


## Quota
Make sure your organization's AWS or GCP quotas are set high enough to support common Vespa Cloud use cases.
A common use case is migrating to new instance types,
and this causes temporary doubled (or more) resource usage in the data migration transition period.
Other use cases with temporary increased resource usage are node replacements.

Best practise is to ensure the quota is 3x of current resource usage, to also cover for capacity expansion.

This is not to be confused with the [Vespa Cloud quota](https://cloud.vespa.ai/en/reference/quota).
