---
# Copyright Vespa.ai. All rights reserved.
title: "Buckets"
---

The content layer splits the document space into chunks called *buckets*,
and algorithmically maps documents to buckets by their id.
The cluster automatically splits and joins buckets
to maintain a uniform distribution across all nodes
and to keep bucket sizes within configurable limits.

Documents have string identifiers that maps to a 58 bit numeric location.
A bucket is defined as all the documents that shares a given amount
of the least significant bits within the location.
The amount of bits used controls how many buckets will exist.
For instance, if a bucket contains all documents whose 8 LSB bits is 0x01,
the bucket can be split in two by using the 9th bit in the location to split them.
Similarly, buckets can be joined by requiring one less bit in common.

## Distribution

Distribution happens in several layers.
* Documents map to 58 bit numeric locations.
* Locations map to buckets
* Buckets map to distributors responsible for handling requests related to those buckets.
* Buckets map to content nodes responsible for storing replicas of buckets.

### Document to location distribution

Document identifiers use [document identifier schemes](../documents.html)
to map documents to locations.
This way it is possible to co-locate data within buckets
by enforcing some documents to have common LSB bits.
Specifying a group or numeric value with the n and g options
overrides the 32 LSB bits of the location.
Only use when required, e.g. when using streaming search for personal search.

### Location to bucket distribution

The cluster state contains a distribution bit count,
which is the amount of location bits to use to generate buckets which can be mapped to distributors.

The cluster state may change the number of distribution bits to adjust the
number of buckets distributed at this level.
When adding more nodes to the cluster,
the number of buckets increases in order for the distribution to remain uniform.

Altering the distribution bit count causes a redistribution of all buckets.

If locations have been overridden to co-localize documents into few units,
the distribution of documents into these buckets may be skewed.

### Bucket to distributor distribution

Buckets are mapped to distributors using the ideal state algorithm.

### Bucket to content node distribution

Buckets are mapped to content nodes using the ideal state algorithm.
As the content nodes persist data,
changing bucket ownership takes more time/resources than on the distributors.

There is usually a replica of a bucket on the same content node
as the distributor owning the bucket, as the same algorithm is used.

The distributors may split the buckets further than the distribution bit count indicates,
allowing more units to be distributed among the content nodes to create a more even distribution,
while not affecting routing from client to distributors.

## Maintenance operations

The content layer defines a set of maintenance operations to keep the cluster balanced.
Distributors schedule maintenance operations and issue them to content nodes.
Maintenance operations are typically not high priority requests.
Scheduling a maintenance operation does not block any external operations.

| Split bucket | Split a bucket in two, by enforcing the documents within the new buckets to have more location bits in common. Buckets are split either because they have grown too big, or because the cluster wants to use more distribution bits. |
| Join bucket | Join two buckets into one. If a bucket has been previously split due to being large, but documents have now been deleted, the bucket can be joined again. |
| Merge bucket | If there are multiple replicas of a bucket, but they do not store the same set of versioned documents, *merge* is used to synchronize the replicas. A special case of a merge is a one-way merge, which may be done if some of the replicas are to be deleted right after the merge. Merging is used not only to fix inconsistent bucket replicas, but also to move buckets between nodes. To move a bucket, an empty replica is created on the target node, a merge is executed, and the source bucket is deleted. |
| Create bucket | This operation exist merely for the distributor to notify a content node that it is now to store documents for this bucket too. This allows content nodes to refuse operations towards buckets it does not own. The ability to refuse traffic is a safeguard to avoid inconsistencies. If a client talks to a distributor that is no longer working correctly, we rather want its requests to fail than to alter the content cluster in strange ways. |
| Delete bucket | Drop stored state for a bucket and reject further requests for it |
| (De)activate bucket | Activate bucket for search results - refer to [bucket management](../proton.html#bucket-management) |
| Garbage collections | If configured, documents are periodically garbage collected through background maintenance operations. |

### Bucket split size

The distributors may split existing buckets further to keep bucket sizes at manageable levels,
or to ensure more units to split among the backends and their partitions.

Using small buckets, the distribution will be more uniform and bucket operations will be smaller.
Using large buckets, less memory is needed for metadata operations
and bucket splitting and joining is less frequent.

The size limits may be altered by configuring [bucket splitting](../reference/services-content.html#bucket-splitting).

## Document to bucket distribution

Each document has a document identifier following a document identifier
[uri scheme](../documents.html).
From this scheme a 58 bit numeric *location* is generated.
Typically, all the bits are created from an MD5 checksum of the whole identifier.

Schemes specifying a *groupname*, will have the LSB bits of
the location set to a hash of the *groupname*.
Thus, all documents belonging to that group will have locations with similar least significant bits,
which will put them in the same bucket.
If buckets end up split far enough to use more bits than the hash bits overridden by the group,
the data will be split into many buckets, but each will typically only contain data for that group.

MD5 checksums maps document identifiers to random locations.
This creates a uniform bucket distribution, and is default.
For some use cases, it is better to co-locate documents,
optimizing grouped access - an example is personal documents.
By enforcing some documents to map to similar locations,
these documents are likely to end up in the same actual buckets.
There are several use cases for where this may be useful:
* When migrating documents for some entity between clusters, this may be
  implemented more efficient if the entity is contained in just a few
  buckets rather than having documents scattered around all the existing
  buckets.
* If operations to the cluster is clustered somehow, clustering
  the documents equally in the backend may make better use of caches. For
  instance, if a service stores data for users, and traffic is typically
  created for users at short intervals while the users are actively using
  the service, clustering user data may allow a lot of the user traffic
  to be easily cached by generic bucket caches.

If the `n=` option is specified, the 32 LSB bits of the given
number overrides the 32 LSB bits of the location.
If the `g=` option is specified, a hash is created of the group name,
the hash value is then used as if it were specified with `n=`.
When the location is calculated, it is mapped to a bucket.
Clients map locations to buckets using
[distribution bits](#location-to-bucket-distribution).

Distributors map locations to buckets by searching their bucket database,
which is sorted in inverse location order.
The common case is that there is one.
If there are several, there is currently inconsistent bucket splitting.
If there are none, the distributor will create a new bucket for
the request if it is a request that may create new data.
Typically, new buckets are generated split according to the distribution bit count.

Content nodes should rarely need to map documents to buckets, as distributors
specify bucket targets for all requests. However, as external operations are
not queued during bucket splits and joins, the content nodes remap operations
to avoid having to fail them due to a bucket having recently been split or joined.

### Limitations

One basic limitation to the document to location mapping is that it may never change.
If it changes, then documents will suddenly be in the wrong buckets in the cluster.
This would violate a core invariant in the system, and is not supported.

To allow new functionality,
document identifier schemes may be extended or created that
maps to location in new ways, but the already existing ones must map
the same way as they have always done.

Current document identifier schemes typically allow the 32 least significant
bits to be overridden for co-localization, while the remaining 26 bits are
reserved for bits created from the MD5 checksum.

### Splitting

When there are enough documents co-localized to the same bucket,
causing the bucket to be split, it will typically need to split past the 32 LSB.
At this split-level and beyond, there is no longer a 1-1 relationship between the
node owning the bucket and the nodes its replica data will be stored on.

The effect of this is that documents sharing a location will be spread across
nodes in the entire cluster once they reach a certain size. This enables efficient
parallel processing.

## Bucket space

Buckets exist in the *default* or *global* bucket space.
