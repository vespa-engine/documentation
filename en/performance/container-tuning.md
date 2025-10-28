---
# Copyright Vespa.ai. All rights reserved.
title: "Container Tuning"
---

A collection of configuration parameters to tune the Container as used in Vespa.
Some configuration parameters have native
[services.xml](../application-packages.html) support
while others are configured through
[generic config overrides](../reference/config-files.html#generic-configuration-in-services-xml).

## Container worker threads

The container uses multiple thread pools for its operations.
Most components including request handlers use the container's *default thread pool*,
which is controlled by a shared executor instance.
Any component can utilize the default pool by injecting an `java.util.concurrent.Executor` instance.
Some built-in components have dedicated thread pools - such as the Jetty server and the search handler.
These thread pools are injected through special wiring in the config model and
are not easily accessible from other components.

The thread pools are by default scaled on the system resources as reported by the JVM
(`Runtime.getRuntime().availableProcessors()`).
It's paramount that the `-XX:ActiveProcessorCount`/`jvm_availableProcessors`
configuration is correct for the container to work optimally.
The default thread pool configuration can be overridden through services.xml.
We recommend you keep the default configuration as it's tuned to work across a variety of workloads.
Note that the default configuration and pool usage may change between minor versions.

The container will pre-start the minimum number of worker threads,
so even an idle container may report running several hundred threads.
The thread pool is pre-started with the number of thread specified in the
[`threads`](../reference/services-search.html#threadpool-threads) parameter.
Note that tuning the capacity upwards increases the risk of high GC pressure
as concurrency becomes higher with more in-flight requests.
The GC pressure is a function of number of in-flight requests, the time it takes to complete the request
and the amount of garbage produced per request.
Increasing the queue size will allow the application to handle shorter traffic bursts without rejecting requests,
although increasing the average latency for those requests that are queued up.
Large queues will also increase heap consumption in overload situations.
Extra threads will be created once the queue is full (when [`boost`](../reference/services-search.html#threads.boost) is specified), and are destroyed after an idle timeout.
If all threads are occupied, requests are rejected with a 503 response.

The effective thread pool configuration and utilization statistics can be observed through the
[Container Metrics](/en/operations/metrics.html#container-metrics).
See [Thread Pool Metrics](/en/operations/metrics.html#thread-pool-metrics) for a list of metrics exported.

{% include note.html content=' If the queue size is set to 0 the metric measuring the queue size -
`jdisc.thread_pool.work_queue.size` - will instead switch to measure how many threads are active.'%}

### Recommendation

A fixed size pool is preferable for stable latency during peak load,
at a cost of a higher static memory load and increased context-switching overhead if excessive number of threads are configured.
Variable size pool is mostly beneficial to minimize memory consumption during low-traffic periods, and in general if the size of peak load is somewhat unknown.
The downside is that once all core threads are active,
latency will increase as additional tasks are queued and launching extra threads is relatively expensive as it involves system calls to the OS.

### Lower limit

The container will override any configuration if the effective value is below a fixed minimum. This is to
reduce the risk of certain deadlock scenarios and improve concurrency for low-resource environments.
* Minimum 8 threads.
* Minimum 650 queue capacity (if queue is not disabled).

### Example

```
{% highlight xml %}







            40


            100







        1000
        1000


{% endhighlight %}
```

## Container memory usage

> Help, my container nodes are using more than 70% memory!

It's common to observe the container process utilizing its maximum configured heap size.
This, by itself, is not necessarily an indication of a problem. The Java Virtual Machine (JVM)
manages memory within the allocated heap, and it's designed to use as much of it as possible
to reduce the frequency of garbage collection.

To understand whether enough memory is allocated, look at the garbage collection activity.
If GC is running frequently and using significant CPU or causing long pauses, it might
indicate that the heap size is too small for the workload. In such cases, consider increasing
the maximum heap size. However, if the garbage collector is running infrequently and efficiently,
it's perfectly normal for the container to utilize most or all of its allocated heap, and even more
(as some memory will also be allocated outside the heap; e.g. direct buffers for efficient data transfer).

Vespa exports several metrics to allow you to monitor JVM GC performance, such as [jvm.gc.overhead](../reference/container-metrics-reference.html#jvm_gc_overhead)
- if this exceeds 8-10% you should consider increasing heap memory and/or tuning GC settings.

## JVM heap size

Change the default JVM heap size settings used by Vespa to better suit
the specific hardware settings or application requirements.

By setting the relative size of the total JVM heap in
[percentage of available memory](../reference/services-container.html#nodes),
one does not know exactly what the heap size will be,
but the configuration will be adaptable
and ensure that the container can start
even in environments with less available memory.
The example below allocates 50% of available memory on the machine to the JVM heap:

```
{% highlight xml %}






{% endhighlight %}
```

## JVM Tuning

Use *gc-options* for controlling GC related parameters
and *options* for tuning other parameters.
See [reference documentation](../reference/services-container.html#nodes).
Example: Running with 4 GB heap using G1 garbage collector and using NewRatio = 1
(equal size of old and new generation) and enabling verbose GC logging (logged to stdout to vespa.log file).

```
{% highlight xml %}






{% endhighlight %}
```

The default heap size with docker image is 1.5g which can for high throughput applications be on the low side,
causing frequent garbage collection.
By default, the G1GC collector is used.

### Config Server and Config Proxy

The config server and proxy are not executed based on the model in *services.xml*.
On the contrary, they are used to bootstrap the services in that model.
Consequently, one must use configuration variables
to set the JVM parameters for the config server and config proxy.
They also need to be restarted (*services* in the config proxy's case) after a change,
but one does *not* need to *vespa prepare*
or *vespa activate* first. Example:

```
VESPA_CONFIGSERVER_JVMARGS      -Xlog:gc
VESPA_CONFIGPROXY_JVMARGS       -Xlog:gc -Xmx256m
```

Refer to [Setting Vespa variables](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables).

## Container warmup

Some applications observe that the first queries made to a freshly started container
take a long time to complete.
This is typically due to some components performing lazy setup of data structures or connections.
Lazy initialization should be avoided in favor of eager initialization in component constructor,
but this is not always possible.

A way to avoid problems with the first queries in such cases
is to perform warmup queries at startup.
This is done by issuing queries from the constructor of the Handler of regular queries.
If using the default handler,
[com.yahoo.search.handler.SearchHandler](https://github.com/vespa-engine/vespa/blob/master/container-search/src/main/java/com/yahoo/search/handler/SearchHandler.java),
subclass this and configure your subclass as the handler of query requests in *services.xml*.

Add a call to a warmupQueries() method as the last line of your handler constructor.
The method can look something like this:

```
{% highlight java %}
private void warmupQueries() {
    String[] requestUris = new String[] {"warmupRequestUri1", "warmupRequestUri2"};
    int warmupIterations = 50;

    for (int i = 0; i < warmupIterations; i++) {
        for (String requestUri : requestUris) {
            handle(HttpRequest.createTestRequest(requestUri, com.yahoo.jdisc.http.HttpRequest.Method.GET));
        }
    }
}
{% endhighlight %}
```

Since these queries will be executed before the container starts accepting external queries,
they will cause the first external queries to observe a warmed up container instance.

Use [metrics.ignore](../reference/query-api-reference.html#metrics.ignore)
in the warmup queries to eliminate them from being reported in metrics.
