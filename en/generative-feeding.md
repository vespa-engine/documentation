---
# Copyright Vespa.ai. All rights reserved.
title: "Generating text with LLMs"
---

Large Language Models (LLMs) enable a wide variety of text processing tasks without coding.
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
    
    
    field text_spanish type string {
        indexing: input text | generate spanish_translator | index | summary
        index: enable-bm25
    }
}
```

This schema includes two synthetic fields, `names` and `text_spanish`, generated from `text` field during feeding.
Generators `names_extractor` and `spanish_translator` are ids for text generator components,
which use an LLM to extract named entities and translate text to spanish.
They are defined in `services.xml` as follows:

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

    <component id="spanish_translator" class="ai.vespa.llm.generation.LanguageModelTextGenerator">
        <config name="ai.vespa.llm.generation.language-model-text-generator">
            <providerId>openai</providerId>
            <promptTemplateFile>files/spanish_translator_prompt.txt</promptTemplateFile>
        </config>
    </component>
    ...
</container>
```

Both `names_extractor` and `spanish_translator` specify `openai` as their `providerId`, 
referencing OpenAI client component configured to use `gpt-4o-mini` model.
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

Prompts can be specified directly in `service.xml` using `<promptTemplate>` instead of `<promptTemplateFile>`.
If neither `<promptTemplate>` nor `<promptTemplateFile>` are specified, the default prompt will be set to `{input}`.

## Dynamic prompts

Prompts can constructed prompts from several document fields, e.g.

```
input "Translate from " . lang . " to Norwegian: " . text | generate translator | split "\n" | index | summary
```

In this example `lang` is a field specifying the original language for the `text` filed.




## Generating array of strings



## Support for local LLMs

Vespa supports [local LLMs](llms-local.md) with `generate`.
In this case, `providerId` in `LanguageModelTextGenerator` component is set to the `id` of the `LocalLLM` component
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

Local LLMs run in [container nodes]() and require considerable computational resources depending on the model, 
context size and number of parallel requests.
GPU is often needed to achieve acceptable performance in practical use cases.
Test your application thoroughly to ensure that node size fits your local LLM configuration and workload.
See [local LLMs](llms-local.md) for details on node sizing and configuration of local LLMs.

Model in `LocalLLM` component is usually specified with `model-id` (Vespa Cloud only) or `url` (both Cloud and OSS).
During application deployment, LLM files are downloaded into container nodes, 
which can take long time depending on the model size.
Therefore we recommended testing deployments with tiny LLMs first, e.g.:
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

Tiny models, like the one configure above, don't need a GPU.
Later when the rest of the application is tests, replace the model with a larger one and add a GPU to your container nodes.

## Custom text generators





Prompts can be also specified directly in `service.xml` by using `<promptTemplate>` tag instead of `<promptTemplateFile>`. 
If neither `<promptTemplate>` nor `<promptTemplateFile>` are specified, the default prompt is `{input}`.
