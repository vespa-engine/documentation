---
title: Vespa Cloud Security Whitepaper
category: cloud
---

<style>
  td:nth-child(1) {
    white-space: nowrap !important;
    font-style: italic !important;
  }

  tr {
    margin-bottom: 0.5em !important;
  }
</style>

## Table of Contents

- TOC
{:toc}

## Introduction

This document describes the Vespa Cloud service security features and
operational procedures.

## Concepts and architecture

<!-- TODO: Make figure have split data plane? -->
<img alt="Vespa Cloud overall architecture diagram" style="max-height: 500px" src="/assets/img/overall-architecture.png"/>

The Vespa Cloud consists of a _Control Plane_ and a _Date Plane_. Each have
their own web service APIs, respectively managing Vespa applications (Control),
and interacting with a deployed Vespa application (Data).

The Control Plane manages deployment of applications in the zones they specify,
and lets tenant administrators manage their tenant information in Vespa Cloud.
The Control Plane is shared among all tenants in Vespa Cloud and is globally
synchronized.

The Data Plane lets the tenants communicate with their deployed Vespa
applications. It supports queries, feeding, and any other type of requests the
tenant has configured and deployed in their application. The Data Plane is
isolated for each tenant, application, and (optionally) service.

The Vespa Cloud is divided into _Zones_. A zone is a combination of an
_environment_ and a _region_ and have names like _prod.aws-us-east-1c_. Zones
are stand-alone and does not have critical dependencies on services outside the
zone. Tenants can implement service redundancy by specifying that applications
be deployed in multiple zones.

A Zone is managed by a _Configuration Server_ cluster. These receive the
application packages from the _Control Plane_ on deployment and manages the
local deployment process in the zone, including provisioning the node resources
required to run the deployed application in the zone. Separately, it is
responsible for maintaining those resources - replacing failed nodes, upgrading
their OS and similar.

Vespa applications run on _Nodes_ - a Linux container executed on a _Host_. The
_Host_ is the actual machine running the containers. Each Host has a management
process that receives instructions from the Configuration Server about what
containers should run on the Host. Once started, the containers ask the
Configuration Server cluster what Vespa services of what application they should
run.

It is the individual Node that contains the customer data such as indexes and
document, and which receives the queries and feeding requests from the
customer's authenticated and authorized clients. Each Node is always dedicated
to a single Vespa application cluster. Hosts are shared by default, but
applications may specify that they require dedicated hosts to obtain an
additional level of security isolation.

<!-- TODO: We need to define _deployment_ -->

## Service deployment

### Control plane authentication and authorization

#### Control plane API access

All API operations towards the Vespa Cloud control plane require authorization,
and no tenant or application information will be presented for unauthorized
access. A user can present a valid OAuth2 token which will be verified by the
API. If a OAuth2 token is not available the user can choose to use an API key
instead. The intended use for API keys is for service automation (e.g. CI/CD
workflows or GitHub actions), but they can also be used by developers.

#### Roles and privileges

Members of tenants in Vespa Cloud can be assigned to three different roles that
grant different privileges:

- **Reader:** Can read tenant and application metadata. This is the minimal
  privilege which is implicitly granted to all members of a tenant.
- **Developer:** Can create applications, deploy to dev and prod zones.
  These are the privileges needed by members working on applications.
- **Administrator:** Can manage members of a tenant and tenant metadata, such as
  tenant contact information and billing actions.

All role memberships are stored in an external identity provider.

### Service isolation

<img alt="image" width="100%" src="/assets/img/service-isolation.png" title="Service isolation"/>

Nodes belonging to the same application are allowed to communicate with each
other while nodes of different applications are isolated on the network layer
and through authorization.

Communication between Vespa services is encrypted and authenticated using mutual
TLS (mTLS). Identities and certificates are provided by infrastructure
components that can validate the configuration.

#### Access control and service identity

Each host and node has a unique cryptographic service identity. This identity is
required in all inter-service communication, including HTTPS and internal binary
RPC protocols. On the host, node, and configuration server level there are
authorization rules in place to ensure that only relevant services can
communicate with each other and retrieve resources from shared services, like
the configuration server.

#### Node isolation

The identity of the node is based on the tenant, application, and instance the
node is part of. The host and configuration server will together establish the
identity of the node. The configuration server tells the host which nodes it
should start, and the host requests a cryptographic identity for the nodes from
the identity provider.

This node identity is used for all internal communication inside the
application.

Nodes are implemented as Linux containers on the hosts. Each node runs in their
own container user namespaces, and each node has a dedicated IP address.

#### Host isolation

The lowest physical resource in the service architecture is a host. The
configuration server is responsible for provisioning hosts and will keep track
of known hosts, and reject any unknown hosts. Hosts only communicate directly
with the configuration server and cannot communicate with each other.

#### Configuration isolation

Both nodes and hosts will consume application configuration from the
configuration server. The configuration server will apply authorization rules
based on the host and node identity. Authorization rules are based on least
privilege. Hosts will only see which nodes to run, while the nodes are able to
access the application configuration.

#### Network isolation

All communication between services is protected through mTLS. mTLS authorization
is based on the identity mentioned above. In addition, network level isolation
is used to prevent any unauthorized network access between services. The network
rules are configured in the configuration server and applied by the host.
Changes to the topology are reflected within minutes.

## Communication

### Data plane

All access to application endpoints are secured by mTLS and optionally token authentication. 
Upon deployment, every application is provided a certificate with SAN DNS names 
matching the endpoint names. This certificate will be automatically refreshed every 
90 days. The application owner must provide a set of trusted Certificate Authorities 
which will be used by all clients when accessing the endpoints using mTLS.

