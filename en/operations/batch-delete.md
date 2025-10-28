---
# Copyright Vespa.ai. All rights reserved.
title: "Batch delete"
---

Options for batch deleting documents:

1. Use [vespa feed](../vespa-cli.html#documents):

   ```
   $ vespa feed -t my-endpoint deletes.json
   ```
2. Find documents using a query, delete, repeat. Pseudocode:

   ```
   while True; do
      query and read document ids, if empty exit
      delete document ids using /document/v1
      wait a sec # optional, add wait to reduce load while deleting
   ```
3. Use a [document selection](../documents.html#document-expiry) to expire documents.
   This deletes all documents *not* matching the expression.
   It is possible to use parent documents and imported fields for expiry of a document set.
   The content node will iterate over the corpus and delete documents (that are later compacted out):

   ```
   {% highlight xml %}



   {% endhighlight %}
   ```
4. Use [/document/v1](../reference/document-v1-api-reference.html#delete) to delete documents
   identified by a [document selection](../reference/document-select-language.html) -
   example dropping all documents from the *my_doctype* schema.
   The *cluster* value is the ID of the content cluster in *services.xml*,
   e.g., `<content id="my_cluster" version="1.0">`:

   ```
   $ curl -X DELETE \
     "$ENDPOINT/document/v1/my_namespace/my_doctype/docid?selection=true&cluster=my_cluster"
   ```
5. It is possible to drop a schema, with all its content, by removing the mapping to the content cluster.
   To understand what is happening, here is the status before the procedure:

   ```
   # ls $VESPA_HOME/var/db/vespa/search/cluster.music/n0/documents

   drwxr-xr-x 6 vespa vespa 4096 Oct 25 16:59 books
   drwxr-xr-x 6 vespa vespa 4096 Oct 25 12:47 music
   ```

   Remove the schema from configuration:

   ```
   <documents>
       <document type="music" mode="index" />
       <!--document type="books" mode="index" /-->
   </documents>
   ```

   It is not required to remove the schema file itself.
   It is however required to add a `schema-removal` entry to
   [validation-overrides.xml](../reference/validation-overrides.html):

   ```
   <validation-overrides>
       <allow until="2022-10-31">schema-removal</allow>
   </validation-overrides>
   ```

   {% include note.html content='Use validation override name `content-type-removal` before Vespa 8.73' %}

   Deploy the application package.
   This will reconfigure the content node processes,
   and the directory with the schema data is removed:

   ```
   # ls $VESPA_HOME/var/db/vespa/search/cluster.music/n0/documents

   drwxr-xr-x 6 vespa vespa 4096 Oct 25 12:47 music
   ```

   Add the mapping back and redeploy - the cluster now has a `books` schema with zero documents.

   ```
   # ls $VESPA_HOME/var/db/vespa/search/cluster.music/n0/documents

   drwxr-xr-x 6 vespa vespa 4096 Oct 25 17:06 books
   drwxr-xr-x 6 vespa vespa 4096 Oct 25 12:47 music
   ```

   Use the [Custom Component State API](../proton.html#custom-component-state-api)
   to inspect document count per schema.

   The procedure, deploying with and without the schema, is an efficient way to drop all documents.
   After the procedure, it is good practice to remove *validation-overrides.xml*
   or the `schema-removal` element inside, to avoid accidental data loss later.
   The directory listing above is just for illustration.

## Example

This is an end-to-end example on how to track number of documents, and delete a subset using a
[selection string](/en/reference/document-select-language.html).

### Feed sample documents

Feed a batch of documents, e.g. using the [vector-search](https://github.com/vespa-cloud/vector-search)
sample application:

```
$ vespa feed <(python3 feed.py 100000 3)
```

See number of documents for a node using the
[content.proton.documentdb.documents.total](/en/reference/searchnode-metrics-reference.html#content_proton_documentdb_documents_total) metric (here 100,000):

```
$ docker exec vespa curl -s http://localhost:19092/prometheus/v1/values | grep ^content.proton.documentdb.documents.total

  content_proton_documentdb_documents_total_max{metrictype="standard",instance="searchnode",documenttype="vector",clustername="vectors",vespa_service="vespa_searchnode",} 100000.0 1695383025000

  content_proton_documentdb_documents_total_last{metrictype="standard",instance="searchnode",documenttype="vector",clustername="vectors",vespa_service="vespa_searchnode",} 100000.0 1695383025000
```

Using the metric above is useful while feeding this example.
Another alternative is [visiting](../visiting.html) all documents to print the ID:

```
$ vespa visit --field-set "[id]" | wc -l
  100000
```

At this point, there are 100,000 document in the index.

### Define selection

Define the subset of documents to delete - e.g. by age or other criteria.
In this example, select random 1%. Do a test run:

```
$ vespa visit --field-set "[id]" --selection 'id.hash().abs() % 100 == 0' | wc -l
    1016
```

Hence, the selection string `id.hash().abs() % 100 == 0` hits 1,016 documents.

### Delete documents

Delete documents, see the number of documents deleted in the response:

```
$ curl -X DELETE \
  "http://localhost:8080/document/v1/mynamespace/vector/docid?selection=id.hash%28%29.abs%28%29+%25+100+%3D%3D+0&cluster=vectors"

  {
      "pathId":"/document/v1/mynamespace/vector/docid",
      "documentCount":1016
  }
```

In case of a large result set, a continuation token might be returned in the response, too:

```
"continuation": "AAAAEAAAA"
```

If so, add the token and redo the request:

```
$ curl -X DELETE \
  "http://localhost:8080/document/v1/mynamespace/vector/docid?selection=id.hash%28%29.abs%28%29+%25+100+%3D%3D+0&cluster=vectors&continuation=AAAAEAAAA"
```

Repeat as long as there are tokens in the output.
The token changes in every response.

### Validate

Check that all documents matching the selection criterion are deleted:

```
$ vespa visit --selection 'id.hash().abs() % 100 == 0' --field-set "[id]" | wc -l
  0
```

List remaining documents:

```
$ vespa visit --field-set "[id]" | wc -l
  98984
```
