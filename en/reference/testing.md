---
# Copyright Vespa.ai. All rights reserved.
title: Basic HTTP testing
---

This is the Vespa Testing reference for basic HTTP tests, used to write
[Vespa application system tests](../testing.html).

These tests verify the behaviour of a Vespa application by using its HTTP interfaces.
Basic HTTP tests are written in JSON; to write more advanced tests, see
the [Java testing reference](testing-java.html).

See the [testing guide](../testing.html) for examples of how to run the tests.

## Test suites

The [testing documentation](../testing.html) defines three test scenarios,
comprised of four test code categories. For basic HTTP tests, the category of a test is defined
by its placement in the application tests directory:

| Category | Directory | Description |
| --- | --- | --- |
| System test | tests/system-test/ | Independent, functional tests |
| Staging setup | tests/staging-setup/ | Set state before upgrade |
| Staging test | tests/staging-test/ | Verify state after upgrade |
| Production test | tests/production-test/ | Verify domain specific metrics |

{% include note.html content="If the application package has Java code,
the `tests` directory is `src/test/application/tests`"%}

Each test is described by a JSON file, and may include other files using relative paths:

```
$ ls -1 tests/*/*

tests/production-test/metrics-test.json
tests/staging-setup/set-up-old-documents.json
tests/staging-test/verify-search-still-works.json
tests/system-test/data/document.json
tests/system-test/feed-and-search-test.json
tests/system-test/ranking-test.json
```

For an example with actual system and staging tests, check out a Vespa Cloud
[sample test suite](https://github.com/vespa-cloud/examples/tree/main/CI-CD/production-deployment-with-tests/tests).
Since production tests are highly application specific, this suite has none, but such a test could be:

```
{% highlight json %}
{
    "steps": [
        {
            "request": {
                "uri": "https://my.external.service/metrics/?query=customer-engagement"
            }
        }
    ]
}
{% endhighlight %}
```

## Test file structure

Each `.json` file directly under any of the directories listed above describes one test.
Each test consists of a series of steps, and each step specifies an HTTP request to run,
and some assertions about the response to obtain.
Some additional properties may also be specified on both the test and step levels.
A full example, with `//` comments:

```
{
    "name": "my test",
    "defaults": {
        "cluster": "default",
        "parameters": {
            "timeout": "1.618s"
        }
    },
    "steps": [
        {
            "name": "clear existing documents",
            "request": {
                "method": "DELETE",
                "uri": "/document/v1/",
                "parameters": {
                    "cluster": "music",
                    "selection": "true"
                }
            }
        },
        {
            "name": "feed foo",
            "request": {
                "method": "POST",
                // should contain payload as expected by /document/v1/
                "body": "foo/body.json",
                // specify only the path and query for Vespa requests
                "uri": "/document/v1/test/music/docid/foo?timeout=8s",
                // JSON object file; merged with query from "uri"
                "parameters": "foo/parameters.json"
            }
            // no response spec: just assert code 200
        },
        {
            "name": "query for foo",
            "request": {
                // no "uri": defaults to "/search/"
                "parameters": {
                    "query": "artist: foo"
                }
            },
            "response": {
                "body": {
                    "root": {
                        "children": [
                            // assert "children" has a single element ...
                            {
                                // ... which has the field "fields" ...
                                "fields": {
                                    // ... where the field "artist" is "Foo Fighters" ...
                                    "artist": "Foo Fighters"
                                },
                                // ... and the field "relevance" close to 0.381862383599
                                "relevance": 0.381862383599
                            }
                        ]
                    }
                }
            }
        }
    ]
}
```

### Test JSON specification

A full list of fields, with description:

| Name | Parent | Type | Default | Description |
| --- | --- | --- | --- | --- |
| name | root step | string | file name, step *n* | Name used for display purposes in the test report. The file name is used by default for the test, while the 1-indexed "step n" is used for steps. |
| defaults | root | object |  | Default settings for all steps in this test. May be overridden in each step. |
| steps | root | array |  | The non-empty list of steps that constitute this test. |
| request | step | object |  | A specification of a request to send, to Vespa, or to an external service. |
| cluster | defaults request | string |  | The name of the Vespa cluster to send a request to, as specified in [services.xml](services.html). If this is not specified, and the application has a single container cluster, this is used. |
| method | request | string | "GET" | The HTTP method to use for a request. |
| uri | request | string | "/search/" | When this is path + (encoded) query, the host is determined by the specified cluster; otherwise, it must be an absolute URI (with scheme), and its host is used. Query parameters specified here override those specified in the defaults. |
| parameters | defaults request | string object |  | HTTP request query parameters. The values should not be encoded. These are merged with parameters from the specified URI, and override those specified in the defaults. If the value is a string, it must be a relative file reference to a parameters object. |
| body | request response | string object |  | The body for a request, or the partial body (see [matching](#json-matching)) for a response. If the value is a string, it must be a relative file reference to a JSON object to be used in its place. |
| response | step | object |  | A specification for assertions to make on the body of the HTTP response obtained by executing the HTTP request in the same step. |
| code | response | number | 200 | The status code the response should have. |

### JSON matching

All requests and responses must be in JSON format. The tests allow simple JSON verification,
by describing *what should be present* in the actual response. This is done by
specifying a JSON structure, a *template*, for each response, and requiring each field
present in the template to match fields in the actual response. Unmatched fields result in test
failure, with the following rules:
* Objects must contain all listed fields, and may also contain unlisted ones.
* Arrays must match element-by-element.
* Numbers must match within precision `1e-9`.
* All other values must match exactly.

Note that the empty object `{ }` matches any other object, and can be used to fill
elements of an array that require no further validation.
