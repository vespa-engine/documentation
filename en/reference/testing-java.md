---
# Copyright Vespa.ai. All rights reserved.
title: Testing with Java JUnit tests
---

This is the Vespa Testing reference for [Vespa application system tests](../testing.html)
written in Java, as JUnit 5 unit test.

These tests verify the behaviour of a Vespa application by using its HTTP interfaces.
To write tests without Java, see [basic HTTP test reference](testing.html).

See the [testing guide](../testing.html) for examples of how to run the tests.

## Test suites

The [testing documentation](../testing.html) defines three test scenarios,
comprised of four test code categories. The *system test framework* in
[com.yahoo.vespa:tenant-cd-api](https://search.maven.org/artifact/com.yahoo.vespa/tenant-cd-api)
uses Java annotations to declare what category a JUnit test class belongs to.
To run tests with Maven belonging to a specific category, a JUnit 5 test *tag* must be specified:

```
{% highlight sh %}
$ mvn test -D test.categories=system -D vespa.test.config=/path-to/test-config.json
{% endhighlight %}
```

| Category | Annotation | JUnit tag | Description |
| --- | --- | --- | --- |
| System test | @SystemTest | system | Independent, functional tests |
| Staging setup | @StagingSetup | staging-setup | Set state before upgrade |
| Staging test | @StagingTest | staging | Verify state after upgrade |
| Production test | @ProductionTest | production | Verify domain specific metrics |

For an example including system and staging tests, check out the
[sample application test suite](https://github.com/vespa-cloud/examples/tree/main/CI-CD/production-deployment-with-tests-java).

## TestNG

Combining Vespa JUnit 5 test suites with unit tests in TestNG is possible. You'll need to explicitly configure
Maven's surefire plugin to enable integration for both frameworks. To execute the Vespa test suites specify
`-D test.categories=[tag]`, where *[tag]* is one of the values listed in [Test suites](#test-suites).

```
{% highlight xml %}

    org.apache.maven.plugins
    maven-surefire-plugin


            org.apache.maven.surefire
            surefire-junit-platform
            ${surefire.vespa.tenant.version}


            org.apache.maven.surefire
            surefire-testng
            ${surefire.vespa.tenant.version}



{% endhighlight %}
```
