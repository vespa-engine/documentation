---
# Copyright Vespa.ai. All rights reserved.
title: "Documentation Conventions"
---

This documentation is for users of Vespa, or potential users -
being application owners / PMs, engineers or operators.
The documentation covers conceptual overviews of the product,
including background theory and explanations of why the product has developed along the lines it has.
This is followed by deeper investigation of the features that developers will use first.

For Vespa plugin development, the documentation is aimed at experienced Java developers.
It is not aimed at beginners and does not cover general programming techniques
or the basics of programming languages.

For parts of the documentation the reader should be familiar with Unix-like platforms,
as Vespa is available on Linux.
The exposure of Vespa's APIs is such that the user does not need in-depth knowledge
about how Vespa's inner workings in order to start using it.
The reader does not have to be an expert by any means,
but the text and samples become easier to follow
as Vespa's principles are more properly understood.

If you find errors, spelling mistakes, faulty pieces of code
or want to improve the documentation,
please submit a pull request or [create an issue](https://github.com/vespa-engine/vespa/issues).
*Italic* is used for:
* Pathnames, filenames, program names, hostnames, and URLs
* New terms where they are defined

`Constant Width` is used for:
* Programming language elements, code examples, keywords, functions,
  classes, interfaces, methods, etc.
* Commands and command-line output

Commands meant to be run on the command line are shown like this,
prepended by a $ for the prompt:

```
$ export PATH=$VESPA_HOME/bin:$PATH   # how to highlight text in <pre>
```

Notes and other Important pieces of information are shown like:

{% include note.html content="Some info here"%}
{% include important.html content="Important info here"%}
{% include warning.html content="Warning here"%}
{% include deprecated.html content="Deprecation warning here"%}
