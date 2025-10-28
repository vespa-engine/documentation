---
# Copyright Vespa.ai. All rights reserved.
title: "Procedure: Change from attribute to index"
category: oss
redirect_from:
- /en/operations/procedure-change-attribute-index.html
---

Changing between `index` and `attribute` is a common field change operation
to optimize performance.
Use the [reindexing](/en/operations/reindexing.html) feature to safely migrate data to/from index structures.

Changing from attribute to index can be seen as "drop attribute" and "add index".
When the attribute aspect of a field is removed, the field's data is not queryable after deployment.
The reindexing process will populate the field's index structure,
but this takes time, depending on corpus size.

Another approach is to run with both attribute and index in the transition, keeping data available for queries.
The gist of this procedure is to add `index`, run a reindex -
then remove `attribute` aspect:

```
# field configuration at start
field artist type string {
    indexing: summary | attribute
}
->

# intermediate step to populate index structure, keeping the data in the attribute
field artist type string {
    indexing: summary | attribute | index
    match: word
    stemming: none
}
->

# final configuration, migrated to index
field artist type string {
    indexing: summary | index
    match: word
    stemming: none
}
```

{% include note.html content='If the field is used as a filter only (i.e. no ranking),
consider adding `rank: filter`, see example in
[feature-tuning](/en/performance/feature-tuning.html).' %}

## Procedure

1. Test this using the [quick-start](/en/vespa-quick-start.html),
   changing the `artist` field to an attribute before running.
   Also add a [validation override](/en/reference/validation-overrides.html)
   in `src/main/application/validation-overrides.xml`:

   ```
   <validation-overrides>
       <allow until="2021-08-30">indexing-change</allow>
   </validation-overrides>
   ```
2. Run the quick start, stop after feeding documents.
   Run a query to validate data can be queried:

   ```
   $ curl "http://localhost:8080/search/?ranking=rank_albums&yql=select%20%2A%20from%20sources%20%2A%20where%20artist%20contains%20%22Coldplay%22"
   ```

   One can also [dump current index structures](#appendix), see `artist` as an attribute.
3. Add index aspect and match/stemming settings to the field, deploy and observe output

   ```
   field artist type string {
       indexing: summary | attribute | index
           match    : word
           stemming : none
   }

   $ (cd src/main/application && zip -r - .) |   curl --header Content-Type:application/zip --data-binary @- \
     localhost:19071/application/v2/tenant/default/prepareandactivate

   {
     "log": [
       {
         "time": 1628239290150,
         "level": "WARNING",
         "message": "Change(s) between active and new application that may require re-index:\nindexing-change:
                     Consider re-indexing document type 'music' in cluster 'music' because:\n
                     1) Document type 'music': Field 'artist' changed: add index aspect,
                     indexing script: '{ input artist | summary artist | attribute artist; }' ->
                                      '{ input artist | exact | summary artist | attribute artist | index artist; }'\n"
       }
     ],
     "tenant": "default",
     "url": "http://localhost:19071/application/v2/tenant/default/application/default/environment/prod/region/default/instance/default",
     "message": "Session 3 for tenant 'default' prepared and activated.",
     "configChangeActions": {
       "restart": [],
       "refeed": [],
       "reindex": [
         {
           "name": "indexing-change",
           "documentType": "music",
           "clusterName": "music",
           "messages": [
             "Document type 'music': Field 'artist' changed:
                add index aspect, indexing script:
                  '{ input artist | summary artist | attribute artist; }'
                ->
                  '{ input artist | exact | summary artist | attribute artist | index artist; }'"
           ],
           "services": [
             {
               "serviceName": "searchnode",
               "serviceType": "searchnode",
               "configId": "music/search/cluster.music/0",
               "hostName": "vespa-container"
             }
           ]
         }
       ]
     }
   }
   ```
4. Wait for the new configuration generation to be activated on the config server(s) -
   this is normally quite immediate.
   After that, allow up to 3 minutes for the config servers to set reindexing ready,
   track this using the `reindexing` endpoint:

   ```
   $ while true; do
       curl http://localhost:19071/application/v2/tenant/default/application/default/environment/prod/region/default/instance/default/reindexing | jq .
       sleep 10
     done

   {
     "enabled": true,
     "clusters": {
       "music": {
         "pending": {
           "music": 3
         },
         "ready": {
           "music": {}
         }
       }
     }
   }

   ...

   {
     "enabled": true,
     "clusters": {
       "music": {
         "pending": {},
         "ready": {
           "music": {
             "readyMillis": 1628665589516
           }
         }
       }
     }
   }
   ```
5. When ready, deploy again to start reindexing,
   wait for it to complete (use the loop in previous step):

   ```
   $ (cd src/main/application && zip -r - .) |   curl --header Content-Type:application/zip --data-binary @- \
     localhost:19071/application/v2/tenant/default/prepareandactivate

   ...

   {
     "enabled": true,
     "clusters": {
       "music": {
         "pending": {},
         "ready": {
           "music": {
             "readyMillis": 1628665589516
           }
         }
       }
     }
   }

   ...

   {
     "enabled": true,
     "clusters": {
       "music": {
         "pending": {},
         "ready": {
           "music": {
             "readyMillis": 1628665589516,
             "startedMillis": 1628668739973,
             "endedMillis": 1628668740536,
             "state": "successful"
           }
         }
       }
     }
   }
   ```
6. Dumping the index structures now shows artist both in index and attribute, and there is an entry in vespa.log.
   Verify the query still works:

   ```
   $ docker exec vespa /usr/bin/sh -c 'vespa-logfmt | grep Reindexer'
   [2021-08-11 07:59:00.535] INFO    : container-clustercontroller Container.ai.vespa.reindexing.Reindexer
                                       Completed reindexing of datatype music (code: 1412693671) after PT0.558683S

   $ curl "http://localhost:8080/search/?ranking=rank_albums&yql=select%20%2A%20from%20sources%20%2A%20where%20artist%20contains%20%22Coldplay%22"
   ```
7. As data is now reindexed into the index data structures, deploy without attribute.
   (Observe changes to index files, "artist" is now in index only).
   Test query after restart:

   ```
   field artist type string {
       indexing: summary | index
           match    : word
           stemming : none
   }

   $ (cd src/main/application && zip -r - .) |   curl --header Content-Type:application/zip --data-binary @- \
     localhost:19071/application/v2/tenant/default/prepareandactivate

   $ curl "http://localhost:8080/search/?ranking=rank_albums&yql=select%20%2A%20from%20sources%20%2A%20where%20artist%20contains%20%22Coldplay%22"
   ```
8. Optional: restart Vespa - a restart will reclaim memory from the attribute:

   ```
   $ docker exec vespa sh -c 'vespa-stop-services && vespa-start-services'
   ```

Notes:
* The match/stemming settings above are set to the same at default attribute settings

## Appendix

To inspect attribute and index data (can be useful when troubleshooting),
use [vespa-proton-cmd](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-proton-cmd),
then list files:

```
$ docker exec vespa vespa-proton-cmd --local triggerFlush
$ docker exec vespa find /opt/vespa/var/db/vespa/search/cluster.music/n0/documents/music/0.ready
```
