---
# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Vespa tutorial pt. 3: Blog recommendation with Neural Network models"
---

## Introduction

The main objective of this tutorial is to show how to deploy neural network
models in Vespa using our Tensor Framework. In fact, any model that can be
represented by a series of Tensor operations can be deployed in Vespa.  Neural
network is just a popular example. In addition, we will introduce the
multi-phase ranking model available in Vespa that can be used to run more
expensive models in a phase based on a reduced number of documents returned by
previous phases. This feature allow us to run models that would be
prohibitively expensive to use if we had to run them at query-time across all
the documents indexed in Vespa.

This tutorial builds upon [Vespa tutorial pt. 2](blog-recommendation.html), and
therefore reading it is necessary to fully understand the ideas presented here.

## Model Training

In this section, we will define a neural network model, show how we created a
suitable dataset to train the model and train the model using TensorFlow.

### The neural network model

In the Vespa tutorial pt. 2, we computed latent factors for each user and each
document and then used a dot-product between user and document vectors to rank
the documents available for recommendation to a specific user. In this tutorial
we will train a 2-layer fully connected neural network model that will take the
same user ( $$u$$ ) and document ( $$d$$ ) latent factors as input and will
output the probability of that specific user liking the document.

More technically, in the Vespa tutorial pt. 2 our rank function $$r$$ was given
by

$$r(u,d)= u * d$$

while in this tutorial it will be given by

$$r(u,d, \theta)= f(u, d, \theta)$$

where $$f$$ represents the neural network model described below and $$\theta$$
is the neural network parameter values that we need to learn from training
data.

The specific form of the neural network model used here is

$$p = \text{sigmoid}(h_1 \times W_2 + b_2)$$

$$h_1 = \text{ReLU}(x \times W_1 + b_1)$$

where $$x = [u, d]$$ is the concatenation of the user and document latent
factor, ReLU is the rectifier activation function, sigmoid represents the
sigmoid function, p is the output of the model and in this case can be
interpreted as the probability of the user u liking a blog post d. The
parameters of the model are represented by $$\theta = (W_1, W_2, b_1, b_2)$$.

### Training data

