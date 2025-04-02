---
# Copyright Vespa.ai. All rights reserved.
title: "Migrating to Vespa Cloud"
category: cloud
---

Migrating a Vespa application to Vespa Cloud is straightforward,
as applications on Vespa Cloud supports all the same features as your self-hosted Vespa instances,
you're just gaining some new capabilities and avoid the operational work.

The high-level process is as follows:
1. Functional validation using the [dev](https://cloud.vespa.ai/en/reference/environments.html#dev) environment (this guide).
2. Deployment to a [prod](https://cloud.vespa.ai/en/reference/environments.html#prod) zone.

The rest of this guide assumes you have a [tenant](/en/cloud/tenant-apps-instances.html) ready for deployment:
<!-- ToDo: Expand this paragraph with some more details, e.g. enclave users -->
```
$ export VESPA_TENANT_NAME=mytenant
```

{% include pre-req.html %}
{% include note.html content='[Vespa Cloud Enclave](/en/cloud/enclave/enclave.html) users: Run the Enclave setup steps first.'%}

### 1. Verify source application package
An [application package](https://cloud.vespa.ai/en/reference/application-package.html) from a self-hosted system
can be deployed with minor modifications to the Vespa Cloud `dev` environment.

The root of an application package might look at this:

```
├── schemas
│   └── doc.sd
└── services.xml
```

There are often more files, the above is a minimum.
This is the root of the application package - make this the current working directory:

```
$ cd /location/of/app/package
```


### 2. Validate the Vespa CLI
Make sure the Vespa CLI is installed, see pre-requisites above:

```
$ vespa
Usage:
  vespa [flags]
  vespa [command]
```


### 3. Vespa Cloud login
Configure the local environment and log in to Vespa Cloud:

```
$ vespa config set target cloud && \
  vespa config set application $VESPA_TENANT_NAME.myapp && \
  vespa auth login
```


### 4. Add Credentials to the Application package
Create and get security credentials:

```
$ vespa auth cert
```

This will add the `security` directory to the application package,
and add a public certificate to it:

```
├── schemas
│   └── doc.sd
├── security
│   └── clients.pem
└── services.xml
```

The command also installs a key/certificate pair in the Vespa CLI home directory, see
[vespa auth cert](https://docs.vespa.ai/en/reference/vespa-cli/vespa_auth_cert.html).
This pair is used in subsequent accesses to the data plane for document and query operations.


### 5. Vespa Cloud Enclave Only: Add Account
{% include note.html content='Skip this step unless you are using [Vespa Cloud Enclave](/en/cloud/enclave/enclave.html).'%}

Add [deployment.xml](https://cloud.vespa.ai/en/reference/deployment#deployment) with your cloud provider account -
This ensures the deployment uses resources from the correct account - examples:
```xml
<deployment version="1.0" cloud-account="gcp:project-name">
   <dev />
</deployment>
```
```xml
<deployment version="1.0" cloud-account="aws:123456789012">
    <dev />
</deployment>
```
The application package should look like:
```
├── deployment.xml
├── schemas
│   └── doc.sd
├── security
│   └── clients.pem
└── services.xml
```


### 6. Remove hosts.xml
`hosts.xml` is not used in Vespa Cloud, remove it.


### 7. Modify services.xml
Edit the `<nodes>` configuration in `services.xml` - from:
```xml
<container id="default" version="1.0">
    <document-api/>
    <document-processing/>
    <search/>
    <nodes>
        <node hostalias="node4" />
        <node hostalias="node5" />
    </nodes>
</container>
```
to:
```xml
<container id="default" version="1.0">
    <document-api/>
    <document-processing/>
    <search/>
    <nodes count="2">
         <resources vcpu="2" memory="8Gb" disk="50Gb"/>
    </nodes>
</container>
```

In short, this is the Vespa Cloud syntax for resource specifications.

Example, migrating from a cluster using `c7i.2xlarge` instance type,
with a 200G disk - from the AWS specifications:
```
c7i.2xlarge  8  16  EBS-Only
```
Equivalent Vespa Cloud configuration:
```xml
<resources vcpu="8" memory="16Gb" disk="200Gb"/>
```
Repeat this for all clusters in `services.xml`. Notes:

1. As you are now migrating to the `dev` environment, what is _actually_ deployed is a minimized version.
   The configuration changes above are easily tested in this environment.
2. Using `count=2` is best practise at this point.
3. Resources must match a node instance type at the cloud providers(s) deploying to, see
   [AWS flavors](https://cloud.vespa.ai/en/reference/aws-flavors.html)
   and [GCP flavors](https://cloud.vespa.ai/en/reference/gcp-flavors.html).


### 8. Deploy to Vespa Cloud Dev Environment
At this point, the local environment and the application package is ready for deployment:

```
$ vespa deploy --wait 600
```

Please note that a first-time deployment normally takes a few minutes,
as resources are provisioned.

At this point, we recommend opening the console to observe the deployed application.
The link will be `https://console.vespa-cloud.com/tenant/mytenant/application/myapp/dev/instance/default`
(replace with your own names) - this is also easily found in the console main page:

![dev view](/assets/img/free-trial.png)

Refer to [vespa8 release notes](/en/vespa8-release-notes.html) for troubleshooting
in case the deployments fails, based on a Vespa 7 (or earlier) version.





### 9. Use the Endpoints
The endpoints are shown in the console, one can also list them like:
```
$ vespa status query
Container default at https://aa1c1234.b225678e.z.vespa-app.cloud/ is ready
```

Test the query endpoint, expect `totalCount: 0`:
```
$ vespa query 'select * from sources * where true'
```
```json
{
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 0
        },
```

In the `services.xml` examples at the start of this guide,
both `<search>` and `<document>` and configured in the same cluster, named `default`.
In case of multiple container clusters, select the one configured with `<search>`:
```
vespa query 'select * from sources * where true' --cluster myquerycluster
```

Finally, feed a document to the cluster (this is the cluster configured with `<document>`)
```
vespa feed mydoc.jsonl --cluster myfeedcluster
```

Redo the query and observe nonzero `totalCount`.


## Next steps
This is the final step in the functional validation. Please note:
{% include note.html content='Deployments to `dev` expire after 7 days of inactivity,
i.e., 7 days after the last deployment.
**This applies to all plans**.
Use the Vespa Console to extend the expiry period, or redeploy the application to add 7 more days.' %}

* Read more about the [dev](https://cloud.vespa.ai/en/reference/environments.html#dev) environment
* Feed (a subset) of the data and validate that queries and other API accesses work as expected.
* At the end of the validation process,
  continue to [production deployment](https://cloud.vespa.ai/en/production-deployment.html) to set up in production zones.
