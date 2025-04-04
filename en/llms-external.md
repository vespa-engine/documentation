---
# Copyright Vespa.ai. All rights reserved.
title: "External LLMs in Vespa"
---

Please refer to [Large Language Models in Vespa](llms-in-vespa.html) for an
introduction to using LLMs in Vespa.

Vespa provides a client for integration with OpenAI compatible APIs.
This includes, but is not limited to 
[OpenAI](https://platform.openai.com/docs/overview), 
[Google Gemini](https://ai.google.dev/), 
[Anthropic](https://www.anthropic.com/api), 
[Cohere](https://docs.cohere.com/docs/compatibility-api) 
and [Together.ai](https://docs.together.ai/docs/openai-api-compatibility).
You can also host your own OpenAI-compatible server using for example 
[VLLM](https://docs.vllm.ai/en/latest/getting_started/quickstart.html#quickstart-online) or 
[llama-cpp-server](https://llama-cpp-python.readthedocs.io/en/latest/server/).

{% include note.html content='Note that this is currently a Beta feature so changes can be expected.' %}

### Configuring the OpenAI client

To set up a connection to an LLM service such as OpenAI's ChatGPT, you need to
define a component in your application's
[services.xml](reference/services.html):

```
<services version="1.0">
  <container id="default" version="1.0">

    ...

    <component id="openai" class="ai.vespa.llm.clients.OpenAI">

      <!-- Optional configuration: -->
      <config name="ai.vespa.llm.clients.llm-client">
        <apiKeySecretName> ... </apiKeySecretName>
        <endpoint> ... </endpoint>
      </config>

    </component>

    ...

  </container>
</services>
```

To see the full list of available configuration parameters, refer to the [llm-client config definition file](https://github.com/vespa-engine/vespa/blob/master/model-integration/src/main/resources/configdefinitions/llm-client.def).

This sets up a client component that can be used in a
[searcher](glossary.html#searcher) or a [document processor](glossary.html#document-processor).

### API key configuration

Vespa provides several options to configure the API key used by the client.

1. Using the [Vespa Cloud secret store](https://cloud.vespa.ai/en/security/secret-store.html) to store the API key. This is done by setting the `apiKeySecretName` configuration parameter to the name of the secret in the secret store. This is the recommended way for Vespa Cloud users.
2. Providing the API key in the `X-LLM-API-KEY` HTTP header of the Vespa query. 
3. It is also possible to configure the API key in a custom component. For example, [this](https://github.com/vespa-engine/system-test/tree/master/tests/docproc/generate_field_openai) system-test shows how to retrieve the API key from a local file deployed with your Vespa application. Please note that this is NOT recommended for production use, as it is less secure than using the secret store, but it can be modified to suit your needs.

You can set up multiple connections with different settings. For instance, you
might want to run different LLMs for different tasks. To distinguish between the
connections, modify the `id` attribute in the component specification. We will
see below how this is used to control which LLM is used for which task.

As a reminder, Vespa also has the option of running custom LLMs locally. Please refer to
[running LLMs in your application](llms-local.html) for more information.

### Inference parameters

Please refer to the general discussion in [LLM parameters](llms-in-vespa.html#llm-parameters) for setting inference
parameters.

The OpenAI-client also has the following inference parameters that can be sent along
with the query:

<table class="table">
  <thead>
    <tr>
      <th>Parameter (Vespa)</th>
      <th>Parameter (OpenAI)</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>maxTokens</code></td>
      <td><code>max_completion_tokens</code></td>
      <td>Maximum number of tokens that can be generated in the chat completion.</td>
    </tr>
    <tr>
      <td><code>temperature</code></td>
      <td><code>temperature</code></td>
      <td>Number between 0 and 2. Higher values like 0.8 make output more random, while lower values like 0.2 make it more focused and deterministic.</td>
    </tr>
    <tr>
      <td><code>topP</code></td>
      <td><code>top_p</code></td>
      <td>An alternative to temperature sampling. Model considers tokens with top_p probability mass (0-1). Value of 0.1 means only tokens comprising top 10% probability are considered.</td>
    </tr>
    <tr>
      <td><code>seed</code></td>
      <td><code>seed</code></td>
      <td>If specified, the system will attempt to sample deterministically, so repeated requests with the same seed should return similar results. Determinism is not guaranteed.</td>
    </tr>
    <tr>
      <td><code>npredict</code></td>
      <td><code>n</code></td>
      <td>How many chat completion choices to generate for each input message. Note that you will be charged based on the number of generated tokens across all choices.</td>
    </tr>
    <tr>
      <td><code>frequencypenalty</code></td>
      <td><code>frequency_penalty</code></td>
      <td>Number between -2.0 and 2.0. Positive values penalize new tokens based on their frequency in the text so far, decreasing the likelihood of repetition. Negative values encourage repetition.</td>
    </tr>
    <tr>
      <td><code>presencepenalty</code></td>
      <td><code>presence_penalty</code></td>
      <td>Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics. Negative values encourage repeating content from the prompt.</td>
    </tr>
  </tbody>
</table>

Any parameter sent with the query will override configuration specified for the client component in `services.xml`.

Note that if you are not using OpenAI's API, the parameters may be handled differently than the descriptions above.


### Connecting to other OpenAI-compatible providers

By default, this particular client connects to the OpenAI service, but can be used against any
<a href="https://platform.openai.com/docs/guides/text-generation/chat-completions-api" data-proofer-ignore>OpenAI chat completion compatible API</a>
by changing the `endpoint` configuration parameter.

### FAQ

- **Q: How do I know if my LLM is compatible with the OpenAI client?**
  - A: The OpenAI client is compatible with any LLM that implements the OpenAI chat completion API. You can check the documentation of your LLM provider to see if they support this API.
- **Q: Can I use the [Responses](https://platform.openai.com/docs/api-reference/responses/create) provided by OpenAI**
  - A: No, currently only the [Chat Completion API](https://platform.openai.com/docs/api-reference/chat) is supported.
- **Q: Can I use the OpenAI client for reranking?**
  - A: Yes, but currently, you need to implement a [custom searcher](/en/searcher-development.html) that uses the OpenAI client to rerank the results.
- **Q: Can I use the OpenAI client for retrieving embeddings?**
  - A: No, currently, only the [Chat Completion API](https://platform.openai.com/docs/api-reference/chat) is supported.