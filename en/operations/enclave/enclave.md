---
# Copyright Vespa.ai. All rights reserved.
title: Vespa Cloud Enclave
category: cloud
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

Vespa Cloud Enclave is available in AWS and GCP. Azure is on the roadmap.

**Note:** As the Vespa Cloud Enclave resources run in _your_ account, this incurs
resource costs from your cloud provider in _addition_ to the Vespa Cloud costs.

## AWS
* [Getting started](aws-getting-started.html)
* [Architecture and security](aws-architecture)

## GCP
* [Getting started](gcp-getting-started.html)
* [Architecture and security](gcp-architecture)

## Guides
* [Log archive](archive)
* [Operations and Support](operations)

## FAQ
**Which kind of permission is needed for the Vespa control plane to access my AWS accounts / GCP projects?**
The permissions required are coded into the Terraform modules found at:
* [terraform-aws](https://github.com/vespa-cloud/terraform-aws-enclave/tree/main)
* [terraform-google](https://github.com/vespa-cloud/terraform-google-enclave/tree/main)

Navigate to the _modules_ directory for details.

**How can I configure agents/daemons on Vespa hosts securely?**
Use terraform to grant Vespa hosts access to necessary secrets, and create an RPM
that retrieves them and configures your application. See [enclave-examples](https://github.com/vespa-cloud/enclave-examples/tree/main/systemd-secrets)
for a complete example.

**Deployment failure: Cloud not provision ...**
This happens if you deploy to new zones _before_ running the Terraform/CloudFormation templates in [step 3](aws-getting-started#3-configure-aws-account):
```
Deployment failed: Invalid application: In container cluster 'mycluster': Could not provision load balancer mytenant:myapp:myinstance:mycluster: Expected to find exactly 1 resource, but got 0 for subnet with service 'tenantelb'
```
