---
# Copyright Vespa.ai. All rights reserved.
title: "Instance, region, cloud and environment variants"
category: cloud
---

Sometimes it is useful to create configuration that varies depending on properties of the deployment,
for example to set region specific endpoints of services used by [Searchers](/en/searcher-development.html),
or use smaller clusters for a "beta" instance.

This is supported both for [services.xml](#services.xml-variants) and
[query profiles](#query-profile-variants).

## services.xml variants

[services.xml](services.html) files support different configuration settings
for different *tags*, *instances*, *environments*, *clouds* and *regions*.
To use this, import the *deploy* namespace:

```
{% highlight xml %}

{% endhighlight %}
```

Deploy directives are used to specify with which tags, and in which instance, environment,
cloud and/or [region](https://cloud.vespa.ai/en/reference/zones) an XML element should be included:

```
{% highlight xml %}

    2
















{% endhighlight %}
```

The example above configures different node counts/configurations depending on the deployment target.
Deploying the application in the *dev* environment gives:

```
{% highlight xml %}

    2





{% endhighlight %}
```

Whereas in `aws-us-west-2a` it is:

```
{% highlight xml %}

    2







{% endhighlight %}
```

This can be used to modify any config by deployment target.

The `deploy` directives have a set of override rules:
* A directive specifying more conditions will override one specifying fewer.
* Directives are inherited in child elements.
* When multiple XML elements with the same name is specified
  (e.g. when specifying search or docproc chains),
  the *id* attribute or the *idref* attribute of the element
  is used together with the element name when applying directives.

Some overrides are applied by default in some environments,
see [environments](https://cloud.vespa.ai/en/reference/environments).
Any override made explicitly for an environment will override the defaults for it.

### Specifying multiple targets

More than one tag, instance, region or environment can be specified in the attribute, separated by space.

Note that `tags` by default only apply in production instances,
and are matched whenever the tags of the element and the tags of the instance intersect.
To match tags in other environments,
an explicit `deploy:environment` directive for that environment must also match.
Use tags if you have a complex instance structure which you want config to vary by.

The namespace can be applied to any element. Example:

```
{% highlight xml %}





                    Hello from application config
                    Hello from east colo!





{% endhighlight %}
```

Above, the `container` element is configured for the 4 environments only (it will not apply to `dev`) -
and in region `aws-us-east-1c`, the config is different.

## Query profile variants

[Query profiles](/en/query-profiles.html) support different configuration settings
for different *instances*, *environments* and *regions* through
[query profile variants](/en/query-profiles.html#query-profile-variants).
This allows you to set different query parameters for a query type depending on these deployment attributes.

To use this feature, create a regular query profile variant with any of
`instance`, `environment` and `region` as dimension names and
let your query profile vary by that. For example:

```
{% highlight xml %}

    instance, environment, region

    My default value



        My beta value




        My dev value




        My main instance prod value


{% endhighlight %}
```

You can pick and combine these dimensions in any way you want with other dimensions sent as query parameters, e.g:

```
{% highlight xml %}
    device, instance, usecase
{% endhighlight %}
```
