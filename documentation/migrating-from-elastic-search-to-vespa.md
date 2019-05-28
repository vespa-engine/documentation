---
# Copyright 2018 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Migrating from Elasticsearch to Vespa"
---


This document will show how to move data from Elasticsearch to Vespa. By the end of this guide you will have generated a deployable Vespa application package from your existing Elasticsearch cluster. To consider whether Vespa is a better choice for your use case, take a look at this [comparison](/documentation/elastic-search-comparison.html)

<a id="Moving_documents_from_ES_to_Vespa"></a>
#### 1. **Get all documents from Elasticsearch with ElasticDump**
It is possible to use [ElasticDump](https://github.com/taskrabbit/elasticsearch-dump) to get all documents from Elasticsearch in a JSON-file. Assuming starting in a empty folder.

 ```
$ git clone --depth 1 https://github.com/taskrabbit/elasticsearch-dump.git
 ```


 Then get all documents and mapping from your cluster(s) with:

 ```bash
$ `pwd`/elasticsearch-dump/bin/elasticdump \
  --input=http://localhost:9200/my_index \
  --output=/path/to/empty/folder/my_index.json \
  --type=data


 $ `pwd`/elasticsearch-dump/bin/elasticdump \
  --input=http://localhost:9200/my_index \
  --output=/path/to/empty/folder/my_index_mapping.json \
  --type=mapping
 ``` 
 
 * `--input` should be the url to your Elasticsearch index
 * `--output` should be the path to your intially empty folder



<a id="parsing"></a>
#### 2. **Parse the ES-documents to Vespa-documents and generate an Application Package**

 Download ES_Vespa_parser.py [here](https://github.com/vespa-engine/vespa/tree/master/config-model/src/main/python), and place it in your intitially empty directory.
 
 **Usage:**
 
 ```
$ ES_Vespa_parser.py [-h] [--application_name APPLICATION_NAME] documents_path mappings_path
 ```
 
Run this command in your folder to parse the documents, so that it can be feeded to Vespa:

 ```
$ python ES_Vespa_parser.py my_index.json my_index_mapping.json
 ```

* `--application_name` defaults to "application_name" - just change if you want
	* The document ids will become *id:`application_name`:`doc_name`::`elasticsearch_id`*



The directory has now a folder `application`:


 ```
/application
      │     
      ├── documents.json
      ├── hosts.xml
      ├── services.xml
      └── /searchdefinitions
            ├── sd1.sd
            └── ... 
 ``` 
 Which contains your converted documents, their search definitions, a hosts.xml and a services.xml - a whole application package.



<a id="deploy"></a>
#### 3. **Deploying Vespa:**

 Go into your initially empty folder. This tutorial have been tested with a Docker container with 10GB RAM.
 We will map the this directory into the /app directory inside the Docker container. Now, to start the Vespa container:
 
 ```bash
 $ docker run -m 10G --detach --name vespa --hostname vespa-es-tutorial \
    --privileged --volume `pwd`:/app \
    --publish 8080:8080 --publish 19112:19112 vespaengine/vespa
 ```
 
 Make sure that the configuration server is running:
 
 ```bash
 $ docker exec vespa bash -c 'curl -s --head http://localhost:19071/ApplicationStatus'
 ```
 
 **Deploy the `application` package:**
 
 ```bash
$ docker exec vespa bash -c '/opt/vespa/bin/vespa-deploy prepare /app/application && \
    /opt/vespa/bin/vespa-deploy activate'
 ``` 

 (or alternatively, run the equivalent commands inside the docker container). After a short while, pointing a browser to [http://localhost:8080/ApplicationStatus](http://localhost:8080/ApplicationStatus) returns JSON-formatted information about the active application. The Vespa node is now configured and ready for use.
 
 For more detailed explanation of deploying application packages read [this](https://docs.vespa.ai/documentation/cloudconfig/application-packages.html#deploy).



 <a id="feeding_vespa"></a>
#### 4. **Feeding the parsed documents to Vespa:**
	
 Send this to Vespa using one of the tools Vespa provides for feeding. In this part of the tutorial, the [Java feeding API](https://docs.vespa.ai/documentation/vespa-http-client.html) is used:
 
 ```bash
$ docker exec vespa bash -c 'java -jar /opt/vespa/lib/jars/vespa-http-client-jar-with-dependencies.jar \
    --verbose --file /app/application/documents.json --host localhost --port 8080'
 ```
 
  You can also inspect the search node state by: `$ docker exec vespa bash -c '/opt/vespa/bin/vespa-proton-cmd --local getState'`


<a id="querying"></a>
#### 5. **Fetching the documents:**

 Fetch documents by document id using the [Document API](https://docs.vespa.ai/documentation/document-api-guide.html):
 
 ```bash
$ curl -s http://localhost:8080/document/v1/application_name/doc_name/docid/elasticsearch_id
 ```
 
 
#### 6. **The first query:**

 Feel free to use our GUI for building queries at [http://localhost:8080/querybuilder/](http://localhost:8080/querybuilder/) (with Vespa-container running) which can help you building queries with e.g. autocompletion of YQL. Also take a look at Vespa's [Search API](https://docs.vespa.ai/documentation/search-api.html).
 

Click for more information about [developing applications](https://docs.vespa.ai/documentation/getting-started-vespa-applications.html) and [application packages](https://docs.vespa.ai/documentation/cloudconfig/application-packages.html) like `application`.

Please take a look at [how to secure your Vespa installation](https://docs.vespa.ai/documentation/securing-your-vespa-installation.html)

<a id="feeding"></a>
## Feeding

Vespa can be feeded with either [*Vespa Http Feeding Client*](https://docs.vespa.ai/documentation/vespa-http-client.html) or using [*Hadoop, Pig, Oozie*](https://docs.vespa.ai/documentation/feed-using-hadoop-pig-oozie.html).

The Vespa Http Feeding Client is a Java API and command line tool to feed document operations to Vespa. The Vespa feedig client allows you to combine high throughput with feedig over HTTP.

#### Enabling in your application

Add the `<document-api>` to a container cluster to enable it to receive documents:

```
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0">

  <container version="1.0" id="default">
     <document-api/>
  </container>

</services>
```

#### Using from the command line
Use the API by running a binary. This binary supports feeding document operations and is installed with Vespa - found at `$VESPA_HOME/lib/jars/vespa-http-client-jar-with-dependencies.jar`.

Example of usage: 

```
$ java -jar $VESPA_HOME/lib/jars/vespa-http-client-jar-with-dependencies.jar --file file.json --host gatewayhost --port 8080
```

__You can also feed Using the Java Vespa Feeding Client API, which you can read more about [here](https://docs.vespa.ai/documentation/vespa-http-client.html), where you also can find sample code.__


<a id="tutorials"></a>
## Tutorials

For more experience with the Vespa Platform, feel free to do one of Vespas tutorials:

* [Quick Start](https://docs.vespa.ai/documentation/vespa-quick-start.html) : 
This guide describes how to install and run Vespa on a single machine using Docker.

* [Vespa tutorial pt. 1: Blog searching](https://docs.vespa.ai/documentation/tutorials/blog-search.html) : Create a basic search engine application from scratch

* [Vespa tutorial pt. 2: Blog recommendation](https://docs.vespa.ai/documentation/tutorials/blog-recommendation.html) : Extends the basic search engine to include machine learned models to help us recommend blog posts to users that arrive at our application.

* [Vespa tutorial pt. 3: Blog recommendation with Neural Network models](https://docs.vespa.ai/documentation/tutorials/blog-recommendation-nn.html) : Show how to deploy neural network models in Vespa using our Tensor Framework.


<a id="help"></a>
## Help
If you find errors, spelling mistakes, faulty pieces of code or want to improve the migration tutorial, please submit a pull request or create an <a href="https://github.com/vespa-engine/vespa/issues">issue</a>