### Federation

It is possible for an application owner to federate calls to 3rd party services.
Either as scheduled jobs, or per request. To support this use case we provide
access to a credential storage in the customer's AWS account.

## Data Storage

### Encryption at Rest

All customer data is encrypted at rest using the cloud provider's native encryption capabilities (AWS KMS or Google Cloud KMS).  Encryption is performed with the following properties:

* Cipher: A strong, industry-standard cipher such as AES-256 (or the provider's default strong cipher) 
* Key Management: Customer-managed keys within the respective cloud provider's key management service (AWS KMS or Google Cloud KMS)   

Access to the keys is strictly controlled and audited through IAM roles and policies employing least privilege.  Key rotation is managed automatically by the cloud provider on a regular basis.

### Data classification

All data handled by Vespa Cloud is classified into two different classes which
has different policies associated with them.

- **Internal data:** Information intended for internal consumption in Vespa
  Cloud operations. This includes system level logs from services that do not
  handle customer data. Internal data is readable by authenticated and
  authorized members of the Vespa Cloud engineering team.

- **Confidential data:** Confidential data is data that is sensitive to Vespa
  Cloud or Vespa Cloud customers. Access to confidential data is subject to
  stringent business need-to-know. Access to confidential data is regulated and
  only granted to Vespa Cloud team members in a peer-approved, time-limited, and
  audited manner. _All customer data is considered confidential._

### Asset types

<table class="table is-striped">
  <thead>
    <tr>
      <th>Asset</th>
      <th>Class</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Control Plane data</td>
      <td>Internal</td>
      <td>
        The Control Plane maintains a database to facilitate orchestration
        of Vespa applications in multiple zones.  This contains metadata
        about tenants and applications in Vespa Cloud.
      </td>
    </tr>
    <tr>
      <td>Configuration Server data</td>
      <td>Confidential</td>
      <td>
        The configuration server database contains the Vespa application
        model as well as the orchestration database.  Since the configuration
        server is part of establishing node and host identities, the configuration server data
        is considered confidential.
      </td>
    </tr>
    <tr>
      <td>Infrastructure logs</td>
      <td>Internal</td>
      <td>
        Logs from infrastructure services like the configuration servers,
        the control plane services, etc. are considered internal.
        This includes logs from Control Plane, Configuration Servers, and Hosts.
      </td>
    </tr>
    <tr>
      <td>Application package</td>
      <td>Internal</td>
      <td>
        The application.zip file uploaded to Vespa Cloud by the customer is
        considered internal.  The application package contains settings and
        configuration that Vespa Cloud operations needs insight in to operate
        the platform.
      </td>
    </tr>
    <tr>
      <td>Node logs</td>
      <td>Confidential</td>
      <td>
        The logs inside the Node may contain data printed by the customer.
        Because of this the logs are classified as confidential since Vespa
        Cloud cannot guarantee they are free of confidential data.
        This includes Data Plane access logs in addition to the node
        Vespa logs.
      </td>
    </tr>
    <tr>
      <td>Core dumps / heap dumps</td>
      <td>Confidential</td>
      <td>
        Occasionally core dumps and heap dumps are generated for running
        services.  These files may contain customer data and are considered
        confidential.
      </td>
    </tr>
    <tr>
      <td>Node data</td>
      <td>Confidential</td>
      <td>
        All data on the node itself is considered confidential.  This data
        includes the document data and the indexes of the application.
      </td>
    </tr>
  </tbody>
</table>

#### Logs

All logs are stored on the nodes where they are generated, but also archived to
a remote object storage. All logs are kept for a maximum of 30 days. Access to
logs is based on the classifications described above.  All logs are persisted in
the same geographic region as the Vespa application that generated them.

Archived logs are encrypted at rest with keys automatically rotated at regular
intervals.

Logs on the node are encrypted at rest with the same mechanism that encrypts
indexes and document databases.

### Access management

Access to confidential data is only granted on a case-by-case basis. Access is
reviewed, time-limited, and audited. No Vespa Cloud team member is allowed to
access any confidential data without review.

## Security Measures

Vespa Cloud employs a multi-layered approach to security, encompassing
vulnerability management, secure development practices, and proactive testing.
These include:

## Security Testing

Vespa Cloud proactively assesses its security posture through:

* A vulnerability disclosure program, detailed at
https://vespa.ai/responsible-disclosure/, enabling security
researchers to responsibly report potential vulnerabilities.
* A yearly hybrid security pentest program, conducted in partnership with
Intigriti, to proactively identify and address vulnerabilities.

### Secure Development

Vespa Cloud follows a CI/CD process with mandatory code review for all commits.
Static analysis tools are employed to detect issues in source code and
third-party dependencies. In addition, the security team conducts regular
internal security reviews of code and infrastructure to identify and address
potential vulnerabilities throughout the development lifecycle.

### Vulnerability Management

Vespa is released up to 4 times a week, and we strive to keep all applications
and dependencies updated to the latest versions. Operating system upgrades are
rolled out every 90 days to address OS-level vulnerabilities. In case of a
severe security issue, fixes are applied and rolled out as quickly as possible.

### Incident Response

Any unexpected production issue, including security incidents, is handled
through our incident management process. Non-security incidents are announced
through our console. Security incidents are communicated directly to affected
customers.  A post-mortem review process is initiated after every incident. In
the event of a potential security breach, a forensic investigation is conducted.