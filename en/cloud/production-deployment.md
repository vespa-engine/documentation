---
# Copyright Vespa.ai. All rights reserved.
title: Production Deployment
category: cloud
---

Production zones enable serving from various locations,
with a [CI/CD pipeline](/en/cloud/automated-deployments) for safe deployments.
This guide goes through the minimal steps for a production deployment - in short:
* Configure a production zone in [deployment.xml](https://cloud.vespa.ai/en/reference/deployment).
* Configure resources for clusters in [services.xml](https://cloud.vespa.ai/en/reference/services).
* Name the tenant, application, log in.
* Create or have access to the data-plane cert/key pair.
* Deploy the application to Vespa Cloud.

The sample application used in [getting started](https://cloud.vespa.ai/en/getting-started) is a good basis for these steps,
see [source files](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation).

Read [migrating to Vespa Cloud](https://cloud.vespa.ai/en/migrating-to-cloud) first,
as a primer on deployment and endpoint usage.

There are alternative ways of deploying at the end of this guide, too.

## deployment.xml

Add a `<prod>` element to *deployment.xml*:

```
{% highlight xml %}


        aws-us-east-1c


{% endhighlight %}
```

If *deployment.xml* does not exist, add it to the application package root (next to *services.xml*).

{% include note.html content='
If the application uses [private endpoints](https://cloud.vespa.ai/en/private-endpoints.html),
add this configuration here, too, and run the setup steps in the guide.'%}

## services.xml

Modify *services.xml* - minimal example:

```
{% highlight xml %}










        2








{% endhighlight %}
```

For production deployments, at least 2 nodes are required for each
cluster to ensure availability during maintenance tasks and upgrades.
The `nodes`-section is also where you specify your required [resources](https://cloud.vespa.ai/en/reference/services.html#resources):

```
{% highlight xml %}



{% endhighlight %}
```

Also note the minimum redundancy requirement of 2:

```
{% highlight xml %}
        2
{% endhighlight %}
```

## Minimum resources

To help ensure a reliable service, there is a minimum resource requirement for nodes in the production environment.
The minimum is currently 0.5 VCPU, 8Gb of memory, and for disk, 2 x memory for stateless nodes, or 3 x memory for content nodes.
As the disk resource is normally the least expensive,
we recommend it should be allocated generously to ensure it does not limit the use of more expensive cpu and memory resources.

## Application name

Give the deployment a name and log in:

```
$ vespa config set target cloud
$ vespa config set application mytenant.myapp
$ vespa auth login
```

The tenant name is found in the console, the application is something unique within your organization -
see [tenants, applications and instances](https://cloud.vespa.ai/en/tenant-apps-instances).

## Add public certificate

Just as in the [getting started](https://cloud.vespa.ai/en/getting-started) guide,
the application package needs the public key in the *security* directory.
You might already have a pair, if not generate it:

```
$ vespa auth cert -f
Success: Certificate written to security/clients.pem
Success: Certificate written to /Users/me/.vespa/mytenant.myapp.default/data-plane-public-cert.pem
Success: Private key written to /Users/me/.vespa/mytenant.myapp.default/data-plane-private-key.pem
```

Observe that the files are put in *$HOME/.vespa*.
The content from *data-plane-public-cert.pem* is copied to *security/clients.pem*.
More details on [data-plane access control permissions](https://cloud.vespa.ai/en/security/guide#permissions).

## Deploy the application

Package the application and deploy it to a production zone:

```
$ vespa prod deploy
```

Find alternative deployment procedures in the next sections.

{% include note.html content='
The `vespa prod deploy` command to prod zones,
which uses [deployment.xml](https://cloud.vespa.ai/en/reference/deployment)
differs from the `vespa deploy` command used for dev/perf zones - see
[environments](https://cloud.vespa.ai/en/reference/environments).'%}

## Endpoints

Find the 'zone' endpoint to use under Endpoints in the [console](https://console.vespa-cloud.com/).
There is an mTLS endpoint for each zone by default.
See [configuring mTLS](https://cloud.vespa.ai/en/security/guide#configuring-mtls)
for how to use mTLS certificates.

You can also add [access tokens](https://cloud.vespa.ai/en/security/guide#configure-tokens)
in the console as an alternative to mTLS,
and specify [global](https://cloud.vespa.ai/en/reference/deployment#endpoints-global)
and [private](https://cloud.vespa.ai/en/reference/deployment#endpoint-private) endpoints
in *deployment.xml*.

Write data efficiently using the
[document/v1 API](/en/reference/document-v1-api-reference.html) using HTTP/2,
or with the [Vespa CLI](/en/vespa-cli.html).
There is also a [Java library](/en/vespa-feed-client.html#java-library).

To feed data from a self-hosted Vespa into a new cloud instances, see the
[appendix](#feeding-data-from-an-existing-vespa-instance) or
[cloning applications and data](https://cloud.vespa.ai/en/cloning-applications-and-data).

Also see the [http best practices documentation](https://cloud.vespa.ai/en/http-best-practices).

## Automate deployments

Use [deploy-vector-search.yaml](https://github.com/vespa-cloud/vector-search/blob/main/.github/workflows/deploy-vector-search.yaml) as a starting point,
and see [Automating with GitHub Actions](/en/cloud/automated-deployments.html#automating-with-github-actions)
for more information.

## Production deployment using console

Instead of using the [Vespa CLI](/en/vespa-cli.html),
one can build an application package for production deployment using zip only:
* Create [deployment.xml](#deployment-xml)
  and modify [services.xml](#services-xml) as above.
* Skip the [Application name](#application-name) step.
* Add a public certificate to *security/clients.pem*.
  See [creating a self-signed certificate](https://cloud.vespa.ai/en/getting-started-shell#create-a-self-signed-certificate)
  for how to create the key/cert pair, then copy the cert file to *security/clients.pem*.
  At this point, the files are ready for deployment.
* Create a deployable zip-file:

  ```
  $ zip -r application.zip . \
    -x application.zip "ext/*" README.md .gitignore ".idea/*"
  ```
* Click *Create Application* in the [console](https://console.vespa-cloud.com/).
  Select the *PROD* tab.
  Enter a name for the application and drop the *application.zip* file in the upload section.
* Click *Create and deploy* to deploy the application to the production environment.

## Production deployment with components

Deploying an application with [Components](/en/jdisc/container-components.html)
is a little different from above:
* The application package root is at *src/main/application*.
* Find the Vespa API version to compile the component.
* The application package is built into a zip artifact, before deploying it.

See [Getting started java](https://cloud.vespa.ai/en/getting-started-java.html) for prerequisites. Procedure:

1. Use the [album-recommendation-java](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation-java) sample application as a starting point.
2. Make the same changes to *src/main/application/deployment.xml* and
   *src/main/application/services.xml*.
3. Run the same steps for [Application name](#application-name) and
   [Add public certificate](#add-public-certificate).
4. Find the lowest Vespa version of the current deployments (if any) -
   [details](/en/cloud/automated-deployments#deploying-components):

   ```
   $ mvn vespa:compileVersion \
     -Dtenant=mytenant \
     -Dapplication=myapp
   ```
5. Build *target/application.zip*:

   ```
   $ mvn -U package -Dvespa.compile.version="$(cat target/vespa.compile.version)"
   ```
6. Run the [Deploy the application](#deploy-the-application) step.
   Here, the Vespa CLI command will deploy *target/application.zip* built in the step above.

## Next steps
* Vespa Cloud takes responsibility for rolling out application changes
  to all production zones as well as testing the changes first.
  You will usually want to set up a job which automatically builds your application package
  when changes to it are checked in, to get continuous deployment of your application.
  Read [automated deployments](/en/cloud/automated-deployments)
  for automation, adding CD tests and multi-zone deployments.
* Once you have experience with load patterns, consider [autoscaling](/en/cloud/autoscaling.html).
* Set up [monitoring](monitoring.html).

## Feeding data from an existing Vespa instance

To dump data from an existing Vespa instance, you can use this command with Vespa CLI:

```
slices=10
for slice in $(seq 0 $((slices-1))); do
    vespa visit \
        --slices $slices --slice-id $slice \
        --target [existing Vespa instance endpoint] \
        | gzip > dump.$slice.gz &
done
```

This dumps all the content to files, but you can also pipe the content directly into 'vespa feed'.

To feed the data:

```
slices=10
for slice in $(seq 0 $((slices-1))); do
    zcat dump.$slice.gz | \
    vespa feed \
        --application <tenant>.<application>.<instance> \
        --target [zone endpoint from the Vespa Console] -
done
```

Note that the different slices in these commands can be done in parallel on different machines.

## Accessing a public cloud application from another VPC on another account

A common challenge when deploying on the public cloud, is network connectivity between workloads
running in different accounts and VPCs. Within in a team, this is often resolved by setting up
VPC peering between VPCs, but this has its challenges when coordinating between many different
teams and dynamic workloads. Vespa does not support direct VPC peering.

There are three recommended options:

1. **Use your public endpoints, but IPv6 if you can:** The default.
   There are many advantages to a Zero-Trust approach and accessing your application through the public endpoint.
   If you use IPv6, you will also avoid some of the network costs associated with IPv4 NATs, etc.
   For some applications, this option could be cost prohibitive,
   but one should not assume this is the case for all applications
   with a moderate amount of data being transferred over the endpoint.
2. **Use private endpoints via AWS PrivateLink or GCP Private Service Connect:**
   Vespa allows you to setup private endpoints for exclusive access from your own, co-located VPCs.
   This requires less administrative overhead than general VPC peering and is also more secure.
   Refer to [private endpoints](https://cloud.vespa.ai/en/private-endpoints.html).
3. **Run Vespa workloads in your own account/project (Enclave):**
   The Vespa Enclave feature allows you to have all your Vespa workloads run in your own account.
   In this case, you can set up any required peering to open the connection into your application.
   While generally available, using Vespa Cloud Enclave requires significantly more effort
   from the application team in terms of operating the service,
   and is only recommended for larger applications that can justify the additional work
   from e.g., a security or interoperability perspective.
   Refer to [Vespa Enclave](https://cloud.vespa.ai/en/enclave/).
