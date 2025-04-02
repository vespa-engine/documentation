---
# Copyright Vespa.ai. All rights reserved.
title: "Running LLMs inside your Vespa application"
---

Please refer to [Large Language Models in Vespa](llms-in-vespa.html) for an
introduction to using LLMs in Vespa.

Vespa supports evaluating LLMs within your application, both on CPU and GPU.

{% include note.html content='Note that this is currently a Beta feature so changes can be expected.' %}

Running large language models (LLMs) directly in your Vespa application offers
various advantages, particularly in terms of data security and privacy. By
running LLMs locally, sensitive information remains within the confines of the
application or network, eliminating the risks associated with data transmission
to external services. This is especially important for [RAG use
cases](llms-rag.html) that handle sensitive or proprietary data, such as
healthcare, finance, and legal services, where privacy compliance and data
security are valid concerns.

Moreover, hosting LLMs locally allows applications to select from a wider
range of models that best suit their specific needs, rather than being limited
to the models offered by external providers. This flexibility enables
businesses to optimize performance, cost, and efficiency tailored to their
operational requirements. Additionally, managing LLMs in-house provides control
over model versions, allowing companies to maintain stable and consistent
outputs by choosing when and how to update their models.

Finally, while massively large foundation models dominates the generalist use
case, the smaller, more specialized, models (sometimes called "small language
models") have become much more capable.

For a quick start, check out the [RAG sample
app](https://github.com/vespa-engine/sample-apps/tree/master/retrieval-augmented-generation)
which demonstrates how to set up a local LLM.


### Setting up LLM clients in services.xml

{% include note.html content='This feature is available in Vespa versions >= 8.331' %}

To set up the required inference engine for running your model, you need to
define a `LocalLLM` component in your application's
[services.xml](reference/services.html):

```
<services version="1.0">
  <container id="default" version="1.0">

    ...

    <component id="local" class="ai.vespa.llm.clients.LocalLLM">
      <config name="ai.vespa.llm.clients.llm-local-client">
          <model url="..." />
      </config>
    </component>

    ...

  </container>
</services>
```

This component will ensure that the underlying inference engine is started and
load the model when the container nodes are started. Each container node in the
cluster will load the LLM. Note that you can set up 
[multiple clusters of container nodes](operations-selfhosted/routing.html#multiple-container-clusters).
This can be helpful for instance if you have multiple LLMs that don't fit in the
available GPU memory, or you would like to offload LLM inference to dedicated
nodes for performance reasons.

The [`model`](reference/config-files.html#parameter-types) configuration
parameter can be either set to a known `model-id` for Vespa Cloud, a `url` or a
`path` to the model inside the application package. Usually, however, LLM files
are too large to practically be included in the application package, so the
`url` attribute is used. See [below](#valid-llm-models) for more information on
model types that can be used in Vespa.

There are many other configuration parameters to customize how inference is run,
please see the [configuration](#local-llm-configuration) section for more details.

### Valid LLM models

Under the hood, Vespa uses [llama.cpp](https://github.com/ggerganov/llama.cpp).
Any model file that works with `llama.cpp` can be used in Vespa. This includes the
following base models and finetunes of them:

- LLama 2/3
- Mistral 7B
- Mixtral MoE
- Gemma
- Command R+
- Phi 2/3
- And many more

Please refer to the [supported
models](https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#description)
section of `llama.cpp` for a full list of updated models.

Vespa supports the `GGUF` file format. `GGUF` models can be found on
[HuggingFace](https://huggingface.co/models), by searching for `GGUF`.  Other
LLM formats such safetensors and pytorch.bin models need to be converted GGUF
before use. Please refer to `llama.cpp` for conversion tools.

Quantized models are also supported. Models are typically trained to
[FP16](https://en.wikipedia.org/wiki/Half-precision_floating-point_format)
precision, but `GGUF` files support reduced precision to 8-bit or lower. This
can save space so larger models can fit in less memory. Be aware however, that
inference time can increase when using reduced precision, so be sure to
benchmark your application accordingly, both in token generation performance
but also in terms of output quality.

### Local LLM configuration

LLM model inference has a number of configuration parameters that is set in
`services.xml` and are applied during model loading.  There are also a set of parameters
that can be set during inference which are passed as query parameters. Please refer
below to [inference parameters](#inference-parameters) for more information on those.

The most significant model configuration parameters are:

- `model`: the model file to use. The attributes are either `model-id` which
  specifies a known model in Vespa Cloud, `url` which specifies a URL to a
  model, for instance in HuggingFace, or `path` which specifies a file found in
  the application package.
- `parallelRequests`: the maximum number of parallel requests to handle. This
  is the batch size of concurrent texts to generate.
- `contextSize`: the size of context window. A model is typically trained with
  a given context size, but this can typically be increased if required. This
  setting has a direct impact on memory usage.
- `useGpu`: toggle the use of GPU if available. Default is `true`, which means
  GPU will be used if it is found. See the [GPU section below](#using-gpus) for
  more details.
- `gpuLayers` : number of layers in the model to offload to GPU. This setting
  allows partial evaluation on CPU and GPU, so models larger than available GPU
  memory can be used. Default is to offload all layers to the GPU.
- `threads`: the number of threads to use when using CPU only inference. The
  default is the number of available cores - 2. Do not set this higher than the
  core count, as this will severely impact performance.
- `maxTokens`: the maximum number of tokens that will be generated. Default is
  512.   
- `maxPromptTokens`: the maximum number of tokens in the prompt. If the prompt
  exceeds this number, it will be truncated. 
  Default is -1, which means that the prompt will not be truncated.
- `contextOverflowPolicy`: determines what to do when `contextSize` is too small 
  to fit prompt and completion tokens for all parallel requests. 
  The default is `NONE`, which allows new tokens to overwrite older ones. 
  This may result in lower quality completions and performance issues.
  `DISARD` ignores the request silently, returning without generating any tokens.
  `FAIL` raises and error.
  
Please refer to the [local LLM client configuration
definition](https://github.com/vespa-engine/vespa/blob/master/model-integration/src/main/resources/configdefinitions/llm-local-client.def)
for an updated list of configuration parameters.

Some important points are worth considering here. First is the context window,
given by the `contextSize` parameter, which is the size (in number of tokens)
that the model uses to generate the next token. In general, larger context
windows are required in [RAG applications](llms-rag.html) to hold the context
from the retrieval stage.  Models are trained with a certain context length,
but this context length can typically be increased up to 4x without much loss
in text generation quality.

The size of the context window has a direct impact on memory use. For instance,
a typical 7B model such as Mistral 7B, with a size of 7 billion parameters will
use around 14Gb memory when using FP16 precision, and 7Gb with 8-bit
quantization. Assuming we use a 8-bit quantization:

- A context window of `4096` will use 7.3Gb for the model, 512Mb for the context
  window and 296Mb for the compute buffer, requiring around 8Gb memory in total.
- A context window of `32768` will use 7.3Gb for the model, 4Gb for the context
  window and 2.2Gb for the compute buffer, requiring almost 14Gb memory in total.

So, a single GPU with 16Gb memory can just about hold the 7B model with a
context size of `32768`.  For reference, the Mistral 7B model is trained with
this context size.

Now, when running in context of Vespa, we generally would like to handle multiple
requests in parallel. The number of parallel requests we can handle per container
node is set with the `parallelRequests` parameter. This in effect sets up a number
of **slots** that can be evaluated simultaneously. Each sequence that should
be generated requires a significant amount of memory to keep the context for
each generated token.

The total amount of memory that is set for this task is given by the
`contextSize` parameter. The effective context size for each request is this
size divided by number of parallel requests. So, for a total context size of
`32768` tokens and `10` parallel requests, each request effectively has a
context window of `3276` tokens. To increase the context size per request, the
total context size must be increased, which naturally has significant impact on
memory use. This is most acute on GPU which has a limited available memory.

Memory restrictions thus drive the settings of these two parameters. For
reference, a 16Gb GPU can hold a 7B 8-bit model with a context size of `4096`
for `10` parallel requests by setting the context size to `40960`. If a larger
context window is required, the number of parallel requests must be decreased.
Likewise, the number of parallel requests can be increased by decreasing the
context size. This depends on the requirements of your application.

<!--
Todo: add the concrete equation here for estimating memory usage, as this
required knowing many things such as model size, context size, model embedding
size etc.
-->


### Inference parameters

Please refer to the general discussion in [LLM
parameters](llms-in-vespa.html#llm-parameters) for setting inference
parameters.

Local LLM inference has the following inference parameters that can be sent along
with the query:

- `npredict`: the number of tokens to generate. Overrides the `maxTokens`
  setting in the model configuration.
- `temperature`: the temperature setting of the model, typically between `0.0`
  and `1.0`.
- `repeatpenalty`: the penalty for repeating tokens.
- `topk` and `topp`: the probability of token sampling. Lower values tend to
  produce more coherent and focused text, while higher values introduce more
  diversity and creativity but potentially more errors or incoherence.
- `jsonSchema`: JSON schema to use for structured output. 
  Specifying this parameter also enables structured output.
  See [structured output](llms-in-vespa.html#structured-output) for more details.

The most significant here are `npredict` which will stop the token generation
process after a certain number of tokens has been generated. Some models can
for certain prompts enter a loop where an infinite number of tokens are
generated.  This is clearly not beneficial situation, so this number should be
set to a high enough value, so all tokens for a response can be generated, but
low enough to stop the model from generating tokens infinitely.


## Using GPUs

Using a GPU can significantly speed up token generation and is generally
recommended. The discussion above about memory requirements are especially
acute when running on GPUs due to memory limitations. In Vespa, the default is
to offload the entire model to the GPU if it is available, but by using the
`gpuLayers` parameter one can experiment with offloading parts of the model to
GPU.

```
<services version="1.0">
  <container id="default" version="1.0">

    <!-- Sets up the inference on a mistral 7B model -->
    <component id="local" class="ai.vespa.llm.clients.LocalLLM">
      <config name="ai.vespa.llm.clients.llm-local-client">
          <model url="url/to/mistral-7B-8bit" />
          <parallelRequests>10</parallelRequests>
          <contextSize>40960</contextSize>
          <useGpu>true</useGpu> <!-- default is true -->
          <gpuLayers>100</gpuLayers>
      </config>
    </component>

  </container>
</services>

```

Here, the model itself has 33 layers, and all are offloaded to the GPU. If your
model is too large to fit on the GPU, you can speed up model evaluation by
offloading parts of the model to the GPU.

To set up GPUs on self-hosted, please refer to [Container GPU
setup](https://docs.vespa.ai/en/operations-selfhosted/vespa-gpu-container.html)
for more details.

It is very easy to use GPU acceleration on Vespa Cloud. To enable GPU
inference, you need to [request
GPUs](https://cloud.vespa.ai/en/reference/services.html#gpu) on the container
nodes. For a more practical introduction, please take a look at the [RAG sample
app](https://github.com/vespa-engine/sample-apps/tree/master/retrieval-augmented-generation)
which also demonstrates how to evaluate the LLM on GPUs on Vespa Cloud.



<!--
Todo: Add section about performance considerations
-->
