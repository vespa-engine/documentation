---
# Copyright Vespa.ai. All rights reserved.
title: Getting Started (without Vespa CLI)
category: cloud
---

Follow these steps to deploy an application to the [dev zone](https://cloud.vespa.ai/en/reference/zones.html) in the Vespa Cloud.
Find more details and tips in the [developer guide](https://cloud.vespa.ai/en/developer-guide),
and see [next steps](#next-steps) for self-hosted deployment options.
Alternative versions of this guide:
* [Getting started, with Vespa CLI](getting-started)
* [Getting started, with an app having Java components](getting-started-java)
* [Getting started, using pyvespa](https://pyvespa.readthedocs.io/en/latest/getting-started-pyvespa-cloud.html) -
  for Python developers
* [Run Vespa locally, using Docker](/en/vespa-quick-start.html).
**Prerequisites:**
* Git - or download the files from
  [album-recommendation](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation)
* zip - or other tool to create a .zip file
* curl - or other tool to send HTTP requests with security credentials
* OpenSSL
---

1. **Get a sample application:**

   ```
   $ git clone --depth 1 https://github.com/vespa-engine/sample-apps.git && \
     cd sample-apps/album-recommendation
   ```

   An [application package](https://cloud.vespa.ai/en/reference/application-package) is the full application configuration.
   See [sample-apps](https://github.com/vespa-engine/sample-apps) for other sample apps you can start from instead.
2. **Create a self-signed certificate:**

   On Unix or Mac, use `openssl`:

   ```
   $ openssl req -x509 -nodes -days 14 -newkey rsa:4096 \
     -subj "/CN=cloud.vespa.example" \
     -keyout data-plane-private-key.pem -out data-plane-public-cert.pem
   ```

   On Windows, the certificate has to be created with [New-SelfSignedCertificate](https://learn.microsoft.com/en-us/powershell/module/pki/new-selfsignedcertificate) in PowerShell, and
   then exported to PEM format using [certutil](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/certutil).

   Once the certificate has been created, add it to the application package.

   ```
   $ mkdir -p app/security && \
     cp data-plane-public-cert.pem app/security/clients.pem
   ```

   This certificate and key will be used to send requests to Vespa Cloud.
   See the [security model](https://cloud.vespa.ai/en/security/guide#data-plane) for more details.
3. **Create the application package:**

   ```
   $ ( cd app && zip -r ../application.zip . )
   ```

   `application.zip` is the artifact to be deployed in next steps.
4. **Create a tenant in the [Vespa Cloud:](https://console.vespa-cloud.com/)**

   Create a *tenant* at
   [console.vespa-cloud.com](https://console.vespa-cloud.com/)
   (unless you already have one).
5. **Create and deploy the application:**

   Click *Deploy Application*.
   Use "myapp" as application name, leave the defaults.
   Make sure *DEV* is selected, and upload `application.zip`.
   Click *Create and deploy*.

   The first deployment will take a few minutes while nodes are provisioned.
   Subsequent deployments on existing nodes will be quicker.

   ```
   $ export VESPA_CLI_HOME=$PWD/.vespa TMPDIR=$PWD/.tmp
   $ mkdir -p $TMPDIR
   $ mkdir -p $VESPA_CLI_HOME/vespa-team.album-rec-java.default
   $ vespa config set target cloud
   $ vespa config set application vespa-team.album-rec-java
   $ export VESPA_CLI_API_KEY="$(echo "$VESPA_TEAM_API_KEY" | openssl base64 -A -a -d)"
   $ cp data-plane-public-cert.pem $VESPA_CLI_HOME/vespa-team.album-rec-java.default
   $ cp data-plane-private-key.pem $VESPA_CLI_HOME/vespa-team.album-rec-java.default
   $ vespa deploy --wait 600
   $ export ENDPOINT=https://album-rec-java.vespa-team.aws-us-east-1c.dev.z.vespa-app.cloud/
   ```
6. **Verify the application endpoint:**

   ```
   $ ENDPOINT=https://name.myapp.tenant-name.aws-us-east-1c.dev.z.vespa-app.cloud/
   ```
```
   $ curl --cert data-plane-public-cert.pem --key data-plane-private-key.pem $ENDPOINT
   ```

   Find the endpoint in the console output, set it for later use and test it.
   You can also [do this in a browser](https://cloud.vespa.ai/en/security/guide#using-a-browser).
   Sample output:

   ```
   {
     "handlers" : [ {
       "id" : "com.yahoo.search.handler.SearchHandler",
       "class" : "com.yahoo.search.handler.SearchHandler",
       "bundle" : "container-search-and-docproc:8.57.18",
       "serverBindings" : [ "http://*/search/*" ]
     }
     ...
   ```
7. **Write documents:**

   ```
   $ curl --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
     -H "Content-Type:application/json" \
     --data-binary @ext/A-Head-Full-of-Dreams.json \
     $ENDPOINT/document/v1/mynamespace/music/docid/a-head-full-of-dreams
   ```
```
   $ curl --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
     -H "Content-Type:application/json" \
     --data-binary @ext/Love-Is-Here-To-Stay.json \
     $ENDPOINT/document/v1/mynamespace/music/docid/love-is-here-to-stay
   ```
```
   $ curl --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
     -H "Content-Type:application/json" \
     --data-binary @ext/Hardwired...To-Self-Destruct.json \
     $ENDPOINT/document/v1/mynamespace/music/docid/hardwired-to-self-destruct
   ```

   This writes documents using [/document/v1](/en/document-v1-api-guide.html).
8. **Send queries:**

   ```
   {% raw %}
   curl --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
     -X POST -H "Content-Type: application/json" --data '
     {
         "yql": "select * from music where true",
         "ranking": {
             "profile": "rank_albums",
             "features": {
                 "query(user_profile)": "{{cat:pop}:0.8,{cat:rock}:0.2,{cat:jazz}:0.1}"
             }
         }
     }' \
     $ENDPOINT/search/
   {% endraw %}
   ```
```
   $ curl --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
   "$ENDPOINT/search/?ranking=rank_albums&yql=select%20%2A%20from%20music%20where%20true&ranking.features.query(user_profile)=%7B%7Bcat%3Apop%7D%3A0.8%2C%7Bcat%3Arock%7D%3A0.2%2C%7Bcat%3Ajazz%7D%3A0.1%7D"
   ```

   Query with a user profile to get album recommendations
   using the [Query API](/en/query-api.html).

{% include note.html content='Deployments to `dev` are removed 7 days after you last deployed it.
You can extend the expiry time in the Vespa Console.
[Read more](https://cloud.vespa.ai/en/reference/environments.html#dev).' %}

### Next steps
* [Set up deployment to production](production-deployment).
* Follow the [Vespa Blog](https://blog.vespa.ai/) for product updates and use cases.
* Explore the [Vespa documentation](/).
