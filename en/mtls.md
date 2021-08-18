---
# Copyright Verizon Media. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Securing Vespa with mutually authenticated TLS (mTLS)"
---

## Introduction
*Note: This document is only relevant if you're **self-hosting Vespa**.
If you're using Vespa Cloud all services are automatically set up securely by default with full mTLS,
with all key/certificate management handled for you.*

[Transport Layer Security (TLS)](https://datatracker.ietf.org/doc/html/rfc5246) is a protocol that uses cryptography
to enable secure, tamper-proof communication over the network.
This document describes the TLS functionality in Vespa and how to configure it.
When properly configured, TLS ensures only trusted Vespa services can talk to each other.
See accompanying [reference](reference/mtls.html) for details on configuration syntax.

By default, all communication between self-hosted Vespa nodes is *unauthenticated* and *unencrypted*.
This means anyone with network access can read and write data and potentially execute commands on the system.
*Enabling TLS is therefore a fundamental part of a secure Vespa installation*.

You should configure TLS even if you already have a firewall set up to prevent outside connections to your system.
TLS helps protect against the case even where an attacker has managed to get a foothold inside your private network.
Vespa will in some future version require TLS for all internal communication.
To ensure you are ready for this, secure your systems as soon as possible.

Vespa offers two separate planes of TLS connectivity:
* **HTTP(S) application containers.** This is the edge of your cluster where search queries and feed requests are handled.
  Authentication and authorization for this plane is handled separately from cluster-internal traffic; this is covered
  in [Configuring Http Servers and Filters](jdisc/http-server-and-filters.html#ssl).
  See also [Securing the application container](securing-your-vespa-installation.html#securing-the-application-container).
* **Cluster-internal data and control planes.** This is all traffic between processes running on the nodes in your cluster.
  This includes clients connecting directly to the backends instead of going through the application container APIs.
  Only mutually authenticated TLS (mTLS) may be configured for this traffic.

This document only covers **cluster-internal traffic**.

Enabling TLS in Vespa means that all internal endpoints are mTLS protected,  even HTTP servers for status pages and metrics.
Be especially aware of this if you have custom solutions in place for collecting
and aggregating low level metrics or status pages from the Vespa backends.
Though the terms *TLS* and *mTLS* may be used interchangeably in this document, *TLS* implies *mTLS* for all cluster-internal traffic.

## Prerequisites

This section assumes you have some experience with generating and using certificates and private keys.

This feature is supported from Vespa 7.441.3.

In order to enable TLS, some extra files must be present on every node in your Vespa application:
* A file containing the X.509 certificates of all trusted Certificate Authorities in PEM format.
* A file containing the X.509 certificate chain that will be used by Vespa processes on the node. This is in standard PEM format.
  The host's own certificate should be the first certificate listed in the file, followed by intermediate certificates (if any), separated by newlines. 
* A file containing the private key corresponding to the certificate in the above chain, in PKCS#8 PEM format.
  Note that Vespa does not currently support encrypted private key files.
* A JSON configuration file telling Vespa which certificate/key files to use, and to provide further options for authorization.
  See [Writing a TLS configuration file](#writing-a-tls-configuration-file) for how to write these.

How certificate and key material is distributed to the nodes is outside the scope of this article.
See [dedicated section](#automatic-reload) for Vespa's support of automatic and live reloading of TLS credentials.

{% include warning.html content="You should never include public Certificate Authorities as part of the list of Certificate Authorities you trust.
Only use CAs that you (or your organization) directly control or trust. This is to minimize the risk of malicious actors
exploiting bugs or authentication flaws in public CAs to pose as your organization and acquire certificates
that would allow them to directly access your system.
" %}

{% include warning.html content="Private keys must be kept secret and protected against unauthorized access.
Make sure only the user running the Vespa processes can read the private key file.
Key and certificate files should only be writable by administrator users.
" %}

## <a name="configuring-tls"/>Configuring Vespa TLS
On any node running Vespa software, TLS is controlled via a single environment variable.
This variable contains an absolute path pointing to a JSON configuration file:
```sh
VESPA_TLS_CONFIG_FILE=<absolute path to configuration file>
```

This environment variable must be set to a valid file path before any Vespa services are started on the node.
All nodes in your Vespa application must have a TLS config file pointing to the certificates that are trusted by the other nodes.

See [Vespa environment variables](setting-vespa-variables.html) for information on configuring environment variables for Vespa.

Setting `VESPA_TLS_CONFIG_FILE` automatically enables TLS for all Vespa processes on the node.
Vespa command-line tools will automatically pick up the required configuration and work transparently.

{% include important.html content="If this variable is not set, Vespa starts up in insecure mode without any TLS!
" %}

### Writing a TLS configuration file
The simplest possible configuration file only needs to know the certificates to trust and the certificate/key pair that identifies the node itself.
Example:
```json
{
  "files": {
    "ca-certificates": "/absolute/path/to/ca-certs.pem",
    "certificates": "/absolute/path/to/host-certs.pem",
    "private-key": "/absolute/path/to/private-key.pem"
  }
}
```

Set the environment variable, for example by appending to the
[conf/vespa/default-env.txt](https://docs.vespa.ai/en/setting-vespa-variables.html) file in your Vespa installation:

```sh
override VESPA_TLS_CONFIG_FILE /absolute/path/to/my-tls-config.json
```

All file paths must be absolute. If a Vespa process cannot load one or more files, it will fail to start up.

### Configuring TLS peer authorization rules
For many simpler deployments, a dedicated self-signed Certificate Authority will be used for the Vespa cluster alone.
In that case simply being in possession of a valid certificate is enough to be authorized to access the cluster nodes;
no one except the Vespa nodes is expected to have such a certificate. More complex deployments may instead use
a shared CA, e.g. a corporate CA issuing certificates to nodes across many services and departments.
In that case simply having a valid certificate is not sufficient to be used as an authorization mechanism.

You can constrain which certificates may access the internal Vespa service by using *authorization rules*.
These are consulted as part of every TLS handshake and must pass before any connection can be established.

Authorization rules are specified as part of the JSON configuration file using the top-level [`authorized-peers`](reference/mtls.html#top-level-elements) member.
See the [reference documentation](reference/mtls.html#peer-authorization-rules) for details on syntax and semantics.

#### Example
Let's assume our Vespa cluster consists of many nodes, each with their own certificate signed by a shared Certificate Authority.
Each certificate contains a Subject Alternate Name (SAN) DNS name entry of the form
`<unique-node-id>.mycluster.vespa.example.com`, where *unique-node-id* is unique per cluster node.
These nodes will be running the actual Vespa services and must all be able to talk to each other.

Let's also assume there is a monitoring service that requires low-level access to the services.
Certificates presented by nodes belonging to this service will always have a Common Name (CN) value of
`vespa-monitoring.example.com` and a DNS SAN entry of the form `<instance>.<region>.monitor.example.com`.
Any monitoring instance in any us-east region must be able to access our cluster, but no others.

Our TLS config file implementing these rules may look like this:

```json
{
  "files": {
    "ca-certificates": "/absolute/path/to/ca-certs.pem",
    "certificates": "/absolute/path/to/host-certs.pem",
    "private-key": "/absolute/path/to/private-key.pem"
  },
  "authorized-peers": [
    {
      "required-credentials": [
        { "field": "CN", "must-match": "vespa-monitoring.example.com" },
        { "field": "SAN_DNS", "must-match": "*.us-east-*.monitor.example.com" }
      ],
      "description": "Backend monitoring service access"
    }, 
    {
      "required-credentials": [
        { "field": "SAN_DNS", "must-match": "*.mycluster.vespa.example.com" }
      ],
      "description": "Cluster-internal node P2P access"
    }
  ]
}
```

### <a name="automatic-reload"/>Automatic reloading of crypto material
Vespa performs periodic reloading of the specified TLS configuration file.
Currently this happens every 60 minutes. This reloading happens live and does not impact service availability.
Both certificates, the private key and authorization rules are reloaded.
Vespa currently does not watch the configuration file for changes, so altering the config file
or any of its dependencies does not trigger a reload by itself.

If live reloading fails, the old configuration continues to be used and a warning is emitted to the local Vespa log.

Vespa does not currently lock files before reading them.
To avoid race conditions where files are reloaded by Vespa while they are being written,
consider splitting file refreshing into multiple phases:
1. Instead of overwriting existing key/cert files, write *new* files with different file names.
1. Create a temporary TLS config JSON file pointing to these files.
1. Atomically rename the new TLS config file to the name specified by `VESPA_TLS_CONFIG_FILE`.
1. Garbage-collect the old files at a later point (for example at the next refresh time).

## Setting up TLS for a new Vespa application or upgrading with downtime
With no Vespa services running on any nodes, ensure the `VESPA_TLS_CONFIG_FILE` environment variable is set to
a valid configuration file path on every node, and [is visible to any Vespa start scripts](setting-vespa-variables.html).
Start Vespa services as you normally would. Check cluster health with
[vespa-get-cluster-state](reference/vespa-cmdline-tools.html#vespa-get-cluster-state)
and check [vespa-logfmt](reference/vespa-cmdline-tools.html#vespa-logfmt) for any TLS-related error messages
that indicate a misconfiguration (such as certificate rejections etc)—see the Troubleshooting section.
The cluster should quickly converge to an available state.

This is the simplest and fastest way to enable TLS, and is highly recommend if downtime is acceptable.

## Upgrading an existing non-TLS Vespa application to TLS without downtime
If you already have a Vespa application serving live traffic that you don't want to take down completely in
order to enable TLS, it's possible to perform a gradual, rolling upgrade. Doing this requires insecure and
TLS connections to be used alongside each other for some time, moving more and more nodes onto TLS.
Finally, once all nodes are speaking only TLS, the support for insecure connections must be removed entirely.

To achieve this, Vespa supports a feature called *insecure mixed mode*.
Enabling mixed mode lets all servers handle both TLS and insecure traffic at the same time.

Mixed mode is controlled via the value set in environment variable `VESPA_TLS_INSECURE_MIXED_MODE`.

TLS rollout happens in 3 phases:

**Phase 1:** clients do not use TLS, servers accept both TLS and plaintext clients
1. Set `VESPA_TLS_INSECURE_MIXED_MODE=plaintext_client_mixed_server`.
1. Set `VESPA_TLS_CONFIG` file as documented in [Configuring Vespa TLS](#configuring-tls).
1. Rolling restart of all Vespa services to make mixed mode take effect.

**Phase 2:** clients use TLS, servers accept both TLS and plaintext clients
1. Set `VESPA_TLS_INSECURE_MIXED_MODE=tls_client_mixed_server`.
1. Rolling restart of all Vespa services to make mixed mode take effect.

**Phase 3:** all clients and servers use TLS only
1. Remove the `VESPA_TLS_INSECURE_MIXED_MODE` environment variable.
1. Rolling restart of all Vespa services to make enforced TLS take effect.

{% include warning.html content="The insecure mixed mode environment variable MUST be removed from all nodes
(and all services subsequently restarted) before a cluster can be considered secure.
Even a single service left with insecure mixed mode enabled could be used by a determined attacker as a jumpgate into
other (believed secure) services.
" %}

## Verify configuration of TLS
Successful configuration should be verified at runtime once TLS is enabled on all nodes.
The [openssl s_client](https://www.openssl.org/docs/man1.1.1/man1/openssl-s_client.html) tool is suitable for this.
Connect to a Vespa service, e.g a configserver on port 19071 or a container on port 8080, and verify that `openssl s_client`
successfully completes the TLS handshake.

```sh
$ openssl s_client -connect <hostname>:<port>  -CAfile /absolute/path/to/ca-certs.pem -key /absolute/path/to/private-key.pem -cert /absolute/path/to/private-key.pem
```

Further, you should verify that servers require clients to authenticate by omitting `-key`/`-cert` from above command.
The `s_client` tool should print an error during handshake and exit immediately.
```sh
$ openssl s_client -connect <hostname>:<port>  -CAfile /absolute/path/to/ca-certs.pem
```

## FAQ
* Q: Should TLS be used even if I have a latency-sensitive real-time search application?
  * A: Yes. The Vespa cloud team has run many such applications in production for a long time and the overhead imposed by TLS is negligible.
    Significant effort have been spent tuning Vespa's TLS integrations to keep overhead to a minimum.
* Q: How much overhead does TLS impose in practice?
  * A: With modern CPUs, expect somewhere around 1-2% extra CPU usage for symmetric encryption (i.e. active connections). Connection handshakes have an expected extra latency of 2-4 ms of CPU time (network latency not included) due to more expensive cryptographic operations. Vespa performs handshake operations in separate threads to avoid stalling other network traffic. Vespa also uses long-lived connections internally to reduce the number of handshakes.

## Troubleshooting
### Disable TLS hostname validation
Vespa enables the [HTTPS endpoint identification algorithm](https://datatracker.ietf.org/doc/html/rfc2818#section-3) by default.
This extra verification can only be used if all certificates have their respective host's IP addresses and hostnames
in the Subject / Subject Alternative Names extensions.
[Disable hostname validation](reference/mtls.html#top-level-elements) if this is not the case.

