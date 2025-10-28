---
# Copyright Vespa.ai. All rights reserved.
title: "Quick Start, using Docker"
---

This guide shows how to install and run Vespa on a single machine using Docker -
it deploys an application, feeds some data and issues queries.
See [Getting Started](getting-started.html) for troubleshooting, next steps and other guides.

{% include pre-req.html memory="4 GB" %}

This guide is tested with *vespaengine/vespa:{{site.variables.vespa_version}}* container image.

## Running Vespa in Docker

1. **Validate the environment:**

   ```
   $ docker info | grep "Total Memory"
   or
   $ podman info | grep "memTotal"
   ```

   Make sure you see at minimum 4 GB.
2. **Install the Vespa CLI:**

   Using [Homebrew](https://brew.sh/):

   ```
   $ brew install vespa-cli
   ```

   You can
   also [download Vespa
   CLI](https://github.com/vespa-engine/vespa/releases) for Windows, Linux and macOS.
3. **Set local target:**

   ```
   $ vespa config set target local
   ```
4. **Start a Vespa Docker container:**

   ```
   $ docker run --detach --name vespa --hostname vespa-container \
     --publish 8080:8080 --publish 19071:19071 \
     vespaengine/vespa
   ```

   The port `8080` is published to make the search and feed interfaces
   accessible from outside the docker container,
   19071 is the config server endpoint.
   Only one docker container named `vespa` can run at a time so change the name if needed.
   See [Docker containers](/en/operations-selfhosted/docker-containers.html) for more insights.
5. **Initialize `myapp/` to a copy of a
   [sample](https://github.com/vespa-engine/sample-apps)
   [application package](application-packages.html):**

   ```
   $ vespa clone album-recommendation myapp && cd myapp
   ```
6. **Deploy it:**

   ```
   $ vespa deploy --wait 300 ./app
   ```
7. **Feed documents:**

   ```
   $ vespa feed dataset/*.json
   ```
8. **Issue queries:**

   ```
   $ vespa query "select * from music where album contains 'head'" \
     language=en-US
   ```
```
   {% raw %}
   $ vespa query "select * from music where true" \
     "ranking=rank_albums" \
     "input.query(user_profile)={pop:0.8,rock:0.2,jazz:0.1}"
   {% endraw %}
   ```
```
   {% raw %}
   $ vespa query "select * from music where true" \
     "ranking=rank_albums" \
     "input.query(user_profile)={pop:0.8,rock:0.2,jazz:0.1}" \
     "presentation.format.tensors=short-value"
   {% endraw %}
   ```

   This uses the [Query API](query-api.html).
   Note that a query's language is a factor when doing text matching,
   refer to [linguistics](linguistics.html#language-handling) to learn more.
9. **Get documents:**

   ```
   $ vespa document get id:mynamespace:music::a-head-full-of-dreams
   ```
```
   $ vespa visit
   ```

   Get a document by ID, or export all documents -
   see [/document/v1](document-v1-api-guide.html)
   and [vespa visit](visiting.html).

## Next steps

Check out [getting started](getting-started.html) for more tutorials and use cases which Vespa is great for.

```
$ docker rm -f vespa
```
