---
# Copyright Vespa.ai. All rights reserved.
title: "Using ZooKeeper"
redirect_from:
- /documentation/using-zookeeper.html
---

The Vespa container supports [ZooKeeper](https://zookeeper.apache.org/), which
allows distributed synchronization across nodes in a container cluster.

Once enabled all nodes in a container cluster will automatically form a
ZooKeeper ensemble, and participate as servers. Vespa takes care of
reconfiguring ZooKeeper members when nodes are added or removed from the
container cluster.

Note that Vespa enforces an optimal node limit for clusters with ZooKeeper.
Application packages that violate this node count will be rejected.
The valid number of nodes is 3, 5 or 7.
See [#15762](https://github.com/vespa-engine/vespa/issues/15762) for other node counts.


## Configuration

1. ZooKeeper must be explicitly enabled in the [container cluster
configuration](reference/services-container.html#zookeeper).

2. The application must specify an dependency on `zkfacade`. Example for `pom.xml`:
   
   ```xml
   <dependency>
     <groupId>com.yahoo.vespa</groupId>
     <artifactId>zkfacade</artifactId>
     <version>[vespa-version]</version>
     <scope>provided</scope>
   </dependency>
   ```


## Code example

ZooKeeper features are exposed through
[VespaCurator](https://github.com/vespa-engine/vespa/blob/master/zkfacade/src/main/java/com/yahoo/vespa/curator/api/VespaCurator.java).
[Inject](jdisc/injecting-components.html) `VespaCurator` to use it. [Handler](jdisc/developing-request-handlers.html) example:

```java
public class MyRequestHandler extends ThreadedHttpRequestHandler {

    private final VespaCurator curator;

    @Inject
    public CuratorHandler(Executor executor, VespaCurator curator) {
        super(executor);
        this.curator = curator;
    }

    @Override
    public HttpResponse handle(HttpRequest httpRequest) {
        Path lockPath = Path.fromString("/locks/mylock");
        Duration timeout = Duration.ofSeconds(1);
        try (var lock = curator.lock(lockPath, timeout)) {
            // Do something while holding lock
        } catch (Exception e) {
            throw new RuntimeException("Failed to acquire lock " + lockPath, e);
        }
    }

}
```
