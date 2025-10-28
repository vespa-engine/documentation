---
# Copyright Vespa.ai. All rights reserved.
title: "Configuration proxy"
category: oss
redirect_from:
- /en/reference/config-proxy.html
- /en/operations/config-proxy.html
---

Read [application packages](/en/application-packages.html)
for an overview of the cloud config system.
The *config proxy* runs on every Vespa node.
It has a set of config sources, defined in
[VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables).

The config proxy will act as a proxy for config clients on the same machine,
so that all clients can ask for config on *localhost:19090*.
The *config source* that the config proxy uses is set in
[VESPA_CONFIGSERVERS](/en/operations-selfhosted/files-processes-and-ports.html#environment-variables)
and consists of one or more config sources
(the addresses of [config servers](/en/operations-selfhosted/configuration-server.html)).

The proxy has a memory cache that is used to serve configs if it is possible.
In default mode, the proxy will have an outstanding request to the config server
that will return when the config has changed (a new generation of config).
This means that every time config changes on the config server,
the proxy will get a response, update its cache and respond to all its clients with the changed config.

The config proxy has two modes:

| Mode | Description |
| --- | --- |
| default | Gets config from server and stores in memory cache. The config proxy will always be started in *default* mode. Serves from cache if possible. Always uses a config source. If restarted, it will lose all configs that were cached in memory. |
| memorycache | Serves config from memory cache only. Never uses a config source. A restart will lose all cached configs. Setting the mode to *memorycache* will make all applications on the node work as before (given that they have previously been running and requested config), since the config proxy will serve config from cache and work without connection to any config server. Applications on this node will not work if the config proxy stops, is restarted or crashes. |

Use [vespa-configproxy-cmd](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-configproxy-cmd)
to inspect cached configs, mode, config sources etc., there are also some commands to change some of the settings.
Run the command as:

```
$ vespa-configproxy-cmd -m
```

to see all possible commands.

## Detaching from config servers

```
$ vespa-configproxy-cmd -m setmode memorycache
```

## Inspecting config

To inspect the configuration for a service, in this example a searchnode (proton) instance, do:

1. Find the active config generation used by the service,
   using [/state/v1/config](/en/reference/state-v1.html#state-v1-config) -
   example for *http://localhost:19110/state/v1/config*, here the generation is 2:

   ```
   {% highlight json %}
   {
       "config": {
           "generation": 2,
           "proton": {
               "generation": 2
           },
           "proton.documentdb.music": {
               "generation": 2
           }
       }
   }
   {% endhighlight %}
   ```
2. Find the relevant *config definition name*, *config id* and *config generation* using
   [vespa-configproxy-cmd](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-configproxy-cmd) - e.g.:

   ```
   $ vespa-configproxy-cmd | grep proton

   vespa.config.search.core.proton,music/search/cluster.music/0,2,MD5:40087d6195cedb1840721b55eb333735,XXHASH64:43829e79cea8e714
   ```

   `vespa.config.search.core.proton` is the *config definition name* for this particular config,
   `music/search/cluster.music/0` is the *config id*
   used by the proton service instance on this node and `2` is the active config generation.
   This means, the service is using the correct config generation as it is matching the /state/v1/config response
   (a restart can be required for some config changes).
3. Get the generated config using
   [vespa-get-config](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-get-config) - e.g.:

   ```
   $ vespa-get-config -n vespa.config.search.core.proton -i music/search/cluster.music/0

   basedir "/opt/vespa/var/db/vespa/search/cluster.music/n0"
   rpcport 19106
   httpport 19110
   ...
   ```

   {% include important.html content='Omitting `-i` will return the
   default configuration,
   meaning not generated for the active service instance.' %}
