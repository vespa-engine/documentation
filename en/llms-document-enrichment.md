---
# Copyright Vespa.ai. All rights reserved.
title: "Document enrichment with LLMs"
---

Document enrichment enables automatic generation of document field values using large language models (LLMs) or custom code during feeding.
It can be used to transform raw text into a more structured representation or expand it with additional contextual information.
Examples of enrichment tasks include:

- Extraction of named entities (e.g., names of people, organizations, locations, and products) for fuzzy matching and customized ranking
- Categorization and tagging (e.g., sentiment and topic analysis) for filtering and faceting
- Generation of relevant keywords, queries, and questions to improve search recall and search suggestions
- Anonymization to remove personally identifiable information (PII) and reduction of bias in search results
- Translation of content for multilingual search
- LLM chunking

These tasks are defined through prompts, which can be customized for a particular application.
Generated fields are indexed and stored as normal fields and can be used for searching without additional latency associated with LLM inference.

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

### Configuring field generators

A schema can contain multiple generated fields that use one or multiple field generators.
All used field generators should be configured in `services.xml`, e.g.

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

In addition to the language model, field generators require a prompt.
Prompts are constructed from three parts:

1. Prompt template, specified either inline inside `<promptTemplate>` or in a file within application package with the path in `<promptTemplateFile>`.
2. Input from the indexing statement, e.g. `input text` where `text` is a document field name.
3. Output type of the field being generated.

If neither `<promptTemplate>` nor `<promptTemplateFile>` are provided, the default prompt is set to the input part.
When both are provided, `<promptTemplateFile>` has precedence.

A prompt template must contain `{input}` placeholder, which will be replaced with the input value.
It is possible to combine several fields into one input by concatenating them into a single string, e.g.

```
input "title: " . title . " text: " . text | generate names_extractor | summary | index
```

