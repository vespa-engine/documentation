---
# Copyright Vespa.ai. All rights reserved.
title: "Distribution Algorithm"
---

The distribution algorithm decides what nodes should be responsible for a given bucket.
This is used directly in the clients to calculate distributor to talk to.
Content nodes need time to move buckets when the distribution is changing,
so routing to content nodes is done using tracked current state.
The distribution algorithm decides which content nodes is wanted to store the bucket copies though,
and due to this, the algorithm is also referred to as the ideal state algorithm.

The input to the distribution algorithm is a bucket identifier,
together with knowledge about what nodes are available, and what their capacities are.

The output of the distribution algorithm is a sorted list of the available nodes.
The first node in the order is the node most preferred to handle a given bucket.
Currently, the highest order distributor node will be the owning distributor,
and the redundancy factor decides how many of the highest order content nodes
are preferred to store copies for a bucket.

To enable minimal transfer of buckets when the list of available nodes changes,
the removal or addition of nodes should not alter the sort order of the remaining nodes.

Desired qualities for the ideal state algorithm:

| Minimal reassignment on cluster state change | * If a node goes down, only buckets that resided on that node should be reassigned. * If a node comes up, only buckets that are moved to the new node should relocate. * Increasing the capacity of a single node should only move buckets to that node. * Reducing the capacity of a single node should only move buckets away from that node. |
| No skew in distribution | * Nodes should get an amount of data relative to their capacity. |
| Lightweight | * A simple algorithm that is easy to understand is a plus.   Being lightweight to calculate is also a plus, giving more options of how to use it,   without needing to cache results. |

## Computational cost

When considering how efficient the algorithm have to be,
it is important to consider how often we need to calculate the ideal locations.
Calculations are needed for the following tasks:
* A client needs to map buckets to the distributors.
  If there are few buckets existing, all the results can be cached in clients,
  but for larger clusters, a lot of buckets may need to exist to create an even distribution,
  and caching becomes more memory intensive.
  Preferably the computational cost is cheap enough, such that no caching is needed.
  Currently, no caching is done by clients, but there is typically less than a million buckets,
  so caching all results would still have been viable.
* Distributors need to calculate ideal state for a single bucket
  to verify that incoming operations are mapped to the correct distributor
  (clients have cluster state matching the distributor).
  This could be eliminated for buckets pre-existing in the bucket database,
  which would be true in most all cases.
  Currently, calculation is done for all requests.
* Distributors need to calculate correct content nodes to create bucket
  copies on when operations to currently non-existing buckets come in.
  This is typically only something happening at the start of the cluster lifetime though.
  Normally buckets are created through splitting or joining existing buckets.
* Distributors need to calculate ideal state to check if any maintenance operations need to be done for a bucket.
* Content nodes need to calculate ideal state for a single bucket
  to verify that the correct distributor sent the request.
  This could be cached or served through bucket database but currently there is no need.

As long as the algorithm is cheap, we can avoid needing to cache the result.
The cache will then not limit scalability,
and we have less dependencies and complexity within the content layer.
The current algorithm has shown itself cheap enough, such that little caching has been needed.

## A simple example: Modulo

A simple approach would be to use a modulo operation to find the most preferred node,
and then just order the nodes in configured order from there,
skipping nodes that are currently not available:

$$\text{most preferred node} = \text{bucket % nodecount}$$

Properties:
* Computational lightweight and easy to understand
* Perfect distribution among nodes.
* Total redistribution on state change.

By just skipping currently unavailable nodes, nodes can go down and up with minimal movement.
However, if the number of configured nodes change,
practically all buckets will be redistributed.
As the content layer is intended to be scalable,
this breaks with one of the intentions and this algorithm has thus not been considered.

## Weighted random election

This is the algorithm that is currently used for distribution in the content layer,
as it fits our use case well.

To avoid a total redistribution on state change,
the mapping can not be heavily dependent on the number of nodes in the cluster.
By using random numbers, we can distribute the buckets randomly between the nodes,
in such a fashion that altering the cluster state has a small impact.
As we need the result to be reproducible,
we obviously need to use a pseudo-random number generator and not real random numbers.

The idea is as follows. To find the location of a given bucket,
seed a random number generator with the bucket identifier,
when draw one number for each node.
The drawn numbers will then decide upon the preferred node order for that specific bucket.

