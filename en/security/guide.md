---
title: Security Guide
applies_to: cloud
redirect_from:
- /en/cloud/security/guide
---

Vespa Cloud has several security mechanisms it is important for developers to
understand. Vespa Cloud has two different interaction paths, _Data Plane_ and
_Control Plane_. Communication with the Vespa application goes through the _Data
Plane_, while the _Control Plane_ is used to manage Vespa tenants and
applications.

The _Control Plane_ and the _Data Plane_ has different security mechanisms,
described in this guide.



## SOC 2
Vespa.ai has a SOC 2 attestation - read more in the [Trust Center](https://trust.vespa.ai/).



## Data Plane

Data plane requests are protected using mutual TLS, or optionally tokens.

### Configuring mTLS

Certificates can be created using the
[Vespa CLI](../clients/vespa-cli.html):

```
$ vespa auth cert --application <tenant>.<app>.<instance>
```

```
$ vespa auth cert --application scoober.albums.default
Success: Certificate written to security/clients.pem
Success: Certificate written to $HOME/.vespa/scoober.albums.default/data-plane-public-cert.pem
Success: Private key written to $HOME/.vespa/scoober.albums.default/data-plane-private-key.pem
```

The certificates can be created regardless of the application existence in Vespa
Cloud. One can use this command to generate <code>security/clients.pem</code>
for an application package:

```
$ cp $HOME/.vespa/scoober.albums.default/data-plane-public-cert.pem security/clients.pem
```

Certificates can also be created using OpenSSL:

```
$ openssl req -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout key.pem -out security/clients.pem
```

The certificate is placed inside the application package in
[security/clients.pem](../reference/applications/application-packages.html). Make sure
`clients.pem` is placed correctly if the certificate is created with OpenSSL,
while the Vespa CLI will handle this automatically.

`security/clients.pem` files can contain multiple PEM encoded certificates by
concatenating them. This allows you to have multiple clients with separate
private keys, making it possible to rotate to a new certificate without any
downtime.


### Permissions

To support different permissions for clients, it is possible to limit the permissions of a client. Only `read` or `write` permissions are supported. 

#### Request mapping
The request actions are mapped from HTTP method. The default mapping rule is:
* GET &rarr; `read`
* PUT, POST, DELETE &rarr; `write`

For `/search/` this is replaced by:
* GET, POST &rarr; `read`

#### Example

Create 3 different certificates, for three different use cases: 
* Serving - `read`
* Ingest - `write`
* Full access - `read, write`

```
$ openssl req -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout key.pem -out security/serve.pem
$ openssl req -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout key.pem -out security/ingest.pem
$ openssl req -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout key.pem -out security/full_access.pem
```

Notes:
* Files must be placed in the <em>security</em> folder inside the application package
* Certificates must be unique
* Certificate chains are currently not supported
* Files must be written using PEM encoding

Reference the certificate files from services xml using the `clients` element:

```xml
<container version='1.0'>
    ...
    <clients>
        <client id="serve" permissions="read">
            <certificate file="security/serve.pem"/>
        </client>
        <client id="ingest" permissions="write">
            <certificate file="security/ingest.pem"/>
        </client>
        <client id="full_access" permissions="read,write">
            <certificate file="security/full_access.pem"/>
        </client>
    </clients>
  ...
</container>
```
#### Custom request mapping

The default mapping can be changed by overriding `requestHandlerSpec()`:

```java
/**
 * Example overriding acl mapping of POST requests to read
 */
public class CustomAclHandler extends ThreadedHttpRequestHandler {

    private final static RequestHandlerSpec REQUEST_HANDLER_SPEC =
            RequestHandlerSpec.builder().withAclMapping(
                    HttpMethodAclMapping.standard()
                            .override(Method.POST, AclMapping.Action.READ)
                            .build())
                    .build();

    @Override
    public RequestHandlerSpec requestHandlerSpec() {
        return REQUEST_HANDLER_SPEC;
    }
```


### Configuring tokens

Application endpoints can also be configured with token based authentication. 
Note that it is still required to define at least one client for mTLS.

{% include note.html content='
Token authentication must be explicitly enabled when used in combination with
<a href="../operations/private-endpoints.html">Private Endpoints</a>.
'%}

#### Creating tokens using the console

Tokens are identified by a name, and can contain multiple versions to easily support token rotation. 

To create a new token:
1. In the [console](https://console.vespa.ai) tenant view, open **Account > Tokens**
1. Click **Add token**
1. Enter a name you'll reference in the application later and click **Add**. Remember to copy the token value and store it securely.

To add a new token *version*:
1. Find the existing token, click **Add version**
1. Select expiration and click **Add**. Copy the token value and store securely.

To revoke a version:
1. Find the existing token version, click **Revoke**

To manually rotate a token:
1. Add a new token *version* following the above steps
1. Revoke the old version when no clients use the old version

#### Application configuration with token endpoints

After creating a token, it must be configured in your application's services.xml by adding the
[clients](../reference/applications/services/container.html#clients) element to your container cluster(s).

Here is an example with multiple container clusters and tokens (you may only have one):
```xml
<container id="documentapi" version="1.0">
    ...
    <clients>
        <client id="mtls" permissions="read,write">
            <certificate file="security/clients.pem"/>
        </client>
        <client id="feed-token-client" permissions="read,write">
            <token id="feed-token"/>
        </client>
    </clients>
    ...
</container>
<container id="query" version="1.0">
    ...
    <clients>
        <client id="mtls" permissions="read">
            <certificate file="security/clients.pem"/>
        </client>
        <client id="query-token-client" permissions="read">
            <token id="query-token"/>
        </client>
    </clients>
    ...
</container>
```


#### Security recommendations

The cryptographic properties of token authentication vs mTLS are comparable. There are however a few key differences in how they are used:
* tokens are sent as a header with every request
* since they are part of the request they are also more easily leaked in log outputs or source code (e.g. curl commands).

It is therefore recommended to 
* create tokens with a short expiry (keeping the default of 30 days).
* keep tokens in a secret provider, and remember to hide output.
* never commit secret tokens into source code repositories!



### Use endpoints

#### Using mTLS

Once the application is configured and deployed with a certificate in the
application package, requests can be sent to the application. Again, the Vespa
CLI can help to use the correct certificate.

```
$ vespa curl --application <tenant>.<app>.<instance> /ApplicationStatus
```

```
$ curl --key $HOME/.vespa/scoober.albums.default/data-plane-private-key.pem \
       --cert $HOME/.vespa/scoober.albums.default/data-plane-public-key.pem \
       $ENDPOINT
```

#### Using tokens

The token endpoint must be used when using tokens.
After deployment is complete, the token endpoint will be available in the token endpoint list (marked “Token”).
To use the token endpoint, the token should be sent as a bearer authorization header:

```
$ vespa query \
  --header="Authorization: Bearer $TOKEN" \
  'yql=select * from music where album contains "head"'
```
<!-- ToDo: Does this work with document api ? -->
```
curl -H "Authorization: Bearer $TOKEN" $ENDPOINT
```

#### Using a browser

In Vespa guides, curl is used in examples, like:

```
$ curl --cert ./data-plane-public-cert.pem --key ./data-plane-private-key.pem $ENDPOINT
```

To use a browser, install key/cert pair into KeyChain Access (MacOS Sonoma), assuming Certificate Common Name is
"cloud.vespa.example" (as in the guides):

<ol>
  <li>
    Install key/cert pair:
<pre>
$ cat data-plane-public-cert.pem data-plane-private-key.pem > pkcs12.pem
$ openssl pkcs12 -export -out pkcs12.p12 -in pkcs12.pem
</pre>
  </li>

   <li>
     New password will be requested, and it will be used in the next steps.
   </li>

  <li>
    In Keychain Access: With login keychain
        <ul>
        <li> Click "File" -> Import Items. </li>
        <li> Choose pkcs12.p12 file created before and type the password. </li>
        <li> Double-click the imported certificate, open "Trust" and set "When using this certificate" to "Always Trust". </li>
        <li> Right-click and "New Certificate Preference...", then add the $ENDPOINT. </li>
        </ul>
  </li>
  <li>
    Open the same URL in Chrome, choose the example.com certificate and allow Chrome to read the private key.
  </li>
</ol>


#### Using Postman

Many developers prefer interactive tools like
<a href="https://postman.com/">Postman</a>. The Vespa blog has an article on
<a href="https://blog.vespa.ai/interface-with-vespa-apis-using-postman/">how to
use Postman with Vespa</a>.

#### Using Cloudflare Workers
See [Using Cloudflare Workers with Vespa Cloud](cloudflare-workers).



## Control Plane

The control plane is used to manage the Vespa applications.

There are two different ways for access the Control Plane, using
`vespa auth login` to log in as a regular user and using Application Keys.
`vespa auth login` is intended for developers deploying manually to dev, while
Application Keys are intended for deploying applications to production,
typically by a continuous build tool. See more about these two methods below.

### Managing users

Tenant administrators manage user access through the Vespa Console.

<img src="/assets/img/manage-users.png" alt="Vespa Console user management"
  width="800px" height="auto" />

Users have two different privilege levels

- **Admin:** Can administrate the tenants metadata and the users of the tenant.
- **Developer:** Can administrate the applications deployed in the tenant.

### User access to Control Plane

Outside using the Vespa Console, communicating with the Control Plane is easiest
with the [Vespa CLI](../clients/vespa-cli.html).

```
$ vespa auth login
Your Device Confirmation code is: ****-****

If you prefer, you can open the URL directly for verification
Your Verification URL: https://vespa.auth0.com/activate?user_code=****-****

Press Enter to open the browser to log in or ^C to quit...

Waiting for login to complete in browser ... done

Successfully logged in.
```

After logging in with the Vespa CLI, the CLI can be used to deploy applications.
Users are logged in with the same privilege as the user described in the Vespa
Console.

### Application Key

If programmatic access to the Control Plane is needed, for example from a CI/CD
system like GitHub Actions, the Application Key can be used -
see example [deploy-vector-search.yaml](https://github.com/vespa-cloud/vector-search/blob/main/.github/workflows/deploy-vector-search.yaml).

#### Configuration

The Application Key can be generated in the Console from the Deployment Screen.
The key is generated in the browser but the private key appears as a download in
the browser. The public key can be downloaded separately from Deployment Screen.
The private key is never persisted in Vespa Cloud, so it is important that the
private key is kept securely. If lost, the private key is unrecoverable.

<img src="/assets/img/application-key.png" alt="Vespa Console application key management">

The Application Key can also be generated using the Vespa CLI.

```
$ vespa auth api-key -a <tenant>.<app>.<instance>
```

```
$ vespa auth api-key -a scoober.albums.default
Success: API private key written to $HOME/.vespa/scoober.api-key.pem

This is your public key:
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE5fQUq12J/IlQQdE8pWC5596S7x9f
HpPcyxCX2dXBS4aqKxnfN5HEyTkLCNGCo9HQljgLziqW1VFzshAdm3hHQg==
-----END PUBLIC KEY-----

Its fingerprint is:
91:1f:de:e3:9f:d3:21:28:1b:1b:05:40:52:72:81:4f

To use this key in Vespa Cloud click 'Add custom key' at
https://console.vespa-cloud.com/tenant/scoober/keys
and paste the entire public key including the BEGIN and END lines.
```

#### Using the application key

The Application Key can be used from the Vespa CLI to run requests again the
Control Plane. Action like deploying applications to Vespa Cloud.

```
$ vespa deploy -z dev.aws-us-east-1c
```



## Dataplane access

Vespa Cloud users on paid plans have access to Vespa Cloud Support.
For cases where the Vespa Team needs access to the application's data to provide
support, the Vespa support personnel can request access after an explicit approval
from the customer in the open support case.
