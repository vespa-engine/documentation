---
# Copyright Vespa.ai. All rights reserved.
title: Using Cloudflare Workers with Vespa Cloud
category: cloud
---

This guide describes how you can access mutual TLS protected Vespa Cloud endpoints using
[Cloudflare Workers](https://workers.cloudflare.com/).

## Writing and reading from Vespa Cloud Endpoints

Vespa Cloud's endpoints are protected using mutual TLS. 
This means the client must present a TLS certificate that the Vespa application trusts. The application
knows which certificate to trust because the certificate is included in the
Vespa application package. 

### mTLS Configuration

Mutual TLS certificates can be created using the
[Vespa CLI](https://docs.vespa.ai/en/vespa-cli.html):

For example, for tenant `samples` with application `vsearch` and instance `default`:

```
$ vespa auth cert --application samples.vsearch.default
Success: Certificate written to security/clients.pem
Success: Certificate written to $HOME/.vespa/samples.vsearch.default/data-plane-public-cert.pem
Success: Private key written to $HOME/.vespa/samples.vsearch.default/data-plane-private-key.pem
```

Refer to the [security guide](guide) for details. 

### Creating a Cloudflare Worker to interact with mTLS Vespa Cloud endpoints
In March 2023, Cloudflare announced [Mutual TLS available for Workers](https://blog.cloudflare.com/mtls-workers/), 
see also [Workers Runtime API mTLS](https://developers.cloudflare.com/workers/runtime-apis/mtls/).

Install wrangler and create a worker project.
Wrangler is the Cloudflare command line interface (CLI), refer to
[Workers:Get started guide](https://developers.cloudflare.com/workers/get-started/guide/). 
Once configured and authenticated, one can upload the Vespa Cloud data plane certificates to Cloudflare.

Upload Vespa Cloud mTLS certificates to Cloudflare:

```
$ npx wrangler mtls-certificate upload \
  --cert $HOME/.vespa/samples.vsearch.default/data-plane-public-cert.pem \
  --key $HOME/.vespa/samples.vsearch.default/data-plane-private-key.pem \
  --name vector-search-dev
```
The output will look something like this:
```
Uploading mTLS Certificate vector-search-dev...
Success! Uploaded mTLS Certificate vector-search-dev
ID: 63316464-1404-4462-baf7-9e9f81114d81
Issuer: CN=cloud.vespa.example
Expires on 3/11/2033
```

Notice the `ID` in the output; This is the `certificate_id` of the uploaded mTLS certificate. 
To use the certificate in the worker code, add an `mtls_certificates` variable to the `wrangler.toml` file
in the project to bind a name to the certificate id. In this case, bind to `VESPA_CERT`:

```
mtls_certificates = [
 { binding = "VESPA_CERT", certificate_id = "63316464-1404-4462-baf7-9e9f81114d81" }
]
```

With the above binding in place, you can access the `VESPA_CERT` in Worker code like this:

```javascript
export default {
    async fetch(request, env) {
        return await env.VESPA_CERT.fetch("https://vespa-cloud-endpoint");
    }
}
```

Notice that `env` is a variable passed by the Cloudflare worker infrastructure. 

### Worker example

The following worker example forwards POST and GET HTTP requests to the `/search/` path 
of the Vespa cloud endpoint. It rejects other paths or other HTTP methods.

```javascript
/**
 * Simple Vespa proxy that forwards read (POST and GET) requests to the 
 * /search/ endpoint
 * Learn more at https://developers.cloudflare.com/workers/
 */

export default {
  async fetch(request, env, ctx) {
    //Change to your endpoint url, obtained from the Vespa Cloud Console. 
    //Use global endpoint if you have global routing with multiple Vespa regions
    const vespaEndpoint = "https://vsearch.samples.aws-us-east-1c.dev.z.vespa-app.cloud";
    async function MethodNotAllowed(request) {
      return new Response(`Method ${request.method} not allowed.`, {
        status: 405,
        headers: {
          Allow: 'GET,POST',
        }
      });
    }
    async function NotAcceptable(request) {
      return new Response(`Path not Acceptable.`, {
        status: 406,
      });
    }

    if (request.method !== 'GET' && request.method !== 'POST') {
      return MethodNotAllowed(request);
    }
    let url = new URL(request.url)
    const { pathname, search } = url;
    if (!pathname.startsWith("/search/")) {
      return NotAcceptable(request);
    }
    const destinationURL = `${vespaEndpoint}${pathname}${search}`;
    let new_request = new Request(destinationURL, request);
    return await env.VESPA_CERT.fetch(new_request)
  },
};

```
To deploy the above to the worldwide global edge network of Cloudflare, use:

```
$ npx wrangler publish
```

To start a local instance, use:

```
$ npx wrangler dev
```

Test using `curl`:
```
$ curl --json '{"yql": "select * from sources * where true"}' http://127.0.0.1:8787/search/
```

After publishing to Cloudflare production:

```
$ curl --json '{"yql": "select * from sources * where true"}' https://your-worker-name.workers.dev/search/
```

## Data plane access control permissions
Vespa Cloud supports having multiple certificates to separate `read` and `write` access.  
This way, one can upload the read-only certificate to a Cloudflare worker to limit write access.

See [Data plane access control permissions](guide#permissions).
