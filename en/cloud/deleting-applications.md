---
# Copyright Verizon Media. All rights reserved.
title: Deleting Applications
---

{% include warning.html content='Following these steps will remove production instances or regions and all data within them.
Data will be unrecoverable.' %}



## Deleting an application
To delete an application, use the console:
* navigate to the *application* view at
http://console.vespa.ai/tenant/tenant-name/application where you can find the trash 
can icon to the far right, as an `ACTION`.
* navigate to the *deploy* view at
*http://console.vespa.ai/tenant/tenant-name/application/app-name/prod/deploy*.

![delete production deployment](/assets/img/console/delete-production-deployment.png)

When the application deployments are deleted,
delete the application in the [console](http://console.vespa.ai).
Remove the CI job that builds and deploys application packages, if any.



## Deleting an instance / region
To remove an instance or a deployment to a region from an application:

1. Remove the `region` from `prod`, or the `instance` from `deployment`
   in [deployment.xml](https://cloud.vespa.ai/en/reference/deployment#instance):

    ```xml
    <deployment version="1.0">
        <prod>
            <region>aws-us-east-1c</region>
            <!-- Removing the deployment in the region 'aws-eu-west-1a' -->
            <!--region>aws-eu-west-1a</region-->
        </prod>
    </deployment>
    ```

2.  Add or modify [validation-overrides.xml](https://docs.vespa.ai/en/reference/validation-overrides.html),
    allowing Vespa Cloud to remove production instances:

    ```xml
    <validation-overrides>
        <allow until="2021-03-01" comment="Remove region/instance ...">deployment-removal</allow>
        <!-- If the region was part of a global endpoint/instance had a global endpoint: -->
        <allow until="2021-03-01" comment="Remove region/instance ...">global-endpoint-change</allow>
    </validation-overrides>
    ```

3. Build and deploy the application package.
