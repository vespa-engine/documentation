---
# Copyright Vespa.ai. All rights reserved.
title: "Document enrichment with LLMs"
---

Document enrichment enables automatic generation of document field values using large language models (LLMS) or custom code during feeding.
It can be used to transform raw text into a more structured representation or expand it with additional contextual information.
Examples of enrichment tasks include:

- Extraction of named entities (e.g., names of people, organizations, locations, and products) for fuzzy matching and customized ranking
- Categorization and tagging (e.g., sentiment and topic analysis) for filtering and faceting
- Generation of relevant keywords, queries, and questions to improve search recall and search suggestions
- Anonymization to remove personally identifiable information (PII) and reduction of bias in search results
- Translation of content for multilingual search

These tasks are defined through prompts, which can be customized for a particular application.
Generated fields are indexed and stored as normal fields and can be used for searching without additional latency associated with LLM inference.

[Vespa already offers integrations with LLMs](https://docs.vespa.ai/en/llms-in-vespa.html),
including support for local models that run within Vespa and a client for external OpenAI-compatible APIs.

## Setting up document enrichment components

### Defining generated fields

Enrichments are defined in a schema using a [`generate` indexing expression](reference).
For example the following schema defines two [synthetic fields](https://docs.vespa.ai/en/operations/reindexing.html) with `generate`:

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
    
    # Generate relevant questions to increase recall and search suggestions
    field questions type array<string> {
        indexing: input text | generate questions_generator | summary | index
        index: enable-bm25
    }
    
    # Extract named entities for fuzzy matching with ngrams
    field names type array<string> {
        indexing: input text | generate names_extractor | summary | index
        match {
            gram
            gram-size: 3
        }
    }
}
```

Indexing statement `input text | generate questions_generator | summary | index` is interpreted as follows:
1. Take document field named `text` as an input
2. Pass the input to a field generator with id `questions_generator`
3. Store the output of the generator as summary
4. Index the output of the generator for lexical search

### Configuring field generators

A schema can contain multiple generated fields that use one or multiple field generators.
All field generators should be configured in `services.xml`, e.g.

```xml
<services version="1.0">
    ...
    <container id="container" version="1.0">
        ...
        <component id="questions_generator" class="ai.vespa.llm.generation.LanguageModelFieldGenerator">
            <config name="ai.vespa.llm.generation.language-model-field-generator">
                <providerId>local_llm</providerId>
                <promptTemplate>Generate 3 questions relevant for this text: {input}</promptTemplate>
            </config>
        </component>
        
        <component id="names_extractor" class="ai.vespa.llm.generation.LanguageModelFieldGenerator">
            <config name="ai.vespa.llm.generation.language-model-field-generator">
                <providerId>openai</providerId>
                <promptTemplateFile>files/names_extractor.txt</promptTemplateFile>
            </config>
        </component>
        ...
    </container>
    ...
</services>
```

All field generators must specify `<providerId>` that references a language model component, 
which is either a local LLM, an OpenAI client or a custom component.
Language model components specify parameters such as a model and context size.
Instructions for configuring these components can be found on [LLMs in Vespa documentation page](https://docs.vespa.ai/en/llms-in-vespa.html).

In addition to the language model, field generators require a prompt.
The prompt is constructed from three parts:

1. Prompt template, which is either specified inline inside `<promptTemplate>` or in a separate file with the path in `<promptTemplateFile>` tags.
2. Input from the indexing statement, e.g. `input text`.
3. Output type which is inferred automatically from the type of the field being generated.

If neither `<promptTemplate>` nor `<promptTemplateFile>` are provided, the default prompt is set to the input part.
When both are provided, `<promptTemplateFile>` has precedence.

A prompt template must contain `{input}` placeholder, which will be replaced with the input value.
It is possible to combine several fields into one input by concatenating them into a single string, e.g.

```
input "title: " . title . " text: " . text | generate names_extractor | summary | index
```

A prompt template might also contain a `{jsonSchema}` placeholder which will be replaced with a JSON schema based on the type of the field being generated.
For example, JSON schema generated for `field questions type array<string>` in document `passage` is as follows:

```json
{
    "type": "object",
    "properties": {
        "passage.questions": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "passage.questions"
    ],
    "additionalProperties": false
}
```

Including a JSON schema in a prompt can help an LLM to generate an output in a specific format.
Note that by default field generators leverage [structured output with constrained decoding](https://huggingface.co/learn/cookbook/structured_generation#-constrained-decoding)
to force an LLM to produce outputs that conform to the schema.
Therefore, including `{jsonSchema}` in the prompt is not required for most use cases.

Structured output can be disabled by specifying `<responseFormatType>TEXT</responseFormatType>`.
In this case, the generated field must have a `string` type.
This is useful for very small models (less than a billion parameters) that struggle to generate structured output.
For most use cases, it is recommended to use structured output even for `string` fields.
For more information on structured output see the [structured output section](#structured-output).

The last parameter in the field generator configuration is `<invalidResponseFormatPolicy>`, 
which specifies what to do when the output from the underlying language model can't be converted to the generated field type.
This shouldn't happen when using structured output, but it can happen with `TEXT` response format.
The default value is `DISCARD`, which leaves the field empty, sets it to `null`.
Other values `WARN` and `FAIL` log a warning and throw an exception respectively.

Overview of all the field generator parameters is available in the [configuration definition file](https://github.com/vespa-engine/vespa/blob/master/model-integration/src/main/resources/configdefinitions/language-model-field-generator.def).

### Configuring local LLM

Local LLM configuration is covered in LLMs(https://docs.vespa.ai/en/llms-in-vespa.html),











Generators specify `providerId` referring to a local LLM or OpenAI client, which are also defined in `services.xml`.
Example of a local LLM component: 

```xml
<services version="1.0">
    ...
    <container id="container" version="1.0">
        ...
        <!-- Local language model -->
        <component id="llm" class="ai.vespa.llm.clients.LocalLLM">
            <config name="ai.vespa.llm.clients.llm-local-client">
                <!-- Specify LLM by id for Vespa Cloud -->
                <model model-id="phi-3.5-mini-q4"/>-->
                <!-- Alternative is to use url, which also works outside Vespa Cloud -->
                <!-- <model url="https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf"/>-->
                <!-- Number of tokens an LLM can attend in each inference for all parallel request. -->
                <contextSize>5000</contextSize>
                <!-- Requests are processed in parallel using continuous batching.
                Each request will use 5000 / 5 = 1000 context tokens. -->
                <parallelRequests>5</parallelRequests>
                <!--Request context size split between prompt and completion tokens: 500 + 500 = 1000 -->
                <maxPromptTokens>500</maxPromptTokens>
                <maxTokens>500</maxTokens>
                <!-- Documents will be set in a queue to wait until one of the parallel requests is done process. -->
                <maxQueueSize>3</maxQueueSize>
                <!-- Both enqueue and queue wait has to be set proportional to max queues size 
                because the last request will need to wait for all previous ones before starting the processing. -->
                <maxEnqueueWait>100000</maxEnqueueWait>
                <maxQueueWait>100000</maxQueueWait>
                <!-- Context overflow leads to hallucinations, better to skip generation than generating nonsense. -->
                <contextOverflowPolicy>DISCARD</contextOverflowPolicy>
            </config>
        </component>
        ...
    </container>
    ...
</services>
```
See [local LLM parameters documentation](https://docs.vespa.ai/en/llms-in-vespa.html#llm-parameters) for configuration details.
Example of an OpenAI client component.
 
```xml
<container version="1.0">
    ...
    <container id="container" version="1.0">
        ...
        <!-- OpenAI client -->
        <component id="openai" class="ai.vespa.llm.clients.OpenAI">
            <config name = "ai.vespa.llm.clients.llm-client">
                <apiKeySecretName>openai-key</apiKeySecretName>
                <model>gpt-4o-mini</model>
            </config>
        </component>
        ...
    </container>
    ...
</services>
```

Note that OpenAI client specifies API key secret from a 
[secret store](https://cloud.vespa.ai/en/security/secret-store.html) in Vespa Cloud.
See [OpenAI client documentation]() for how to provide secrets outside Vespa Cloud.

Prompts for an LLM are constructed by combining an input of an indexing statement with a prompt template of a generator.
For example, consider the following indexing statement for the `questions` field:

```
input text | generate questions_generator | summary | index
```

In this case, value of the document field `text` will replace the `{input}` placeholder in the prompt template of `questions_generator`:

```xml
<promptTemplate>Generate 3 questions relevant for this text: {input}</promptTemplate>
```

Generated fields `questions` and `names` will be indexed and stored as part of the document and can be used for matching and ranking, e.g.
```
rank-profile with_question_and_names {
    first-phase {
        expression: 0.4 * nativeRank(text) + 0.1 * nativeRank(questions) + 0.5 * nativeRank(names)
    }
}
```

Example of a retrieved document:

```json
{
    "id": "71",
    "text": "Barley (Hordeum vulgare L.), a member of the grass family, is a  major cereal grain. It was one of the first cultivated grains and is now grown widely. Barley grain is a staple in Tibetan cuisine and was eaten widely by peasants in Medieval Europe. Barley has also been used as animal fodder, as a source of fermentable material for beer and certain distilled beverages, and as a component of various health foods.",
    "questions": [
      "What are the major uses of Barley (Hordeum vulgare L.) in different cultures and regions throughout history?",
      "How has the cultivation and consumption of Barley (Hordeum vulgare L.) evolved over time, from its initial cultivation to its present-day uses?",
      "What role has Barley (Hordeum vulgare L.) played in traditional Tibetan cuisine and Medieval European peasant diets?"
    ],
    "names": [
      "Barley",
      "Hordeum vulgare L.",
      "Tibetan",
      "Medieval Europe"
    ]
}
```

A complete application that this example is based on is is available in our [sample-apps repository]().
You can clone and run it in Vespa Cloud or locally.

# 

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

In most cases, `generate` with LLM will be the bottleneck in the feeding pipeline, 
significantly reducing feeding throughput, increasing latency and cost.
Each `generate` statement in a schema will make one (`string` input) or several (`array<string>` input) calls to LLM for each document.
This can lead to a very large number of calls, so it is important to be aware of the performance and cost implications.

With local LLMs, model configuration and use of GPU have a major impact on performance and cost.
See [local LLMs](llms-local.md) for more details.

When using remote providers, e.g. OpenAI, consider [costs](https://openai.com/api/pricing/) 
and [rate limits](https://platform.openai.com/docs/guides/rate-limits) for your subscription tier and model.