---
# Copyright Verizon Media. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "News search and recommendation tutorial - getting started on Docker"
---

## Introduction

Our goal with this series is to set up a Vespa application for personalized
news recommendations. We will do this in stages, starting with a simple news
search system and gradually adding functionality as we go through the
tutorial parts.

The parts are:  

1. Getting started - this part.
2. A basic news search application - application packages, feeding, query.
3. News search - sorting, grouping, and ranking.
4. Generating embeddings for users and news articles.
5. News recommendation - partial updates (news embeddings), ANNs, filtering
6. News recommendation - custom searchers, doc processors
7. News recommendation - parent-child, tensor ranking
8. Advanced news recommendation - intermission - training a ranking model
9. Advanced news recommendation - ML models

There are different entry points to this tutorial. This one is for getting
started using Docker on your local machine. Getting started on 
[cloud.vespa.ai](https://cloud.vespa.ai) is coming soon. We will also have a
version for [pyvespa](https://github.com/vespa-engine/pyvespa) soon.

In this part we will start with a minimal Vespa application to
get used to some basic operations for running the application on Docker.
In the next part of the tutorial, we'll start developing our application.

## Prerequisites

- [Docker Desktop on Mac](https://docs.docker.com/docker-for-mac/install) 
  or Docker on Linux
- [Git](https://git-scm.com/downloads)
- Operating system: macOS or Linux
- Architecture: x86_64
- Minimum **6GB** memory dedicated to Docker (the default is 2GB on Macs)

In the next part of this series, we will have some additional python
dependencies as we use PyTorch to train vector representations for news and
users and train machine learning models for use in ranking.

## A minimal Vespa application

This tutorial has a [companion sample
application](https://github.com/vespa-engine/sample-apps.git). Throughout
the tutorial we will be using support code from this application.
Also, the final state of each tutorial can be found in the various
`app-...` sub-directories.

Let's start by cloning the sample application. 

<pre data-test="exec">
$ git clone https://github.com/vespa-engine/sample-apps.git
$ cd sample-apps
$ git checkout lesters/add-news-tutorial-sample-app  # REMOVE me when merged
$ cd news
</pre>

The `getting-started` directory contains a minimal Vespa application. There
are three files there:

- `services.xml` -  defines the services the application consists of
- `hosts.xml` - defines which hosts or nodes the application will run on
- `schemas/news.sd` - defines the schema for searchable content. 

We will get back to these files in the next part of the tutorial.

## Starting Vespa

This application doesn't contain much at the moment, but let's start up the
application anyway by starting a Docker container to run it:

<pre data-test="exec">
$ docker pull vespaengine/vespa
$ docker run -m 10G --detach --name vespa --hostname vespa-tutorial \
    --volume `pwd`:/app --publish 8080:8080 vespaengine/vespa
</pre>

First, we pull the latest Vespa image from the Docker repository, then we
start it with the name `vespa`. This starts the Docker container and the
initial Vespa services to be able to deploy an application.

Starting the container can take a short while. Before continuing, make sure
that the configuration service is running. This is signified by a `200 OK`
response when querying the configuration service, running on port 19071:

<pre data-test="exec" data-test-wait-for="200 OK">
$ docker exec vespa bash -c 'curl -s --head http://localhost:19071/ApplicationStatus'
</pre>

The `docker exec vespa bash -c '...'` runs the command inside the Docker
container, so we don't have to expose the configuration server out from the
container. With the config server up and running, we can deploy our application:

<pre data-test="exec">
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-deploy prepare /app/app-getting-started && \
    /opt/vespa/bin/vespa-deploy activate'
</pre>

This runs the `vespa-deploy` command inside the Docker container, as before.
The `vespa-deploy prepare` command uploads the application and verifies the
content. If anything is wrong with the application, this step will fail with
a failure description. If everything is OK, the application can be activated by
`vespa-deploy activate`, which switches the application to a live status.

Whenever you have a new version of your application, you perform the same
steps: `vespa-deploy prepare` and `vespa-deploy activate`. In most cases,
there is no need to restart the application. Vespa takes care of
reconfiguring the system. If a restart is required in some rare case,
however, the `vespa-deploy prepare` will notify you.

In the upcoming parts of the tutorials, we'll frequently deploy the 
application in this manner. 

<p class="alert alert-success"> 
Note here that we prepare the *directory* `src/main/application`. Both
application directories and a zip file containing the application are
accepted. A zip file is created when compiling and packaging an
application containing custom Java code. We'll get back to that in part 6 
of the tutorial.
</p>

The first time you deploy your application, it might take a while to
start the services. Like the configuration server, you can query the 
status:

<pre data-test="exec" data-test-wait-for="200 OK">
$ curl -s --head http://localhost:8080/ApplicationStatus
</pre>

This returns a `200 OK` when it is ready for receiving traffic. Note here 
that we don't run the command inside the Docker container. The port `8080`
was exposed when starting the Docker container, so we can query it directly.

## Feeding to Vespa

We must index data before we can search for it. This is called 'feeding', 
and we'll get back to that in the next part of the tutorial. For now,
we'll feed in a single test document. We'll use the `vespa-http-client` 
Java feeder for this:

<pre data-test="exec" >
$ docker exec vespa bash -c 'java -jar /opt/vespa/lib/jars/vespa-http-client-jar-with-dependencies.jar \
    --verbose --file /app/doc.json --host localhost --port 8080'
</pre>

This runs the `vespa-http-client` Java client with the file 
`doc.json` file. This contains a single document which we'll 
query for below.

In later tutorials, when more data should be fed to the system,
use this command while pointing to the correct feed file.


## Testing Vespa

If everything is ok so far, our application should be up and running. We 
can query the endpoint:

<pre data-test="exec" data-test-assert-contains='Hello world!'>
$ curl -s http://localhost:8080/search/?query=sddocname:news
</pre>

This uses the `search` API to search for all documents of type `news`.
This should return `1` result, which is the document we fed above.
Well done!


## Stopping and starting Vespa

To stop Vespa, we can run the following commands:

<pre>
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-stop-services'
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-stop-configserver'
</pre>

Likewise, to start the Vespa services:

<pre>
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-start-configserver'
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-start-services'
</pre>

If a restart is required due to changes in the application package,
these two steps are what you need to do.

You can stop and kill the Vespa Docker application like this:

<pre data-test="after">
$ docker rm -f vespa
</pre>

This will delete the Vespa application, including all data, so 
don't do this unless you are sure.

## Conclusion

Our very simple application should now be up and running. In 
the next part of the tutorial, we'll start building from this 
foundation.

<script>
function processFilePREs() {
    var tags = document.getElementsByTagName("pre");

    // copy elements, because the list above is mutated by the insert html below
    var elems = [];
    for (i = 0; i < tags.length; i++) {
        elems.push(tags[i]);
    }

    for (i = 0; i < elems.length; i++) {
        var elem = elems[i];
        if (elem.getAttribute("data-test") === "file") {
            var html = elem.innerHTML;
            elem.innerHTML = html.replace(/<!--\?/g, "<?").replace(/\?-->/g, "?>").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            elem.insertAdjacentHTML("beforebegin", "<pre class=\"filepath\">file: " + elem.getAttribute("data-path") + "</pre>");
        }
    }
};

processFilePREs();

</script>