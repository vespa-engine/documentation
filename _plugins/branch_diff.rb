# Copyright Vespa.ai. All rights reserved.
#
# Local review aid for `jekyll serve`: append `?diff` to a page URL to see what
# the current branch changed on that page, compared to the merge-base of HEAD
# and origin/master. Use `?diff=<ref>` to compare against the merge-base with
# another ref instead.
#
# Changed and added elements are tinted, with the new words inside a changed
# element tinted more strongly. Removed text is not shown: a thin red marker
# shows where something was removed, and hovering over it shows what. Click a
# dashed marker to show the removed elements as they were rendered.
#
# The baseline page is rendered and diffed only when a request asks for it.
# Nothing is written to _site, and `jekyll build` is unaffected.

require 'cgi'
require 'nokogiri'
require 'open3'

module BranchDiff
  DEFAULT_REF = 'origin/master'.freeze

  # Elements that own the text directly inside them. Each text node belongs
  # to its nearest ancestor among these, and that group is the unit of diffing.
  BLOCKS = %w[p li dt dd h1 h2 h3 h4 h5 h6 pre td th caption blockquote figcaption summary div body].freeze
  SKIP = %w[script style noscript template].freeze

  # Upper bound for the word-level LCS table, to keep requests fast.
  MAX_CELLS = 4_000_000

  # Two blocks are treated as the same block edited if this many of their
  # words overlap (Dice coefficient).
  PAIR_THRESHOLD = 0.4

  # An inset shadow tints on top of an element's own background (such as a
  # code block's), where setting `background` would replace it.
  STYLE = <<~CSS.freeze
    .bd-added { box-shadow: inset 0 0 0 9999px rgba(45, 164, 78, 0.10); border-radius: 3px; }
    .bd-changed { box-shadow: inset 0 0 0 9999px rgba(212, 167, 44, 0.12); border-radius: 3px; }
    .bd-word { background: rgba(212, 167, 44, 0.30); border-radius: 2px; }
    /* Removal markers: a thin visible line inside a larger hit area (the
       padding), drawn above neighbouring elements so they can be hovered.
       Removed blocks sit in a <details>, opened by clicking its line. */
    span.bd-gap, details.bd-gap > summary { position: relative; z-index: 1; box-sizing: content-box; }
    span.bd-gap { display: inline-block; width: 2px; height: 1em; padding: 0 4px; margin: 0 -2px; cursor: help;
                  vertical-align: text-bottom; background: rgba(207, 34, 46, 0.55) content-box; }
    details.bd-gap { display: block; margin: 0; }
    details.bd-gap > summary { display: block; list-style: none; height: 2px; padding: 5px 0; cursor: pointer;
                               background: repeating-linear-gradient(90deg, rgba(207, 34, 46, 0.55) 0 6px,
                                                                     transparent 6px 10px) content-box; }
    details.bd-gap > summary::-webkit-details-marker { display: none; }
    span.bd-gap:hover, details.bd-gap > summary:hover { background-color: rgba(207, 34, 46, 0.9); }
    span.bd-gap:hover::after, details.bd-gap > summary:hover::after {
      content: attr(data-removed); position: absolute; left: 0; top: 100%; z-index: 100001;
      width: max-content; max-width: 480px; margin-top: 4px; padding: 6px 10px; border-radius: 4px;
      background: #24292f; color: #f6f8fa; font: 13px/1.4 sans-serif; font-weight: normal;
      white-space: normal; text-align: left; text-transform: none; pointer-events: none;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); }
    details.bd-gap[open] > summary:hover::after { content: "Click to hide the removed text."; }
    .bd-removed-content { margin: 4px 0 12px; padding: 4px 12px; border-left: 3px solid rgba(207, 34, 46, 0.55);
                          box-shadow: inset 0 0 0 9999px rgba(207, 34, 46, 0.06); }
    #bd-banner { position: fixed; right: 16px; bottom: 16px; z-index: 100000; max-width: 420px;
                 padding: 10px 14px; border-radius: 6px; font: 13px/1.4 sans-serif;
                 background: #24292f; color: #f6f8fa; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3); }
    #bd-banner a { color: #8cc4ff; }
    #bd-banner code { color: inherit; background: none; }
  CSS

  Block = Struct.new(:node, :text_nodes) do
    def text
      @text ||= text_nodes.map(&:text).join
    end

    def words
      @words ||= text.split(/\s+/).reject(&:empty?)
    end

    def key
      @key ||= "#{node.name}:#{words.join(' ')}"
    end

    # True when the block's element contains no other blocks, so it can be
    # marked as a whole.
    def leaf?
      !%w[body div].include?(node.name) && node.css(BLOCKS.join(',')).empty?
    end
  end

  @mutex = Mutex.new
  @cache = {}
  @site = nil

  class << self
    def built(site)
      @mutex.synchronize do
        @site = site
        @cache.clear
      end
    end

    # Called after the dev server has produced its normal response.
    def handle(req, res)
      ref = requested_ref(req)
      return if ref.nil? || @site.nil?
      return unless res.status == 200 && res['content-type'].to_s.start_with?('text/html')

      page = find_page(@site, req.path)
      return if page.nil?

      current = read_body(res)
      res.body = current
      html = @mutex.synchronize { render_diff(@site, page, ref, req.query['diff'].to_s, current) }
      res.body = html
      res.content_length = html.bytesize
    rescue StandardError => e
      Jekyll.logger.warn 'Branch diff:', "#{e.class}: #{e.message}"
      Jekyll.logger.debug 'Branch diff:', e.backtrace.join("\n")
    end

    private

    def requested_ref(req)
      value = req.query['diff']
      return nil if value.nil?

      value = value.to_s
      ref = (value.empty? || value == '1') ? DEFAULT_REF : value
      ref.match?(%r{\A[\w][\w./@^~-]*\z}) ? ref : nil
    end

    def find_page(site, path)
      candidates = [path, "#{path}.html", path.sub(/index\.html\z/, '')]
      site.pages.find do |p|
        candidates.include?(p.url) && File.file?(site.in_source_dir(p.relative_path))
      end
    end

    def read_body(res)
      body = res.body
      return body.to_s unless body.respond_to?(:read)

      begin
        body.read
      ensure
        body.close if body.respond_to?(:close)
      end
    end

    def git(dir, *args)
      out, status = Open3.capture2('git', '-C', dir, *args, err: File::NULL)
      status.success? ? out : nil
    end

    def render_diff(site, page, ref, param, current)
      base = git(site.source, 'merge-base', 'HEAD', ref).to_s.strip
      if base.empty?
        return Annotator.banner_only(current, "Could not find the merge-base of <code>HEAD</code> and <code>#{CGI.escapeHTML(ref)}</code>.")
      end

      label = "<code>#{CGI.escapeHTML(ref)}</code> (merge-base <code>#{base[0, 9]}</code>)"
      old_source = git(site.source, 'show', "#{base}:./#{page.relative_path}")
      if old_source.nil?
        return Annotator.banner_only(current, "This page does not exist at #{label}: it is new on this branch.")
      end

      old_html = (@cache[[base, page.relative_path]] ||= BaselinePage.new(site, page, old_source).render_output)
      Annotator.new(old_html, current, label, param).run
    end
  end

  # A copy of an existing page, with its source taken from a string (the file
  # at the baseline commit) instead of from disk.
  class BaselinePage < Jekyll::Page
    def initialize(site, page, source)
      @baseline_source = source
      super(site, site.source, page.instance_variable_get(:@dir), page.name)
    end

    def read_yaml(_base, _name, _opts = {})
      self.content = @baseline_source.dup.force_encoding(Encoding::UTF_8)
      match = Jekyll::Document::YAML_FRONT_MATTER_REGEXP.match(content)
      if match
        self.content = match.post_match
        self.data = SafeYAML.load(match[1])
      end
      self.data ||= {}
    end

    def render_output
      Jekyll::Renderer.new(site, self, site.site_payload).run
    end
  end

  class Annotator
    def self.banner_only(html, message)
      doc = Nokogiri::HTML(html)
      add_style_and_banner(doc, message)
      doc.to_html
    end

    def self.add_style_and_banner(doc, message)
      head = doc.at('head') || doc.root
      head.add_child(doc.create_element('style', STYLE))
      body = doc.at('body') || doc.root
      banner = Nokogiri::HTML.fragment("<div id=\"bd-banner\">#{message} <a href=\"?\">Hide diff</a></div>").children.first
      body.children.empty? ? body.add_child(banner) : body.children.first.add_previous_sibling(banner)
    end

    def initialize(old_html, new_html, label, param)
      @old = Nokogiri::HTML(old_html)
      @new = Nokogiri::HTML(new_html)
      @label = label
      @param = param
      @stats = Hash.new(0)
    end

    def run
      old_blocks = blocks(@old)
      new_blocks = blocks(@new)
      ops = BranchDiff::Lcs.diff(old_blocks.map(&:key), new_blocks.map(&:key))
      apply(ops, old_blocks, new_blocks)
      keep_diff_param_on_links

      summary = if @stats.empty?
                  "No changes on this page relative to #{@label}."
                else
                  "Changes relative to #{@label}: #{@stats[:changed]} changed, " \
                    "#{@stats[:added]} added, #{@stats[:removed]} removed blocks."
                end
      self.class.add_style_and_banner(@new, summary)
      @new.to_html
    end

    private

    def blocks(doc)
      groups = {}
      doc.xpath('//body//text()').each do |t|
        next if t.text.strip.empty?
        next if t.ancestors.any? { |a| SKIP.include?(a.name) }

        owner = t.ancestors.find { |a| BLOCKS.include?(a.name) }
        next if owner.nil?

        (groups[owner] ||= Block.new(owner, [])).text_nodes << t
      end
      groups.values
    end

    # Walks the block-level edit script. Runs of deletions and insertions
    # between unchanged blocks form a hunk.
    def apply(ops, old_blocks, new_blocks)
      dels = []
      inss = []
      prev_new = nil
      flush = lambda do |next_new|
        apply_hunk(dels.map { |i| old_blocks[i] }, inss.map { |j| new_blocks[j] }, prev_new, next_new)
        prev_new = inss.empty? ? prev_new : new_blocks[inss.last]
        dels = []
        inss = []
      end
      ops.each do |op, i, j|
        case op
        when :del then dels << i
        when :ins then inss << j
        else
          flush.call(new_blocks[j]) unless dels.empty? && inss.empty?
          prev_new = new_blocks[j]
        end
      end
      flush.call(nil) unless dels.empty? && inss.empty?
    end

    def apply_hunk(dels, inss, prev_new, next_new)
      di = 0
      inss.each do |ins|
        match = (di...dels.size).find { |k| similarity(dels[k], ins) >= PAIR_THRESHOLD }
        if match
          show_removed(dels[di...match], ins, nil)
          show_changed(dels[match], ins)
          di = match + 1
        else
          show_added(ins)
        end
      end
      show_removed(dels[di..], next_new, inss.last || prev_new)
    end

    def similarity(a, b)
      wa = a.words.uniq
      wb = b.words.uniq
      return 0.0 if wa.empty? || wb.empty?

      2.0 * (wa & wb).size / (wa.size + wb.size)
    end

    def show_added(block)
      @stats[:added] += 1
      highlight(block, 'bd-added')
    end

    # Tints the block, and the words in it that are new or reworded.
    def show_changed(old_block, new_block)
      @stats[:changed] += 1
      highlight(new_block, 'bd-changed')

      ow = old_block.words
      nw = new_block.words
      return if ow.size * nw.size > MAX_CELLS

      inserted = {}
      removed_before = Hash.new { |h, k| h[k] = [] }
      BranchDiff::Lcs.diff(ow, nw).each_with_object([0]) do |(op, i, j), pos|
        case op
        when :ins then inserted[j] = true
                       pos[0] = j + 1
        when :del then removed_before[pos[0]] << ow[i]
        else pos[0] = j + 1
        end
      end

      # Replaced words are shown by tinting the new ones, so a removal marker
      # is only needed where nothing took their place.
      w = 0
      new_block.text_nodes.each_with_index do |text_node, k|
        tokens = text_node.text.scan(/\s+|\S+/)
        segments = []
        tokens.each_with_index do |tok, x|
          if tok.match?(/\A\s/)
            # Whitespace between two new words joins them into one tinted span.
            joined = w.positive? && inserted[w - 1] && inserted[w] && tokens[x + 1]
            segments << [joined ? :word : :text, tok]
            next
          end
          segments << [:gap, removed_before[w].join(' ')] unless removed_before[w].empty? || inserted[w]
          segments << [inserted[w] ? :word : :text, tok]
          w += 1
        end
        if k == new_block.text_nodes.size - 1 && !removed_before[w].empty? && !inserted[w - 1]
          segments << [:gap, removed_before[w].join(' ')]
        end
        replace_text(text_node, segments)
      end
    end

    # Marks where blocks were removed, next to `before` (or after `after` when
    # there is nothing left to place them before).
    def show_removed(removed, before, after)
      return if removed.empty?

      @stats[:removed] += removed.size
      anchor = before || after
      return if anchor.nil?

      if anchor.leaf? && !%w[td th].include?(anchor.node.name)
        marker = removed_details(removed)
        before ? anchor.node.add_previous_sibling(marker) : anchor.node.add_next_sibling(marker)
      else
        marker = gap_marker(removed.map { |b| b.words.join(' ') }.join(' '))
        # A block placed before has not been annotated yet, so its first text
        # node is still in the tree. A block placed after may have been.
        before ? anchor.text_nodes.first.add_previous_sibling(marker) : anchor.node.add_child(marker)
      end
    end

    # A dashed line that, when clicked, shows the removed blocks as they were
    # rendered.
    def removed_details(removed)
      words = removed.sum { |b| b.words.size }
      preview = removed.first.words.first(25).join(' ')
      preview += ' …' if words > 25
      details = @new.create_element('details', class: 'bd-gap')
      details.add_child(@new.create_element('summary', 'data-removed': "Removed: #{preview} (#{words} words, click to show)"))
      content = details.add_child(@new.create_element('div', class: 'bd-removed-content'))
      removed.each do |block|
        copy = removed_copy(block)
        last = content.children.last
        # Keep consecutive removed list items in one list.
        if %w[ul ol].include?(copy.name) && last&.name == copy.name
          last.add_child(copy.children.first)
        else
          content.add_child(copy)
        end
      end
      details
    end

    def removed_copy(block)
      copy = if block.leaf? && !%w[td th].include?(block.node.name)
               block.node.dup(1, @new)
             else
               @new.create_element('p', block.words.join(' '))
             end
      copy.xpath('descendant-or-self::*[@id]').each { |n| n.remove_attribute('id') }
      return copy unless copy.name == 'li'

      list = @new.create_element(block.node.parent&.name == 'ol' ? 'ol' : 'ul')
      list.add_child(copy)
      list
    end

    # A thin line within the text where words were removed. Hovering over it
    # shows them.
    def gap_marker(text)
      text = "#{text[0, 600]} …" if text.size > 600
      @new.create_element('span', class: 'bd-gap', 'data-removed': "Removed: #{text}")
    end

    def replace_text(text_node, segments)
      merged = segments.each_with_object([]) do |(type, s), acc|
        if acc.last && acc.last[0] == type
          acc.last[1] += s
        else
          acc << [type, s.dup]
        end
      end
      merged.each do |type, s|
        node = case type
               when :text then @new.create_text_node(s)
               when :gap then gap_marker(s)
               else @new.create_element('span', s, class: 'bd-word')
               end
        text_node.add_previous_sibling(node)
      end
      text_node.remove
    end

    # Marks the whole element when it contains no other blocks. Otherwise only
    # its own text is marked, so nested blocks are not marked with it.
    def highlight(block, cls)
      if block.leaf?
        add_class(block.node, cls)
      else
        block.text_nodes.each { |t| t.wrap("<span class=\"#{cls}\"></span>") }
      end
    end

    def add_class(node, cls)
      node['class'] = [node['class'], cls].compact.join(' ')
    end

    # Keeps diff mode on when following links within the site.
    def keep_diff_param_on_links
      query = @param.empty? ? 'diff' : "diff=#{CGI.escape(@param)}"
      @new.css('a[href]').each do |a|
        href = a['href']
        next if href.start_with?('#') || href.include?('?') || href.match?(%r{\A[a-z][a-z0-9+.-]*:|\A//}i)

        path, fragment = href.split('#', 2)
        a['href'] = "#{path}?#{query}#{fragment ? "##{fragment}" : ''}"
      end
    end
  end

  # Longest common subsequence edit script over two arrays. Returns
  # [:eq, i, j], [:del, i, nil] and [:ins, nil, j] in document order.
  module Lcs
    def self.diff(a, b)
      prefix = 0
      prefix += 1 while prefix < a.size && prefix < b.size && a[prefix] == b[prefix]
      suffix = 0
      suffix += 1 while suffix < a.size - prefix && suffix < b.size - prefix &&
                        a[a.size - 1 - suffix] == b[b.size - 1 - suffix]

      ops = (0...prefix).map { |k| [:eq, k, k] }
      ops.concat(middle(a, b, prefix, a.size - suffix, b.size - suffix))
      ops.concat((0...suffix).map { |k| [:eq, a.size - suffix + k, b.size - suffix + k] })
    end

    def self.middle(a, b, start, a_end, b_end)
      n = a_end - start
      m = b_end - start
      # table[i][j]: LCS length of a[start+i..] and b[start+j..]
      table = Array.new(n + 1) { Array.new(m + 1, 0) }
      (n - 1).downto(0) do |i|
        row = table[i]
        below = table[i + 1]
        ai = a[start + i]
        (m - 1).downto(0) do |j|
          row[j] = ai == b[start + j] ? below[j + 1] + 1 : [below[j], row[j + 1]].max
        end
      end
      ops = []
      i = 0
      j = 0
      while i < n && j < m
        if a[start + i] == b[start + j]
          ops << [:eq, start + i, start + j]
          i += 1
          j += 1
        elsif table[i + 1][j] >= table[i][j + 1]
          ops << [:del, start + i, nil]
          i += 1
        else
          ops << [:ins, nil, start + j]
          j += 1
        end
      end
      (i...n).each { |k| ops << [:del, start + k, nil] }
      (j...m).each { |k| ops << [:ins, nil, start + k] }
      ops
    end
  end

  module ServletPatch
    def do_GET(req, res) # rubocop:disable Naming/MethodName
      rtn = super
      BranchDiff.handle(req, res)
      rtn
    end
  end

  # The dev server's servlet is loaded only by `jekyll serve`, after the
  # initial build. Patch it at that point, so `jekyll build` never touches it.
  module ServeSetup
    private

    def setup(destination)
      super
      servlet = Jekyll::Commands::Serve::Servlet
      servlet.prepend(ServletPatch) unless servlet < ServletPatch
    end
  end
end

Jekyll::Commands::Serve.singleton_class.prepend(BranchDiff::ServeSetup)

Jekyll::Hooks.register :site, :post_write do |site|
  BranchDiff.built(site)
end
