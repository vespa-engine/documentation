# _plugins/html_to_markdown_generator.rb

require 'reverse_markdown'
require 'fileutils'
require 'parallel'

Jekyll::Hooks.register :site, :post_write do |site|
  # Filter HTML pages and gather the necessary data upfront.
  # Complex objects (like Jekyll::Page) don't work well across processes,
  # so we extract the simple data (strings) we need.
  pages_to_process = (site.pages + site.documents).filter_map do |page|
    next unless page.output_ext == '.html' && page.data['generate_markdown'] != false
    
    html_path = page.destination(site.dest)
    # Skip if the source HTML file doesn't exist
    next unless File.exist?(html_path)

    {
      html_path: html_path,
      url: page.url,
      # Pass mtime to avoid a separate File.stat call in the child process
      html_mtime: File.mtime(html_path)
    }
  end

  # Calculate all unique destination directories before the parallel block.
  # This avoids using a slow Mutex for synchronization inside the loop.
  required_dirs = pages_to_process.map do |page_data|
    File.dirname(construct_markdown_path(site.dest, page_data[:url]))
  end.uniq
  
  FileUtils.mkdir_p(required_dirs)
  Jekyll.logger.info "Markdown Generator:", "Pre-created #{required_dirs.count} directories."

  # For CPU-bound tasks like HTML parsing, processes are much faster than threads
  # in Ruby due to the Global Interpreter Lock (GIL).
  # We pass site.dest as an argument to make it available in each process.
  Parallel.each(pages_to_process, in_processes: Parallel.processor_count, progress: "Generating Markdown") do |page_data|
    md_path = construct_markdown_path(site.dest, page_data[:url])
    
    # Skip if the markdown file is newer than the HTML file
    next if File.exist?(md_path) && File.mtime(md_path) >= page_data[:html_mtime]

    html_content = File.read(page_data[:html_path])

    markdown_content = ReverseMarkdown.convert(
      html_content, 
      github_flavored: true,
      unknown_tags: :bypass,
      tag_border: ''
    )

    processed_content = process_markdown_content(markdown_content)

    File.write(md_path, processed_content)
  end
  
  Jekyll.logger.info "Markdown Generator:", "Processing complete."
end


def process_markdown_content(markdown_content)
  # Find the first line that starts with '#' followed by a space
  if (index = markdown_content.index(/^#\s/))
    markdown_content.slice(index..-1)
  else
    # If no heading is found, return the original content
    markdown_content
  end
end

# Combined the logic for URLs ending in "/" and other paths.
def construct_markdown_path(site_dest, page_url)
  # Handle the root index page specifically
  if page_url == "/"
    return File.join(site_dest, "index.html.md")
  end

  # For all other URLs (/about/, /page.html), remove the leading slash
  # and append ".md". The path becomes `_site/about/.md` or `_site/page.html.md`.
  File.join(site_dest, page_url[1..-1] + ".md")
end