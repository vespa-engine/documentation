---
# Copyright Vespa.ai. All rights reserved.
title: "Getting help from LLMs"
redirect_from:
- /en/llm-help
---

This page describes some of the ways that you can get help from large language models (LLMs) when developing a Vespa application.

From our experience, providing the right context to the LLM is essential to get good results when asking questions about Vespa.

## Markdown version of documentation pages

Every page of the documentation is available in markdown format, by changing the URL from `.html` to `.html.md`.
There is also a link to the markdown version in the top right corner of each page.

This can for example be used to copy/paste relevant markdown documentation page(s) into your AI tool of choice when working with LLMs on particular topics.

## llms.txt

We provide an [llms.txt](../../llms.txt) file, that can serve as a top level entrypoint for an LLM, which includes both top-level overview, architecture, as well as title of and link to markdown-version of all documentation pages.

See [llmstxt.org](https://llmstxt.org/) for more information about the format.

### Example usage

The [llms.txt](../../llms.txt) file can be downloaded with:

```bash
curl -O https://docs.vespa.ai/llms.txt
```

This file can then be used as an entrypoint when working with LLMs, either through an IDE, CLI or a chat interface.
If the LLM has a tool available that allows it to fetch the referenced URLs, it can fetch the content of the desired pages as needed.

We also provide [llms-full.txt](../llms-full.txt) which contains the _full_ content of all documentation pages in markdown format. 
This file is relatively large (almost 0.5M words as of Oct 2025), so use accordingly.

## MCP Server

We don't provide any official MCP server at this time, but will update this page as soon as we do.
