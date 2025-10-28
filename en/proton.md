---
# Copyright Vespa.ai. All rights reserved.
title: "Proton"
redirect_from:
- /en/reference/search-custom-state-api.html
---

Proton is Vespa's search core and runs on each content node as the *vespa-proton-bin* process.
Proton maintains disk and memory structures for documents (organized per document type),
handles [read and write operations](reads-and-writes.html#operations),
and execution of [queries](#queries).
As the document data is dynamic, disk and memory structures are periodically optimized by
[maintenance jobs](#proton-maintenance-jobs).

The content node has a *bucket management system*
which sends requests to a set of *document databases*,
which each consists of three *sub-databases*
`ready`, `not ready` and `removed`:

![Proton feed overview](/assets/img/proton-feed.svg)

### Bucket management

When the node starts up it first needs to get an overview of what documents and buckets it has.
Once metadata for all buckets is known, the content nodes transition from down to up state.
As the distributors want quick access to bucket metadata, it maintains an in-memory bucket
database to efficiently serve these requests.
The state of the bucket database can always be reconstructed from the durably persisted
search node state, but this is expensive and therefore only happens at process startup time.

This database is considered the source of truth for the state of the node's bucket metadata
for the duration of the process's lifetime. As incoming operations mutate the state of the
documents on the node, it is critical that the database is always kept in sync with these changes.

### Persistence threads and operation dispatching

A content node has a pool of *persistence threads* that is created at startup
and remains fixed in size for the lifetime of the process. It is the responsibility of the
persistence threads to schedule incoming write and read operations received by the content
node, dispatch these to the search core, and ensure the bucket database remains in sync
with changes caused by write operations.

Unless explicitly configured, the size of the thread pool is automatically set based on the
number of CPU cores available.

Persistence threads are backed by a *persistence queue*. Read/write-operations received
by the RPC subsystem are pushed onto this queue. The queue is operation deadline-aware; if
an operation has exceeded its deadline while enqueued, it is immediately failed back to
the sender without being executed. This avoids a particular failure scenario where a heavily
loaded node spends increasingly more and more time processing already doomed operations,
due to not being able to drain its queue quickly enough.

All operations bound for a particular data bucket (such as Puts, Gets, etc.) execute in the
context of a *bucket lock*. Locks are *shared* for reads and *exclusive* for writes.
This means that multiple read operations can execute in parallel for the same bucket, but
only one write operation can execute for a bucket at any given time (and no reads can be
started concurrently with existing writes for a bucket, and vice versa). Note that some of
these locking restrictions can be relaxed when it's safe to do so—see
[performance optimizations](#performance-optimizations) for details.

If a persistence thread tries to pop an operation from the queue and sees that the bucket it's
bound for is already locked, it will leave the operation in place in the queue and try the next
operation(s) instead. This means that although the queue acts as a FIFO for client operations
towards a *single* bucket, this is not the case across *multiple* buckets.

#### Write operations

Write operations are dispatched as *asynchronous*—i.e., non-blocking—tasks to the search core.
This increases parallelism by freeing up persistence threads to handle other operations, and a deeper
pipeline enables the search core to optimize transaction log synchronization and batching of data
structure updates.

Since a deeper pipeline comes at the potential cost of increased latency when many operations are in
flight, the maximum number of concurrent asynchronous operations is bounded by an adaptive persistence
throttling mechanism. The throttler will dynamically scale the window of concurrency until it reaches a
saturation point where further increasing the window size also results in increased operation latencies.
When the number of in-flight operations hits the current maximum, persistence threads will not
dispatch any more writes until the number goes down. Reads can still be processed during this time.

An asynchronous write-task holds on to the exclusive bucket lock for the duration of its lifetime.
Once the search core completes the write operation, the bucket database is updated with the new metadata
state of the bucket (which reflects the side effects of the write) prior to releasing the lock.
An operation reply is then generated and sent back via the RPC subsystem.

#### Read operations

Read operations are always evaluated *synchronously*—i.e. blocking—by persistence threads.
To avoid having potentially expensive maintenance read operations (such as those used for
[replica reconciliation](content/consistency.html#replica-reconciliation)) block client
operations for prolonged amounts of time, a subset of the persistence threads are *not* allowed
to process such maintenance operations.

Note that the condition evaluation step of a test-and-set write is considered a *read* sub-operation
and is therefore done synchronously. Since it's part of a write operation, it happens atomically in
the context of the exclusive lock of the higher-level operation.

#### Performance optimizations

To reduce thread context switches, some write operations may bypass the persistence thread queues
and be directly asynchronously dispatched to the search core from the RPC thread the operation
was received at.
Such operations must still successfully acquire the appropriate exclusive bucket lock—if the
lock cannot be immediately acquired the operation is pushed onto the persistence queue instead.

To reduce lock contention and thread wakeups, smaller numbers of persistence threads are grouped
together in *stripes* that share a dedicated per-stripe persistence queue.
Operations are routed deterministically to a particular stripe based on their bucket ID, meaning
that stripes operate on non-overlapping parts of the bucket space. Together, the many stripes and
queues form one higher-level *logical* queue that covers the entire bucket space.

If the queue contains multiple *non-conflicting* write operations to the same bucket, these
may be dispatched in parallel in the context of the *same* write lock. This avoids having
to wait for an entire lock-execute-unlock roundtrip prior to dispatching the next write for the
same bucket. An example of conflicting writes is multiple Puts to the same document ID.
The maximum number of operations dispatched in parallel is implementation-defined.

### Document database

Each document database is responsible for a single document type.
It has a component called FeedHandler which takes care of incoming documents, updates, and remove requests.
All requests are first written to a [transaction log](#transaction-log),
then handed to the appropriate sub-database, based on the request type.

### Sub-databases

There are three types of sub-databases, each with its own
[document meta store](attributes.html#document-meta-store) and [document store](#document-store).
The document meta store holds a map from the document id to a local id.
This local id is used to address the document in the document store.
The document meta store also maintains information on the
state of the buckets that are present in the sub-database.

The sub-databases are maintained by the *Maintenance Controller*.
The document distribution changes as the system is resized.
When the number of nodes in the system changes,
the Maintenance Controller will move documents between the Ready and
Not Ready sub-databases to reflect the new distribution.
When an entry in the Removed sub-database gets old, it is purged.
The sub-databases are:

| Not Ready | Holds the redundant documents that are not searchable, i.e. the *not ready* documents. Documents that are not ready are only stored, not indexed. It takes some processing to move from this state to the ready state. |
| Ready | Maintains attributes and indexes of all *ready* documents and keeps them searchable. One of the ready copies is *active* while the rest are *not active:*  |  |  | | --- | --- | | Active | There should always be exactly one active copy of each document in the system, though intermittently there may be more. These documents produce results when queries are evaluated. | | Not Active | The ready copies that are not active are indexed but will not produce results. By being indexed, they are ready to take over immediately if the node holding the active copy becomes unavailable. Read more in [searchable-copies](reference/services-content.html#searchable-copies). | |
| Removed | Keeps track of documents that have been removed. The id and timestamp for each document are kept. This information is used when buckets from two nodes are merged. If the removed document exists on another node but with a different timestamp, the most recent entry prevails. |

## Transaction log

Content nodes have a transaction log to persist mutating operations.
The transaction log persists operations by file append.
Having a transaction log simplifies proton's in-memory index structures
and enables steady-state high performance, read more below.

All operations are written and synced to the [transaction log](proton.html#transaction-log).
This is sequential (not random) IO, but might impact overall feed performance if running on NAS attached storage
where the sync operation has a much higher cost than on local attached storage (e.g., SSD).
See [sync-transactionlog](reference/services-content.html#sync-transactionlog).

By default, proton will
[flush components](reference/services-content.html#flush-on-shutdown)
like attribute vectors and memory index on shutdown, for quicker startup after scheduled restarts.

## Document store

Documents are stored as compressed serialized blobs in the *document store*.
Put, update and remove operations are persisted in the [transaction log](#transaction-log)
before updating the document in the document store.
The operation is acked to the client and the result of the operation is immediately seen in search results.

Files in the document store are written sequentially, and occur in pairs - example:

```
-rw-r--r-- 1 owner users 4133380096 Aug 10 13:36 1467957947689211000.dat
-rw-r--r-- 1 owner users   71192112 Aug 10 13:36 1467957947689211000.idx
```

The [maximum size](reference/services-content.html#summary-store-logstore-maxfilesize):
(in bytes) per .dat file on disk can be set using the following:

```
<content id="mycluster" version="1.0">
  <engine>
    <proton>
      <tuning>
        <searchnode>
          <summary>
            <store>
              <logstore>
                <maxfilesize>8000000000</maxfilesize>
```

Notes:
* The files are written in sequence. *proton* starts with one pair
  and grows it until *maxfilesize*. Once full, a new pair is started.
* This means the pair is immutable, except for the last pair, which is written to.
* Documents exist in multiple versions in multiple files.
  Older versions are compacted away when a pair is scheduled to be the new active pair -
  obsolete versions are removed, leaving only the active document version left in a new file pair
  - which is the new active pair.
* Read more on implications of setting *maxfilesize* in
  [proton maintenance jobs](proton.html#document-store-compaction).
* Files are written in [chunks](reference/services-content.html#summary-store-logstore-chunk),
  using compression settings.

### Defragmentation

[Document store compaction](#document-store-compaction),
defragments and sort document store files.
It removes stale versions of documents (i.e. old versions of updated documents).
It is triggered when the disk bloat of the document store is larger than the total disk usage of the document store
times [diskbloatfactor](reference/services-content.html#flushstrategy-native-total-diskbloatfactor).
Refer to [summary tuning](reference/services-content.html#summary) for details.

Defragmentation status is best observed by tracking the
[max_bucket_spread](reference/searchnode-metrics-reference.html#content_proton_documentdb_ready_document_store_max_bucket_spread)
metric over time.
A sawtooth pattern is normal for corpora that change over time.
The [document_store_compact](reference/searchnode-metrics-reference.html#content_proton_documentdb_job_document_store_compact)
metric tracks when proton is running the document store compaction job.
Compaction settings can be set too tight, in that case, the metric is always, or close to, 1.

When benchmarking, it is important to set the correct compaction settings,
and also make sure that proton has compacted files since (can take hours),
and is not actively compacting (*document_store_compact* should be 0 most of the time).

{% include note.html content="There is no bucket-compaction across files - documents will not move between files."%}

### Optimized reads using chunks

As documents are clustered within the .dat file,
proton optimizes reads by reading larger chunks when accessing documents.
When visiting, documents are read in *bucket* order.
This is the same order as the defragmentation jobs use.

The first document read in a visit operation for a bucket will read a chunk from the .dat file into memory.
Subsequent document accesses are served by a memory lookup only.
The chunk size is configured by
[maxsize](reference/services-content.html#summary-store-logstore-chunk-maxsize):

```
<engine>
  <proton>
    <tuning>
      <searchnode>
        <summary>
          <store>
            <logstore>
              <chunk>
                <maxsize>16384</maxsize>
              </chunk>
            </logstore>
```

There can be 2^22=4M chunks. This sets a minimum chunk size based on *maxfilesize* -
e.g. an 8G file can have minimum 2k chunk size.
Finally, the bucket size is configured by setting
[bucket-splitting](reference/services-content.html#bucket-splitting):

```
<content id="imagepersonal" version="1.0">
  <tuning>
    <bucket-splitting max-documents="1024"/>
```

The following are the relevant sizing units:
* .dat file size - *maxfilesize*.
  Larger files give fewer files and so better locality,
  but compaction requires more memory and more time to complete.
* chunk size - *maxsize*.
  Smaller chunks give less wasted IO bytes but more IO operations.
* bucket size - *bucket-splitting*.
  Larger buckets give fewer buckets and better locality to nodes and files, but
  incur more overhead during content layer bucket maintenance operations.
  Overhead can be treated as linear in both CPU, memory and network usage
  with the bucket size.

### Memory usage

The document store has a mapping in memory from local ID (LID) to position in a document store file (.dat).
Part of this mapping is persisted in the .idx-file paired to the .dat file.
The memory used by the document store is linear with the number of documents and updates to these.

The metric [content.proton.documentdb.ready.document_store.memory_usage.allocated_bytes](reference/searchnode-metrics-reference.html#content_proton_documentdb_ready_document_store_memory_usage_allocated_bytes)
gives the size in memory -
use the [metric API](reference/state-v1.html#state-v1-metrics) to find it.
A rule of thumb is 12 bytes per document.

## Attributes

[Attribute](attributes.html) fields are in-memory fields used for
matching, ranking, sorting and grouping.
Each attribute is a separate component that consists of a set of
[data structures](attributes.html#data-structures)
to store values for that field across all documents in a sub-database.
Attributes are managed by the Ready sub-database.
Some attributes can also be managed by the Not Ready sub-database,
see [high-throughput updates](attributes.html#fast-access) for details.

## Index

Index fields are string fields, used for text search.
Other field types are [attributes](attributes.html)
and [summary fields](document-summaries.html).

The Index in the Ready sub-database consists of a memory index and one or more disk indexes.
Mutating document operations are applied to the memory index,
which is [flushed](#memory-index-flush) regularly.
Flushed memory indexes are [merged](#disk-index-fusion) with the primary disk index.

Proton stores position information in text indices by default, for proximity relevance -
`posocc` (below).
All the occurrences of a term are stored in the posting list, with its position.
This provides superior ranking features,
but is somewhat more expensive than just storing a single occurrence per document.
For most applications, it is the correct tradeoff,
since most of the cost is usually elsewhere and relevance is valuable.

Applications that only need occurrence information for filtering
can use [rank: filter](reference/schema-reference.html#rank)
to optimize query performance, using only `boolocc`-files (below).

The memory index has a dictionary per index field.
This contains all unique words in that field, with mapping to posting lists with position information.
The position information is used during ranking, see
[nativeRank](nativerank.html) for details on how a text match score is calculated.

The disk index stores the content of each index field in separate folders.
Each folder contains:
* Dictionary. Files: `dictionary.pdat`,
  `dictionary.spdat`, `dictionary.ssdat`.
* Compressed posting lists with position information. File: `posocc.dat.compressed`.
* Posting lists with only occurrence information (bitvector). These are generated for common words.
  Files: `boolocc.bdat`, `boolocc.idx`.

Example:

```
{% highlight sh%}
$ pwd
/opt/vespa/var/db/vespa/search/cluster.mycluster/n1/documents/myschema/0.ready/index/index.flush.1/myfield
$ ls -la
total 7632
drwxr-xr-x  2 org users     145 Oct 29 06:09 .
drwxr-xr-x 74 org users    4096 Oct 29 06:11 ..
-rw-r--r--  1 org users    4096 Oct 29 06:11 boolocc.bdat
-rw-r--r--  1 org users    4096 Oct 29 06:11 boolocc.idx
-rw-r--r--  1 org users    8192 Oct 29 06:11 dictionary.pdat
-rw-r--r--  1 org users    8192 Oct 29 06:11 dictionary.spdat
-rw-r--r--  1 org users    4120 Oct 29 06:11 dictionary.ssdat
-rw-r--r--  1 org users 7778304 Oct 29 06:11 posocc.dat.compressed
{% endhighlight %}
```

Note that `boolocc`-files are empty if the number of occurrences is small, like in the example above.

## Proton maintenance jobs

The memory and disk data structures used in Proton are
periodically optimized by a set of maintenance jobs.
These jobs are automatically executed, and some can be tuned in
[flush strategy tuning](reference/services-content.html#flushstrategy).
All jobs are described in the table below.

There is only one instance of each job at a time - e.g., attributes are flushed in sequence.
When a job is running, its metric is set to 1 - otherwise 0.
Use this to correlate observed performance or resource usage with job runs - see *Run metric* below.

The *temporary* resources used when jobs are executed are described in *CPU*, *Memory* and *Disk*.
The memory and disk usage metrics of components that are optimized by the jobs
are described in *Metrics* (with *Metric prefix*).
For a list of all available Proton metrics, refer to the searchnode metrics in the
[Vespa Metric Set](reference/vespa-set-metrics-reference.html#searchnode-metrics).
Metrics are available at the [Metrics API](operations/metrics.html).

| Job | Description |
| --- | --- |
| attribute flush | Flush an [attribute](attributes.html) vector from memory to disk, based on the configuration in the [flush strategy](reference/services-content.html#flushstrategy). This ensures that Proton starts quicker - see [flush on shutdown](reference/services-content.html#flush-on-shutdown). An attribute flush also releases memory after a [LID-space compaction](#lid-space-compaction). | |  |
| CPU | Little - one thread flushes to disk |
| Memory | Little - some temporary use |
| Disk | A new file is written too, so 2x the size of an attribute on disk until the old flush file is deleted. |
| Run metric | *content.proton.documentdb.job.attribute_flush* |
| Metric prefix | *content.proton.documentdb.[ready|notready].attribute.memory_usage.* |
| Metrics | *allocated_bytes.average  used_bytes.average  dead_bytes.average  onhold_bytes.average* |
| memory index flush | Flush a *memory index* to disk, then trigger [disk index fusion](#disk-index-fusion). The goal is to shrink memory usage by adding to the disk-backed indices. Note: A high feed rate can cause multiple smaller flushed indices, like *$VESPA_HOME/var/db/vespa/search/cluster.name/n1/documents/doc/0.ready/index/index.flush.102* - see the high index number. Multiple smaller indices are a symptom of too small memory indices compared to the feed rate - to fix, increase [flushstrategy > native > component > maxmemorygain](reference/services-content.html#flushstrategy). | |
| CPU | Little - one thread flushes to disk |
| Memory | Little |
| Disk | Creates a new disk index, size of the memory index. |
| Run metric | *content.proton.documentdb.job.memory_index_flush* |
| Metric prefix | *content.proton.documentdb.index.memory_usage.* |
| Metrics | *allocated_bytes.average  used_bytes.average  dead_bytes.average  onhold_bytes.average* |
| disk index fusion | Merge the primary disk index with smaller indices generated by [memory index flush](#memory-index-flush) - triggered by the memory index flush. | |
| CPU | Multiple threads merge indices, configured as a function of [feeding concurrency](reference/services-content.html#feeding-concurrency) - refer to this for details |
| Memory | Little |
| Disk | Creates a new index while serving from the current: 2x temporary disk usage for the given index. |
| Run metric | *content.proton.documentdb.job.disk_index_fusion* |
| document store flush | Flushes the [document store](#memory-usage). | |
| CPU | Little |
| Memory | Little |
| Disk | Little |
| Run metric | *content.proton.documentdb.job.document_store_flush* |
| document store compaction | Defragment and sort [document store](#document-store) files as documents are updated and deleted, in order to reduce disk usage. The file is sorted in bucket order on output. Triggered by [diskbloatfactor](reference/services-content.html#flushstrategy-native-total-diskbloatfactor). | |
| CPU | Little - one thread reads one file, sorts and writes a new file |
| Memory | Holds a document store file in memory plus memory for sorting the file. **Note: This is important on hosts with little memory!** Reduce [maxfilesize](reference/services-content.html#summary-store-logstore-maxfilesize) to increase the number of files and use less temporary memory for compaction. |
| Disk | A new file is written while the current is serving, max temporary usage is 2x. |
| Run metric | *content.proton.documentdb.job.document_store_compact* |
| Metric prefix | *content.proton.documentdb.[ready|notready|removed].document_store.* |
| Metrics | *disk_usage.average  disk_bloat.average  max_bucket_spread.average  memory_usage.allocated_bytes.average  memory_usage.used_bytes.average  memory_usage.dead_bytes.average  memory_usage.onhold_bytes.average* |
| bucket move | Triggered by nodes going up/down, refer to [content cluster elasticity](elasticity.html) and [searchable-copies](reference/services-content.html#searchable-copies). It causes documents to be indexed or de-indexed, similar to feeding. This moves documents between the *ready* and *not ready* sub-databases. | |
| CPU | CPU similar to feeding. Consumes capacity from the write threads, so has feeding impact |
| Memory | As feeding - e.g., the attribute memory usage and memory index in the *ready* sub-database will grow |
| Disk | As feeding |
| Run metric | *content.proton.documentdb.job.bucket_move* |
| lid-space compaction | Each sub-database has a [document meta store](attributes.html#document-meta-store) that manages a local document id space (LID-space). When a [cluster grows](elasticity.html) with more nodes, documents are redistributed to new nodes, and each node ends up with fewer documents. The result is holes in the LID-space, and a compaction is triggered when the bloat is above 1%. This in-place defragments the [document meta store](attributes.html#document-meta-store) and [attribute](attributes.html) vectors by moving documents from high to low LIDs inside the sub-database. Resources are freed on a subsequent [attribute flush](#attribute-flush). | |
| CPU | Like feeding - add and remove documents |
| Memory | Little |
| Disk | 0 |
| Run metric | *content.proton.documentdb.job.lid_space_compact* |
| Metric prefix | *content.proton.documentdb.[ready|notready|removed].lid_space.* |
| Metrics | *lid_limit.last  lid_bloat_factor.average  lid_fragmentation_factor.average* |
| removed documents pruning | Prunes the *removed* sub-database, which keeps IDs for deleted documents. See [removed-db](/en/reference/services-content.html#removed-db) for details. | |
| CPU | Little |
| Memory | Little |
| Disk | Little |
| Run metric | *content.proton.documentdb.job.removed_documents_prune* |

## Retrieving documents

Retrieving documents is done by specifying an id to *get*,
or use a [selection expression](reference/document-select-language.html)
to *visit* a range of documents - refer to the [Document API](api.html).
Overview:

![Retrieving documents](/assets/img/elastic-visit-get.svg)

|  |  |
| --- | --- |
| Get | When the content node receives a get request, it scans through all the document databases, and for each one, it checks all three sub-databases. Once the document is found, the scan is stopped and the document returned. If the document is found in a Ready sub-database, the document retriever will apply any changes that are stored in the [attributes](attributes.html) before returning the document. |
| Visit | A visit request creates an iterator over each candidate bucket. This iterator will retrieve matching documents from all sub-databases of all document databases. As for get, attribute values are applied to document fields in the Ready sub-database. |

## Queries

Queries have a separate pathway through the system.
They do not use the distributor, nor do they go through the content node persistence threads.
They are orthogonal to the elasticity set up by the storage and retrieval described above.
How queries move through the system:

![Queries](/assets/img/proton-query.svg)

A query enters the system through the *QR-server (query rewrite server)*
in the [Vespa Container](jdisc/).
The QR-server issues one query per document type to the search nodes:

|  |  |
| --- | --- |
| Container | The Container knows all the document types and rewrites queries as a collection of queries, one for each type. Queries may have a [restrict](reference/query-api-reference.html#model.restrict) parameter, in which case the container will send the query only to the specified document types.  It sends the query to content nodes and collects partial results. It pings all content nodes every second to know whether they are alive, and keeps open TCP connections to each one. If a node goes down, the elastic system will make the documents available on other nodes. |
| Content node matching | The *match engine*  receives queries and routes them to the right document database based on the document type. The query is passed to the *Ready* sub-database, where the searchable documents are. Based on information stored in the document meta store, the query is augmented with a blocklist that ensures only *active* documents are matched. |

## /state/v1 API

Besides the common endpoints documented in the
[/state/v1 API reference](reference/state-v1.html), Proton has additional endpoints
as part of the /state/v1 API that expose information about the internal state of a search node.
This API is available at `http://host:stateport/state/v1/`.

Run [vespa-model-inspect](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect)
to find the JSON HTTP stateport:

```
vespa-model-inspect service searchnode
```

### Initialization Progress API

The initialization progress can be found by HTTP GET at `http://host:stateport/state/v1/initialization`.
This endpoint becomes available early during initialization of Proton when other endpoints are not yet available.
It gives a human-readable overview of the document databases and their attributes being loaded.
Note that this is **not** a stable API, and it will expand and change between releases.

Example `state/v1/initialization`:

```
{% highlight json %}
{
  "state": "initializing",
  "current_time": "1758873251.933488",
  "start_time": "1758873249.715624",
  "load": 1,
  "replay_transaction_log": 0,
  "online": 0,
  "dbs": [
    {
      "state": "load",
      "start_time": "1758873249.936939",
      "name": "dbname",
      "ready_subdb": {
        "loaded_attributes": [
          {
            "state": "loaded",
            "start_time": "1758873249.941415",
            "name": "int_field",
            "end_time": "1758873249.942051"
          },
          {
            "state": "loaded",
            "start_time": "1758873249.941498",
            "name": "string_field",
            "end_time": "1758873249.944647"
          }
        ],
        "loading_attributes": [
          {
            "state": "reprocessing",
            "start_time": "1758873249.941555",
            "name": "tensor_field",
            "reprocess_progress": "6.061879",
            "reprocess_start_time": "1758873249.993847"
          }
        ],
        "queued_attributes": [

        ]
      }
    }
  ]
}
{% endhighlight %}
```

### Custom Component State API

The custom component status can be found by HTTP GET at `http://host:stateport/state/v1/custom/component`.
It gives an overview of the relevant search node components and their internal state.
Note that this is **not** a stable API, and it will expand and change between releases.

Example `state/v1/custom/component`:

```
{% highlight json %}
{
    "documentdb": {
        "mydoctype": {
            "documentType": "mydoctype",
            "status": {
                "state": "ONLINE",
                "configState": "OK"
            },
            "documents": {
                "active": 10,
                "ready": 10,
                "total": 10,
                "removed": 0
            },
            "url": "http://host:stateport/state/v1/custom/component/documentdb/mydoctype"
        }
    },
    "threadpools": {
        "url": "http://host:stateport/state/v1/custom/component/threadpools"
    },
    "matchengine": {
        "status": {
            "state": "ONLINE"
        },
        "url": "http://host:stateport/state/v1/custom/component/matchengine"
    },
    "flushengine": {
        "url": "http://host:stateport/state/v1/custom/component/flushengine"
    },
    "tls": {
        "url": "http://host:stateport/state/v1/custom/component/tls"
    },
    "hwinfo": {
        "url": "http://host:stateport/state/v1/custom/component/hwinfo"
    },
    "resourceusage": {
        "url": "http://host:stateport/state/v1/custom/component/resourceusage",
        "disk": 0.25,
        "memory": 0.35,
        "attribute_address_space": 0
    },
    "session": {
        "search": {
            "url": "http://host:stateport/state/v1/custom/component/session/search",
            "numSessions": 0
        }
    }
}
{% endhighlight %}
```

Example `state/v1/custom/component/documentdb/mydoctype`:

```
{% highlight json %}
{
    "documentType": "mydoctype",
    "status": {
        "state": "ONLINE",
        "configState": "OK"
    },
    "documents": {
        "active": 10,
        "ready": 10,
        "total": 10,
        "removed": 0
    },
    "subdb": {
        "removed": {
            "url": "http://host:stateport/state/v1/custom/component/documentdb/mydoctype/subdb/removed"
        },
        "ready": {
            "url": "http://host:stateport/state/v1/custom/component/documentdb/mydoctype/subdb/ready"
        },
        "notready": {
            "url": "http://host:stateport/state/v1/custom/component/documentdb/mydoctype/subdb/notready"
        }
    },
    "threadingservice": {
        "url": "http://host:stateport/state/v1/custom/component/documentdb/mydoctype/threadingservice"
    },
    "bucketdb": {
        "url": "http://host:stateport/state/v1/custom/component/documentdb/mydoctype/bucketdb",
        "numBuckets": 1
    },
    "maintenancecontroller": {
        "url": "http://host:stateport/state/v1/custom/component/documentdb/mydoctype/maintenancecontroller"
    }
}
{% endhighlight %}
```
