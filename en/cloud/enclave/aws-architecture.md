---
# Copyright Vespa.ai. All rights reserved.
title: Vespa Cloud Enclave AWS Architecture
category: cloud
---

Each Enclave in the tenant AWS account corresponds to a Vespa Cloud
[zone](https://cloud.vespa.ai/en/reference/zones.html). Inside the tenant AWS account one Enclave is
contained within one single
[VPC](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html).

![Enclave architecture](/assets/img/vespa-cloud-enclave-aws.png)

#### EC2 Instances, Load Balancers, and S3 buckets

Configuration Servers inside the Vespa Cloud zone makes the decision to create
or destroy EC2 instances ("Vespa Hosts" in diagram) based on the Vespa
applications that are deployed. The Configuration Servers also set up the
Network Load Balancers needed to communicate with the deployed Vespa
application.

Each Vespa Host will periodically sync its logs to a S3 bucket ("Log Archive").
This bucket is "local" to the Enclave and provisioned by the Terraform module
inside the tenant's AWS account.

#### Networking

The Enclave VPC is very network restricted. Vespa Hosts do not have public IPv4
addresses and there is no
[NAT gateway](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
available in the VPC. Vespa Hosts have public IPv6 addresses and are able to
make outbound connections. Inbound connections are not allowed. Outbound IPv6
connections are used to bootstrap communication with the Configuration Servers,
and to report operational metrics back to Vespa Cloud.

When a Vespa Host is booted it will set up an encrypted tunnel back to the
Configuration Servers. All communication between Configuration Servers and the
Vespa Hosts will be run over this tunnel after it is set up.

### Security

The Vespa Cloud operations team does _not_ have any direct access to the
resources that is part of the customer account. The only possible access is
through the management APIs needed to run Vespa itself. In case it is needed
for, e.g. incident debugging, direct access can only be granted to the Vespa
team by the tenant itself. For further details, see the documentation for the
[`ssh`-submodule](https://registry.terraform.io/modules/vespa-cloud/enclave/aws/latest/submodules/ssh).

All communication between the Enclave and the Vespa Cloud configuration servers
is encrypted, authenticated and authorized using
[mTLS](https://en.wikipedia.org/wiki/Mutual_authentication#mTLS) with identities
embedded in the certificate. mTLS communication is facilitated with the
[Athenz](https://www.athenz.io/) service.

All data stored is encrypted at rest using
[KMS](https://docs.aws.amazon.com/kms/latest/developerguide/overview.html). All
keys are managed by the tenant in the tenant's AWS account.

The resources provisioned in the tenant AWS account is either provisioned by the
Terraform module executed by the tenant, or by the orchestration services inside
a Vespa Cloud Zone.

Resources are provisioned by the Vespa Cloud configuration servers, using the
[`provision_policy`](https://github.com/vespa-cloud/terraform-aws-enclave/blob/main/modules/provision/main.tf)
AWS IAM policy document defined in the Terraform module.

The tenant that registered the AWS account is the only tenant that can deploy
applications targeting the Enclave.

For more general information about security in Vespa Cloud, see the
[whitepaper](https://cloud.vespa.ai/en/security/whitepaper).
