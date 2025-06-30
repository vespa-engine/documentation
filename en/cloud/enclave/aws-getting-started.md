---
# Copyright Vespa.ai. All rights reserved.
title: Getting started with Vespa Cloud Enclave in AWS
category: cloud
---

Setting up Vespa Cloud Enclave requires:

1. Registration at [Vespa Cloud](https://console.vespa-cloud.com), or use a pre-existing tenant.
2. Registration of the AWS account ID in Vespa Cloud
3. Running a [Terraform](https://www.terraform.io/) configuration to provision AWS resources in the account.
   Go through the [AWS tutorial](https://developer.hashicorp.com/terraform/tutorials/aws-get-started) as needed.
4. Deployment of a Vespa application.


### 1. Vespa Cloud Tenant setup

Register at [Vespa Cloud](https://console.vespa-cloud.com) or use an existing tenant.
Note that the tenant must be on a [paid plan](https://vespa.ai/pricing/).


### 2. Onboarding

Contact [support@vespa.ai](mailto:support@vespa.ai) stating which tenant should be on-boarded to use Vespa Cloud Enclave.
Also include the [AWS account ID](https://docs.aws.amazon.com/accounts/latest/reference/manage-acct-identifiers.html#FindAccountId)
to associate with the tenant.

{% include note.html content='We recommend using a _dedicated_ account for your Vespa Cloud Enclave.
Resources in this account will be fully managed by Vespa Cloud.' %}

One account can host all your Vespa applications, there is no need for multiple tenants or accounts.


### 3. Configure AWS Account

The same AWS account used in step two must be prepared for deploying Vespa applications.
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
The [notification system](/en/cloud/notifications.html)
will let you know when a new release is available.


### 4. Deploy a Vespa application

By default, all applications are deployed on resources in Vespa Cloud accounts.
To deploy in your Enclave account,
update [deployment.xml](/en/reference/deployment.html) to reference the account used in step two:

```xml
<deployment version="1.0" cloud-account="aws:123456789012">
    <dev />
</deployment>
```

Useful resources are [getting started](https://docs.vespa.ai/en/cloud/getting-started)
and [migrating to Vespa Cloud](https://docs.vespa.ai/en/cloud/migrating-to-cloud.html) -
put _deployment.xml_ next to _services.xml_.


## Next steps

After a successful deployment to the [dev](https://cloud.vespa.ai/en/reference/environments.html#dev) environment,
iterate on the configuration to implement your application on Vespa.
The _dev_ environment is ideal for this, with rapid deployment cycles.

For production serving, deploy to the [prod](https://cloud.vespa.ai/en/reference/environments.html#prod) environment -
follow the steps in [production deployment](/en/cloud/production-deployment.html).


## Enclave teardown

To tear down a Vespa Cloud Enclave system, do the steps above in reverse order:

1. [Undeploy the application(s)](/en/cloud/deleting-applications.html)
2. Undeploy the Terraform changes

It is important to undeploy the Vespa application(s) first.
After running the Terraform, Vespa Cloud cannot manage the resources allocated, so you must clean up these yourself.
