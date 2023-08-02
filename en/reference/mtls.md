---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Mutually authenticated TLS (mTLS) reference"
redirect_from:
- /documentation/reference/mtls.html
---

{% include note.html content="See [Securing Vespa with mutually authenticated TLS (mTLS)](../mtls.html) 
on how to secure Vespa with mutually authenticated TLS."
%}

## Environment variables


<table class="table table-striped">
    <tr><th>Name</th><th>Description</th></tr>
    <tr>
        <td>VESPA_TLS_CONFIG_FILE</td>
        <td>Absolute path JSON configuration file with TLS configuration.</td>
    </tr>
    <tr>
        <td>VESPA_TLS_INSECURE_MIXED_MODE</td>
        <td markdown="span">Enables TLS mixed mode. See [TLS Mixed mode](#tls-mixed-mode) for possible values.</td>
    </tr>
</table>

### TLS mixed mode
Possible TLS mixed mode settings for `VESPA_TLS_INSECURE_MIXED_MODE`:

<table class="table table-striped">
    <tr><th>Name</th><th>Description</th></tr>
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

#### Top-level elements
<table class="table table-striped">
    <tr><th>Name</th><th>Required</th><th>Description</th></tr>
    <tr>
        <td markdown="span">[files](#the-files-element)</td>
        <td>Yes</td>
        <td>JSON object containing file system paths crypto material.</td>
    </tr>
    <tr>
        <td>authorized-peers</td>
        <td>No</td>
        <td markdown="span">
          JSON array of [authorized-peer](#the-authorized-peer-element) objects. Authorization engine is disabled if not specified.
          See dedicated [section](#peer-authorization-rules) on how to create peer authorization rules.</td>
    </tr>
    <tr>
        <td>accepted-ciphers</td>
        <td>No</td>
        <td markdown="span">
          JSON array of accepted TLS cipher suites. See [here](#cipher-suites) for cipher suites enabled by default.
          You can only specify a _subset_ of the default cipher suites.
          _This is an expert option_—use the default unless you have good reasons not to.
        </td>
    </tr>
    <tr>
        <td>accepted-protocols</td>
        <td>No</td>
        <td markdown="span">
          JSON array of accepted TLS protocol versions. See [here](#protocol-versions) for TLS versions enabled by default.
          You can only specify a _subset_ of the default protocol versions.
          _This is an expert option_—use the default unless you have good reasons not to.
        </td>
    </tr>
    <tr>
        <td>disable-hostname-validation</td>
        <td>No</td>
        <td markdown="span">Disables TLS/HTTPS hostname validation. Enabled by default (default value `false`).</td>
    </tr>
</table>

#### The *files* element
<table class="table table-striped">
    <tr><th>Name</th><th>Required</th><th>Description</th></tr>
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

#### The *authorized-peer* element
<table class="table table-striped">
    <tr><th>Name</th><th>Required</th><th>Description</th></tr>
    <tr>
        <td>required-credentials</td>
        <td>Yes</td>
        <td markdown="span">A JSON array specifying each [credential requirement](#the-required-credential-element) for this particular rule.</td>
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
</table>

#### The *required-credential* element
<table class="table table-striped">
    <tr><th>Name</th><th>Required</th><th>Description</th></tr>
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

#### Peer authorization rules
The `authorized-peers` member is an array of credential rule-set objects. For a peer to be considered authorized its certificate MUST match at least one rule set completely.

Each rule set must contain a `required-credentials` array of credential matchers. For a certificate to match a rule set it MUST match all its credential matchers.

A credential is matched by checking a pattern given in `must-match` against a specified certificate `field`. The following fields are currently supported:
* *CN* - the Common Name part of the certificate's Distinguished Name information. If multiple CN entries are present, the last one will be considered.
* *SAN_DNS* - a Subject Alternate Name with type DNS. A certificate may contain many SAN entries. If so, all entries are checked and the credential is considered a match if at least one entry matches.
* *SAN_URI* - a Subject Alternate Name with type URI. It is similar to *SAN_DNS* but with slightly different pattern matching semantics.

For *CN* and *SAN_DNS* fields, the `must-match` pattern is a "glob"-style pattern with the following semantics:
* `*` matches 0-n non-dot characters within a single dot-separated hostname part. This is similar to the wildcards used by certificates for HTTPS hostname validation. Examples
  * `*.baz` matches `bar.baz` but not `foo.bar.baz` or `foo.baz.bar`.
  * `*.*.baz` matches `foo.bar.baz` but not `bar.baz`.
  * `*-myservice` matches `foo-myservice` but not `bar.foo-myservice`.
* `?` matches exactly 1 non-dot character within a single dot-separated hostname part. Examples:
  * `?.bar` matches `x.bar` but not `bar`, `.bar` or `yx.bar`.
  * `?.?.baz` matches `x.y.baz` but not `x.baz` or `xx.yy.baz`.

For *SAN_URI* fields, `must-match` is also a "glob"-style pattern, with some deviation compared to *CN*/*SAN_DNS*:
* The `*` wildcard matches 0-n non-slash characters. A `/` is used as separator between the host and path components, as well as separator between path segments. Examples:
  * `vespa://myapp/content/*` matches `vespa://myapp/content/node1` but not `vespa://myapp/container/node1` or `vespa://myapp/content/node1/myservice`.
  * `vespa://*/*/*` matches `vespa://myapp/content/node1` but not `vespa://myapp/content` or `vespa://myapp/content/node1/myservice`.
* `?` in a pattern has no special behaviour - it only matches the `?` literal. URIs use `?` as separator between the path and query components.

The description field is optional and is useful for e.g. documenting why a particular ruleset is present. It has no semantic meaning to the authorization engine.

Not providing the `authorized-peers` field means only certificate validity is used for authorization.
If the `authorized-peers` field is provided, it must contain at least one entry.

#### Example

```json
{
    "files": {
        "ca-certificates": "/absolute/path/to/ca-certs.pem",
        "certificates": "/absolute/path/to/host-certs.pem",
        "private-key": "/absolute/path/to/private-key.pem",
        "disable-hostname-validation": false
    },
    "authorized-peers": [
        {
            "required-credentials": [
                { "field": "CN", "must-match": "vespa-monitoring.example.com" },
                { "field": "SAN_DNS", "must-match": "*.us-east-*.monitor.example.com" }
            ],
            "description": "Backend monitoring service access",
            "name": "monitoring"
        }, 
        {
            "required-credentials": [
                { "field": "SAN_DNS", "must-match": "*.mycluster.vespa.example.com" }
            ],
            "description": "Cluster-internal node P2P access",
            "name": "cluster"
        }
    ]
}
```
## TLS features supported by Vespa
Vespa is built with modern, high-performance cryptography libraries. For security reasons,
the Vespa TLS stack has some additional constraints that are always present:
* `TLSv1.2` is the oldest TLS version that can be negotiated.
* Only cipher suites supporting [forward secrecy](https://en.wikipedia.org/wiki/Forward_secrecy) can be negotiated
  (i.e. cipher suites using ECDHE as part of their key exchange).
* Only modern, symmetric ciphers with
  [AEAD](https://en.wikipedia.org/wiki/Authenticated_encryption#Authenticated_encryption_with_associated_data)
  properties are supported. In practice this means [AES-GCM](https://en.wikipedia.org/wiki/AES-GCM) or
  [ChaCha20-Poly1305](https://en.wikipedia.org/wiki/ChaCha20-Poly1305).
  Supported cipher suites are listed [here](#cipher-suites).
* TLS compression is explicitly disabled to mitigate [CRIME](https://en.wikipedia.org/wiki/CRIME)/BREACH-style
  compression oracle attacks.
* TLS renegotiation is explicitly disabled.
* TLS session resumption is explicitly disabled, as this opens up some potential vulnerabilities related to replay attacks.
  Note that the Vespa application container edge does support session resumption, due to needing to support many frequent,
  short-lived connections from proxies and clients.

{% include note.html content="The above assumes you are using a Vespa version built with our `vespa_openssl` 
package (which is the case for all Open-Source RPMs and Docker images). 
If you are doing a custom build, it is highly recommended building against OpenSSL 1.1.1 or newer. 
Older versions may have performance regressions or reduced crypto functionality.
OpenSSL versions prior to 1.0.1 are not supported."
%}

### Default TLS protocol settings
Vespa will by default use the following TLS configuration (unless overridden by `accepted-ciphers` / `accepted-protocols`).

#### Protocol versions
* `TLSv1.3` - _note:_ due to certain limitations in the current Java runtime, TLSv1.3 is only supported by the C++ backends for now.
  We will revisit this in the near future to ensure Java defaults to TLSv1.3 as well.
* `TLSv1.2`

#### Cipher suites
* `TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384`
* `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`
* `TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256` (JDK 12+)
* `TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256`
* `TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256`
* `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`
* `TLS_AES_128_GCM_SHA256` (TLSv1.3)
* `TLS_AES_256_GCM_SHA384` (TLSv1.3)
* `TLS_CHACHA20_POLY1305_SHA256` (TLSv1.3, JDK 12+)
