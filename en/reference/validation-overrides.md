---
# Copyright Vespa.ai. All rights reserved.
title: validation-overrides.xml
---

*validation-overrides.xml* is added to the root of an
[application package](application-packages-reference.html)
(i.e. next to [services.xml](services.html))
to allow a deployment that otherwise fails to validate to proceed.
Validations which can be overridden in this way
are returned with a dash-separated validation-id preceding the validation message.
E.g. if the message is `field-type-change: Changing the type of field 'foo' to 'bar' is not supported`
the validation id is `field-type-change`.

Validations protect against inadvertently corrupting a production instance.
Overriding them may be useful e.g. if the application is not in production yet
or if you think the consequences of inconsistencies or loss of the data in a particular field are fine.

Read more about schema changes in the [schema reference](schema-reference.html#modifying-schemas).

## Structure

```
{% highlight xml %}

    validation-id

{% endhighlight %}
```

Any number of `allow` tags is permissible. Example:

```
{% highlight xml %}

    resources-reduction
    field-type-change

{% endhighlight %}
```

## allow

An `allow` tag disables a particular validation for a limited time.
It contains a single validation id, see [list](#list) below.
`allow` tags with unknown ids are ignored.

| Attribute | Mandatory | Value |
| --- | --- | --- |
| until | Yes | The last day this change is allowed, as a ISO-8601-format date in UTC, e.g. 2016-01-30. Dates may at most be 30 days in the future, but should be as close to now as possible for safety, while allowing time for review and propagation to all deployed zones. `allow`-tags with dates in the past are ignored. |
| comment | No | Text explaining the reason for the change to humans. |

## List of validation overrides

| ID | Required when... | Action needed or effect of change |
| --- | --- | --- |
| `indexing-change` | Changing what tokens are expected and stored in field indexes. | Requires reindexing of data. |
| `indexing-mode-change` | Changing the index mode (streaming, indexed, store-only) of documents. | Requires reindexing of data. |
| `field-type-change` | Field type changes. | Requires re-feeding data. |
| `resources-reduction` | Large reductions in node resources (> 50% of the current max total resources). | Might cause large load increase. |
| `content-type-removal` | Removal of a schema (causes deletion of all documents). | Causes loss of all documents in this schema. |
| `content-cluster-removal` | Removal (or id change) of content clusters. | Causes loss of all documents in the cluster. |
| `deployment-removal` | Removal of production zones from deployment.xml. | Causes removal of all clusters and data in the zones. |
| `global-document-change` | Changing global attribute for document types in content clusters. | Requires stopping all nodes, applying validation override and starting nodes again. |
| `global-endpoint-change` | Changing global endpoints. |  |
| `zone-endpoint-change` | Changing zone (possibly private) endpoint settings. |  |
| `redundancy-one` | The first deployment of an application with `redundancy=1` requires a validation override. A redundancy of 2 is required for clusters in production otherwise |  |
| `paged-setting-removal` | Typically removed due to [disadvantages](/en/attributes.html#paged-attributes-disadvantages) described in doc. May cause content nodes to run out of memory. | More data will be loaded into memory, might cause OOM. |
| `certificate-removal` | Removing data plane certificates, typically when moving to new certificates. | Unable to access endpoint with removed certificates. |

See [ValidationId.java](https://github.com/vespa-engine/vespa/blob/master/config-model-api/src/main/java/com/yahoo/config/application/api/ValidationId.java) for a complete list of validation overrides.
