---
# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa tutorial pt. 1: Blog searching"
---

* TOC
{:toc}


## Introduction

This is the first of a series of tutorials where data from WordPress.com (WP)
will be used to highlight how Vespa can be used to store, search and recommend
blog posts. The data was made available during a [Kaggle
challenge](https://www.kaggle.com/c/predict-wordpress-likes) to predict which
blog posts someone would like based on their past behavior. It contains many
ingredients that are necessary to showcase needs, challenges and possible
solutions that are useful for those interested in building and deploying such
applications in production.

At any given time, Vespa will store a set of documents (also called a content
pool), which in this case is formed by the blog posts available. Our end goal
with this series of tutorials is to build an application where:

1. Users will be able to search and manipulate the pool of blog posts
   available.
1. Users will get blog post recommendations from the content pool based on
   their interest.

This tutorial will address:

- How to describe the dataset used as well as any information connected to the data
  that we consider relevant to this tutorial.
- How to set up a basic blog post search engine using Vespa.

The next tutorial will show how to extend this basic search engine application
with machine learned models to create a blog recommendation engine.


## Dataset

The dataset used throughout these tutorials contains blog posts written by WP
bloggers and actions, in this case 'likes', performed by WP readers in blog
posts they have interacted with. The dataset is [publicly available at
Kaggle](https://www.kaggle.com/c/predict-wordpress-likes/data) and was
released during a challenge to develop algorithms to help predict which blog
posts users would most likely 'like' if they were exposed to them. In the
following is a short description of the data that we will use.

From the content side, the data includes these fields per blog post:

<table class="table">
<thead></thead><tbody>
<tr><th>post_id</th><td>unique numerical id identifying the blog post</td></tr>
<tr><th>date_gmt</th><td>string representing date of blog post creation in GMT format <em>yyyy-mm-dd hh:mm:ss</em></td></tr>
<tr><th>author</th><td>unique numerical id identifying the author of the blog post</td></tr>
<tr><th>url</th><td>blog post URL</td></tr>
<tr><th>title</th><td>blog post title</td></tr>
<tr><th>blog</th><td>unique numerical id identifying the blog that the blog post belongs to</td></tr>
<tr><th>tags</th><td>array of strings representing the tags of the blog posts</td></tr>
<tr><th>content</th><td>body text of the blog post, in html format</td></tr>
<tr><th>categories</th><td>array of strings representing the categories the blog post was assigned to</td></tr>
</tbody>
</table>

For the user actions:

<table class="table">
<thead></thead><tbody>
<tr><th>post_id</th><td>unique numerical id identifying the blog post</td></tr>
<tr><th>uid</th><td>unique numerical id identifying the user that liked <strong>post_id</strong></td></tr>
<tr><th>dt</th><td>date of the interaction in GMT format <em>yyyy-mm-dd hh:mm:ss</em></td></tr>
</tbody>
</table>


### Downloading raw data

For the purposes of this tutorial, it is sufficient to use the first release of
training data that consists of 5 weeks of posts as well as all the "like"
actions that occurred during those 5 weeks.

[This first release of training data is available
here](https://www.kaggle.com/c/predict-wordpress-likes/download/trainPosts.zip),
but only for logged-in users of Kaggle; you will need to make an account or
log in using your account on one of the supported digital identity platforms 
(Facebook, Google, Yahoo) to be able to download the file.

Once you have the zip file downloaded, unzip it. The 1,196,111 line
trainPosts.json will be our practice document data. This file is around 5GB in size.


## Dataset & Resource usage

Indexing the full data set requires 23GB disk space.
These tutorials have been tested with a Docker container with 10GB RAM.
We used similar settings as described in the
[vespa quick start guide](../vespa-quick-start.html).
As in the guide we assume that the $VESPA_SAMPLE_APPS env variable points
to the directory with your local clone of the
[vespa sample apps](https://github.com/vespa-engine/sample-apps).
``bash
$ docker run -m 10G --detach --name vespa --hostname vespa-tutorial --privileged \
  --volume $VESPA_SAMPLE_APPS:/vespa-sample-apps --publish 8080:8080 vespaengine/vespa
``


## Searching blog posts

This tutorial provides an overview of the major features of Vespa. The
objective is to build a Vespa based blog post search engine application.
Functional specification:

- Blog post title, content, tags and categories must all be searchable
- Allow blog posts to be sorted by both relevance and date
- Allow grouping of search results by tag or category

In terms of data, Vespa operates with the notion of documents. A document
represents a single, searchable item in your system, e.g., a blog post, a
Flickr photo, or a Yahoo News article. Each document type must be defined in
your Vespa configuration through a *search definition*. You can think of a
search definition as being similar to a table definition in a relational
database; it consists of a set of fields, each with a given name, a specific
type, and some optional properties.

As an example, for this simple blog post search application, we could create the document
type `blog_post` with the following fields:

<dl class="dl-horizontal">
  <dt>url</dt> <dd>of type uri</dd>
  <dt>title</dt> <dd>of type string</dd>
  <dt>content</dt> <dd>of type string (string fields can be of any length)</dd>
  <dt>date_gmt</dt> <dd>of type string (to store the creation date in GMT format)</dd>
</dl>

The data fed into Vespa must match the structure of the search definition,
and the hits returned when searching will be on this format as well.


## Application Packages

A Vespa [application package](../cloudconfig/application-packages.html)
is the set of configuration files and Java plugins that together
define the behavior of a Vespa system: what functionality to use, the
available document types, how ranking will be done and how data will be
processed during feeding and indexing.
A _search definition_, e.g., `blog_post.md`, is a required part of an application package —
the other required files are `services.xml` and `hosts.xml`.

The sample application [blog search](https://github.com/vespa-engine/vespa/tree/master/sample-apps/blog-search)
creates a simple but functional blog post search engine. The application
package is found in
[src/main/application](https://github.com/vespa-engine/sample-apps/tree/master/blog-search/src/main/application).


### Services Specification

[services.xml](../reference/services.html) defines the services that make up the Vespa application — which
services to run and how many nodes per service:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<services version='1.0'>

  <container id='default' version='1.0'>
    <search/>
    <document-api/>
    <nodes>
      <node hostalias='node1'/>
    </nodes>
  </container>

  <content id='blog_post' version='1.0'>
    <search>
      <visibility-delay>1.0</visibility-delay>
    </search>
    <redundancy>1</redundancy>
    <documents>
      <document mode='index' type='blog_post'/>
    </documents>
    <nodes>
      <node hostalias='node1'/>
    </nodes>
    <engine>
      <proton>
        <searchable-copies>1</searchable-copies>
      </proton>
    </engine>
  </content>

</services>
```

`<container>` defines the [container](../jdisc/index.html) cluster for document, query and result processing:  
`<search>` sets up the _search_ endpoint for Vespa queries. The default port for both is 8080.  
`<document-api>` sets up the _document_ endpoint for feeding.  
`<nodes>` defines the nodes required per service.
(See the [reference](../reference/services-container.html) for more on container cluster setup.)

`<content>` defines how documents are stored and searched within Vespa:  
`<redundancy>` denotes how many copies to keep of each document.  
`<documents>` assigns the document types in the _search definition_ —
setting the `mode` attribute to `index` for the document type enables indexed search
(as opposed to [streaming search](../streaming-search.html)).
The content cluster capacity can be increased by adding node elements — see
[elastic Vespa](../elastic-vespa.html). (See also the [reference](../reference/services-content.html) for more on content cluster setup.)  
`<nodes>` defines the hosts for the content cluster.

### Deployment Specification

[hosts.xml](../reference/hosts.html) contains a list of all the hosts/nodes that is part of
the application, with an alias for each of them.
This tutorial uses a single node:
```xml
<?xml version="1.0" encoding="utf-8" ?>
<hosts>
  <host name="localhost">
    <alias>node1</alias>
  </host>
</hosts>
```

### Search Definition

The `blog_post` document type mentioned in `src/main/application/service.xml` is defined in a
[search definition](../search-definitions.html). `src/main/application/searchdefinitions/blog_post.sd`
contains the search definition for a document of type `blog_post`:

    search blog_post {

        document blog_post {

            field date_gmt type string {
                indexing: summary
            }

            field language type string {
                indexing: summary
            }

            field author type string {
                indexing: summary
            }

            field url type string {
                indexing: summary
            }

            field title type string {
                indexing: summary | index
            }

            field blog type string {
                indexing: summary
            }

            field post_id type string {
                indexing: summary
            }

            field tags type array<string> {
                indexing: summary
            }

            field blogname type string {
                indexing: summary
            }

            field content type string {
                indexing: summary | index
            }

            field categories type array<string> {
                indexing: summary
            }

            field date type int {
                indexing: summary | attribute
            }

        }


        fieldset default {
            fields: title, content
        }


        rank-profile post inherits default {

            first-phase {
                expression:nativeRank(title, content)
            }

        }

    }

`document` is wrapped inside another element called `search`.
The name following these elements, here `blog_post`, must be exactly the same for both.

The field property `indexing` configures the _indexing pipeline_ for a field,
which defines how Vespa will treat input during indexing — see
[indexing language](../reference/advanced-indexing-language.html).
Each part of the indexing pipeline is separated by the pipe character '|', and the two keywords
used above — `index` and `summary` — are the most common ones:

- `index:` Create a search index for this field
- `attribute:` Store this field in memory as an [attribute](../attributes.html)
  — for [sorting](../reference/sorting.html),
    [searching](../search-api.html) and [grouping](../grouping.html)
- `summary:` Let this field be part of the
    [document summary](../document-summaries.html) in the result set


## Deploy the Application Package

Once done with the application package, deploy the Vespa application —
build and start Vespa as in the [quick start](../vespa-quick-start.html).
We assume that the vespa source code repository is mounted at /vespa-sample-apps as in the quick start guide.
Deploy the application:

    $ cd /vespa-sample-apps/blog-search
    $ vespa-deploy prepare src/main/application && vespa-deploy activate

This prints that the application was activated successfully and also
the checksum, timestamp and generation for this deployment (more on that later).
Pointing a browser to
[http://localhost:8080/ApplicationStatus](http://localhost:8080/ApplicationStatus)
returns JSON-formatted information about the active application, including its checksum,
timestamp and generation (and should be the same as the values when `vespa-deploy activate` was run).
The generation will increase by 1 each time a new application is successfully deployed,
and is the easiest way to verify that the correct version is active.

The Vespa node is now configured and ready for use, so it is time to feed it some data.


## Feeding Data

As mentioned before, the data fed to Vespa must match the search definition for
the document type. The data downloaded from Kaggle, contained in
<em>trainPosts.json</em>, must be converted to a valid Vespa document format
before it can be fed to Vespa. Find a parser in the [utility
repository](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared)
for this tutorial. Since the full data set is unnecessarily large for the purposes
of this first part of the tutorial, we use only the first 10,000 lines of it, 
but feel free to load all 1,1M entries if you prefer:

    $ head -10000 trainPosts.json > trainPostsSmall.json
    $ python parse.py trainPostsSmall.json > tutorial_feed.json

With Vespa-compatible data, send this to Vespa using one of the tools Vespa
provides for feeding.  In this part of the tutorial, the [Java feeding
API](../vespa-http-client.html) is used, which is suitable for most
applications requiring high thoughput.

    $ java -jar $VESPA_HOME/lib/jars/vespa-http-client-jar-with-dependencies.jar --verbose --file tutorial_feed.json --host localhost --port 8080

Note that in the sample-apps/blog-search directory, there is a file with sample data. You
may also feed this file using this method.

### Track feeding progress

Use the [Metrics API](../reference/metrics-health-format.html) to track
number of documents indexed:

    $ curl -s 'http://localhost:19112/state/v1/metrics' | tr ',' '\n' | grep -A 2 proton.doctypes.blog_post.numdocs

You can also inspect the search node state by 
 
    $ vespa-proton-cmd --local getState  

### Fetch documents

Although searching is the most useful way to access the documents, one can
fetch documents by document id using the [Document API](../api.html):

    $ curl -s 'http://localhost:8080/document/v1/blog-search/blog_post/docid/1750271' | python -m json.tool


## The first query

Searching with Vespa is done using a simple HTTP interface, with basic GET requests.
The general form of an unstructured search request is:

    <host>/<templatename>?<param1=value1>&<param2=value2>...

The template name is optional. The only mandatory parameter is the *query* itself,
given with `query=<query string>` for the *simple* query language, or with
`yql=<yql query>` when using the *advanced* query syntax.

- The *simple* query language is intended to be usable directly by end users,
  and provides a somewhat simplistic interface to Vespa.
- The *advanced* query syntax is intended for programmatic use, and is the 
  syntax we use in these tutorials. It uses the YQL query language.

More details can be found in the [Search API](../search-api.html).

### Simple query language examples

Given the above search definition, where the fields `title` and `content` are part of the
`field set default`, any document containing the word "music" in one or more of these two
fields matches our query below:

    $ curl -s 'http://localhost:8080/search/?query=music' | python -m json.tool

Looking at the output, please note:

- The field `documentid` in the output and how it matches the value
  we assigned to each put operation when feeding data to Vespa.
- Each hit has a property named relevance, which indicates how well the given
  document matches our query, using a pre-defined default ranking function. You
  have full control over ranking — more about ranking and ordering later. The
  hits are sorted by this value.
- When multiple hits have the same relevance score their internal ordering is
  undefined. However, their internal ordering will not change unless the
  documents are re-indexed.

### Advanced query syntax examples

If you add `&tracelevel=2` to the end of the simple query above, you will see
the query is parsed 

    $ curl -s 'http://localhost:8080/search/?query=music&tracelevel=2' | python -m json.tool | grep Query
    "message": "Query parsed to: select * from sources * where default contains \"music\";"

which can also be written in YQL as:

    $ curl -s 'http://localhost:8080/search/?yql=select+*+from+sources+*+where+default+contains+%22music%22%3B' | python -m json.tool

### Other examples

    yql=select+title+from+sources+*+where+title+contains+%22music%22%3B

Once more a search for the single term "music", but this time with the explicit
field `title`. This means that we only want to match documents that contain the
word "music" in the field `title`. If you try this query right now you will see
that the number of documents returned will be different from the previous query.

    yql=select+*+from+sources+*+where+default+contains+%22music%22+AND+default+contains+%22festival%22%3B

A query for the two terms "music" and "festival", combined with an `AND`
operation. So it will find documents that match both terms, but not just one of them.

    yql=select+*+from+sources+*+where+sddocname+contains+%22blog_post%22%3B

This is a single-term query in the special field `sddocname` for the value "blog_post".
This is a common and useful Vespa trick to get the number of
indexed documents for a certain document type (search definition): 
`sddocname` is a special and reserved field which is always set to the name of
the document type for a given document. Our 1196 documents are all of type `blog_post`,
and will therefore automatically have the field sddocname set to that value.

This means that the query above really means "Return all documents of type blog_post",
and as such all 1196 documents in our index will be returned.

Refer to the [Search API](../search-api.html) for more information.


## Relevance and Ranking

Ranking and relevance were briefly mentioned above;
what is really the relevance of a hit,
and how can one change the relevance calculations?
It is time to introduce _rank profiles_ and _rank expressions_ —
simple, yet powerful methods for tuning the relevance.

Relevance is a measure of how well a given document matches a query.
The default relevance is calculated by a formula that takes several factors into consideration,
but it computes, in essence, how well the document matches the terms in the query.

When building specialized applications using Vespa,
there are use cases for tweaking the relevance calculations:

- Personalize search results based on some property; age, nationality,
  language, friends and friends of friends, and so on.
- Rank fresh (age) documents higher, while still considering other relevance measures.
- Rank documents by geographical location, searching for relevant resources nearby.

Vespa allows creating any number of _rank profiles_:
named collections of ranking and relevance calculations that one can choose from at query time.
A number of built-in functions and expressions are available to create highly specialized rank expressions.

### Blog popularity signal

It is time to include the notion of blog popularity into the ranking function.
Do this by including the `post_popularity` rank profile below at the bottom of
`src/main/application/searchdefinitions/blog_post.sd`, just below the `post` rank profile.

        rank-profile post_popularity inherits default {

            first-phase {
                expression: nativeRank(title, content) + 10 * if(isNan(attribute(popularity)), 0, attribute(popularity))
            }

        }


Also, add a `popularity` field at the end of the `document` definition:

            field popularity type double {
                indexing: summary | attribute
            }

Notes (more information can be found in the
[search definition reference](../reference/search-definitions-reference.html#rank-profile)):

- `rank-profile post_popularity inherits default`

  This configures Vespa to create a new rank profile named `post_popularity`,
  which inherits all the properties of the default rank-profile;
  only properties that are explicitly defined, or overridden, will differ
  from those of the default rank-profile.

- `first-phase`

  Relevance calculations in Vespa are two-phased. The calculations done in the
  first phase are performed on every single document matching your query,
  while the second phase calculations are only done on the top n documents
  as determined by the calculations done in the first phase.

- `expression: nativeRank(title, content) + 10 * if(isNan(attribute(popularity)), 0, attribute(popularity))`

Still using the basic search relevance for title and content,
boosting documents based on some document level popularity signal.

  This expression is used to rank documents. Here, the default ranking expression —
  the `nativeRank` of the `default` field set — is included to make the query
  relevant, while the custom, second term includes the document value `attribute(popularity)`, 
  if this is set. The weighted sum of these two terms is the final relevance for each document.

Deploy the configuration:

    $ vespa-deploy prepare src/main/application && vespa-deploy activate

Use [parse.py](https://github.com/vespa-engine/sample-apps/blob/master/blog-tutorial-shared/src/python/parse.py) —
which has a `-p` option to calculate and add a `popularity` field — and then feed the parsed data:

    $ python parse.py -p trainPostsSmall.json > tutorial_feed_with_popularity.json
    $ java -jar $VESPA_HOME/lib/jars/vespa-http-client-jar-with-dependencies.jar --file tutorial_feed_with_popularity.json --host localhost --port 8080

After feeding, query

    $ curl -s 'http://localhost:8080/search/?query=music&ranking=post_popularity' | python -m json.tool

and find documents with high `popularity` values at the top.


## Sorting and Grouping

### What is an attribute?

An [_attribute_](../attributes.html) is an in-memory field,
which means that Vespa keeps the contents of the field in memory at all times;
this behavior is different from that of regular _index_ fields,
which may be moved to a disk-based index as more documents are added and the index grows. 
Since attributes are kept in memory, they are excellent for fields which
require fast access, e.g., fields used for sorting or grouping query results.
The downside is that they make Vespa use more memory per document.
Thus, by default, no index is generated for attributes, and search over
these defaults to a linear scan. To build and index for an attribute field,
include `attribute:fast-search` in the field definition.

### Defining an attribute field

A field with indexing attribute will be present in memory at all time for very
fast access; an example is found in `blog_post.sd`:

    field date type int {
        indexing: summary | attribute
    }

The data has format YYYYMMDD. And since the field is an `int`, it can be used for
[range searches](#range-searches).

### Example queries using attribute field

    yql=select+*+from+sources+*+where+default+contains+%2220120426%22%3B

A single-term query for the term _20120426_ in the _default_ field set.
Inspecting the search definition, the field `date` is not included in the `default` field set.
As such, this query will has 0 results:

    yql=select+*+from+sources+*+where+date+contains+%2220120426%22%3B

Another single-term query for the term _20120426_, but this time restricted to
the field named `date`. This query will find all documents in the document
corpus that have the field `date` set to the value _20120426_, that is,
all documents from April 26th of 2012.
Note that since `date` has not been defined with `attribute:fast-search`,
searching will be done by scanning *all* documents.

    yql=select+*+from+sources+*+where+default+contains+%22recipe%22+AND+date+contains+%2220120416%22%3B

A query with two terms; a search in the `default` field set for the term
"recipe" combined with a search in the `date` field for the term _20120416_.
There's a lot of recipes in the test data.
This query will return only the one posted on April 16. 2012.
This search will be faster than the previous example as the query term _recipe_
is using a field which has an index and the search core will try to evaluate that query term first.

### Range searches

The examples above searched `date` just as  any other field, and
requested documents where the value was exactly _20120426_ or exactly _20120416_.
But since the field is defined as being of type int,
Vespa is aware that any value found here is an integer.
We can use this to our advantage and do range searches using the less than and greater than operators
(these symbols have been URL encoded into %3C and %3E, respectively):

    yql=select+*+from+sources+*+where+date+%3C+20120401%3B

Find all documents where the value of `date` is less than _20120401_; all
documents from before April of 2012:

    yql=select+*+from+sources+*+where+date+%3E+20120401%3B

Find all documents where the value of `date` is greater than _20120401_; all
documents submitted after April 1st 2012.

### Sorting

The first feature we will look at is how an attribute can be used to change the
order of the hits that are returned when you do a query. Remember our original
query for "music AND festival"? We got seven document hits, and — only considering
date and relevance for each document — the output and order looks like this:

    {...
        "relevance": 0.261262217185,
        "fields": {...
            "date": **20120409**
        }
    },
    {...
        "relevance": 0.126084565522,
        "fields": {...
            "date": **20120410**
        }
    },
    {...
        "relevance": 0.0871006875725,
        "fields": {...
            "date": **20120417**
        }
    },
    {...
        "relevance": 0.0864373902049,
        "fields": {...
            "date": **20120409**
        }
    },
    {...
        "relevance": 0.0864092913995,
        "fields": {...
            "date": **20120326**
        }
    },
    {...
        "relevance": 0.0560099448101,
        "fields": {...
            "date": **20120406**
        }
    },
    {...
        "relevance": 0.055545350117,
        "fields": {...
            "date": **20120424**
        }
    }

The hits are sorted by relevance; the better the document matched our query,
the higher the relevance, and the higher up in the list of hits.
Now try to send the following query to Vespa and look at the order of the hits:

    $ curl -s 'http://localhost:8080/search/?yql=select+*+from+sources+*+where+default+contains+%22music%22+AND+default+contains+%22festival%22+order+by+date%3B' | python -m json.tool

Adding the keyword `desc` after the attribute name leads to sorting in
descending order, while omitting the keyword (or using `asc`) sorts the results
in ascending order.

    $ curl -s 'http://localhost:8080/search/?yql=select+*+from+sources+*+where+default+contains+%22music%22+AND+default+contains+%22festival%22+order+by+date+desc%3B' | python -m json.tool

### Query time data grouping

*Grouping* is the concept of looking through all matching documents at
query-time and then performing a set of operations on the data in specific
fields across all the documents — some common use cases include:

- Find all the unique values for a given field, make **one group per unique
  value**, and return the count of documents per group
- **Group documents by time and date** in fixed-width or custom-width buckets.
  An example of fixed-width buckets could be to group all documents by year,
  while an example of custom buckets could be to sort bug tickets by date of
  creation into the buckets *Today*, *Past Week*, *Past Month*, *Past Year*,
  and *Everything else*
- Calculate the **minimum/maximum/average value** for a given field

Displaying such groups and their size (in terms of matching documents per
group) on a search result page (SERP), is a common way to let end-users refine
and narrow down their search by clicking on a single link.

For now we will only do a very simple grouping query to get a list of unique
values for `date` ordered by the number of documents they occur in and top 3 is
shown:

    curl -s 'http://localhost:8080/search/?yql=select%20*%20from%20sources%20*%20where%20sddocname%20contains%20%22blog_post%22%20limit%200%20%7C%20all(group(date)%20max(3)%20order(-count())each(output(count())))%3B' | python -m json.tool

You then get the following output:

    {
        "root": {
            "children": [
                {
                    "children": [
                        {
                            "children": [
                                {
                                    "fields": {
                                        "count()": 43
                                    },
                                    "id": "group:long:20120419",
                                    "relevance": 1.0,
                                    "value": "20120419"
                                },
                                {
                                    "fields": {
                                        "count()": 40
                                    },
                                    "id": "group:long:20120424",
                                    "relevance": 0.6666666666666666,
                                    "value": "20120424"
                                },
                                {
                                    "fields": {
                                        "count()": 39
                                    },
                                    "id": "group:long:20120417",
                                    "relevance": 0.3333333333333333,
                                    "value": "20120417"
                                }
                            ],
                            "continuation": {
                                "next": "BGAAABEBGBC"
                            },
                            "id": "grouplist:date",
                            "label": "date",
                            "relevance": 1.0
                        }
                    ],
                    "continuation": {
                        "this": ""
                    },
                    "id": "group:root:0",
                    "relevance": 1.0
                }
            ],
            "coverage": {
                "coverage": 100,
                "documents": 1000,
                "full": true,
                "nodes": 0,
                "results": 1,
                "resultsFull": 1
            },
            "fields": {
                "totalCount": 1000
            },
            "id": "toplevel",
            "relevance": 1.0
        }
    }

As you can see, the three most common unique values of `date` are listed, along
with their respective counts.

Try to change the filter part of the YQL+ expression to text match of "recipe"
or numeric match of `date` to less than 20120401 and see how the list of unique
values changes as the set of matching documents for your query changes. Try to
search for the single-term "Verizon" as well — a word we know is *not* present
in our document set, and as such will not match any documents — and you will
see that the list of groups is empty.

### Attribute limitations

#### Memory usage

The attributes are kept in memory at all time —
as opposed to normal indexes where the data is mostly kept on disk.
So even with large search nodes, one will notice that it is not
practical to define all the search definition fields as attributes,
as it will heavily restrict the number of documents per search node.
Some Vespa installations have more than 1 billion documents per node —
having megabytes of text in memory per document is not an option.

#### Matching

Another limitation is the way so-called *matching* is done for attributes.
Consider the field `blogname` from our search definition, and the document for
the blog called "Thinking about museums". In our original input, the value for
`blogname` is a string built of up the three words "Thinking", "about", and
"museums", with a single whitespace character between them. How should we be
able to search this field?

For normal index fields, Vespa does something called tokenization on the
string. In our case this means that the string above is split into the three
tokens "Thinking", "about" and "museums", enabling Vespa to match this document
both for the single-term queries "Thinking", "about" and "museums", the exact
phrase query "Thinking about museums", and a query with two or more tokens in
either order (e.g. "museums thinking"). This is how we all have come to expect
normal free text search to work.

As mentioned there is however a limitation in Vespa when it comes to attribute
fields and matching. Attributes do not support normal token-based matching,
only *exact matching* or *prefix matching*. Exact matching is the default, and
as the name implies it requires you to search for the exact contents of the
field in order to get a match.

### When to use attributes

There are both advantages and drawbacks of using attributes —
it enables sorting and grouping, but uses
more memory and has limited matching capabilities. When to use
attributes depends on the application, in general the following applies:

- When sorting the results by a field, e.g. a last update timestamp
- A field included in grouping
- If the fields are not very long string fields
- All numeric type fields must always be attributes


## Clean environment by removing all documents

[vespa-remove-index](../reference/vespa-cmdline-tools.html#vespa-remove-index)
removes all documents:

    $ vespa-stop-services
    $ vespa-remove-index
    $ vespa-start-services


## Conclusion

This concludes the basic Vespa tutorial. You should now have a basic
understanding of how Vespa can help build your application. In the
[next part of the tutorial](blog-recommendation.html)
we will proceed to show how can we use Statistics and Machine
Learning to extend a basic search application into a recommendation system.

