# Vespa Documentation Feed

Job for indexing Vespa cloud and open source documentation.

Steps:

1. Clone [vespa/documentation](github.com/vespa/documentation)
  and [vespa/cloud](github.com/vespa/cloud) to get documentation source

1. Build a Vespa feed from the source:
    1. Use Jekyll to generate HTML from the content (some files are in [Markdown](https://daringfireball.net/projects/markdown/))
    1. Use [Nokogiri](https://nokogiri.org/) to extract text from HTML
    1. Implement HTML-to-text in a Vespa feed file by using a [Jekyll Generator](https://jekyllrb.com/docs/plugins/generators/),
      see [vespa_index_generator.rb](_plugins/vespa_index_generator.rb)
    1. The end result is hence a JSON file can can be [fed to vespa](https://docs.vespa.ai/documentation/reference/document-json-format.html)    

1. Feed changes to https://console.vespa.oath.cloud/tenant/vespa-team/application/vespacloud-docsearch using [feed_to_vespa.py](feed_to_vespa.py):   
    1. Visit all content on the Vespa instance to list all IDs
    1. Determine whether or not to remove documents
    1. Feed all content
    
1. Automate these steps using GitHub Actions
    1. Store the keys required to feed data as secrets in Github
