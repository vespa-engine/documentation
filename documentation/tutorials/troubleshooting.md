---
# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa tutorial troubleshooting"
---

## Deployment of a new application

If you've already had an application deployed and want to deploy a different one,
remove all the old documents using
[vespa-remove-index](../reference/vespa-cmdline-tools.html#vespa-remove-index):

    $ vespa-stop-services
    $ vespa-remove-index
    $ vespa-start-services

Next remove zookeeper files created by vespa, in `$VESPA_HOME/var/zookeeper`.
Now you should be able to deploy the new application without error.

