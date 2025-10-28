---
# Copyright Vespa.ai. All rights reserved.
title: Vespa testing
---

A system tests suite is an invaluable tool both when developing and maintaining a complex Vespa application.
These are functional tests which are run against a deployment of the application package to verify,
and use its HTTP APIs to execute feed and query operations which are compared to expected outcomes.
Vespa provides two formalizations of this:
* [Basic HTTP tests](reference/testing.html),
  expressing requests and expected responses as JSON,
  and run with the [Vespa CLI](vespa-cli.html).
* [Java JUnit tests](reference/testing-java.html), for more advanced tests,
  run as regular Java tests, with some extra configuration.

These two frameworks also includes an upgrade—or staging—test construct for scenarios where the application
is upgraded, and state in the backend depends on the old application configuration;
as well as a production verification test—basically a health check for production deployments.
For system and staging tests, the frameworks provide an easy way to perform HTTP request against a
designated test deployment, separating the tests from the deployment and configuration of the test clusters.

This document describes how each of these test categories can be run as part of an imagined
CI/CD system for safely deploying changes to a Vespa application in a continuous manner.

Finally, find a section on [A/B-testing / bucket tests](#feature-switches-and-bucket-tests)
using feature switches.

## System tests

System tests are just functional tests that verify a deployed Vespa application behaves as expected
when fed and queried. Running a system test is as simple as making a separate deployment with the
application package to test, and then running the system test suite, or one or a few or those tests.

{% include note.html content="Each system test should be self-contained,
i.e., it should be able to run each test in isolation; or all tests, in any order.
To achieve this, **system tests should generally start by clearing all documents from the cluster to test.**
This is the case with our sample system tests, so take care to not run them against a production cluster."%}

For the most part, system tests must be updated due to changes in the application package.
Rarely, an upgrade of the Vespa version may also lead to changed functionality, but within
major versions, this should only be new features and bug fixes. In any case, it is a good idea
to always run system tests against a dedicated test deployment—both before upgrading the Vespa
platform, and the application package—before deploying the change to production.

### Running system tests

The [Vespa CLI](vespa-cli.html) makes it easy to set up a test deployment, and run system and staging tests.
To run a system test, first set up a test deployment:

```
{% highlight sh %}
$ vespa deploy --wait 600
{% endhighlight %}
```

Run the basic HTTP tests (prefer using this test suite for regular tests) - also see the
[example](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/CI-CD/production-deployment-with-tests) application:

```
{% highlight sh %}
$ vespa test tests/system-test/feed-and-search-test.json
{% endhighlight %}
```

Example Java API tests (use for complex test cases) - also see the
[example](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/CI-CD/production-deployment-with-tests-java) application:

```
{% highlight sh %}
$ mvn test -D test.categories=system -D vespa.test.config=/path-to/test-config.json
{% endhighlight %}
```

The test config file used by the test runner in the maven-plugin defines the endpoints for each of the clusters in
[services.xml](reference/services.html) as fields under a `localEndpoints` JSON object:

```
{% highlight json %}
{
    "localEndpoints": {
        "query-service": "http://localhost:8080/",
        "feed-service" : "http://localhost:8081/"
    }
}
{% endhighlight %}
```

`feed-service` is the endpoint of the container cluster with `<document-api>`
in [services.xml](reference/services.html).
`query-service` is the endpoint of the container cluster with `<search>`
in [services.xml](reference/services.html).

## Staging tests

The goal of staging (upgrade) tests is *not* to ensure the new deployment
satisfies its functional specifications, as that should be covered by
system tests; rather, it is to ensure the upgrade of the application
package and/or Vespa platform does not break the application, and is
compatible with the behavior expected by existing clients.

As an example, consider a change in how documents are indexed, e.g., adding new document processor.
A system test would test verify this new behavior by feeding a document, and then verifying the
document processor modified the document, or perhaps did something else.
A staging test, on the other hand, would feed the document *before* the document processor was added,
and querying for the document after the upgrade could give different results
from what the system test would expect.

Many such changes, which require additional action post-deployment, are also guarded by
[validation overrides](reference/validation-overrides.html),
but the staging test is then a great way of figuring out what the exact consequences of the change are,
and how to deal with it.

As opposed to system tests, staging tests are not self-contained, as the state change during upgrade is
precisely what is tested. Instead, execution order of any staging tests that modify state, particularly
after upgrade, must be controlled. Indeed, some changes will require re-feeding data, and this should then be
part of the *staging test* code. Finally, it is also good to verify the expected state prior to upgrade.

The clients of a Vespa application should be compatible with both the system and staging test expectations,
and this dictates the workflow when deploying a breaking change - steps:

1. The application code and system and staging tests are updated, so tests pass;
   and clients are updated to reflect the updated test code.
2. The application is upgraded.
3. The *staging setup* code is updated to match the new application code.

Again, it is a good idea to always run staging tests before deployment of every change—be it a
change in the application package, or an upgrade of the Vespa platform.

### Running staging tests

See [system tests](#system-tests) above for links to example applications.
Steps:

1. A dedicated deployment is made with the *current* setup (package and Vespa version).
2. *staging setup* code is run to put the test cluster in a particular state—typically
   one that mimics the state in production clusters.
3. The deployment is then upgraded to the *new* setup (package and/or Vespa version).
4. *staging test* code is run to verify the cluster behaves as expected post-upgrade.

Example using JSON-tests:

```
{% highlight sh %}
# load old application code, deploy it, run setup
$ vespa deploy --wait 600
$ vespa test tests/staging-setup

# make changes to the application, deploy it, run tests
$ vespa deploy --wait 120
$ vespa test tests/staging-test
{% endhighlight %}
```

Example using Java tests (see [system tests](#running-system-tests) for *test-config.json*):

```
{% highlight sh %}
# load old application code, deploy it, run setup
$ vespa deploy --wait 600
$ mvn test -D test.categories=staging-setup -D vespa.test.config=/path-to/test-config.json

# make changes to the application, deploy it, run tests
$ vespa deploy --wait 120
$ mvn test -D test.categories=staging -D vespa.test.config=/path-to/test-config.json
{% endhighlight %}
```

## Feature switches and bucket tests

With continuous deployment, it is not practical to hold off releasing a feature until it is done,
test it manually until convinced it works and then release it to production.
What to do instead?
The answer is *feature switches*: release new features to production as they are developed,
but include logic which keeps them deactivated until they are ready,
or until they have been verified in production with a subset of users.
*Bucket tests* is the practice of systematically testing new features or behavior for a controlled subset of users.
This is common practice when releasing new science models,
as they are difficult to verify in test, but can also be used for other features.

To test new behavior in Vespa, use a combination of
[search chains](components/chained-components.html) and
[rank profiles](reference/schema-reference.html#rank-profile),
controlled by [query profiles](query-profiles.html),
where one query profile corresponds to one bucket.
These features support inheritance to make it easy to express variation without repetition.

Sometimes a new feature requires
[incompatible changes to a data field](reference/schema-reference.html#modifying-schemas).
To be able to CD such changes, it is necessary to create a new field containing the new version of the data.
This costs extra resources but less than the alternative: standing up a new system copy with the new data.
New fields can be added and populated while the system is live.

One way to reduce the need for incompatible changes can be decreased
by making the semantics of the fields more precise.
E.g., if a field is defined as the "quality" of a document, where a higher number means higher quality,
a new algorithm which produces a different range and distribution will typically be an incompatible change.
However, if the field is defined more precisely as the average time spent on the document once it is clicked,
then a new algorithm which produces better estimates of this value will not be an incompatible change.
Using precise semantics also have the advantage of making it easier to understand
if the use of the data and its statistical properties are reasonable.
