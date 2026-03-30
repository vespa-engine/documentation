---
# Copyright Vespa.ai. All rights reserved.
title: AWS Archive guide
applies_to: cloud
redirect_from:
- /en/cloud/archive-guide-aws
---

{% include note.html content="This guide is for tenants using Vespa Cloud.
If your tenant uses **Enclave**, the archive buckets are in your own cloud account
and you can access them directly — see the
[Enclave archive guide](/en/operations/enclave/archive.html) instead." %}

Vespa Cloud exports log data, heap dumps, and Java Flight Recorder sessions to buckets in AWS S3.
This guide explains how to access this data.  Access to the data must happen through an AWS account
controlled by the tenant.  Data traffic to access this data is charged to this AWS account.

These resources are needed to get started:
* An AWS account
* An IAM Role in that AWS account
* The [AWS command line client](https://aws.amazon.com/cli/)

Access is configured through the Vespa Cloud Console in the tenant account screen.
Choose the "archive" tab, then expand the **AWS** section.

## Register IAM Role
<!-- TODO: Add screenshot of the AWS accordion expanded, showing the "Configure access to your cloud archive" button -->

Click **Configure access to your cloud archive** to open the configuration dialog.

In **Step 1**, enter the ARN of the IAM Role that should have access to the S3 buckets
(e.g. `arn:aws:iam::123456789012:role/my-iam-role`) and click **Save**.
Vespa Cloud will then grant access to that role on the S3 buckets.

## Grant access to Vespa Cloud resources
<!-- TODO: Add screenshot of the configure access modal showing Step 1 (IAM role input) and Step 2 (generated IAM policy) -->

In **Step 2** of the same dialog, a policy is generated that must be attached to your IAM Role.
Copy the policy and attach it to the IAM Role in your AWS account.
AWS requires permissions to be registered in both Vespa Cloud's AWS account (step 1)
and the tenant's AWS account (step 2).
Make your own equivalent policy should you have other requirements.
For more information, see the [AWS documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_manage-attach-detach.html).

## Access files using AWS CLI
<!-- TODO: Add screenshot of the download logs section showing the S3 URI table and CLI command -->

Once permissions have been granted, the IAM Role can access the contents of the archive
buckets.  Any AWS S3 client will work, but the AWS command line client is an easy tool
to use.  The archive page will list all buckets where data is stored, typically one
bucket per zone the tenant has applications.

The `--request-payer=requester` parameter is mandatory to make sure network traffic
is charged to the correct AWS account.

Refer to [access-log-lambda](https://github.com/vespa-cloud/vespa-documentation-search/blob/main/access-log-lambda/README.md)
for how to install and use `aws cli`, which can be used to download logs as in the illustration,
or e.g. list objects:

```
$ aws s3 ls --profile=archive --request-payer=requester \
  s3://vespa-cloud-data-prod.aws-us-east-1c-9eb633/vespa-team/

        PRE album-rec-searcher/
        PRE cord-19/
        PRE vespacloud-docsearch/
```

In the example above, the S3 bucket name is _vespa-cloud-data-prod.aws-us-east-1c-9eb633_
and the tenant name is _vespa-team_ (for that particular prod zone).
Archiving is per tenant, and a log file is normally stored with a key like:

    /vespa-team/vespacloud-docsearch/default/h2946a/logs/access/JsonAccessLog.default.20210629100001.zst

The URI to this object is hence:

    s3://vespa-cloud-data-prod.aws-us-east-1c-9eb633/vespa-team/vespacloud-docsearch/default/h2946a/logs/access/JsonAccessLog.default.20210629100001.zst

Objects are exported once generated - access log files are compressed and exported at least once per hour.

If you are having problems accessing the files, please run

    aws sts get-caller-identity

to verify that you are correctly assuming the role which has been granted access.

## Lambda processing

When processing logs using a lambda function,
write a minimal function to list objects,
to sort out access / keys / roles:

```
const aws = require("aws-sdk");
const s3 = new aws.S3({ apiVersion: "2006-03-01" });

const findRelevantKeys = ({ Bucket, Prefix }) => {
  console.log(`Finding relevant keys in bucket ${Bucket}`);
  return s3
    .listObjectsV2({ Bucket: Bucket, Prefix: Prefix, RequestPayer: "requester" })
    .promise()
    .then((res) =>
      res.Contents.map((content) => ({ Bucket, Key: content.Key }))
    )
    .catch((err) => Error(err));
};

exports.handler = async (event, context) => {
  const options = { Bucket: "vespa-cloud-data-prod.aws-us-east-1c-9eb633", Prefix: "MY-TENANT-NAME/" };
  return findRelevantKeys(options)
    .then((res) => {
      console.log("response: ", res);
      return { statusCode: 200 };
    })
    .catch((err) => ({ statusCode: 500, message: err }));
};
```

Note: Always set `RequestPayer: "requester"` to access the objects -
transfer cost is assigned to the requester.

Once the above lists the log files from S3,
review [access-log-lambda](https://github.com/vespa-cloud/vespa-documentation-search/blob/main/access-log-lambda/README.md)
for how to write a function to decompress and handle the log data.
