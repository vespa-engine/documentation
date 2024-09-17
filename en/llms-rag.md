---
# Copyright Vespa.ai. All rights reserved.
title: "Retrieval-augmented generation (RAG) in Vespa"
redirect_from:
- /documentation/llms-rag.html
---

Please refer to [Large Language Models in Vespa](llms-in-vespa.html) for an
introduction to using LLMs in Vespa.

Retrieval-Augmented Generation (RAG) is a technique that merges retrieval
systems with generative models to enhance language model outputs. It works by
first using a retrieval system like Vespa to fetch relevant documents based on
an input query, and then a generative model, like an LLM, to generate more
contextually relevant responses. This method allows language models to access
up-to-date or specific domain knowledge beyond their training, improving
performance in tasks such as question answering and dynamic content creation.

In Vespa, the `RAGSearcher` first performs the query as specified by the user,
creates a prompt based on the results, and queries the language model to
generate a response.

For a quick start, check out the [RAG sample
app](https://github.com/vespa-engine/sample-apps/tree/master/retrieval-augmented-generation)
which demonstrates using either an external LLM service or a local LLM.


### Setting up the RAGSearcher

In `services.xml`, specify your LLM connection and the `RAGSearcher`:

```
<services version="1.0">
  <container id="default" version="1.0">

    ...

    <component id="openai" class="ai.vespa.llm.clients.OpenAI">
      <!-- Configure as required -->
    </component>

    <search>
      <chain id="rag" inherits="vespa">
        <searcher id="ai.vespa.search.llm.RAGSearcher">
          <config name="ai.vespa.search.llm.llm-searcher">
            <providerId>openai</providerId>
          </config>
        </searcher>
      </chain>
    </search>

    ...

  </container>
</services>
```

As mentioned in [LLMs in Vespa](llms-in-vespa.html), you can call this chain
using the Vespa CLI:

```
$ vespa query \
    --header="X-LLM-API-KEY:..." \
    query="what was the manhattan project?" \
    searchChain=rag \
    format=sse
```

However, notice here the use of the `query` query parameter. In [LLMs in
Vespa](llms-in-vespa.html), we used a `prompt` parameter to set up the prompt
to send to the LLM. You can also do that in the `RAGSearcher`, however this means
that no actual query is run in Vespa. For Vespa to run a search, you need to
specify a `yql` or `query` parameter. By using `query` here, this text is
used as both query text for the document retrieval, and in the prompt sent to
the LLM, as we will see below.

Indeed, with the `RAGSearcher` you can use any type of [search in
Vespa](query-api.html), including [text search based on
BM25](tutorials/text-search.html) and advanced [approximate vector
search](approximate-nn-hnsw.html). This makes the retrieval part of
RAG very flexible.

### Controlling the prompt

Based on the query, Vespa will retrieve a set of documents. The `RAGSearcher`
will create a context from these documents looking like this:

```
field1: ...
field2: ...
field3: ...

field1: ...
field2: ...
field3: ...

...

```

Here, `field1` and so on are the actual fields as returned from the search. For
instance, the [text search tutorial](tutorials/text-search.html) defines a
document schema consisting of fields: `id`, `title`, `url`, and `body`. If you
only want to include the `title` and `body` fields for use in the context, you
can issue a query like this:

```
$ vespa query \
    --header="X-LLM-API-KEY:..." \
    yql="select title,body from msmarco where userQuery()" \
    query="what was the manhattan project?" \
    searchChain=rag \
    format=sse
```

The actual prompt that will be sent to the LLM will, by default, look like this:

```
{context}

{@prompt or @query}
```

where `{context}` is as given above, and `@prompt` is replaced with the `prompt`
query parameter if given, and `@query` is replaced with the user query if given.
This means you can customize the actual prompt by passing in a `prompt`
parameter, and thus distinguish between what is searched for in Vespa, and what
is asked for from the LLM.

For instance:

```
$ vespa query \
    --header="X-LLM-API-KEY:..." \
    yql="select title,body from msmarco where userQuery()" \
    query="what was the manhattan project?" \
    prompt="{context} @query Be as concise as possible." \
    searchChain=rag \
    format=sse
```

will results in a prompt like this:

```
title: <title of first document>
body: <body of first document>

title: <title of second document>
body: <body of second document>

<rest of documents>

what was the manhattan project? Be as concise as possible.
```

Note that if your `prompt` does not contain `{context}`, the context will
automatically be prepended to your prompt. However, if `@query` is not
found in the prompt, it will not automatically be added to the prompt.

Please be advised that all documents as returned by Vespa will be used in the
context. Most LLMs have some form of limit for how large the prompt can be. LLM
services also typically have a cost per query based on number of tokens both in
input and output. To reduce context size it is important to control the number
of results by using the `hits` [query
parameter](reference/query-api-reference.html#hits). Also, using the query above
limit the fields to only what is strictly required.

To debug the prompt, i.e. what is actually sent to the LLM, you can use the
`traceLevel` query parameter, and set that to a value larger than `0`:

```
$ vespa query \
    --header="X-LLM-API-KEY:..." \
    query="what was the manhattan project?" \
    searchChain=rag \
    format=sse \
    traceLevel=1

event: prompt
data: {"prompt":"<the actual prompt sent to the LLM>"}

event: token
data: {"token":"<first token of response>"}

...
```
