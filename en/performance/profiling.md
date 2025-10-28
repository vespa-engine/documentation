---
# Copyright Vespa.ai. All rights reserved.
title: "Profiling"
redirect_from:
- /en/performance/profiling-search-container.html
---

Guidelines when profiling:
* Define clearly what to profile.
* Find a load that represents what to profile.
  This is often the hardest part, as there is a lot of noise if stressing other components.
* Make sure that there are no other bottlenecks that blocks stressing the profiled component.
  It makes little sense to do CPU profiling if the network or the disk is the limitation factor.
* If possible, write special unit-tests like benchmark programs
  that stress exactly what to profile.
* If the system is multithreaded:
  + Always profile single threaded first -
    that gives a baseline for doing the scaling tests.
    Verify utilizing as many cores as expected.
  + Increase scaling gradually to at least 2x numcores
    or until throughput degrades.

Also see [using valgrind with Vespa](valgrind.html).

## CPU profiling

| vmstat | *vmstat* can be used to figure out what kind of resources are used:   * cpu usage split in user, system, idle, and io wait:   system should be low(<10) * swap in/out: should be zero.   Note: A maxed out system should have either maxed out disks or cpu (idle == 0). If not, there might be lock contention or the system is bottlenecked by upstream services.  Example:   ``` $ vmstat 1  procs -----------memory---------- ---swap-- -----io---- --system-- ----cpu---- r  b   swpd   free   buff  cache   si   so    bi    bo   in    cs us sy id wa 0  0   5628 3315460 304024 23008616    0    0    14    34    0     0  0  0 99  0 1  0   5628 3298884 304024 23008640    0    0     0   396   33  4615  9  1 90  0 0  0   5628 3316336 304028 23008644    0    0     0     0   15  4469  4  1 95  0 0  0   5628 3316592 304028 23008644    0    0     0     0   24  4364  0  0 100  0 0  0   5628 3316592 304028 23008644    0    0     0  2948   20  4305  0  0 100  0 0  0   5628 3316468 304028 23008644    0    0     0     0   22  4259  0  0 100  0 0  0   5628 3316468 304028 23008644    0    0     0   180   20  4279  0  0 100  0 0  0   5628 3316468 304028 23008644    0    0     0     0   26  4349  0  0 100  0 16  0   5628 3284236 304056 23008688    0    0    12   188   17  9196 38  2 60  0 19  0   5628 3267020 304056 23008732    0    0     8   128   44  6408 99  1  0  0 16  0   5628 3245472 304060 23008840    0    0    20     0    9  7191 99  1  0  0 17  0   5628 3227784 304060 23008872    0    0    20     0   27  6420 99  1  0  0 ``` |
| top | Use [top](https://linux.die.net/man/1/top) to get a real-time view of which processes consume CPU and memory. |
| iostat | Use [iostat](https://linux.die.net/man/1/iostat) to monitor disk IO. Note that the % busy is useless for SSD/NVMe storage disks, see [Two traps in iostat: %util and svctm](https://brooker.co.za/blog/2014/07/04/iostat-pct.html). |

## CPU Profiling using perf

Sometimes, when debugging cpu usage in a remote cluster and debugging performance,
it might be beneficial to get a performance profile snapshot.
To use `perf` find the pid of the [vespa-proton-bin](../proton.html) process which can be obtained using
[vespa-sentinel-cmd](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-sentinel-cmd), or *top/ps*. Record:

```
$ sudo perf record -g --pid=<pid-of-proton-process> sleep 60
```

View a performance profile report:

```
$ sudo perf report
```

Sometimes it is useful to have kernel debug info installed to get symbol info for the Linux kernel:

```
$ sudo yum install --enablerepo=base-debuginfo kernel-debuginfo-$(uname -r)
```

It is important to get somewhat same version of *kernel-debuginfo* as the *kernel* package.

### Container privileges

When debugging an unprivileged docker container,
`perf` commands can be executed from inside a privileged container sharing pid space:
{% raw %}

```
$ CONTAINER=host002-09
$ sudo docker run -ti --rm --privileged --pid container:$CONTAINER \
  --entrypoint bash $(sudo docker ps --filter name=$CONTAINER --format "{{.Image}}")
```

{% endraw %}

This starts a privileged container that shares the pid namespace,
using the same docker image as the container to debug.
Run `perf record ...` inside this privileged container.

## Profiling the Query Container

This section describes how you can configure the Container to
allow for profiling custom searchers in order to identify performance bottlenecks -
be it lock contention or CPU intensive algorithms.

### Install YourKit profiler on the Container

Yourkit is a good and simple tool for finding hotspots in Java code.
It supports both sampling and tracing. Often it is necessary to use both modes.
Tracing is accurate as to how many times a method is invoked and from where.
That can be used to analyze if you are actually not computing the same thing from multiple places
and overall doing more than you need.
However, it will hide effects of cache miss and especially cost of atomic operations and synchronization costs.

Assume there is an installation in a data center that you would like to profile,
preferably with a nice UI running on your local desktop.
All this is just a few steps away:
* Install yourkit
* Modify *services.xml*:

  ```
  <nodes>
    <jvm options="-agentlib:yjpagent" />
  ...
  </nodes>
  ```

  Read more about [jvm tuning](container-tuning.html).
  Disabling the freezedetector stops the container from shutting down during profiling.
* Re-deploy the application:

  ```
  $ vespa deploy appdir
  ```
* restart Vespa on the node that runs the Container

Browse *$VESPA_HOME/logs/vespa.log* for errors.
You are now ready to perform profiling; you just need to install the UI on your desktop.

### Install YourKit UI on the Desktop

The server is ready for profiling,
now install the YourKit profiler on the desktop.
Download the distribution that fits the OS you are running from
[YourKit](https://www.yourkit.com/).
Follow the installation instructions, including setting the *license server*.
**Note:**
By default the YourKit agent runs on port 10001.
If Vespa is running on hosts not directly reachable from the desktop,
setting up an SSH tunnel can work around:

```
$ ssh -L 1080:$hostname:10001 $hostname
```

where *$hostname* is the node that is running the container with the YourKit agent profiler.
All traffic to localhost (the desktop) port 1080 will be forwarded to the remote application running on port 10001.

### Using Yourkit

You are now ready to profile your application.
(You will need to put some realistic load against the container instance,
see the [Vespa benchmarking guide](vespa-benchmarking.html))
After having started the load simulation you can start the profiling session,
open the YourKit application installed locally and select
*Monitor Remote Applications => Connect to remote application*.
Enter *localhost:1080* and press Connect.
You should now see the profiling screen with
*Remote application "Server" (PID XXXXX) is being profiled at localhost:1080*.
