---
# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa tutorial pt. 2: Blog recommendation"
---

## Introduction

In this tutorial we will build upon the [blog searching tutorial](blog-search.html)
and extend our basic search engine to include machine learned models to help us
recommend blog posts to users that arrive at our application.  Assume that once
a user arrives, we obtain his user identification number, denoted in this
tutorial by `user_id`, and that we will send this information down to Vespa and
expect to obtain a blog post recommendation list containing 100 blog posts
tailored for that specific user.

Code source and build instructions related to the code used throughout this
tutorial can be found at our tutorial supporting [code
repository](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared).

## Vespa and Hadoop

Vespa was designed to keep low-latency performance even at Yahoo-like web
scale.  This means supporting a large number of concurrent requests as well as
a very large number of documents. In the previous tutorial we used a data set
that was approximately 5Gb. Data sets of this size do not require a distributed
file system for data manipulation. However, we assume that most Vespa users
would like at some point to scale their applications up.  Therefore, in this
section we will start using tools such as [Apache
Hadoop](https://hadoop.apache.org), [Apache Pig](https://pig.apache.org) and
[Apache Spark](http://spark.apache.org/) when manipulating the data. These can
be run locally on your laptop in case you do not have access to a cluster.

We will still assume throughout this tutorial that the data is stored locally
on your laptop, but in case you would like to use HDFS (Hadoop Distributed
File System) for storing the data, it is just a matter of uploading it to HDFS
with the following command:

    $ hadoop fs -put trainPosts.json blog-app/trainPosts.json

If you go with this approach, you need to replace the local file paths with the
equivalent HDFS file paths throughout the rest of the tutorial.

Vespa has [a set of tools](../feed-using-hadoop-pig-oozie.html) to facilitate the interaction
between Vespa and the Hadoop ecosystem. These can also be used locally. An example
of feeding to Vespa using Pig is conceptually as simple as the following example:

    REGISTER vespa-hadoop.jar

    DEFINE VespaStorage com.yahoo.vespa.hadoop.pig.VespaStorage();

    A = LOAD '<path>' [USING <storage>] [AS <schema>];

    -- apply any transformations

    STORE A INTO '$ENDPOINT' USING VespaStorage();

To feed a file into Vespa you call this script using Pig:

    pig -x local -f feed.pig -p ENDPOINT=endpoint-1,endpoint-2

Here, the -x local option is added to specify that this script is run locally,
and will not attempt to retrieve scripts and data from HDFS. You need both Pig
and Hadoop libraries installed on your machine to run this locally, but you
don't need to install and start a running instance of Hadoop. More examples of
feeding to Vespa from Pig can be found in the [sample apps
directory](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared/src/main/pig).


## Vespa Evaluation Framework

### Training and test sets

In order to evaluate the gains obtained by our recommendation system when we
start to improve it with more accurate algorithms, we will split the dataset we
have available into training and test sets. The training set will contain
document (blog post) and user action (likes) pairs as well as any information
available about the documents contained in the training set. There is no
additional information about the users besides the blog posts they have liked.
The test set will be formed by a series of documents available to be
recommended and a set of users to whom we need to make recommendations. This
list of test set documents constitutes the Vespa content pool, which is the set
of documents stored in Vespa that are available to be served to users. The user
actions will be hidden from the test set and used later to evaluate the
recommendations made by Vespa.

To create an application that more closely resembles the challenges faced by
companies when building their recommendation systems, we decided to construct
the training and test sets in such a way that:

- There will be blog posts that had been liked in the training set by a set of
  users and that had also been liked in the test set by another set of users,
  even though this information will be hidden in the test set.

  Those cases are interesting to evaluate if the exploitation (as opposed to
  exploration) component of the system is working well. That is, if we are able
  to identify high quality blog posts based on the available information during
  training and exploit this knowledge by recommending those high quality blog
  posts to another set of users that might like them as well.

- There will be blog posts in the test set that had never been seen in the
  training set.

  Those cases are interesting in order to evaluate how the system deals with
  the cold-start problem. Systems that are too biased towards exploitation will
  fail to recommend new and unexplored blog posts, leading to a feedback loop
  that will cause the system to focus into a small share of the available
  content.

A key challenge faced by recommender system designers is how to balance the
exploitation/exploration components of their system, and our training/test set
split outlined above will try to replicate this challenge in our tutorial.
Notice that this split is different from the approach taken by the [Kaggle
competition](https://www.kaggle.com/c/predict-wordpress-likes) where the blog
posts available in the test set had never been seen in the training set, which
removes the exploitation component of the equation.

The Spark job below will use the "input_file" and create two folders in the
"output_path" named "training_set_ids" and "test_set_ids" containing files with
information about the ``post_id`` and ``user_id`` pairs that were assigned
to the training set and test set, respectively.

	spark-submit --class "com.yahoo.example.blog.BlogRecommendationApp" \
		--master local[4] blog-support.jar \
		--task split_set --input_file trainPosts.json \
		--test_perc_stage1 0.05 --test_perc_stage2 0.20 --seed 123 \
		--output_path blog-job/training_and_test_indices

Find blog-support.jar at target/scala\*/blog-support\*.jar. Other parameters:

- test_perc_stage1: The percentage of the blog posts that will be located only on the test set (exploration component).
- test_perc_stage2: The percentage of the remaining (post_id, user_id) pairs that should be moved to the test set (exploitation component).
- seed: seed value used in order to replicate results if required.

{% comment %}
TODO: Include file samples for those that do not want to generate their own
{% endcomment %}

### Evaluation metrics

The evaluation metric used by
[Kaggle](https://www.kaggle.com/c/predict-wordpress-likes/details/evaluation)
for this challenge was the Mean Average Precision at 100 (MAP@100).  However,
since we do not have information about which blog posts the users did not like
(that is, we have only positive feedback) and our inability to obtain user
behavior to the recommendations we make (this is an offline evaluation,
different from the usual A/B testing performed by companies that use
recommendation systems), we offer a similar remark as the one included in (Hu
et. al. 2008) and prefer recall-oriented measures. Following (Hu et. al.  2008)
we will use the expected percentile ranking, which in our case can be defined
by

$$
prank = \frac{\sum _{u,i} rank_{u,i}}{\sum_u N_u}
$$

where $$rank_{u,i}$$ is the percentile-ranking of blog post $$i$$ that was read by the user
$$u$$ within the ordered list of all blog post recommendation prepared for user $$u$$.
This way, $$rank_{u,i}=0\%$$ would mean that one of the blog posts read by user $$u$$ was the
first on the list of blog post recommendation given to user $$u$$.
On the other hand, $$rank_{u,i}=100\%$$ indicates that the blog post $$i$$ was placed at
the end of the recommendation list. $$N_u$$ represents the number of blog posts read by user
$$u$$ from the recommended list of blog posts.

{% comment %}

[This Scala script](https://github.com/vespa-engine/sample-apps/tree/master/blog-recommendation/src/spark/expected_percentile.scala)
illustrates how to compute the expected percentile ranking with the following inputs:

- test_file_path: location of the folder where test set pairs (post_id,
  user_id) will be stored.
- blog_recom_file_path: location of the folder where the recommendation list
  containing (user_id, rank, post_id) will be stored
- size_recommendation_list: The number of blog posts to be recommended, which
  is 100 in our tutorial.

{% endcomment %}

## Tensor framework

Modern machine learning applications often make use of large, multidimensional
feature spaces and perform complex operations on those features, such as in
large logistic regression and deep learning models. It is therefore necessary
to have an expressive framework to define and evaluate ranking expressions of
such complexity at scale.

Vespa comes with a Tensor framework, which unify and generalize scalar, vector
and matrix operations, handles the sparseness inherent to most machine learning
application (most cases evaluated by the model is lacking values for most of
the features) and allow for models to be continuously updated.

{%comment%} Should we mention this before it is ready? {%endcomment%}

We will cover the usage of tensors in Vespa as needed when walking through this
tutorial. Additional information about the Tensor framework can be found in the
[tensor user guide](../tensor-user-guide.html).

## Collaborative Filtering

We will start our recommendation system by implementing the collaborative
filtering algorithm for implicit feedback described in (Hu et. al. 2008). Our
data is said to be implicit because the users did not explicitly rate each blog
post they have read. Instead, the have "liked" blog posts they have likely
enjoyed (positive feedback) but did not have the chance to "dislike" blog posts
they did not enjoy (absence of negative feedback). Because of that, implicit
feedback is said to be inherently noisy and the fact that a user did not "like"
a blog post might have many different reasons not related with his negative
feelings about that blog post.

In terms of modeling, a big difference between explicit and implicit feedback
datasets is that the ratings for the explicit feedback are typically unknown
for the majority of user-item pairs and are treated as missing values and
ignored by the training algorithm. For an implicit dataset, we would assume a
rating of zero in case the user has not liked a blog post. To encode the fact
that a value of zero could come from different reasons we will use the concept
of confidence as introduced by (Hu et. al. 2008), which causes the positive
feedback to have a higher weight than a negative feedback.

{%comment%} references {%endcomment%}

Once we train the collaborative filtering model, we will have one vector
representing a latent factor for each user and item contained in the training
set. Those vectors will later be used in the Vespa ranking framework to make
recommendations to a user based on the dot product between the user and
documents latent factors. An obvious problem with this approach is that new
users and new documents will not have those latent factors available to them.
This is what is called a cold start problem and will be addressed with
content-based techniques described in future tutorials.


## Updating search definitions

As mentioned above, after training the model we obtain one latent factor vector
for each user and one for each document available in the training set. We want
to have those latent factors available in a Tensor representation to be used
during ranking by the Tensor framework. To accomplish this we will update the
blog post search definition `blog_post.sd` and create a new document type
`user` by specifying a new search definition named `user.sd`.

### blog_post.sd

We will update the search definition `blog_post.sd` to include a field of type
tensor named `user_item_cf` to hold the document latent factor.

	field user_item_cf type tensor(user_item_cf[10]) {
		indexing: summary | attribute
		attribute: tensor(user_item_cf[10])
	}

	field has_user_item_cf type byte {
		indexing: summary | attribute
		attribute: fast-search
	}

{% comment %}
TODO: Explain the indexing and attribute spec for the tensor type ... and explain why
we have a field has_user_item_cf for now.
{% endcomment %}

### user.sd

We will create a new search definition named `user.sd` that defines a new
document type named `user` to hold information related to the users. For now,
`user.sd` will contain the following fields

	search user {
		document user {

			field user_id type string {
				indexing: summary | attribute
				attribute: fast-search
			}

			field has_read_items type array<string> {
				indexing: summary | attribute
			}

			field user_item_cf type tensor(user_item_cf[10]) {
				indexing: summary | attribute
				attribute: tensor(user_item_cf[10])
			}

			field has_user_item_cf type byte {
				indexing: summary | attribute
				attribute: fast-search
			}

		}
	}

where

- user_id: unique identifier for the user
- user_item_cf: tensor that will hold the user latent factor
- has_user_item_cf

{% comment %}
TODO: Comment Tensor spec
{% endcomment %}

## Computing user and item latent factors

In this section we will use the complete training set to compute user and item
latent factors. We will leave the discussion about tuning and performance
improvement of the model used to the section about [model tuning and offline
evaluation](#model-tuning-and-offline-evaluation). If you [submit the following
Spark job](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared#building-and-running-the-spark-script-for-calculating-latent-factors)

	spark-submit --class "com.yahoo.example.blog.BlogRecommendationApp" \
		--master local[4] blog-support.jar \
		--task collaborative_filtering
		--input_file blog-job/training_and_test_indices/training_set_ids \
		--rank 10 --numIterations 10 --lambda 0.01 \
		--output_path blog-job/user_item_cf

you will compute the user and item latent factors and store them on the file
system, which will be HDFS in case you are running Spark on a cluster or your
regular file system in case you are running Spark locally. Once we have the
latent factors available, we need to send them to the running instance of your
Vespa application.

## Feeding tensors to Vespa

The following is the Pig command used to feed these latent factors to Vespa:

	pig -x local -f tutorial_feed_content_and_tensor_vespa.pig \
		-param VESPA_HADOOP_JAR=vespa-hadoop.jar \
		-param DATA_PATH=trainPosts.json \
		-param TEST_INDICES=blog-job/training_and_test_indices/testing_set_ids \
		-param BLOG_POST_FACTORS=blog-job/user_item_cf/product_features \
		-param USER_FACTORS=blog-job/user_item_cf/user_features \
		-param ENDPOINT=$(hostname):8080

* the "tutorial_feed_content_and_tensor_vespa.pig" script can be found
  [at our code repository](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared/src/main/pig/tutorial_feed_content_and_tensor_vespa.pig)
* ``VESPA_HADOOP_JAR`` is the vespa-hadoop library jar file that is part of
  [the Vespa code](https://github.com/vespa-engine/vespa/tree/master/vespa-hadoop)
* ``DATA_PATH`` is the JSON file containing the information about the blog
  posts
* ``BLOG_POST_FACTORS`` and ``USER_FACTORS`` are the two subdirectories in
  the user_item_cf directory created by the Spark script above
* ``ENDPOINT`` is the hostname of your Vespa instance.

For now, we need to re-feed the blog post contents when feeding the blog post
latent factors because Vespa does not allow partial updates of tensor fields.

## Query Vespa with tensor content

So now that we have fed our latent vectors to Vespa, we need to set up a rank
function to return the best matching blog posts given some user latent factor.
In order to do this, we need to tell Vespa how to interpret a query that
includes a specific latent factor. In order words, we need to programmatically
create a query based on a specific latent factor that will be sent to the Vespa
backend.

This type of query (and result) manipulation happens in the Vespa Search
Container, which is the home for all global processing of queries and their
results. The components of the search container are called Searchers.

### Searcher introduction

A searcher is a component which extends the class `com.yahoo.search.Searcher`
All Searchers must implement a single method:

	public Result search(Query query, Execution execution);

When the container receives a request, it will create a `Query` representing it
and execute a configured list of such Searcher components, called a search
chain.  The `query` object contains all the information needed to create a
result to the request while the `Result` encapsulates all the data generated
from a `Query`. The `Execution` object keeps track of the call state for an
execution of the searchers of a search chain.

### Adding a rank-profile to rank blog posts

For now we will rank the documents by a simple dot product between a query
tensor and the blog post tensor. We add the following rank-profile to
`blog_post.sd`:

    rank-profile tensor {
        first-phase {
            expression {
                sum(query(user_item_cf) * attribute(user_item_cf))
            }
        }
    }

The entire ranking of a document is given by this dot product, which is
a sum between the product of the two tensors:

- `query(user_item_cf)`, which is sent along with the query.
- `attribute(user_item_cf)`, which is the document field previously fed to.

How does the ranking framework know to expect that `query(user_item_cf)` is a
tensor, and that it is compatible with the attribute? We define that through a
[query profile type](../query-profiles.html#query-profile-types).  As explained
there, we create a new file `search/query-profiles/types/root.xml` in the
application package with the following content:

    <query-profile-type id="root" inherits="native">
        <field name="ranking.features.query(user_item_cf)" type="tensor(user_item_cf[10])" />
    </query-profile-type>

This tells the ranking backend that the ranking feature named
`query(user_item_cf)` will have type `tensor(user_item_cf[10])`, which defines
it as an indexed tensor with 10 elements. As the blog post document attribute
is also defined similarly, the ranking framework can effectively compile an
expression that computes the tensor product.

## The blog post searcher

Now that we have set up the backend to expect a tensor sent along with the
query, we need to actually pass one down. In this section we will set up a
custom search chain containing only the blog post searcher for easy testing
before we move on. We will design this so that if the searcher encounters a
query parameter called `user_item_cf`, it will construct a tensor from the
contents in this field and add that to the query so it can be passed to the
backend. The code for this is:

    package com.yahoo.example;

    import com.yahoo.prelude.query.IntItem;
    import com.yahoo.processing.request.CompoundName;
    import com.yahoo.search.Query;
    import com.yahoo.search.Result;
    import com.yahoo.search.Searcher;
    import com.yahoo.search.querytransform.QueryTreeUtil;
    import com.yahoo.search.searchchain.Execution;
    import com.yahoo.tensor.Tensor;

    public class BlogTensorSearcher extends Searcher {

        @Override
        public Result search(Query query, Execution execution) {

            Object userItemCfProperty = query.properties().get("user_item_cf");
            if (userItemCfProperty != null) {

                // Modify the query by restricting to blog_posts...
                query.getModel().setRestrict("blog_post");

                // ... that has a tensor field fed
                QueryTreeUtil.andQueryItemWithRoot(query, new IntItem(1, "has_user_item_cf"));

                // Modify the ranking by using the 'tensor' rank-profile (as defined in blog_post.sd)...
                query.properties().set(new CompoundName("ranking"), "tensor");

                // ... and setting 'query(user_item_cf)' used in that rank-profile
                query.getRanking().getFeatures().put("query(user_item_cf)", toTensor(userItemCfProperty));
            }

            return execution.search(query);
        }

        private Tensor toTensor(Object tensor) {
            if (tensor instanceof Tensor) {
                return (Tensor) tensor;
            }
            return Tensor.from("tensor(user_item_cf[10])", tensor.toString());
        }

    }

There are two parts to this code. The first part modifies which documents are
matched, and the second part modifies how these documents are ranked.

By modifying the query we change which which documents are selected. First we
restrict the results to blog posts. Then we AND the query root with an IntItem
which specifies that the `has_user_item_cf` field must be 1. This effectively
limits the search to documents that have their latent factors set. Note that we
do not explicitly set the query here, we just add to the query in case the user
wants to perform more elaborate queries.

The code goes on to modify the ranking by explicitly setting the rank profile
to the one we defined above. The most important part is where the ranking
feature `query(user_item_cf)` is set. Here we set this feature to the tensor
that is sent in the query parameter `user_item_cf`. In the `toTensor` method,
we check to see if it already is of type `Tensor`. We will see in the next
section how to add another searcher that retrieves a user profile and add that
tensor to this field. For now however, we expect that the content of this query
property is a string following the standard tensor format.  Vespa takes care of
URL decoding the string while the method `Tensor.from(String tensor)`
constructs a tensor from this string.

The final step is telling Vespa about this searcher. We set up this searcher in
its own search chain for ease of testing. Add the following to `services.xml`
inside the `services/jdisc/search` section:

    <chain id='blog' inherits='vespa'>
        <searcher bundle='blog-recommendation' id='com.yahoo.example.BlogTensorSearcher' />
    </chain>

With this you should now be ready to deploy your application. See [Developing applications](jdisc/developing-applications.html) for how to deploy the application. 

Try out the following query:

    http://<host>:<port>/search/?searchChain=blog&user_item_cf=%7B%7Buser_item_cf%3A0%7D%3A0.1%2C%7Buser_item_cf%3A1%7D%3A0.1%2C%7Buser_item_cf%3A2%7D%3A0.1%2C%7Buser_item_cf%3A3%7D%3A0.1%2C%7Buser_item_cf%3A4%7D%3A0.1%2C%7Buser_item_cf%3A5%7D%3A0.1%2C%7Buser_item_cf%3A6%7D%3A0.1%2C%7Buser_item_cf%3A7%7D%3A0.1%2C%7Buser_item_cf%3A8%7D%3A0.1%2C%7Buser_item_cf%3A9%7D%3A0.1%7D

where the query property `user_item_cf` here is the URL encoded representation
of the following tensor string:

    {
        {user_item_cf:0}:0.1,
        {user_item_cf:1}:0.1,
        {user_item_cf:2}:0.1,
        {user_item_cf:3}:0.1,
        {user_item_cf:4}:0.1,
        {user_item_cf:5}:0.1,
        {user_item_cf:6}:0.1,
        {user_item_cf:7}:0.1,
        {user_item_cf:8}:0.1,
        {user_item_cf:9}:0.1
    }

The result should be a list of blog posts ranked according to the input tensor.

## Query Vespa with user id

Now that we have successfully queried blog posts given a tensor, we would now
like to retrieve a user profile and use that to recommend blog posts. The user
profiles has previously been fed to Vespa in the `user_item_cf` field of the
`user` document type. We would like to query Vespa with a single `user_id` and
have it return a single hit matching the user if it exists, and extract the
tensor from that hit.

Let us start with setting up a searcher to retrieve the user profile. The input
would be a user id, and we set up a query to Vespa for this user id. If we find
the user, we will add the tensor to the query so it can be picked up by the
BlogTensorSearcher in its `toTensor` method. Here is one way we can set this
up:

    package com.yahoo.example;

    import com.yahoo.data.access.Inspectable;
    import com.yahoo.data.access.Inspector;
    import com.yahoo.prelude.query.WordItem;
    import com.yahoo.processing.request.CompoundName;
    import com.yahoo.search.Query;
    import com.yahoo.search.Result;
    import com.yahoo.search.Searcher;
    import com.yahoo.search.result.Hit;
    import com.yahoo.search.searchchain.Execution;
    import com.yahoo.search.searchchain.SearchChain;
    import com.yahoo.tensor.IndexedTensor;
    import com.yahoo.tensor.Tensor;

    import java.util.Iterator;
    import java.util.Map;

    public class UserProfileSearcher extends Searcher {

        public Result search(Query query, Execution execution) {

            Object userIdProperty = query.properties().get("user_id");
            if (userIdProperty != null) {

                // Retrieve user profile...
                Tensor userProfile = retrieveUserProfile(userIdProperty.toString(), execution);

                // ... and add user profile to query properties so BlogTensorSearcher can pick it up
                query.properties().set(new CompoundName("user_item_cf"), userProfile);

                if (query.isTraceable(9)) {
                    String tensorRepresentation = userProfile != null ? userProfile.toString() : "";
                    query.trace("Setting user profile to :" + tensorRepresentation, 9);
                }
            }

            return execution.search(query);
        }


        private Tensor retrieveUserProfile(String userId, Execution execution) {
            Query query = new Query();
            query.getModel().setRestrict("user");
            query.getModel().getQueryTree().setRoot(new WordItem(userId, "user_id"));
            query.setHits(1);

            SearchChain vespaChain = execution.searchChainRegistry().getComponent("vespa");
            Result result = new Execution(vespaChain, execution.context()).search(query);

            // This is needed to get the actual summary data
            execution.fill(result);

            Hit hit = getFirstHit(result);
            if (hit != null) {
                Object userItemCf = hit.getField("user_item_cf");
                if (userItemCf instanceof Inspectable) {
                    return convertTensor((Inspectable) userItemCf);
                }
            }
            return null;
        }

        private Hit getFirstHit(Result result) {
            Iterator<Hit> hiterator = result.hits().deepIterator();
            return hiterator.hasNext() ? hiterator.next() : null;
        }

        private Tensor convertTensor(Inspectable field) {
            IndexedTensor.Builder tensorBuilder = IndexedTensor.Builder.of(TensorType.fromSpec("tensor(user_item_cf[10])"));

            Inspector cells = field.inspect().field("cells");
            for (Inspector cell : cells.entries()) {
                Tensor.Builder.CellBuilder cellBuilder = tensorBuilder.cell();

                Inspector address = cell.field("address");
                for (Map.Entry<String, Inspector> entry : address.fields()) {
                    String dim = entry.getKey();
                    String label = entry.getValue().asString();
                    cellBuilder.label(dim, label);
                }

                Inspector value = cell.field("value");
                cellBuilder.value(value.asDouble());
            }
            return tensorBuilder.build();
        }

    }

{% comment %}
TODO: Update with the new code that also all already read articles
{% endcomment %}

Basically what this code does is that if a query property named `user_id`
exists, it sets up a new query which restricts the search to the `user`
document type and sets up a query with a single match instruction to the user
id. After setting up this query, we execute a separate query chain and wait for
the response.

We do it this way for two reasons. The first is that normally the user profile
might exist on a different system set up for key/value persistent storage such
as Redis, and we would normally have to set up a RPC or HTTP call for request
it from there. The other reason is that this query has different
characteristics than a Vespa search and we programmatically set up everything
we need here.

After the hit is returned, we extract the tensor from the hit and construct an
object of Tensor type. This object is added to the `user_item_cf` query
property which is subsequently picked up by the BlogTensorSearcher and used to
query blog posts.

Let us chain together these two searchers in the default search chain. Add the
following in the `services/jdisc/search` section of the services.xml file:

    <chain id='default' inherits='vespa'>
        <searcher bundle='recommendation' id='com.yahoo.example.UserProfileSearcher' />
        <searcher bundle='recommendation' id='com.yahoo.example.BlogTensorSearcher' />
    </chain>

After deploying, you should be able to execute queries such as the following:

    http://<host>:<port>/search/?user_id=14344185

This will return all the blog post recommended for that user given the
rank expression we set up. In addition, you can modify the query to match
specific documents:

    http://<host>:<port>/search/?user_id=14344185&query=music

This should return documents containing the term 'music', but still ranked according
to the users profile.

## Model tuning and offline evaluation

We will now optimize the latent factors using the training set instead of
manually picking hyperparameter values as was done in the [Computing user and
item latent factors](#computing-user-and-item-latent-factors) section.

	spark-submit --class "com.yahoo.example.blog.BlogRecommendationApp" \
		--master local[4] blog-support.jar \
		--task collaborative_filtering_cv \
		--input_file blog-job/training_and_test_indices/training_set_ids \
		--numIterations 10 --output_path blog-job/user_item_cf_cv

Feed the newly computed latent factors to Vespa as before. Note that we need to
update the tensor specification in the search definition in case the size of
the latent vectors change. We have used size 10 (rank = 10) in the [Computing
user and item latent factors](#computing-user-and-item-latent-factors) section
but our cross-validation algorithm above tries different values for rank (10,
50, 100).

	pig -x local -f tutorial_feed_content_and_tensor_vespa.pig \
		-param VESPA_HADOOP_JAR=vespa-hadoop.jar \
		-param DATA_PATH=trainPosts.json \
		-param TEST_INDICES=blog-job/training_and_test_indices/testing_set_ids \
		-param BLOG_POST_FACTORS=blog-job/user_item_cf_cv/product_features \
		-param USER_FACTORS=blog-job/user_item_cf_cv/user_features \
		-param ENDPOINT=$(hostname):8080

Once Vespa is properly fed we can run the following script that will use Java
UDF VespaQuery from the vespa-hadoop library to query Vespa for a specific
number of blog post recommendations for each user_id in our test set. With the
list of recommendation for each user, we can then compute the expected
percentile ranking as described in section [Evaluation metrics](#evaluation-metrics).

	pig -x local -f tutorial_compute_metric.pig \
		-param VESPA_HADOOP_JAR=vespa-hadoop.jar \
		-param DATA_PATH=trainPosts.json \
		-param TEST_INDICES=blog-job/training_and_test_indices/testing_set_ids \
		-param BLOG_POST_FACTORS=blog-job/user_item_cf_cv/product_features \
		-param USER_FACTORS=blog-job/user_item_cf_cv/user_features \
		-param ENDPOINT=$(hostname):8080
		-param NUMBER_RECOMMENDATIONS=100
		-param OUTPUT=blog-job/metric

{% comment %}
TODO: add a summary here of what we accomplished and way forward from here.
{% endcomment %}

You can now move on to the [next part of the tutorial](blog-recommendation-nn.html)
where we improve accuracy using a simple neural network.
