require 'json'
require 'nokogiri'

module Jekyll

    class VespaIndexGenerator < Generator
        priority :lowest

        def generate(site)
            doctype = site.config["search"]["doctype"]
            operations = []
            site.pages.each do |page|
                if page.data["index"] == true
                    operations.push({
                        :put => "id:doc:doc::" + doctype + page.url,
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
            File.open(site.config["search"]["feed"], "w") { |f| f.write(json) }

        end

        def extract_text(page)
            doc = Nokogiri::HTML(page.content)
            content = doc.xpath("//text()").to_s
            page_text = content.gsub("\r"," ").gsub("\n"," ")
        end

    end

end
