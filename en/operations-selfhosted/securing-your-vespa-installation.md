---
# Copyright Vespa.ai. All rights reserved.
title: "Securing a Vespa Installation"
redirect_from:
- /en/securing-your-vespa-installation.html
---
{% include note.html content="This document is only relevant for **self-hosting Vespa** as Vespa Cloud does this for you." %}

It is critical to understand the security requirements and limitations
of any networked system. Vespa is no exception. This document gives the most
important information related to security at the network and physical host levels.
 
To keep the self-hosted Vespa installation safe, follow the guidelines outlined below:

1. Isolate the Vespa hosts
2. Secure the application container with access control filters and TLS
3. Lockdown directory permissions
4. Securing Vespa with mutually authenticated TLS (mTLS)



## Isolating the Vespa hosts

**When running self-hosted Vespa instances, hosts running Vespa MUST NOT be directly exposed 
to the public internet or to untrusted networks. Failure to ensure this may lead to data 
exfiltration/infiltration or host compromise.**
 
Vespa's internal protocols are not authenticated by default and are therefore not safe
in the face of untrusted network actors.
When running Vespa in your own organization, or on the public cloud in particular, this
is something you must take into account.
 
Connections to _any_ hosts running Vespa services should _only_ be allowed from
a controlled set of trusted hosts. All Vespa hosts must be able to connect
to, and receive connections from, all other Vespa hosts that are part of the
same installation. For added security, consider limiting Vespa hosts to only
be able to talk to other Vespa hosts. If you are contacting external services
as part of [federation](/en/federation.html) in the application container, your
container hosts must be able to connect to these services.
 
This may be implemented by e.g. iptables, AWS Security Groups or similar technologies.
 
The entry point into your Vespa installation is port 8080 on hosts running the
application container. This port is used for feed, document retrieval and search
queries. It should only be exposed to an untrusted network if you have properly
[secured the application container](#securing-the-application-container). It
should never be exposed directly to external traffic. All traffic to the containers
should be sent by your frontends or backends.
 
Inter-node communication inside a Vespa installation is not encrypted by default
and will need to be configured explicitly as documented in 
[Securing Vespa with mutually authenticated TLS](/en/operations-selfhosted/mtls.html).



## Securing the application container

By default, the container allows unauthenticated writes to, and reads from, the Vespa installation.
For a production deployment, this must be locked down.
 
Connections to the HTTP containers may be [protected with TLS](/en/jdisc/http-server-and-filters.html#tls).
Mutual TLS is supported and should be configured.
 
Access to the container API endpoints can be controlled using
[request filters](/en/jdisc/http-server-and-filters.html#set-up-filter-chains).
These filters can implement the required authentication and authorization logic
for your specific use case.
 
If you do not set up TLS with restrictive filter logic, you should restrict the
container port in the same way as you would the rest of the Vespa hosts.



## Locking down directory permissions

All Vespa processes run under the Linux user given by `$VESPA_USER` and store their
data under `$VESPA_HOME`. You should ensure the files and directories under
`$VESPA_HOME` are not accessible by other users if you store sensitive data in your application.

Note also that private keys used by the container to set up TLS must be protected 
to be readable by the container process only.
 
Vespa does not have application-level support for encryption of on-disk document stores or
indexes. This would typically be implemented through file-system or storage-level (e.g. remote cloud storage)
encryption.



## Securing Vespa with mutually authenticated TLS (mTLS)

Protect all internal endpoints and protocols in Vespa with mutually authenticated Transport Layer Security (mTLS).
See the [dedicated documentation](/en/operations-selfhosted/mtls.html) on how to get started,
and try the [multinode-HA](https://github.com/vespa-engine/sample-apps/tree/master/examples/operations/multinode-HA)
example.
