---
# Copyright Vespa.ai. All rights reserved.
title: "Reindexing"
redirect_from:
- /en/reindexing.html
---

When the indexing pipeline of a Vespa application changes,
Vespa may automatically refeed stored data such that the index is updated according to the new specification.
Changes in the indexing pipeline may be due to changes in external libraries,
e.g. for linguistics, or due to changes in the configuration done by the user,
such as the [indexing script](../reference/indexing-language-reference.html) in a document's schema,
or the [indexing mode](../reference/services-content.html#document.mode)
of a document type in a content cluster.
Reindexing can be done for an application's full corpus, for only certain content clusters,
or for only certain document types in certain clusters,
using the [reindex endpoint](../reference/deploy-rest-api-v2.html#reindex),
and inspected at the [reindexing endpoint](../reference/deploy-rest-api-v2.html#reindexing), details
are described below.

## Start reindexing

When a change in the indexing pipeline of an application is deployed, this is discovered by the config server
(see the [prepare endpoint](../reference/deploy-rest-api-v2.html#prepare-session) for details).
If the change is to be deployed, a [validation override](../reference/validation-overrides.html) might have to be
added to the application package (e.g. if changing match settings for a field).
Deployment output will then list the *reindex actions* required to make the index reflect the new indexing pipeline.
Use the [reindex endpoint](../reference/deploy-rest-api-v2.html#reindex)
to mark reindexing as ready for affected document types,
**but only after the new indexing pipeline is successfully deployed**,
i.e. when the application has [converged on the config generation](/en/application-packages.html#convergence)
that introduced the change.
Reindexing then commences with the next deployment of the application.
Summary of steps needed to enable and start reindexing:

1. Change indexing pipeline in application package, adding validation overrides if needed
2. Wait until config has converged on new config generation
3. Mark reindexing change as ready by POSTing to reindex endpoint
4. Start reindexing job by deploying application package one more time

## Reindexing progress

Reindexing is done by a component in each content cluster that
[visits](../visiting.html) all documents of the indicated types,
and re-feeds these through the [indexing chain](/en/operations-selfhosted/routing.html#chain-indexing) of the cluster.
(Note that only the [document fields](../reference/schema-reference.html#document) are re-fed —
all derived fields, produced by the indexing pipeline, are recomputed.)
The reindexing process avoids write races with concurrent feed by locking
[small subsets](../content/buckets.html) of the corpus when reindexing them;
this may cause elevated write latencies for a fraction of concurrent write operations,
but does not impact general throughput.
Moreover, since reindexing can be both lengthy and resource consuming, depending on the corpus,
the process is tuned to yield resources to other tasks,
such as external feed and serving,
and is generally safe to run in the background.

Reindexing is done for one document type at a time, in parallel across content clusters.
Detailed progress can be found at the
[reindexing endpoint](../reference/deploy-rest-api-v2.html#reindexing).
If state is *failed*, reindexing attempts to resume from the position where it failed after a grace period of some minutes.
State *pending* indicates reindexing will start, or resume, when the cluster is ready,
while *running* means it's currently progressing.
Finally, *successful* means all documents of that type were successfully reindexed.
Additionally, if the *speed* of a reindexing is `0.0`—set by users—that reindexing is
halted until the speed is either set to a positive value again, or it is replaced by a new reindexing of that document type.

## Procedure

Refer to [schema changes](/en/reference/schema-reference.html#modifying-schemas)
for a procedure / way to test the reindexing feature, and tools to validate the data.

## Use cases

Below are sample changes to the schema for different use cases,
or examples of operational steps for data manipulation.

| Use case | Description |
| --- | --- |
| clear field | To clear a field, do a partial update of all documents with the value, say an empty string.  It is also possible to use reindexing, but there is a twist - intuitively, this would work:   ``` field artist type string {     indexing: "" | summary | index } ```   However, the reset only works for [synthetic fields](../reference/schema-reference.html#schema).  A solution is to deploy a [document processor](../document-processing.html) that empties the field, to the default indexing chain - then trigger a reprocessing. |
| change indexing settings | As reindexing takes time, a field's data can be in one state or another, while the queries to it have the most current state. This is OK for many changes and applications.  If not, it is possible to reindex to a new field for a more atomic change. Add a *synthetic field* outside the *document definition* and pipe the content of the current field to it:   ``` search mydocs {      field title_non_stemmed type string {         indexing: input title | index | summary         stemming: none     }      document mydocs {         field title type string {             indexing: index | summary         } ```   Once reindexing is completed, switch queries to use the new field. This solution naturally increases memory and disk requirements in the transition.  Going back to using the original field with the new settings can be done by changing the index settings for the original field, wait for reindexing to be finished and start using the original field again in queries, then remove the temporary synthetic field. |

Relevant pointers:
* [Advanced indexing language](../reference/indexing-language-reference.html)
* [Schemas](../schemas.html)
