---
# Copyright Vespa.ai. All rights reserved.
title: "Re-ranking using a custom Searcher"
redirect_from:
  - /en/reranking-in-searcher
---

This guide demonstrates how to deploy a [searcher](../applications/searchers.html) 
implementing a last stage of [phased ranking](phased-ranking.html). The searcher re-ranks the 
global top 200 documents which have been ranked by the content nodes using the configurable [ranking](ranking-intro)
specification in the document [schema(s)](../basics/schemas.html).  

The reranking searcher uses [multiphase searching](../applications/searchers.html#multiphase-searching):

**Matching query protocol phase:** The matching protocol phase which asks each content node involved in the query
to return the locally best ranking hits (ranked by the configurable ranking expressions defined in the schema).
This matching query protocol phase can include several ranking phases which are executed per content node. 
In the query protocol phase the content nodes can also return [match-features](../reference/schemas/schemas.html#match-features) which
a re-ranking searcher can use to re-rank results (or feature logging). 
In the custom searcher one is working on the global best ranking hits from the content nodes, and
can have access to aggregated features which is calculated across the top-ranking documents (the global best documents).

**Fill query protocol phase:** Fill summary data for the global top ranking hits after all ranking phases.
If one needs access to the document fields,
the searcher would need to call `execution.fill` before the re-ranking logic,
this would then cost more resources
than just using `match-features` which is delivered in the first protocol matching phase.
If one needs access to a subset of fields during stateless re-ranking,
consider configuring a dedicated [document summary](../querying/document-summaries.html).

See also [life of a query in Vespa](../performance/sizing-search.html#life-of-a-query-in-vespa).

{% include pre-req.html memory="4 GB" extra-reqs='
<li><a href="https://openjdk.org/projects/jdk/17/" data-proofer-ignore>Java 17</a>.</li>
<li><a href="https://maven.apache.org/install.html">Apache Maven</a> is used to build the application.</li>' %}


### A minimal Vespa application

To define the Vespa app package using our custom reranking searcher, four files is needed:

- The schema
- The deployment specification `services.xml`
- The custom reranking searcher
- [pom.xml](https://maven.apache.org/guides/introduction/introduction-to-the-pom.html)

Start by defining a simple schema with two fields.
We also define a rank profile with two [rank features](../reference/ranking/rank-features.html)
to be used in the searcher for re-ranking:

<pre data-test="file" data-path="my-app/src/main/application/schemas/doc.sd">{% highlight vespa-schema-language %}
 
schema doc {

    document doc {
        field name type string {
            indexing: summary | index
            match: text 
            index: enable-bm25
        }

        field downloads type int {
            indexing: summary | attribute
        }
    }

    fieldset default {
        fields: name 
    }

    rank-profile rank-profile-with-match {
        first-phase {
            expression: bm25(name) 
        }
        match-features {
            bm25(name)
            attribute(downloads)
        }
    }
}
{% endhighlight %}</pre>

The searcher implementing the re-ranking logic:

<pre data-test="file" data-path="my-app/src/main/java/ai/vespa/example/searcher/ReRankingSearcher.java">{% highlight java %}
package ai.vespa.example.searcher;

import com.yahoo.search.Query;
import com.yahoo.search.Result;
import com.yahoo.search.Searcher;
import com.yahoo.search.result.FeatureData;
import com.yahoo.search.result.Hit;
import com.yahoo.search.searchchain.Execution;

public class ReRankingSearcher extends Searcher {
    @Override
    public Result search(Query query, Execution execution) {
        int hits = query.getHits();
        query.setHits(200); //Re-ranking window
        query.getRanking().setProfile("rank-profile-with-match");
        Result result = execution.search(query);
        if(result.getTotalHitCount() == 0
                || result.hits().getErrorHit() != null)
            return result;
        double max = 0;
        //Find max value of the window
        for (Hit hit : result.hits()) {
            FeatureData featureData = (FeatureData) hit.getField("matchfeatures");
            if(featureData == null)
                throw new RuntimeException("No 'matchfeatures' found - wrong rank profile used?");
            double downloads = featureData.getDouble("attribute(downloads)");
            if (downloads > max)
                max = downloads;
        }
        //re-rank using normalized value
        for (Hit hit : result.hits()) {
            FeatureData featureData = (FeatureData) hit.getField("matchfeatures");
            if(featureData == null)
                throw new RuntimeException("No 'matchfeatures' found - wrong rank profile used?");
            double downloads = featureData.getDouble("attribute(downloads)");
            double normalizedByMax = downloads / max; //Change me
            double bm25Name = featureData.getDouble("bm25(name)");
            double newScore = bm25Name + normalizedByMax;
            hit.setField("rerank-score",newScore);
            hit.setRelevance(newScore);
        }
        result.hits().sort();
        //trim the result down to the requested number of hits
        result.hits().trim(0, hits);
        return result;
    }
}
{% endhighlight %}</pre>

[services.xml](../reference/applications/services/services.html) is needed 
to make up a Vespa [application package](../reference/applications/application-packages.html). 
Here we include the custom searcher in the `default` [search chain](../applications/chaining.html):

<pre data-test="file" data-path="my-app/src/main/application/services.xml">{% highlight xml %}
<?xml version="1.0" encoding="utf-8" ?>
<services version="1.0" xmlns:deploy="vespa" xmlns:preprocess="properties">
    <container id="default" version="1.0">
        <document-api/>
        <search>
            <chain id="default" inherits="vespa">
                <searcher id="ai.vespa.example.searcher.ReRankingSearcher" bundle="ranking"/>
            </chain>
        </search>
        <nodes>
            <node hostalias="node1" />
        </nodes>
    </container>

    <content id="docs" version="1.0">
        <redundancy>2</redundancy>
        <documents>
            <document type="doc" mode="index" />
        </documents>
        <nodes>
            <node hostalias="node1" distribution-key="0" />
        </nodes>
    </content>
</services>
{% endhighlight %}</pre>

Notice the `bundle` name of the searcher, this needs to be in synch with the `artifactId` defined in `pom.xml`: 

<pre data-test="file" data-path="my-app/pom.xml">{% highlight xml %}
<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
                             http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>ai.vespa.example</groupId>
    <artifactId>ranking</artifactId>  <!-- Note: When changing this, also change bundle names in services.xml -->
    <version>1.0.0</version>
    <packaging>container-plugin</packaging>
    <parent>
        <groupId>com.yahoo.vespa</groupId>
        <artifactId>cloud-tenant-base</artifactId>
        <version>[7,999)</version>  <!-- Use the latest Vespa release on each build -->
        <relativePath/>
    </parent>
    <properties>
        <bundle-plugin.failOnWarnings>true</bundle-plugin.failOnWarnings>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <test.hide>true</test.hide>
    </properties>
</project>
{% endhighlight %}</pre>


### Starting Vespa
Now, we have the files and can start Vespa:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ docker pull vespaengine/vespa
$ docker run --detach --name vespa --hostname vespa-container \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa
</pre>
</div>

Install [vespa-cli](../clients/vespa-cli.html) using Homebrew:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre>
$ brew install vespa-cli
</pre>
</div>

Build the Maven project, this step creates the application package including the custom searcher:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ (cd my-app && mvn package)
</pre>
</div>

Deploy the application to Vespa using vespa-cli:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa deploy --wait 300 my-app
</pre>
</div>


### Feed data

Create a few sample docs:

<pre data-test="file" data-path="doc-1.json">{% highlight json %}
{
    "put": "id:docs:doc::0",
    "fields": {
        "name": "A sample document",
        "downloads": 100
    }
}
{% endhighlight %}</pre>

<pre data-test="file" data-path="doc-2.json">{% highlight json %}
{
    "put": "id:docs:doc::1",
    "fields": {
        "name": "Another sample document",
        "downloads": 10
    }
}
{% endhighlight %}</pre>

Feed them using the CLI:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa document doc-1.json && vespa document doc-2.json 
</pre>
</div>

### Query the data
Run a query - this will invoke the reranking searcher since it was included in a the `default` search chain:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains='"totalCount": 2'>
$ vespa query 'yql=select * from doc where userQuery()' \
 'query=sample' 
</pre>
</div>

<pre>{% highlight json %}
{
    "root": {
        "id": "toplevel",
        "relevance": 1.0,
        "fields": {
            "totalCount": 2
        },
        "coverage": {
            "coverage": 100,
            "documents": 2,
            "full": true,
            "nodes": 1,
            "results": 1,
            "resultsFull": 1
        },
        "children": [
            {
                "id": "id:docs:doc::0",
                "relevance": 1.1823215567939547,
                "source": "docs",
                "fields": {
                    "matchfeatures": {
                        "attribute(downloads)": 100.0,
                        "bm25(name)": 0.1823215567939546
                    },
                    "rerank-score": 1.1823215567939547,
                    "sddocname": "doc",
                    "documentid": "id:docs:doc::0",
                    "name": "A sample document",
                    "downloads": 100
                }
            },
            {
                "id": "id:docs:doc::1",
                "relevance": 0.2823215567939546,
                "source": "docs",
                "fields": {
                    "matchfeatures": {
                        "attribute(downloads)": 10.0,
                        "bm25(name)": 0.1823215567939546
                    },
                    "rerank-score": 0.2823215567939546,
                    "sddocname": "doc",
                    "documentid": "id:docs:doc::1",
                    "name": "Another sample document",
                    "downloads": 10
                }
            }
        ]
    }
}
{% endhighlight %}</pre>

<pre style="display:none" data-test="exec" data-test-assert-contains='"rerank-score": 1.18'>
$ vespa query 'yql=select * from doc where userQuery()' \
 'query=sample' 
</pre>

### Teardown
Remove app and data:
<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="after">
$ docker rm -f vespa
</pre>
</div>

<script src="/js/process_pre.js"></script>
