---
# Copyright Vespa.ai. All rights reserved.
title: "/application/v2/tenant API reference"
redirect_from:
- /en/cloudconfig/tenant-rest-api.html
- /en/reference/tenant-rest-api.html
---

This is the /application/v2/tenant API reference with examples for the HTTP REST API to
[list](#list-tenants),
[create](#create-tenant) and
[delete](#delete-tenant) a tenant,
which can be used to [deploy](deploy-rest-api-v2.html) an application.

The response format is JSON. The tenant value is "default".

The current API version is 2. The API port is 19071 - use
[vespa-model-inspect](/en/operations-selfhosted/vespa-cmdline-tools.html#vespa-model-inspect) service configserver
to find config server hosts - example:
`http://myconfigserver.mydomain.com:19071/application/v2/tenant/`

## HTTP requests

| HTTP request | application/v2/tenant operation | Description |
| --- | --- | --- |
| GET | List tenant information. | |
|  | List tenants | ``` /application/v2/tenant/ ```   Example response:   ``` {% highlight json %} [     "default" ] {% endhighlight %} ``` |
|  | Get tenant | ``` /application/v2/tenant/default ```   Example response:   ``` {% highlight json %} {     "message": "Tenant 'default' exists." } {% endhighlight %} ``` |
| PUT | Create a new tenant. | |
|  | Create tenant | ``` /application/v2/tenant/default ```   Response: A message with the name of the tenant created - example:   ``` {% highlight json %} {     "message" : "Tenant default created." } {% endhighlight %} ```  {% include note.html content="This operation is asynchronous, it will eventually propagate to all config servers." %} |
| DELETE | Delete a tenant. | |
|  | Delete tenant | ``` /application/v2/tenant/default ```   Response: A message with the deleted tenant:   ``` {% highlight json %} {     "message" : "Tenant default deleted." } {% endhighlight %} ```  {% include note.html content="This operation is asynchronous, it will eventually propagate to all config servers." %} |

## Request parameters

None.

## HTTP status codes

Non-exhaustive list of status codes.
Any additional info is included in the body of the return call, JSON-formatted.

| Code | Description |
| --- | --- |
| 400 | Bad request. Client error. The error message should indicate the cause. |
| 404 | Not found. For example using a session id that does not exist. |
| 405 | Method not implemented. E.g. using GET where only POST or PUT is allowed. |
| 500 | Internal server error. Generic error. The error message should indicate the cause. |

## Response format

Responses are in JSON format, with the following fields:

| Field | Description |
| --- | --- |
| message | An info/error message. |
