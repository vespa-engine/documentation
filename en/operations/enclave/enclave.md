---
# Copyright Vespa.ai. All rights reserved.
title: Vespa Cloud Enclave
applies_to: cloud
redirect_from:
- /en/cloud/enclave/enclave
---

![enclave architecture](/assets/img/enclave-architecture.png)

Vespa Cloud Enclave allows Vespa Cloud applications to run inside the tenant's
own cloud accounts while everything is still fully managed by Vespa Cloud's
automation, giving the tenant full access to Vespa Cloud features inside their
own cloud account. This allows tenant data to always remain within the bounds of
services controlled by the tenant, and also to build closer integrations with
Vespa applications inside the cloud services.

Vespa Cloud Enclave is available in AWS, Azure, and GCP.

**Note:** As the Vespa Cloud Enclave resources run in _your_ account, this incurs
resource costs from your cloud provider in _addition_ to the Vespa Cloud costs.

## AWS

* [Getting started](aws-getting-started.html)
* [Architecture and security](aws-architecture)

## Azure

* [Getting started](azure-getting-started.html)
* [Architecture and security](azure-architecture)

## GCP

* [Getting started](gcp-getting-started.html)
* [Architecture and security](gcp-architecture)

## Guides

* [Log archive](archive)
* [Operations and Support](operations)

## FAQ

**Which kind of permission is needed for the Vespa control plane to access my AWS accounts / Azure subscriptions / GCP projects?**
The permissions required are coded into the Terraform modules found at:

* [terraform-aws](https://github.com/vespa-cloud/terraform-aws-enclave/tree/main)
* [terraform-azure](https://github.com/vespa-cloud/terraform-azure-enclave/tree/main)
* [terraform-google](https://github.com/vespa-cloud/terraform-google-enclave/tree/main)

Navigate to the _modules_ directory for details.

**How can I configure agents/daemons on Vespa hosts securely?**
Use terraform to grant Vespa hosts access to necessary secrets, and create an RPM
that retrieves them and configures your application. See [enclave-examples](https://github.com/vespa-cloud/enclave-examples/tree/main/systemd-secrets)
for a complete example.

**Deployment failure: Could not provision ...**
This happens if you deploy to new zones _before_ running the Terraform/CloudFormation templates:

```
Deployment failed: Invalid application: In container cluster 'mycluster': Could not provision load balancer mytenant:myapp:myinstance:mycluster: Expected to find exactly 1 resource, but got 0 for subnet with service 'tenantelb'
```

**Do we  need to take any actions when AWS sends us Amazon EC2 Instance Retirement, Amazon EC2 Instance Availability Issue, or Amazon EC2 Maintenance notifications,?**

Vespa Cloud will take proactive actions on maintenance operations and replace instances that are scheduled for maintenance tasks ahead of time to reduce any impact the maintenance may incur.

All EC2 instance failures are detected by our control plane, and the problematic instances are automatically replaced. The system will, as part of the replacement process, also ensure that the document distribution is kept in line with your application configuration.
