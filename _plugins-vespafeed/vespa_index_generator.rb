# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

require 'json'
require 'nokogiri'
require 'kramdown/parser/kramdown'

module Jekyll

    class VespaIndexGenerator < Jekyll::Generator
        priority :lowest

        def generate(site)
            namespace = site.config["search"]["namespace"]
            operations = []
            site.pages.each do |page|
                next if page.path.start_with?("css/") ||
                        page.url.start_with?("/redirects.json") ||
                        is_empty(page)
                if page.data["index"]
                    url = page.url
                    url += 'index.html' if url[-1, 1] == '/'
                    text = extract_text(page)
                    outlinks = extract_links(page)
                    headers = extract_headers(page)
                    keywords = get_keywords(page)
                    fields = {
                        :path => url,
                        :namespace => namespace,
                        :title => page.data["title"],
                        :content => text,
                        :html => get_html(page),
                        :term_count => text.split.length(),
                        :last_updated => Time.now.to_i
                    }
                    fields[:outlinks] = outlinks if !outlinks.empty?
                    fields[:headers]  = headers  if !headers.empty?
                    fields[:keywords] = keywords if !keywords.empty?
                    operations.push({:put => "id:" + namespace + ":doc::" + namespace + url,
                                     :fields => fields})
                end
            end
            json = JSON.pretty_generate(operations)
            File.open(namespace + "_index.json", "w") { |f| f.write(json) }
        end

        def is_empty(page)
            # The generated client-side redirects should not be indexed -
            # they have no title and node content
            return page.content == "" && !page.data["title"]
        end

        def get_html(page)
            if page.name[page.name.rindex('.')+1..-1] == "md"
                doc = Kramdown::Document.new(page.content).to_html
            else
                doc = page.content
            end
        end

        def get_doc(page)
            if page.name[page.name.rindex('.')+1..-1] == "md"
                doc = Nokogiri::HTML(Kramdown::Document.new(page.content).to_html)
            else
                doc = Nokogiri::HTML(page.content)
            end
        end

        def reset_xml_pre(doc)
            # The highlighter works on un-quoted XML, so some docs have non-HTML elements like <services>
            # Read and set such fields again for proper quoting and later text extraction (dirty hack ...)
            doc.search('pre').each do |pre|
                if pre.to_s =~ /\{% highlight xml %}/
                    pre.content = pre.to_s.gsub("\n", " ")
                        .gsub(/<pre>\s*\{% highlight xml %}(.+?)\{% endhighlight %}<\/pre>/, '\1')
                end
            end
            return doc
        end

        def extract_text(page)
            doc = reset_xml_pre(get_doc(page))
            doc.search('th,td').each{ |e| e.after "\n" }
            doc.search('style').each{ |e| e.remove }
            content = doc.xpath("//text()").to_s
                .gsub("\r"," ")
                .gsub("\n"," ")
            return strip_liquid(content)
        end

        def extract_links(page)
            doc = get_doc(page)
            links = doc.css('a').map { |link| link['href'] || ""}
            links.reject{ |l| l.empty? }.map{ |l| l }
            return links
        end

        def extract_headers(page)
            doc = get_doc(page)
            headers = doc.css('h1,h2,h3,h4').map { |header| header.content.gsub("\r"," ").gsub("\n"," ") || ""}
            headers.reject{ |h| h.empty? }.map{ |h| h }
            return headers
        end

        def get_keywords(page)
            doc = get_doc(page)
            keywords = []
            if page.data["keywords"]
                page.data["keywords"].split(/,/).each do |k|
                    k = k.strip
                    keywords.push(k) if ! k.empty?
                end
            end
            return keywords
        end

        def strip_liquid(text)
            return text.gsub(/\{%(.+?)%}/) { "#{ process_liquid($1) }" } # .+? is a lazy match, match only once
        end

        def process_liquid(match)
        # https://ruby-doc.org/core-3.1.2/Regexp.html for the quotes
        # ToDo: define the quote pattern (\"|\p{Pi}|\p{Pf}|') once and build regex using this as a parameter
        #
        # This is a poor man's solution to clean the data for search -
        # the alternative is building the site and _then_ extract data
        # That will however add jekyll build as a dependency for feeding, so keeping this simple for now
            return match.gsub(/^\s*highlight\s*\w*/, "")
                     .gsub(/^\s*(raw|endraw|endhighlight)/, "")
                     .gsub(/^\s*include\s*(deprecated|important|note|query|warning).html\s*content=\s*(\"|\p{Pi}|\p{Pf}|')/, "")
                     .gsub(/^\s*include\s*video-include.html\s.*video-title=\s*(\"|\p{Pi}|\p{Pf}|')/, "Find at vespa.ai/resources: ")
                     .gsub(/^\s*include\s*pre-req.html\s*memory=\s*(\"|\p{Pi}|\p{Pf}|')(.*)/)  { "#{ process_pre_req($2) }" }
                     .gsub(/(\"|\p{Pi}|\p{Pf}|')\s*$/, "")
        end

        def process_pre_req(match)
            return match.gsub(/([0-9]*)\s*GB/, '
                Docker: Docker Desktop for Mac/Windows, or Docker on Linux.
                Operating system: Linux, macOS or Windows 10 Pro.
                Architecture: x86_64 or arm64.
                Minimum \1 GB RAM dedicated to Docker (the default is 2 GB on macOS). Memory recommendations.
                Homebrew to install the Vespa CLI, or download Vespa CLI from Github releases.')
                .gsub(/(\"|\p{Pi}|\p{Pf}|')\s*extra-reqs=\s*(\"|\p{Pi}|\p{Pf}|')/, "")
        end

    end

end
