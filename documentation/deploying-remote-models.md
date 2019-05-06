---
# Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Deploying remote models"
---

Machine learned models in Vespa, either [TensorFlow](tensorflow.html), [ONNX](onnx.html), or [XGBoost](xgboost.html),
are expected to be put in the application package under the `models` directory.
This might be inconvenient for some applications, for instance for models that are frequently retrained on some remote system.
Additionally, some models might be too large to fit within the constraints of the version control system.

The solution is to download the models from the remote location during the application package build.
This is simply implemented by adding a step in the `pom.xml` of the Vespa application:

```
<build>
  <plugins>
    <plugin>
      <groupId>org.codehaus.mojo</groupId>
      <artifactId>exec-maven-plugin</artifactId>
      <version>1.4.0</version>
      <executions>
        <execution>
          <id>download-model</id>
          <phase>generate-resources</phase>
          <goals>
            <goal>exec</goal>
          </goals>
          <configuration>
            <executable>bin/download_models.sh</executable>
            <arguments>
              <argument>target/application/models</argument>
              <argument>MODEL-URL</argument>
            </arguments>
          </configuration>
        </execution>
      </executions>
    </plugin>
  </plugins>
</build>
```

A simplistic example of `bin/download_model.sh` is:

```
#!/bin/bash

DIR="$1"
URL="$2"

echo "[INFO] Downloading $URL into $DIR"

mkdir -p $DIR
pushd $DIR
    curl -O $URL
popd

```

Any necessary credentials for authentication and authorization should be added to this script,
as well as any unpacking of archives (for TensorFlow models for instance).

To automatically deploy periodically trained models,
the model training pipeline could trigger the Vespa CD system for a full application rebuild and deployment.
One should probably set up some form of staging environment to test the model before deploying to production.

