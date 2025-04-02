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

# Setting up document enrichment components
## Defining generated fields

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

Example of a document generated with this schema:
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

## Configuring field generators

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

All field generators must specify `<providerId>` that references a language model client, 
which is either a local LLM, an OpenAI client or a custom component.
See [configuring LLM for document enrichment](#configuring-llm-for-document-enrichment) for details.

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

## Configuring LLMs

Field generators specify `<providerId>` to reference a language model client 
to be used for generation, which is either a local LLM, an OpenAI client or a custom component.

Configuration details for local LLM and OpenAI client are covered in [local LLM](llms-local.html)
and [OpenAI client](llms-openai.html) documentation.
This section focuses on configuration parameters that are important for document enrichment.

Both local LLM and OpenAI client can be configured with different models.
For efficient scaling of document enrichment, it is recommended to select the smallest 
model that delivers acceptable performance for the task at hand.
In general, larger models produce better results but are more expensive and slower.

Document enrichment tasks such as information extraction, summarization, expansion and classification 
are often less complex than the problem-solving capabilities targeted by larger models.
These tasks can be accomplished by smaller, cost-efficient models, 
such as [Microsoft Phi-3.5-mini](https://huggingface.co/microsoft/Phi-3.5-mini-instruct) for a local model 
or [GPT-4o mini](https://platform.openai.com/docs/models/gpt-4o-mini) for OpenAI API.

Here is an example of a OpenAI client configured with GPT-4o mini model:

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

For OpenAI client, model selection influences API cost and latency.

In addition to the model, local LLM client has several other parameters 
that are important for performance of document enrichment.
The following configuration is a good starting point:

```xml
<services version="1.0">
    ...
    <container id="container" version="1.0">
        ...
       <component id="llm" class="ai.vespa.llm.clients.LocalLLM">
            <config name="ai.vespa.llm.clients.llm-local-client">
                <!-- For Vespa Cloud, specify model by model-id to speed-up deployment -->
                <model model-id="phi-3.5-mini-q4"/>

                <!-- For self-hosted Vespa and Vespa Cloud, specify model by URL -->
                <!-- <model url="https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf"/>-->
                
                <!-- Number of tokens a LLM can do inference with.
                This includes prompt and completion tokens for all parallel request.-->
                <contextSize>5000</contextSize>
                
                <!-- Requests are processed in parallel using continuous batching.
                Each request is allocated 5000 / 5 = 1000 context tokens. -->
                <parallelRequests>5</parallelRequests>
                
                <!--Request context size split between prompt and completion tokens: 500 + 500 = 1000 -->
                <maxPromptTokens>500</maxPromptTokens>
                <maxTokens>500</maxTokens>
                
                <!-- A waiting line for requests to start processing. 
                It is reasonable to set it to <= parallelRequests -->
                <maxQueueSize>3</maxQueueSize>
                
                <!-- How long a request can wait until added to the queue, otherwise timeout. 
                On average, Ca. = number of milliseconds it takes to process all parallel requests. -->
                <maxEnqueueWait>60000</maxEnqueueWait>
                
                <!-- How long a request can wait in the queue until starting processing
                In the worst case, ca. = number of milliseconds it takes to process all requests in the queue. -->
                <maxQueueWait>60000</maxQueueWait>
                
                <!-- Context overflow occurs when a request uses more context tokens than allocated in contextSize / parallelRequests. 
                This should not happen if contextSize, parallelRequests, maxPromptTokens, maxTokens are configured correctly.
                In this case, we want the request to fail so we know if some configuration is wrong.-->
                <contextOverflowPolicy>FAIL</contextOverflowPolicy>
            </config>
        </component>
        ...
    </container>
    ...
</services>
```

There are three important aspects of this configuration in addition to the model used.

1. `model`, `contextSize` and `parallelRequests` determine compute resources necessary to run the model.
2. `contextSize`, `parallelRequests`, `maxPromptTokens` and `maxTokens` 
   should be configured to avoid context overflow - a situation when context size 
   is too small to process multiple parallel requests with the given number of prompt and completion tokens.
3. `maxQueueSize`, `maxEnqueueWait` and `maxQueueWait` are related to managing the queue 
   used for storing and feeding parallel requests into the LLM runtime.

[Local LLMs documentation](llms-local.html) explains how to configure 
`model`, `contextSize` and `parallelRequests` with respect to the model and compute resources used.
Memory usage (RAM or GPU VRAM) is especially important to considered when configuring these parameters. 

To avoid context overflow, set `contextSize`, `parallelRequests`, `maxPromptTokens` and `maxTokens` 
parameters so that `contextSize / parallelRequests >= maxPromptTokens + maxTokens`.
Also consider that larger `contextSize` takes longer to process.

Finally, the queue related parameters are used to balance latency with throughput.
Values for these parameters heavily depends on underlying compute resources.
Local LLM configuration presented above is optimized for CPU nodes with 16 cores and 32GB RAM 
as well as GPU nodes with NVIDIA T4 GPUs 16GB VRAM.

## Configuring compute resources

Configuration of compute resources applies only to local LLMs since OpenAI client uses remote APIs.
In practice, GPU is highly recommended for running local LLMs, providing order of magnitude speedup compared to CPU.

For Vespa Cloud a reasonable starting configuration is as follows:
```xml
<container version="1.0">
    ...
    <container id="container" version="1.0">
        ...
        <nodes count="1" deploy:environment="dev">
            <resources vcpu="8.0" memory="32Gb" architecture="x86_64" storage-type="local" disk="225Gb" >
                <gpu count="1" memory="16.0Gb" type="T4"/>
            </resources>
        </nodes>
        ...
    </container>
    ...
</services>
```

This will provision a single node with NVIDIA T4 GPUs 16GB VRAM.
Local model performance scales linearly with the number of nodes, e.g. 
8 GPU nodes * 1.5 gen/sec per node = 12 docs/sec.

## Configuring feeding

Generated fields introduce considerable latency during feeding.
High number of parallel requests can lead to timeouts.
To avoid this, it is recommended to reduce number of connections during feeding.
A reasonable starting point is to use 1 connection per CPU node or 3 connections per GPU node.
Example for one GPU node:

```sh
vespa feed data/feed_100.json --conections 3
```

# Structured output

# Custom field generators

Application developers can implement custom Java components to be used with `generate` expression.
This enables arbitrary text processing logic and integrations as part of the indexing pipeline,
as an alternative to [custom document processing components](https://github.com/vespa-engine/sample-apps/tree/master/examples/document-processing).
Custom components compatible with `generate` implement `com.yahoo.language.process.FieldGenerator` interface with `generate` method, e.g.

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

