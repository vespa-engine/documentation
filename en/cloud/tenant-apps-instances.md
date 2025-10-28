---
# Copyright Vespa.ai. All rights reserved.
title: Tenants, Applications and Instances
category: cloud
---

When registering for Vespa Cloud, a *tenant* is created.
Tenant is the billable unit, and most often represents an organization.
A tenant has one more more *applications* with one or more *instances*:

![A tenant can have multiple applications with multiple instances each](/assets/img/tenants-apps-instances.svg)

Instances are used for different use cases,
and are deployed to a set of [zones](https://cloud.vespa.ai/en/reference/zones) - example:

![An application can be deployed to multiple zones](/assets/img/instances-zones.svg)

The *Application* has a "default" instance serving queries from two *production* zones.
It has an "integration" instance with another dataset, used for other applications to interface a
production-like, stable interface.
Finally, a developer has deployed the "bob" instance to a *dev* zone to further develop plugin code.

Deployments to production zones are specified in [deployment.xml](https://cloud.vespa.ai/en/reference/deployment.html).
Deployments to manual zones like *dev* and *perf*
are normally done directly from a developer computer for rapid code and config development.
Read more in [Automated deployments](automated-deployments.html).

The service configuration is specified in [services.xml](https://cloud.vespa.ai/en/reference/services.html)
and is composed of individually sized *clusters*.
A cluster is deployed to a set of *nodes* with *resources* specified.

## Lifecycle

The tenant name cannot be changed - create a new tenant, or contact Vespa Support.

Tenants in trial are auto-expired once trial is completed.
Move to a paid plan to keep applications and data.

It is not possible to auto-migrate applications and data between tenants.
To move an application to a new tenant, re-deploy the application with the new tenant name,
see [cloning applications and data](cloning-applications-and-data).
