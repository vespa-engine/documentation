<!-- Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root. -->
[![Vespa Documentation Search Feed](https://github.com/vespa-engine/documentation/actions/workflows/feed.yml/badge.svg)](https://github.com/vespa-engine/documentation/actions/workflows/feed.yml)
[![/documentation link checker](https://cd.screwdriver.cd/pipelines/7021/link-checker-documentation/badge)](https://cd.screwdriver.cd/pipelines/7021/)

# Creating Vespa documentation

All Vespa features must have user documentation - this document explains how to write documentation.
See [introduction to documentation](en/introduction-to-documentation.html)
for styles and examples.


## Practical information

Vespa documentation is served using
[GitHub Project pages](https://help.github.com/categories/github-pages-basics/)
with
[Jekyll](https://help.github.com/en/github/working-with-github-pages/about-github-pages-and-jekyll).
To edit documentation, check out and work off the master branch in this repository.

Documentation is written in HTML or Markdown.
Use a single Jekyll template [_layouts/default.html](_layouts/default.html) to add header, footer and layout.

Install [bundler](https://bundler.io/), then

    $ bundle install
    $ bundle exec jekyll serve --incremental --drafts --trace

to set up a local server at localhost:4000 to see the pages as they will look when served.
If you get strange errors on bundle install try

    $ export PATH=“/usr/local/opt/ruby@2.6/bin:$PATH”
    $ export LDFLAGS=“-L/usr/local/opt/ruby@2.6/lib”
    $ export CPPFLAGS=“-I/usr/local/opt/ruby@2.6/include”
    $ export PKG_CONFIG_PATH=“/usr/local/opt/ruby@2.6/lib/pkgconfig”

The output will highlight rendering/other problems when starting serving.

Alternatively, use the docker image `jekyll/jekyll` to run the local server on
Mac

    $ docker run -ti --rm --name doc \
      --publish 4000:4000 -e JEKYLL_UID=$UID -v $(pwd):/srv/jekyll \
      jekyll/jekyll jekyll serve

or RHEL 8

    $ podman run -it --rm --name doc -p 4000:4000 -e JEKYLL_ROOTLESS=true \
      -v "$PWD":/srv/jekyll:Z docker.io/jekyll/jekyll jekyll serve

The layout is written in [denali.design](https://denali.design/),
see [_layouts/default.html](_layouts/default.html) for usage.
Please do not add custom style sheets, as it is harder to maintain.

## Writing good documentation

Learn how to [contribute](https://github.com/vespa-engine/vespa/blob/master/CONTRIBUTING.md) to documentation, 
then read the following guide before writing some.

### Guides and references

A document cannot be both comprehensive and comprehensible.
Because of this, documentation is split into *guides* and *reference* documents.

Guides should be easy to understand by only explaining the most important concepts under discussion.
Reference documents on the other hand must be complete but should skip verbiage meant to aid understanding.

Reference documents are those that are placed in reference/ subdirectories.

### Maintainability

Prioritize maintainability higher than usability:

* Don't include unnecessary details, especially ephemeral ones such as that a feature is "recently added" or how things was before, etc. The guide/reference distinction helps here: Guides are harder to maintain as they contain more verbiage, and they should not unnecessarily repeat information found in a reference doc. **Write such that the document will still be correct in a half decade.**

* Don't repeat information found in other documents. It is tempting to make life easier for users by writing use-case oriented documentation on how to accomplish specific tasks, but this backfires as it leads to a lot of repetition which we fail to maintain. In the long run it is better to explain the concepts clearly and succinctly and leave it to the users to piece together the information. **Use the same principles for documentation as for code: DRY, refactor for coherency etc.**

* Be wary of adding code in the documentation. The code will becomes incorrect over time and should in most cases be placed in git as continuously built code and referenced from the doc.

### Text quality

Documentation is not high prose, and not a podcast.
Users want to consume the information as soon as possible with as little effort as possible and get on with their lives.

Make the text as short, clear, and easy to read as possible:
* Describe things plainly "as they are". You usually shouldn't worry about explaining why, what you can do with it etc.
* Use short sentences with simple structure.
* Avoid superfluous words such as "very".
* Avoid filler sentences intended to improve the flow of the text - documents are usually browsed, not read anyway.
* Use consistent terminology even when it leads to repetition which would be bad in other kinds of writing.
* Use active form "index the documents", not passive "indexing the documents".
* Avoid making it personal - do not use "we", "you", "our".
* Do not use &amp;quot; , &amp;mdash; and the likes - makes the document harder to edit, and no need to use it.
* Less is more - &lt;em&gt; and &lt;strong&gt; is sufficient formatting in most cases.

### Links

Add an *id* attribute to each heading such that link can refer to it: Use the exact same text as the heading as id, lowercased and with spaces replaced by dashes such that references can be made without checking the source.
Don't change headings/ids unless completely necessary as that breaks links.

Example:
&lt;h2 id=&quot;my-nice-heading&quot;&gt;My nice Heading&lt;/h2&gt;
If this algorithmic transformation is followed it is possible to link to this section using &lt;a href=&quot;doc.html#my-nice-heading&quot;&gt; without having to consult the html source of the page to find the right id.

### Link to Javadoc

* Link to javadoc for an artifact: https://javadoc.io/doc/com.yahoo.vespa/container-search
* Link to javadoc for a package: https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/federation/vespa/package-summary.html
* Link to javadoc for a class: https://javadoc.io/doc/com.yahoo.vespa/vespa-feed-client-api/latest/ai/vespa/feed/client/JsonFeeder.html

*By Jon Bratseth, June 2016*



## Appendix: Vespa Documentation Search

See [Vespa Documentation Search](https://github.com/vespa-engine/sample-apps/tree/master/vespa-cloud/vespa-documentation-search)
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

1. Feed changes to https://console.vespa.oath.cloud/tenant/vespa-team/application/vespacloud-docsearch
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
