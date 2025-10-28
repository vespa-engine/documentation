---
# Copyright Vespa.ai. All rights reserved.
title: "/cluster/v2 API reference"
redirect_from:
- /en/content/api-state-rest-api.html
---

The cluster controller has a /cluster/v2 API for viewing and modifying a content cluster state.
To find the URL to access this API, identify the [cluster controller services](../content/content-nodes.html#cluster-controller) in the application.
Only the master cluster controller will be able to respond.
The master cluster controller is the cluster controller alive that has the lowest index.
Thus, one will typically use cluster controller 0, but if contacting it fails, try number 1 and so on.
Using [vespa-model-inspect](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect):

```
$ vespa-model-inspect service -u container-clustercontroller

container-clustercontroller @ hostname.domain.com : admin
admin/cluster-controllers/0
    http://hostname.domain.com:19050/ (STATE EXTERNAL QUERY HTTP)
    http://hostname.domain.com:19117/ (EXTERNAL HTTP)
    tcp/hostname.domain.com:19118 (MESSAGING RPC)
    tcp/hostname.domain.com:19119 (ADMIN RPC)
```

In this example, there is only one clustercontroller, and the State Rest API is
available on the port marked STATE and HTTP, 19050 in this example.
This information can also be retrieved through the model config in the config server.

Find examples of API usage in [content nodes](../content/content-nodes.html#cluster-v2-API-examples).

## HTTP requests

| HTTP request | cluster/v2 operation | Description |
| --- | --- | --- |
| GET | List cluster and nodes. Get cluster, node or disk states. | |
|  | List content clusters | ``` /cluster/v2/ ``` |
|  | Get cluster state and list service types within cluster | ``` /cluster/v2/<cluster> ``` |
|  | List nodes per service type for cluster | ``` /cluster/v2/<cluster>/<service-type> ``` |
|  | Get node state | ``` /cluster/v2/<cluster>/<service-type>/<node> ``` |
| PUT | Set node state | |
|  | Set node user state | ``` /cluster/v2/<cluster>/<service-type>/<node> ``` |

## Node state

Content and distributor nodes have state:

| State | Description |
| --- | --- |
| `Up` | The node is up and available to keep buckets and serve requests. |
| `Down` | The node is not available, and can not be used. |
| `Stopping` | This node is stopping and is expected to be down soon. This state is typically only exposed to the cluster controller to tell why the node stopped. The cluster controller will expose the node as down or in maintenance mode for the rest of the cluster. This state is thus not seen by the distribution algorithm. |
| `Maintenance` | This node is temporarily unavailable. The node is available for bucket placement, so redundancy is lower.  Using this mode, new replicas of the documents stored on this node will not be created, allowing the node to be down with less of a performance impact on the rest of the cluster. This mode is typically used to mask a down state during controlled node restarts, or by an administrator that need to do some short maintenance work, like upgrading software or restart the node. |
| `Retired` | A retired node is available and serves requests. This state is used to remove nodes while keeping redundancy. Buckets are moved to other nodes (with low priority), until empty. Special considerations apply when using [grouped distribution](../elasticity.html#grouped-distribution) as buckets are not necessarily removed. |

Distributor nodes start / transfer buckets quickly
and are hence not in `maintenance` or `retired`.

Refer to [examples](../content/content-nodes.html#cluster-v2-API-examples) of manipulating states.

## Types

| Type | Spec | Description |
| --- | --- | --- |
| cluster | *<identifier>* | The name given to a content cluster in a Vespa application. |
| description | *.** | Description can contain anything that is valid JSON. However, as the information is presented in various interfaces, some which may present reasons for all the states in a cluster or similar, keeping it short and to the point makes it easier to fit the information neatly into a table and get a better cluster overview. |
| group-spec | *<identifier>*(\.*<identifier>*)* | The hierarchical group assignment of a given content node. This is a dot separated list of identifiers given in the application services.xml configuration. |
| node | [0-9]+ | The index or distribution key identifying a given node within the context of a content cluster and a service type. |
| service-type | (distributor|storage) | The type of the service to look at state for, within the context of a given content cluster. |
| state-disk | (up|down) | One of the valid disk states. |
| state-unit | [up](#up) | [stopping](#stopping) | [down](#down) | The cluster controller fetches states from all nodes, called *unit states*. States reported from the nodes are either `up` or `stopping`. If the node can not be reached, a `down` state is assumed.  This means, the cluster controller detects failed nodes. The subsequent *generated states* will have nodes in `down`, and the [ideal state algorithm](../content/idealstate.html) will redistribute [buckets](../content/buckets.html) of documents. |
| state-user | [up](#up) | [down](#down) | [maintenance](#maintenance) | [retired](#retired) | Use tools for [user state management](/en/operations-selfhosted/admin-procedures.html#cluster-state).   * Retire a node from a cluster -   use `retired` to move buckets to other nodes * Short-lived maintenance work -   use `maintenance` to avoid merging buckets to other nodes * Fail a bad node. The cluster controller or an operator can set a node `down` |
| state-generated | [up](#up) | [down](#down) | [maintenance](#maintenance) | [retired](#retired) | The cluster controller generates the cluster state from the `unit` and `user` states, over time. The generated state is called the *cluster state*. |

## Request parameters

| Parameter | Type | Description |
| --- | --- | --- |
| recursive | number | Number of levels, or `true` for all levels. Examples:   * Use `recursive=1` for a node request to also see all data * use `recursive=2` to see all the node data within each service type   In recursive mode, you will see the same output as found in the spec below. However, where there is a `{ "link" : "<url-path>" }` element, this element will be replaced by the content of that request, given a recursive value of one less than the request above. |

## HTTP status codes

Non-exhaustive list of status codes:

| Code | Description |
| --- | --- |
| 200 | OK. |
| 303 | Cluster controller not master - master known.  This error means communicating with the wrong cluster controller. This returns a standard HTTP redirect, so the HTTP client can automatically redo the request on the correct cluster controller.  As the cluster controller available with the lowest index will be the master, the cluster controllers are normally queried in index order. Hence, it is unlikely to ever get this error, but rather fail to connect to the cluster controller if it is not the current master.   ``` HTTP/1.1 303 See Other Location: http://<master>/<current-request> Content-Type: application/json  {     "message" : "Cluster controller index not master. Use master at index index. } ``` |
| 503 | Cluster controller not master - unknown or no master.  This error is used if the cluster controller asked is not master, and it doesn't know who the master is. This can happen, e.g. in a network split, where cluster controller 0 no longer can reach cluster controller 1 and 2, in which case cluster controller 0 knows it is not master, as it can't see the majority, and cluster controller 1 and 2 will vote 1 to master.   ``` HTTP/1.1 503 Service Unavailable Content-Type: application/json  {     "message" : "No known master cluster controller currently exist." } ``` |

## Response format

Responses are in JSON format, with the following fields:

| Field | Description |
| --- | --- |
| message | An error message — included for failed requests. |
| ToDo | Add more fields here. |
