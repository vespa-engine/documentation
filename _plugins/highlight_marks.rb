# _plugins/highlight_marks.rb
#
# Keeps markup in {% highlight %} blocks, so that code can be both syntax highlighted and have
# parts marked in yellow, linked, or emphasised, as plain <pre> blocks can:
#
#   <pre>{% highlight vespa-schema-language %}
#   field title type string {
#       indexing: summary | <span class="pre-hilite">index</span>
#       # See <a href="../rag/embedding.html">embedding</a>
#   }
#   {% endhighlight %}</pre>
#
# The kept markup is <span class="pre-hilite">, <a ...>, <em>, <b>, <strong> and <i>. It is removed
# before the code is lexed, and put back around the same characters in the highlighted output,
# splitting a token where markup starts or ends inside it. Markup may be nested. Code with a tag
# that is not closed is highlighted as it is.

require 'rouge'

module HighlightMarks
  TAG = %r{(?<open><span class="pre-hilite">|<a\s[^>]*>|<(?:em|b|strong|i)>)|</(?<close>span|a|em|b|strong|i)>}

  # A range of the code without markup, and the tags that went around it.
  Mark = Struct.new(:range, :open, :close)

  # Returns the code without markup, and the marks. A closing tag with no opening tag is code.
  def self.extract(code)
    plain = +''
    marks = []
    open_tags = []
    pos = 0
    while (m = TAG.match(code, pos))
      plain << code[pos...m.begin(0)]
      if m[:open]
        open_tags << [m[:open][/\A<(\w+)/, 1], m[:open], plain.length]
      elsif open_tags.last && open_tags.last[0] == m[:close]
        _, open, start = open_tags.pop
        marks << Mark.new(start...plain.length, open, m[0])
      else
        plain << m[0]
      end
      pos = m.end(0)
    end
    plain << code[pos..]
    open_tags.empty? ? [plain, marks] : [code, []]
  end

  # Formats tokens like Rouge's HTML formatter, with the marks around their ranges.
  def self.format(tokens, marks)
    formatter = Rouge::Formatters::HTML.new
    cuts = marks.flat_map { |m| [m.range.begin, m.range.end] }.uniq.sort
    outer_first = marks.sort_by { |m| [m.range.begin, -m.range.end] }
    out = +''
    offset = 0
    active = []
    tokens.each do |token, value|
      next if value.empty?

      stop = offset + value.length
      bounds = cuts.select { |c| c > offset && c < stop }
      ([offset] + bounds).zip(bounds + [stop]).each do |from, to|
        wanted = outer_first.select { |m| m.range.cover?(from) }
        kept = active.zip(wanted).take_while { |a, w| a.equal?(w) }.length
        active[kept..].reverse_each { |m| out << m.close }
        wanted[kept..].each { |m| out << m.open }
        active = wanted
        out << formatter.span(token, value[(from - offset)...(to - offset)])
      end
      offset = stop
    end
    active.reverse_each { |m| out << m.close }
    out
  end

  # Replaces Jekyll's Rouge rendering for blocks that contain markup.
  module HighlightBlock
    private

    def render_rouge(code)
      return super if @highlight_options[:linenos] || !TAG.match?(code)

      plain, marks = HighlightMarks.extract(code)
      return super if marks.empty?

      lexer = ::Rouge::Lexer.find_fancy(@lang, plain) || Rouge::Lexers::PlainText
      HighlightMarks.format(lexer.lex(plain), marks)
    end
  end
end

Jekyll::Tags::HighlightBlock.prepend(HighlightMarks::HighlightBlock) if defined?(Jekyll::Tags::HighlightBlock)
