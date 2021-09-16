---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Deploy to Vespa Cloud"
---
> How to host a Vespa application on the cloud

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vespa-engine/documentation/blob/master/en/pyvespa/deploy-vespa-cloud.ipynb)

## Install pyvespa

```python
pip install pyvespa
```

## Define application package

This tutorial assumes that a [Vespa application package](create-text-app.html) was defined and stored in the variable `app_package`. To illustrate this tutorial, we will use a basic question answering app from our gallery.

```python
from vespa.gallery import QuestionAnswering

app_package = QuestionAnswering()
```

## Setup your Vespa Cloud account

1. Sign-in or sign-up:
  * To deploy `app_package` on Vespa Cloud, you need to [login into your account](https://cloud.vespa.ai/) first. You can create one and give it a try for free.
2. Choose a tenant:
  *  You either create a new tenant or use an existing one. That will be the `TENANT_NAME` env variable in the example below. 
3. Get your user key:
  * Once you are on your chosen tenant dashboard, you can generate and download a user key under the key tab. Set the `USER_KEY` env variable to be the path to the downloaded user key. 
4. Create a new application under your tenant
  * Within the tenant dashboard, you can also create a new application associated with that tenant and set the `APPLICATION_NAME` env variable below to the name of the application. 
  
That is all that needs to be setup on the Vespa Cloud dashboard before deployment.

## Create a VespaCloud instance

```python
from vespa.deployment import VespaCloud

vespa_cloud = VespaCloud(
    tenant=os.getenv("TENANT_NAME"),
    application=os.getenv("APPLICATION_NAME"),
    key_location=os.getenv("USER_KEY"),
    application_package=app_package,
)
```

## Deploy to the Cloud

We can have multiple instances of the same application, we can then chose a valid `INSTANCE_NAME` to identify the instance created here and set the `DISK_FOLDER` to a local path to hold deployment related files such as certifications and Vespa config files.


```python
app = vespa_cloud.deploy(
    instance=os.getenv("INSTANCE_NAME"), disk_folder=os.getenv("DISK_FOLDER")
)
```

That is it, you can now interact with your deployed application through the `app` instance.
