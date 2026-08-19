<!-- Copyright Vespa.ai. All rights reserved. -->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://assets.vespa.ai/logos/Vespa-logo-green-RGB.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://assets.vespa.ai/logos/Vespa-logo-dark-RGB.svg">
  <img alt="#Vespa" width="200" src="https://assets.vespa.ai/logos/Vespa-logo-dark-RGB.svg" style="margin-bottom: 25px;">
</picture>

[![Vespa Documentation Search Feed](https://github.com/vespa-engine/documentation/actions/workflows/feed.yml/badge.svg)](https://github.com/vespa-engine/documentation/actions/workflows/feed.yml)
[![/documentation link checker](https://cd.screwdriver.cd/pipelines/7021/link-checker-documentation/badge)](https://cd.screwdriver.cd/pipelines/7021/)

# Creating Vespa documentation

All Vespa features must be documented - this document explains how to add to the documentation.

## Practical information

Vespa documentation is served using [AWS Amplify](https://aws.amazon.com/amplify/) with [Jekyll](https://jekyllrb.com/).
To edit documentation, check out and work off the master branch in this repository.

Documentation is written in HTML or Markdown.
Use a single Jekyll template [_layouts/default.html](_layouts/default.html) to add header, footer and layout.

You probably need to get the right Ruby version first, with

    $ brew install rbenv
    $ rbenv init
    $ source ~/.zprofile
    $ rbenv install 3.3.7
    $ rbenv local 3.3.7

Prepend /opt/homebrew/opt/ruby/bin to your $PATH, e.g. in your .zshrc.

Then you should be able to run:

    $ bundle install
    $ bundle exec jekyll serve --incremental --drafts --trace

to set up a local server at localhost:4000 to see the pages as they will look when served.

The output will highlight rendering/other problems when starting serving.

Alternatively, use the docker image `jekyll/jekyll` to run the local server on
Mac

    $ docker run -ti --rm --name doc \
      --publish 4000:4000 -e JEKYLL_UID=$UID -v $(pwd):/srv/jekyll \
      jekyll/jekyll jekyll serve --incremental --force_polling

or RHEL 8

    $ podman run -it --rm --name doc -p 4000:4000 -e JEKYLL_ROOTLESS=true \
      -v "$PWD":/srv/jekyll:Z docker.io/jekyll/jekyll jekyll serve --incremental --force_polling

The Jekyll server should normally rebuild HTML files automatically
when a source files changes. If this does not happen, you can use
`jekyll serve --force-polling` as a workaround.

The layout is written in [denali.design](https://denali.design/),
see [_layouts/default.html](_layouts/default.html) for usage.
Please do not add custom style sheets, as it is harder to maintain.

## Writing documentation

This explains the style and considerations to follow before contributing documentation.
See [contribute](https://docs.vespa.ai/en/learn/contributing.html) on the practicalities of
submitting changes.

### Table of contents

All documents must be listed in_data/sidebar.yml.

### Guides and references

A document cannot be both comprehensive and comprehensible.
Because of this, documentation is split into *guides* and *reference* documents.

Guides should be easy to understand by only explaining the most important concepts under discussion.
Reference documents on the other hand must be complete but should skip verbiage meant to aid understanding.

Reference documents are those that are placed in reference/ subdirectory.

### Categorization

The documents are categorized in a set of categories which are mostly the same for guides and references.

The subdirectory and category used in the TOC (sidebar.yml) must always be the same.

Place new documents in the most suitable category. Most times they can fit multiple ones; such is life.

Be conscious of the category a document is in when editing it. If you're adding off-category information,
maybe it should be split into another document? 

Be extra careful about what is added to the "basics" documents: They should be a clean, easy to understand
introduction to only the most important concepts of Vespa.

If you need to move a document, you can; just make sure to add a redirect header from the old location.

### Applicability

Some documentation only applies to Vespa Cloud ("cloud"), self-managed instances ("self-managed"), 
and/or is only available commercially ("enterprise").
Such documents *must* be marked by setting the appropriate applies_to tags in the document header. 
See https://docs.vespa.ai/en/learn/about-documentation.html for more a more detailed description of the three applicability
types.

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

Use relative internal links. All internal links will work with and without ".html" suffix, ".md" suffix does not work.
Use the ".html" suffix when linking to pages where the source is html, and no suffix when linking to Markdown sources.
That convention is helpful to determine whether a link marked as non-existing in your editor is due to it being a
Markdown file (with suffix .md, which can't be used in the link), or due to it actually not existing.

Add an *id* attribute to each heading such that it can be linked to: Use the exact same text as the heading as id, 
lowercased and with spaces replaced by dashes such that references can be made without checking the source.
Don't change headings/ids unless completely necessary as that breaks links.

### Link to Javadoc

* Link to javadoc for an artifact: https://javadoc.io/doc/com.yahoo.vespa/container-search
* Link to javadoc for a package: https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/federation/vespa/package-summary.html
* Link to javadoc for a class: https://javadoc.io/doc/com.yahoo.vespa/vespa-feed-client-api/latest/ai/vespa/feed/client/JsonFeeder.html

## Appendix: Vespa Documentation Search

See the [Vespa Documentation Search](https://github.com/vespa-cloud/vespa-documentation-search)
sample application for architecture.

Below is a description of the job for indexing this repository's documentation.
File locations below refer to this repo's root.

1. Build a Vespa feed from the source in this repo:
    1. Use Jekyll to generate HTML from the content
      (some files are in [Markdown](https://daringfireball.net/projects/markdown/))
    1. Use [Nokogiri](https://nokogiri.org/) to extract text from HTML
    1. Implement HTML-to-text in a Vespa feed file by using a
      [Jekyll Generator](https://jekyllrb.com/docs/plugins/generators/),
      see [_plugins-vespafeed/vespa_index_generator.rb](/_plugins-vespafeed/vespa_index_generator.rb)
    1. The generated _open_index.json_ can then be
      [fed to Vespa](https://docs.vespa.ai/en/reference/document-json-format.html)

1. Feed changes to https://console.vespa-cloud.com/tenant/vespa-team/application/vespacloud-docsearch
   using [feed_to_vespa.py](feed_to_vespa.py):
    1. Visit all content on the Vespa instance to list all IDs
    1. Determine whether or not to remove documents
    1. Feed all content
    
1. Automate these steps using GitHub Actions
    1. Store the keys required to feed data as secrets in Github
    1. Find workflow at [.github/workflows/feed.yml](/.github/workflows/feed.yml)

Local development:

    $ bundle exec jekyll build
    $ ./feed_to_vespa.py   # put data-plane-private/public-key.pem in this dir in advance
