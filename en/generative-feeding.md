---
# Copyright Vespa.ai. All rights reserved.
title: "Generative indexing with LLMs"
---

Large Language Models (LLMs) enable a wide variety of natural language processing tasks 
such as information extraction, summarization, question answering, translation, sentiment analysis etc.
Vespa makes it easy to use LLMs at scale with [generate]() indexing expression without writing code.

Consider the following schema:

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
which use an LLM to extract named entities and translation.
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
referencing `OpenAI` client component with `gpt-4o-mini` model.
See [OpenAI client reference]() for other parameters.

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

Inputs can be constructed from several fields by concatenating them into one string, e.g.

```
input "Translate from " . language . " to Norwegian: " . text | generate translator
```

Prompts can be specified directly in `service.xml` using `<promptTemplate>` instead of `<promptTemplateFile>` tag.
If neither `<promptTemplate>` nor `<promptTemplateFile>` are specified, the default prompt is set to `{input}`.
See [LanguageModelTextGenerator reference]() for other parameters.

## Generating string arrays

Input for `generate` expression can either have type `string` or `array<string>`.
When processing a `string` input, `generate` produces a `string` output.

With `array<string>` input, `generate` processes each `string` in the array independently, 
making a separate call to a text generator component and underlying LLM.
The output is `array<string>`.

For some use cases, e.g. information extraction, it can be useful to generate multiple strings from one string input.
It can be achieved by a combination of prompting and `split` expression that takes `string` as input 
and produces `array<string>` as output, e.g.

```
input text | generate names_extractor | split "\n"
```

The prompt in this case, should explicitly ask to make a list with one item per line:

```
Output should be a list of names, one name per line.
Nothing else should be in the output.
```

It also helps to include examples as part of the prompt, e.g.

```
Example1:
Input: 
Trondheim, known as Nidaros in ancient times, was founded by the Viking King Olav Tryggvason in the year 997.
Output:
Trondheim
Nidaros
Olav Tryggvason

Example 2:
Text: The city quickly grew in prominence and became a bustling trading hub in the following centuries.
Output:
```

## Support for local LLMs

Vespa supports using [local LLMs](llms-local.md) with `generate`.
In this case, `providerId` in `LanguageModelTextGenerator` component should be set to the `id` of the `LocalLLM` component
specified in `services.xml`:

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

Local LLMs run in [container nodes]() and require considerable computational resources depending on the model, 
context size and number of parallel requests.
GPU is often needed to achieve acceptable performance in practical use cases.
Test your application thoroughly to ensure that the node size fits your local LLM configuration and workload.
See [local LLMs](llms-local.md) for details on node sizing and configuration of local LLMs.

Model in `LocalLLM` component is usually specified with `model-id` (Vespa Cloud) or `url` (both Vespa Cloud and OSS).
During application deployment, LLM files are downloaded into container nodes. 
This can take a long time depending on the model size.
Therefore we recommended testing deployments with smaller LLMs first, e.g.:
```
<container>
    ...
    <component id="local_llm" class="ai.vespa.llm.clients.LocalLLM">
        <config name="ai.vespa.llm.clients.llm-local-client">
            <model url="https://data.vespa-cloud.com/gguf_models/Llama-160M-Chat-v1.Q6_K.gguf" />
        </config>
    </component>
    ...
</container>
```

Small models, like the one configured above, are fast enough to be used without GPU.
After initial testing, replace the model with a larger one and add a GPU to your container nodes, e.g.

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

Since `generate` is part of the

## Custom text generators

Application developers can implement custom Java components that can be used with `generate` expression.
This allows for arbitrary text processing components and integrations as part of the indexing pipeline,
as an alternative to [custom document processing components](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing).
The component should implement `com.yahoo.language.process.TextGenerator` interface with `generate` method, e.g.

```java
public class MyTextGenerator implements TextGenerator {
    private final MockTextGeneratorConfig config;

    public MyTextGenerator(MyTextGeneratorConfig config) {
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


Configuration for the component is implemented as described [Configuring Java components](https://docs.vespa.ai/en/configuring-components.html).
The component is referenced in `services.xml` as follows:

```
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