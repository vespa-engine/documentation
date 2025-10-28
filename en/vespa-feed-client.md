---
# Copyright Vespa.ai. All rights reserved.
title: "vespa-feed-client"
---

* Java library and command line client for feeding document operations using
  [Document v1](document-v1-api-guide.html) over [HTTP/2](performance/http2.html).
* Asynchronous, high-performance Java implementation, with retries and dynamic throttling.
* Supports a JSON array of feed operations, as well as [JSONL](https://jsonlines.org):
  one operation JSON per line.

## Installing

### Java library

The Java library is available as a
[Maven JAR artifact](https://search.maven.org/search?q=g:com.yahoo.vespa%20a:vespa-feed-client) at Maven Central.

### Command line client

Two alternatives:
* Install [*vespa-clients*/*vespa*](build-install-vespa.html) RPM package.
* Download [vespa-feed-client **zip** artifact](https://search.maven.org/artifact/com.yahoo.vespa/vespa-feed-client-cli) from Maven Central.

Download example:

```
$ F_REPO="https://repo1.maven.org/maven2/com/yahoo/vespa/vespa-feed-client-cli" && \
  F_VER=$(curl -Ss "${F_REPO}/maven-metadata.xml" | sed -n 's/.*<release>\(.*\)<.*>/\1/p') && \
  curl -SsLo vespa-feed-client-cli.zip ${F_REPO}/${F_VER}/vespa-feed-client-cli-${F_VER}-zip.zip && \
  unzip -o vespa-feed-client-cli.zip
```

## Enable feed endpoint in Vespa

Requirements:
* [Document API must be enabled on container](reference/services-container.html#document-api).

HTTP/2 over [TLS](reference/services-http.html#ssl) is optional but recommended from a security perspective.

Example *services.xml* with TLS:

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">
    <container version="1.0" id="default">
        <http>
            <server id="default" port="443">
                <ssl>
                    <private-key-file>/path/to/private-key.pem</private-key-file>
                    <certificate-file>/path/to/certificate.pem</certificate-file>
                    <ca-certificates-file>/path/ca-certificates.pem</ca-certificates-file>
                </ssl>
            </server>
        </http>
        <document-api/>
    </container>
</services>
```

Example *services.xml* without TLS:

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">
    <container version="1.0" id="default">
        <document-api/>
    </container>
</services>
```

## Using the client

The Javadoc for the programmatic API is available at
[javadoc.io](https://javadoc.io/doc/com.yahoo.vespa/vespa-feed-client-api).
See output of `$ vespa-feed-client --help` for usage.

Use `--speed-test` for bandwidth testing.

### Example Java

Add *vespa-feed-client* as dependency to your Maven (or other build system using Maven for dependency management):

```
<dependency>
    <groupId>com.yahoo.vespa</groupId>
    <artifactId>vespa-feed-client</artifactId>
    <version>{{site.variables.vespa_version}}</version>
</dependency>
```

Code examples are listed in the
[vespa-feed-client source code](https://github.com/vespa-engine/vespa/tree/master/vespa-feed-client-api/src/test/java/ai/vespa/feed/client/examples) on GitHub.
* [JsonFileFeederExample.java](https://github.com/vespa-engine/vespa/blob/master/vespa-feed-client-api/src/test/java/ai/vespa/feed/client/examples/JsonFileFeederExample.java)
* [JsonStreamFeederExample.java](https://github.com/vespa-engine/vespa/blob/master/vespa-feed-client-api/src/test/java/ai/vespa/feed/client/examples/JsonStreamFeederExample.java)
* [SimpleExample.java](https://github.com/vespa-engine/vespa/blob/master/vespa-feed-client-api/src/test/java/ai/vespa/feed/client/examples/SimpleExample.java)

### Example command line

HTTP/2 over TLS:

```
$ vespa-feed-client \
  --connections 4 \
  --certificate cert.pem --private-key key.pem --ca-certificates ca.pem \
  --file /path/to/json/file \
  --endpoint https://container-endpoint:443/
```

The input must be either a proper JSON array, or a series,
of JSON feed operations ([JSONL](https://jsonlines.org)),
in the format described for the Vespa feed client
[here](reference/document-json-format.html#document-operations).

HTTP/2 without TLS:

```
$ vespa-feed-client \
  --connections 4 \
  --file /path/to/json/file \
  --endpoint http://container-endpoint:8080/
```
