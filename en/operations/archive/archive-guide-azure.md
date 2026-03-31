---
# Copyright Vespa.ai. All rights reserved.
title: Azure Archive guide
applies_to: cloud
---

{% include note.html content="This guide is for tenants using Vespa Cloud.
If your tenant uses **Enclave**, the archive buckets are in your own cloud account
and you can access them directly — see the
[Enclave archive guide](/en/operations/enclave/archive.html) instead." %}

Vespa Cloud exports log data, heap dumps, and Java Flight Recorder sessions to
Azure Blob Storage containers. This guide explains how to access this data.
Access to the data is through an Azure principal controlled by the tenant.

These resources are needed to get started:
* An Azure account
* An email address or principal with access to that account
* [AzCopy](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10)

Access is configured through the Vespa Cloud Console in the tenant account screen.
Choose the "archive" tab, then expand the **Azure** section.

## Register Azure principal
![Azure archive accordion](/assets/img/archive-azure-expanded-dropdown.png)

Click **Configure access to your cloud archive** to open the configuration dialog.

## Configure access
![Azure configure access](/assets/img/archive-azure-configure-access.png)

In **Step 1**, enter the email address or principal that should have access to the
blob storage containers (e.g. `email@example.com`) and click **Save**.
Vespa Cloud will then grant access to that principal on the storage containers.

In **Step 2**, you will receive an email from Microsoft inviting you to join the Vespa.ai tenant.
Open that email and follow the instructions to accept the invitation.
This is required in order to have the necessary permissions to access and download the logs.

## Access files using AzCopy
![Azure download logs](/assets/img/archive-azure-access-logs.png)

Once permissions have been granted, the Azure principal can access the contents of the archive
containers.  Any Azure Blob Storage client will work, but
[AzCopy](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10)
is an easy tool to use.  The archive page will list all containers where data is stored,
typically one container per zone the tenant has applications.

```
$ azcopy list CONTAINER_URI
```

Archiving is per tenant, and a log file is normally stored with a key like:

    mytenant/myapp/default/h2946a/logs/access/JsonAccessLog.default.20210629100001.zst

Objects are exported once generated - access log files are compressed and exported at least once per hour.
