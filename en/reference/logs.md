---
# Copyright Vespa.ai. All rights reserved.
title: "Log Files"
---

All Vespa components use a common log module for logging.
These log messages are added to a local log file in *$VESPA_HOME/logs/vespa/* and filtered,
then forwarded, to the log server on the administration node.
The log archive and rotation is explained in [log server](#log-server).

{% include note.html content='
If Vespa is running in a local container (named "vespa"), run `docker exec vespa vespa-logfmt`
to quickly dump logs.'%}

## Log file fields

Log files are in a machine-readable log format, made more human-readable by
[vespa-logfmt](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-logfmt) -
it can filter out log messages from specific programs, only show certain log levels,
print the time in a more directly understandable format and so on.
Each line that is logged consists of the following fields, in order, separated by a TAB (ASCII 9) character:

```
time host pid service component level message
```

| Log field | Description |
| --- | --- |
| *time* | Time in seconds since 1970-01-01 UTC, with optional fractional seconds after. E.g. 1102675319.726342 |
| *host* | The hostname of the machine that produced this log entry |
| *pid* | The process id, and an optional thread-id of the process/thread that logged the message |
| *service* | The Vespa service name of the logger |
| *component* | The component name that logged. An application may have multiple subcomponents with their own component names, usually starts with the name of the binary |
| *level* | One of fatal, error, warning, info, config, event, debug, or spam |
| *message* | The log message itself. All dangerous characters are escaped (CR, NL, TAB, \, ASCII < 32 and ASCII 128..159) |

| Log level | Description |
| --- | --- |
| *fatal* | Fatal error messages. The application must exit immediately, and restarting it will not help |
| *error* | Error messages. These are serious, the application cannot function correctly |
| *warning* | Warnings - the application may be able to continue, but the situation should be looked into |
| *info* | Informational messages that are not reporting error conditions, but should still be useful to the operator |
| *config* | Configuration settings |
| *event* | [Machine-readable events](#log-events). May contain information about processes starting and stopping, and various metrics |
| *debug* | Debug messages - normally suppressed |
| *spam* | Low-level debug messages, normally suppressed. Generates massive amounts of logs when enabled |

## Controlling log levels

Use [vespa-logctl](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-logctl)
to change active log levels of Vespa programs running as services, run-time.
When running in the cloud, tuning can be done in services.xml - see
[admin element (logging)](services-admin.html#logging).
Standalone programs will instead read the environment variable *VESPA_LOG_LEVEL*
on startup to determine which log levels should be active.
The default setting for *VESPA_LOG_LEVEL* is *"all -debug -spam"*,
which enables all log levels except debug and spam.
*vespa-logctl* shows or modifies the active log levels for a program,
or for parts of a program, while it is running.
This is useful for enabling debug output in parts of a live system for diagnosing problems.
It can also be used to silence programs that logs too verbose.

Programs that can be controlled by *vespa-logctl* put log control files in
*$VESPA_HOME/var/db/vespa/logcontrol/service.logcontrol*.
If this file exists on program startup, it will be used to set the logging levels.
This means that log level modifications done with *vespa-logctl* are sticky,
and can also be performed even if the program is not running.

## Log events

Event messages are log messages of the *event* type.
Events contain a well-defined payload which makes them suitable
for automated processing of various kinds, like alerting.
An event is emitted by a component when something of interest happens to it,
or when it has some metric data it wants to share with the world.
As all other log messages, events are collected to the admin nodes by the logserver component,
where they may be found in the Vespa log or intercepted programmatically by a logserver plugin.

Metrics are used to report on internal variables detailing the
processing performed by a particular component.
*VALUES* are numbers with momentarily significance,
such as queue lengths and latencies.
*COUNTER* are numbers increasing monotonically with each processing step,
such as number of documents processes, or number of queries.
Refer to the [metrics API](../operations/metrics.html).

Each event has an event *type*, a *version* and an optional *payload*.
In the log format, event types are expressed as a single word, versions as a simple integer,
and the payload as a set of *key=value* pairs.
The event payload is backslash-quoted just like log messages are in general.
This means that events may be double-quoted during transport.
Double-quote delimiters are not supported.

| Event | Description |
| --- | --- |
| starting | Payload: *name=<name>*  This event is sent by processes when they are about to start another process. Typical for, but not limited to, shell scripts. This event is not required to track processes, but is useful in cases where a sub-process may fail during startup. Example:  ``` starting container for default/container.0 ``` |
| started | Payload: *name=<name>*  The *started* event is sent by a service that just started up. Example:  ``` started/1 name="vespa-proton" ``` |
| stopping | Payload: *name=<name> why=<why>*  The *stopping* event is sent by a process that is about to exit. Example:  ``` stopping/1 name="vespa-proton" why="clean shutdown" ``` |
| stopped | Payload: *name=<name> pid=<pid> exitcode=<exitcode>*  This event is sent by a process monitoring when a sub-process exits. Example:  ``` stopped/1 name="vespa-proton" pid=14523 exitcode=0 ``` |
| crash | Payload: *name=<name> pit=<pid> signal=<signal>*  Submitted by a process monitoring a sub-process when the sub-process crashes (dumps core etc.). Example:  ``` crash/1 name="vespa-proton" pid=12345 signal=11 ``` |
| count | Payload: *name=<name> value=<value>*  General event for counts - for tracking any type of counter metric. The *name* is specific to each library/application. Counters are assumed to increase with time, counting the number of events since the program was started. Example:  ``` count/1 name="queries" value=10 ``` |
| value | Payload: *name=<name> value=<value>*  General event for values - for tracking any type of value metric. *Value is for values that cannot be counts*. Typical values are queue lengths, transaction frequencies and so on. Example:  ``` value/1 name="peak_qps" value=200 ``` |
| state | Payload: *name=<name> value=<value>*  General event for components in a process. *value* contains a string with more detailed information on what has happened. Note that the format and content of such strings can change between releases. Example:  ``` state/1 name="transactionlog.replay.start" value="{"domain":"test","serialnum":{"first":1,"last":1000}}" ``` |

## Logd

A small program named *logd* is responsible for rotating the
`vespa.log` file and also forwarding most log messages
(see next section for details) to the log server.
The log file is rotated after 24 hours, or if it grows too large.
Rotated logs are removed by logd after 30 days, or if the total size
grows above 1000 MB.

## Log server

On the log server on the administration node, the *Archiver*
plugin will write the log messages from each
node to a log archive. These messages are written to the
log file based on the message timestamp. The log files are located
in the `$VESPA_HOME/logs/vespa/logarchive` directory.
The catalog structure is like:

```
logarchive/<year>/<month>/<day>/<hour>-<serial>
```

For instance will a message logged at 2016-07-22 08:05:00 be found in:

```
logarchive/2016/07/22/08-0
```

All dates and times are in UTC. If the log file exceeds 20 Mb,
the file will be rotated and the serial number will increase.
Rotated log files more than *two hours* old, will be compressed to
save disk space. Archived log files in the log archive will be deleted for two reasons:
* Log file is more than 30 days old
* The full size of the log archive exceeds 30GB

{% include note.html content="If you need to remove log files more aggressively than this to e.g. prevent
running out of storage space, you need to add a way of purging log files no longer needed yourself."%}

Events and log messages with level *debug* and *spam* are normally filtered out
before sending to the log archive.
As an example, to forward events and *debug* log messages, add this to *services.xml*:

```
<services>
    <config name="cloud.config.log.logd">
        <loglevel>
            <event>
                <forward>true</forward>
            </event>
            <debug>
                <forward>true</forward>
            </debug>
        </loglevel>
    </config>
```

## Access log file content

The Container logs each request in its access log.
The log files are found in *$VESPA_HOME/logs/vespa/access/*. See
[access logging](../access-logging.html) for details.

### Time values in the access log compared to metrics and log events

The timing in the access log will in general be slightly off compared
to the timing values in vespa.log.
The reason is the "probes" into the system are placed at slightly different levels of abstraction.
The explanations here are directed at experienced users and troubleshooting.

#### Definition of processing time in the access log

Processing time in the access log starts when the execution is first
invoked from the search handler. The end is dependent on whether
the response is asynchronous or not. For a synchronous response, the
end is after the renderer has been invoked, but before the rendering
buffer is flushed. For an asynchronous response, e.g. a normal
search response, the end is defined as when the completion handler
is created. That means after control flow has returned from the
search chains, but before any network traffic or rendering has been done.

#### Definition of processing time in the vespa.log

StatisticsSearcher defines the metric *query_latency* and the log event
*mean_query_latency*. The data fed into both is the same.
The start of the interval is defined as when the control flow enters
StatisticsSearcher, the end as when the next searcher after
StatisticsSearcher returns from search(). This has the side
effect of *not* including fill time if the result was not already
filled when passed on from StatisticsSearcher. This may happen if the
SearchHandler has to invoke fill() itself, e.g. if no searchers need to access hit fields.

#### Timing summary

The access log includes everything happening before rendering, but
will exclude expensive rendering logic and slow networks. The query
latency event and metrics only covers what happens inside the search
chain where StatisticsSearcher is placed, and may exclude summary fetching.

### ZooKeeper Log

The ZooKeeper log file is normally not necessary to monitor on a regular basis,
but is mentioned here as a possible source of information in case you
should ever need to debug the Vespa configuration system.
It is located at `$VESPA_HOME/logs/vespa/zookeeper.<servicename>.log`.
