---
# Copyright Vespa.ai. All rights reserved.
title: "Routing"
category: oss
redirect_from:
- /en/routing.html
- /en/reference/services-routing.html
- /en/reference/routingpolicies.html
---

*Routing* is used to configure the paths that documents and updates written
to Vespa take through the system. Vespa will automatically set up a routing
configuration which is appropriate for most cases, so no explicit routing
configuration is necessary. However, explicit routing can be used in advanced use
cases such as sending different document streams to different document processing
clusters, or through multiple consecutive clusters etc.

There are other, more in-depth, articles on routing:
* Use [vespa-route](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-route)
  to inspect routes and services of a Vespa application, like in the
  [example](#example-reconfigure-the-default-route)
* [Routing policies reference](#routing-policies-reference).
  See the [routing policies](#routing-policies) note
  for complex routes and default routing

In Vespa, there is a transport layer and a programming interface that
are available to clients that wish to communicate with a Vespa application.
The transport layer is *Message Bus*.
[Document API](/en/document-api-guide.html) is
implemented on top of Message Bus.
Configuring the interface therefore exposes some features available in Message Bus.
Refer to the [Vespa APIs and interfaces](/en/api.html)
for clients using the *Document API*.
The atoms in Vespa routing are *routes* and *hops*.

[document-processing](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing) is an example of custom document processing, and useful for testing routing.

## A route is a sequence of hops

The sequence of hosts, routers, bridges, gateways, and other devices
that network traffic takes, or could take, from its source to its
destination is what is classically termed a *route*.
As a verb, *to route* means to determine the link down which to send a packet,
that will minimize its total journey time according to some routing algorithm.

In Vespa, a route is simply a sequence of named hops.
Instead of leaving selection logic to a route,
the responsibility of resolving recipients is given to
the [hops](#a-hop-is-a-point-to-point-transmission)' [selectors](#selection-logic).
A hop can do more or less whatever it wants
to change a message's journey through your application;
it can slightly alter itself by choosing among some predefined recipients,
it can change itself completely by either rewriting or looking up another hop,
or it can even modify the entire route from that branch onwards.
In effect, a route can end up branching at several points along its path,
resulting in complex routes.
As the figure suggests, Message Bus supports
both [unicasting](https://en.wikipedia.org/wiki/Unicast)
and [multicasting](https://en.wikipedia.org/wiki/Multicast) -
Message Bus allows for arbitrarily complex routes.
Each node in the above graph represents a Vespa service:

![Illustration of routes with hops](/assets/img/routing.svg)

## A hop is a point-to-point transmission

In telecommunication, a *hop* is one step, from one router to the next,
on the path of a packet on an Internet Protocol network.
It is a direct host-to-host connection forming part of the route between
two hosts in a routed network such as the Internet.
In more general terms, a hop is a point-to-point transmission in a series
required to get a message from point A to point B.

With Message Bus the concept of hops was introduced as the smallest
steps of the transmission of a message.
A hop consists of a *name* that is used by the messaging clients to select it,
a list of *recipient* services that it may transmit to,
and a *selector* that is used to select among those recipients.
Unlike traditional hops, in Vespa a hop is a transmission from one sender to many recipients.

Well, the above is only partially true;
it is the easiest way to understand the hop concept.
In fact, a hop's recipient list is nothing more than a configured list of strings
that is made available to all [routing policies](#routing-policies)
that are named in the selector string.
See [selection logic](#selection-logic) below for details.

A hop's recipient is the service name of a Message Bus client that has
been registered in Vespa's service location broker (vespa-slobrok).
These names are well-defined once their derivation logic is understood;
they are "/"-separated sets of address-components whose values
are given by a service's role in the application.
An example of a recipient is:

```
search/cluster.foo/*/feed-destination
```

The marked components of the above recipient, `/search/cluster.foo/*`,
resolves to a host's symbolic name.
This is the name with which a Message Bus instance was configured.
The unmarked component, `feed-destination`,
is the local name of the running service that the hop transmits to,
i.e. the name of the *session* created on the running Message Bus instance.

The Active Configuration page in Vespa's administration interface
gives an insight into what symbolic names exist for any given
application by looking at its current configuration subscriptions.
All available Message Bus services use their `ConfigId` as their host's symbolic name.
See [vespa-route](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-route) for how to inspect this,
or use the [config API](/en/reference/config-rest-api-v2.html).

A hop can be prefixed using the special character "?" to force it to behave as if its
[ignore-result](#hop) attribute was configured to "true".

### Asterisk

A service identifier may include the special character "*" as an address component.
A recipient that contains this character
is a request for the network to choose *any one* service that matches it.

## Routing policies

A routing policy is a protocol-specific algorithm that chooses among a
list of candidate recipients for a single address component -
see [hop description](#a-hop-is-a-point-to-point-transmission) above.
These policies are designed and implemented as key parts of a Message Bus protocol.
E.g. for the "Document" protocol these are what make up the routing behavior for document transmission.
Without policies, a hop would only be able to match verbatim to a recipient,
and thus the only advanced selection logic would be that of the [asterisk](#asterisk).

In addition to implementing a selection algorithm,
a routing policy must also implement a merging algorithm that combines the replies
returned from each selected recipient into a single sensible reply.
This is needed because a client does not necessarily know
whether a message has been sent to one or multiple recipients,
and **Message Bus guarantees a single reply for every message**.

More formally, a routing policy is an arbitrarily large (or small),
named, stand-alone piece of code registered with a Message Bus protocol.
As discussed [above](#selection-logic),
an instance of a policy is run both when resolving a route to recipients,
and when merging replies.
The policy is passed a `RoutingContext` object
that pretty much allows it to do whatever it pleases to the route and replies.
The same policy object and the same context object is used for both selection and merging.

Refer to the [routing policy reference](#routing-policies-reference).

## Selection logic

When Message Bus is about to route a message, at the last possible time,
it inspects the **first** hop of the message's route to resolve a set of recipients.
First, all of its [policies are resolved](#1-resolve-policy-directives).
Second, the output service name is matched to the routing table to see if it maps to another hop or route.
Finally, the message is [sent](#3-send-to-services) to all chosen recipient services.
Because each policy can select multiple recipients,
this can give rise to an arbitrarily complex routing tree.
There are, of course, safeguards within Message Bus to prevent infinite recursions
due to circular dependencies or misconfiguration.

{% include note.html content="It **is** possible to develop a different protocol with other
policies to run in the application,
but since all of Vespa's component only support the \"Document\" protocol,
it makes little sense to do so."%}

### 1. Resolve Policy Directives

The logic run at this step is actually simple;
as long as the hop string contains a policy directive,
i.e. some arbitrary string enclosed in square brackets,
Message Bus will create and run an instance of that policy for the protocol of the message being routed.

```
Name:        storage/cluster.backup
Selector:    storage/cluster.backup/distributor/[Distributor]/default
Recipients:  -
```

The above hop is probably the simplest hop you will encounter in Vespa;
it has a single policy directive contained in a string
that closely resembles service names discussed above, and it has no recipients.
When resolving this hop,
Message Bus creates an instance of the "DocumentRouteSelector" policy
and invokes its `select()` method.
The "Distributor" policy will replace its own directive
with a proper distributor identifier,
yielding a hop string that is now an unambiguous service identifier.

```
Name:        indexing
Selector:    [DocumentRouteSelector]
Recipients:  search/cluster.music
             search/cluster.books
```

This hop has a selector which is nothing more than a single policy directive,
"[DocumentRouteSelector]", and it has two configured recipients,
"search/cluster.music" and "search/cluster.books".
This policy expands the hop to zero, one or two **new** routes
by replacing its own directive with the content of the recipient routes.
Each of these routes may have one or more hops themselves.
In turn, these will be processed independently.
When replies are available from all chosen recipients,
the policy's `merge()` method is invoked,
and the resulting reply is passed upwards.

```
Name:        default
Selector:    [AND:indexing storage/cluster.backup]
Recipients:  -
```

This hop has a selector but no recipients.
The reason for this is best explained in
the [routing policies reference](#routing-policies-reference),
but it serves as an example of a hop that has no configured recipients.
Notice how the policy directive contains a colon (":")
which denotes that the remainder of the directive is a parameter to the policy constructor.
This policy replaces the whole route of the message
with the set of routes named in the parameter string.

What routing policies are available depends on what protocol is currently running.
As of this version the only supported protocol is "Document".
This offers a set of routing policies discussed
[below](#routing-policies-reference).

### 2. Resolve Hop- and Route names

As soon as all policy directives have been resolved,
Message Bus makes sure that the resulting string is,
in fact, a service name and not the name of another hop or route (in that order)
configured for the running protocol. The outcome is either:

1. The string is recognized as a hop name - The current hop
   is replaced by the named one, and processing returns
   to [step 1](#1-resolve-policy-directives).
2. The string is recognized as a route name - The current
   route, including all the hops following this, is replaced by the named one.
   Processing returns to [step 1](#1-resolve-policy-directives).
3. The string is accepted as a service name - This terminates
   the current branch of the routing tree. If all branches are terminated,
   processing proceeds to [step 3](#3-send-to-services).

Because hop names are checked before route names,
Message Bus also supports a "route:" prefix that forces the remainder of the string
to resolve to a configured route or fail.

### 3. Send to Services

When the route resolver reaches this point,
the first hop of the message being sent has been resolved to an arbitrarily complex routing tree.
Each leaf of this tree represents a service that is to receive the message,
unless some policy has already generated a reply for it.
No matter how many recipients are chosen, the message is serialized only once,
and the network transmission is able to share the same chunk of memory between all recipients.

As replies to the message arrive at the sender they are handed over to
the corresponding leaf nodes of the routing tree,
but merging will not commence until all leaf nodes are ready.

Route resolving happens just before network transmission, after all resending logic.
This means that if the route configuration changes while there are messages scheduled for resending,
these will adhere to the new routes.

If the resolution of a recipient passed through a hop that was configured
to [ignore results](#hop),
the network layer will reply immediately with a synthetic "OK".

## Example: Reconfigure the default route

Assume that the application requires both search and storage capabilities,
but that the default feed should only pass through to search.
An imaginary scenario for this would be a system where there
is a continuous feed being passed into Vespa with no filtering on spam.
You would like a minimal storage-only cluster that stores a URL blocklist
that can be used by a custom document processor to block incoming documents from offending sites.

Apart from the blocklist and the document processor, add the following:

```
<routing version="1.0">
    <routingtable protocol="document">
        <route name="default" hops="docproc/cluster.blocklist/*/chain.blocklist indexing" />
    </routingtable>
</routing>
```

This overrides the default route to pass through any available
blocklisting document processor before being indexed.
If the document processor decides to block a message,
it must respond with an appropriate *ok* reply,
or your client software needs to accept whatever error reply you decide to return when blocking.

When feeding blocklist information to storage,
your application need only use the already available `storage` hop.

See [#13193](https://github.com/vespa-engine/vespa/issues/13193)
for a discussion on using *default* as a name.

### The Document API

With the current implementation of Document API running on Message bus,
the configuration of the API implies configuration of the latter.
Most clients will only ever route through this API.
To use the Document API, you need to instantiate a class
that implements the `DocumentAccess` interface.
At the time of writing only `MessageBusDocumentAccess` exists,
and it requires a parameter set for creation.
These parameters are contained in an instance of `MessageBusDocumentAccessParam`
that looks somewhat like the following:

```
class MessageBusDocumentAccessParams {
    String documentManagerConfigId; // The id to resolve to document manager config.
    String oosServerPattern;        // The service pattern to resolve to fleet controller
                                    // services.
    String appConfigId;             // The id to resolve to application config.
    String slobrokConfigId;         // The id to resolve to slobrok config.
    String routingConfigId;         // The id to resolve to messagebus routing config.

    String routeName;               // The name of the route to send to.
    int    traceLevel;              // The trace level to use when sending.

    class SourceSessionParams {
        int    maxPending;          // Maximum number of pending messages.
        int    maxPendingSize;      // Maximum size of pending messages.
        double timeout;             // Default timeout in seconds for messages
                                    // that have no timeout set.
        double requestTimeoutA;     // Default request timeout in seconds, using
        double requestTimeoutB;     // the equation 'requestTimeout = a * retry + b'.
        double retryDelay;          // Number of seconds to wait before resending.
    };
}
```

The most obvious configuration parameter is `routeName`,
which informs the `MessageBusDocumentAccess` object the
name of the route to use when sending documents and updates.
The second parameter is `traceLevel`,
which allows a client to see exactly how the data was transmitted.

{% include note.html content="Tracing can be enabled on a level from 1-9,
where a higher number means more tracing.
Because the concept of tracing is not exposed by the Document API itself,
its data will simply be printed to standard output when a reply arrives for the sender.
This should therefore not be used in production,
but can be helpful when debugging."%}

Refer to the [Document API JavaDoc](https://javadoc.io/doc/com.yahoo.vespa/documentapi).

## Routing services

This is the reference documentation for all elements in
the *routing* section of [services.xml](/en/reference/services.html).

```
routing [version]
    routingtable [protocol, verify]
        route [name, hops]
        hop [name, selector, ignore-result]
            recipient [session]
    services [protocol]
        service [name]
```

## routing

Contained in [services](/en/reference/services.html#services).
The container element for all configuration related to routing.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| version | required | number |  | Must be set to "1.0" in this Vespa-version |

Optional subelements:
* [routingtable](#routingtable)
* [services](#services)

Example:

```
<routing version="1.0">
    <routingtable protocol="document">
        <route name="route1" hops="hop1 hop2" />
        <route name="route2" hops="hop3 hop4 hop5" />
        <hop name="hop1" selector="docproc/cluster.foo/docproc/*/feed-processor">
            <recipient session="docproc/cluster.foo/docproc/*/feed-processor" />
        </hop>
        <hop name="hop2" selector="search/cluster.bar/[SearchGroup]/[SearchRow]/[SearchColumn]/feed-destination">
            <recipient session="search/cluster.bar/g0/c0/r0/feed-destination" />
            <recipient session="search/cluster.bar/g0/c1/r0/feed-destination" />
            <recipient session="search/cluster.bar/g0/c0/r1/feed-destination" />
            <recipient session="search/cluster.bar/g0/c1/r1/feed-destination" />
            <recipient session="search/cluster.bar/g1/c0/r0/feed-destination" />
            <recipient session="search/cluster.bar/g1/c1/r0/feed-destination" />
            <recipient session="search/cluster.bar/g1/c0/r1/feed-destination" />
            <recipient session="search/cluster.bar/g1/c1/r1/feed-destination" />
        </hop>
    </routingtable>
    <services protocol="document">
        <service name="foo/bar" />
    </services>
</routing>
```

## routingtable

Contained in [routing](#routing).
Specifies a routing table for a specific protocol.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| protocol | required |  |  | Configure which protocol to use. Only the protocol *document* is defined, so if you define a routing table for an unsupported protocol, the application will just log an INFO entry that contains the name of that protocol. |
| verify | optional | boolean |  | ToDo: document this |

Optional subelements:
* [route](#route)
* [hop](#hop)

Example:

```
<routing version="1.0">
    <routingtable protocol="document">
        <route name="route1" hops="hop1 hop2" />
        <hop name="hop1" selector="docproc/cluster.foo/docproc/*/feed-processor">
            <recipient session="docproc/cluster.foo/docproc/*/feed-processor" />
        </hop>
    </routingtable>
</routing>
```

## route

Contained in [routingtable](#routingtable).
Specifies a route for a message to its destination through a set of intermediate hops.
If at least one hop in a route does not exist,
the application will fail to start and issue an error that contains the name of that hop.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| name | required |  |  | Route name. |
| hops | required |  |  | A whitespace-separated list of hop names, where each name must be a valid hop. |

Subelements: none

Example:

```
<routing version="1.0">
    <routingtable protocol="document">
        <route name="route1" hops="hop1 hop2" />
        <route name="route2" hops="hop3 hop4 hop5" />
    </routingtable>
</routing>
```

## hop

Contained in [routingtable](#routingtable).
Specifies a single hop that can be used to construct one or more routes.
A hop must have a name that is unique within the routing table to which it belongs.
A hop contains a selector string and a list of recipient sessions.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| name | required |  |  | Hop name. |
| selector | required |  |  | Selector string. |
| ignore-result | optional |  |  | If set to *true*, specifies that the result of routing through that hop should be ignored. |

Optional subelements:
* [recipient](#recipient)

Example:

```
<routing version="1.0">
    <routingtable protocol="document">
        <hop name="hop1" selector="docproc/cluster.foo/docproc/*/feed-processor">
            <recipient session="docproc/cluster.foo/docproc/*/feed-processor" />
        </hop>
    </routingtable>
</routing>
```

## recipient

Contained in [hop](#hop).
Specifies a recipient session of a hop.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| session | required |  |  | This attribute must correspond to a running instance of a service that can be routed to. All session identifiers consist of a location part and a name. A search node is always given a session name on the form *search/cluster.name/g#/r#/c#/feed-destination*, whereas a document processor service is always named *docproc/cluster.name/docproc/#/feed-processor*. |

Subelements: none

Example:

```
<routing version="1.0">
    <routingtable protocol="document">
        <hop name="search/cluster.music" selector="search/cluster.music/[SearchGroup]/[SearchRow]/[SearchColumn]/feed-destination">
            <recipient session="search/cluster.music/g0/c0/r0/feed-destination" />
            <recipient session="search/cluster.music/g0/c0/r1/feed-destination" />
            <recipient session="search/cluster.music/g1/c0/r0/feed-destination" />
            <recipient session="search/cluster.music/g1/c0/r1/feed-destination" />
        </hop>
    </routingtable>
</routing>
```

## services

Contained in [routing](#routing).
Specifies a set of services available for a specific protocol.
At the moment the only supported protocol is *document*.
The services specified are used by the route verification step
to allow hops and routes to reference services known to exist,
but that can not be derived from *services.xml*.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| protocol | required |  |  | Configure which protocol to use. Only the protocol *document* is defined. |

Optional subelements:
* [service](#service)

Example:

```
<routing version="1.0">
    <services protocol="document">
        <service name="foo/bar" />
    </services>
</routing>
```

## service

Contained in [services](#services).
Specifies a single known service that can not be derived from the *services.xml*.

| Attribute | Required | Value | Default | Description |
| --- | --- | --- | --- | --- |
| name | required |  |  | The name of the service. |

Subelements: none

Example:

```
<routing version="1.0">
    <services protocol="document">
        <service name="foo/bar" />
    </services>
</routing>
```

## Routingpolicies reference

This article contains detailed descriptions of the behaviour of all routing policies available in Vespa.

The *Document protocol* is currently the only Message Bus protocol supported by Vespa.
Furthermore, all routing policies that are part of this protocol
share a common code path for [merging replies](#merge).
The policies offered by the protocol are:
* [AND](#and) - Selects all configured recipient hops.
* [DocumentRouteSelector](#documentrouteselector) - Uses a [document selection string](/en/reference/document-select-language.html) to select compatible routes
* [Content](#content) - Selects a content cluster distributor based on system state
* [MessageType](#messagetype) - Selects a next hop based on message type
* [Extern](#extern) - Selects a recipient by querying a remote Vespa application
* [LocalService](#localservice) - Selects a recipient based on ip address
* [RoundRobin](#roundrobin) - Selects one from the configured recipients in round-robin order
* [SubsetService](#subsetservice) - Selects only among a subset of all matching services
* [LoadBalancer](#loadbalancer) - A round-robin policy that chooses between the recipients
  by generating a weight according to their performance

### Common Document `merge()` logic

The shared merge logic of most Document routing policies is an attempt to
do the "right" thing when merging multiple replies into one.
It works by first stepping through all replies, storing their content as either:

1. OK replies,
2. IGNORE replies, or
3. ERROR replies

If at least one ERROR reply is found, return a new reply that contains all the errors of the others.
If there is at least one OK reply, return the first OK reply,
but transfer all feed information from the others to this
(this is specific data for start- and end-of-feed messages).
Otherwise, return a new reply that contains all the IGNORE errors. Pseudocode:

```
for each reply, do
    if reply has no errors, do
        store reply in OK list
    else, do
        if reply has only IGNORE errors
            copy all errors from reply to IGNORE list
        else, do
            copy all errors from reply to ERROR list

if ERROR list is not empty, do
    return new reply with all errors
else, do
    if OK list is not empty, do
        return first reply with all feed answers
    else, do
        return new reply with all IGNORE errors
```

## Routing policies reference

| Policy | Description |
| --- | --- |
| AND | This is a mostly a convenience policy that allows the user to fork a message's route to all configured recipients. It is not message-type aware, and will simply always select all recipients. Replies are merged according to the [shared logic](#merge).  The optional string parameter is parsed as a space-separated list of hops. Configured recipients have precedence over parameter-given recipients, although this is likely to be changed in the future. |
| DocumentRouteSelector | This policy is responsible for selecting among the policy's recipients according to the subscription rules defined by a content cluster's *documents* element in [services.xml](/en/reference/services.html). If the "selection" attribute is set in the "documents" element, its value is processed as a [document select](/en/reference/document-select-language.html) string, and run on documents and document updates to determine routes. If the "feedname" attribute is set, all feed commands are filtered through it.  The recipient list of this policy is required to map directly to route names. E.g. if a recipient is "search/cluster.music", and a message is appropriate according to the selection criteria, the message is routed to the "search/cluster.music" route. If the route does not exist, this policy will reply with an error. In short, this policy selects one or more recipient routes based on document content and configured criteria.  If more than one route is chosen, its replies are merged according to the [shared logic](#merge).  This policy does not support any parameters.  The configuration for this is "documentrouteselectorpolicy" available from config id "routing/documentapi". {% include important.html content="Because GET messages do not contain any document on which to run the selection criteria, this policy returns an IGNORED reply that the merging logic processes. You can see this by attempting to retrieve a document from an application that does not have a content cluster."%} |
| Content This policy allows you to send a message to a content cluster. The policy uses a system state retrieved from the cluster in question in conjunction with slobrok information to pick the correct distributor for your message.  In short; use this policy when communicating with document storage.  This policy supports multiple parameters, up to one each of:   | cluster | The name of the cluster you want to reach. Example: cluster=mycluster | | config | A comma-separated list of config servers or proxies you want to use to fetch configuration for the policy. This can be used to communicate with other clusters than the one you're currently in. Example: config=tcp/myadmin1:19070,tcp/myadmin2:19070 |  Separate each parameter with a semicolon. | |
| MessageType | This policy will select the next hop based on the type of the message. You configure where all messages should go (defaultroute). Then you configure what messages types should be overridden and sent to alternative routes. It is currently only used internally by vespa when using the [content](/en/reference/services-content.html#content) element. |
| Extern | This policy implements the necessary logic to communicate with an external Vespa application and resolve a single service pattern using that other application's slobrok servers. Keep in mind that there might be some delay from the moment this policy is initially created and when it receives the response to its service query, so using this policy might cause a message to be resent a few times until it is resolved. If you disable retries, this policy might cause all messages to fail for the first seconds.  This policy uses its parameter for both the address of the extern slobrok server to connect to, and also the pattern to use for querying. The parameter is required to be on the form `<spec>;<service>`, where `spec` is a comma-separated list of slobrok connection specs on the form "tcp/hostname:port", and `service` is a service running on the remote Vespa application. {% include important.html content="The remote application needs to have a version of both message bus and the document api that is binary compatible with the application sending from. This can be a problem even between patch releases, so keep the application versions in sync when using this policy."%} |
| LocalService | This policy is used to select among all matching services, but preferring those running on the same host as the current one. The pattern used when querying for available services is the current one, but replacing the policy directive with an asterisk. E.g. the hop "docproc/cluster.default/[LocalService]/chain.default" would prefer local services among all those that match the pattern "docproc/cluster.default/*/chain.default". If there are multiple matching services that run locally, this policy will do simple round-robin load balancing between them. If no matching services run locally, this policy simply returns the asterisk as a match to allow the underlying network logic to do load balancing among all available.  This policy accepts an optional parameter which overrides the local hostname. Use this if you wish the hop to prefer some specific host. {% include important.html content="There is no additional logic to replace other policy directives with an asterisk, meaning that if other policies directives are present in the hop string after \"[LocalService]\", no services can possibly be matched."%} |
| RoundRobin | This policy is used to select among a configured set of recipients. For each configured recipient, this policy determines what online services are matched, and then selects one among all of those in round-robin order. If none of the configured recipients match any available service, this policy returns an error that indicates to the sender that it should retry later.  Because this policy only selects a single recipient, it contains no merging logic. |
| SubsetService | This policy is used to select among a subset of all matching services, and is used to minimize number of connections in the system. The pattern used when querying for available services is the current one, but replacing the policy directive with an asterisk. E.g. the hop "docproc/cluster.default/[SubsetService:3]/chain.default" would select among a subset of all those that match the pattern "docproc/cluster.default/*/chain.default". Given that the pattern returns a set of matches, this policy stores a subset of these based on the hash-value of the running message bus' connection string (this is unique for each instance). If there are no matching services, this policy returns the asterisk as a match to allow the underlying network logic to fail gracefully.  This policy parses its optional parameter as the size of the subset. If none is given, the subset defaults to size 5. {% include important.html content="There is no additional logic to replace other policy directives with an asterisk, meaning that if other policies directives are present in the hop string after \"[SubsetService]\", no services can possibly be matched."%} |
| LoadBalancer | This policy is used to send to a stateless cluster such as docproc, where any node can be chosen to process any message. Messages are sent between the nodes in a round-robin fashion, but each node is assigned a weight based on its performance. The weights are calculated by measuring the number of times the node had a full input-queue and returned a busy response. Use this policy to send to docproc clusters that have nodes with different performance characteristics.  This policy supports multiple parameters, up to one each of:   | cluster | The name of the cluster you want to reach. Example: cluster=docproc/cluster.default (mandatory) | | session | The destination session you want to reach. In the case of docproc, the name of the docproc chain. Example: session=chain.mychain (mandatory) | | config | A comma-separated list of config servers or proxies you want to use to fetch configuration for the policy. This can be used to communicate with other clusters than the one you're currently in. Example: config=tcp/myadmin1:19070,tcp/myadmin2:19070 |  Separate each parameter with a semicolon. By default, this policy will use the current Vespa cluster for configuration. |

## Routing for indexing

A normal Vespa configuration has container and content cluster(s),
with one or more document types defined in *schemas*.
Routing document writes means routing documents to the *indexing* container cluster,
then the right *content* cluster.

The indexing cluster is a container cluster -
see [multiple container clusters](#multiple-container-clusters) for variants.
Add the [document-api](/en/reference/services-container.html#document-api)
feed endpoint to this cluster.
The mapping from document type to content cluster is in
[document](/en/reference/services-content.html#document) in the content cluster.
From [album-recommendation](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation/app/services.xml):

```
<services version="1.0">

    <container id="container" version="1.0">
        <document-api />
        <search />
        <nodes>
            <node hostalias="node1" />
        </nodes>
    </container>

    <content id="music" version="1.0">
        <redundancy>1</redundancy>
        <documents>
            <document type="music" mode="index" />
        </documents>
        <nodes>
            <node hostalias="node1" distribution-key="0" />
        </nodes>
    </content>

</services>
```

Given this configuration, Vespa knows which is the container cluster used for indexing,
and which content cluster that stores the *music* document type.
Use [vespa-route](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-route)
to display routing generated from this configuration:

```
$ vespa-route
There are 6 route(s):
    1. default
    2. default-get
    3. music
    4. music-direct
    5. music-index
    6. storage/cluster.music

There are 2 hop(s):
    1. container/chain.indexing
    2. indexing
```

Note the *default* route. This route is auto-generated by Vespa,
and is used when no other route is used when using [/document/v1](/en/reference/document-v1-api-reference.html).
*default* points to *indexing*:

```
$ vespa-route --route default
The route 'default' has 1 hop(s):
    1. indexing
```
```
$ vespa-route --hop indexing
The hop 'indexing' has selector:
       [DocumentRouteSelector]
And 1 recipient(s):
    1. music
```
```
$ vespa-route --route music
The route 'music' has 1 hop(s):
    1. [MessageType:music]
```

In short, the *default* route handles documents of type *music*.
Vespa will route to the container cluster with *document-api* -
note the *chain.indexing* above.
This is a set of built-in *document processors* that does the indexing (below).

Refer to the [trace appendix](#appendix-trace) for routing details.

## chain.indexing

This indexing chain is set up on the container once a content cluster has `mode="index"`.

The
[IndexingProcessor](https://github.com/vespa-engine/vespa/blob/master/docprocs/src/main/java/com/yahoo/docprocs/indexing/IndexingProcessor.java)
annotates the document based on the [indexing script](/en/reference/indexing-language-reference.html)
generated from the schema. Example:

```
$ vespa-get-config -n vespa.configdefinition.ilscripts \
  -i container/docprocchains/chain/indexing/component/com.yahoo.docprocs.indexing.IndexingProcessor

maxtermoccurrences 100
fieldmatchmaxlength 1000000
ilscript[0].doctype "music"
ilscript[0].docfield[0] "artist"
ilscript[0].docfield[1] "artistId"
ilscript[0].docfield[2] "title"
ilscript[0].docfield[3] "album"
ilscript[0].docfield[4] "duration"
ilscript[0].docfield[5] "year"
ilscript[0].docfield[6] "popularity"
ilscript[0].content[0] "clear_state | guard { input artist | tokenize normalize stem:"BEST" | summary artist | index artist; }"
ilscript[0].content[1] "clear_state | guard { input artistId | summary artistId | attribute artistId; }"
ilscript[0].content[2] "clear_state | guard { input title | tokenize normalize stem:"BEST" | summary title | index title; }"
ilscript[0].content[3] "clear_state | guard { input album | tokenize normalize stem:"BEST" | index album; }"
ilscript[0].content[4] "clear_state | guard { input duration | summary duration; }"
ilscript[0].content[5] "clear_state | guard { input year | summary year | attribute year; }"
ilscript[0].content[6] "clear_state | guard { input popularity | summary popularity | attribute popularity; }"
```

Refer to [linguistics](/en/linguistics.html) for more details.

By default, the indexing chain is set up on the *first* container cluster in *services.xml*.
When having multiple container clusters, it is recommended to configure this explicitly, see
[multiple container clusters](#multiple-container-clusters).

## Document selection

The [document](/en/reference/services-content.html#document)
can have a [selection](/en/reference/document-select-language.html) string,
normally used to expire documents.
This is also evaluated during feeding, so documents that would immediately expire are dropped.
This is not an error, the document API will report 200 - but can be confusing.

The evaluation is done in the
[DocumentRouteSelector](https://github.com/vespa-engine/vespa/blob/master/documentapi/src/main/java/com/yahoo/documentapi/messagebus/protocol/DocumentRouteSelectorPolicy.java) at the feeding endpoint - *before* any processing/indexing.
I.e. the document is evaluated using the selection string (drop it or not),
then where to route it, based on document type.

Example: the selection is configured to not match the document being fed:

```
<content id="music" version="1.0">
    <redundancy>1</redundancy>
    <documents>
        <document type="music" mode="index" selection='music.album == "thisstringwillnotmatch"'/>
```
```
$ vespa-feeder --trace 6 doc.json

<trace>
    [1564576570.693] Source session accepted a 4096 byte message. 1 message(s) now pending.
    [1564576570.713] Sequencer sending message with sequence id '-1163801147'.
    [1564576570.721] Recognized 'default' as route 'indexing'.
    [1564576570.727] Recognized 'indexing' as HopBlueprint(selector = { '[DocumentRouteSelector]' }, recipients = { 'music' }, ignoreResult = false).
    [1564576570.811] Running routing policy 'DocumentRouteSelector'.
    [1564576570.822] Policy 'DocumentRouteSelector' assigned a reply to this branch.
    [1564576570.828] Sequencer received reply with sequence id '-1163801147'.
    [1564576570.828] Source session received reply. 0 message(s) now pending.
</trace>

Messages sent to vespa (route default) :
----------------------------------------
PutDocument:	ok: 0 msgs/sec: 0.00 failed: 0 ignored: 1 latency(min, max, avg): 9223372036854775807, -9223372036854775808, 0
```

Without the selection (i.e. everything matches):

```
$ vespa-feeder --trace 6 doc.json

<trace>
    [1564576637.147] Source session accepted a 4096 byte message. 1 message(s) now pending.
    [1564576637.168] Sequencer sending message with sequence id '-1163801147'.
    [1564576637.176] Recognized 'default' as route 'indexing'.
    [1564576637.180] Recognized 'indexing' as HopBlueprint(selector = { '[DocumentRouteSelector]' }, recipients = { 'music' }, ignoreResult = false).
    [1564576637.256] Running routing policy 'DocumentRouteSelector'.
    [1564576637.268] Component '[MessageType:music]' selected by policy 'DocumentRouteSelector'.
    ...
</trace>

Messages sent to vespa (route default) :
----------------------------------------
PutDocument:	ok: 1 msgs/sec: 1.05 failed: 0 ignored: 0 latency(min, max, avg): 845, 845, 845
```

In the last case, in the [DocumentRouteSelector](https://github.com/vespa-engine/vespa/blob/master/documentapi/src/main/java/com/yahoo/documentapi/messagebus/protocol/DocumentRouteSelectorPolicy.java) routing policy,
the document matched the selection string / there was no selection string,
and the document was forward to the nex hop in the route.

## Document processing

Add custom processing of documents using [document processing](/en/document-processing.html).
The normal use case is to add document processors in the default route, before indexing. Example:

```
<services version="1.0">

    <container id="container" version="1.0">
        <document-api />
        <search />
        <document-processing>
            <chain id="default">
                <documentprocessor
                    id="com.mydomain.example.Rot13DocumentProcessor"
                    bundle="album-recommendation-docproc" />
            </chain>
        </document-processing>
        <nodes>
            <node hostalias="node1" />
        </nodes>
    </container>

    <content id="music" version="1.0">
        <redundancy>1</redundancy>
        <documents>
            <document >type="music" mode="index" />
        </documents>
        <nodes>
            <node hostalias="node1" distribution-key="0" />
        </nodes>
    </content>

</services>
```

Note that a new hop *default/chain.default* is added,
and the default route is changed to include this:

```
$ vespa-route

There are 6 route(s):
    1. default
    2. default-get
    3. music
    4. music-direct
    5. music-index
    6. storage/cluster.music

There are 3 hop(s):
    1. default/chain.default
    2. default/chain.indexing
    3. indexing
```
```
$ vespa-route --route default

The route 'default' has 2 hop(s):
    1. default/chain.default
    2. indexing
```

Note that the document processing chain must be called *default*
to automatically be included in the default route.

### Inherit indexing chain

An alternative to the above is inheriting the indexing chain - use this when getting this error:

```
Indexing cluster 'XX' specifies the chain 'default' as indexing chain.
As the 'default' chain is run by default, using it as the indexing chain will run it twice.
Use a different name for the indexing chain.
```

Call the chain something else than *default*, and let it inherit *indexing*:

```
<services version="1.0">

    <container id="container" version="1.0">
        <document-api />
        <search />
        <document-processing>
            <chain id="offer-processing" inherits="indexing">
                <documentprocessor id="processor.OfferDocumentProcessor"/>
            </chain>
        </document-processing>
        <nodes>
            <node hostalias="node1" />
        </nodes>
    </container>

    <content id="music" version="1.0">
        <redundancy>1</redundancy>
        <documents>
            <document type="offer" mode="index"/>
            <document-processing cluster="default" chain="offer-processing"/>
        </documents>
        <nodes>
            <node hostalias="node1" distribution-key="0" />
        </nodes>
    </content>

</services>
```

See [#13193](https://github.com/vespa-engine/vespa/issues/13193) for details.

## Multiple container clusters

Vespa can be configured to use more than one container cluster.
Use cases can be to separate search and document processing
or having different document processing clusters due to capacity constraints or dependencies.
Example with separate search and feeding/indexing container clusters:

```
<services version="1.0">

    <container id="container-search" version="1.0">
        <search />
        <nodes>
            <node hostalias="node1" />
        </nodes>
    </container>

    <container id="container-indexing" version="1.0">
        <http>
            <server id="httpServer2" port="8081" />
        </http>
        <document-api />
        <document-processing />
        <nodes>
            <node hostalias="node1" />
        </nodes>
    </container>

    <content id="music" version="1.0">
        <redundancy>1</redundancy>
        <documents>
            <document type="music" mode="index" />
            <document-processing cluster="container-indexing" />
        </documents>
        <nodes>
            <node hostalias="node1" distribution-key="0" />
        </nodes>
    </content>

</services>
```

Notes:
* The indexing route is explicit using
  [document-processing](/en/reference/services-content.html#document-processing)
  elements from the content to the container cluster
* Set up *document-api* on the same cluster as indexing to avoid network hop
  from feed endpoint to indexing processors
* If no *document-processing* is configured,
  it defaults to a container cluster named *default*.
  When using multiple container clusters,
  it is best practice to explicitly configure *document-processing*.

Observe the *container-indexing/chain.indexing* hop,
and the indexing chain is set up on the *container-indexing* cluster:

```
$ vespa-route

There are 6 route(s):
    1. default
    2. default-get
    3. music
    4. music-direct
    5. music-index
    6. storage/cluster.music

There are 2 hop(s):
    1. container-indexing/chain.indexing
    2. indexing
```
```
$ curl -s http://localhost:8081 | python -m json.tool | grep -C 3 chain.indexing

        {
            "bundle": "container-disc:7.0.0",
            "class": "com.yahoo.messagebus.jdisc.MbusClient",
            "id": "chain.indexing@MbusClient",
            "serverBindings": []
        },
        {
--
            "class": "com.yahoo.docproc.jdisc.DocumentProcessingHandler",
            "id": "com.yahoo.docproc.jdisc.DocumentProcessingHandler",
            "serverBindings": [
                "mbus://*/chain.indexing"
            ]
        },
        {
```

## Appendix: trace

Below is a trace example, no selection string:

```
$ cat doc.json
[
{
    "put": "id:mynamespace:music::123",
    "fields": {
         "album": "Bad",
         "artist": "Michael Jackson",
         "title": "Bad",
         "year": 1987,
         "duration": 247
    }
}
]

$ vespa-feeder --trace 6 doc.json
<trace>
    [1564571762.403] Source session accepted a 4096 byte message. 1 message(s) now pending.
    [1564571762.420] Sequencer sending message with sequence id '-1163801147'.
    [1564571762.426] Recognized 'default' as route 'indexing'.
    [1564571762.429] Recognized 'indexing' as HopBlueprint(selector = { '[DocumentRouteSelector]' }, recipients = { 'music' }, ignoreResult = false).
    [1564571762.489] Running routing policy 'DocumentRouteSelector'.
    [1564571762.493] Component '[MessageType:music]' selected by policy 'DocumentRouteSelector'.
    [1564571762.493] Resolving '[MessageType:music]'.
    [1564571762.520] Running routing policy 'MessageType'.
    [1564571762.520] Component 'music-index' selected by policy 'MessageType'.
    [1564571762.520] Resolving 'music-index'.
    [1564571762.520] Recognized 'music-index' as route 'container/chain.indexing [Content:cluster=music]'.
    [1564571762.520] Recognized 'container/chain.indexing' as HopBlueprint(selector = { '[LoadBalancer:cluster=container;session=chain.indexing]' }, recipients = {  }, ignoreResult = false).
    [1564571762.526] Running routing policy 'LoadBalancer'.
    [1564571762.538] Component 'tcp/vespa-container:19101/chain.indexing' selected by policy 'LoadBalancer'.
    [1564571762.538] Resolving 'tcp/vespa-container:19101/chain.indexing [Content:cluster=music]'.
    [1564571762.580] Sending message (version 7.83.27) from client to 'tcp/vespa-container:19101/chain.indexing' with 179.853 seconds timeout.
    [1564571762.581] Message (type 100004) received at 'container/container.0' for session 'chain.indexing'.
    [1564571762.581] Message received by MbusServer.
    [1564571762.582] Request received by MbusClient.
    [1564571762.582] Running routing policy 'Content'.
    [1564571762.582] Selecting route
    [1564571762.582] No cluster state cached. Sending to random distributor.
    [1564571762.582] Too few nodes seen up in state. Sending totally random.
    [1564571762.582] Component 'tcp/vespa-container:19114/default' selected by policy 'Content'.
    [1564571762.582] Resolving 'tcp/vespa-container:19114/default'.
    [1564571762.586] Sending message (version 7.83.27) from 'container/container.0' to 'tcp/vespa-container:19114/default' with 179.995 seconds timeout.
    [1564571762.587181] Message (type 100004) received at 'storage/cluster.music/distributor/0' for session 'default'.
    [1564571762.587245] music/distributor/0 CommunicationManager: Received message from message bus
    [1564571762.587510] Communication manager: Sending Put(BucketId(0x2000000000000020), id:mynamespace:music::123, timestamp 1564571762000000, size 275)
    [1564571762.587529] Communication manager: Passing message to source session
    [1564571762.587547] Source session accepted a 1 byte message. 1 message(s) now pending.
    [1564571762.587681] Sending message (version 7.83.27) from 'storage/cluster.music/distributor/0' to 'storage/cluster.music/storage/0/default' with 180.00 seconds timeout.
    [1564571762.587960] Message (type 10) received at 'storage/cluster.music/storage/0' for session 'default'.
    [1564571762.588052] music/storage/0 CommunicationManager: Received message from message bus
    [1564571762.588263] PersistenceThread: Processing message in persistence layer
    [1564571762.588953] Communication manager: Sending PutReply(id:mynamespace:music::123, BucketId(0x2000000000000020), timestamp 1564571762000000)
    [1564571762.589023] Sending reply (version 7.83.27) from 'storage/cluster.music/storage/0'.
    [1564571762.589332] Reply (type 11) received at 'storage/cluster.music/distributor/0'.
    [1564571762.589448] Source session received reply. 0 message(s) now pending.
    [1564571762.589459] music/distributor/0Communication manager: Received reply from message bus
    [1564571762.589679] Communication manager: Sending PutReply(id:music:music::123, BucketId(0x0000000000000000), timestamp 1564571762000000)
    [1564571762.589807] Sending reply (version 7.83.27) from 'storage/cluster.music/distributor/0'.
    [1564571762.590] Reply (type 200004) received at 'container/container.0'.
    [1564571762.590] Routing policy 'Content' merging replies.
    [1564571762.590] Reply received by MbusClient.
    [1564571762.590] Sending reply from MbusServer.
    [1564571762.590] Sending reply (version 7.83.27) from 'container/container.0'.
    [1564571762.612] Reply (type 200004) received at client.
    [1564571762.613] Routing policy 'LoadBalancer' merging replies.
    [1564571762.613] Routing policy 'MessageType' merging replies.
    [1564571762.615] Routing policy 'DocumentRouteSelector' merging replies.
    [1564571762.622] Sequencer received reply with sequence id '-1163801147'.
    [1564571762.622] Source session received reply. 0 message(s) now pending.
</trace>

Messages sent to vespa (route default) :
----------------------------------------
PutDocument:	ok: 1 msgs/sec: 3.30 failed: 0 ignored: 0 latency(min, max, avg): 225, 225, 225
```
