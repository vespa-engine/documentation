---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Deploy to Docker"
redirect_from:
- /documentation/pyvespa/deploy-vespa-docker.html
---
> Deploy Vespa applications to Docker containers.

## Install pyvespa


```python
!pip install pyvespa
```

## Define your application package

This tutorial assumes that a [Vespa application package](create-text-app.html)
was defined and stored in the variable `app_package`.
To illustrate this tutorial, we will use a basic question answering app from our gallery.


```python
from vespa.gallery import QuestionAnswering

app_package = QuestionAnswering()
```

## Docker requirement

This guide illustrates how to deploy a Vespa application to a Docker container in your local machine.
It is required to have Docker installed in the machine you are running this tutorial from.
For that reason we cannot run this tutorial in Google Colab,
as Docker is not available on their standard runtime machines.

## Deploy to a Docker container

Create a `VespaDocker` instance based on the application package.
Set the environment variable `WORK_DIR` to the absolute path of the desired working directory.


```python
import os
from vespa.deployment import VespaDocker

disk_folder = os.path.join(os.getenv("WORK_DIR"), "sample_application")
vespa_docker = VespaDocker(port=8089, disk_folder=disk_folder)
```

Call the `deploy` method.
Behind the scenes, `pyvespa` will write the Vespa config files and store them in the `disk_folder`,
it will then run a Vespa engine Docker container and deploy those config files in the container.


```python
app = vespa_docker.deploy(
    application_package = app_package,
)
```

That is it, you can now interact with your deployed application through the `app` instance.

## Clean up environment


```python
from shutil import rmtree

rmtree(disk_folder, ignore_errors=True)
vespa_docker.container.stop()
vespa_docker.container.remove()
```
