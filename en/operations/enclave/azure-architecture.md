---
# Copyright Vespa.ai. All rights reserved.
title: Architecture for Vespa Cloud Enclave in Azure
applies_to: cloud
redirect_from:
- /en/cloud/enclave/azure-architecture
---

### Architecture

With Vespa Cloud Enclave, all Azure resources associated with your Vespa Cloud applications
are in your enclave Azure subscription, as opposed to a shared Vespa Cloud subscription.

Each Vespa Cloud [zone](../zones.html) has an associated zone resource group (RG)
in the enclave subscription, that contains all the resources for that zone.  For instance,
it has one Virtual Network (VNet aka [VPC](https://cloud.google.com/vpc/)).

![Enclave architecture](/assets/img/vespa-cloud-enclave-azure.png)

#### Virtual Machines, Load Balancers, and Blob Storage

Config Servers inside the Vespa Cloud subscription makes the decision to create
or destroy virtual machines ("Vespa Hosts" in diagram) based on the Vespa
applications that are deployed. The Config Servers also set up the
Load Balancers needed to communicate with the deployed Vespa
application.

Each Vespa Host will periodically sync its logs to a Blob Storage container ("Log
Archive") in a Storage Account in the zone RG. This storage account is "local" 
to the enclave and provisioned by the Terraform module inside your Azure subscription.

#### Networking

The Zone Virtual Network (VNet aka VPC) is very network restricted. The Vespa Hosts do not
have a public IPv4 address.  But your application can connect to external IPv4 services using a 
[NAT gateway](https://learn.microsoft.com/en-us/azure/nat-gateway/nat-overview).
Vespa Hosts have public IPv6 addresses and are able to make outbound
connections. Inbound connections are not allowed. Outbound IPv6 connections are
used to bootstrap communication with the Config Servers, and to report
operational metrics back to Vespa Cloud.

When a Vespa Host is booted it will set up an encrypted tunnel back to the
Config Servers. All communication between Configuration Servers and the
Vespa Hosts will be run over this tunnel after it is set up.

### Security

The Vespa Cloud operations team does _not_ have any direct access to the
resources in your subscription. The only possible access is
through the management APIs needed to run Vespa itself. In case it is needed
for, e.g. incident debugging, direct access can only be granted to the Vespa
team by you. Enable direct access by setting the
`enable_ssh` input to true in the enclave module. For further details, see the
documentation for the
[enclave module inputs](https://registry.terraform.io/modules/vespa-cloud/enclave/azure/latest/?tab=inputs).

All communication between the enclave and the Vespa Cloud config servers
is encrypted, authenticated, and authorized using
[mTLS](https://en.wikipedia.org/wiki/Mutual_authentication#mTLS) with identities
embedded in the certificate. mTLS communication is facilitated with the
[Athenz](https://www.athenz.io/) service.

All data stored is encrypted at rest using
[Encryption At Host](https://learn.microsoft.com/en-us/azure/virtual-machines/disk-encryption-overview). All
keys are managed automatically by the Azure platform.

The resources provisioned in your Azure subscription are either provisioned by the
Vespa Cloud Enclave Terraform module you apply, or by the orchestration services inside
a Vespa Cloud zone.

Resources are provisioned by the Vespa Cloud config servers, using the
[`id-provisioner`](https://github.com/vespa-cloud/terraform-azure-enclave/blob/main/provisioner.tf)
user-assigned managed identity defined in the Terraform module.

Your Vespa tenant that registered the Azure subscription is the only Vespa Cloud tenant that can deploy
applications targeting your enclave.

For more general information about security in Vespa Cloud, see the
[whitepaper](../../security/whitepaper).
