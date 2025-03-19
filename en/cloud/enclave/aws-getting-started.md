---
# Copyright Vespa.ai. All rights reserved.
title: Getting started with Vespa Cloud Enclave in AWS
---

Vespa Cloud Enclave builds on top of some tooling that it is necessary to become familiar with before getting started.
[Terraform](https://www.terraform.io/) is especially important, and understanding the basics is necessary.
Going through a [tutorial for AWS](https://developer.hashicorp.com/terraform/tutorials/aws-get-started) will help.

## Getting started

Setting up Enclave in your account requires:

1. Registration of the AWS account in Vespa Cloud
2. Running a Terraform configuration to provision necessary AWS resources in the account
3. Deployment of a Vespa application.

### 1. Onboarding

Contact [support@vespa.ai](mailto:support@vespa.ai) stating which tenant should be on-boarded to use Vespa Cloud Enclave.
Also include the [AWS account ID](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-identifiers.html#FindAccountId)
to associate with the tenant.

**Note:** We strongly recommend _dedicated_ accounts to use for your Vespa Cloud Enclaves.
Resources in these accounts will be fully managed by Vespa Cloud.

### 2. Configure AWS Account

The same AWS account used in step one must be prepared for deploying Vespa applications.
Use [Terraform](https://www.terraform.io/) to set up the necessary resources using the
[modules](https://registry.terraform.io/modules/vespa-cloud/enclave/aws/latest) published by the Vespa team.

Modify the
[multi-region Terraform files](https://github.com/vespa-cloud/terraform-aws-enclave/blob/main/examples/multi-region/main.tf)
for your deployment.

If you are unfamiliar with Terraform: It is a tool to manage resources and their
configuration in various cloud providers, like AWS and GCP.
Terraform has published an
[AWS](https://developer.hashicorp.com/terraform/tutorials/aws-get-started)
tutorial, and we strongly encourage Enclave users to read and follow the
Terraform recommendations for
[CI/CD](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform).

The Terraform module we provide is regularly updated to add new required
resources or extra permissions for Vespa Cloud to automate the operations of
your applications. In order for your enclave applications to use the new
features you must re-apply your terraform templates with the latest release.
The <a href="https://cloud.vespa.ai/en/notifications">
notification system</a> will let you know when a new release is available.

### 3. Deploy a Vespa application

By default, all applications are deployed on resources in Vespa Cloud accounts.
To deploy in your Enclave account,
update [deployment.xml](https://cloud.vespa.ai/en/reference/deployment.html) to reference the account used in step 1:

```xml
<deployment version="1.0" cloud-account="aws:123456789012">
    <dev />
</deployment>
```

Useful resources are [getting started](https://cloud.vespa.ai/en/getting-started)
and [migrating to Vespa Cloud](https://cloud.vespa.ai/en/migrating-to-cloud) -
put _deployment.xml_ next to _services.xml_.

## Production deployments

After a successful deployment to the [dev](https://cloud.vespa.ai/en/reference/environments.html#dev) environment,
iterate on the configuration to implement your application on Vespa.
The _dev_ environment is ideal for this, with rapid deployment cycles.

For production serving, deploy to the [prod](https://cloud.vespa.ai/en/reference/environments.html#prod) environment -
follow the steps in [production deployment](https://cloud.vespa.ai/en/production-deployment.html).