A prompt template might also contain a `{jsonSchema}` placeholder which will be replaced with a JSON 
schema based on the type of the field being generated, see the [structured output section](#structured-output) for details.
Including a JSON schema in your prompt can help language models generate output in a specific format. 
However, it's important to understand that field generators already provide the JSON schema 
as a separate inference parameter to the underlying language model client.
Both local LLM and OpenAI client utilize [structured output](#structured-output) functionality, 
which forces LLMs to produce outputs that conform to the schema.
For this reason, explicitly including `{jsonSchema}` in your prompt template is unnecessary for most use cases.

Structured output can be disabled by specifying `<responseFormatType>TEXT</responseFormatType>`.
In this case, the generated field must have a `string` type.
This is useful for very small models (less than a billion parameters) that struggle to generate structured output.
For most use cases, it is recommended to use structured output even for `string` fields.

The last parameter in the field generator configuration is `<invalidResponseFormatPolicy>`, 
which specifies what to do when the output from the underlying language model can't be converted to the generated field type.
This shouldn't happen when using structured output, but it can happen with `TEXT` response format.
The default value is `DISCARD`, which leaves the field empty, sets it to `null`.
Other values `WARN` and `FAIL` log a warning and throw an exception respectively.

Overview of all the field generator parameters is available in the [configuration definition file](https://github.com/vespa-engine/vespa/blob/master/model-integration/src/main/resources/configdefinitions/language-model-field-generator.def).

## Configuring language models

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
   used for storing and feeding parallel requests into LLM runtime (llama.cpp).

[Local LLMs documentation](llms-local.html) explains how to configure 
`model`, `contextSize` and `parallelRequests` with respect to the model and compute resources used.
Memory usage (RAM or GPU VRAM) is especially important to considered when configuring these parameters. 

To avoid context overflow, configure `contextSize`, `parallelRequests`, `maxPromptTokens` and `maxTokens` 
parameters so that `contextSize / parallelRequests >= maxPromptTokens + maxTokens`.
Also consider that larger `contextSize` takes longer to process.

The queue related parameters are used to balance latency with throughput.
Values for these parameters heavily depends on underlying compute resources.
Local LLM configuration presented above is optimized for CPU nodes with 16 cores and 32GB RAM 
as well as GPU nodes with NVIDIA T4 GPUs 16GB VRAM.

### Configuring compute resources

Provisioned compute resources only affect local LLM performance, 
as OpenAI client merely calls a remote API that leverages the service provider's infrastructure.
In practice, GPU is highly recommended for running local LLMs.
It provided order of magnitude speedup compared to CPU.
For Vespa Cloud, a reasonable starting configuration is as follows:

```xml
<container version="1.0">
    ...
    <container id="container" version="1.0">
        ...
        <nodes count="1">
            <resources vcpu="8.0" memory="32Gb" architecture="x86_64" storage-type="local" disk="225Gb" >
                <gpu count="1" memory="16.0Gb" type="T4"/>
            </resources>
        </nodes>
        ...
    </container>
    ...
</services>
```

This configuration provisions a container cluster with a single node containing NVIDIA T4 GPUs 16GB VRAM.
Local model throughput scales linearly with the number of nodes in the container cluster used for feeding.
For example with 8 GPU nodes (`<nodes count="8">`) and throughput per node 1.5 generations/second, 
combined throughput will be close to 12 generations/second.

### Feeding configuration

Generated fields introduce considerable latency during feeding.
Large number of high-latency parallel requests might lead to timeouts in the document processing pipeline.
To avoid this, it is recommended to reduce the number of connections during feeding.
A reasonable starting point is to use three connections per GPU node and one connection per CPU node.
Example for one GPU node:

```sh
vespa feed data.json --conections 3
```

## Structured output

Document enrichment generates field values based on the data types defined in a document schema. 
Both local LLMs and the OpenAI client support structured output, forcing LLMs to produce JSON that conforms to a specified schema. 
This JSON schema is automatically constructed by a field generator according to the data type of the field being created.
For example, a JSON schema for `field questions type array<string>` in document `passage` will be as follows:

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

Constructed schemas for different data types correspond to the 
[document JSON format](https://docs.vespa.ai/en/reference/document-json-format.html#) used for feeding.
The following field types are supported:
- string
- bool
- int
- long
- byte
- float
- float16
- double
- array of types mentioned above 

## Custom field generator

As usual with Vespa, existing functionality can be extended by developing [custom application components](https://docs.vespa.ai/en/developer-guide.html).
A custom generator component can be used to implement application-specific logic to construct prompts, transform and validate LLM inputs and output,
combine outputs of several LLMs or use other sources such a knowledge graph.

A custom field generator compatible with `generate` should implement `com.yahoo.language.process.FieldGenerator` 
interface with `generate` method that returns a field value. 
Here is toy example of a custom field generator:

```java
package ai.vespa.test;

import ai.vespa.llm.completion.Prompt;
import com.yahoo.document.datatypes.FieldValue;
import com.yahoo.document.datatypes.StringFieldValue;
import com.yahoo.language.process.FieldGenerator;

public class MockFieldGenerator implements FieldGenerator {
   private final MockFieldGeneratorConfig config;

   public MockFieldGenerator(MockFieldGeneratorConfig config) {
      this.config = config;
   }

   @Override
   public FieldValue generate(Prompt prompt, Context context) {
      var stringBuilder = new StringBuilder();

      for (int i = 0; i < config.repetitions(); i++) {
         stringBuilder.append(prompt.asString());

         if (i < config.repetitions() - 1) {
            stringBuilder.append(" ");
         }
      }


      return new StringFieldValue(stringBuilder.toString());
   }
}
```

The config definition for this component looks as follows:
```
namespace=ai.vespa.test
package=ai.vespa.test

repetitions int default=1
```

To be used with `generate` indexing expression this component should be added to `services.xml`:
```xml
<container>
   ...
   <component id="mock_generator" class="ai.vespa.test.MockFieldGenerator" bundle="mock_field_generator_app">
      <config name="ai.vespa.test.mock-field-generator">
         <repetitions>2</repetitions>
      </config>
   </component>
   ...
</container>
```

The last step is to use it in a document schema, e.g.:
```
schema passage {
    document passage {
        field text type string {
            indexing: summary | index
            index: enable-bm25
        }
    }
    
    field mock_text type string {
        indexing: input text | generate mock_generator | summary
    }
}
```
