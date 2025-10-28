---
# Copyright Vespa.ai. All rights reserved.
title: "Application Package Reference"
category: oss,cloud
---

This is the [application package](../application-packages.html) reference.
An application package is the deployment unit in Vespa.
To deploy an application, create an application package
and [vespa deploy](/en/vespa-cli.html#deployment) or
use the [deploy API](deploy-rest-api-v2.html).
The application package is a directory of files and subdirectories:

| Directory/file | Required | Description |
| --- | --- | --- |
| [services.xml](services.html) | Yes | Describes which services to run where, and their main configuration. |
| [hosts.xml](hosts.html) | No | Vespa Cloud: Not used. See node counts in [services.xml](/en/reference/services).  Self-managed: The mapping from logical nodes to actual hosts. |
| [deployment.xml](/en/reference/deployment) | Yes, for Vespa Cloud | Specifies which environments and regions the application is deployed to during automated application deployment, as which application instances.  This file also specifies other deployment-related configurations like [cloud accounts](/en/cloud/enclave/enclave.html) and [private endpoints](/en/cloud/private-endpoints.html).  The file is required when deploying to the [prod environment](https://cloud.vespa.ai/en/reference/environments#production) - it is ignored (with some exceptions) when deploying to *dev* or *perf* environments. |
| [validation-overrides.xml](validation-overrides.html) | No | Override, allowing this package to deploy even if it fails validation. |
| [.vespaignore](vespaignore.html) | No | Contains a list of path patterns that should be excluded from the `application.zip` deployed to Vespa. |
| [models](stateless-model-reference.html)/ | No | Machine-learned models in the application package. Refer to [stateless model evaluation](../stateless-model-evaluation.html), [Tensorflow](../tensorflow.html), [Onnx](../onnx.html), [XGBoost](../xgboost.html), and [LightGBM](../lightgbm.html), also see [deploying remote models](../application-packages.html#deploying-remote-models) |
| [schemas](../schemas.html)/ | No | Contains the *.sd files describing the document types of the application and how they should be queried and processed. |
| [schemas/[schema]](schema-reference.html#rank-profile)/ | No | Contains *.profile files defining [rank profiles](../ranking.html#rank-profiles). This is an alternative to defining rank profiles inside the schema. |
| [security/clients.pem](/en/cloud/security/guide.html) | Yes, for Vespa Cloud | PEM encoded X.509 certificates for data plane access. See the [security guide](/en/cloud/security/guide.html) for how to generate and use. |
| [components](../jdisc/container-components.html)/ | No | Contains *.jar files containing searcher(s) for the JDisc Container. |
| [rules](semantic-rules.html)/ | No | Contains *.sr files containing rule bases for semantic recognition and translation of the query |
| [search/query-profiles](query-profile-reference.html)/ | No | Contains *.xml files containing a named set of search request parameters with values |
| [constants](../tensor-user-guide.html#constant-tensors)/ | No | Constant tensors |
| [tests](testing.html)/ | No | Test files for automated tests |
| ext/ | No | Files that are guaranteed to be ignored by Vespa: They are excluded when processing the application package and cannot be referenced from any other element in it. |

Additional files and directories can be placed anywhere in the application package.
These will be not be processed explicitly by Vespa when deploying the application package
(i.e. they will only be considered if they are referred to from within the application package),
but there is no guarantee to how these might be processed in a future release.
To extend the application package in a way that is guaranteed
to be ignored by Vespa in all future releases, use the *ext/* directory.

## Deploy

| Command | Description |
| --- | --- |
| upload | Uploads an application package to the config server. Normally not used, as *prepare* includes *upload* |
| prepare | 1. Verifies that a configuration server is up and running 2. Uploads the application to the configuration server, which stores it in    *$VESPA_HOME/var/db/vespa/config_server/serverdb/tenants/default/sessions/[sessionid]*.    *[sessionid]* increases for each *prepare*-call.    The config server also stores the application in a    [ZooKeeper](/en/operations-selfhosted/configuration-server.html)    instance at */config/v2/tenants/default/sessions/[sessionid]* -    this distributes the application to all config servers 3. Creates metadata about the deployed the applications package (which user deployed it,    which directory was it deployed from and at what time was it deployed) and stores it in    *...sessions/[sessionid]/.applicationMetaData* 4. Verifies that the application package contains the required files and performs a consistency check 5. Validates the xml config files using the    [schema](https://github.com/vespa-engine/vespa/tree/master/config-model/src/main/resources/schema),    found in *$VESPA_HOME/share/vespa/schema* 6. Checks if there are config changes between the active application and this prepared application    that require actions like restart or re-feed (like changes to    [schemas](../schemas.html)).    These actions are returned as part of the prepare step in the    [deployment API](deploy-rest-api-v2.html#prepare-session).    This prevents breaking changes to production - also read about    [validation overrides](validation-overrides.html) 7. Distributes constant tensors and bundles with [components](../jdisc/container-components.html)    to nodes using [file distribution](../application-packages.html#file-distribution).    Files are downloaded to *$VESPA_HOME/var/db/vespa/filedistribution*,    URL download starts downloading to *$VESPA_HOME/var/db/vespa/download* |
| activate | 1. Waits for prepare to complete 2. Activates new configuration version 3. Signals to containers to load new bundles -    read more in [container components](../jdisc/container-components.html) |
| fetch | Use *fetch* to download the active application package |

An application package can be zipped for deployment:

```
$ zip -r ../app.zip .
```

Use any name for the zip file - then refer to the file instead of the path in [deploy](/en/vespa-cli.html#deployment) commands.

{% include important.html content='Using `tar` / `gzip` is not supported.
[Details](https://github.com/vespa-engine/vespa/issues/17837).'%}

## Preprocess directives

Use preprocess directives to:
* *preprocess:properties*:
  define properties that one can refer to everywhere in *services.xml*
* *preprocess:include*:
  split *services.xml* in smaller chunks

Below, *${container.port}* is replaced by *4099*.
The contents of *content.xml* is placed at the *include* point.
This is applied recursively, one can use preprocess directives in included files,
as long as namespaces are defined in the top level file:

```
<services version="1.0" xmlns:preprocess="properties">
    <preprocess:properties>
        <container.port>4099</container.port>
    </preprocess:properties>
    <container version="1.0">
        <http>
            <server id="container" port="${container.port}" />
        </http>
        <search />
    </container>
    <preprocess:include file="content.xml" />
</services>
```

Sample *content.xml*:

```
<content version="1.0" >
    <redundancy>1</redundancy>
    <documents>
        <document type="music.sd" mode="index" />
    </documents>
    <nodes>
        <node hostalias="node0"/>
        <node hostalias="node1"/>
        <node hostalias="node2"/>
    </nodes>
</content>
```

## Versioning application packages

An application can be given a user-defined version, available at
[/ApplicationStatus](../jdisc/container-components.html#monitoring-the-active-application).
Configure the version in [services.xml](services.html) (at top level):

```
<services>
    <config name="container.handler.observability.application-userdata">
        <version>42</version>
    </config>
    ...
</services>
```
