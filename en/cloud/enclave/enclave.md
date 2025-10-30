---
# Copyright Vespa.ai. All rights reserved.
title: Vespa Cloud Enclave
category: cloud
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
* [Getting started](/en/cloud/enclave/aws-deploy-an-application.html)
* [Architecture and security](/en/cloud/enclave/aws-architecture)

## GCP
* [Getting started](/en/cloud/enclave/gcp-deploy-an-application.html)
* [Architecture and security](/en/cloud/enclave/gcp-architecture)

## Guides
* [Log archive](/en/cloud/enclave/archive)
* [Operations and Support](/en/cloud/enclave/operations)

## FAQ
**Which kind of permission is needed for the Vespa control plane to access my AWS accounts / GCP projects?**
The permissions required are coded into the Terraform modules found at:
* [terraform-aws](https://github.com/vespa-cloud/terraform-aws-enclave/tree/main)
* [terraform-google](https://github.com/vespa-cloud/terraform-google-enclave/tree/main)

Navigate to the _modules_ directory for details.

**How can I configure agents/daemons on Vespa hosts securely?**
Use terraform to grant Vespa hosts access to necessary secrets, and create an RPM
that retrieves it and configures your application. See [enclave-examples](https://github.com/vespa-cloud/enclave-examples/tree/main/systemd-secrets)
for a complete example.
