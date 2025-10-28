---
# Copyright Vespa.ai. All rights reserved.
title: Getting Started
category: cloud
---

Follow these steps to deploy an application to the [dev zone](https://cloud.vespa.ai/en/reference/zones.html) in the Vespa Cloud.
Find more details and tips in the [developer guide](https://cloud.vespa.ai/en/developer-guide).
Alternative versions of this guide:
* [Getting started, without Vespa CLI](getting-started-shell)
* [Getting started, with an app having Java components](getting-started-java)
* [Getting started, using pyvespa](https://pyvespa.readthedocs.io/en/latest/getting-started-pyvespa-cloud.html) -
  for Python developers
* [Run Vespa locally, using Docker](/en/vespa-quick-start.html).


{% include pre-req.html %}
---

1. **Create a tenant in the [Vespa Cloud:](https://console.vespa-cloud.com/)**

   Create a *tenant* at
   [console.vespa-cloud.com](https://console.vespa-cloud.com/)
   (unless you already have one).
2. **Install the [Vespa CLI](/en/vespa-cli)**
   using [Homebrew](https://brew.sh/):

   ```
   $ brew install vespa-cli
   ```
3. **Configure the Vespa client:**

   ```
   $ vespa config set target cloud && \
     vespa config set application tenant-name.myapp
   ```
```
   $ export VESPA_CLI_HOME=$PWD/.vespa TMPDIR=$PWD/.tmp
   $ mkdir -p $TMPDIR
   $ vespa config set target cloud
   $ vespa config set application vespa-team.album-rec-java
   ```

   Use the tenant name from step 2.
   This guide uses `myapp` as application name and `default` as instance name -
   [learn more](tenant-apps-instances).
4. **Authorize Vespa Cloud access:**

   ```
   $ vespa auth login
   ```
```
   $ export VESPA_CLI_API_KEY="$(echo "$VESPA_TEAM_API_KEY" | openssl base64 -A -a -d)"
   ```

   Follow the instructions from the command to authenticate.
5. **Get a sample application:**

   ```
   $ vespa clone album-recommendation myapp && cd myapp
   ```

   An [application package](https://cloud.vespa.ai/en/reference/application-package) is the full application configuration.
   See [sample-apps](https://github.com/vespa-engine/sample-apps) for other sample apps you can clone instead.
6. **Add public certificate:**

   ```
   $ vespa auth cert app
   ```

   This creates a self-signed certificate for data plane access (reads and writes),
   and adds it to the application package. See the [security model](https://cloud.vespa.ai/en/security/guide#data-plane) for details.
7. **Deploy the application:**

   ```
   $ vespa deploy --wait 600 ./app
   ```

   The first deployment will take a few minutes while nodes are provisioned.
   Subsequent deployments on existing nodes will be quicker.
8. **Feed documents:**

   ```
   $ vespa feed dataset/documents.jsonl
   ```
9. **Run queries:**

   ```
   $ vespa query "select * from music where album contains 'head'"
   ```
```
   {% raw %}
   $ vespa query \
     "select * from music where true" \
     "ranking=rank_albums" \
     "ranking.features.query(user_profile)={{cat:pop}:0.8,{cat:rock}:0.2,{cat:jazz}:0.1}"
   {% endraw %}
   ```

   These requests use the [Query API](/en/query-api.html).

{% include note.html content='Deployments to `dev` are removed 7 days after you last deployed it.
You can extend the expiry time in the Vespa Console.
[Read more](https://cloud.vespa.ai/en/reference/environments.html#dev).' %}

## Next steps
* [Set up deployment to production](production-deployment).
* Follow the [Vespa Blog](https://blog.vespa.ai/) for product updates and use cases.
* Explore the [Vespa documentation](/).
