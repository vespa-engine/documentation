---
# Copyright Vespa.ai. All rights reserved.
title: "Developer Guide"
---

See [getting started](/en/getting-started.html) to deploy a basic sample application,
or its Java variant to deploy an application with custom Java components.

Keep reading for more details on how to develop applications, including basic terminology,
tips on using the Vespa Cloud Console, and how to benchmark and size your application.
[Automated deployments](/en/cloud/automated-deployments.html) makes production deployments safe and simple.

## Manual deployments

Developers will typically deploy their application to the `dev` [zone](https://cloud.vespa.ai/en/reference/zones)
during development. Each deployment is owned by a *tenant*, and each specified *instance* is
a separate copy of the application; this lets developers work on independent copies of the same application,
or collaborate on a shared one, as they prefer—more details [here](/en/cloud/tenant-apps-instances.html).
These values can be set in the Vespa Cloud UI when deploying, or with each of the build and deploy tools,
as shown in the respective getting-started guides.
Additionally, a deployment may specify a different [zone](https://cloud.vespa.ai/en/reference/zones) to deploy to, instead of the
default `dev` zone; see [performance testing](#performance-testing) below for how to do this.

### Auto downsizing

Deployments to `dev` are downscaled to one small node by default, so that
applications can be deployed there without changing `services.xml`.
If you need more resources in the `dev` application, set `nodes` or
`resources` explicitly by adding those tags to `services.xml` with
`deploy:environment="dev"`,
see [variants in services.xml](https://cloud.vespa.ai/en/reference/deployment-variants.html#services.xml-variants).

### Availability

The `dev` zone is a sandbox and not for production serving; It has no uptime guarantees.

An automated Vespa software upgrade can be triggered at any time,
and this may lead to some downtime if you have only one node per cluster
(as with the default [auto downsizing](#auto-downsizing)).

## Performance testing

In addition to `dev`, there is also a `perf` zone for performance testing.
Like production zones, this zone honors the resources specified in `services.xml`—see
[the reference](https://cloud.vespa.ai/en/reference/services) for how to configure them.
Performance and sizing tests can then be extrapolated to a production scenario.
In all other ways, this zone works the same way as `dev`.

To deploy to `perf` with Vespa CLI:

```
--zone perf.aws-us-east-1c
```

To deploy to `perf` with Maven:

```
-D environment=perf
```

Read more in [benchmarking](/en/cloud/benchmarking.html).

## Component overview

![Vespa Overview](/assets/img/vespa-overview.svg)

Application packages can contain Java components to be run in container clusters.
The most common component types are:
* [Searchers](searcher-development.html), which can modify or build the query,
  modify the result, implement workflows issuing multiple queries etc.
* [Document processors](document-processing.html) that can modify incoming write operations.
* [Handlers](jdisc/developing-request-handlers.html) that can implement custom web service APIs.
* [Renderers](result-rendering.html) that are used to define custom result formats.

Components are constructed by dependency injection and are reloaded safely on deployment without restarts.
See the [container documentation](jdisc/index.html) for more details.

See the sample applications in [getting started](getting-started.html),
to find examples of applications containing Java components.
Also see [troubleshooting](/en/operations-selfhosted/admin-procedures.html#troubleshooting).

## Developing Components

The development cycle consists of creating the component,
deploying the application package to Vespa, writing tests, and iterating.
These steps refer to files in
[album-recommendation-java](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation-java):

|  |  |  |
| --- | --- | --- |
| Build | All the Vespa sample applications use the [bundle plugin](components/bundles.html#maven-bundle-plugin) to build the components.   | |
| Configure | A key Vespa feature is code and configuration consistency, deployed using an [application package](application-packages.html). This ensures that code and configuration is in sync, and loaded atomically when deployed. This is done by generating config classes from config definition files. In Vespa and application code, configuration is therefore accessed through generated config classes.  The Maven target `generate-sources` (invoked by `mvn install`) uses [metal-names.def](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation-java/src/main/resources/configdefinitions/metal-names.def) to generate `target/generated-sources/vespa-configgen-plugin/com/mydomain/example/MetalNamesConfig.java`.  After generating config classes, they will resolve in tools like [IntelliJ IDEA](https://www.jetbrains.com/idea/download/).   | |
| Tests | Examples unit tests are found in [MetalSearcherTest.java](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation-java/src/test/java/ai/vespa/example/album/MetalSearcherTest.java). `testAddedOrTerm1` and `testAddedOrTerm2` illustrates two ways of doing the same test:   * The first setting up the minimal search chain for [YQL](query-language.html) programmatically * The second uses `com.yahoo.application.Application`, which sets up the application package and simplifies testing   Read more in [unit testing](unit-testing.html). |

## Debugging Components

{% include important.html content="The debugging procedure only works for endpoints with an open debug port -
most managed services don't do this for security reasons." %}

Vespa Cloud does not allow debugging over the *Java Debug Wire Protocol (JDWP)* due to the protocol's inherent lack of security measures.
If you need interactive debugging, deploy your application to a self-hosted Vespa installation (below)
and manually [add the *JDWP* agent to JVM options](/en/developer-guide.html#debugging-components).

You may debug your Java code by requesting either a JVM heap dump or a Java Flight Recorder recording through the
[Vespa Cloud Console](https://console.vespa-cloud.com/). Go to your application's cluster overview and select
*export JVM artifact* on any *container* node. The process will take up to a few minutes.
You'll find the steps to download the dump on the Console once it's completed.
Extract the files from the downloaded Zstandard-compressed archive, and use the free
[JDK Mission Control](https://www.oracle.com/java/technologies/jdk-mission-control.html) utility to inspect
the dump/recording.

![Generate JVM dump](/assets/img/jvm-dump.png)

To debug a [Searcher](searcher-development.html) /
[Document Processor](document-processing.html) /
[Component](jdisc/container-components.html) running in a self-hosted container,
set up a remote debugging configuration in the IDEA - IntelliJ example:

1. Run -> Edit Configurations...
2. Click `+` to add a new configuration.
3. Select the "Remote JVM Debug" option in the left-most pane.
4. Set hostname to the host running the container, change the port if needed.
5. Set the container's [jvm options](reference/services-container.html#jvm)
   to the value in "Command line arguments for remote JVM":

   ```
   <container id="default" version="1.0">
       <nodes>
           <jvm options="-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005" />
   ```
6. Re-deploy the application, then restart Vespa on the node that runs the container.
   Make sure the port is published if using a Docker/Podman container, e.g.:

   ```
   $ docker run --detach --name vespa --hostname vespa-container \
     --publish 127.0.0.1:8080:8080 --publish 127.0.0.1:19071:19071 --publish 127.0.0.1:5005:5005 \
     vespaengine/vespa
   ```
7. Start debugging! Check *vespa.log* for errors.

{% include video-include.html
image-url='/assets/img/video-thumbs/deploying-a-vespa-searcher.png'
video-url='https://www.youtube.com/embed/dUCLKtNchuE'
video-title='Debugging a Vespa Searcher' %}

## Developing system and staging tests

When using Vespa Cloud, system and tests are most easily developed using a test deployment in a
`dev` zone to run the tests against.
Refer to [general testing guide](/en/testing.html)
for a discussion of the different test types,
and the [basic HTTP tests](/en/reference/testing.html) or
[Java JUnit tests](/en/reference/testing-java.html) reference
for how to write the relevant tests.

If using the [Vespa CLI](/en/vespa-cli.html) to deploy and run
[basic HTTP tests](/en/reference/testing.html),
the same commands as in the test reference will just work,
provided the CLI is configured to use the `cloud` target.

### Running Java tests

With Maven, and [Java Junit tests](/en/reference/testing-java.html),
some additional configuration is required,
to infuse the test runtime on the local machine with API and data plane credentials:

```
$ mvn test \
  -D test.categories=system \
  -D dataPlaneKeyFile=data-plane-private-key.pem -D dataPlaneCertificateFile=data-plane-public-cert.pem \
  -D apiKey="$API_KEY"
```

The `apiKey` is used to fetch the *dev* instance's endpoints.
The data plane key and certificate pair is used by
[ai.vespa.hosted.cd.Endpoint](https://github.com/vespa-engine/vespa/blob/master/tenant-cd-api/src/main/java/ai/vespa/hosted/cd/Endpoint.java)
to access the application endpoint. See the [Vespa Cloud API reference](https://cloud.vespa.ai/en/reference/vespa-cloud-api)
for details on configuring Maven invocations. Note that the `-D vespa.test.config` argument is gone;
this configuration is automatically fetched from the Vespa Cloud API—hence the need for the API key.

When running Vespa self-hosted like in the
[sample application](/en/vespa-quick-start.html),
no authentication is required by default, to either API or container, and specifying a data plane key and certificate
will instead cause the test to fail, since the correct SSL context is the Java default in this case.

Make sure the TestRuntime is able to start.
As it will init an SSL context, make sure to remove config when running locally, in order to use a default context.
Remove properties from *pom.xml* and IDE debug configuration.

Developers can also set these parameters in the IDE run configuration to debug system tests:

```
-D test.categories=system
-D tenant=my_tenant
-D application=my_app
-D instance=my_instance
-D apiKeyFile=/path/to/myname.mytenant.pem
-D dataPlaneCertificateFile=data-plane-public-cert.pem
-D dataPlaneKeyFile=data-plane-private-key.pem
```

## Tips and troubleshooting
* Vespa Cloud upgrades daily, and applications in `dev` and `perf` also have their Vespa platform upgraded.
  This usually happens at the opposite time of day of when deployments are made to each instance, and takes some minutes.
  Deployments without redundancy will be unavailable during the upgrade.
* Failure to deploy, due to authentication (HTTP code 401) or authorization (HTTP code 403),
  is most often due to wrong configuration of `tenant` and/or `application`,
  when using command line tools to deploy. Ensure the values set with Vespa CLI or in `pom.xml`
  match what is configured in the UI. For Maven, also see [here](https://cloud.vespa.ai/en/reference/vespa-cloud-api) for details.
* In case of data plane failure,
  remember to copy the public certificate to `src/main/application/security/clients.pem`
  before building and deploying. This is handled by the Vespa CLI `vespa auth cert` command.
* To run Java [system and staging tests](/en/reference/testing-java.html) in an IDE,
  ensure all API and data plane keys and certificates are configured in the IDE as well;
  not all IDEs pick up all settings from `pom.xml` correctly:

  ```
  -Dtest.categories=system
  -DapiKeyFile=/path-to/tname.pem
  -DdataPlaneCertificateFile=/path-to/data-plane-public-cert.pem
  -DdataPlaneKeyFile=/path-to/data-plane-private-key.pem
  ```
