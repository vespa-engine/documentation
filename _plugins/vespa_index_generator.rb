require 'json'
require 'nokogiri'

module Jekyll

    class VespaIndexGenerator < Jekyll::Generator
        priority :lowest

        def generate(site)
            doctype = site.config["search"]["doctype"]
            operations = []
            site.pages.each do |page|
                if page.data["index"] == true
                    operations.push({
                        :fields => {
                            :path => page.url,
                            :doctype => doctype,
                            :title => page.data["title"],
                            :content => extract_text(page)
                        }
                    })
                end
            end

            json = JSON.pretty_generate(operations)
            File.open(doctype + "_index.json", "w") { |f| f.write(json) }
        end

        def extract_text(page)
            doc = Nokogiri::HTML(page.content)
            doc.search('th,td').each{ |e| e.after "\n" }
            content = doc.xpath("//text()").to_s
            page_text = content.gsub("\r"," ").gsub("\n"," ")
        end

    end

end
