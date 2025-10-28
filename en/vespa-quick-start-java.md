---
# Copyright Vespa.ai. All rights reserved.
title: "Quick Start, with Java, using Docker"
---

This guide shows how to install and run Vespa on a single machine using Docker -
it builds and deploys an application, feeds some data and issues queries.
This application contains Java components, there's also
[a version that doesn't use Java](vespa-quick-start.html).
See [Getting Started](getting-started.html) for troubleshooting, next steps and other guides.

{% include pre-req.html memory="4 GB" extra-reqs='- [Java 17](https://openjdk.org/projects/jdk/17/).
- [Apache Maven](https://maven.apache.org/install.html) is used to build the application.
' %}

This guide is tested with *vespaengine/vespa:{{site.variables.vespa_version}}* container image.

## Running Vespa in Docker

1. **Validate the environment:**

   Make sure you see at minimum 4 GB.
   Refer to [Docker memory](/en/operations-selfhosted/docker-containers.html#memory)
   for details and troubleshooting:

   ```
   $ docker info | grep "Total Memory"
   or
   $ podman info | grep "memTotal"
   ```
2. **Install the Vespa CLI:**

   Using [Homebrew](https://brew.sh/):

   ```
   $ brew install vespa-cli
   ```

   You can also [download Vespa CLI](https://github.com/vespa-engine/vespa/releases)
   for Windows, Linux and macOS.
3. **Start a Vespa Docker container:**

   ```
   $ docker run --detach --name vespa --hostname vespa-container \
     --publish 8080:8080 --publish 19071:19071 \
     vespaengine/vespa
   ```

   The port `8080` is published to make the query and feed endpoints
   accessible from outside the docker container,
   19071 is the config server endpoint.
   Only one docker container named `vespa` can run at a time, change the name as needed.
   See [Docker containers](/en/operations-selfhosted/docker-containers.html) for more insights.
4. **Initialize `myapp/` to a copy of a sample
   [application package](application-packages.html):**

   ```
   $ vespa clone album-recommendation-java myapp
   $ cd myapp
   ```
5. **Build it:**

   ```
   $ mvn install
   ```
6. **Deploy it:**

   ```
   $ vespa deploy --wait 300
   ```
7. **Feed documents:**

   ```
   $ vespa feed src/test/resources/*.json
   ```
8. **Issue queries:**

   ```
   $ vespa query "select * from music where album contains 'head'"
   ```

   {% raw %}

   ```
   $ vespa query "select * from music where true" \
     "ranking=rank_albums" \
     "input.query(user_profile)={{cat:pop}:0.8,{cat:rock}:0.2,{cat:jazz}:0.1}"
   ```

   {% endraw %}

   This uses the [Query API](query-api.html).

## Next steps

Check out [getting started](getting-started.html) for more tutorials and use cases which Vespa is great for.

Explore the Vespa [sample applications](https://github.com/vespa-engine/sample-apps).

```
$ docker rm -f vespa
```
