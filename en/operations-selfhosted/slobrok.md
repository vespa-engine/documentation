---
# Copyright Vespa.ai. All rights reserved.
title: "Service location broker - slobrok"
category: oss
redirect_from:
- /en/slobrok.html
---

Slobrok is an acronym for *Service Location Broker*,
and it is a name service used in Vespa.
The service listens on a specific port -
use [vespa-model-inspect](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect)
to find the `Slobrok` service's port number.

Slobrok is running by default on the administration node as well as one or two other random nodes for redundancy.
Best practise for a multi-node, high-availability application is found in the
[multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
sample application.
In this application, slobrok instances are hosted on nodes running
[config servers](/en/operations-selfhosted/configuration-server.html).
The motivation is, like the config servers, Vespa requires slobrok to be up for services to function.
Operating slobrok is the same as config servers, too - three is enough for most applications.
As slobrok requires minimal system resources,
it does not impact other services running on the same node ->
using config server nodes is ideal.

Clients, like the [Document API](/en/api.html),
will do lookups on any of the service location broker nodes.
Slobrok is not used in the query pipeline.
The [cluster-controller](/en/content/content-nodes.html#cluster-controller)
uses slobrok to evaluate service availability.

The Slobrok process looks like:

```
{% highlight sh %}
$ ps ax | grep vespa-slobrok
93906  ??  SJ     2:31.52 $VESPA_HOME/sbin/vespa-slobrok -p 19100 -c slobrok.0
{% endhighlight %}
```
