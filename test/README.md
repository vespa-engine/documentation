<!-- Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root. -->

# Documentation testing

The test suite is exactly the same as in [sample-apps](https://github.com/vespa-engine/sample-apps),
refer to [sample-apps/test/README.md](https://github.com/vespa-engine/sample-apps/blob/master/test/README.md).
Only [_test_config.yml](_test_config.yml) should differ.

Ideally, this directory did not have to be copied, better if test scripts added to a test docker image
or test artifacts pulled from a central location.
