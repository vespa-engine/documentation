---
# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa tutorial troubleshooting"
---

* TOC
{:toc}

## Deployment of a new application

If you've already had an application deployed and want to deploy a different one, you need to remove all the old documents, since they probably won't be relevant anymore. To do that, stop the vespa service and run

	$ vespa-remove-index

Next you will need to manually remove zookeeper files created by vespa, in `$VESPA_HOME/var/zookeeper`. Now you should be able to deploy the new application without error.

