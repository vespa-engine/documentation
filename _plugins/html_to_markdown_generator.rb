# _plugins/html_to_markdown_generator.rb

require 'nokogiri'
require 'fileutils'

Jekyll::Hooks.register :site, :post_write do |site|
  # Filter HTML pages and gather the necessary data upfront
  pages_to_process = (site.pages + site.documents).filter_map do |page|
    next unless page.output_ext == '.html' && page.data['generate_markdown'] != false

    html_path = page.destination(site.dest)
    next unless File.exist?(html_path)

    {
      html_path: html_path,
      url: page.url,
      html_mtime: File.mtime(html_path)
    }
  end

  # Calculate all unique destination directories
  required_dirs = pages_to_process.map { |pd| File.dirname(construct_markdown_path(site.dest, pd[:url])) }
                                 .uniq.reject { |dir| dir == '.' }

  FileUtils.mkdir_p(required_dirs) unless required_dirs.empty?
  Jekyll.logger.info "Markdown Generator:", "Pre-created #{required_dirs.count} directories."

  # Process pages sequentially (GitHub Pages compatible)
  processed_count = 0
  total_count = pages_to_process.length

  pages_to_process.each do |page_data|
    md_path = construct_markdown_path(site.dest, page_data[:url])

    # Skip if the markdown file is newer than the HTML file
    next if File.exist?(md_path) && File.mtime(md_path) >= page_data[:html_mtime]

    html_content = File.read(page_data[:html_path])
    markdown_content = html_to_markdown(html_content)
    processed_content = process_markdown_content(markdown_content)

    File.write(md_path, processed_content)

    processed_count += 1
    if processed_count % 10 == 0 || processed_count == total_count
      Jekyll.logger.info "Markdown Generator:", "Processed #{processed_count}/#{total_count} pages"
    end
  end

  Jekyll.logger.info "Markdown Generator:", "Processing complete."
end

# --- Core conversion pipeline ---

# Convert HTML to Markdown using Nokogiri (GitHub Pages compatible)
def html_to_markdown(html_content)
  doc = Nokogiri::HTML(html_content)

  # Remove obvious non-content chrome early
  doc.css('script, style, noscript, template').remove
  doc.css('nav, header, footer, aside, [role="navigation"], [aria-hidden="true"]').remove
  # Remove common sidebar/TOC containers (conservative)
  doc.css('[class*="sidebar"], [id*="sidebar"], [class*="toc"], [id*="toc"]').remove

  # Find the main content area; fall back to body
  root = doc.at_css('main, .main-content, #main-content, article, .content') || doc.at_css('body')
  return "" unless root

  # Keep only content from the first H1 onward
  prune_to_first_h1!(root)

  # Convert the pruned fragment to markdown
  convert_element_to_markdown(root).strip
end

# Remove everything in +root+ that appears before the first <h1>.
# Walk up from the <h1> to +root+, removing previous siblings at each level.
def prune_to_first_h1!(root)
  h1 = root.at_css('h1')
  return root unless h1 # No H1? keep as-is.

  node = h1
  while node && node != root
    remove_previous_siblings!(node)
    node = node.parent
  end

  # If H1 is a direct child of root, ensure nothing precedes it there either
  remove_previous_siblings!(h1) if h1.parent == root

  root
end

def remove_previous_siblings!(node)
  # Remove all previous siblings (elements and text nodes) one by one
  while (sib = node.previous_sibling)
    sib.remove
  end
end

# --- HTML -> Markdown (element-wise) ---

def convert_element_to_markdown(element)
  name = element.element? ? element.name.downcase : nil

  case name
  when 'h1' then "# #{element.text.strip}\n\n"
  when 'h2' then "## #{element.text.strip}\n\n"
  when 'h3' then "### #{element.text.strip}\n\n"
  when 'h4' then "#### #{element.text.strip}\n\n"
  when 'h5' then "##### #{element.text.strip}\n\n"
  when 'h6' then "###### #{element.text.strip}\n\n"
  when 'p'   then "#{convert_children_to_markdown(element).strip}\n\n"
  when 'br'  then "\n"
  when 'strong', 'b' then "**#{element.text.strip}**"
  when 'em', 'i'     then "*#{element.text.strip}*"
  when 'code'
    if element.parent && element.parent.name.downcase == 'pre'
      "```\n#{element.text}\n```\n\n"
    else
      "`#{element.text.strip}`"
    end
  when 'pre'
    if element.css('code').any?
      convert_children_to_markdown(element)
    else
      "```\n#{element.text}\n```\n\n"
    end
  when 'a'
    href = element['href']
    text = element.text.strip
    if href && !href.empty? && text != href
      "[#{text}](#{href})"
    else
      text
    end
  when 'ul' then convert_children_to_markdown(element)
  when 'ol' then convert_children_to_markdown(element, true)
  when 'li'
    content = convert_children_to_markdown(element).strip
    if element.parent && element.parent.name.downcase == 'ol'
      "1. #{content}\n"
    else
      "- #{content}\n"
    end
  when 'blockquote'
    lines = convert_children_to_markdown(element).strip.split("\n")
    lines.map { |line| "> #{line}" }.join("\n") + "\n\n"
  when 'hr' then "---\n\n"
  when 'table' then convert_table_to_markdown(element)
  when 'div', 'span', 'article', 'section', 'main'
    convert_children_to_markdown(element)
  else
    if element.text?
      element.text
    else
      convert_children_to_markdown(element)
    end
  end
end

def convert_children_to_markdown(element, is_ordered_list = false)
  result = +""
  list_counter = 1

  element.children.each do |child|
    if child.text?
      # Collapse excessive whitespace to reduce noise
      result << child.text.gsub(/\s+/, ' ')
    else
      chunk = convert_element_to_markdown(child)
      if is_ordered_list && child.name.downcase == 'li'
        chunk = chunk.sub(/^1\./, "#{list_counter}.")
        list_counter += 1
      end
      result << chunk
    end
  end

  result
end

def convert_table_to_markdown(table)
  rows = table.css('tr')
  return "" if rows.empty?

  md = +""
  rows.each_with_index do |row, idx|
    cells = row.css('th, td')
    row_text = cells.map { |c| c.text.strip.gsub('|', '\\|') }.join(' | ')
    md << "| #{row_text} |\n"
    if idx == 0 && row.css('th').any?
      md << "| #{Array.new(cells.length, '---').join(' | ')} |\n"
    end
  end
  md << "\n"
end

# Slice from the first markdown H1 ("# ") anywhere in the string (defensive).
def process_markdown_content(markdown_content)
  # Match start-of-string or newline, optional spaces, then "# "
  if (m = markdown_content.match(/(?:\A|\n)\s*#\s/))
    start = m.begin(0)
    start += 1 if markdown_content[start] == "\n" # drop leading newline if present
    markdown_content.slice(start..-1)
  else
    markdown_content
  end
end

# Combined the logic for URLs ending in "/" and other paths.
def construct_markdown_path(site_dest, page_url)
  # Handle the root index page specifically
  return File.join(site_dest, "index.html.md") if page_url == "/"

  # Remove the leading slash
  path_without_slash = page_url.sub(/\A\//, '')

  # If the URL ends with "/", it's a directory index page
  if page_url.end_with?("/")
    # Convert "/en/tutorials/" to "_site/en/tutorials/index.html.md"
    File.join(site_dest, path_without_slash + "index.html.md")
  else
    # For regular pages like "/page.html", convert to "_site/page.html.md"
    File.join(site_dest, path_without_slash + ".md")
  end
end