For this to be reproducible, all nodes need to draw the same numbers each time.
Each node is assigned a distribution key in the configuration.
This key decides what random number the node will be assigned.
For instance, a node with distribution key 13, will be assigned the 14th random number generated.
(As the first will go to the node with key 0).
The existence of this node then also requires us to always generate at least 14 random numbers
to do the calculation.

Thus, one may end up calculating random numbers for nodes that are currently not available,
either because they are temporarily down,
or because the configuration have left holes in the distribution key space.
It is recommended to not leave too large holes in the distribution key space to not waste too much.

Using this approach, if you add another node to the cluster, it will roll for each bucket.
It should thus steal ownership of some of the buckets.
As all the numbers are random, it will steal buckets from all the other nodes, thus,
given that the bucket count is large compared to the number of nodes,
it will steal on average 1/n of the buckets from each pre-existing node,
where n is the number of nodes in the current cluster.
Likewise, if a node is removed from the cluster,
the remaining nodes will divide the extra load between them.

### Weighting nodes

By enforcing all the numbers drawn to be floating point numbers between 0 and 1,
we can introduce node weights using the following formula:

$${r}^{\frac{1}{c}}$$

Where r is the floating point number between 0 and 1 that was drawn for a given node,
and c is the node capacity, which is the weight of the node.
Proof not included here, but this will end up giving each node on average an
amount of data that is relative to its capacity.
That is, among any nodes there are two nodes X and Y,
where the number of buckets given to X should be equal to the number of buckets
given to Y multiplied by capacity(X)/capacity(Y). (Given perfect random distribution)

Altering the weight in a running system will also create a minimal redistribution of data.
If we reduce the capacity, all the nodes number will be reduced,
and some of its buckets will be taken over by the other nodes,
and vice versa if the capacity is increased. Properties:
* Minimum data movement on state changes.
* Some skew, depending on how good the random number generator is, the
  amount of nodes we have to divide buckets between, and the number of
  buckets we have to divide between them.
* Fairly cheap to compute given a reasonable amount of nodes, and an
  inexpensive pseudo-random number generator.

### Distribution skew

The algorithm does generate a bit of skew in the distribution,
as it is essentially random. The following attributes decrease the skew:
* Having more buckets to distribute.
* Having less targets (nodes and partitions) to distribute buckets to.
* Having a more uniform pseudo-random function.

The more buckets exist, the more metadata needs to be tracked in the distributors though,
and operations that wants to scan all the buckets will take longer.
Additionally, the backend may want buckets above a given size to improve performance,
storage efficiency or similar.
Consequently, we typically want to enforce enough buckets for a decent distribution, but not more.

Then the number of nodes increase, more buckets need to exist to keep the distribution even.
If the number of nodes is doubled,
the number of buckets must typically more than double to keep the distribution equally even.
Thus, this scales worse than linear. It does not scale much worse though,
and this has not proved to be a practical problem for the cluster sizes we have used up until now.
(A cluster size of a thousand nodes does not seem to be any issue here)

Having a good and uniform pseudo-random function makes the distribution more even.
However, this may require more computationally heavy generators.
Currently, we are using a simple and fast algorithm,
and it has proved more than sufficient for our needs.

The distribution to distributors are done to create an even distribution between the nodes.
The distributors are free to split the buckets further if the backend wants buckets to contain less data.
They can not use fewer buckets than are needed for distribution though.
By using a minimum amount of buckets for distribution,
the distributors have more freedom to control sizes of buckets.

### Distribution waste

To measure how many buckets are needed to create a decent distribution a metric is needed.
We have defined a waste metric for this purpose as follows:

Distribute the buckets to all the units.
Assume the size of all units are identical.
Assume the unit with the most units assigned to it is at 100% capacity.
The wasted space is the percentage of unused capacity compared to the used capacity.

This definition seems useful as a cluster is considered at full capacity once
one of its partitions is at full capacity.
Having one node with more buckets than the rest is thus damaging,
while having one node with fewer buckets than the rest is just fine.

Example: There are 4 nodes distributing 18 units. The node with the most units has 6.
Distribution waste is `100% * (4 * 6 - 18) / (4 * 6) = 25%`.

