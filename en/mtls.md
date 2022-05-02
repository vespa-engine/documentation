---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Securing Vespa with mutually authenticated TLS (mTLS)"
redirect_from:
- /documentation/mtls.html
---

{% include note.html content="This document is only relevant if **self-hosting Vespa**.
If using Vespa Cloud, all services are automatically set up securely by default with full mTLS,
with all key/certificate management handled." %}

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
  Authentication and authorization for this plane is handled separately from Vespa-internal traffic; this is covered
  in [Configuring Http Servers and Filters](jdisc/http-server-and-filters.html#ssl).
  See also [Securing the application container](securing-your-vespa-installation.html#securing-the-application-container).
* **Vespa-internal communication.** This is all communication between processes running on the nodes in your cluster.
  This includes clients connecting directly to the backends instead of going through the application container APIs.
  Only mutually authenticated TLS (mTLS) may be configured for this traffic.

This document only covers **Vespa-internal communication**.

Enabling TLS in Vespa means that all internal endpoints are mTLS protected,  even HTTP servers for status pages and metrics.
Be especially aware of this if you have custom solutions in place for collecting
and aggregating low level metrics or status pages from the Vespa backends.
Though the terms *TLS* and *mTLS* may be used interchangeably in this document, *TLS* implies *mTLS* for all Vespa-internal traffic.



## Prerequisites

This section assumes you have some experience with generating and using certificates and private keys.
For an introduction, see [Appendix A: setting up with a self-signed Certificate Authority](#appendix-a-setting-up-with-a-self-signed-certificate-authority)
which gives step-by-step instructions on setting up certificates that can be used internally for a
single Vespa application.

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
See [dedicated section](#automatic-reloading-of-crypto-material) for Vespa's support of automatic and live reloading of TLS credentials.

{% include warning.html content="You should never include public Certificate Authorities as part of the list of Certificate Authorities you trust.
Only use CAs that you (or your organization) directly control or trust. This is to minimize the risk of malicious actors
exploiting bugs or authentication flaws in public CAs to pose as your organization and acquire certificates
that would allow them to directly access your system.
" %}

{% include warning.html content="Private keys must be kept secret and protected against unauthorized access.
Make sure only the user running the Vespa processes can read the private key file.
Key and certificate files should only be writable by administrator users." %}



## Configuring Vespa TLS
On any node running Vespa software, TLS is controlled via a single environment variable.
This variable contains an absolute path pointing to a JSON configuration file:
```sh
VESPA_TLS_CONFIG_FILE=/absolute/path/to/my-tls-config.json
```

This environment variable must be set to a valid file path before any Vespa services are started on the node.
All nodes in your Vespa application must have a TLS config file pointing to the certificates that are trusted by the other nodes.

See [Vespa environment variables](reference/files-processes-and-ports.html#environment-variables)
for information on configuring environment variables for Vespa.

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

Set the environment variable, for example by appending to
[conf/vespa/default-env.txt](reference/files-processes-and-ports.html#environment-variables):

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

See the [reference documentation](reference/mtls.html#peer-authorization-rules) for details on syntax and semantics.


### Automatic reloading of crypto material
Vespa performs periodic reloading of the specified TLS configuration file.
Currently, this happens every 60 minutes. This reloading happens live and does not impact service availability.
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
a valid configuration file path on every node,
and [is visible to any Vespa start scripts](reference/files-processes-and-ports.html#environment-variables).
Start Vespa services as you normally would. Check cluster health with
[vespa-get-cluster-state](reference/vespa-cmdline-tools.html#vespa-get-cluster-state)
and check [vespa-logfmt](reference/vespa-cmdline-tools.html#vespa-logfmt) for any TLS-related error messages
that indicate a misconfiguration (such as certificate rejections etc.)—see the Troubleshooting section.
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
1. Set `VESPA_TLS_CONFIG` file as documented in [Configuring Vespa TLS](#configuring-vespa-tls).
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
$ openssl s_client -connect <hostname>:<port>  -CAfile /absolute/path/to/ca-certs.pem -key /absolute/path/to/private-key.pem -cert /absolute/path/to/host-cert.pem
```

Further, you should verify that servers require clients to authenticate by omitting `-key`/`-cert` from above command.
The `s_client` tool should print an error during handshake and exit immediately.
```sh
$ openssl s_client -connect <hostname>:<port>  -CAfile /absolute/path/to/ca-certs.pem
```



## FAQ
* **Q: Should TLS be used even if I have a latency-sensitive real-time search application?**
  * A: Yes. The Vespa cloud team has run many such applications in production for a long time and the overhead imposed by TLS is negligible.
    Significant effort have been spent tuning Vespa's TLS integrations to keep overhead to a minimum.
* **Q: How much overhead does TLS impose in practice?**
  * A: With modern CPUs, expect somewhere around 1-2% extra CPU usage for symmetric encryption (i.e. active connections). Connection handshakes have an expected extra latency of 2-4 ms of CPU time (network latency not included) due to more expensive cryptographic operations. Vespa performs handshake operations in separate threads to avoid stalling other network traffic. Vespa also uses long-lived connections internally to reduce the number of handshakes.



## Troubleshooting

### Certificate validation fails due to mismatching hostnames

Vespa enables the [HTTPS endpoint identification algorithm](https://datatracker.ietf.org/doc/html/rfc2818#section-3) by default.
This extra verification can only be used if all certificates have their respective host's IP addresses and hostnames
in the Subject / Subject Alternative Names extensions.
[Disable hostname validation](reference/mtls.html#top-level-elements) if this is not the case.


### Application deployment fails with `SEC_ERROR_BAD_KEY`

This is usually caused by running `vespa-deploy` from an OS that has an old version of `curl` (such as on CentOS 7).
Older versions of the NSS cryptographic library used by `curl` do not support elliptic curve (EC) keys.

To resolve this, either run `vespa-deploy` from an environment with a sufficiently new version of `curl` or
use RSA keys instead of EC keys.



## Appendix A: setting up with a self-signed Certificate Authority

Our goal is to create cryptographic keys and certificates that can be used by Vespa for secure mTLS
communication within a single Vespa installation.

This requires the following steps, which we'll go through below:

1. [Creating a root Certificate Authority](#creating-a-root-certificate-authority-ca).
   This is only done once, regardless of how many Vespa hosts you want to secure.
1. [Creating a private key and Certificate Signing_request for each Vespa host](#creating-a-private-key-and-certificate-for-a-vespa-host).
1. [Signing the CSR using the CA, creating a certificate for each Vespa host](#sign-host-certificate).

We'll be using the [OpenSSL command-line tool](https://www.openssl.org/docs/man1.1.1/man1/) to
generate all our crypto keys and certificates.

{% include note.html content="If you are setting up Vespa in an organization
that already has procedures for provisioning keys and certificates,
you should first reach out to the team responsible for this to make sure you're following best practices." %}


### Creating a root Certificate Authority (CA)

When a server (or client) presents a certificate as part of proving its identity to us, we
must have a way to determine if this information is trustworthy. We do this by verifying
if the certificate is _cryptographically signed_ by a [Certificate Authority (CA)](https://en.wikipedia.org/wiki/Certificate_authority)
that we already know we can trust. It is possible that the certificate is in fact signed by a CA that we don't
directly trust, but that in turn is signed by a CA that we _do_ trust. These are known as
_intermediate_ Certificate Authorities and are part of what's known as the _certificate chain_.
There may be more than one intermediate CA in a chain. In our simple setup we will not be using
any intermediate CAs.

At the top of the chain sits a _root_ Certificate Authority. Since we trust the root CA, we also
implicitly trust any intermediate CA it has signed and in turn any leaf certificates such an
intermediate CA has signed.

A root Certificate Authority is special in that it has no CA above it to sign in. It is _self-signed_.

To create our own root CA for our Vespa installation we'll first create its [_private key_](https://en.wikipedia.org/wiki/Public-key_cryptography).

We have two choices of what kind of key to create; either based on [RSA](https://en.wikipedia.org/wiki/RSA_(cryptosystem))
or [Elliptic Curve (EC)](https://en.wikipedia.org/wiki/Elliptic-curve_cryptography)
cryptography. EC keys are faster to process than RSA-based keys and take up less space, but older
OS versions or cryptographic libraries may not support these (see
[Application deployment fails with `SEC_ERROR_BAD_KEY`](#application-deployment-fails-with-sec_error_bad_key)).
In the latter case, RSA keys offer the highest level of backwards compatibility.

(Recommended) either create an Elliptic Curve private key:
```
$ openssl ecparam -name prime256v1 -genkey -noout -out root-ca.key
```

**OR:** create an RSA private key:
```
$ openssl genrsa -out root-ca.key 2048
```

The root CA private key is stored in `root-ca.key`. This key is used to sign certificates and the
file MUST therefore be kept secret! If it is compromised, an attacker can create any number of
valid certificates that impersonate your Vespa hosts.

We'll now create our CA X.509 certificate, self-signed with the private key. Substitute the information
given in `-subj` with whatever is appropriate for you; it's not really important for our
simple usage.

```
$ openssl req -new -x509 -nodes \
    -key root-ca.key \
    -out root-ca.pem \
    -subj '/C=US/L=California/O=ACME/OU=ACME test root CA' \
    -sha256 \
    -days 3650
```

Copy the resulting `root-ca.pem` file to your Vespa node(s) and point the `"ca-certificates"`
field in the TLS config file to its absolute file path on the node.

With both the CA key and certificate, we have what we need to start signing certificates for
the hosts Vespa will be running on.


### Creating a private key and certificate for a Vespa host

_Note: This section can be repeated for each Vespa host in your application.
See [Alternatives to having a unique certificate per individual host](#alternatives-to-having-a-unique-certificate-per-individual-host)
for (possibly less secure) options that do not require doing this step per host._

Just like our CA our host needs its own private cryptographic key.

If we're using Elliptic Curve keys:
```
$ openssl ecparam -name prime256v1 -genkey -noout -out host.key
```

**OR:** if we're using RSA keys:
```
$ openssl genrsa -out host.key 2048
```

As part of creating the certificate we'll first create a [Certificate Signing Request (CSR)](https://en.wikipedia.org/wiki/Certificate_signing_request).
Again, you can substitute the information in `-subj` with something more appropriate for you.

```
$ openssl req -new \
    -key host.key -out host.csr \
    -subj '/C=US/L=California/OU=ACME/O=My Vespa App' \
    -sha256
```

#### Sign host certificate

By default, Vespa runs with TLS hostname validation enabled, which requires the server's certificate
to contain a hostname matching what the client is connecting to. This is fundamental to the security
of protocols such as HTTP, but often sees less use with mTLS. Vespa supports it as an added layer of
security. Using certificates containing hostnames has the added benefit that you can run tools such
as `curl` against Vespa HTTPS status pages without having to explicitly disable certificate verification.

Certificates can contain many entries known as ["Subject Alternate Names" (SANs)](https://en.wikipedia.org/wiki/Subject_Alternative_Name)
that list what DNS names and IP addresses the certificate is issued for.
We'll add a single such DNS SAN entry with the hostname of our node. We'll also use the opportunity
to add certain X.509 extensions to the certificate that specifies exactly what the certificate can
be used for.

Below, substitute `myhost.example.com` with the hostname of your Vespa node.
```
$ cat > cert-exts.cnf << EOF
[host_cert_extensions]
basicConstraints       = critical, CA:FALSE
keyUsage               = critical, digitalSignature, keyAgreement, keyEncipherment
extendedKeyUsage       = serverAuth, clientAuth
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid,issuer
subjectAltName         = @host_sans
[host_sans]
DNS.1 = myhost.example.com
EOF
```

We can now use our existing CA key and certificate to sign the host's CSR, additionally
providing the above file of certificate extensions to OpenSSL.

```
$ openssl x509 -req \
    -in host.csr \
    -CA root-ca.pem \
    -CAkey root-ca.key \
    -CAcreateserial \
    -out host.pem \
    -extfile cert-exts.cnf \
    -extensions host_cert_extensions \
    -days 3650 \
    -sha256
```

This creates an X.509 certificate in PEM format for the host, valid for 3650 days from the
time of signing.

We can inspect the certificate using the `openssl x509` command. Here's some example output
for a certificate using EC keys. Your output will look different since the serial
number, dates and key information etc. will differ.

```
$ openssl x509 -in host.pem -text -noout
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 13516182920561857512 (0xbb9320c1234a93e8)
    Signature Algorithm: ecdsa-with-SHA256
        Issuer: C=US, L=California, O=ACME, OU=ACME test root CA
        Validity
            Not Before: Aug 19 13:09:37 2021 GMT
            Not After : Aug 17 13:09:37 2031 GMT
        Subject: C=US, L=California, OU=ACME, O=My Vespa App
        Subject Public Key Info:
            Public Key Algorithm: id-ecPublicKey
                Public-Key: (256 bit)
                pub:
                    04:ed:01:0e:1e:c5:05:17:99:41:74:68:a0:c5:32:
                    52:4f:45:d5:04:f8:a0:9c:35:26:ae:66:0c:e5:89:
                    34:5c:21:09:b8:a9:ed:81:22:06:bb:d1:1c:9e:13:
                    80:0a:9a:9e:0c:a0:78:ac:7c:c4:6f:1c:ec:e6:df:
                    c1:59:2d:71:8e
                ASN1 OID: prime256v1
                NIST CURVE: P-256
        X509v3 extensions:
            X509v3 Basic Constraints: critical
                CA:FALSE
            X509v3 Key Usage: critical
                Digital Signature, Key Encipherment, Key Agreement
            X509v3 Extended Key Usage:
                TLS Web Server Authentication, TLS Web Client Authentication
            X509v3 Subject Key Identifier:
                08:EF:C7:B4:95:36:64:EC:2A:2F:9F:5A:C3:EA:F0:98:2C:E5:78:EC
            X509v3 Authority Key Identifier:
                DirName:/C=US/L=California/O=ACME/OU=ACME test root CA
                serial:94:77:40:20:69:50:87:45

            X509v3 Subject Alternative Name:
                DNS:myhost.example.com
    Signature Algorithm: ecdsa-with-SHA256
         30:45:02:21:00:91:58:bb:7f:47:75:60:c3:49:09:b3:d2:54:
         ad:d2:47:58:1c:17:c7:5a:5f:f0:f4:9c:67:e9:6a:44:21:8e:
         08:02:20:23:9c:99:42:1b:91:29:26:f7:83:58:d1:09:65:38:
         c1:18:e8:0d:55:3a:57:f6:e0:c6:5b:72:57:e4:d9:6a:d8
```

Copy `host.key` and `host.pem` to your Vespa host and point the `"private-key"` and
`"certificates"` TLS config fields to their respective absolute paths. The CSR and
extension config files can be safely discarded.

{% include warning.html content="Ensure that `host.key` is only readable by the Vespa user on your host(s)" %}


### Alternatives to having a unique certificate per individual host

It's possible to avoid having to create a separate certificate per host in favor of a single certificate
shared between all hosts.

* Hostname SANs do not have to be added (or match) if hostname validation is explicitly disabled in the
  TLS config file. **Caveat:** this makes it impossible for clients to verify that they're talking to the host they expected.
* Many SAN entries can be added to the extension file, one per host. **Caveat:** new certificates must be generated
  if new hosts are added to the Vespa application that aren't already in the SAN list.
* If all hosts share a common pattern (e.g. `foo.vespa.example.com` and `bar.vespa.example.com`) it's possible to use
  a wildcard DNS SAN entry (`*.vespa.example.com`) instead of listing all hosts.

However, for production deployments we recommend using a distinct certificate per host to help mitigate
the impact of a host being compromised.
