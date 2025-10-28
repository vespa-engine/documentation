---
# Copyright Vespa.ai. All rights reserved.
title: "Using Libraries for Pluggable Frameworks"
---

Many libraries provide pluggable architectures via Service Provider Interfaces (SPI).
Using such libraries usually requires some manual setup in the application package.

## Troubleshooting and Configuring the Application

Libraries for pluggable frameworks rely on loading classes dynamically at runtime,
usually via `Class.forName("…")`.
If the package of the class that is loaded is not imported by our user bundle,
this will result in the following error:

```
java.lang.ClassNotFoundException: com.sun.imageio.plugins.jpeg.JPEGImageReaderSpi not found by my-bundle [29]
    at
org.apache.felix.framework.BundleWiringImpl.findClassOrResourceByDelegation(BundleWiringImpl.java:1532)
```

The example above is from using the
[Image I/O framework](https://docs.oracle.com/javase/6/docs/technotes/guides/imageio/).
In this case, notice that the missing class is from a `com.sun` package,
which is available in the SDK.

### Importing the Missing Package

The `ClassNotFoundException` means that the bundle is not importing the package.
The [bundle-plugin](../components/bundles.html#maven-bundle-plugin) will usually not have added an import
since the class is only referred to from a string in a `Class.forName("…")` statement.
Hence, add an explicit `importPackage` in the bundle's pom.xml:

```
<build>
    <plugins>
        <plugin>
          <groupId>com.yahoo.vespa</groupId>
          <artifactId>bundle-plugin</artifactId>
          ...
          <configuration>
              <importPackage>com.sun.imageio.plugins.jpeg</importPackage>
              ...
          </configuration>
        </plugin>
    </plugins>
</build>
```

The `importPackage` configuration option takes a comma-separated list of packages.
Adding multiple `importPackage` elements in pom.xml means that only one of them will take effect.

### Exporting the Missing Package from the Container

As mentioned, the missing package in this example is part of the SDK.
In these cases, we must tell the Container to export the missing package.
When running in [cluster mode](/en/operations-selfhosted/multinode-systems.html#aws-ecs),
this is done in `services.xml`:

```
<container version="1.0">
    <config name="search.config.qr-start">
        <jdisc>
            <export_packages>com.sun.imageio.plugins.jpeg</export_packages>
        </jdisc>
    </config>
    ...
</container>
```
