---
# Copyright Vespa.ai. All rights reserved.
title: Benchmarking
category: cloud
---

This is a step-by-step guide to get started with benchmarking on Vespa Cloud,
based on the [Vespa benchmarking guide](/en/performance/vespa-benchmarking.html),
using the [sample app](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation).
Overview:

![Vespa Cloud Benchmarking](/assets/img/cloud-benchmarks.svg)

## Set up a perf instance

Use an instance in the [perf zone](https://cloud.vespa.ai/en/reference/environments.html) for benchmarks.
To deploy an instance there, use the [getting started](getting-started.html) guide,
set the `perf` zone in the deploy step set:

```
$ vespa deploy -z perf.aws-us-east-1c --wait 600
```

Feed documents:

```
$ vespa feed -z perf.aws-us-east-1c ext/documents.jsonl
```

Query documents to validate the feed:

```
$ vespa query -z perf.aws-us-east-1c "select * from music where true"
```

Query documents using curl:

```
$ curl \
  --cert ~/.vespa/mytenant.myapp.default/data-plane-public-cert.pem \
  --key  ~/.vespa/mytenant.myapp.default/data-plane-private-key.pem \
  -H "Content-Type: application/json" \
  --data '{"yql" : "select * from music where true"}' \
  https://myapp.tenant.aws-us-east-1c.perf.z.vespa-app.cloud/search/
```

At this point, the instance is ready, with data, and can be queried using data-plane credentials.

## Test using vespa-fbench

The rest of the guide assumes the data-plane credentials are in working directory:

```
$ ls -1 *.pem
  data-plane-private-key.pem
  data-plane-public-cert.pem
```

Prepare a query file:

```
$ echo "/search/?yql=select+*+from+music+where+true" > query001.txt
```

Test using
[vespa-fbench](/en/operations/tools.html#vespa-fbench)
running in a docker container:

```
$ docker run -v $(pwd):/files -w /files \
    --entrypoint /opt/vespa/bin/vespa-fbench \
    vespaengine/vespa \
    -C data-plane-public-cert.pem \
    -K data-plane-private-key.pem \
    -T /etc/ssl/certs/ca-bundle.crt \
    -n 1 -q query001.txt -s 1 -c 0 \
    -o output.txt \
    myapp.mytenant.aws-us-east-1c.perf.z.vespa-app.cloud 443
```

`-o output.txt` is useful when validating the test - remove this option when load testing.
Make sure there are no `SSL_do_handshake` errors in the output.
Expect HTTP status code 200:

```
  Starting clients...
  Stopping clients
  Clients stopped.
  .
  Clients Joined.
  *** HTTP keep-alive statistics ***
  connection reuse count -- 4
  ***************** Benchmark Summary *****************
  clients:                       1
  ran for:                       1 seconds
  cycle time:                    0 ms
  lower response limit:          0 bytes
  skipped requests:              0
  failed requests:               0
  successful requests:           5
  cycles not held:               5
  minimum response time:    128.17 ms
  maximum response time:    515.35 ms
  average response time:    206.38 ms
  25 percentile:            128.70 ms
  50 percentile:            129.60 ms
  75 percentile:            130.20 ms
  90 percentile:            361.32 ms
  95 percentile:            438.36 ms
  99 percentile:            499.99 ms
  actual query rate:          4.80 Q/s
  utilization:               99.03 %
  zero hit queries:              5
  http request status breakdown:
    200 :        5
```

At this point, running queries using *vespa-fbench* works well from local laptop.

## Run queries inside data center

Next step is to run this from the same location (data center) as the perf zone.
In this example, an AWS [zone](https://cloud.vespa.ai/en/reference/zones). Deduce the AWS zone from Vespa Cloud zone name.
Below is an example using a host with Amazon Linux 2023 AMI (HVM) image:

1. Create the host - here assume key pair is named *key.pem*.
   No need to do anything other than default.
2. Log in, update, install docker:

   ```
   $ ssh -i key.pem ec2-user@ec2-xx-xxx-xxx-xxx.compute-1.amazonaws.com
   [ec2-user]$ sudo yum update -y
   [ec2-user]$ sudo yum install -y docker
   [ec2-user]$ sudo service docker start
   [ec2-user]$ sudo usermod -a -G docker ec2-user
   [ec2-user]$ exit
   ```
3. Copy credentials for endpoint access, log in and validate docker setup:

   ```
   $ scp -i key.pem data-plane-private-key.pem ec2-user@ec2-xx-xxx-xxx-xxx.compute-1.amazonaws.com:
   $ scp -i key.pem data-plane-public-cert.pem ec2-user@ec2-xx-xxx-xxx-xxx.compute-1.amazonaws.com:

   $ ssh -i key.pem ec2-user@ec2-xx-xxx-xxx-xxx.compute-1.amazonaws.com
   [ec2-user]$ docker info
   ```
4. Make a dummy query:

   ```
   [ec2-user]$ echo "/search/?yql=select+*+from+music+where+true" > query001.txt
   ```
5. Run vespa-fbench and verify 200 response:

   ```
   [ec2-user]$ docker run -v $(pwd):/files -w /files \
                 --entrypoint /opt/vespa/bin/vespa-fbench \
                 vespaengine/vespa \
                 -C data-plane-public-cert.pem \
                 -K data-plane-private-key.pem \
                 -T /etc/ssl/certs/ca-bundle.crt \
                 -n 1 -q query001.txt -s 1 -c 0 \
                 myapp.mytenant.aws-us-east-1c.z.vespa-app.cloud 443
   ```

At this point, you are able to benchmark using *vespa-fbench* in the same zone as the Vespa Cloud perf instance.

## Run benchmark

Use the [Vespa Benchmarking Guide](/en/performance/vespa-benchmarking.html)
to plan and run benchmarks.
Also see [sizing](#sizing) below.
Make sure the client running the benchmark tool has sufficient resources.

Export [metrics](/en/operations/metrics.html):

```
$ curl \
    --cert data-plane-public-cert.pem \
    --key data-plane-private-key.pem \
    https://myapp.mytenant.aws-us-east-1c.perf.z.vespa-app.cloud/prometheus/v1/values
```

Notes:
* Periodially dump all metrics using `consumer=Vespa`.
* Make sure you will not exhaust your serving threads on your container nodes while in production. This can be verified by making
  sure this expression stays well below 100% (typically below 50%) for the traffic you expect:
  `100 * (jdisc.thread_pool.active_threads.sum / jdisc.thread_pool.active_threads.count) / jdisc.thread_pool.size.max`
  for each `threadpool` value. You can increase the number of threads in the pools by using larger container nodes,
  more container nodes or by tuning the number of threads as described in
  [services-search](/en/reference/services-search.html#threadpool).
  In the case you do exhaust a threadpool and its queue you will experience HTTP 503 responses for requests that are rejected by
  the container.

## Making changes

Whenever deploying changes to configuration, track progress in the Deployment dashboard.
Some changes, like changing
[requestthreads](/en/reference/services-content.html#requestthreads)
will restart content nodes, and this is done in sequence and takes time.
Wait for successful completion in *Wait for services and endpoints to come online*.

When changing node type/count, wait for auto data redistribution to complete,
watching the `vds.idealstate.merge_bucket.pending.average` metric:

```
$ while true; do curl -s \
    --cert data-plane-public-cert.pem \
    --key data-plane-private-key.pem \
    https://myapp.mytenant.aws-us-east-1c.perf.z.vespa-app.cloud/prometheus/v1/values?consumer=Vespa | \
    grep idealstate.merge_bucket.pending.average; \
    sleep 10; done
```

Notes:
* Dump all metrics using `consumer=Vespa`.
* After changing the number of content nodes, this metric will jump, then decrease (not necessarily linearly) -
  speed depending on data volume.

## Sizing

Using Vespa Cloud enables the Vespa Team to assist you to optimise the application to reduce resource spend.
Based on 150 applications running on Vespa Cloud today, savings are typically 50%.
Cost optimization is hard to do without domain knowledge -
but few teams are experts in both their application and its serving platform.
Sizing means finding both the right node size and the right cluster topology:

![Resize to fewer and smaller nodes](/assets/img/nodes.svg)

Applications use Vespa for their primary business use cases.
Availability and performance vs. cost are business decisions.
The best sized application can handle all expected load situations,
and is configured to degrade quality gracefully for the unexpected.

Even though Vespa is cost-efficient out of the box,
Vespa experts can usually spot over/under-allocations in CPU, memory and disk space/IO,
and discuss trade-offs with the application team.

Using [automated deployments](automated-deployments) applications go live with little risk.
After launch, right-size the application based on true load after using Vespa’s elasticity features
with automated data migration.

Use the [Vespa sizing guide](/en/performance/sizing-search.html)
to size the application and find metrics used there. Pro-tips:
* 60% is a good max memory allocation
* 50% is a good max CPU allocation, although application dependent.
* 70% is a good max disk allocation

Rules of thumb:
* Memory and disk scales approximately linearly for indexed fields' data -
  attributes have a fixed cost for empty fields.
* Data variance will impact memory usage.
* Undersized instances will
  [block writes](/en/operations/feed-block.html).
* If is often a good idea to use the `dev` zone to test memory impact of adding large fields,
  e.g. adding an embedding.

## Notes
* The user running benchmarks must have read access to the endpoint -
  if you already have, you can skip this section.
  Refer to the [Vespa security guide](https://cloud.vespa.ai/en/security/guide#data-plane).
* [Monitoring](monitoring) is useful to track metrics when benchmarking.
