---
# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa tutorial pt. 1: Blog searching"
---

## Introduction

This is the first of a series of tutorials where data from WordPress.com (WP)
is used to highlight how Vespa can be used to store, search and recommend blog posts.
The data was made available during a [Kaggle challenge](https://www.kaggle.com/c/predict-wordpress-likes)
to predict which blog posts someone would like based on their past behavior.
It contains many ingredients that are necessary to showcase needs, challenges and possible
solutions that are useful for those interested in building and deploying such applications in production.

The end goal with these tutorials is to build an application where:

- Users will be able to search and manipulate the pool of blog posts
   available.
- Users will get blog post recommendations from the content pool based on
   their interest.

This tutorial addresses:

- How to describe the dataset used as well as any information connected to the data
  considered relevant to this tutorial.
- How to set up a basic blog post search engine using Vespa.

The next tutorials shows how to extend this basic search engine application
with machine learned models to create a blog recommendation engine.


## Dataset

The dataset contains blog posts written by WP bloggers and actions, in this case 'likes',
performed by WP readers in blog posts they have interacted with.
The dataset is [publicly available at Kaggle](https://www.kaggle.com/c/predict-wordpress-likes/data)
and was released during a challenge to develop algorithms to help predict which blog
posts users would most likely 'like' if they were exposed to them.
The data includes these fields per blog post:

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
training data that consists of 5 weeks of posts as well as all the 'like'
actions that occurred during those 5 weeks.

[This first release of training data is available
here](https://www.kaggle.com/c/predict-wordpress-likes/download/trainPosts.zip) -
once downloaded, unzip it. The 1,196,111 line
trainPosts.json will be our practice document data. This file is around 5GB in size.


### Requirements

Indexing the full data set requires 23GB disk space.
These tutorials have been tested with a Docker container with 10GB RAM.
We used similar settings as described in the
[vespa quick start guide](../vespa-quick-start.html).
As in the guide we assume that the $VESPA_SAMPLE_APPS env variable points
to the directory with your local clone of the
[vespa sample apps](https://github.com/vespa-engine/sample-apps):

    $ docker run -m 10G --detach --name vespa --hostname vespa-tutorial --privileged --volume $VESPA_SAMPLE_APPS:/vespa-sample-apps --publish 8080:8080 vespaengine/vespa



## Searching blog posts

Functional specification:

- Blog post title, content, tags and categories must all be searchable
- Allow blog posts to be sorted by both relevance and date
- Allow grouping of search results by tag or category

In terms of data, Vespa operates with the notion of [documents](../documents.html).
A document represents a single, searchable item in your system, e.g., a blog post, a
photo, or a news article. Each document type must be defined in
the Vespa configuration through a [search definition](../search-definitions.html).
Think of a search definition as being similar to a table definition in a relational database;
it consists of a set of fields, each with a given name, a specific type, and some optional properties.

As an example, for this simple blog post search application, we could create the document
type `blog_post` with the following fields:

<table class="table">
<thead></thead><tbody>
  <tr>
    <th>url</th><td>of type uri</td>
  </tr><tr>
    <th>title</th><td>of type string</td>
    </tr><tr>
    <th>content</th><td>of type string (string fields can be of any length)</td>
    </tr><tr>
    <th>date_gmt</th><td>of type string (to store the creation date in GMT format)</td>
  </tr>
</tbody>
</table>

The data fed into Vespa must match the structure of the search definition,
and the hits returned when searching will be on this format as well.


## Application Packages

A Vespa [application package](../cloudconfig/application-packages.html)
is the set of configuration files and Java plugins that together
define the behavior of a Vespa system: what functionality to use, the
available document types, how ranking will be done and how data will be
processed during feeding and indexing.
The search definition, e.g., `blog_post.sd`, is a required part of an application package —
the other required files are `services.xml` and `hosts.xml`.

The sample application [blog search](https://github.com/vespa-engine/sample-apps/tree/master/blog-search)
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

`<container>` defines the [container](../jdisc/index.html) cluster for document, query and result processing

`<search>` sets up the [search](../search-api.html) endpoint for Vespa queries. The default port is 8080.

`<document-api>` sets up the [document](../document-api.html) endpoint for feeding.

`<nodes>` defines the nodes required per service.
(See the [reference](../reference/services-container.html) for more on container cluster setup.)

`<content>` defines how documents are stored and searched

`<redundancy>` denotes how many copies to keep of each document.

`<documents>` assigns the document types in the _search definition_ —
the content cluster capacity can be increased by adding node elements — see
[elastic Vespa](../elastic-vespa.html). (See also the [reference](../reference/services-content.html) for more on content cluster setup.)

`<nodes>` defines the hosts for the content cluster.

### Deployment Specification

[hosts.xml](../reference/hosts.html) contains a list of all the hosts/nodes that is part of
the application, with an alias for each of them. This tutorial uses a single node:

```xml
<?xml version="1.0" encoding="utf-8" ?>
<hosts>
  <host name="localhost">
    <alias>node1</alias>
  </host>
</hosts>
```

### Search Definition

The `blog_post` document type mentioned in `src/main/application/service.xml` is defined in the
search definition. `src/main/application/searchdefinitions/blog_post.sd`
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
Each part of the indexing pipeline is separated by the pipe character '|':

- `index:` Create a search index for this field
- `attribute:` Store this field in memory as an [attribute](../attributes.html)
  — for [sorting](../reference/sorting.html),
    [searching](../search-api.html) and [grouping](../grouping.html)
- `summary:` Let this field be part of the
    [document summary](../document-summaries.html) in the result set


## Deploy the Application Package

Once done with the application package, deploy the Vespa application —
build and start Vespa as in the [quick start](../vespa-quick-start.html).
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

The Vespa node is now configured and ready for use.


## Feeding Data

The data fed to Vespa must match the search definition for the document type.
The data downloaded from Kaggle, contained in <em>trainPosts.json</em>,
must be converted to a valid Vespa document format before it can be fed to Vespa.
Find a parser in the [utility repository](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared)
for this tutorial. Since the full data set is unnecessarily large for the purposes
of this first part of the tutorial, we use only the first 10,000 lines of it, but feel free to load all 1,1M entries:

    $ head -10000 trainPosts.json > trainPostsSmall.json
    $ python parse.py trainPostsSmall.json > tutorial_feed.json

Send this to Vespa using one of the tools Vespa provides for feeding.
In this part of the tutorial, the [Java feeding API](../vespa-http-client.html) is used:

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

Fetch documents by document id using the [Document API](../api.html):

    $ curl -s 'http://localhost:8080/document/v1/blog-search/blog_post/docid/1750271' | python -m json.tool


## The first query

Searching with Vespa is done using a HTTP GET requests, like:

    <host:port>/<search>?<yql=value1>&<param2=value2>...

The only mandatory parameter is the query, using `yql=<yql query>`.
More details can be found in the [Search API](../search-api.html).

Given the above search definition, where the fields `title` and `content` are part of the
`fieldset default`, any document containing the word "music" in one or more of these two
fields matches our query below:

    $ curl -s 'http://localhost:8080/search/?yql=select+*+from+sources+*+where+default+contains+%22music%22%3B' | python -m json.tool

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
- Add `&tracelevel=9` to dump query parsing details

### Other examples

    yql=select+title+from+sources+*+where+title+contains+%22music%22%3B

Once more a search for the single term "music", but this time with the explicit
field `title`. This means that we only want to match documents that contain the
word "music" in the field `title`. As expected, you will see fewer hits for this
query, than for the previous one. 

    yql=select+*+from+sources+*+where+default+contains+%22music%22+AND+default+contains+%22festival%22%3B

This is a query for the two terms "music" and "festival", combined with an `AND`
operation; it finds documents that match both terms — but not just one of them.

    yql=select+*+from+sources+*+where+sddocname+contains+%22blog_post%22%3B

This is a single-term query in the special field `sddocname` for the value "blog_post".
This is a common and useful Vespa trick to get the number of
indexed documents for a certain document type (search definition): 
`sddocname` is a special and reserved field which is always set to the name of
the document type for a given document. The documents are all of type `blog_post`,
and will therefore automatically have the field sddocname set to that value.

This means that the query above really means "Return all documents of type blog_post",
and as such all documents in the index are returned.


## Relevance and Ranking

[Ranking](../ranking.html) and relevance were briefly mentioned above;
what is really the relevance of a hit,
and how can one change the relevance calculations?
It is time to introduce _rank profiles_ and _rank expressions_ —
simple, yet powerful methods for tuning the relevance.

Relevance is a measure of how well a given document matches a query.
The default relevance is calculated by a formula that takes several factors into consideration,
but it computes, in essence, how well the document matches the terms in the query.
Sample use cases for tweaking the relevance calculations:

- Personalize search results based on some property; age, nationality,
  language, friends and friends of friends.
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

    $ curl -s 'http://localhost:8080/search/?yql=select+*+from+sources+*+where+default+contains+%22music%22%3B&ranking=post_popularity' | python -m json.tool

and find documents with high `popularity` values at the top.


## Sorting and Grouping

### What is an attribute?

An [_attribute_](../attributes.html) is an in-memory field -
this is different from  _index_ fields,
which may be moved to a disk-based index as more documents are added and the index grows. 
Since attributes are kept in memory, they are excellent for fields which
require fast access, e.g., fields used for sorting or grouping query results.
The downside is higher memory usage.
By default, no index is generated for attributes, and search over these defaults to a linear scan -
to build an index for an attribute field, include `attribute:fast-search` in the field definition.

### Defining an attribute field

An example is found in `blog_post.sd`:

    field date type int {
        indexing: summary | attribute
    }

The data has format YYYYMMDD. And since the field is an `int`, it can be used for
[_range searches_](#range-searches).

### Example queries using attribute field

    yql=select+*+from+sources+*+where+default+contains+%2220120426%22%3B

This is a single-term query for the term _20120426_ in the `default` field set.
(The strings `%22` and `%3B` are URL encodings for `"` and `;`.)
In the search definition, the field `date` is not included in the `default` field set.
Nevertheless, the string "20120426" is found in the content of many posts, which
are returned then as results.

    yql=select+*+from+sources+*+where+date+contains+%2220120426%22%3B

To get documents that were created 26 April 2012, and whose `date` field is _20120426_,
replace `default` with `date` in the YQL query string.
Note that since `date` has not been defined with `attribute:fast-search`,
searching will be done by scanning _all_ documents.

    yql=select+*+from+sources+*+where+default+contains+%22recipe%22+AND+date+contains+%2220120426%22%3B

A query with two terms; a search in the `default` field set for the term
"recipe" combined with a search in the `date` field for the value _20120426_.
This search will be faster than the previous example, as the term "recipe"
is for a field for which there is an index, and for which the search core will 
evaluate the query first. (This speedup is only noticeable with the full data set!)

### Range searches

The examples above searched over `date` just as any other field, and
requested documents where the value was exactly _20120426_.
Since the field is of type _int_, however, we can use it for _range searches_
as well, using the "less than" and "greater than" operators
(`<` and `>`, or `%3C` and `%3E` URL encoded). The query

    yql=select+*+from+sources+*+where+date+%3C+20120401%3B

finds all documents where the value of `date` is less than _20120401_, i.e., all
documents from before April 2012, while 

    yql=select+*+from+sources+*+where+date+%3C+20120401+AND+date+%3E+20120229%3B

finds all documents exactly from March 2012.

### Sorting

The first feature we will look at is how an attribute can be used to change the hit order.
By now, you have probably noticed that hits are returned in order of descending relevance, i.e.,
how well the document matches the query — if not, take a moment to verify this. 

Now try to send the following query to Vespa, and look at the order of the hits:

    $ curl -s 'http://localhost:8080/search/?yql=select+*+from+sources+*+where+default+contains+%22music%22+AND+default+contains+%22festival%22+order+by+date%3B' | python -m json.tool

By default, sorting is done in ascending order. This can also be specified by
appending `asc` after the sort attribute name. Use `desc` to sort the  in descending order:

    $ curl -s 'http://localhost:8080/search/?yql=select+*+from+sources+*+where+default+contains+%22music%22+AND+default+contains+%22festival%22+order+by+date+desc%3B' | python -m json.tool

### Query time data grouping

_Grouping_ is the concept of looking through all matching documents at
query-time and then performing operations with specified fields across all
the documents — some common use cases include:

- Find all the unique values for a given field, make **one group per unique
  value**, and return the count of documents per group.
- **Group documents by time and date** in fixed-width or custom-width buckets.
  An example of fixed-width buckets could be to group all documents by year,
  while an example of custom buckets could be to sort bug tickets by date of
  creation into the buckets _Today_, _Past Week_, _Past Month_, _Past Year_,
  and _Everything else_.
- Calculate the **minimum/maximum/average value** for a given field.

Displaying such groups and their sizes (in terms of matching documents per group)
on a search result page, with a link to each such group, is a common way to let users refine searches.
For now we will only do a very simple grouping query to get a list of unique
values for `date` ordered by the number of documents they occur in and top 3 is shown:

    $ curl -s 'http://localhost:8080/search/?yql=select%20*%20from%20sources%20*%20where%20sddocname%20contains%20%22blog_post%22%20limit%200%20%7C%20all(group(date)%20max(3)%20order(-count())each(output(count())))%3B' | python -m json.tool

With the full data set, you will get the following output:

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

The three most common unique values of `date` are listed, along with their respective counts.

Try to change the filter part of the YQL+ expression — the `where` clause — to a text
match of "recipe", or restrict `date` to be less than 20120401, and see how the list
of unique values changes as the set of matching documents for your query changes.
Try to search for the single term "Verizon" as well — a word we know is *not* present
in the document set, and as such will match no documents — and you will see that the list of groups is empty.

### Attribute limitations

#### Memory usage

Attributes are kept in memory at all time,
as opposed to normal indexes where the data is mostly kept on disk.
Even with large search nodes, one will notice that it is not
practical to define all the search definition fields as attributes,
as it will heavily restrict the number of documents per search node.
Some Vespa installations have more than 1 billion documents per node —
having megabytes of text in memory per document is not an option.

#### Matching

Another limitation is the way *matching* is done for attributes.
Consider the field `blogname` from our search definition, and the document for
the blog called "Thinking about museums". In the original input, the value for
`blogname` is a string built of up the three words "Thinking", "about", and
"museums", with a single whitespace character between them. How should we be
able to search this field?

For normal index fields, Vespa does something called _tokenization_ on the
string. In our case this means that the string above is split into the three
tokens "Thinking", "about" and "museums", enabling Vespa to match this document
both for the single-term queries "Thinking", "about" and "museums", the exact
phrase query "Thinking about museums", and a query with two or more tokens in
either order (e.g. "museums thinking"). This is how we all have come to expect
normal free text search to work.

However, there is a limitation in Vespa when it comes to attribute
fields and matching; attributes do not support normal token-based matching —
only *exact matching* or *prefix matching*. Exact matching is the default, and,
as the name implies, it requires you to search for the exact contents of the
field in order to get a match.

### When to use attributes

There are both advantages and drawbacks of using attributes —
it enables sorting and grouping, but requires
more memory and gives limited matching capabilities. When to use
attributes depends on the application; in general, use attributes for:

- fields used for sorting, e.g., a last-update timestamp,
- fields used for grouping, e.g., problem severity, and
- fields that are not long string fields.

Finally, all numeric fields should always be attributes.


## Clean environment by removing all documents

[vespa-remove-index](../reference/vespa-cmdline-tools.html#vespa-remove-index)
removes all documents:

    $ vespa-stop-services
    $ vespa-remove-index
    $ vespa-start-services


## Conclusion

This concludes the basic Vespa tutorial. You should now have a basic
understanding of how Vespa can help build your application.
In the [next part of the tutorial](blog-recommendation.html)
we will proceed to show how can we use Statistics and Machine Learning
to extend a basic search application into a recommendation system.
