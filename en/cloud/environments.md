---
# Copyright Vespa.ai. All rights reserved.
title: Environments
category: cloud
---

Vespa Cloud has two kinds of environments:
* Manual environments for rapid development and test: `dev` and `perf`
* Automated environment with integrated CD pipeline: `prod`

An application is deployed to one or more *zones* (see [zone list](/en/cloud/zones.html)),
which is a combination of an *environment* and a *region*, like
`vespa deploy -z perf.aws-us-east-1c`.

## Dev

The dev environment is built for rapid developments cycles,
with auto-downscaling and auto-expiry for ease of use and cost control.
The dev environment is the default, to deploy to this, use `vespa deploy`

### Auto downscaling

One use case for the dev environment is to take an application package from a prod environment
and deploy to the dev environment to debug.
To minimize cost and make this speedy,
Vespa Cloud will by default ignore [nodes](/en/reference/services.html#nodes) and
[resources](/en/reference/services.html#resources) settings.

With this, you can safely download an application package from prod (that are normally large) and deploy to dev, with no changes.

To override this behavior and control the resources,
specify them explicitly for the dev environment
as described in [deployment variants](/en/reference/deployment-variants.html#services.xml-variants).
Example:

```
{% highlight xml %}





>
{% endhighlight %}
```

{% include important.html content='The `dev` environment has redundancy 1 by default,
and there are no availability or data persistence guarantees.
Do not use applications deployed to these zones for production serving use cases.' %}

### Auto expiry

Deployments to `dev` expire after 14 days of inactivity,
that is, 14 days after the last [deployment](/en/application-packages.html#deploy).
**This applies to all plans**.
To add 7 more days to the expiry period, redeploy the application or use the Vespa Cloud Console.

### Vespa version

The latest active Vespa version is used when deploying to the dev environment.
The deployment is upgraded at a time which is most likely at night for the developer in order to minimize downtime
(based on the time when last deployments were made).
An upgrade will be skipped if metrics indicate ongoing feed or query load,
but will still be done if current version is more than a week old.

## Perf

The `perf` environment is for benchmarking.

All settings that apply to the dev environment also applies to perf, with one important difference:
In the dev environment, there are no resource isolation guarantees, so benchmarking in dev is of no use.

In perf, you will deploy with `nodes` and `resources` settings to find capacity and latency numbers.
To deploy to the perf environment, use `vespa deploy -z perf.aws-us-east-1c`.

## Prod

Applications are deployed to the `prod` environment for production serving.
Deployments are passed through an integrated CD pipeline for system tests and staging tests.
Read more in [automated deployments](/en/cloud/automated-deployments.html).

## Test

The `test` environment is used by the integrated CD pipeline for prod deployments,
to run [system tests](/en/cloud/automated-deployments.html#system-tests).
The test capacity is ephemeral and only used during test.
Nodes in test and staging environments do not have access to data in prod environments.

Note that one cannot deploy directly to test and staging environments.
For long-lived test applications (e.g., a QA system that is integrated with other services) use the prod environment.

System tests are always invoked, even if there are no tests defined.
In this case, an instance is just started and then stopped.
This has value in itself, as it ensures that the application is able to start.

Test runs can be [aborted](/en/cloud/automated-deployments.html#disabling-tests).

## Staging

See system tests above, this applies to the staging, too.
[Staging tests](/en/cloud/automated-deployments.html#staging-tests)
use a fraction of the configured prod capacity, this can be overridden to using 1 node regardless of prod cluster size:

```
{% highlight xml %}





{% endhighlight %}
```

## Reference

Environment settings:

| Name | Description | Expiry | Cluster sizes |
| --- | --- | --- | --- |
| `dev` | Used for manual development testing. | 14 days | `1` |
| `perf` | Used for manual performance testing. | 14 days | `min(3, spec)` |
| `test` | Used for [automated system tests](/en/testing.html#system-tests). | - | `1` |
| `staging` | Used for [automated staging tests](/en/testing.html#staging-tests). | - | `min(max(2, 0.05 * spec), spec)` |
| `prod` | Hosts all production deployments. | No expiry | `max(2, spec)` |
