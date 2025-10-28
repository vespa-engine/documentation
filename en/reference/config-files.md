---
# Copyright Vespa.ai. All rights reserved.
title: "Custom Configuration File Reference"
---

This is the reference for config file definitions.
It is useful for developing applications that has
[configurable components](../configuring-components.html)
for the [Vespa Container](../jdisc/index.html),
where configuration for individual components may be provided by defining
[`<config>`](#generic-configuration-in-services-xml)
elements within the component's scope in services.xml.

## Config definition files

Config definition files are part of the source code of your application and have a *.def* suffix.
Each file defines and documents the content and semantics of one configuration type.
Vespa's builtin *.def* files are found in
`$VESPA_HOME/share/vespa/configdefinitions/`.

### Package

Package is a mandatory statement that is used to define the package for the java class generated to represent
the file. For [container component](../jdisc/container-components.html) developers,
it is recommended to use a separate package for each bundle that needs to export config classes,
to avoid conflicts between bundles that contain configurable components.
Package must be the first non-comment line, and can only contain lower-case characters and dots:

```
package=com.mydomain.mypackage
```

### Parameter names

Config definition files contain lines on the form:

```
parameterName type [default=value] [range=[min,max]]
```

camelCase in parameter names is recommended for readability.

### Parameter types

Supported types for variables in the *.def* file:

|  |  |
| --- | --- |
| int | 32 bit signed integer value |
| long | 64 bit signed integer value |
| double | 64 bit IEEE float value |
| enum | Enumerated types. A set of strings representing the valid values for the parameter, e.g:   ```       foo enum {BAR, BAZ, QUUX} default=BAR ``` |
| bool | A boolean (true/false) value |
| string | A String value. Default values must be enclosed in quotation marks (" "), and any internal quotation marks must be escaped by backslash. Likewise, newlines must be escaped to `\n` |
| path | A path to a physical file or directory in the application package. This makes it possible to access files from the application package in container components. The path is relative to the root of the [application package](../application-packages.html). A path parameter cannot have a default value, but may be optional (using the *optional* keyword after the type). An optional path does not have to be set, in which case it will be an empty value. The content will be available as a `java.nio.file.Path` instance when the component accessing this config is constructed, or an `Optional<Path>` if the *optional* keyword is used. |
| url | Similar to `path`, an arbitrary URL of a file that should be downloaded and made available to container components. The file content will be available as a java.io.File instance when the component accessing this config is constructed. Note that if the file takes a long time to download, it will also take a long time for the container to come up with the configuration referencing it. See also the [note about changing contents for such an url](../configuring-components.html#adding-files-to-the-component-configuration). |
| model | A pointer to a machine-learned model. This can be a model-id, url or path, and multiple of these can be specified as a single config value, where one is used depending on the deployment environment:   * If a model-id is specified and the application is deployed on Vespa Cloud, the model-id is used.* Otherwise, if a URL is specified, it is used.* Otherwise, path is used.   You may also use remote URLs protected by bearer-token authentication by supplying the optional `secret-ref` attribute. See [using private Huggingface models](../reference/embedding-reference#private-model-hub). On the receiving side, this config value is simply represented as a file path regardless of how it is resolved. This makes it easy to refer to models in multiple ways such that the appropriate one is used depending on the context. The special syntax for setting these config values is documented in [adding files to the configuration](../configuring-components.html#adding-files-to-the-component-configuration). |
| reference | A config id to another configuration (only for internal vespa usage) |

### Structs

Structs are used to group a number of parameters that naturally belong together.
A struct is declared by adding a '.' between the struct name and each member's name:

```
basicStruct.foo string
basicStruct.bar int
```

### Arrays

Arrays are declared by appending square brackets to the parameter name.
Arrays can either contain simple values, or have children.
Children can be simple parameters and/or structs and/or other arrays.
Arbitrarily complex structures can be built to any depth. Examples:

```
intArr[] int                        # Integer value array
row[].column[] int                  # Array of integer value arrays
complexArr[].foo string             # Complex array that contains
complexArr[].bar double             # … two simple parameters
complexArr[].coord.x int            # … and a struct called 'coord'
complexArr[].coord.y int
complexArr[].coord.depths[] double  # … that contains a double array
```

Note that arrays cannot have default values, even for simple value arrays.
An array that has children cannot contain simple values, and vice versa.
In the example above, `intArr` and `row.column` could not have children,
while `row` and `complexArr` are not allowed to contain values.

### Maps

Maps are declared by appending curly brackets to the parameter name.
Arbitrarily complex structures are supported also here. Examples:

```
myMap{} int
complexMap{}.nestedMap{}.id int
complexMap{}.nestedMap{}.name string
```

## Generic configuration in services.xml

`services.xml`has four types of elements:

|  |  |
| --- | --- |
| individual service elements | (e.g. *searcher*, *handler*, *searchnode*) - creates a service, but has no child elements that create services |
| service group elements | (e.g. *content*, *container*, *document-processing* - creates a group of services and can have all types of child elements |
| dedicated config elements | (e.g. *accesslog*) - configures a service or a group of services and can only have other dedicated config elements as children |
| generic config elements | always named *config* |

Generic config elements can be added to most elements that lead to one or
more services being created - i.e. service group elements and individual service elements.
The config is then applied to all services created by that element and all descendant elements.

For example, by adding *config* for *container*,
the config will be applied to all container components in that cluster.
Config at a deeper level has priority,
so this config can be overridden for individual components
by setting the same config values in e.g. *handler* or *server* elements.

Given the following config definition, let's say its name is `type-examples.def`:

```
package=com.mydomain

stringVal string
myArray[].name string
myArray[].type enum {T1, T2, T3} default=T1
myArray[].intArr[] int
myMap{} string
basicStruct.foo string
basicStruct.bar int default=0 range=[-100,100]
boolVal bool
myFile path
myUrl url
myOptionalPath path optional
```

To set all the values for this config in `services.xml`,
add the following xml at the desired element (the name should be *<package>.<config definition file name>*):

```
<config name="com.mydomain.type-examples">
  <stringVal>val</stringVal>
  <myArray>
    <item>
      <name>elem_0</name>
      <type>T2</type>
      <intArr>
        <item>0</item>
        <item>1</item>
      </intArr>
    </item>
    <item>
      <name>elem_1</name>
      <type>T3</type>
      <intArr>
        <item>0</item>
        <item>1</item>
      </intArr>
    </item>
  </myArray>
  <myMap>
    <item key="key1">val1</item>
    <item key="key2">val2</item>
  </myMap>
  <basicStruct>
    <foo>str</foo>
    <bar>3</bar>
  </basicStruct>
  <boolVal>true</boolVal>
  <myFile>components/file1.txt</myFile>
  <myUrl>https://docs.vespa.ai/en/reference/query-api-reference.html</myUrl>
</config>
```

Note that each '.' in the parameter's definition corresponds to a child element in the xml.
It is not necessary to set values that already have a default in the *.def* file,
if you want to keep the default value.
Hence, in the example above, `basicStruct.bar` and `myArray[].type`
could have been omitted in the xml without generating any errors when deploying the application.

### Configuring arrays

Assigning values to *arrays* is done by using the `<item>` element.
This ensures that the given config values do not overwrite any existing array elements
from higher-level xml elements in services, or from Vespa itself.
