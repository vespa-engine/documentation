---
# Copyright Vespa.ai. All rights reserved.
title: Secret Store
category: cloud
---

Vespa Cloud supports secure storage and management of secrets for use in your application.
A secret is a text-based value such as an API key, a token
or other private configuration value required by your application.

By organizing secrets into vaults, setting application-specific access controls,
and integrating secrets cleanly into your application code, Vespa Cloud ensures that sensitive data
like API keys and tokens are kept safe and are easily updatable.

This guide takes you through secret management for your tenant and how to use them in your application.

Use the [Retrieval Augmented Generation (RAG) in Vespa](https://github.com/vespa-engine/sample-apps/tree/master/retrieval-augmented-generation#deploying-to-the-vespa-cloud-using-gpu)
sample application for a practical example getting started using the Secret Store.
This example uses the Secret Store to store an OpenAI API key.



## Secret management
In the Vespa Cloud console, the "Account" section of your tenant contains a
"Secret store" tab. This is where you configure all secrets for your tenant. 


### Vaults
Secrets are organized into vaults, where each vault can contain a number of
secrets. The vault also contains rules for which applications can use the
secrets in the vault. You can have any number of vaults. 

To create a new vault, click the "+ New vault" button. The vault name must
match the rule `[.a-zA-Z0-9_-]` meaning only alphanumeric characters and `.`,
`_`, and `-` are allowed. Spaces are not allowed. 

<img alt="Secret store overview" src="/assets/img/secret-store.png" />

After creation, you can delete the entire vault by clicking the red trash bin
button on the top right.


### Access control
Each vault has an "Access control" section which determines which application
has access to the secrets in the vault. For each application, you can set up
which environment - [dev/perf](https://cloud.vespa.ai/en/reference/environments#dev-and-perf)
or [prod](https://cloud.vespa.ai/en/reference/environments#prod) (including test and staging) - the
application should have access within. 

Note that the application must have been created before you can set access
control to it.
Use the steps at [Retrieval Augmented Generation (RAG) in Vespa](https://github.com/vespa-engine/sample-apps/tree/master/retrieval-augmented-generation#deploying-to-the-vespa-cloud-using-gpu)
to create an application and grant access.


### Secrets
To add a new secret, click the "+ New secret" button. The same naming rules
apply for secrets. You can give any value to the secret. Note that once this is
saved the secret will never be visible again. You can update the secret to new
values, but never retrieve the actual value. Maximum length for a secret is 64K
characters.

Each tenant has a limit of 15 secrets.

<img alt="Creating new secret" src="/assets/img/secret-store-secret.png" />

After the secret has been created, you can update the secret to a new value or
delete it. 

Note that when a secret is updated, applications using it will start using this
new value within 60 seconds.

Also note that your application will not deploy successfully if the application
requests a secret that for some reason is not available, by either not being
defined or does not have access to it.



## Example: Using an OpenAI API key for RAG
Set up a RAG search chain that uses an OpenAI API key as secret:

```xml
<services version="1.0" xmlns:deploy="vespa" xmlns:preprocess="properties">
    <container id="default" version="1.0">

        <!-- configure the OpenAI API key secret -->
        <secrets>
            <apiKey vault="my-vault" name="openai-api-key" />
        </secrets>

        <!-- configure the OpenAI client to use the secret -->
        <component id="openai" class="ai.vespa.llm.clients.OpenAI">
            <config name="ai.vespa.llm.clients.llm-client">
                <apiKeySecretName>apiKey</apiKeySecretName>
            </config>
        </component>

        <!-- configure a search chain to use the OpenAI client -->
        <search>
            <chain id="rag" inherits="vespa">
                <searcher id="ai.vespa.search.llm.RAGSearcher">
                    <config name="ai.vespa.search.llm.llm-searcher">
                        <providerId>openai</providerId>
                    </config>
                </searcher>
            </chain>
        </search>

    </container>
</services>
```
Try [Retrieval Augmented Generation (RAG) in Vespa](https://github.com/vespa-engine/sample-apps/tree/master/retrieval-augmented-generation#deploying-to-the-vespa-cloud-using-gpu)
for a practical example.



## Using secrets
To use the secret in an application, add `secrets` to `services.xml`:

```xml
<services version="1.0" xmlns:deploy="vespa" xmlns:preprocess="properties">
    <container id="default" version="1.0">

        <secrets>
            <myApiKey vault="my-vault" name="my-api-key" />
        </secrets>

    </container>
</services>
```

In this example, we refer to a secret named `my-api-key` in the vault
`my-vault` with the name `myApiKey` in the application.

To access this secret in a custom component, inject the `Secrets` as a
constructor parameter in the component, like a Searcher:

```java
import ai.vespa.secret.Secret;
import ai.vespa.secret.Secrets;
...

public class MySearcher extends Searcher {

    private final Secret apiKeySecret;

    public MySearcher(Secrets secrets) {
        apiKeySecret = secrets.get("myApiKey");
    }

    @Override
    public Result search(Query query, Execution execution) {
        String apiKey = apiKeySecret.current();
        // ... do something with the current value of secret ...
        return execution.search(query);
    }

}
```

Typically, store the `Secret` in your class, and when you want to use the
secret value itself, you call `Secret.current();`. This ensures that you will
use the current secret value if it is updated. Note that it can take up to 60
seconds for the current secret value to be updated for your container code. 

Ensure that you do not store the `current` value itself -
then the secret value will not be updated when the configuration is changed.