Below we have calculated waste based on number of nodes and the amount of
buckets to distribute between them.
Bits refer to distribution bits used.
A distribution bit count of 16 indicates that there will be 216 buckets.

The calculations assume all buckets have the same size. This is normally close
to true as documents are randomly assigned to buckets.
There will be lots of buckets per node too, so a little variance typically evens out fairly well.

The tables below assume only one partition exist on each node.
If you have 4 partitions on 16 nodes, you should rather use the values for
`4 * 16 = 64` nodes.

A higher redundancy factor indicates more buckets to distribute between the same amount of nodes,
resulting in a more even distribution.
Doubling the redundancy has the same effect as adding one to the distribution bit count.
To get values for redundancy 4, the redundancy 2 values can be used,
and then the waste will be equal to the value with one less distribution bit used.

### Calculated waste from various cluster sizes

A value of 1 indicates 100% waste. A value of 0.1 indicates 10% waste.
A waste below 1 % is shown green, below 10% as yellow and below 30% as orange.
Red indicates more than 30% waste.

.td-green { background-color: #a3d977; }
.td-yellow { background-color: #ffdf71; }
.td-orange { background-color: #ffc374; }
.td-red { background-color: #ff8f80; }

#### Distribution with redundancy 1:

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bits \ Nodes | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| 1 | 0.0000 | 0.0000 | 0.3333 | 0.5000 | 0.6000 | 0.6667 | 0.7143 | 0.7500 | 0.7778 | 0.8000 | 0.8182 | 0.8333 | 0.8462 | 0.8571 | 0.8667 |
| 2 | 0.0000 | 0.3333 | 0.3333 | 0.5000 | 0.2000 | 0.3333 | 0.4286 | 0.5000 | 0.5556 | 0.6000 | 0.6364 | 0.6667 | 0.6923 | 0.7143 | 0.7333 |
| 3 | 0.0000 | 0.2000 | 0.1111 | 0.3333 | 0.2000 | 0.3333 | 0.6190 | 0.6667 | 0.8222 | 0.8400 | 0.8545 | 0.8333 | 0.6923 | 0.7143 | 0.7333 |
| 4 | 0.0000 | 0.1111 | 0.1111 | 0.3333 | 0.3600 | 0.3333 | 0.4286 | 0.5000 | 0.7778 | 0.8000 | 0.8182 | 0.8095 | 0.6923 | 0.7143 | 0.6444 |
| 5 | - | 0.0588 | 0.1111 | 0.2727 | 0.2889 | 0.4074 | 0.2381 | 0.3333 | 0.8129 | 0.8316 | 0.8469 | 0.8519 | 0.8359 | 0.8367 | 0.8359 |
| 6 | - | 0.0000 | 0.0725 | 0.1579 | 0.1467 | 0.1111 | 0.1688 | 0.3846 | 0.7037 | 0.7217 | 0.7470 | 0.7460 | 0.7265 | 0.6952 | 0.6718 |
| 7 | - | 0.0725 | 0.0519 | 0.0857 | 0.0857 | 0.1111 | 0.2050 | 0.2000 | 0.4530 | 0.4667 | 0.5152 | 0.5152 | 0.4530 | 0.3905 | 0.3436 |
| 8 | - | 0.0000 | 0.0078 | 0.0725 | 0.0857 | 0.0922 | 0.1293 | 0.1351 | 0.1634 | 0.1742 | 0.1688 | 0.2381 | 0.2426 | 0.2967 | 0.3173 |
| 9 | - | 0.0039 | 0.0192 | 0.1467 | 0.1607 | 0.1203 | 0.1080 | 0.1111 | 0.1380 | 0.1322 | 0.1218 | 0.1795 | 0.1962 | 0.2381 | 0.2580 |
| 10 | - | 0.0019 | 0.0275 | 0.0922 | 0.0898 | 0.0623 | 0.0741 | 0.0922 | 0.1111 | 0.1018 | 0.1218 | 0.1203 | 0.1438 | 0.1688 | 0.1675 |
| 11 | - | 0.0019 | 0.0234 | 0.0430 | 0.0385 | 0.0248 | 0.0248 | 0.0483 | 0.0636 | 0.0648 | 0.0737 | 0.0725 | 0.0894 | 0.0800 | 0.0958 |
| 12 | - | - | 0.0121 | 0.0285 | 0.0282 | 0.0121 | 0.0149 | 0.0571 | 0.0577 | 0.0562 | 0.0549 | 0.0412 | 0.0510 | 0.0439 | 0.0616 |
| 13 | - | - | 0.0074 | 0.0019 | 0.0070 | 0.0177 | 0.0304 | 0.0303 | 0.0337 | 0.0189 | 0.0252 | 0.0358 | 0.0409 | 0.0501 | 0.0385 |
| 14 | - | - | 0.0041 | 0.0024 | 0.0037 | 0.0027 | 0.0145 | 0.0073 | 0.0101 | 0.0130 | 0.0220 | 0.0234 | 0.0290 | 0.0248 | 0.0195 |
| 15 | - | - | 0.0019 | 0.0021 | 0.0036 | 0.0083 | 0.0059 | 0.0056 | 0.0101 | 0.0097 | 0.0123 | 0.0163 | 0.0150 | 0.0186 | 0.0173 |
| 16 | - | - | 0.0010 | 0.0007 | 0.0010 | 0.0030 | 0.0049 | 0.0039 | 0.0085 | 0.0072 | 0.0097 | 0.0108 | 0.0135 | 0.0141 | 0.0115 |
| 17 | - | - | - | - | - | 0.0030 | 0.0033 | 0.0024 | 0.0036 | 0.0030 | 0.0055 | 0.0091 | 0.0135 | 0.0156 | 0.0143 |
| 18 | - | - | - | - | - | - | 0.0019 | - | 0.0029 | 0.0027 | 0.0043 | 0.0040 | 0.0066 | 0.0061 | 0.0060 |
| 19 | - | - | - | - | - | - | - | - | 0.0019 | - | 0.0021 | 0.0030 | 0.0023 | 0.0031 | 0.0042 |
| 20 | - | - | - | - | - | - | - | - | - | - | - | 0.0029 | 0.0025 | 0.0037 | 0.0044 |
| 21 | - | - | - | - | - | - | - | - | - | - | - | - | 0.0026 | 0.0035 | 0.0040 |

#### Distribution with redundancy 2:

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bits \ Nodes | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| 1 | 0.0000 | 0.0000 | 0.3333 | 0.5000 | 0.6000 | 0.6667 | 0.4286 | 0.5000 | 0.5556 | 0.6000 | 0.6364 | 0.6667 | 0.6923 | 0.7143 | 0.7333 |
| 2 | 0.0000 | 0.0000 | 0.3333 | 0.3333 | 0.2000 | 0.3333 | 0.4286 | 0.5000 | 0.5556 | 0.6000 | 0.6364 | 0.6667 | 0.6923 | 0.4286 | 0.4667 |
| 3 | 0.0000 | 0.0000 | 0.1111 | 0.2000 | 0.2000 | 0.3333 | 0.4286 | 0.5000 | 0.7037 | 0.7333 | 0.7576 | 0.7778 | 0.7949 | 0.7714 | 0.7333 |
| 4 | 0.0000 | 0.0000 | 0.1111 | 0.2000 | 0.2000 | 0.3333 | 0.3469 | 0.2000 | 0.7460 | 0.7714 | 0.7762 | 0.7778 | 0.7949 | 0.7714 | 0.7630 |
| 5 | - | - | 0.0725 | 0.1579 | 0.2471 | 0.2381 | 0.2967 | 0.2727 | 0.7265 | 0.7538 | 0.7673 | 0.7778 | 0.7949 | 0.7922 | 0.7968 |
| 6 | - | - | 0.0519 | 0.1111 | 0.1742 | 0.1467 | 0.2050 | 0.2381 | 0.6908 | 0.7023 | 0.7016 | 0.7117 | 0.7265 | 0.7229 | 0.7247 |
| 7 | - | - | 0.0303 | 0.0154 | 0.0340 | 0.0303 | 0.0857 | 0.1111 | 0.4921 | 0.4880 | 0.4828 | 0.4797 | 0.5077 | 0.4622 | 0.4667 |
| 8 | - | - | 0.0078 | 0.0303 | 0.0248 | 0.0623 | 0.0857 | 0.0725 | 0.0970 | 0.1322 | 0.1049 | 0.1293 | 0.1620 | 0.1873 | 0.2242 |
| 9 | - | - | 0.0019 | 0.0266 | 0.0519 | 0.0466 | 0.0682 | 0.0791 | 0.0824 | 0.0519 | 0.0691 | 0.0519 | 0.0623 | 0.0741 | 0.0898 |
| 10 | - | - | 0.0063 | 0.0173 | 0.0154 | 0.0275 | 0.0116 | 0.0340 | 0.0558 | 0.0294 | 0.0452 | 0.0466 | 0.0567 | 0.0501 | 0.0584 |
| 11 | - | - | 0.0078 | 0.0049 | 0.0154 | 0.0177 | 0.0149 | 0.0210 | 0.0275 | 0.0177 | 0.0252 | 0.0303 | 0.0305 | 0.0344 | 0.0317 |
| 12 | - | - | - | 0.0073 | 0.0112 | 0.0192 | 0.0231 | 0.0312 | 0.0296 | 0.0177 | 0.0278 | 0.0358 | 0.0245 | 0.0312 | 0.0385 |
| 13 | - | - | - | 0.0061 | 0.0049 | 0.0096 | 0.0112 | 0.0201 | 0.0218 | 0.0088 | 0.0077 | 0.0199 | 0.0138 | 0.0304 | 0.0317 |
| 14 | - | - | - | 0.0059 | 0.0058 | 0.0058 | 0.0057 | 0.0092 | 0.0128 | 0.0082 | 0.0139 | 0.0081 | 0.0096 | 0.0199 | 0.0213 |
| 15 | - | - | - | - | 0.0014 | 0.0039 | 0.0052 | 0.0034 | 0.0051 | 0.0085 | 0.0044 | 0.0072 | 0.0107 | 0.0101 | 0.0082 |
| 16 | - | - | - | - | 0.0016 | 0.0030 | 0.0026 | 0.0036 | 0.0065 | 0.0051 | 0.0061 | 0.0084 | 0.0065 | 0.0083 | 0.0100 |
| 17 | - | - | - | - | - | - | 0.0010 | 0.0020 | 0.0028 | - | 0.0040 | 0.0049 | 0.0067 | 0.0071 | 0.0062 |
| 18 | - | - | - | - | - | - | - | - | 0.0032 | - | 0.0024 | - | 0.0034 | 0.0056 | 0.0041 |
| 19 | - | - | - | - | - | - | - | - | - | - | - | - | 0.0025 | 0.0018 | - |

#### Distribution with redundancy 2:

|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Bits \ Nodes | 16 | 20 | 32 | 48 | 64 | 100 | 128 | 160 | 200 | 256 | 350 | 500 | 800 | 1000 | 5000 |
| 8 | 0.2000 | 0.3081 | 0.2727 | 0.5152 | 0.5294 | 0.5733 | 0.6364 | 0.7091 | 0.7673 | 0.8000 | 0.8537 | 0.8862 | 0.8933 | 0.8976 | 0.9659 |
| 9 | 0.0725 | 0.2242 | 0.1795 | 0.1795 | 0.3043 | 0.3173 | 0.3846 | 0.5077 | 0.5345 | 0.6364 | 0.7340 | 0.7952 | 0.8400 | 0.8720 | 0.9317 |
| 10 | 0.0725 | 0.1322 | 0.1233 | 0.2099 | 0.1579 | 0.2415 | 0.3333 | 0.5733 | 0.4611 | 0.5789 | 0.6558 | 0.7269 | 0.8293 | 0.8425 | 0.8976 |
| 11 | 0.0340 | 0.0857 | 0.0922 | 0.1111 | 0.1233 | 0.1969 | 0.2558 | 0.5937 | 0.5643 | 0.5897 | 0.5965 | 0.6099 | 0.6587 | 0.7591 | 0.8830 |
| 12 | 0.0448 | 0.0385 | 0.0623 | 0.1065 | 0.0986 | 0.1285 | 0.3725 | 0.3831 | 0.4064 | 0.4074 | 0.4799 | 0.4880 | 0.5124 | 0.8328 | 0.8976 |
| 13 | 0.0340 | 0.0328 | 0.0554 | 0.0699 | 0.0623 | 0.0948 | 0.1049 | 0.2183 | 0.2344 | 0.3191 | 0.3498 | 0.4539 | 0.5733 | 0.6656 | 0.8870 |
| 14 | 0.0140 | 0.0189 | 0.0376 | 0.0452 | 0.0466 | 0.0717 | 0.0986 | 0.1057 | 0.1047 | 0.2242 | 0.2853 | 0.2798 | 0.4064 | 0.4959 | 0.8830 |
| 15 | 0.0094 | 0.0118 | 0.0385 | 0.0268 | 0.0331 | 0.0638 | 0.0708 | 0.0775 | 0.0898 | 0.1322 | 0.2133 | 0.2104 | 0.3550 | 0.4446 | 0.8752 |
| 16 | 0.0097 | 0.0081 | 0.0380 | 0.0303 | 0.0362 | 0.0577 | 0.0501 | 0.0627 | 0.0717 | 0.1033 | 0.1733 | 0.1678 | 0.2586 | 0.3101 | 0.8511 |
| 17 | 0.0075 | 0.0066 | 0.0346 | 0.0293 | 0.0154 | 0.0258 | 0.0466 | 0.0546 | 0.0704 | 0.1041 | 0.1469 | 0.1983 | 0.2702 | 0.2972 | 0.7740 |
| 18 | 0.0053 | 0.0057 | 0.0098 | 0.0098 | 0.0122 | 0.0149 | 0.0238 | 0.0300 | 0.0394 | 0.0353 | 0.0434 | 0.0553 | 0.0611 | 0.1782 | 0.6334 |
| 19 | - | 0.0022 | 0.0050 | 0.0162 | 0.0098 | 0.0133 | 0.0149 | 0.0220 | 0.0242 | 0.0252 | 0.0333 | 0.0398 | 0.0495 | 0.0999 | 0.5145 |
| 20 | - | - | 0.0030 | 0.0107 | 0.0088 | 0.0098 | 0.0144 | 0.0140 | 0.0148 | 0.0203 | 0.0195 | 0.0255 | 0.0348 | 0.1133 | 0.4481 |
| 21 | - | - | 0.0043 | 0.0063 | 0.0051 | 0.0074 | 0.0079 | 0.0085 | 0.0086 | 0.0113 | 0.0147 | 0.0170 | 0.0237 | 0.1068 | 0.4422 |
| 22 | - | - | - | 0.0026 | 0.0035 | 0.0037 | 0.0082 | 0.0061 | 0.0077 | 0.0087 | 0.0101 | 0.0134 | 0.0193 | 0.1140 | 0.4635 |
| 23 | - | - | - | 0.0019 | - | 0.0026 | 0.0080 | 0.0055 | 0.0056 | 0.0057 | 0.0063 | 0.0096 | 0.0155 | 0.1294 | 0.4982 |
| 24 | - | - | - | 0.0013 | - | - | 0.0074 | 0.0060 | 0.0058 | 0.0053 | 0.0049 | 0.0068 | 0.0112 | 0.0471 | 0.3219 |
| 25 | - | - | - | - | - | - | - | - | - | 0.0043 | 0.0043 | 0.0058 | 0.0067 | 0.0512 | 0.2543 |
| 26 | - | - | - | - | - | - | - | - | - | - | 0.0040 | 0.0042 | 0.0043 | 0.0051 | 0.0210 |
| 27 | - | - | - | - | - | - | - | - | - | - | - | - | 0.0028 | 0.0157 | 0.0814 |

### Default number of distribution bits used

Note that changing the amount of distribution bits used will change what buckets exist,
which will change the distribution considerably.
We thus do not want to alter the distribution bit count too often.

Ideally, the users would be allowed to configure minimal and maximal acceptable waste,
and the current amount of distribution bits could then just be calculated on the fly.
But as computing the waste values above are computational heavy,
especially with many nodes and many distribution bits,
currently only a couple of profiles are available for you to configure.
**Vespa Cloud note:** Vespa Cloud locks distribution bit count to 16.
This is because Vespa Cloud offers auto-scaling of nodes, and such a scaling decision
should not implicitly lead to a full redistribution of data by crossing a distribution bit
node count boundary. 16 bits strikes a good balance of low skew and high performance for
most production deployments.

#### Loose mode (default)

The loose mode allows for more waste, allowing the amount of nodes to
change considerably without altering the distribution bit counts.

|  |  |  |  |
| --- | --- | --- | --- |
| Node count | 1-4 | 5-199 | 200-> |
| Distribution bit count | 8 | 16 | 24 |
| Max calculated waste *) | 3.03 % | 7.17 % | ? |
| Minimum buckets/node **) | 256 - 64 | 13108 - 329 | 83886 - |

#### Strict mode (not default)

The strict mode attempts to keep the waste below 1.0 %.
When it needs to increase the bit count it increases the bit count significantly
to allow considerable more growth before having to adjust the count again.

|  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Node count | 1-4 | 5-14 | 15-199 | 200-799 | 800-1499 | 1500-4999 | 5000-> |
| Distribution bit count | 8 | 16 | 21 | 25 | 28 | 30 | 32 |
| Max calculated waste *) | 3 % | 0.83 % | 0.86 % | 0.67 % | ? | ? | ? |
| Minimum buckets/node **) | 256 - 64 | 13107 - 4681 | 139810 - 10538 | 167772 - 41995 | 335544 - 179076 | 715827 - 214791 | 858993 - |
*) Max calculated waste, given redundancy 2 and the max node count in the given range,
as shown in the table above.
(Note that this assumes equal sized buckets, and that every possible bucket exist.
In a real system there will be random variation).
**) Given a node count and distribution bits, there is a minimum number of buckets enforced to exist.
However, splitting due to bucket size may increase this count beyond this number.
This value shows the maximum value of the minimum.
(That is the number of buckets per node enforced for the lowest node count in the range)
Ideally one wants to have few buckets enforced by distribution
and rather let bucket size split buckets, as that leaves more freedom to users.

