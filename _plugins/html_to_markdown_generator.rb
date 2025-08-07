# _plugins/html_to_markdown_generator.rb

# Require the reverse_markdown gem to make its functionality available.
require 'reverse_markdown'

# Register a hook to run after the entire site has been written to disk.
# The :site, :post_write hook provides access to the completed site object.
Jekyll::Hooks.register :site, :post_write do |site|

  # Iterate over all pages and documents (including posts) in the site.
  # This ensures comprehensive coverage for all generated HTML content.
  (site.pages + site.documents).each do |page|
    # Skip any documents that are not HTML files (e.g., CSS, JS, etc.).
    next unless page.output_ext == '.html'

    # Skip pages that explicitly disable markdown generation
    next if page.data['generate_markdown'] == false

    # Construct the full, absolute path to the final HTML file in the _site directory.
    html_path = page.destination(site.dest)

    # Construct the path for the new Markdown file.
    # We need to create the .md file at a location that matches what the template expects
    # when it constructs the URL using {{ page.url | append: '.md' }}
    md_path = construct_markdown_path(site.dest, page.url)

    # Check if the source HTML file actually exists before trying to read it.
    if File.exist?(html_path)
      # Read the content of the generated HTML file.
      html_content = File.read(html_path)

      # Convert the HTML content to Markdown using the reverse_markdown gem.
      # github_flavored: true ensures compatibility with common Markdown platforms.
      # unknown_tags: :bypass leaves unrecognized tags as-is instead of dropping them.
      # tag_border: '' removes extra whitespace around block elements for cleaner output.
      markdown_content = ReverseMarkdown.convert(html_content, 
        github_flavored: true,
        unknown_tags: :bypass,
        tag_border: ''
      )

      # Process the markdown content to skip everything until the first heading
      markdown_content = process_markdown_content(markdown_content)

      # Write the converted Markdown content to the new .html.md file.
      File.write(md_path, markdown_content)
      
      # Log the generation for debugging purposes
      Jekyll.logger.info "Generated Markdown:", "#{md_path}"
    end
  end
end

# Helper method to process markdown content and skip everything until the first heading
def process_markdown_content(markdown_content)
  lines = markdown_content.split("\n")
  output_lines = []
  found_first_heading = false
  
  lines.each do |line|
    # Check if this line is a heading (starts with #)
    if line.strip.match(/^#+\s/)
      found_first_heading = true
    end
    
    # Start collecting lines once we've found the first heading
    if found_first_heading
      output_lines << line
    end
  end
  
  # If no heading was found, return the original content
  # This handles cases where pages might not have standard headings
  return output_lines.empty? ? markdown_content : output_lines.join("\n")
end

# Helper method to construct the markdown file path based on the page URL
# This ensures the .md file is created where the template expects to find it
def construct_markdown_path(site_dest, page_url)
  # Handle different URL patterns:
  # "/" -> "/index.html.md"
  # "/en/performance/" -> "/en/performance/.md" 
  # "/en/document.html" -> "/en/document.html.md"
  
  if page_url == "/"
    # Root page maps to index.html.md
    File.join(site_dest, "index.html.md")
  elsif page_url.end_with?("/")
    # Directory URLs (like /en/performance/) should create .md files at that path
    # The template will request page.url + '.md' which becomes '/en/performance/.md'
    File.join(site_dest, page_url[1..-1] + ".md")
  else
    # Regular pages like /en/document.html become /en/document.html.md
    File.join(site_dest, page_url[1..-1] + ".md")
  end
end
