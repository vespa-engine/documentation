---
# Copyright Vespa.ai. All rights reserved.
title: "Getting help from LLMs"
---

This page describes some of the ways that you can get help from large language models (LLMs) when developing a Vespa application.
From our experience, providing the right context to the LLM is essential to get good results when asking questions about Vespa.

## Markdown version of documentation pages

Every page of the documentation is available in markdown format, by changing the URL from `.html` to `.html.md`.
There is also a link to the markdown version in the top right corner of each page.

This allows you to easily copy/paste relevant documentation pages when working with LLMs on particular topics.

## llms.txt

We provide an [llms.txt](../llms.txt) file, that can serve as a top level entrypoint for an LLM, which includes both top-level overview, architecture, as well as title of and link to markdown-version of all documentation pages.

See [llmstxt.org](https://llmstxt.org/) for more information about the format.

### Example usage

The llms.txt file can be downloaded with:

```bash
curl -O https://docs.vespa.ai/llms.txt
```

This file can then be used as an entrypoint when working with LLMs, either through an IDE, CLI or a chat interface.
If the LLM has a tool available that allows it to fetch the referenced URLs, it can fetch the content of the desired pages as needed.

We also provide [llms-full.txt](../llms-full.txt) which contains the full content of all documentation pages in markdown format, but this file is relatively large (almost 0.5M words as of Sept 2025), and must be used accordingly.

## Search Vespa documentation tool

For humans, we have [search.vespa.ai](https://search.vespa.ai). LLMs can also use this through the API.

TODO: https://api.search.vespa.ai/search/?query=what%20is%20Vespa&filters=%2Bnamespace%3Aopen-p%20%2Bnamespace%3Acloud-p%20%2Bnamespace%3Avespaapps-p%20%2Bnamespace%3Ablog-p%20%2Bnamespace%3Apyvespa-p%20%2Bnamespace%3Acode-p&queryProfile=llmsearch&hits=1