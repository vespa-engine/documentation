---
# Copyright Vespa.ai. All rights reserved.
title: Archive guide
---

Vespa Cloud exports log data, heap dumps, and Java Flight Recorder sessions to
storage buckets. The bucket system used will depend on which cloud provider is
backing the zone your application is running in. AWS S3 will be used in the AWS
zones, and Cloud Storage will be used in the GCP zones.

How to access and use the storage buckets is found in the documentation for the respective cloud providers:

 * [AWS S3](archive-guide-aws)
 * [Google Cloud Storage](archive-guide-gcp)


## Examples
These examples use GCP as source, replace with AWS commands as needed.
Here, _resonant-triode-123456_ is the Google project ID that owns the target bucket _my_access_logs_ for data copy
(and will get the data download cost, if any).

Use the CLUSTERS view in the Vespa Cloud Console to find hostname(s) for the nodes to export logs from -
then list contents:
```
$ gsutil -u resonant-triode-123456 ls \
  gs://vespa-cloud-data-prod-gcp-us-central1-f-73770f/mytenant/myapp/

$ gsutil -u resonant-triode-123456 ls \
  gs://vespa-cloud-data-prod-gcp-us-central1-f-73770f/mytenant/myapp/myinstance

$ gsutil -u resonant-triode-123456 ls \
  gs://vespa-cloud-data-prod-gcp-us-central1-f-73770f/mytenant/myapp/myinstance/h404a/logs/access
```
Copy files for a host to the _my_access_logs_ bucket:
```
$ gsutil -u resonant-triode-123456 \
  -m -o "GSUtil:parallel_process_count=1" \
  cp -r \
  gs://vespa-cloud-data-prod-gcp-us-central1-f-73770f/vespa-team/vespacloud-docsearch/default/h404a \
  gs://my_access_logs/vespa-files
```
`rsync` can be used to reduce number of files copied, using `-x` to exclude paths:
```
$ gsutil -u resonant-triode-123456 \
  -m -o "GSUtil:parallel_process_count=1" \
  rsync -r \
  -x '.*/connection/.*|.*/vespa/.*|.*/zookeeper/.*' \
  gs://vespa-cloud-data-prod-gcp-us-central1-f-73770f/vespa-team/vespacloud-docsearch/default/h404a \
  gs://my_access_logs/vespa-files
```
Refer to [cloud-functions](https://github.com/vespa-engine/sample-apps/tree/master/examples/google-cloud/cloud-functions)
and [lambda](https://github.com/vespa-engine/sample-apps/tree/master/examples/aws/lambda)
for how to write and deploy simple functions to process files in Google Cloud and AWS.

For local processing, copy files for a host to local file system (or use `rsync`):
```
$ gsutil -u resonant-triode-123456 \
  -m -o "GSUtil:parallel_process_count=1" \
  cp -r \
  gs://vespa-cloud-data-prod-gcp-us-central1-f-73770f/vespa-team/vespacloud-docsearch/default/h404a \
  .
```
Use [zstd](https://facebook.github.io/zstd/) to decompress files:
```
$ zstd -d *
```
Example: Filter out healthchecks using [jq](https://stedolan.github.io/jq/):
```
$ cat JsonAccessLog.20230117* | jq '.  |
  select (.uri != "/status.html")      |
  select (.uri != "/state/v1/metrics") |
  select (.uri != "/state/v1/health")'
```
Add a human-readable date field per access log entry:
```
$ cat JsonAccessLog.20230117* | jq '.  |
  select (.uri != "/status.html")      |
  select (.uri != "/state/v1/metrics") |
  select (.uri != "/state/v1/health")  |
  . +{iso8601date:(.time|todateiso8601)}'
```
