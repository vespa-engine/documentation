---
# Copyright Vespa.ai. All rights reserved.
title: "services.xml - 'content'"
---

```
content
    documents
        document
        document-processing
    min-redundancy
    redundancy
    coverage-policy
    nodes
        node
    group
        distribution
        node
        group
    engine
        proton
            searchable-copies
            tuning
                searchnode
                    lidspace
                        max-bloat-factor
                    requestthreads
                        search
                        persearch
                        summary
                    flushstrategy
                        native
                            total
                                maxmemorygain
                                diskbloatfactor
                            component
                                maxmemorygain
                                diskbloatfactor
                                maxage
                            transactionlog
                                maxsize
                            conservative
                                memory-limit-factor
                                disk-limit-factor
                    initialize
                        threads
                    feeding
                        concurrency
                        niceness
                    index
                        io
                            search
                        warmup
                            time
                            unpack
                    removed-db
                        prune
                            age
                            interval
                    summary
                        io
                            read
                        store
                            cache
                                maxsize
                                maxsize-percent
                                compression
                                    type
                                    level
                            logstore
                                maxfilesize
                                chunk
                                    maxsize
                                    compression
                                        type
                                        level
            sync-transactionlog
            flush-on-shutdown
            resource-limits
                disk
                memory
    search
        query-timeout
        visibility-delay
        coverage
            minimum
            min-wait-after-coverage-factor
            max-wait-after-coverage-factor
    tuning
        bucket-splitting
        min-node-ratio-per-group
        distribution
        maintenance
        max-document-size
        merges
        persistence-threads
        resource-limits
        visitors
            max-concurrent
        dispatch
            max-hits-per-partition
            dispatch-policy
            prioritize-availability
            min-active-docs-coverage
            top-k-probability
        cluster-controller
            init-progress-time
            transition-time
            max-premature-crashes
            stable-state-period
            min-distributor-up-ratio
            min-storage-up-ratio
            groups-allowed-down-ratio
```

## content

The root element of a Content cluster definition.
Creates a content cluster. A content cluster stores and/or indexes documents.
The xml file may have zero or more such tags.

Contained in [services](services.html).

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| version | required | number |  | 1.0 in this version of Vespa |
| id | required for multiple clusters | string |  | Name of the content cluster. If none is supplied, the cluster name will be `content`. Cluster names must be unique within the application, if multiple clusters are configured, the name must be set for all but one at minimum. {% include note.html content=" Renaming a cluster is the same as dropping the current cluster and adding a new one. This makes data unavailable or lost, depending on hosting model. Deploying with a changed cluster id will therefore fail with a validation override requirement: `Content cluster 'music' is removed. This will cause loss of all data in this cluster. To allow this add <allow until='yyyy-mm-dd'>content-cluster-removal</allow> to validation-overrides.xml, see https://docs.vespa.ai/en/reference/validation-overrides.html`."%} |

