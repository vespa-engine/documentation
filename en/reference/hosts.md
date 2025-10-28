---
# Copyright Vespa.ai. All rights reserved.
title: "hosts.xml"
category: oss
---

*hosts.xml* is a configuration file in an
[application package](../application-packages.html). Elements:

```
hosts
    host [name]
        alias
```

The purpose of *hosts.xml* is to add aliases for real hostnames to self-defined aliases.
The aliases are used in [services.xml](services.html) to map service instances to hosts.
It is only needed when deploying to multiple hosts.

## host

Sub-elements:
* [`alias`](#alias)

Example:

```
{% highlight xml %}


        SEARCH0
        CONTAINER0


        SEARCH1
        CONTAINER1


{% endhighlight %}
```

## alias

Alias used in [services.xml](services.html) to refer to the host.
