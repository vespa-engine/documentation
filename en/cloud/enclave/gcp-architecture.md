---
# Copyright Vespa.ai. All rights reserved.
title: Architecture for Vespa Cloud Enclave in GCP
category: cloud
---

### Architecture

Each Enclave in the tenant GCP project corresponds to a Vespa Cloud
[zone](https://cloud.vespa.ai/en/reference/zones.html). Inside the tenant GCP project one Enclave is
contained within one single [VPC](https://cloud.google.com/vpc/).

![Enclave architecture](/assets/img/vespa-cloud-enclave-gcp.png)

#### Compute Instances, Load Balancers, and Cloud Storage buckets

Configuration Servers inside the Vespa Cloud zone makes the decision to create
or destroy compute instances ("Vespa Hosts" in diagram) based on the Vespa
applications that are deployed. The Configuration Servers also set up the
Network Load Balancers needed to communicate with the deployed Vespa
application.

Each Vespa Host will periodically sync its logs to a Cloud Storage bucket ("Log
Archive"). This bucket is "local" to the Enclave and provisioned by the
Terraform module inside the tenant's GCP project.

#### Networking

The Enclave VPC is very network restricted. Vespa Hosts do not have public IPv4
addresses and there is no
[NAT gateway](https://cloud.google.com/nat/docs/overview) available in the VPC.
Vespa Hosts have public IPv6 addresses and are able to make outbound
connections. Inbound connections are not allowed. Outbound IPv6 connections are
used to bootstrap communication with the Configuration Servers, and to report
operational metrics back to Vespa Cloud.

When a Vespa Host is booted it will set up an encrypted tunnel back to the
Configuration Servers. All communication between Configuration Servers and the
Vespa Hosts will be run over this tunnel after it is set up.

### Security

The Vespa Cloud operations team does _not_ have any direct access to the
resources that is part of the customer account. The only possible access is
through the management APIs needed to run Vespa itself. In case it is needed
for, e.g. incident debugging, direct access can only be granted to the Vespa
team by the tenant itself. Enabling direct access is done by setting the
`enable_ssh` input to true in the enclave module. For further details, see the
documentation for the
[enclave module inputs](https://registry.terraform.io/modules/vespa-cloud/enclave/google/latest/?tab=inputs).

All communication between the Enclave and the Vespa Cloud configuration servers
is encrypted, authenticated and authorized using
[mTLS](https://en.wikipedia.org/wiki/Mutual_authentication#mTLS) with identities
embedded in the certificate. mTLS communication is facilitated with the
[Athenz](https://www.athenz.io/) service.

All data stored is encrypted at rest using
[Cloud Key Management](https://cloud.google.com/security-key-management). All
keys are managed by the tenant in the tenant's GCP project.

The resources provisioned in the tenant GCP project is either provisioned by the
Terraform module executed by the tenant, or by the orchestration services inside
a Vespa Cloud zone.

Resources are provisioned by the Vespa Cloud configuration servers, using the
[`vespa_cloud_provisioner_role`](https://github.com/vespa-cloud/terraform-google-enclave/blob/main/main.tf)
IAM role defined in the Terraform module.

The tenant that registered the GCP project is the only tenant that can deploy
applications targeting the Enclave.

For more general information about security in Vespa Cloud, see the
[whitepaper](https://cloud.vespa.ai/en/security/whitepaper).
