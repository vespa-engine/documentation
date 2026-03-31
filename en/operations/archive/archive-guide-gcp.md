---
# Copyright Vespa.ai. All rights reserved.
title: GCP Archive guide
applies_to: cloud
redirect_from:
- /en/cloud/archive-guide-gcp
---

{% include note.html content="This guide is for tenants using Vespa Cloud.
If your tenant uses **Enclave**, the archive buckets are in your own cloud account
and you can access them directly — see the
[Enclave archive guide](/en/operations/enclave/archive.html) instead." %}

Vespa Cloud exports log data, heap dumps, and Java Flight Recorder sessions to
buckets in Google Cloud Storage. This guide explains how to access this data.
Access to the data is through a GCP project controlled by the tenant.
Data traffic to access this data is charged to this GCP project.

These resources are needed to get started:
* A GCP project
* A Google user account
* The [gcloud command line interface](https://cloud.google.com/sdk/docs/install)

Access is configured through the Vespa Cloud Console in the tenant account screen.
Choose the "archive" tab, then expand the **GCP** section.

## Register IAM principal
![GCP archive accordion](/assets/img/archive-gcp-expanded-dropdown.png)

Click **Configure access to your cloud archive** to open the configuration dialog.

## Grant access to Vespa Cloud resources
![GCP configure access](/assets/img/archive-gcp-configure-access.png)

Enter a [principal](https://cloud.google.com/iam/docs/overview) with a supported prefix
and click **Save**.  Vespa Cloud will then grant access to that principal on the Cloud Storage buckets.

Supported principal prefixes:
* `user:` — Google Account, e.g. `user:email@example.com`
* `serviceAccount:` — Service account, e.g. `serviceAccount:my-app@project.iam.gserviceaccount.com`
* `group:` — Google group, e.g. `group:admins@example.com`
* `domain:` — Google Workspace or Cloud Identity domain, e.g. `domain:example.com`

## Access files using Gcloud CLI
![GCP download logs](/assets/img/archive-gcp-access-logs.png)

Once permissions have been granted, the GCP member can access the contents of the archive
buckets.  Any Cloud Storage client will work, but the `gsutil` command line
client is an easy tool to use.  The archive page will list all buckets where
data is stored, typically one bucket per zone the tenant has applications.

The `-u user-project` parameter is mandatory to make sure network traffic is
charged to the correct GCP project.

```
$ gsutil -u my-project ls \
  gs://vespa-cloud-data-prod.gcp-us-central1-f-73770f/vespa-team/
        gs://vespa-cloud-data-prod.gcp-us-central1-f-73770f/vespa-team/album-rec-searcher/
        gs://vespa-cloud-data-prod.gcp-us-central1-f-73770f/vespa-team/cord-19/
        gs://vespa-cloud-data-prod.gcp-us-central1-f-73770f/vespa-team/vespacloud-docsearch/
```

In the example above, the bucket name is _vespa-cloud-data-prod.gcp-us-central1-f-73770f_
and the tenant name is _vespa-team_ (for that particular prod zone).
Archiving is per tenant, and a log file is normally stored with a key like:

    /vespa-team/vespacloud-docsearch/default/h7644a/logs/access/JsonAccessLog.20221011080000.zst

The URI to this object is hence:

    gs://vespa-cloud-data-prod.gcp-us-central1-f-73770f/vespa-team/vespacloud-docsearch/default/h2946a/logs/access/JsonAccessLog.default.20210629100001.zst

Objects are exported once generated - access log files are compressed and exported at least once per hour.

Note: Always set a user project to access the objects - transfer cost is
assigned to the requester.
