---
# Copyright Vespa.ai. All rights reserved.
title: Access Logging
---

The Vespa access log format allows the logs to be processed by a number of available tools
handling JSON based (log) files.
With the ability to add custom key/value pairs to the log from any Searcher,
you can easily track the decisions done by container components for given requests.

## Vespa Access Log Format

In the Vespa access log, each log event is logged as a JSON object on a single line.
The log format defines a list of fields that can be logged with every request.
In addition to these fields,
[custom key/value pairs](#logging-key-value-pairs-to-the-json-access-log-from-searchers) can be
logged via Searcher code. Pre-defined fields:

| Name | Type | Description | Always present |
| --- | --- | --- | --- |
| ip | string | The IP address request came from | yes |
| time | number | UNIX timestamp with millisecond decimal precision (e.g. 1477828938.123) when request is received | yes |
| duration | number | The duration of the request in seconds with millisecond decimal precision (e.g. 0.123) | yes |
| responsesize | number | The size of the response in bytes | yes |
| code | number | The HTTP status code returned | yes |
| method | string | The HTTP method used (e.g. 'GET') | yes |
| uri | string | The request URI from path and beyond (e.g. '/search?query=test') | yes |
| version | string | The HTTP version (e.g. 'HTTP/1.1') | yes |
| agent | string | The user agent specified in the request | yes |
| host | string | The host header provided in the request | yes |
| scheme | string | The scheme of the request | yes |
| port | number | The IP port number of the interface on which the request was received | yes |
| remoteaddr | string | The IP address of the [remote client](#logging-remote-address-port) if specified in HTTP header | no |
| remoteport | string | The port used from the [remote client](#logging-remote-address-port) if specified in HTTP header | no |
| peeraddr | string | Address of immediate client making request if different from *remoteaddr* | no |
| peerport | string | Port used by immediate client making request if different from *remoteport* | no |
| user-principal | string | The name of the authenticated user (java.security.Principal.getName()) if principal is set | no |
| ssl-principal | string | The name of the x500 principal if client is authenticated through SSL/TLS | no |
| search | object | Object holding search specific fields | no |
| search.totalhits | number | The total number of hits for the query | no |
| search.hits | number | The hits returned in this specific response | no |
| search.coverage | object | Object holding [query coverage information](graceful-degradation.html) similar to that returned in result set. | no |
| connection | string | Reference to the connection log entry. See [Connection log](#connection-log) | no |
| attributes | object | Object holding [custom key/value pairs](#logging-key-value-pairs-to-the-json-access-log-from-searchers) logged in searcher. | no |

{% include note.html content="IP addresses can be both IPv4 addresses in standard dotted format (e.g. 127.0.0.1)
or IPv6 addresses in standard form with leading zeros omitted (e.g. 2222:1111:123:1234:0:0:0:4321)."%}

An example log line will look like this (here, pretty-printed):

```
{
  "ip": "152.200.54.243",
  "time": 920880005.023,
  "duration": 0.122,
  "responsesize": 9875,
  "code": 200,
  "method": "GET",
  "uri": "/search?query=test&param=value",
  "version": "HTTP/1.1",
  "agent": "Mozilla/4.05 [en] (Win95; I)",
  "host": "localhost",
  "search": {
    "totalhits": 1234,
    "hits": 0,
    "coverage": {
      "coverage": 98,
      "documents": 100,
      "degraded": {
        "non-ideal-state": true
      }
    }
  }
}
```

{% include note.html content="The log format is extendable by design such that the order of the fields can be changed
and new fields can be added between minor versions.
Make sure any programmatic log handling is using a proper JSON processor."%}

Example: Decompress, pretty-print, with human-readable timestamps:

```
$ jq '. + {iso8601date:(.time | todateiso8601)}' \
  <(unzstd -c /opt/vespa/logs/vespa/access/JsonAccessLog.default.20210601010000.zst)
```

### Logging Remote Address/Port

In some cases when a request passes through an intermediate service,
this service may add HTTP headers indicating the IP address and port of the real origin client.
These values are logged as *remoteaddr* and *remoteport* respectively.
Vespa will log the contents in any of the following HTTP request headers as
*remoteaddr*: *X-Forwarded-For*, *Y-RA*, *YahooRemoteIP* or *Client-IP*.
If more than one of these headers are present, the precedence is in the order listed here,
i.e. *X-Forwarded-For* takes precedence over *Y-RA*.
The contents of the *Y-RP* HTTP request header will be logged as *remoteport*.

If the remote address or -port differs from those initiating the HTTP request,
the address and port for the immediate client making the request are logged as
*peeraddress* and *peerport* respectively.

## Configuring Logging

For details on the access logging configuration see [accesslog in the container](reference/services-container.html#accesslog) element in *services.xml*.

Key configuration options include:
* **fileNamePattern**: Pattern for log file names with time variable support
* **rotationInterval**: Time-based rotation schedule (minutes since midnight)
* **rotationSize**: Size-based rotation threshold in bytes (0 = disabled)
* **rotationScheme**: Either 'sequence' or 'date'
* **compressionFormat**: GZIP or ZSTD compression for rotated files

### Logging Request Content

Vespa supports logging of request content for specific URI paths. This is useful for inspecting query content of search POST requests
or document operations of Document v1 POST/PUT requests. The request content is logged as a base64-encoded string in the JSON access log.

To configure request content logging, use the [request-content](reference/services-container.html#request-content) element
in the accesslog configuration in *services.xml*.

Here is an example of how the request content appears in the JSON access log:

```
{
  ...
  "method": "POST",
  "uri": "/search",
  ...,
  "request-content": {
    "type": "application/json; charset=utf-8",
    "length": 12345,
    "body": "<raw bytes encoded with base64>"
  }
}
```

### File name pattern

The file name pattern is expanded using the time when the file is created.
The following parts in the file name are expanded:

| Field | Format | Meaning | Example |
| --- | --- | --- | --- |
| %Y | YYYY | Year | 2003 |
| %m | MM | Month, numeric | 08 |
| %x | MMM | Month, textual | Aug |
| %d | dd | Date | 25 |
| %H | HH | Hour | 14 |
| %M | mm | Minute | 30 |
| %S | ss | Seconds | 35 |
| %s | SSS | Milliseconds | 123 |
| %Z | Z | Time zone | -0400 |
| %T | Long | System.currentTimeMillis | 1349333576093 |
| %% | % | Escape percentage | % |

## Log rotation

Apache httpd style log *rotation* can be configured by setting the *rotationScheme*.
There's two alternatives for the rotationScheme, sequence and date.
Rotation can be triggered by time intervals using *rotationInterval* and/or by file size using *rotationSize*.

### Sequence rotation scheme

The *fileNamePattern* is used for the active log file name
(which in this case will often be a constant string).
At rotation, this file is given the name fileNamePattern.N where N is 1 + the largest integer found by
extracting the integers from all files ending by .<Integer> in the same directory

```
<accesslog type='json'
           fileNamePattern='logs/vespa/access/JsonAccessLog.<container id>.%Y%m%d%H%M%S'
           rotationScheme='sequence' />
```

### Date rotation scheme

The *fileNamePattern* is used for the active log file name here too,
but the log files are not renamed at rotation.
Instead, you must specify a time-dependent fileNamePattern so that each time a new log file is created,
the name is unique.
In addition, a symlink is created pointing to the active log file.
The name of the symlink is specified using *symlinkName*.

```
<accesslog type='json'
           fileNamePattern='logs/vespa/access/JsonAccessLog.<container id>.%Y%m%d%H%M%S'
           rotationScheme='date'
           symlinkName='JsonAccessLog' />
```

### Rotation interval

The time of rotation is controlled by setting *rotationInterval*:

```
<accesslog type='json'
           fileNamePattern='logs/vespa/access/JsonAccessLog.<container id>.%Y%m%d%H%M%S'
           rotationInterval='0 60 ...'
           rotationScheme='date'
           symlinkName='JsonAccessLog.<container id>' />
```

The rotationInterval is a list of numbers specifying when to do rotation.
Each element represents the number of minutes since midnight.
Ending the list with '...' means continuing the
[arithmetic progression](https://en.wikipedia.org/wiki/Arithmetic_progression)
defined by the two last numbers for the rest of the day.
E.g. "0 100 240 480 ..." is expanded to "0 100 240 480 720 960 1200"

### Log retention

Access logs are rotated, but not deleted by Vespa processes.
It is up to the application owner to take care of archiving of access logs.

## Logging Key/Value pairs to the JSON Access Log from Searchers

To add a key/value pair to the access log from a searcher, use

```
query/result.getContext(true).logValue(key,value)
```

Such key/value pairs may be added from any thread participating in handling the
query without incurring synchronization overhead.

If the same key is logged multiple times, the values written will
be included in the log as an array of strings rather than a single string value.

The key/value pairs are added to the *attributes* object in the log.

An example log line will then look something like this:

```
{"ip":"152.200.54.243","time":920880005.023,"duration":0.122,"responsesize":9875,"code":200,"method":"GET","uri":"/search?query=test&param=value","version":"HTTP/1.1","agent":"Mozilla/4.05 [en] (Win95; I)","host":"localhost","search":{"totalhits":1234,"hits":0},"attributes":{"singlevalue":"value1","multivalue":["value2","value3"]}}
```

A pretty print version of the same example:

```
{
  "ip": "152.200.54.243",
  "time": 920880005.023,
  "duration": 0.122,
  "responsesize": 9875,
  "code": 200,
  "method": "GET",
  "uri": "/search?query=test&param=value",
  "version": "HTTP/1.1",
  "agent": "Mozilla/4.05 [en] (Win95; I)",
  "host": "localhost",
  "search": {
    "totalhits": 1234,
    "hits": 0
  },
  "attributes": {
    "singlevalue": "value1",
    "multivalue": [
      "value2",
      "value3"
    ]
  }
}
```

## Connection log

In addition to the access log, one entry per connection is written to the connection log.
This entry is written on connection close. Available fields:

| Name | Type | Description | Always present |
| --- | --- | --- | --- |
| id | string | Unique ID of the connection, referenced from access log. | yes |
| timestamp | number | Timestamp (ISO8601 format) when the connection was opened | yes |
| duration | number | The duration of the request in seconds with millisecond decimal precision (e.g. 0.123) | yes |
| peerAddress | string | IP address used by immediate client making request | yes |
| peerPort | number | Port used by immediate client making request | yes |
| localAddress | string | The local IP address the request was received on | yes |
| localPort | number | The local port the request was received on | yes |
| remoteAddress | string | Original client ip, if proxy protocol enabled | no |
| remotePort | number | Original client port, if proxy protocol enabled | no |
| httpBytesReceived | number | Number of HTTP bytes sent over the connection | no |
| httpBytesSent | number | Number of HTTP bytes received over the connection | no |
| requests | number | Number of requests sent by the client | no |
| responses | number | Number of responses sent to the client | no |
| ssl | object | Detailed information on ssl connection | no |

## SSL information

| Name | Type | Description | Always present |
| --- | --- | --- | --- |
| clientSubject | string | Client certificate subject | no |
| clientNotBefore | string | Client certificate valid from | no |
| clientNotAfter | string | Client certificate valid to | no |
| sessionId | string | SSL session id | no |
| protocol | string | SSL protocol | no |
| cipherSuite | string | Name of session cipher suite | no |
| sniServerName | string | SNI server name | no |
