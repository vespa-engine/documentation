---
# Copyright Vespa.ai. All rights reserved.
title: "Generating text with LLMs"
---

Large Language Models (LLMs) enable a wide variety of natural language processing tasks 
such as information extraction, summarization, question answering, translation, sentiment analysis etc.
Vespa makes it easy to use LLMs at scale with [generate]() indexing expression.
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

Both `names_extractor` and `norwegian_translator` specify `openai` as their `providerId`, 
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
Olav Tryggvason

Example 2:
Text: The city quickly grew in prominence and became a bustling trading hub in the following centuries.
Output:

Here is the input text:
{input}
```

The `{input}` placeholder in prompts is replaced by the value of the `text` field as specified by the indexing statement:
```
input text | generate names_extractor
```
Inputs can be constructed from several several fields by concatenating them into one string, e.g.

```
input "Translate from " . language . " to Norwegian: " . text | generate translator
```

Prompts can be specified directly in `service.xml` using `<promptTemplate>` instead of `<promptTemplateFile>` tag.
If neither `<promptTemplate>` nor `<promptTemplateFile>` are specified, the default prompt is set to `{input}`.

## Generating string arrays

Input for `generate` expression can be of type `string` or `array<string>`.
In case of `array<string>`, `generate` will process each `string` in the array independently, 
making a separate call to a text generator component and corresponding LLM.
The output will be of `array<string>` type.

For some use cases, e.g. information extraction, it can be useful to generate multiple strings from one string input.
It can be achieved by a combination of prompting and `split` expression that takes `string` as input 
and produces `array<string>` as output, e.g.

```
input text | generate names_extractor | split "\n"
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
This can take long time depending on the model size.
Therefore we recommended testing deployments with small LLMs first, e.g.:
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

Small models, like the one configured above, are fast enough without GPU.
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

## Custom text generators

Application developers can implement custom components that can be used with `generate` expression.
The component should implement `com.yahoo.language.process.TextGenerator` interface with `generate` method, e.g.

```java
import ai.vespa.llm.completion.Prompt;
import com.yahoo.language.process.TextGenerator;

public class MyTextGenerator implements TextGenerator {
    @Override
    public String generate(Prompt prompt, Context context) {
        var stringBuilder = new StringBuilder();
        stringBuilder.append("My ");
        stringBuilder.append(prompt.asString());
        return stringBuilder.toString();
    }
}
```

This allows integration of arbitrary text processing components. 