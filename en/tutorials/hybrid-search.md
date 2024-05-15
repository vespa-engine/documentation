---
# Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "Hybrid Text Search Tutorial"
redirect_from:
- /documentation/tutorials/hybrid-search.html
---

This tutorial will guide you through setting up a hybrid text search application. 


The main goal is to set up a text search app that combines simple text scoring features
such as [BM25](../reference/bm25.html) [^1] with vector search using text-embedding models.


{% include pre-req.html memory="4 GB" extra-reqs='
<li>Python3</li>
<li><code>curl</code></li>' %}

## Installing vespa-cli 

This tutorial uses [Vespa-CLI](../vespa-cli.html) to deploy, feed and query Vespa. 

<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ pip3 install vespacli ir_datasets
</pre>
</div>


<div class="pre-parent">
  <button class="d-icon d-duplicate pre-copy-button" onclick="copyPreContent(this)"></button>
<pre data-test="exec">
$ vespa clone text-search text-search && cd text-search
</pre>
</div>

