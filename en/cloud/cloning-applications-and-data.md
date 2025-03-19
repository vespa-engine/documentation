---
# Copyright Vespa.ai. All rights reserved.
title: Cloning applications and data
---

This is a guide on how to replicate a Vespa application in different environments, with or without data.
Use cases for cloning include:
* Get a copy of the application and (some) data on a laptop to work offline, or attach a debugger.
* Deploy local experiments to the `dev` environment to easily cooperate and share.
* Set up a copy of the application and (some) data to test a new major version of Vespa.
* Replicate a bug report in a non-production environment.
* Set up a copy of the application and (some) data in a `prod` environment to experiment with a CI/CD pipeline,
  without touching the current production serving.
* Onboard a new team member by setting up a copy of the application and test data in a `dev` environment.
* Clone to a `perf` environment for load testing.

This guide uses _applications_.
One can also use _instances_, but that will not work across Vespa major versions on Vespa Cloud -
refer to [tenant, applications, instances](tenant-apps-instances) for details.

Vespa Cloud has different environments `dev/perf` and `prod`, with different characteristics -
[details](https://cloud.vespa.ai/en/reference/environments).
Clone to `dev/perf` for short-lived experiments/development,
use `prod` for serving applications with a [CI/CD pipeline](automated-deployments).

As some steps are similar, it is a good idea to read through all, as details are added only the first time for brevity.
Examples are based on the
[album-recommendation](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation) sample application.

{% include note.html content='When done, it is easy to tear down resources in Vespa Cloud.
E.g., _https://console.vespa-cloud.com/tenant/mytenant/application/myapp/prod/deploy_ or
_https://console.vespa-cloud.com/tenant/mytenant/application/myapp/dev/instance/default_ to find a delete-link.
Instances in `dev/perf` environments are auto-expired ([details](https://cloud.vespa.ai/en/reference/environments)),
so application cloning is a safe way to work with Vespa.
Find more information in [deleting applications](deleting-applications).
'%}



## Cloning - self-hosted to Vespa Cloud

**Source setup:**
```
$ docker run --detach --name vespa1 --hostname vespa-container1 \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa

$ vespa deploy -t http://localhost:19071
```


**Target setup:**

[Create a tenant](getting-started) in the Vespa Cloud console, in this guide using "mytenant".


**Export source application package:**

This gets the application package and copies it out of the container to local file system:
```
$ vespa fetch -t http://localhost:19071 && \
  unzip application.zip -x application.zip
```


**Deploy target application package**

The procedure differs a little whether deploying to dev/perf or prod [environment](https://cloud.vespa.ai/en/reference/environments).
The `mvn -U clean package` step is only needed for applications with custom code.
Configure application name and create data plane credentials:
<pre>
$ vespa config set target cloud && \
  vespa config set application mytenant.myapp

$ vespa auth login

$ vespa auth cert -f

$ mvn -U clean package
</pre>
{% include note.html content='When deploying to a new app,
one will often want to generate a new data plane cert/key pair.
To do this, use `vespa auth cert -f`.
If reusing a cert/key pair, drop `-f` and make sure to put the pair in _.vespa_, to avoid errors like
`Error: open /Users/me/.vespa/mytenant.myapp.default/data-plane-public-cert.pem: no such file or directory`
in the subsequent deploy step.'%}
Then deploy the application.
Depending on the use case, deploy to <code>dev</code>/<code>perf</code> or <code>prod</code>:
<ul>
  <li>
    <code>dev</code>/<code>perf</code>:
<pre>
$ vespa deploy
</pre>
    Expect something like:
<pre>
Uploading application package ... done

Success: Triggered deployment of . with run ID 1

Use vespa status for deployment status, or follow this deployment at
https://console.vespa-cloud.com/tenant/mytenant/application/myapp/dev/instance/default/job/dev-aws-us-east-1c/run/1
</pre>
  </li>
  <li>
    Deployments to the <code>prod</code> environment requires <a href="https://cloud.vespa.ai/en/reference/deployment">deployment.xml</a> -
    select which <a href="https://cloud.vespa.ai/en/reference/zones">zone</a> to deploy to:
<pre>
$ cat &lt;&lt;EOF &gt; deployment.xml
&lt;deployment version="1.0"&gt;
    &lt;prod&gt;
        &lt;region&gt;aws-us-east-1c&lt;/region&gt;
    &lt;/prod&gt;
&lt;/deployment&gt;
EOF
</pre>
    <code>prod</code> deployments also require <code>resources</code> specifications
    in <a href="https://cloud.vespa.ai/en/reference/services">services.xml</a>
    - use <a href="https://github.com/vespa-cloud/vespa-documentation-search/blob/main/src/main/application/services.xml">
    vespa-documentation-search</a> as an example and add/replace <code>nodes</code> elements
    for <code>container</code> and <code>content</code> clusters.
    If in doubt, just add a small config to start with, and change later:
<pre>
&lt;nodes count="2"&gt;
    &lt;resources vcpu="2" memory="8Gb" disk="10Gb" /&gt;
&lt;/nodes&gt;
</pre>
    Deploy the application package:
<pre>
$ vespa prod deploy
</pre>
    Expect something like:
<pre>
Hint: See <a href="production-deployment">production deployment</a>
Success: Deployed .
See https://console.vespa-cloud.com/tenant/mytenant/application/myapp/prod/deployment for deployment progress
</pre>
    A proper deployment to a <code>prod</code> zone should have automated tests,
    read more in <a href="automated-deployments">automated deployments</a>
  </li>
</ul>

**Data copy**

Export documents from the local instance and feed to the Vespa Cloud instance:
```
$ vespa visit -t http://localhost:8080 | vespa feed -
```
Add more parameters as needed to `vespa feed` for other endpoints.


**Get access log from source:**
```
$ docker exec vespa1 cat /opt/vespa/logs/vespa/access/JsonAccessLog.default
```



## Cloning - Vespa Cloud to self-hosted
**Download application from Vespa Cloud**

Validate the endpoint, and fetch the application package:
```
$ vespa config get application
application = mytenant.myapp.default

$ vespa fetch
Downloading application package... done
Success: Application package written to application.zip
```

The application package can also be downloaded from the Vespa Cloud Console:
<ul>
  <li>
    <p>
      dev/perf: Navigate to <em>https://console.vespa-cloud.com/tenant/mytenant/application/myapp/dev/instance/default</em>,
      click <em>Application</em> to download:
    </p>
    <img src="/assets/img/app-download-dev.png" alt="Application package download from dev environment" />
  </li>
  <li>
    <p>
      prod: Navigate to <em>https://console.vespa-cloud.com/tenant/mytenant1/application/myapp/prod/deployment?tab=builds</em>
      and select the version of the application to download:
    </p>
    <img src="/assets/img/app-download-prod.png" alt="Application package download from prod environment" />
  </li>
</ul>

**Target setup:**

Note the name of the application package .zip-file just downloaded.
If changes are needed, unzip it and use `vespa deploy -t http://localhost:19071 `
to deploy from current directory:
```
$ docker run --detach --name vespa1 --hostname vespa-container1 \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa

$ vespa config set target local

$ vespa deploy -t http://localhost:19071 mytenant.myapp.default.dev.aws-us-east-1c.zip
```

**Data copy**

Set config target cloud for `vespa visit` and pipe the jsonl output into `vespa feed` to the local instance:
```
$ vespa config set target cloud

$ vespa visit | vespa feed - -t http://localhost:8080
```

**data copy - minimal**

For use cases requiring a few documents, visit just a few documents:
```
$ vespa visit --chunk-count 10
```

**Get access log from source:**

Use the Vespa Cloud Console to get access logs <!-- ToDo: more details -->



## Cloning - Vespa Cloud to Vespa Cloud
This is a combination of the procedures above.
Download the application package from dev/perf or prod,
make note of the source name, like mytenant.myapp.default.
Then use `vespa deploy` or `vespa prod deploy` as above to deploy to dev/perf or prod.

If cloning from `dev/perf` to `prod`, pay attention to changes in _deployment.xml_ and _services.xml_
as in [cloning to Vespa Cloud](#cloning---self-hosted-to-vespa-cloud).

**Data copy**

Set the feed endpoint name / paths, e.g. mytenant.myapp-new.default:
```
$ vespa config set target cloud

$ vespa visit | vespa feed - -t https://default.myapp-new.mytenant.aws-us-east-1c.dev.z.vespa-app.cloud
```

**Data copy 5%**
Set the --selection argument to `vespa visit` to select a subset of the documents.
<!-- ToDo: link to using slicing instead / as an alternative -->



## Cloning - self-hosted to self-hosted
Creating a copy from one self-hosted application to another.
Self-hosted means running [Vespa](https://vespa.ai/) on a laptop
or a [multinode system](https://docs.vespa.ai/en/operations/multinode-systems.html).

This example sets up a source app and deploys the [application package](https://cloud.vespa.ai/en/developer-guide) -
use [album-recommendation](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation)
as an example.
The application package is then exported from the source and deployed to a new target app.
Steps:

**Source setup:**
```
$ vespa config set target local

$ docker run --detach --name vespa1 --hostname vespa-container1 \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa

$ vespa deploy -t http://localhost:19071
```

**Target setup:**
```
$ docker run --detach --name vespa2 --hostname vespa-container2 \
  --publish 8081:8080 --publish 19072:19071 \
  vespaengine/vespa
```

**Export source application package**

Export files:
```
$ vespa fetch -t http://localhost:19071
```

**Deploy application package to target**

Before deploying, one can make changes to the application package files as needed. Deploy to target:
```
$ vespa deploy -t http://localhost:19072 application.zip
```

**Data copy from source to target**

This pipes the source data directly into `vespa feed` -
another option is to save the data to files temporarily and feed these individually:
```
$ vespa visit -t http://localhost:8080 | vespa feed - -t http://localhost:8081
```

**Data copy 5%**

This is an example on how to use a [selection](https://docs.vespa.ai/en/reference/document-select-language.html)
to specify a subset of the documents - here a "random" 5% selection:
```
$ vespa visit -t http://localhost:8080 --selection 'id.hash().abs() % 20 = 0' | \
  vespa feed - -t http://localhost:8081
```
<!-- ToDo: link to using slicing instead / as an alternative -->


**Get access log from source**

Get the current query access log from the source application (there might be more files there):
```
$ docker exec vespa1 cat /opt/vespa/logs/vespa/access/JsonAccessLog.default
```
