---
# Copyright Vespa.ai. All rights reserved.
title: "HTTP Performance Testing of the Container using Gatling"
---

For container testing, more flexibility and more detailed
checking than straightforward saturating an interface with HTTP requests is
often required. The stress test tool [Gatling](https://gatling.io/) provides such capabilities in a
flexible manner with the possibility of writing arbitrary plug-ins and a DSL for
the most common cases. This document shows how to get started using Gatling
with Vespa. Experienced Gatling users should find there is nothing special with
testing Vespa versus other HTTP services.

## Install Gatling

Refer to Gatling's [documentation for getting started](https://gatling.io/docs/gatling/reference/current/),
or simply get the newest version from the
[Gatling front page](https://gatling.io/),
unpack the tar ball and jump straight into it.
The tool runs happily from the directory created when unpacking it.
This tutorial is written with Gatling 2 in mind.

## Configure the First Test with a Query Log

Refer to the Gatling documentation on how to set up the recorder.
This tool acts as a browser proxy, recording what you do in the browser,
allowing you to replay that as a test scenario.

After running *bin/recorder.sh* and setting package to *com.vespa.example*
and class name to *VespaTutorial*,
running a simple query against your node *mynode* (running e.g.
[album-recommendation-java](https://github.com/vespa-engine/sample-apps/tree/master/album-recommendation-java)), should create a basic simulation looking something like the following in
*user-files/simulations/com/vespa/example/VespaTutorial.scala*:

```
package com.vespa.example

import io.gatling.core.Predef._
import io.gatling.core.session.Expression
import io.gatling.http.Predef._
import io.gatling.jdbc.Predef._
import io.gatling.http.Headers.Names._
import io.gatling.http.Headers.Values._
import scala.concurrent.duration._
import bootstrap._
import assertions._

class VespaTutorial extends Simulation {

        val httpProtocol = http
                .baseURL("http://mynode:8080")
                .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
                .acceptEncodingHeader("gzip, deflate")
                .connection("keep-alive")
                .userAgentHeader("Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0")

        val headers_1 = Map("""Cache-Control""" -> """max-age=0""")

        val scn = scenario("Scenario Name")
                .exec(http("request_1")
                        .get("""/search/?query=bad""")
                        .headers(headers_1))

        setUp(scn.inject(atOnce(1 user))).protocols(httpProtocol)
}
```

Running a single query over and over again is not useful, so we have a
tiny query log in a CSV file we want to run in our test,
*user-files/data/userinput.csv*:

```
userinput
bad religion
bad
lucky oops
radiohead
bad jackson
```

As usual for CSV files, the first line names the parameters.
A literal comma may be escaped with backslash as "\,".
Gatling takes hand of URL quoting, there is no need to e.g. encode space as "%20".

Add a feeder:

```
package com.vespa.example

import io.gatling.core.Predef._
import io.gatling.core.session.Expression
import io.gatling.http.Predef._
import io.gatling.jdbc.Predef._
import io.gatling.http.Headers.Names._
import io.gatling.http.Headers.Values._
import scala.concurrent.duration._
import bootstrap._
import assertions._

class VespaTutorial extends Simulation {

        val httpProtocol = http
                .baseURL("http://mynode:8080")
                .acceptHeader("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
                .acceptEncodingHeader("gzip, deflate")
                .connection("keep-alive")
                .userAgentHeader("Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0")

        val headers_1 = Map("""Cache-Control""" -> """max-age=0""")

        val scn = scenario("Scenario Name")
                .feed(csv("userinput.csv").random)
                .exec(http("request_1")
                        .get("/search/")
                        .queryParam("query", "${userinput}")
                        .headers(headers_1))

        setUp(scn.inject(constantRate(100 usersPerSec) during (10 seconds)))
                .protocols(httpProtocol)
}
```

Now, we have done a couple of changes to the original scenario.
First, we have added the feeder.
Since we do not have enough queries available for running long enough to get a scenario for some traffic,
we chose the "random" strategy.
This means a random user input string will be chosen for each invocation, and it might be reused.
Also, we have changed how the test is run, from just a single query, into a constant rate of 100 users for 10 seconds.
We should expect something as close as possible to 100 QPS in our test report.

## Running a Benchmark

We now have something we can run both on a headless node and on a personal laptop,
sample run output:

```
$ ./bin/gatling.sh
GATLING_HOME is set to ~/tmp/gatling-charts-highcharts-2.0.0-M3a
Choose a simulation number:
     [0] advanced.AdvancedExampleSimulation
     [1] basic.BasicExampleSimulation
     [2] com.vespa.example.VespaTutorial
2
Select simulation id (default is 'vespatutorial'). Accepted characters are a-z, A-Z, 0-9, - and _

Select run description (optional)

Simulation com.vespa.example.VespaTutorial started...

================================================================================
2014-04-09 11:54:33                                           0s elapsed
---- Scenario Name -------------------------------------------------------------
[-                                                                         ]  0%
          waiting: 998    / running: 2      / done:0
---- Requests ------------------------------------------------------------------
> Global                                                   (OK=0      KO=0     )

================================================================================

================================================================================
2014-04-09 11:54:38                                           5s elapsed
---- Scenario Name -------------------------------------------------------------
[####################################                                      ] 49%
          waiting: 505    / running: 0      / done:495
---- Requests ------------------------------------------------------------------
> Global                                                   (OK=495    KO=0     )
> request_1                                                (OK=495    KO=0     )
================================================================================

================================================================================
2014-04-09 11:54:43                                          10s elapsed
---- Scenario Name -------------------------------------------------------------
[######################################################################### ] 99%
          waiting: 8      / running: 0      / done:992
---- Requests ------------------------------------------------------------------
> Global                                                   (OK=992    KO=0     )
> request_1                                                (OK=992    KO=0     )
================================================================================

================================================================================
2014-04-09 11:54:43                                          10s elapsed
---- Scenario Name -------------------------------------------------------------
[##########################################################################]100%
          waiting: 0      / running: 0      / done:1000
---- Requests ------------------------------------------------------------------
> Global                                                   (OK=1000   KO=0     )
> request_1                                                (OK=1000   KO=0     )
================================================================================

Simulation finished.
Generating reports...
Parsing log file(s)...
Parsing log file(s) done

================================================================================
---- Global Information --------------------------------------------------------
> numberOfRequests                                    1000 (OK=1000   KO=0     )
> minResponseTime                                       10 (OK=10     KO=-     )
> maxResponseTime                                       30 (OK=30     KO=-     )
> meanResponseTime                                      10 (OK=10     KO=-     )
> stdDeviation                                           2 (OK=2      KO=-     )
> percentiles1                                          10 (OK=10     KO=-     )
> percentiles2                                          10 (OK=10     KO=-     )
> meanNumberOfRequestsPerSecond                         99 (OK=99     KO=-     )
---- Response Time Distribution ------------------------------------------------
> t < 800 ms                                          1000 (100%)
> 800 ms < t < 1200 ms                                   0 (  0%)
> t > 1200 ms                                            0 (  0%)
> failed                                                 0 (  0%)
================================================================================

Reports generated in 0s.
Please open the following file : ~/tmp/gatling-charts-highcharts-2.0.0-M3a/results/vespatutorial-20140409115432/index.html
```

The report gives graphs showing how the test progressed and summaries for failures and time spent.
