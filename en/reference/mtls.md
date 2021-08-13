---
# Copyright Verizon Media. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Mutually authenticated TLS (mTLS) reference"
---

{% include note.html content="See [Securing Vespa with mutually authenticated TLS (mTLS)](../mtls.html) 
on how to secure Vespa with mutually authenticated TLS."
%}

## Environment variables


<table class="table table-striped">
    <tr><th scope="col" class="col-xs-3">Name</th><th scope="col" class="col-xs-9">Description</th></tr>
    <tr>
        <td>VESPA_TLS_CONFIG_FILE</td>
        <td>Absolute path JSON configuration file with TLS configuration.</td>
    </tr>
    <tr>
        <td>VESPA_TLS_INSECURE_MIXED_MODE</td>
        <td markdown="span">Enables TLS mixed mode. See [TLS Mixed mode](#tls-mixed-mode) for possible values.</td>
    </tr>
</table>

### <a name="tls-mixed-mode"/>TLS mixed mode
Possible TLS mixed mode settings for `VESPA_TLS_INSECURE_MIXED_MODE`:

<table class="table table-striped">
    <tr><th scope="col" class="col-xs-3">Name</th><th scope="col" class="col-xs-9">Description</th></tr>
    <tr>
        <td>plaintext_client_mixed_server</td>
        <td>Clients do not use TLS, servers accept both TLS and plaintext clients.</td>
    </tr>
    <tr>
        <td>tls_client_mixed_server</td>
        <td>Clients use TLS, servers accept both TLS and plaintext clients.</td>
    </tr>
    <tr>
        <td>tls_client_tls_server</td>
        <td>All clients and servers use TLS only.</td>
    </tr>
</table>

### Configuration file
The TLS configuration file contains a single top-level JSON object.

#### <a name="top-level-elements"/>Top-level elements
<table class="table table-striped">
    <tr><th scope="col" class="col-xs-2">Name</th><th scope="col" class="col-xs-1">Required</th><th scope="col" class="col-xs-9">Description</th></tr>
    <tr>
        <td markdown="span">[files](#files)</td>
        <td>Yes</td>
        <td>JSON object containing file system paths crypto material.</td>
    </tr>
    <tr>
        <td>accepted-ciphers</td>
        <td>No</td>
        <td>JSON array of accepted TLS cipher suites.</td>
    </tr>
    <tr>
        <td>accepted-protocols</td>
        <td>No</td>
        <td>JSON array of accepted TLS protocol versions.</td>
    </tr>
    <tr>
        <td>authorized-peers</td>
        <td>No</td>
        <td markdown="span">JSON array of [authorized-peer](#authorized-peer) objects.</td>
    </tr>
    <tr>
        <td>disable-hostname-validation</td>
        <td>No</td>
        <td>Disables TLS/HTTPS hostname validation. Enabled by default.</td>
    </tr>
</table>

#### <a name="files"/>The *files* element
<table class="table table-striped">
    <tr><th scope="col" class="col-xs-2">Name</th><th scope="col" class="col-xs-1">Required</th><th scope="col" class="col-xs-9">Description</th></tr>
    <tr>
        <td>private-key</td>
        <td>Yes</td>
        <td>Absolute path to file containing the private key in PKCS#8 PEM format.</td>
    </tr>
    <tr>
        <td>certificate</td>
        <td>Yes</td>
        <td>
            Absolute path to file containing X.509 certificate chain (including any intermediate certificates).
            Certificates must be encoded in PEM format separated by newlines.
        </td>
    </tr>
    <tr>
        <td>ca-certificates</td>
        <td>Yes</td>
        <td>
            Absolute path to file containing all trusted X.509 Certificate Authorities.
            Certificates must be encoded in PEM format separated by newlines.
        </td>
    </tr>
</table>

#### <a name="authorized-peer"/>The *authorized-peer* element
<table class="table table-striped">
    <tr><th scope="col" class="col-xs-2">Name</th><th scope="col" class="col-xs-1">Required</th><th scope="col" class="col-xs-9">Description</th></tr>
    <tr>
        <td>required-credentials</td>
        <td>Yes</td>
        <td markdown="span">A JSON array specifying each [credential requirement](#required-credential) for this particular rule.</td>
    </tr>
    <tr>
        <td>name</td>
        <td>Yes</td>
        <td>Name of the rule.</td>
    </tr>
    <tr>
        <td>description</td>
        <td>No</td>
        <td>Description of the rule.</td>
    </tr>
    <tr>
        <td>roles</td>
        <td>No</td>
        <td>JSON array containing roles assumed if peer matches against the rule.</td>
    </tr>
</table>

#### <a name="required-credential"/>The *required-credential* element
<table class="table table-striped">
    <tr><th scope="col" class="col-xs-2">Name</th><th scope="col" class="col-xs-1">Required</th><th scope="col" class="col-xs-9">Description</th></tr>
    <tr>
        <td>field</td>
        <td>Yes</td>
        <td markdown="span">Certificate field. Possible values: *CN*, *SAN_DNS*, *SAN_URI*.</td>
    </tr>
    <tr>
        <td>must-match</td>
        <td>Yes</td>
        <td>String containing a "glob"-style pattern.</td>
    </tr>
</table>

#### Example
```json
{
  "files": {
    "ca-certificates": "/absolute/path/to/ca-certs.pem",
    "certificates": "/absolute/path/to/host-certs.pem",
    "private-key": "/absolute/path/to/private-key.pem",
    "disable-hostname-validation": true,
    "accepted-ciphers": ["TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384", "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"],
    "accepted-protocols": ["TLSv1.2"]
  },
  "authorized-peers": [
    {
      "required-credentials": [
        { "field": "CN", "must-match": "vespa-monitoring.example.com" },
        { "field": "SAN_DNS", "must-match": "*.us-east-*.monitor.example.com" }
      ],
      "description": "Backend monitoring service access",
      "name": "monitoring",
      "roles": ["monitor"]
    }, 
    {
      "required-credentials": [
        { "field": "SAN_DNS", "must-match": "*.mycluster.vespa.example.com" }
      ],
      "description": "Cluster-internal node P2P access",
      "name": "cluster",
      "roles": ["monitor", "cluster"]
    }
  ]
}
```
## TLS features supported by Vespa
Vespa is built with modern, high-performance cryptography libraries that fully support TLSv1.3,
and this will be used by default for all cluster-internal communication. For security reasons,
the Vespa TLS stack has some additional constraints that are always present:
* `TLSv1.2` is the oldest TLS version that can be negotiated.
* Only cipher suites supporting [forward secrecy](https://en.wikipedia.org/wiki/Forward_secrecy) can be negotiated
  (i.e. cipher suites using ECDHE as part of their key exchange).
* Only modern, symmetric ciphers with
  [AEAD](https://en.wikipedia.org/wiki/Authenticated_encryption#Authenticated_encryption_with_associated_data)
  properties are supported. In practice this means AES-GCM. Supported cipher suites are listed [here](#cipher-suites).
* TLS compression is explicitly disabled to mitigate [CRIME](https://en.wikipedia.org/wiki/CRIME)/BREACH-style
  compression oracle attacks.
* TLS renegotiation is explicitly disabled.
* TLS session resumption is explicitly disabled, as this opens up some potential vulnerabilities related to replay attacks.
  Note that the Vespa application container edge does support session resumption, due to needing to support many frequent,
  short-lived connections from proxies and clients.

{% include note.html content="The above assumes you are using a Vespa version built with our `vespa_openssl` 
package (which is the case for all Open-Source RPMs and Docker images). 
If you are doing a custom build, it is highly recommended to build against OpenSSL 1.1.1 or newer. 
Older versions may have performance regressions or reduced crypto functionality.
OpenSSL versions prior to 1.0.1 are not supported."
%}

### Default TLS protocol settings
Vespa will by default use the following TLS configuration (unless overridden by `accepted-ciphers` / `accepted-protocols`).

#### Protocol version
* `TLSv1.2`

#### <a name="cipher-suites"/>Cipher suites
* `TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384`
* `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`
* `TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256` (JDK 12+)
* `TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256`
* `TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256`
* `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`
* `TLS_AES_128_GCM_SHA256` (TLSv1.3)
* `TLS_AES_256_GCM_SHA384` (TLSv1.3)
* `TLS_CHACHA20_POLY1305_SHA256` (TLSv1.3, JDK 12+)
