---
# Copyright Vespa.ai. All rights reserved.
title: "Vespa CLI"
redirect_from:
- /en/vespa-cli-feed.html
---

Vespa CLI is the command-line client for Vespa.
It is a single binary without any runtime dependencies and is available for Linux, macOS and Windows.
With Vespa CLI you can:
* Clone the [sample applications](https://github.com/vespa-engine/sample-apps/) repository
* Deploy your application to a Vespa installation running locally or remote
* Deploy your application in [Vespa Cloud](https://cloud.vespa.ai/)* Feed and [query](query-language.html#query-examples) documents
  * Send custom requests with automatic authentication
  * Automate deployment operations with [vespa auth api-key](reference/vespa-cli/vespa_auth_api-key.html)

Install Vespa CLI:
* Homebrew: `brew install vespa-cli`
* [Download from GitHub](https://github.com/vespa-engine/vespa/releases)

To learn the basics on how to use Vespa CLI, see
the [quick start guide](vespa-quick-start.html) or the [cheat sheet
below](#cheat-sheet).

See the [reference documentation](reference/vespa-cli/vespa.html)
for documentation of individual Vespa CLI commands and their options. This
documentation is also bundled with CLI and accessible through `vespa help
<command>` or `man vespa-<command>`.

## Cheat sheet

### Install, configure and run

```
{% highlight shell %}
# Install - make sure to upgrade frequently for new features
$ brew install vespa-cli
$ brew upgrade vespa-cli

# Set home dir to a writeable directory - useful in some container contexts
$ export VESPA_CLI_HOME=/tmp

# export a token value for dataplane access
$ export VESPA_CLI_DATA_PLANE_TOKEN='value-of-token'

# Get help
$ vespa document put --help
{% endhighlight %}
```

### Login and init

```
{% highlight shell %}
# Use endpoints on localhost
$ vespa config set target local

# Use Vespa Cloud
$ vespa config set target cloud

# Use a browser to log into Vespa Cloud
$ vespa auth login

# Configure application instance
$ vespa config set application vespa-team.vespacloud-docsearch.default

# Configure application instance, override global configuration (write to local .vespa)
$ vespa config set --local application vespa-team.vespacloud-docsearch.other
{% endhighlight %}
```

### Deployment

```
{% highlight shell %}
# Deploy an application package from cwd
$ vespa deploy

# Deploy to a specific zone
$ vespa deploy -z perf.aws-us-east-1c

# Get the deployed application package as a .zip-file
$ vespa fetch

# Deploy an application package from cwd to a prod zone with CD pipeline in Vespa Cloud using deployment.xml
$ vespa prod deploy

# Track deployment to Vespa Cloud status
$ vespa status

# Validate endpoint status, get endpoint only
$ vespa status --format=plain

# Remove a deployment from Vespa Cloud
$ vespa destroy -a vespa-team.vespacloud-docsearch.other
{% endhighlight %}
```

### Documents

```
{% highlight shell %}
# Put a document from file
$ vespa document put file-with-one-doc.json

# Put a document
$ vespa document put id:mynamespace:music::a-head-full-of-dreams --data '
{
    "fields": {
        "album": "A Head Full of Dreams",
        "artist": "Coldplay"
    }
}'

# Put a document, ID in JSON
$ vespa document put --data '
{
    "put": "id:mynamespace:music::a-head-full-of-dreams",
    "fields": {
        "album": "A Head Full of Dreams",
        "artist": "Coldplay"
    }
}'

# Update a document
$ vespa document update id:mynamespace:music::a-head-full-of-dreams --data '
{
    "fields": {
        "album": {
            "assign": "A Head Full of Thoughts"
        }
    }
}'

# Get one or more documents
$ vespa document get id:mynamespace:music::a-head-full-of-dreams
$ vespa document get id:mynamespace:music::a-head-full-of-dreams id:mynamespace:music::when-we-all-fall-asleep-where-do-we-go

# Delete a document
$ vespa document remove id:mynamespace:music::a-head-full-of-dreams

# Feed multiple documents or feed from stdin
$ vespa feed *.jsonl
$ cat docs.json | vespa feed -

# Feed to Vespa Cloud
$ vespa feed --application mytenant.myapp -target https://b123e1db.b68a1234.z.vespa-app.cloud feedfile.json

# Print successful and failed operations:
$ vespa feed --verbose docs.json

# Display a periodic summary every 3 seconds while feeding:
$ vespa feed --progress=3 docs.json

# Export all documents in "doc" schema, using "default" container cluster
$ vespa visit --zone prod.aws-us-east-1c --cluster default --selection doc

# Export slice 0 of 10 - approximately 10% of the documents
$ vespa visit --slices 10 --slice-id 0

# List IDs - great for counting total number of documents
$ vespa visit --field-set "[id]"

# Export fields "title" and "term_count" from "doc" schema
$ vespa visit --field-set "doc:title,term_count"

# Export documents using a selection string
$ vespa visit --selection 'doc.last_updated > now() - 86400'

# Export all documents in "doc" schema, in "open" namespace
$ vespa visit --selection 'doc AND id.namespace == "open"'

# Export a specific document, including synthetic (generated) fields
$ vespa visit --selection 'id == "id:en:doc::doc-en-7764"' --field-set '[all]'

# Copy documents from one cluster to another:
$ vespa visit --target http://localhost:8080 | vespa feed --target http://localhost:9090 -
{% endhighlight %}
```

Notes:
* The input files for `vespa feed` contains either a JSON array of feed operations,
  or one JSON operation per line ([JSONL](https://jsonlines.org/)).
* The [<document-api>](/en/reference/services-container.html#document-api)
  must be enabled in the container before documents can be fed or accessed -
  see [example](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation/app/services.xml).
* For automation, see example usage in a
  [GitHub Action](https://github.com/vespa-engine/documentation/blob/master/.github/workflows/feed.yml).
  This action uses security credentials in `VESPA_CLI_DATA_PLANE_CERT` and `VESPA_CLI_DATA_PLANE_KEY`
  for easy security management in GitHub.

### Queries

```
{% highlight shell %}
# Query for all documents in all schemas / sources
$ vespa query 'yql=select * from sources * where true'

# YQL parameter is assumed if missing - this is equivalent to the above
$ vespa query 'select * from sources * where true'

# Query with an extra query API parameter
$ vespa query 'select * from music where album contains "head"' \
  hits=5

# Use verbose to print a curl equivalent, too
$ vespa query -v 'select * from music where album contains "head"' hits=5

# Query a different port (after modifying http server port)
$ vespa query 'select * from sources * where true' -t 'http://127.0.0.1:9080'

# Use a query file - useful for large queries, e.g., when using query vectors
$ vespa query --file queries-vector.json
{% endhighlight %}
```

Example query file:

```
{% highlight json %}
{
    "yql": "select product_id, title from products where {targetHits: 200}nearestNeighbor(dense_embedding, q_vector)",
    "input.query(q_vector)": [-0.050548091530799866, ... ,0.028366032987833023],
    "ranking": "vector_distance"
}
{% endhighlight %}
```
