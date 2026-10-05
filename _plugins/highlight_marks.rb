# _plugins/highlight_marks.rb
#
# Keeps <span class="pre-hilite"> marks in {% highlight %} blocks, so that code can be both syntax
# highlighted and have parts marked in yellow, as plain <pre> blocks do:
#
#   <pre>{% highlight vespa-schema-language %}
#   field title type string {
#       indexing: summary | <span class="pre-hilite">index</span>
#   }
#   {% endhighlight %}</pre>
#
# The marks are removed before the code is lexed, and put back around the same characters in the
# highlighted output, splitting a token where a mark starts or ends inside it.

require 'rouge'

module HighlightMarks
  OPEN = '<span class="pre-hilite">'
  CLOSE = '</span>'

  # Returns the code without marks, and the character ranges the marks covered.
  def self.extract(code)
    plain = +''
    ranges = []
    pos = 0
    while (open = code.index(OPEN, pos)) && (close = code.index(CLOSE, open + OPEN.length))
      plain << code[pos...open]
      start = plain.length
      plain << code[(open + OPEN.length)...close]
      ranges << (start...plain.length)
      pos = close + CLOSE.length
    end
    plain << code[pos..]
    [plain, ranges]
  end

  # Formats tokens like Rouge's HTML formatter, with a mark around each marked range.
  def self.format(tokens, ranges)
    formatter = Rouge::Formatters::HTML.new
    cuts = ranges.flat_map { |r| [r.begin, r.end] }
    out = +''
    offset = 0
    marked = false
    tokens.each do |token, value|
      next if value.empty?

      piece_start = offset
      bounds = cuts.select { |c| c > offset && c < offset + value.length }.uniq.sort
      ([offset] + bounds).zip(bounds + [offset + value.length]).each do |from, to|
        inside = ranges.any? { |r| r.cover?(from) }
        out << (inside ? OPEN : CLOSE) if inside != marked
        marked = inside
        out << formatter.span(token, value[(from - piece_start)...(to - piece_start)])
      end
      offset += value.length
    end
    out << CLOSE if marked
    out
  end

  # Replaces Jekyll's Rouge rendering for blocks that contain marks.
  module HighlightBlock
    private

    def render_rouge(code)
      return super unless code.include?(OPEN) && !@highlight_options[:linenos]

      plain, ranges = HighlightMarks.extract(code)
      lexer = ::Rouge::Lexer.find_fancy(@lang, plain) || Rouge::Lexers::PlainText
      HighlightMarks.format(lexer.lex(plain), ranges)
    end
  end
end

Jekyll::Tags::HighlightBlock.prepend(HighlightMarks::HighlightBlock) if defined?(Jekyll::Tags::HighlightBlock)
