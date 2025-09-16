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
  end.uniq.reject { |dir| dir == '.' }
  
  FileUtils.mkdir_p(required_dirs) unless required_dirs.empty?
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

  # First, we want to add a new file that is called llms.txt.
  # The first lines should be
  # # Vespa documentation

  # > Top level description goes here

  # Optional details go here

  # Then, we want to append to that file, for each generated markdown file:    
  # For each page in pages_to_process, we want to construct:
  # A. section: This will be the directory level below  /en.
  # B. md_path: This will be the full path of the markdown file. 
  # Example: /en/reference/index.html.md will be: 
  # section: reference
  # md_path: /en/reference/index.html.md
  
  # Pass the site object to generate_llms_txt so we can access the base URL
  generate_llms_txt(site.dest, pages_to_process, site)

  Jekyll.logger.info "Markdown Generator:", "Processing complete."
end

def generate_llms_txt(site_dest, pages_to_process, site)
  # Write to parent directory of site_dest
  site_parent = File.expand_path("..", site_dest)
  # Path to llms.txt
  llms_path = File.join(site_dest, "llms.txt")
  repo_path = File.join(site_parent, "llms.txt")
  # Read llms-template.md to get top level description
  template_path = File.join(site_parent, "llms-template.md")
  if File.exist?(template_path)
    template_content = File.read(template_path)
  else
    Jekyll.logger.Error "Markdown Generator:", "Template file not found at #{template_path}. Cannot generate llms.txt."
    return
  end
  
  # Get base URL from site configuration
  base_url = site.config['url'] || 'https://docs.vespa.ai'
  
  # Initialize the file with header content
  File.open(llms_path, 'w') do |file|
    # Write template content first
    file.puts template_content
    
    # Process each markdown file to generate a map of sections to files to content.
    sections_map = {}
    
    pages_to_process.each do |page_data|
      md_path = construct_markdown_path(site_dest, page_data[:url])
      
      # Extract section from URL (directory level below /en)
      section = extract_section(page_data[:url])

      # Extract title first H1 heading from md_path
      title_desc = extract_title_and_description(md_path, page_data[:url])
      
      # Initialize section array if not exists
      sections_map[section] ||= []
      
      # Add page info to section
      page_info = {
        md_path: md_path,
        title: title_desc[:title],
        description: title_desc[:description],
        url: page_data[:url]
      }
      
      # Read content if file exists
      if File.exist?(md_path)
        page_info[:content] = File.read(md_path)
      end
      
      sections_map[section] << page_info
    end
    
    # Write each section to the llms.txt file
    sections_map.each do |section, pages|
      # Skip if section is '404'
      next if section == '404'
      # Filter out pages that start with "Redirect"
      valid_pages = pages.reject { |page_info| page_info[:title].start_with?("Redirect") }
      # Skip section entirely if no valid pages
      next if valid_pages.empty?
      
      file.puts "## #{section}\n\n"
      
      valid_pages.each do |page_info|
        # Use the base URL from site configuration + original page URL
        web_url = "#{base_url}#{page_info[:md_path]}"
        file.puts "- [#{page_info[:title]}](#{web_url})" + (page_info[:description] ? ": #{page_info[:description]}" : "")
      end
      file.puts "\n"
    end
    # Copy file to repo_path
    FileUtils.cp(llms_path, repo_path)
  end
  
  Jekyll.logger.info "Markdown Generator:", "Generated llms.txt with #{pages_to_process.count} pages."
end

def extract_title_and_description(md_path, page_url)
  # First try to extract H1 heading from the markdown file. 
  # The description should be the first sentence (detected by a period followed by space or end of line) after the H1 heading.
  title = nil
  description = nil
  
  if File.exist?(md_path)
    File.open(md_path, 'r') do |file|
      file.each_line do |line|
        # Look for the first line that starts with a single # followed by a space
        if line.match(/^#\s+(.+)$/)
          title = line.match(/^#\s+(.+)$/)[1].strip
          
          # Try to read the next non-empty line for description
          while (next_line = file.gets)
            next_line = next_line.strip
            next if next_line.empty? || next_line.start_with?('#')
            
            # Extract first sentence (up to first period followed by space or end of line)
            if match = next_line.match(/^(.+?\.)\s/)
              description = match[1]
            elsif next_line.end_with?('.')
              description = next_line
            else
              description = next_line
            end
            break
          end
          break
        end
      end
    end
  end
  
  # Fallback: extract title from URL (last part before .html.md) if no title found
  if title.nil?
    path_parts = page_url[1..-1].split('/')
    last_part = path_parts.last
    
    # If it ends with .html, remove that extension
    if last_part&.end_with?('.html')
      last_part = last_part[0...-5]  # Remove '.html'
    end
    
    # If the last part is empty or just 'index', use the parent directory name
    if last_part.nil? || last_part.empty? || last_part == 'index'
      # Get the parent directory name
      parent_dir = path_parts[-2] if path_parts.length > 1
      title = parent_dir || 'root'
    else
      title = last_part
    end
  end
  
  return { title: title, description: description }
rescue => e
  Jekyll.logger.warn "Markdown Generator:", "Error extracting title from #{md_path}: #{e.message}"
  # Final fallback to last part of URL
  fallback_title = page_url.split('/').last&.gsub(/\.html$/, '') || 'untitled'
  return { title: fallback_title, description: nil }
end

def extract_section(page_url)
  # Remove leading slash and split by '/'
  parts = page_url[1..-1].split('/')
  # Remove .html suffix from the last part if present
  parts[-1] = parts[-1].sub(/\.html$/, '') if parts.any?
  to_return = nil
  # If URL starts with 'en/', return the next directory level
  if parts.first == 'en' && parts.length > 2
    to_return = parts[2]  # e.g., /en/tutorials/getting-started.html -> section is 'tutorials'
  elsif parts.first == 'en' && parts.length == 2
    to_return = parts[1]  # e.g., /en/ -> section is 'en'
  else
    # If not under 'en/', return the first directory level
    to_return = parts.first || 'root'  # e.g., /about.html -> section is 'about'
  end
  # Replace "-" with " " and capitalize each word
  to_return.split('-').map(&:capitalize).join(' ')
rescue => e
  Jekyll.logger.warn "Markdown Generator:", "Error extracting section from #{page_url}: #{e.message}"
  'Unknown'
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

  # Remove the leading slash
  path_without_slash = page_url[1..-1]
  
  # If the URL ends with "/", it's a directory index page
  if page_url.end_with?("/")
    # Convert "/en/tutorials/" to "_site/en/tutorials/index.html.md"
    File.join(site_dest, path_without_slash + "index.html.md")
  else
    # For regular pages like "/page.html", convert to "_site/page.html.md"
    File.join(site_dest, path_without_slash + ".md")
  end
end