For the training dataset, we will start with the (user_id, post_id) rows from
the "training_set_ids" generated in the section [Training and test
sets](blog-recommendation.html#generate-training-and-test-sets) of the previous
tutorial. Then, we remove every row for which there is no latent factors for
the user_id or post_id contained in that row. This gives us a dataset with only
positive feedback (label = 1), since each row represents one instance of a
user_id liking a post_id.

In order to train our model, we need to generate negative feedback (label = 0).
So, for each row (user_id, post_id) in the current dataset we will generate N
negative feedback rows by randomly sampling post_id_fake from the pool of
post_id's available in the current set, so that for each (user_id, post_id) row
with label = 1 we will increase the dataset with N (user_id, post_id_fake) rows
with label = 0.

<!-- Pre computed dataset can be found here(link here when published) and -->
Find code to generate the dataset in the [utility
scripts](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared#create-training-dataset).

### Training with TensorFlow

With the training data in hand, we have split it into 80% training set and 20%
validation set and used TensorFlow to train the model. The script used can be
found in the [utility
scripts](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared#train-model-with-tensorflow)
and executed by

	$ python vespaModel.py --product_features_file_path vespa_tutorial_data/user_item_cf_cv/product.json \
	                       --user_features_file_path vespa_tutorial_data/user_item_cf_cv/user.json \
	                       --dataset_file_path vespa_tutorial_data/nn_model/training_set.txt

The progress of your training can be visualized using Tensorboard

	$ tensorboard --logdir runs/*/summaries/

Below we see the accuracy and loss metrics plotted after every 1000 training steps:

<div style="text-align:center"><img src="images/accuracy_vespa_nn.png" style="width: 70%; margin-right: 1%; margin-bottom: 0.5em;"></div>

<div style="text-align:center"><img src="images/loss_vespa_nn.png" style="width: 70%; margin-right: 1%; margin-bottom: 0.5em;"></div>

## Model deployment in Vespa

### Two Phase Ranking

When a query is sent to Vespa, it will scan all documents available and select
the ones (possibly all) that match the query. When the set of documents
matching a query is found, Vespa must decide the order of these documents.
Unless explicit sorting is used, Vespa decides this order by calculating a
number for each document, the rank score, and sorts the documents by this
number.

The rank score can be any function that takes as arguments parameters sent by
the query, document attributes defined in search definitions and global
parameters not directly linked to query or document parameters. One example of
rank score is the output of the neural network model defined in this tutorial.
The model takes the latent factor $$u$$ associated with a specific
`user_id` (query parameter), the latent factor $$d$$ associated with
document `post_id` (document attribute) and learned model parameters
(global parameters not related to a specific query nor document) and returns
the probability of user $$u$$ to like document $$d$$.

However, even though Vespa is designed to carry out such calculations
optimally, complex expressions becomes expensive when they must be calculated
over every one of a large set of matching documents. To relieve this, Vespa can
be configured to run two ranking expressions - a smaller and less accurate one
on all hits during the matching phase, and a more expensive and accurate one
only on the best hits during the reranking phase. In general this allows a more
optimal usage of the cpu budget by dedicating more of the total cpu towards the
best candidate hits.

The reranking phase, if specified, will by default be run on the 100 best hits
on each search node, after matching and before information is returned upwards
to the search container. The number of hits to rerank can be turned up or down as needed.
Below is a toy example showing how to configure first and second phase ranking
expressions in the rank profile section of search definitions where the second
phase rank expression is run on the 200 best hits from first phase on each
search node.

	search myapp {
	    ...
	    rank-profile default inherits default {

	        first-phase {
	            expression: nativeRank + query(deservesFreshness) * freshness(timestamp)
	        }

	        second-phase {
	            expression {
	                0.7 * ( 0.7*fieldMatch(title) + 0.2*fieldMatch(description) + 0.1*fieldMatch(body) ) +
	                0.3 * attributeMatch(keywords)
	            }
	            rerank-count: 200
	        }
	    }
	}

### Vespa ranking expressions

In order to evaluate the neural network model trained with TensorFlow in the
previous section, we need to import the TensorFlow model and use it in the
`blog_post` search definition. To honor a low-latency response, we will take
advantage of the two phase ranking available in Vespa and define the first
phase ranking to be the same ranking function used in the Vespa tutorial pt. 2,
which is a dot-product between the user and latent factors. After the documents
have been sorted by the first phase ranking function, we will rerank the top
200 document from each search node using the second phase ranking given by the
neural network model presented above.

Note that we define two ranking profiles in the search definition below. This
allow us to decide which ranking profile to use at query time. We define a
ranking profile named `tensor` which only applies the dot-product between
user and document latent factors for all matching documents and a ranking
profile named `nn_tensor`, which rerank the top 200 documents using the
neural network model discussed in the previous section.

We will walk through each part of the `blog_post` search definition, see
[blog_post.sd](https://github.com/vespa-engine/sample-apps/tree/master/blog-recommendation/src/main/application/searchdefinitions/blog_post.sd).

We define a ranking profile named `tensor` which ranks all the matching
documents by the dot-product between the document latent factor and the user
latent factor. This is the same ranking expression used in the previous
tutorial, which includes code to retrieve the user latent factor based on the
`user_id` sent by the query to Vespa.

    # Simpler ranking profile without second-phase ranking
    rank-profile tensor {
        first-phase {
            expression {
                sum(query(user_item_cf) * attribute(user_item_cf))
            }
        }
    }

Now we specify a second rank-profile called `nn_tensor` that will use the same
first phase as the rank-profile `tensor` but will rerank the top 200 documents
using the TensorFlow model as second phase. We refer to [Ranking with
TensorFlow models in Vespa](../tensorflow.html) for more information regarding
the TensorFlow import and other operations used in the code below.

    # rank profile with neural network model as second phase
    rank-profile nn_tensor {

        # This defines where to get the user latent factor from
        function input_u() {
            expression: query(user_item_cf)
        }

        # This defines where to get the blog latent factor from
        function input_d() {
            expression: attribute(user_item_cf)
        }

        # First phase ranking: dot product between latent factors
        first-phase {
            expression: sum(query(user_item_cf) * attribute(user_item_cf))
        }

        # Second phase ranking: neural network based on latent factors
        second-phase {
            rerank-count: 200
            expression: sum(tensorflow("blog/saved"))
        }
    }

The first part to notice is the `second-phase` ranking. Here we use the
`tensorflow` rank feature to load the model trained using the script above.
Once the model has been trained in TensorFlow, the following code saves
the model to a directory `saved`:

    export_path = "saved"
    builder = tf.saved_model.builder.SavedModelBuilder(export_path)
    signature = tf.saved_model.signature_def_utils.predict_signature_def(
                inputs = {'input_u':vespa_model.input_u, 'input_d':vespa_model.input_d},
                outputs = {'y':vespa_model.y})
    builder.add_meta_graph_and_variables(sess,
                [tf.saved_model.tag_constants.SERVING],
                signature_def_map={'serving_default':signature})
    builder.save(as_text=True)

This model can be copied into the application package under the `models`
directory, and it will be deployed along with the application. I.e. the ranking
expression above, `tensorflow("blog/saved")`, expects the model to be under the
directory `models/blog/saved`.

An important part of the model-saving code above is the definition of the
inputs and outputs. These are defined in the signature of the saved model. The
inputs to the model are the latent factor vectors for the user (`input_u`) and
the blog post (`input_d`). Vespa expects to find user-defined functions of
the same name, which returns the values to use as inputs. This can be
seen in the rank profile above which defines `input_u` to retrieve the
value from the query and 'input_d' to retrieve the value from the document.

The signature also defines the output value to be the output of the `y`
operation. This output is typically a tensor itself, and we use the `sum`
ranking feature to reduce the tensor to a single scalar value that can
be ranked with.

This is typically all that is needed to import TensorFlow models. For more
information, please see [Ranking with TensorFlow models in
Vespa](http://docs.vespa.ai/documentation/tensorflow.html).

## Offline evaluation

We will now query Vespa and obtain 100 blog post recommendations for each `user_id`
in our test set. Below, we query Vespa using the `tensor` ranking function which
contain the simpler ranking expression involving the dot-product between user and
document latent factors.

	pig -x local -f tutorial_compute_metric.pig \
	  -param VESPA_HADOOP_JAR=vespa-hadoop.jar \
	  -param TEST_INDICES=blog-job/training_and_test_indices/testing_set_ids \
	  -param ENDPOINT=$(hostname):8080
	  -param NUMBER_RECOMMENDATIONS=100
	  -param RANKING_NAME=tensor
	  -param OUTPUT=blog-job/cf-metric

We perform the same query routine below, but now using the ranking-profile `nn_tensor`
which reranks the top 200 documents using the neural network model.

	pig -x local -f tutorial_compute_metric.pig \
	  -param VESPA_HADOOP_JAR=vespa-hadoop.jar \
	  -param TEST_INDICES=blog-job/training_and_test_indices/testing_set_ids \
	  -param ENDPOINT=$(hostname):8080
	  -param NUMBER_RECOMMENDATIONS=100
	  -param RANKING_NAME=nn_tensor
	  -param OUTPUT=blog-job/cf-metric

The `tutorial_compute_metric.pig` script can be found [in our
repo](https://github.com/vespa-engine/sample-apps/tree/master/blog-tutorial-shared#offline-evaluation).

Comparing the recommendations obtained by those two ranking profiles and our
test set, we see that by deploying a more complex and accurate model in the
second phase ranking, we increased the number of relevant documents (documents
read by the user) retrieved from 11948 to 12804 (more than 7% increase) and
those documents retrieved appeared higher up in the list of recommendations, as
shown by the expected percentile ranking metric introduced in the Vespa
tutorial pt. 2 which decreased from 37.1% to 34.5%.

