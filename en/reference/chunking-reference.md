---
# Copyright Vespa.ai. All rights reserved.
title: "Chunking Reference"
---

Reference configuration for *chunkers*: Components that splits text into pieces in
[chunk indexing expressions](indexing-language-reference.html#chunk), as in

```
indexing: input myTextField | chunk fixed-length 500 | index
```

See also the [guide to working with chunks](../working-with-chunks.html).

## Built-in chunkers

Vespa provides these built-in chunkers:

| Chunker id | Arguments | Description |
| --- | --- | --- |
| sentence | - | Splits the text into chunks at sentence boundaries. |
| fixed-length | target chunk length in characters | Splits the text into chunks with roughly equal length. This will prefer to make chunks of similar length, and to split at reasonable locations over matching the target length exactly. |

## Chunker components

Chunkers are [components](../jdisc/container-components.html), so you can also add your own:

```
{% highlight xml %}



            foo



{% endhighlight %}
```

You create a chunker component by implementing the
[com.yahoo.language.process.Chunker](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/process/Chunker.java)
interface, see [these examples](https://github.com/vespa-engine/vespa/tree/master/linguistics/src/main/java/ai/vespa/language/chunker).
