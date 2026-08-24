<!-- Copyright Vespa.ai. All rights reserved. -->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://assets.vespa.ai/logos/Vespa-logo-green-RGB.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://assets.vespa.ai/logos/Vespa-logo-dark-RGB.svg">
  <img alt="#Vespa" width="200" src="https://assets.vespa.ai/logos/Vespa-logo-dark-RGB.svg" style="margin-bottom: 25px;">
</picture>

# Creating Vespa documentation

All Vespa features must be documented - this document explains how to add to the documentation.

## Practical information

Vespa documentation is served using [Mintlify](https://mintlify.com/docs).
To edit documentation, check out and work off the master branch in this repository.

Documentation is written in [MDX](https://mintlify.com/docs/text) and lives under `en/` (and `ja/`).
Navigation is defined in [docs.json](docs.json).

### Local development

Install the [Mintlify CLI](https://www.npmjs.com/package/mint) to preview documentation changes locally:

    $ npm i -g mint

Run the following command at the root of the repository, where `docs.json` is located:

    $ mint dev

View the local preview at `http://localhost:3000`.
The output will highlight rendering/other problems when starting serving.

Troubleshooting:

- If the dev environment isn't running: Run `mint update` to ensure you have the most recent version of the CLI.
- If a page loads as a 404: Make sure you are running in a folder with a valid `docs.json`.

### Publishing changes

Changes are deployed to production automatically after pushing to the default branch,
via the [Mintlify GitHub app](https://dashboard.mintlify.com/settings/organization/github-app).

### Migration scripts

[scripts/](scripts/) contains the helper scripts used to convert the Jekyll HTML/Markdown
sources to MDX during the Mintlify migration, e.g. [scripts/html_to_mdx.py](scripts/html_to_mdx.py).

## Writing documentation

This explains the style and considerations to follow before contributing documentation.
See [contribute](https://docs.vespa.ai/en/learn/contributing) on the practicalities of
submitting changes.

### Table of contents

All documents must be listed in the navigation in [docs.json](docs.json).

### Guides and references

A document cannot be both comprehensive and comprehensible.
Because of this, documentation is split into *guides* and *reference* documents.

Guides should be easy to understand by only explaining the most important concepts under discussion.
Reference documents on the other hand must be complete but should skip verbiage meant to aid understanding.

Reference documents are those that are placed in reference/ subdirectory.

### Categorization

The documents are categorized in a set of categories which are mostly the same for guides and references.

The subdirectory and the navigation group used in docs.json must always be the same.

Place new documents in the most suitable category. Most times they can fit multiple ones; such is life.

Be conscious of the category a document is in when editing it. If you're adding off-category information,
maybe it should be split into another document?

Be extra careful about what is added to the "basics" documents: They should be a clean, easy to understand
introduction to only the most important concepts of Vespa.

If you need to move a document, you can; just make sure to add an entry in the `redirects`
array in [docs.json](docs.json) from the old location.

### Applicability

Some documentation only applies to Vespa Cloud ("cloud"), self-managed instances ("self-managed"),
and/or is only available commercially ("enterprise").
Make this clear in the document when applicable.
See https://docs.vespa.ai/en/learn/about-documentation for a more detailed description of the three
applicability types.

### Maintainability

Prioritize maintainability higher than usability:

* Don't include unnecessary details, especially ephemeral ones such as that a feature is "recently added" or how things was before, etc. The guide/reference distinction helps here: Guides are harder to maintain as they contain more verbiage, and they should not unnecessarily repeat information found in a reference doc. **Write such that the document will still be correct in a half decade.**

* Don't repeat information found in other documents. It is tempting to make life easier for users by writing use-case oriented documentation on how to accomplish specific tasks, but this backfires as it leads to a lot of repetition which we fail to maintain. In the long run it is better to explain the concepts clearly and succinctly and leave it to the users to piece together the information. **Use the same principles for documentation as for code: DRY, refactor for coherency etc.**

* Be wary of adding code in the documentation. The code will become incorrect over time and should in most cases be placed in git as continuously built code and referenced from the doc.

### Style

Documentation is not high prose, and not a podcast.
Users want to consume the information as soon as possible with as little effort as possible and get on with their lives.

Make the text as short, clear, and easy to read as possible:
* Describe things plainly "as they are". You usually shouldn't worry about explaining why, what you can do with it etc.
* Use short sentences with simple structure.
* Avoid superfluous words such as "very".
* Avoid filler sentences intended to improve the flow of the text - documents are usually browsed, not read anyway.
* Use consistent terminology even when it leads to repetition which would be bad in other kinds of writing.
* Use active form "index the documents", not passive "indexing the documents".

### Linking

Use root-relative internal links without a file suffix, e.g. `/en/querying/query-api`.

Don't change headings unless completely necessary, as heading anchors are derived from
the heading text and changing them breaks links.

### Link to Javadoc

* Link to javadoc for an artifact: https://javadoc.io/doc/com.yahoo.vespa/container-search
* Link to javadoc for a package: https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/federation/vespa/package-summary.html
* Link to javadoc for a class: https://javadoc.io/doc/com.yahoo.vespa/vespa-feed-client-api/latest/ai/vespa/feed/client/JsonFeeder.html
