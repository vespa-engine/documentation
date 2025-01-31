---
# Copyright Vespa.ai. All rights reserved.
title: "Generative feeding with LLMs"
---

Large Language Models (LLMs) are capable of many text processing tasks including 
information extraction, summarization, question answering, translation, sentiment analysis and etc.
Vespa makes it easy to use LLMs at scale with [generate](reference/indexing-language-reference.html#generate) indexing expression.
During [feeding](reads-and-writes.html#feed-flow) it generates text values for synthetic fields based on text values of other fields.
Consider the following schema as an example:

```
schema passage {
    document passage {
        field id type string {
            indexing: summary | attribute
        }
    
        field text type string {
            indexing: summary | index
            index: enable-bm25
        }
    }
    
    field names type array<string> {
        indexing: input text | generate names_extractor | split "\n" | index | summary
        index: enable-bm25
    }
    
    field text_norwegian type string {
        indexing: input text | generate norwegian_translator | index | summary
        index: enable-bm25
    }
}
```

This schema includes two synthetic fields, `names` and `text_norwegian`, generated from `text` field during feeding.
Generators `names_extractor` and `norwegian_translator` are ids for text generator components, 
which use an LLM for named entity recognition and translation.
These components are specified in `services.xml` as follows:

```xml
<container id="container" version="1.0">
    ...
    <secrets>
        <openai-api-key vault="sample-apps" name="openai-dev"/>
    </secrets>

    <component id="openai" class="ai.vespa.llm.clients.OpenAI">
        <config name = "ai.vespa.llm.clients.llm-client">
            <apiKeySecretName>openai-api-key</apiKeySecretName>
            <model>gpt-4o-mini</model>
        </config>
    </component>
    
    <component id="names_extractor" class="ai.vespa.llm.generation.LanguageModelTextGenerator">
        <config name="ai.vespa.llm.generation.language-model-text-generator">
            <providerId>openai</providerId>
            <promptTemplateFile>files/names_extractor_prompt.txt</promptTemplateFile>
        </config>
    </component>

    <component id="norwegian_translator" class="ai.vespa.llm.generation.LanguageModelTextGenerator">
        <config name="ai.vespa.llm.generation.language-model-text-generator">
            <providerId>openai</providerId>
            <promptTemplateFile>files/norwegian_translator_prompt.txt</promptTemplateFile>
        </config>
    </component>
    ...
</container>
```

Both `names_extractor` and `norwegian_translator` specify `openai` as `providerId`, 
referencing `OpenAI` client component configured with `gpt-4o-mini` model.
See [LLM Client config definition](https://github.com/vespa-engine/vespa/blob/master/model-integration/src/main/resources/configdefinitions/llm-client.def) for other parameters.

Prompt templates are specified in separate files, e.g. `files/names_extractor_prompt.txt`.
```
Your task is to extract names of people, locations and events from text.
Output should include a list of names, one name per line.
Nothing else should be in the output.

Example1:
Input: 
Trondheim, known as Nidaros in ancient times, was founded by the Viking King Olav Tryggvason in the year 997.
Output:
Trondheim
Nidaros
Viking King Olav Tryggvason
997

Example 2:
Text: The city quickly grew in prominence and became a bustling trading hub in the following centuries.
Output:

Here is the input text:
{input}
```

The `{input}` placeholder is replaced with the value of the `text` field as specified by the indexing statement:

```
input text | generate names_extractor
```

The prompt can be constructed from several fields by concatenating them into one string, e.g.

```
input "Translate from " . language . " to Norwegian: " . text | generate translator
```

Prompt templates can be also specified in `service.xml` with `<promptTemplate>` tag instead of `<promptTemplateFile>`.
If neither `<promptTemplate>` nor `<promptTemplateFile>` are provided, the default prompt is set to `{input}`.
See [LanguageModelTextGenerator](https://github.com/vespa-engine/vespa/blob/master/model-integration/src/main/resources/configdefinitions/language-model-text-generator.def) for other parameters.

## Generating string arrays

Input for `generate` expression can either have type `string` or `array<string>`.
When processing a `string` input, `generate` produces a `string` output.

With `array<string>` input, generate produces `array<string>` output.
For each `string` in the array it makes a separate call to a text generator component and underlying LLM.

For some use cases, e.g. information extraction, it is useful to generate multiple strings from one string input.
It can be achieved by a combining a prompt that asks to produce a list as output with [split indexing expression](), which converts a `string` to `array<string>`.

Example indexing statement:
```
input text | generate names_extractor | split "\n" | for_each { trim } | index | summary
```

Example prompt:
```
Output should be a list of names, one name per line.
Nothing else should be in the output.
```

It might also help to include examples as part of the prompt, e.g.
```
Example 1
Input:  Trondheim, known as Nidaros in ancient times, was founded by the Viking King Olav Tryggvason in the year 997.
Output:
Trondheim
Nidaros
Olav Tryggvason

Example 2:
Input: The city quickly grew in prominence and became a bustling trading hub in the following centuries.
Output:
```

## Support for local LLMs

Vespa supports using [local LLMs](llms-local.md) with `generate`.
In this case, `providerId` in `LanguageModelTextGenerator` component are set to the `id` of the `LocalLLM` component
specified in `services.xml` as follows:
```
<container>
    ...
    <component id="local_llm" class="ai.vespa.llm.clients.LocalLLM">
        <config name="ai.vespa.llm.clients.llm-local-client">
            <model model-id="phi-3.5-mini-q4"/>
        </config>
    </component>
    
    <component id="names_extractor" class="ai.vespa.llm.generation.LanguageModelTextGenerator">
        <config name="ai.vespa.llm.generation.language-model-text-generator">
            <providerId>local_llm</providerId>
            <promptTemplateFile>files/names_extractor_prompt.txt</promptTemplateFile>
        </config>
    </component>
    ...
</container>
```

Local LLMs run in [container nodes](https://docs.vespa.ai/en/jdisc/) and require considerable computational resources 
depending on the model, context size and number of parallel requests.
GPU is often needed to achieve acceptable performance for practical use cases.
Test your application to ensure that the node size fits your local LLM configuration and workload.
See [local LLMs documentation](llms-local.md) and [LLMs in Vespa blog post](https://blog.vespa.ai/vespa-and-llms/#local-llm-inference) 
for details on node sizing and configuration of local LLMs.

The `model` configuration parameter in the `LocalLLM` component can be either set to a known `model-id` for Vespa Cloud, 
a `url` or a `path` to the model inside the application package.
Usually LLM files are too large to be included in the application package, so the `model-id` or `url` attribute are used.
However, for initial testing we recommend using small LLMs, e.g.
[Llama-160M-Chat-v1](https://huggingface.co/afrideva/Llama-160M-Chat-v1-GGUF).
Small LLMs can be part of an application package, avoiding extra time it takes to download larger models during deployment.
In addition, they are fast enough without GPU, reducing time it takes to provision necessary compute resources.
After initial testing, replace it with a larger LLM and add a GPU to your container nodes, e.g.

```xml
<container>
    ...
    <nodes count="1">
        <resources vcpu="4.0" memory="16Gb" architecture="x86_64" storage-type="local" disk="125Gb">
            <gpu count="1" memory="16.0Gb"/>
        </resources>
    </nodes>
    ...
</container>
```

## Custom text generators

Application developers can implement custom Java components to be used with `generate` expression.
This enables arbitrary text processing logic and integrations as part of the indexing pipeline,
as an alternative to [custom document processing components](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing).
Custom components compatible with `generate` implement `com.yahoo.language.process.TextGenerator` interface with `generate` method, e.g.

```java
public class MockTextGenerator implements TextGenerator {
    private final MockTextGeneratorConfig config;

    public MockTextGenerator(MockTextGeneratorConfig config) {
        this.config = config;
    }

    @Override
    public String generate(Prompt prompt, Context context) {
        var stringBuilder = new StringBuilder();

        for (int i = 0; i < config.repetitions(); i++) {
            stringBuilder.append(prompt.asString());

            if (i < config.repetitions() - 1) {
                stringBuilder.append(" ");
            }
        }


        return stringBuilder.toString();
    }
}
```

Configuration of custom components is implemented as described in [Configuring Java components](https://docs.vespa.ai/en/configuring-components.html).
Components are configured in `services.xml`, e.g.:

```xml
<container>
    ...
    <component id="mock_gen" class="ai.vespa.test.MockTextGenerator" bundle="generate-text-feed">
        <config name="ai.vespa.test.mock-text-generator">
            <repetitions>2</repetitions>
        </config>
    </component>
    ...
</container>
```

See the [Generative Feeding sample app]() for complete example of an application with a custom text generator.

## Performance and cost considerations

When used with an LLM, each `generate` statement makes a call to LLM for each document. 
When used with `array<string>` inputs, the number of calls is multiplied by the number of strings in the array.
Many documents and/or large arrays result in many LLM calls, which significantly reduces feeding throughput and increases latency and costs.

With local LLMs, model configuration and use of GPU have a major impact on performance and cost.
See [local LLMs](llms-local.md) for more details.
A separate feeding cluster with GPU nodes that can be scaled independently of other clusters can be a cost-effective solution.

When using remote providers, e.g. OpenAI, consider costs and [rate limits](https://platform.openai.com/docs/guides/rate-limits) for your subscription tier and model.
Costs can be estimated by multiplying the number of documents, number of `generate` statements, approximate number of tokens in prompts and responses, and the cost per token.
