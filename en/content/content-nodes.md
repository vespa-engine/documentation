---
# Copyright Vespa.ai. All rights reserved.
title: "Content nodes, states and metrics"
---

![Content cluster overview](/assets/img/elastic-feed.svg)

Content cluster processes are *distributor*, *proton* and *cluster controller*.

The distributor calculates the correct content node using
the distribution algorithm and the [cluster state](#cluster-state).
With no known cluster state, the client library will send requests to a random node,
which replies with the updated cluster state if the node was incorrect.
Cluster states are versioned, such that clients hitting outdated distributors do not override
updated states with old states.

The [distributor](#distributor) keeps track of
which content nodes that stores replicas of each bucket (maximum one replica each),
based on [redundancy](../reference/services-content.html#redundancy)
and information from the *cluster controller*.
A bucket maps to one distributor only.
A distributor keeps a bucket database with bucket metadata.
The metadata holds which content nodes store replicas of the buckets,
the checksum of the bucket content and the number of documents and meta entries within the bucket.
Each document is algorithmically mapped to a bucket and forwarded to the correct content nodes.
The distributors detect whether there are enough bucket replicas on the
content nodes and add/remove as needed.
Write operations wait for replies from every replica
and fail if less than redundancy are persisted within timeout.

The [cluster controller](#cluster-controller)
manages the state of the distributor and content nodes.
This *cluster state* is used by the document processing chains
to know which distributor to send documents to,
as well as by the distributor to know which content nodes should have which bucket.

## Cluster state

There are three kinds of state: [unit state](../reference/cluster-v2.html#state-unit),
[user state](../reference/cluster-v2.html#state-user) and
[generated state](../reference/cluster-v2.html#state-generated) (a.k.a. *cluster state*).

For new cluster states, the cluster state version is incremented,
and the new cluster state is broadcast to all nodes.
There is a minimum time between each cluster state change.

It is possible to set a minimum capacity for the cluster state to be `up`.
If a cluster has so many nodes unavailable that it is considered down,
the state of each node is irrelevant,
and thus new cluster states will not be created and broadcast
before enough nodes are back for the cluster to come back up.
A cluster state indicating the entire cluster is down,
may thus have outdated data on the node level.

## Cluster controller

The main task of the cluster controller is to maintain the [cluster state](#cluster-state).
This is done by *polling* nodes for state,
*generating* a cluster state,
which is then *broadcast* to all the content nodes in the cluster.
Note that clients do not interface with the cluster controller -
they get the cluster state from the distributors - [details](#distributor).

| Task | Description |
| --- | --- |
| Node state polling | The cluster controller polls nodes, sending the current cluster state. If the cluster state is no longer correct, the node returns correct information immediately. If the state is correct, the request lingers on the node, such that the node can reply to it immediately if its state changes. After a while, the cluster controller will send a new state request to the node, even with one pending. This triggers a reply to the lingering request and makes the new one linger instead. Hence, nodes have a pending state request.  During a controlled node shutdown, it starts the shutdown process by responding to the pending state request that it is now stopping. {% include note.html content='As controlled restarts or shutdowns are implemented as TERM signals from the [config-sentinel](/en/operations-selfhosted/config-sentinel.html), the cluster controller is not able to differ between controlled and other shutdowns.' %} |
| Cluster state generation | The cluster controller translates unit and user states into the generated *cluster state* |
| Cluster state broadcast | When node unit states are received, a cluster controller internal cluster state is updated. New cluster states are distributed with a minimum interval between.  A grace period per unit state too - e.g., distributors and content nodes that are on the same node often stop at the same time.  The version number is incremented, and the new cluster state is broadcast.  If cluster state version is [reset](../operations-selfhosted/admin-procedures.html#cluster-state), distributors and content node processes may have to be restarted in order for the system to converge to the new state. Nodes will reject lower cluster state versions to prevent race conditions caused by overlapping cluster controller leadership periods. |

See [cluster controller configuration](../operations-selfhosted/admin-procedures.html#cluster-controller-configuration).

### Master election

Vespa can be configured with one cluster controller.
Reads and writes will work well in case of cluster controller down,
but other changes to the cluster (like a content node going down) will not be handled.
It is hence recommended to configure a set of cluster controllers.

The cluster controller nodes elect a master,
which does the node polling and cluster state broadcast.
The other cluster controller nodes only exist to do master election
and potentially take over if the master dies.

All cluster controllers will vote for the cluster controller with the lowest index that says it is ready.
If a cluster controller has more than half of the votes, it will be elected master.
As a majority vote is required,
the number of cluster controllers should be an odd number of 3 or greater.
A fresh master will not broadcast states before a transition time is passed,
allowing an old master to have some time to realize it is no longer the master.

## Distributor

Buckets are mapped to distributors using the [ideal state algorithm](idealstate.html).
As the cluster state changes, buckets are re-mapped immediately.
The mapping does not overlap -
a bucket is owned by one distributor.

Distributors do not persist the bucket database,
the bucket-to-content-node mapping is kept in memory in the distributor.
Document count, persisted size and a metadata checksum per bucket is stored as well.
At distributor (re)start, content nodes are polled for bucket information,
and return which buckets are owned by this distributor (using the ideal state algorithm).
There is no centralized bucket directory node.
Likewise, at any distributor cluster state change,
content nodes are polled for bucket handover -
a distributor will then handle a new set of buckets.

Document operations are mapped to content nodes based on bucket locations -
each put/update/get/remove is mapped to a [bucket](buckets.html)
and sent to the right content nodes.
To manage the document set as it grows and nodes change, buckets move between content nodes.

Document API clients (i.e. container nodes with
[<document-api>](../reference/services-container.html#document-api))
do not communicate directly with the cluster controller, and do not know the cluster state at startup.
Clients therefore start out by sending requests to a random distributor.
If the document operation hits the wrong distributor,
`WRONG_DISTRIBUTION` is returned, with the current cluster state in the response.
`WRONG_DISTRIBUTION` is hence expected and normal at cold start / state change events.

### Timestamps

[Write operations](../reads-and-writes.html)
have a *last modified time* timestamp assigned when passing through the distributor.
The timestamp is guaranteed to be unique within the
[bucket](buckets.html) where it is stored.
The timestamp is used by the content layer to decide which operation is newest.
These timestamps can be used when [visiting](../visiting.html),
to process/retrieve documents within a given time range.
To guarantee unique timestamps, they are in microseconds -
the microsecond part is generated to avoid conflicts with other documents.

If documents are migrated *between* clusters,
the target cluster will have new timestamps for their entries.
Also, when [reprocessing documents](../document-processing.html) *within* a cluster,
documents will have new timestamps, even if not modified.

### Ordering

The Document API uses the [document ID](../documents.html#document-ids) to order operations.
A Document API client ensures that only one operation is pending at the same time.
This ensures that if a client sends multiple operations for the same document,
they will be processed in a defined order. This is done by queueing pending
operations *locally* at the client.

{% include note.html content='If sending two write operations to the same document,
and the first operation fails, the enqueued operation is sent. In other words, the
client does not assume there exists any kind of dependency between separate
operations to the same document. If you need to enforce this, use
[test-and-set conditions](../document-v1-api-guide.html#conditional-writes)
for writes.' %}

If *different* clients have pending operations on the same document,
the order is unspecified.

### Maintenance operations

Distributors track which content nodes have which buckets in their bucket database.
Distributors then use the [ideal state algorithm](idealstate.html)
to generate bucket *maintenance operations*.
A stable system has all buckets located per the ideal state:
* If buckets have too few replicas, new are generated on other content nodes.
* If the replicas differ, a bucket merge is issued to get replicas consistent.
* If a buckets has too many replicas, superfluous are deleted.
  Buckets are merged, if inconsistent, before deletion.
* If two buckets exist, such that both may contain the same document,
  the buckets are split or joined to remove such overlapping buckets.
  Read more on [inconsistent buckets](buckets.html).
* If buckets are too small/large, they will be joined or split.

The maintenance operations have different priorities.
If no maintenance operations are needed, the cluster is said to be in the *ideal state*.
The distributors synchronize maintenance load with user load,
e.g. to remap requests to other buckets after bucket splitting and joining.

### Restart

When a distributor stops, it will try to respond to any pending cluster state request first.
New incoming requests after shutdown is commenced will fail immediately,
as the socket is no longer accepting requests.
Cluster controllers will thus detect processes stopping almost immediately.

The cluster state will be updated with the new state internally in the cluster controller.
Then the cluster controller will wait for maximum
[min_time_between_new_systemstates](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/fleetcontroller.def)
before publishing the new cluster state - this to reduce short-term state fluctuations.

The cluster controller has the option of setting states to make other
distributors take over ownership of buckets, or mask the change, making the
buckets owned by the distributor restarting unavailable for the time being.

If the distributor transitions from `up` to `down`,
other distributors will request metadata from the content nodes to take
over ownership of buckets previously owned by the restarting distributor.
Until the distributors have gathered this new metadata from all the content
nodes, requests for these buckets can not be served, and will fail back to client.
When the restarting node comes back up and is marked `up` in the cluster state again,
the additional nodes will discard knowledge of the extra buckets they previously acquired.

For requests with timeouts of several seconds,
the transition should be invisible due to automatic client resending.
Requests with a lower timeout might fail,
and it is up to the application whether to resend or handle failed requests.

Requests to buckets not owned by the restarting distributor will not be affected.

## Content node

The content node runs *proton*, which is the query backend.

### Restart

When a content node does a controlled restart,
it marks itself in the `stopping` state and rejects new requests.
It will process its pending request queue before shutting down.
Consequently, client requests are typically unaffected by content node restarts.
The currently pending requests will typically be completed.
New copies of buckets will be created on other nodes, to store new requests in appropriate redundancy.
This happens whether node transitions through `down` or `maintenance` state.
The difference being that if transitioning through `maintenance`,
the distributor will not start any effort of synchronizing new copies with existing copies.
They will just store the new requests until the maintenance node comes back up.

When starting, content nodes will start with gathering information
on what buckets it has data stored for.
While this is happening, the service layer will expose that it is `down`.

## Metrics

| Metric | Description |
| --- | --- |
| .idealstate.idealstate_diff | This metric tries to create a single value indicating distance to the ideal state. A value of zero indicates that the cluster is in the ideal state. Graphed values of this metric gives a good indication for how fast the cluster gets back to the ideal state after changes. Note that some issues may hide other issues, so sometimes the graph may appear to stand still or even go a bit up again, as resolving one issue may have detected one or several others. |
| .idealstate.buckets_toofewcopies | Specifically lists how many buckets have too few copies. Compare to the *buckets* metric to see how big a portion of the cluster this is. |
| .idealstate.buckets_toomanycopies | Specifically lists how many buckets have too many copies. Compare to the *buckets* metric to see how big a portion of the cluster this is. |
| .idealstate.buckets | The total number of buckets managed. Used by other metrics reporting bucket counts to know how big a part of the cluster they relate to. |
| .idealstate.buckets_notrusted | Lists how many buckets have no trusted copies. Without trusted buckets operations against the bucket may have poor performance, having to send requests to many copies to try and create consistent replies. |
| .idealstate.delete_bucket.pending | Lists how many buckets that needs to be deleted. |
| .idealstate.merge_bucket.pending | Lists how many buckets there are, where we suspect not all copies store identical document sets. |
| .idealstate.split_bucket.pending | Lists how many buckets are currently being split. |
| .idealstate.join_bucket.pending | Lists how many buckets are currently being joined. |
| .idealstate.set_bucket_state.pending | Lists how many buckets are currently altered for active state. These are high priority requests which should finish fast, so these requests should seldom be seen as pending. |

Example, using the [quickstart](../vespa-quick-start.html) -
find the distributor port (look for HTTP):

```
$ docker exec vespa vespa-model-inspect service distributor

distributor @ vespa-container : content
music/distributor/0
    tcp/vespa-container:19112 (MESSAGING)
    tcp/vespa-container:19113 (STATUS RPC)
    tcp/vespa-container:19114 (STATE STATUS HTTP)
```

Get the metric value:

```
$ docker exec vespa curl -s http://localhost:19114/state/v1/metrics | jq . | \
  grep -A 10 idealstate.merge_bucket.pending

        "name": "vds.idealstate.merge_bucket.pending",
        "description": "The number of operations pending",
        "values": {
          "average": 0,
          "sum": 0,
          "count": 1,
          "rate": 0.016666,
          "min": 0,
          "max": 0,
          "last": 0
        },
```

## /cluster/v2 API examples

Examples of state manipulation using the [/cluster/v2 API](../reference/cluster-v2.html).

List content clusters:

```
$ curl http://localhost:19050/cluster/v2/
```
```
{% highlight json %}
{
    "cluster": {
        "music": {
            "link": "/cluster/v2/music"
        },
        "books": {
            "link": "/cluster/v2/books"
        }
    }
}
{% endhighlight %}
```

Get cluster state and list service types within cluster:

```
$ curl http://localhost:19050/cluster/v2/music
```
```
{% highlight json %}
{
    "state": {
        "generated": {
            "state": "state-generated",
            "reason": "description"
        }
    }
    "service": {
        "distributor": {
            "link": "/cluster/v2/music/distributor"
        },
        "storage": {
            "link": "/cluster/v2/music/storage"
        }
    }
 }
{% endhighlight %}
```

List nodes per service type for cluster:

```
$ curl http://localhost:19050/cluster/v2/music/storage
```
```
{% highlight json %}
{
    "node": {
        "0": {
            "link": "/cluster/v2/music/storage/0"
        },
        "1": {
            "link": "/cluster/v2/music/storage/1"
        }
    }
}
{% endhighlight %}
```

Get node state:

```
$ curl http://localhost:19050/cluster/v2/music/storage/0
```
```
{% highlight json %}
{
    "attributes": {
        "hierarchical-group": "group0"
    },
    "state": {
        "generated": {
            "state": "up",
            "reason": ""
        },
        "unit": {
            "state": "up",
            "reason": ""
        },
        "user": {
            "state": "up",
            "reason": ""
        }
    },
    "metrics": {
        "bucket-count": 0,
        "unique-document-count": 0,
        "unique-document-total-size": 0
    }
}
{% endhighlight %}
```

Get all nodes, including topology information (see `hierarchical-group`):

```
$ curl http://localhost:19050/cluster/v2/music/?recursive=true
```
```
{% highlight json %}
{
    "state": {
        "generated": {
            "state": "up",
            "reason": ""
        }
    },
    "service": {
        "storage": {
            "node": {
                "0": {
                    "attributes": {
                        "hierarchical-group": "group0"
                    },
                    "state": {
                        "generated": {
                            "state": "up",
                            "reason": ""
                        },
                        "unit": {
                            "state": "up",
                            "reason": ""
                        },
                        "user": {
                            "state": "up",
                            "reason": ""
                        }
                    },
                    "metrics": {
                        "bucket-count": 0,
                        "unique-document-count": 0,
                        "unique-document-total-size": 0
                    }
{% endhighlight %}
```

Set node user state:

```
curl -X PUT -H "Content-Type: application/json" --data '
  {
      "state": {
          "user": {
              "state": "retired",
              "reason": "This node will be removed soon"
          }
      }
  }' \
  http://localhost:19050/cluster/v2/music/storage/0
```
```
{% highlight json %}
{
    "wasModified": true,
    "reason": "ok"
}
{% endhighlight %}
```

## Further reading
* Refer to [administrative procedures](../operations-selfhosted/admin-procedures.html)
  for configuration and state monitoring / management.
* Try the [Multinode testing and observability](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode) sample app to get familiar with interfaces and behavior.
