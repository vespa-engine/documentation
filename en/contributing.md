---
title: Contributing to Vespa
---

# Contributing to Vespa

Contributions to [Vespa](http://github.com/vespa-engine/vespa) and the [Vespa documentation](http://github.com/vespa-engine/documentation) are welcome. This document tells you what you need to know to contribute.

This is a test.

### Open development

All work on Vespa happens directly on GitHub, using the [GitHub flow model](https://docs.github.com/en/get-started/quickstart/github-flow). We release the master branch a few times a week, and you should expect it to almost always work. In addition to the [builds seen on factory.vespa.ai](https://factory.vespa.ai) we have a large acceptance and performance test suite which is also run continuously.

#### Pull requests

All pull requests are reviewed by a member of the Vespa Committers team. You can find a suitable reviewer in the OWNERS file upward in the source tree from where you are making the change (the OWNERS have a special responsibility for ensuring the long-term integrity of a portion of the code). If you want to become a committer/OWNER making some quality contributions is the way to start.

We require all pull request checks to pass.

### Versioning

Vespa uses semantic versioning - see [vespa versions](https://vespa.ai/releases#versions). Notice in particular that any Java API in a package having a @PublicAPI annotation in the package-info file cannot be changed in an incompatible way between major versions: Existing types and method signatures must be preserved (but can be marked deprecated).

### Issues

We track issues in [GitHub issues](https://github.com/vespa-engine/vespa/issues). It is fine to submit issues also for feature requests and ideas, whether you intend to work on them or not.

There is also a [ToDo list](https://github.com/vespa-engine/vespa/blob/master/TODO.md) for larger things which no one are working on yet.

### Community

If you have questions, want to share your experience or help others, please join our community on the [Vespa Slack](http://slack.vespa.ai), or see Vespa on [Stack Overflow](http://stackoverflow.com/questions/tagged/vespa).
