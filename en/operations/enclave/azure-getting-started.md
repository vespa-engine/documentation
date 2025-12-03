---
# Copyright Vespa.ai. All rights reserved.
title: Getting started with Vespa Cloud Enclave in Azure
category: cloud
redirect_from:
- /en/cloud/enclave/azure-getting-started
- /en/cloud/enclave/azure-deploy-an-application
---

Setting up Vespa Cloud Enclave requires:

1. Registration at [Vespa Cloud](https://console.vespa-cloud.com), or use a pre-existing Vespa tenant.
2. Running a [Terraform](https://www.terraform.io/) configuration to provision necessary Azure resources in the subscription.
3. Registration of the Azure subscription in Vespa Cloud.
4. Deployment of a Vespa application.


### 1. Vespa Cloud Tenant setup

Register at [Vespa Cloud](https://console.vespa-cloud.com) or use an existing Vespa tenant.
Note that the tenant must be on a [paid plan](https://vespa.ai/pricing/).


### 2. Configure Azure subscription

Choose an Azure subscription to use for Vespa Cloud Enclave.

{% include note.html content='We recommend using a _dedicated_ subscription for your Vespa Cloud Enclave.
Resources in this subscription will be fully managed by Vespa Cloud.' %}

One subscription can host all your Vespa applications, there is no need for multiple Vespa tenants or Azure subscriptions.

The subscription must be prepared for deploying Vespa applications.
Use [Terraform](https://www.terraform.io/) to set up the necessary resources using the
[modules](https://registry.terraform.io/modules/vespa-cloud/enclave/azure/latest)
published by the Vespa team.

Feel free to use the
[multi-region example](https://github.com/vespa-cloud/terraform-azure-enclave/blob/main/examples/multi-region/main.tf)
to get started.

If you are unfamiliar with Terraform: It is a tool to manage resources and their
configuration in various cloud providers, like AWS, Azure, and GCP.
Terraform has published a
[Get Started - Azure](https://developer.hashicorp.com/terraform/tutorials/azure-get-started)
tutorial, and we strongly encourage enclave users to read and follow the
Terraform recommendations for
[CI/CD](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform).

The Terraform module we provide is regularly updated to add new required
resources or extra permissions for Vespa Cloud to automate the operations of
your applications. In order for your enclave applications to use the new
features you must re-apply your terraform templates with the latest release.
The [notification system](../notifications.html)
will let you know when a new release is available.

### 3. Onboarding

Contact [support@vespa.ai](mailto:support@vespa.ai) and provide the `enclave_config` output after
applying the Terraform, see
[Outputs](https://github.com/vespa-cloud/terraform-azure-enclave?tab=readme-ov-file#outputs).
The `enclave_config` includes which Vespa tenant should be on-boarded to use Vespa Cloud Enclave.
And the Azure tenant ID, the subscription ID, and a client ID of an Athenz identity the Terraform created.

### 4. Deploy a Vespa application

By default, all applications are deployed on resources in Vespa Cloud accounts.
To deploy in your Azure enclave subscription instead,
update [deployment.xml](../../reference/applications/deployment.html) to reference the subscription ID from step 2:

```xml
<deployment version="1.0" cloud-account="azure:11111111-1111-1111-1111-111111111111">
    <dev />
</deployment>
```

Useful resources are [getting started](../../basics/deploy-an-application.html)
and [migrating to Vespa Cloud](../../learn/migrating-to-cloud) -
put _deployment.xml_ next to _services.xml_.


## Next steps

After a successful deployment to the [dev](../environments.html#dev) environment,
iterate on the configuration to implement your application on Vespa.
The _dev_ environment is ideal for this, with rapid deployment cycles.

For production serving, deploy to the [prod](../environments.html#prod) environment -
follow the steps in [production deployment](../production-deployment.html).


## Enclave teardown

To tear down a Vespa Cloud Enclave system, do the steps above in reverse order:

1. [Undeploy the application(s)](../deleting-applications.html)
2. Undeploy the Terraform changes

It is important to undeploy the Vespa application(s) first.
After running the Terraform, Vespa Cloud cannot manage the resources allocated, so you must clean up these yourself.
