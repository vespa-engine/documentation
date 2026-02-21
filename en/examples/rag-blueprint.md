---
# Copyright Vespa.ai. All rights reserved.
title: "The RAG Blueprint"
---

Vespa is the [platform of choice](https://blog.vespa.ai/perplexity-builds-ai-search-at-scale-on-vespa-ai/)
for large scale RAG applications like Perplexity.
It gives you all the features you need but putting them all together can be a challenge.

This open source sample applications contains all the elements you need to create a RAG application that

* delivers state-of-the-art quality, and
* scales to any amount of data, query load, and complexity.

This README provides the steps to create and run your own application based on the blueprint.
Refer to the [RAG Blueprint tutorial](https://docs.vespa.ai/en/learn/tutorials/rag-blueprint.html) for more in-depth explanations,
or try out the [Python notebook](https://vespa-engine.github.io/pyvespa/examples/rag-blueprint-vespa-cloud.html).



{% include setup.html appname='rag-blueprint' %}



## Test the application

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec" data-test-assert-contains="Success">
$ vespa deploy --wait 900 ./app
</pre>
</div>

Feed some documents, this will also chunk and embed so it takes about 3 minutes:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa feed dataset/docs.jsonl
</pre>
</div>

Now you can issue queries:

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa query 'query=yc b2b sales'
</pre>
</div>

<pre data-test="after" style="display:none">
$ vespa destroy --force
</pre>

> [!TIP]
> Add "-v" to see the HTTP request this becomes.

Congratulations! You have now created a RAG application that can scale to billions of documents and thousands
of queries per second, while delivering state-of-the-art quality.

## Explore more

What do you want to do next?

- To learn what this application can do, look at the files in your app/ dir.
- [Run your application locally using Docker](deploy-locally.md)
- [Using query profiles to define behavior for different use cases](query-profiles.md)
- [Evaluate and improve relevance of the data returned](relevance.md)
- [Do LLM generation inside the application](generation.md)

