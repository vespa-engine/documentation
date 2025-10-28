---
# Copyright Vespa.ai. All rights reserved.
title: ".vespaignore"
---

When deploying an [application
package](../application-packages.html) with [Vespa CLI](/en/vespa-cli.html),
a `.vespaignore` file (similar to `.gitignore`) can be
added to the package to prevent specific files or path patterns from being
included in the deployed package.

Ignoring files is useful when the Vespa application directory contains files
that are only used for development purposes, and are not directly referenced
by the application.

## Location

The `.vespaignore` file must be placed at the same level
as [services.xml](services.html). Having
multiple `.vespaignore` at different path levels is not supported.

## Example

This is an example of a `.vespaignore` file that excludes files
and directories rarely needed in an application package.

```
# exclude hidden files and readme
.DS_Store
.gitignore
README.md

# exclude feed input
ext/

# exclude auxiliary scripts
*.py
*.sh
```

## Format

The `.vespaignore` format is a subset of
the `.gitignore` format, where:
* Lines starting with `#` are ignored and can be used for comments
* Each non-empty line specifies a path pattern to ignore
* Patterns are relative to `services.xml`
* A pattern can be either a literal string,
  or a pattern string as consumed by [filepath.Match](https://pkg.go.dev/path/filepath#Match)
* Lines ending with `/` always denote a directory, e.g. the pattern `foo/`
  will match the directory `foo` (and any files below),
  but not the file `foo`

Complex rules, such as negated patterns and recursive globbing (`**`) are not supported.