Subelements:
* [documents](#documents) (required)
* [min-redundancy](#min-redundancy)
* [redundancy](#redundancy)
* [coverage-policy](#coverage-policy)
* [nodes](#nodes)
* [group](#group)
* [engine](#engine)
* [search](#search)
* [tuning](#tuning)

## documents

Contained in [content](#content).
Defines which document types should be routed to this content cluster using the default route,
and what documents should be kept in the cluster if the garbage collector runs.
Read more on [expiring documents](../documents.html#document-expiry).
Also have some backend specific configuration for whether documents should be searchable or not.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| selection | optional | string |  | A [document selection](document-select-language.html), restricting documents that are routed to this cluster. Defaults to a selection expression matching everything.  This selection can be specified to match document identifier specifics that are *independent* of document types. For restrictions that apply only to a *specific* document type, this must be done within that particular document type's [document](#document) element. Trying to use document type references in this selection makes an error during deployment. The selection given here will be merged with per-document type selections specified within document tags, if any, meaning that any document in the cluster must match *both* selections to be accepted and kept.  This feature is primarily used to [expire documents](../documents.html#document-expiry). |
| garbage-collection | optional | true / false | false | If true, regularly verify the documents stored in the cluster to see if they belong in the cluster, and delete them if not. If false, garbage collection is not run. |
| garbage-collection-interval | optional | integer | 3600 | Time (in seconds) between garbage collection cycles. Note that the deletion of documents is spread over this interval, so more resources will be used for deleting a set of documents with a small interval than with a larger interval. |

Subelements:
* [document](#document) (required)
* [document-processing](#document-processing) (optional)

## document

Contained in [documents](#documents).
The document type to be routed to this content cluster.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| type | required | string |  | [Document type name](schema-reference.html#document) |
| mode | required | index / store-only / streaming |  | The mode of storing and indexing. Refer to [streaming search](../streaming-search.html) for *store-only*, as documents are stored the same way for both cases.  Changing mode requires an *indexing-mode-change* [validation override](validation-overrides.html), and documents must be re-fed. |
| selection | optional | string |  | A [document selection](document-select-language.html), restricting documents that are routed to this cluster. Defaults to a selection expression matching everything.  This selection must apply to fields in *this document type only*. Selection will be merged together with selection for other types and global selection from [documents](#documents) to form a full expression for what documents belong to this cluster. |
| global | optional | true / false | false | Set to *true* to distribute all documents of this type to all nodes in the content cluster it is defined.  Fields in global documents can be imported into documents to implement joins - read more in [parent/child](../parent-child.html). Vespa will detect when a new (or outdated) node is added to the cluster and prevent it from taking part in searches until it has received all global documents.  Changing from *false* to *true* or vice versa requires a *global-document-change* [validation override](validation-overrides.html). First, [stop services](/en/operations-selfhosted/admin-procedures.html#vespa-start-stop-restart) on all content nodes. Then, deploy with the validation override. Finally, [start services](/en/operations-selfhosted/admin-procedures.html#vespa-start-stop-restart) on all content nodes.  Note: *global* is only supported for *mode="index"*. |

## document-processing

Contained in [documents](#documents).
Vespa Search specific configuration for which document processing cluster and chain to run index preprocessing.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| cluster | optional | string | Container cluster on content node | Name of a [document-processing](services-docproc.html) container cluster that does index preprocessing. Use cluster to specify an alternative cluster, other than the default cluster on content nodes. |
| chain | optional | string | `indexing` chain | A document processing chain in the container cluster specified by *cluster* to use for index preprocessing. The chain must inherit the `indexing` chain. |

Example - the container cluster enables [document-processing](services-docproc.html),
referred to by the content cluster:

```
{% highlight xml %}








{% endhighlight %}
```

To add document processors either before or after the indexer,
declare a chain (inherit *indexing*) in a *document-processing* container cluster
and add document processors.
Annotate document processors with `before=indexingStart` or `after=indexingEnd`.
Configure this cluster and chain as the indexing chain in the content cluster - example:

```
{% highlight xml %}





                indexingStart


                indexingEnd








{% endhighlight %}
```

{% include important.html content='
Note the [document-api](services-container.html#document-api) configuration.
Set up this API on the same nodes as `document-processing` -
find details in [indexing](../indexing.html).' %}

## min-redundancy

Contained in [content](#content).
The minimum total data copies the cluster will maintain.
This can be set instead of (or in addition to) redundancy to ensure that a
minimum number of copies are always maintained regardless of other configuration.

Example: If *min-redundancy* is 2 and there is 1 content group, there will be 2
data copies in the group (2 copies for the cluster). If the number of groups is
changed to 2 there will be 1 data copy in each group (still 2 copies for the cluster).

Read more about the actual number of replicas when using [groups](#group)
in [topology change](/en/elasticity.html#changing-topology).

`min-redundancy` can be changed without node restart - replicas will be added or removed automatically.

## redundancy

Contained in [content](#content).

{% include note.html content='
Use [min-redundancy](#min-redundancy) instead of `redundancy`.' %}

Vespa Cloud: The number of data copies *per group*.

Self-managed: The total data copies the cluster will maintain to avoid data loss.

Example: with a redundancy of 2, the system tolerates 1 node failure before data becomes unavailable
(until the system has managed to create new replicas on other online nodes).

Redundancy can be changed without node restart - replicas will be added or removed automatically.

## coverage-policy

Contained in [content](#content).

Specifies the coverage policy for the content cluster. Valid values are `group` or `node`.
The default value is `group`.

If the policy is `group` coverage is maintained per group, meaning that when doing maintenance,
upgrades etc. one group is allowed to be down at a time. If there is only one group in the cluster,
coverage will be the same as policy `node`.

If the policy is `node` coverage is maintained on a node level, meaning that when doing
maintenance, upgrades etc. coverage will be maintained on a node level, so in practice 1 node in the whole
cluster is allowed to be down at a time.

When having several groups the common reason for changing policy away from the default `group` policy
is when the load added to the remaining groups will increase too much when a whole group is allowed to
go down. In that case it will be better to use the `node` policy, as taking one node at a time
will give just a minor increase in load.

## nodes

Contained in [content](#content).
Defines the set of content nodes in the cluster - parent for node-elements.

Also see [nodes](/en/reference/services.html#nodes).

## node

Contained in [nodes](#nodes) or [group](#group).
Configures a content node to the cluster.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| distribution-key | required | integer |  | Sets the distribution key of a node. It is not recommended changing this for a given node. It is recommended (but not required) that the set of distribution keys in the cluster are contiguous and starting at 0. Example: If the biggest distribution key is 499, then the distribution algorithm needs to calculate 500 random numbers to calculate the correct target. It is hence recommended to not leave too many gaps in the distribution key range.  Distribution keys are used to identify nodes and groups for the [distribution algorithm](../content/idealstate.html). If a node changes distribution key, the distribution algorithm regards it as a new node, so buckets are redistributed. When merging clusters, one might need to change distribution keys - [details](/en/operations-selfhosted/admin-procedures.html#add-or-remove-a-content-node).  Content nodes need unique node distribution keys across the whole cluster, as the key is also used as a node identifier where group information is not specified. |
| capacity | optional | double | 1 | {% include deprecated.html content="Capacity of this node, relative to other nodes. A node with capacity 2 will get double the data and feed requests of a node with capacity 1. This feature is deprecated and expert mode only. Don't use in production, Vespa assumes homogenous cluster capacity."%} |
| baseport | optional | integer |  | baseport |
| hostalias | optional | string |  | hostalias |
| preload | optional | string |  | preload |

## group

Contained in [content](#content) or
[group](#group) - groups can be nested.
Defines the [hierarchical structure](../elasticity.html#grouped-distribution) of the cluster.
Can not be used in conjunction with the [nodes](#nodes) element.
Groups can contain other groups or nodes, but not both.
There can only be a single level of leaf groups under the top group.

When using groups in [Open Source Vespa](https://vespa.ai/),
[searchable-copies](#searchable-copies) and
[redundancy](#redundancy) is the *total* replica number,
across all leaf groups in the cluster.
For groups in Vespa Cloud,
see [services in Vespa Cloud](/en/reference/services.html#nodes).

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| distribution-key | required | integer |  | Sets the distribution key of a group. It is not allowed to change this for a given group. Group distribution keys only need to be unique among groups that share the same parent group. |
| name | required | string |  | The name of the group, used for access from status pages and the like. |

{% include important.html content="
There is no deployment-time verification that the distribution key remains unchanged for any given node or group.
Consequently, take great care when modifying the set of nodes in a content cluster.
Assigning a new distribution key to an existing node is undefined behavior;
Best case, the existing data will be temporarily unavailable until the error has been corrected.
Worst case, risk crashes or data loss."%}

See [Vespa Serving Scaling Guide](../performance/sizing-search.html)
for when to consider using grouped distribution
and [Examples](../performance/sizing-examples.html) for example deployments
using flat and grouped distribution.

## distribution (in group)

Contained in [group](#group).
Defines the data distribution to subgroups of this group.
*distribution* should not be in the lowest level group containing storage nodes,
as here the ideal state algorithm is used directly.
In higher level groups, *distribution* is mandatory.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| partitions | required if there are subgroups in the group | string |  | String conforming to the partition specification:  | Partition specification | Description | | --- | --- | | * | Distribute all copies over 1 of N groups | | 1|* | Distribute all copies over 2 of N groups | | 1|1|* | Distribute all copies over 3 of N groups | |

The partition specification is used to evenly distribute content copies across groups.
Set a number or `*` per group separated by pipes (e.g. `1|*` for two groups).
See [sample deployment configurations](../performance/sizing-examples.html).

## engine

Contained in [content](#content).
Specify the content engine to use, and/or adjust tuning parameters for the engine.
Allowed engines are `proton` and `dummy`,
the latter being used for debugging purposes. If no engine is given, proton is used.
Sub-element: [proton](#proton).

## proton

Contained in [engine](#engine).
If specified, the content cluster will use the Proton content engine.
This engine supports storage, indexed search and secondary indices.
Optional sub-elements are [searchable-copies](#searchable-copies),
[tuning](#tuning-proton),
[sync-transactionlog](#sync-transactionlog),
[flush-on-shutdown](#flush-on-shutdown), and
[resource-limits (in proton)](#resource-limits-proton).

## searchable-copies

Contained in [proton](#proton).
Default value is 2, or [redundancy](#redundancy), if lower.
If set to less than redundancy, only some of the stored copies are ready for searching at any time.
This means that node failures causes temporary data unavailability
while the alternate copies are being indexed for search.
The benefit is using less memory, trading off availability during transitions.
Refer to [bucket move](../proton.html#bucket-move).

If updating documents or using [document selection](#documents) for garbage collection,
consider setting [fast-access](schema-reference.html#attribute)
on the subset of attribute fields used for this to make sure that these attributes are always kept
in memory for fast access.
Note that this is only useful if `searchable-copies` is less than `redundancy`.
Read more in [proton](../proton.html).

`searchable-copies` can be changed without node restart. Note that when reducing
`searchable-copies` resource usage will not be reduced until content nodes are restarted.

## tuning

Contained in [proton](#proton), optional.
Tune settings for the search nodes in a content cluster - sub-element:

| Element | Required | Quantity |
| --- | --- | --- |
| [searchnode](#searchnode) | No | Zero or one |

## searchnode

Contained in [tuning](#tuning-proton), optional.
Tune settings for search nodes in a content cluster - sub-elements:

| Element | Required | Quantity |
| --- | --- | --- |
| [lidspace](#lidspace) | No | Zero or one |
||  |  |  |
| --- | --- | --- |
| [requestthreads](#requestthreads) | No | Zero or one |
| [flushstrategy](#flushstrategy) | No | Zero or one |
| [initialize](#initialize) | No | Zero or one |
| [feeding](#feeding) | No | Zero or one |
| [index](#index) | No | Zero or one |
| [summary](#summary) | No | Zero or one |

```
{% highlight xml %}











{% endhighlight %}
```

## requestthreads

Contained in [searchnode](#searchnode), optional.
Tune the number of request threads used on a content node,
see [thread-configuration](../performance/sizing-search.html#thread-configuration) for details.
Sub-elements:

| Element | Required | Default | Description |
| --- | --- | --- | --- |
| search | Optional | 64 | Number of search threads. |
| persearch | Optional | 1 | Number of search threads. Number of search threads used per search, see the [Vespa serving scaling guide](../performance/sizing-search.html) for an introduction of using multiple threads per search per node to reduce query latency. Number of threads per search can be adjusted down per *rank-profile* using [num-threads-per-search](schema-reference.html#num-threads-per-search). |
| summary | Optional | 16 | Number of summary threads. |

```
{% highlight xml %}

    64
    1
    16

{% endhighlight %}
```

## flushstrategy

Contained in [searchnode](#searchnode), optional.
Tune the *native*-strategy for flushing components to disk -
a smaller number means more frequent flush:
* *Memory gain* is how much memory can be freed by flushing a component
* *Disk gain* is how much disk space can be freed by flushing a
  component (typically by using compaction)

Refer to [Proton maintenance jobs](../proton.html#proton-maintenance-jobs).
Optional sub-elements:
* `native`:
  + `total`
    - `maxmemorygain`:
      The total maximum memory gain (in bytes) for *all* components
      before running flush, default 4294967296 (4 GB)
    - `diskbloatfactor`:
      Trigger flush if the total disk gain (in bytes) for *all* components is larger
      than the factor times current total disk usage, default 0.25
  + `component`
    - `maxmemorygain`:
      The maximum memory gain (in bytes) by *a single* component
      before running flush, default 1073741824 (1 GB)
    - `diskbloatfactor`:
      Trigger flush if the disk gain (in bytes) by *a single* component is larger than
      the given factor times the current disk usage by that component, default 0.25
    - `maxage`:
      The maximum age (in seconds) of unflushed content for a single component
      before running flush, default 111600 (31h)
  + `transactionlog`
    - `maxsize`:
      The total maximum size (in bytes) of [transaction logs](../proton.html#transaction-log)
      for all document types before running flush, default 21474836480 (20 GB)
  + `conservative`
    - `memory-limit-factor`:
      When [resource-limits (in proton)](#resource-limits-proton) for memory is reached,
      flush more often by downscaling `total.maxmemorygain` and
      `component.maxmemorygain`, default 0.5
    - `disk-limit-factor`:
      When [resource-limits (in proton)](#resource-limits-proton) for disk is reached,
      flush more often by downscaling `transactionlog.maxsize`, default 0.5

```
{% highlight xml %}



            4294967296
            0.2


            1073741824
            0.2
            111600


            21474836480


            0.5
            0.5



{% endhighlight %}
```

## initialize

Contained in [searchnode](#searchnode), optional.
Tune settings related to how the search node (proton) is initialized. Optional sub-elements:
* `threads`:
  The number of initializer threads used for loading structures from disk at proton startup.
  The threads are shared between document databases when the value is larger than 0.
  Default value is the number of document databases + 1.
  + When set to larger than 1, document databases are initialized in parallel
  + When set to 1, document databases are initialized in sequence
  + When set to 0, 1 separate thread is used per document database,
    and they are initialized in parallel.

```
{% highlight xml %}

    2

{% endhighlight %}
```

## lidspace

Contained in [searchnode](#searchnode), optional.
Tune settings related to how lidspace is managed. Optional sub-elements:
* `max-bloat-factor`:
  Maximum bloat allowed before lidspace compaction is started. Compaction is moving a document
  from a high lid to a lower lid. Cost is similar to feeding a document and removing it.
  Also see description in [lidspace compaction maintenance job](../proton.html#lid-space-compaction).
  Default value is 0.01 or 1% of total lidspace. Will be increased to target of 0.50 or 50%.

```
{% highlight xml %}

    0.5

{% endhighlight %}
```

## feeding

Contained in [searchnode](#searchnode), optional.
Tune [proton](../proton.html) settings for feed operations. Optional sub-elements:
* `concurrency`:
  A number between 0.0 and 1.0 that specifies the concurrency when handling feed operations, default 0.5.
  When set to 1.0, all cores on the cpu can be used for feeding. Changing this value requires restart of
  node to take effect.
* `niceness`:
  A number between 0.0 and 1.0 that specifies the niceness of the feeding threads, default 0.0 => not any nicer than anyone else.
  Increasing this number will reduce priority of feeding compared to search. The real world effect is hard to predict as the magic
  exists in the OS level scheduler. Changing this value requires restart of node to take effect.

```
{% highlight xml %}

    0.8
    0.5

{% endhighlight %}
```

## index

Contained in [searchnode](#searchnode), optional.
Tune various aspect with the handling of disk and memory indexes. Optional sub-elements:
* `io`
  + `search`:
    Controls io read options used during search,
    values={mmap,populate}, default `mmap`. Using `populate` will eagerly touch all pages when index is loaded (after re-start or after index fusion is complete).
* `warmup`
  + `time`:
    Specifies in seconds how long the index shall be warmed up before being switched in for serving.
    During warmup, it will receive queries and posting lists will be iterated, but results ignored
    as they are duplicates of the live index. This will pull in the most important ones in the cache.
    However, as warming up an index will occupy more memory, do not turn it on unless you suspect you need it.
    And always benchmark to see if it is worth it.

    It's only potentially relevant for fields with indexing setting [index](../schemas.html#indexing),
    which have regular disk based indexes,
    and where the disk indexes are merged/fused in the background.
    When switching the index, warmup can be used.
    Also note that [state-v1-health](state-v1.html#state-v1-health)
    is independent of `warmup` - the node can be "up" before warmup.
  + `unpack`:
    Controls whether all posting features are pulled in to the cache, or only the most important.
    values={true, false}, default false.

```
{% highlight xml %}


        mmap


        60
        true


{% endhighlight %}
```

## removed-db

Contained in [searchnode](#searchnode), optional.
Tune various aspect of the db of removed documents. Optional sub-elements:
* `prune`
  + `age`:
    Specifies how long (in seconds) we must remember removed documents before we can prune them away.
    Default is 2 weeks.
    This sets the upper limit on how long a node can be down and still be accepted back in the system,
    without having the index wiped.
    There is no point in having this any higher than the age of the documents.
    If corpus is re-fed every day, there is no point in having this longer than 24 hours.
  + `interval`:
    Specifies how often (in seconds) to prune old documents. Default is 3.36 hours (prune age / 100).
    No need to change default. Exposed here for reference and for testing.

```
{% highlight xml %}


        86400


{% endhighlight %}
```

## summary

Contained in [searchnode](#searchnode), optional.
Tune various aspect with the handling of document summary. Optional sub-elements:
* `io`
  + `read`:
    Controls io read options used during reading of stored documents.
    Values are `directio` `mmap` `populate`.
    Default is `mmap`. `populate` will do an eager mmap and touch all pages.
* `store`
  + `cache`: Used to tune the cache used by the document store.
    Enabled by default, using up to 5% of available memory.
    - `maxsize`:
      The maximum size of the cache in bytes.
      If set, it takes precedence over [maxsize-percent](#summary-store-cache-maxsize-percent).
      Default is unset.
    - `maxsize-percent`:
      The maximum size of the cache in percent of available memory. Default is 5%.
    - `compression`
      * `type`:
        The compression type of the documents while in the cache.
        Possible values are , `none` `lz4` `zstd`.
        Default is `lz4`
      * `level`:
        The compression level of the documents while in cache.
        Default is 6
  + `logstore`:
    Used to tune the actual document store implementation (log-based).
    - `maxfilesize`:
      The maximum size (in bytes) per summary file on disk. Default value is 1GB.
      [document-store-compaction](../proton.html#document-store-compaction)
    - `chunk`
      * `maxsize`:
        Maximum size (in bytes) of a chunk. Default value is 64KB.
      * `compression`
        + `type`:
          Compression type for the documents, `none` `lz4` `zstd`.
          Default is `zstd`.
        + `level`:
          Compression level for the documents. Default is 3.

```
{% highlight xml %}


        directio



            5

                none




                16384

                    zstd
                    3





{% endhighlight %}
```

## flush-on-shutdown

Contained in [proton](#proton). Default value is true.
If set to true, search nodes will flush a set of components (e.g. memory index, attributes) to disk
before shutting down such that the time it takes to flush these components
plus the time it takes to replay the [transaction log](../proton.html#transaction-log)
after restart is as low as possible.
The time it takes to replay the transaction log depends on the amount of data to replay,
so by flushing, some components before restart the transaction log will be pruned,
and we reduce the replay time significantly.
Refer to [Proton maintenance jobs](../proton.html#proton-maintenance-jobs).

## sync-transactionlog

Contained in [proton](#proton). Default value is true.
If true, the transactionlog is synced to disk after every write.
This enables the transactionlog to survive power failures and kernel panic.
The sync cost is amortized over multiple feed operations.
The faster you feed the more operations it is amortized over.
So with a local disk this is not known to be a performance issue.
However, if using NAS (Network Attached Storage) like EBS on AWS one can see significant
feed performance impact. For one particular case, turning off sync-transactionlog for EBS gave a 60x improvement.

With sync-transactionlog turned off, the risk of losing data depends on the kernel's
[sysctl settings.](https://www.kernel.org/doc/html/latest/admin-guide/sysctl/vm.html#dirty-background-bytes)
For example, this is a common default:

```
# sysctl -a
...
vm.dirty_expire_centisecs = 3000
vm.dirty_ratio = 20
vm.dirty_writeback_centisecs = 500
...
```

With this configuration, the worse case scenario is to lose 35 seconds worth of transactionlog, but no more than 1/20
of the free memory. Because kernel flusher threads wake up every 5s (dirty_writeback_centisecs) and write data
older than 30s (dirty_expire_centisecs) from memory to disk. But if un-synced data exceeds 1/20 of the free memory,
the Vespa process will sync it (dirty_ratio).

The above also assumes that all copies of the data are lost at the same time **and** that kernels on all these nodes
flush at the same time: realistic scenario only with one copy.

Adjust these [sysctl settings](https://www.kernel.org/doc/html/latest/admin-guide/sysctl/vm.html#dirty-background-bytes)
to manage the trade-off between data loss and performance. You'll see more in those kernel docs: for example,
thresholds can be expressed in bytes.

## resource-limits (in proton)

Contained in [proton](#proton).
Specifies resource limits used by proton to reject both external and internal write operations (on this content node) when a limit is reached.

{% include warning.html content="
These proton limits should almost never be changed directly.
Instead, change [resource-limits](#resource-limits)
that controls when external write operations are blocked in the entire content cluster.
Be aware of the risks of tuning resource limits as seen in the link."%}

The local proton limits are derived from the cluster limits if not specified, using this formula:

$${L_{proton}} = {L_{cluster}} + \frac{1-L_{cluster}}{2}$$

| Element | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| disk | optional | float [0, 1] | 0.875 | Fraction of total space on the disk partition used before put and update operations are rejected |
| memory | optional | float [0, 1] | 0.9 | Fraction of physical memory that can be resident memory in anonymous mapping by proton before put and update operations are rejected |

Example:

```
{% highlight xml %}


        0.83
        0.82
{% endhighlight %}
```

## search

Contained in [content](#content), optional.
Declares search configuration for this content cluster. Optional sub-elements are
[query-timeout](#query-timeout),
[visibility-delay](#visibility-delay) and
[coverage](#coverage).

## query-timeout

Contained in [search](#search).
Specifies the query timeout in seconds for queries against the search interface on the content nodes.
The default is 0.5 (500ms), the max is 600.0.
For query timeout also see the request parameter [timeout](query-api-reference.html#timeout).

{% include note.html content='One can not override this value using the
[timeout](query-api-reference.html#timeout) request parameter.' %}

## visibility-delay

Contained in [search](#search). Default 0, max 1, seconds.

This setting controls the TTL caching for [parent-child](../parent-child.html) imported fields.
See [feature tuning](../performance/feature-tuning.html#parent-child-and-search-performance).

## coverage

Contained in [search](#search).
Declares search coverage configuration for this content cluster. Optional sub-elements are
[minimum](#minimum),
[min-wait-after-coverage-factor](#min-wait-after-coverage-factor) and
[max-wait-after-coverage-factor](#max-wait-after-coverage-factor).
Search coverage configuration controls how many nodes the query dispatcher process
should wait for, trading search coverage versus search performance.

## minimum

Contained in [coverage](#coverage).
Declares the minimum search coverage required before returning the results of a query.
This number is in the range `[0, 1]`, with 0 being no coverage and 1 being full coverage.

The default is 1; unless configured otherwise a query will not return
until all search nodes have responded within the specified timeout.

## min-wait-after-coverage-factor

Contained in [coverage](#coverage).
Declares the minimum time for a query to wait for full coverage once the declared
[minimum](#minimum) has been reached. This number is a factor that is
multiplied with the time remaining at the time of reaching minimum coverage.

The default is 0; unless configured otherwise a query will return as soon as the
minimum coverage has been reached, and the remaining search nodes appear to be lagging.

## max-wait-after-coverage-factor

Contained in [coverage](#coverage).
Declares the maximum time for a query to wait for full coverage once the declared
[minimum](#minimum) has been reached.
This number is a factor that is multiplied with the time remaining
at the time of reaching minimum coverage.

The default is 1; unless configured otherwise a query is allowed to wait its full
timeout for full coverage even after reaching the minimum.

## tuning

Contained in [content](#content), optional. Optional tuning parameters are:
[bucket-splitting](#bucket-splitting),
[min-node-ratio-per-group](#min-node-ratio-per-group),
[cluster-controller](#cluster-controller),
[dispatch](#dispatch-tuning),
[distribution](#distribution_type),
[maintenance](#maintenance),
[max-document-size](#max-document-size),
[merges](#merges),
[persistence-threads](#persistence-threads) and
[visitors](#visitors).

## bucket-splitting

Contained in [tuning](#tuning).
The [bucket](../content/buckets.html) is the fundamental unit of distribution
and management in a content cluster.
Buckets are auto-split, no need to configure for most applications.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| max-documents | optional | integer | 1024 | Maximum number of documents per content bucket. Buckets are split in two if they have more documents than this. Keep this value below 16K. |
| max-size | optional | integer | 32MiB | Maximum size (in bytes) of a bucket. This is the sum of the serialized size of all documents kept in the bucket. Buckets are split in two if they have a larger size than this. Keep this value below 100 MiB. |
| minimum-bits | optional | integer |  | Override the ideal distribution bit count configured for this cluster. Prefer to use the [distribution type](#distribution_type) setting instead if the default distribution bit count does not fit the cluster. This variable is intended for testing and to work around possible distribution bit issues. Most users should not need this option. |

## min-node-ratio-per-group

{% include important.html content='This is configuration for the cluster controller.
Most users are normally looking for
[min-active-docs-coverage](#min-active-docs-coverage)
which controls how many nodes can be down before query load is routed to other groups.' %}

Contained in [tuning](#tuning).
States a lower bound requirement on the ratio of nodes within *individual* [groups](#group)
that must be online and able to accept traffic before the entire group is automatically taken out of service.
Groups are automatically brought back into service when the availability
of its nodes has been restored to a level equal to or above this limit.

Elastic content clusters are often configured to use multiple groups
for the sake of horizontal traffic scaling and/or data availability.
The content distribution system will try to ensure a configured number of replicas is always present
within a group in order to maintain data redundancy.
If the number of available nodes in a group drops too far,
it is possible for the remaining nodes in the group to not have sufficient capacity to take over
storage and serving for the replicas they now must assume responsibility for.
Such situations are likely to result in increased latencies and/or feed rejections caused by resource exhaustion.
Setting this tuning parameter allows the system to instead automatically take down the remaining nodes in the group,
allowing feed and query traffic to fail completely over to the remaining groups.

Valid parameter is a decimal value in the range [0, 1].
Default is 0, which means that the automatic group out-of-service functionality will *not* automatically take effect.

Example: assume a cluster has been configured with *n* groups of 4 nodes each
and the following tuning config:

```
{% highlight xml %}

    0.75

{% endhighlight %}
```

This tuning allows for 1 node in a group to be down. If 2 or more nodes go down,
all nodes in the group will be marked as down, letting the *n-1* remaining groups handle all the traffic.

This configuration can be changed live as the system is running and altered limits will take effect immediately.

## distribution (in tuning)

Contained in [tuning](#tuning).
Tune the distribution algorithm used in the cluster.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| type | optional | loose | strict | legacy | loose | When the number of a nodes configured in a system changes over certain limits, the system will automatically trigger major redistributions of documents. This is to ensure that the number of buckets is appropriate for the number of nodes in the cluster. This enum value specifies how aggressive the system should be in triggering such distribution changes.  The default of `loose` strikes a balance between rarely altering the distribution of the cluster and keeping the skew in document distribution low. It is recommended that you use the default mode unless you have empirically observed that it causes too much skew in load or document distribution.  Note that specifying `minimum-bits` under [bucket-splitting](#bucket-splitting) overrides this setting and effectively "locks" the distribution in place. |

## maintenance

Contained in [tuning](#tuning).
Controls the running time of the bucket maintenance process.
Bucket maintenance verifies bucket content for corruption.
Most users should not need to tweak this.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| start | required | HH.MM |  | Start of daily maintenance window, e.g. 02:00 |
| stop | required | HH.MM |  | End of daily maintenance window, e.g. 05:00 |
| high | required | HH.MM |  | Day of week for starting full file verification cycle, e.g. monday. The full cycle is more costly than partial file verification |

## max-document-size

Contained in [tuning](#tuning).
Specifies max document size in the content cluster, measured as the uncompressed size
of a document operation arriving over the wire by the distributor service. The limit will
be used for all document types. A document larger than this limit will be rejected by the
distributor. Note that some document operations that don't contain the entire document, like
[document updates](../document-api-guide.html#document-updates)
might increase the size of a document above this limit.

Valid values are numbers including a unit (e.g. *10MiB*) and the value must be between 1Mib and 2048 Mib (inclusive).
Values will be rounded to nearest MiB, so using MiB as a unit is preferrable.
It is strongly recommended to make sure this is not set too high, 10 MiB is a reasonable setting for most use cases,
setting it above 100 MiB is not recommended, as allowing large documents might impact operations, e.g. when
restarting nodes, moving documents between nodes etc. Default value is 128 MiB.

Example:

```
{% highlight xml %}

    10MiB

{% endhighlight %}
```

## merges

Contained in [tuning](#tuning).
Defines throttling parameters for bucket merge operations.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| max-per-node | optional | number |  | Maximum number of parallel active bucket merge operations. |
| max-queue-size | optional | number |  | Maximum size of the merge bucket queue, before reporting BUSY back to the distributors. |

## persistence-threads

Contained in [tuning](#tuning).
Defines the number of persistence threads per partition on each content node.
A content node executes bucket operations against the persistence engine synchronously in each of these threads.
8 threads are used by default. Override with the **count** attribute.

## visitors

Contained in [tuning](#tuning).
Tuning parameters for visitor operations.
Might contain [max-concurrent](#max-concurrent).

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| thread-count | optional | number |  | The maximum number of threads in which to execute visitor operations. A higher number of threads may increase performance, but may use more memory. |
| max-queue-size | optional | number |  | Maximum size of the pending visitor queue, before reporting BUSY back to the distributors. |

## max-concurrent

Contained in [visitors](#visitors).
Defines how many visitors can be active concurrently on each storage node.
The number allowed depends on priority - lower priority visitors should not block higher priority visitors completely.
To implement this, specify a fixed and a variable number.
The maximum active is calculated by adjusting the variable component using the priority,
and adding the fixed component.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| fixed | optional | number | [16](https://github.com/vespa-engine/vespa/blob/master/storage/src/vespa/storage/visiting/stor-visitor.def) | The fixed component of the maximum active count |
| variable | optional | number | [64](https://github.com/vespa-engine/vespa/blob/master/storage/src/vespa/storage/visiting/stor-visitor.def) | The variable component of the maximum active count |

## resource-limits

Contained in [tuning](#tuning).
Specifies resource limits used to decide whether external write operations should be blocked in the entire content cluster,
based on the reported resource usage by content nodes.
See [feed block](../operations/feed-block.html) for more details.
**Warning:** The content nodes require resource headroom to handle
extra documents as part of re-distribution during node failure,
and spikes when running
[maintenance jobs](../proton.html#proton-maintenance-jobs).
Tuning these limits should be done with extreme care,
and setting them too high might lead to permanent data loss.
They are best left untouched, using the defaults, and cannot be set in Vespa Cloud.

| Element | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| disk | optional | float [0, 1] | 0.75 | Fraction of total space on the disk partition used on a content node before feed is blocked |
| memory | optional | float [0, 1] | 0.8/0.75 | Fraction of physical memory that can be resident memory in anonymous mapping on a content node before feed is blocked. Total physical memory is sampled as the minimum of `sysconf(_SC_PHYS_PAGES) * sysconf(_SC_PAGESIZE)` and the cgroup (v1 or v2) memory limit. Nodes with 8 Gib or less memory in Vespa Cloud has a limit of 0.75. |

Example - in the content tag:

```
{% highlight xml %}


        0.78
        0.77


{% endhighlight %}
```

## dispatch

Contained in [tuning](#tuning).
Tune the query dispatch behavior - child elements:

| Element | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| max-hits-per-partition | optional | Integer | No capping: Return all | Maximum number of hits to return from a content node. By default, a query returns the requested number of hits + offset from every content node to the container. The container orders the hits globally according to the query, then discards all hits beyond the number requested.  In a system with a large fan-out, this consumes network bandwidth and the container nodes easily network saturated. Containers will also sort and discard more hits than optimal.  When there are sufficiently many search nodes, assuming an even distribution of the hits, it suffices to only return a fraction of the request number of hits from each node. Note that changing this number will have global ordering impact. See *top-k-probability* below for improving performance with fewer hits. |
| dispatch-policy | optional | best-of-random-2 / adaptive | adaptive | Configure policy for choosing which group shall receive the next query request. However, multiphase requests that either requires or benefits from hitting the same group in all phases are always hashed. Relevant only for [grouped distribution](../performance/sizing-search.html#data-distribution):   |  |  | | --- | --- | | best-of-random-2 | Selects 2 random groups and selects the one with the lowest latency. | | adaptive | measures latency, preferring lower latency groups, selecting group with probability latency/(sum latency over all groups) |  | prioritize-availability | optional | Boolean | true | With [grouped distribution](../performance/sizing-search.html#data-distribution): If true, or by default, all groups that are within min-active-docs-coverage of the **median** of the document count of other groups will be used to service queries. If set to false, only groups within min-active-docs-coverage of the **max** document count will be used, with the consequence that full coverage is prioritized over availability when multiple groups are lacking content, since the remaining groups may not be able to service the full query load. | | min-active-docs-coverage | optional | A float percentage | 97 | With [grouped distribution](../performance/sizing-search.html#data-distribution): The percentage of active documents one needs to have compared to average of other groups in order to be active for serving queries. Because of measurement timing differences, it is not advisable to tune this above 99 percent. | | top-k-probability | optional | Double | 0.9999 | Probability that the top K hits will be the globally best. Based on this probability, the dispatcher will fetch enough hits from each node to achieve this. The only way to guarantee a probability of 1.0 is to fetch K hits from each partition. However, by reducing the probability from 1.0 to 0.99999, one can significantly reduce number of hits fetched and save both bandwidth and latency. The number of hits to fetch from each partition is computed as:  $${q}={\frac{k}{n}}+{qT}({p},{30})×{\sqrt{ {k}×{\frac{1}{n}}×({1}-{\frac{1}{n}}) }}$$  where qT is a Student's t-distribution. With n=10 partitions, k=200 hits and p=0.99999, only 45 hits per partition is needed, as opposed to 200 when p=1.0.  Use this option to reduce network and container cpu/memory in clusters with many nodes per group - see [Vespa Serving Scaling Guide](../performance/sizing-search.html). | |

## cluster-controller

Contained in [tuning](#tuning).
Tuning parameters for the cluster controller managing this cluster - child elements:

| Element | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| init-progress-time | optional |  |  | If the initialization progress count have not been altered for this amount of seconds, the node is assumed to have deadlocked and is set down. Note that initialization may actually be prioritized lower now, so setting a low value here might cause false positives. Though if it is set down for wrong reason, when it will finish initialization and then be set up again. |
| transition-time | optional |  | [storage_transition_time](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def) [distributor_transition_time](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def) | The transition time states how long (in seconds) a node will be in maintenance mode during what looks like a controlled restart. Keeping a node in maintenance mode during a restart allows a restart without the cluster trying to create new copies of all the data immediately. If the node has not started or got back up within the transition time, the node is set down, in which case, new full bucket copies will be created. Note separate defaults for distributor and storage (i.e. search) nodes. |
| max-premature-crashes | optional |  | [max_premature_crashes](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def) | The maximum number of crashes allowed before a content node is permanently set down by the cluster controller. If the node has a stable up or down state for more than the *stable-state-period*, the crash count is reset. However, resetting the count will not re-enable the node again if it has been disabled - restart the cluster controller to reset. |
| stable-state-period | optional |  | [stable_state_time_period](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def) | If a content node's state doesn't change for this many seconds, it's state is considered *stable*, clearing the premature crash count. |
| min-distributor-up-ratio | optional |  | [min_distributor_up_ratio](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def) | The minimum ratio of distributors that are required to be *up* for the cluster state to be *up*. |
| min-storage-up-ratio | optional |  | [min_storage_up_ratio](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def) | The minimum ratio of content nodes that are required to be *up* for the cluster state to be *up*. |
| groups-allowed-down-ratio | optional |  | [groups-allowed-down-ratio](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def) | A ratio for the number of content groups that are allowed to be down simultaneously. A value of 0.5 means that 50% of the groups are allowed to be down. The default is to allow only one group to be down at a time. |