## Q/A
**Q: I have a cluster with multiple groups, with the same number of nodes (more than one) in
each group. Why does the first node in the first group store a slightly different number of documents
than the first node in the second group (and so on)?**

A: This is both expected and intentional—to see why we must look at how the ideal state algorithm works.

As previously outlined, the ideal state algorithm requires 3 distinct inputs:

1. The ID of the bucket to be replicated across content nodes.
2. The set of all nodes (i.e. unique distribution keys) in the cluster *across* all groups,
   and their current availability state (Down, Up, Maintenance etc.).
3. The cluster topology and replication configuration. The topology includes knowledge of all groups.

From this the algorithm returns a deterministic, ordered sequence of nodes (i.e. distribution keys)
across all configured groups. The ordering of nodes is given by their individual pseudo-random node
*score*, where higher scoring nodes are considered more *ideal* for storing replicas
for a given bucket. The set of nodes in this sequence respects the constraints given by the configured
group topology and replication level.

When computing node scores within a group, the *absolute* distribution keys are used rather
than a node's *relative* ordering within the group. This means the individual node scores—and
consequently the distribution of bucket replicas—within one group is different (with a very high
probability) from all other groups.

What the ideal state algorithm ensures is that there exists a deterministic, configurable number of replicas
per bucket within each group and that they are evenly distributed across each group's nodes—the exact mapping
can be considered an unspecified "implementation detail".

The rationale for using absolute distribution keys rather than relative ordering is closely related to
the earlier discussion about why [modulo distribution](#a-simple-example-modulo) is a poor
choice. Let \(N_g \gt 1\) be the number of nodes in a given group:
* A relative ordering means that removing—or just reordering—a single node from the configuration can
  potentially lead to a full redistribution of all data within that group, not just \( \frac{1}{N_g} \)
  of the data. Imagine for instance moving a node from being first in the group to being the last.
* If we require nodes with the same relative index in each group to store the same data set (i.e.
  a row-column strategy), this immediately suffers in failure scenarios even when just a single node
  becomes unavailable.
  Data coverage in the group remains reduced until the node is replaced, as no other nodes can take over
  responsibility for the data. This is because removing the node leads to the problem in the previous point,
  where a disproportionally large amount of data must be moved due to the relative ordering changing.
  With the ideal state algorithm, the remaining nodes in the group will transparently assume ownership
  of the data, with each node receiving an expected \( \frac{1}{N_g - 1} \) of the unavailable node's buckets.
