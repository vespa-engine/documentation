# Checks the Rouge lexers that _plugins/rouge_textmate.rb builds from the grammars in _grammars/,
# the C++ lexer extension in _plugins/rouge_cpp_types.rb, the console lexer adaptation in
# _plugins/rouge_console.rb, and the markup kept in highlighted code by _plugins/highlight_marks.rb.
#
# Run from the repository root:
#   bundle exec ruby test/test_rouge_lexers.rb

require 'cgi'
require 'rouge'
require_relative '../_plugins/rouge_textmate'
require_relative '../_plugins/rouge_cpp_types'
require_relative '../_plugins/rouge_console'
require_relative '../_plugins/highlight_marks'

SCHEMA_SAMPLE = <<~'SD'
  # A schema with the main constructs
  schema music inherits base {
      document music {
          field title type string {
              indexing: summary | index
              index: enable-bm25
          }
          field embedding type tensor<float>(x[384]) {
              indexing {
                  input title | embed e5 | attribute
              }
              attribute {
                  distance-metric: angular
              }
          }
          field tags type array<string> {
              indexing: attribute
              match: exact
          }
      }
      rank-profile hybrid inherits default {
          inputs {
              query(q) tensor<float>(x[384])
          }
          first-phase {
              expression: bm25(title) + 0.5 * closeness(field, embedding)
          }
          match-features: bm25(title)
      }
  }
SD

# [text in the sample, occurrence (1-based), expected token]. The token of the first character of
# that occurrence is checked.
SCHEMA_EXPECTATIONS = [
  ['# A schema',     1, 'Comment.Single'],
  ['schema',         2, 'Keyword.Declaration'],
  ['music',          1, 'Name.Class'],
  ['base',           1, 'Name.Class'],
  ['field',          1, 'Keyword.Declaration'],
  ['string',         1, 'Keyword.Type'],
  ['summary',        1, 'Keyword.Type'],
  ['|',              1, 'Operator'],
  ['tensor',         1, 'Keyword'],
  ['float',          1, 'Keyword.Type'],
  ['384',            1, 'Literal.Number'],
  ['embed',          2, 'Name.Function'],
  ['angular',        1, 'Name.Constant'],
  ['array',          1, 'Keyword.Type'],
  ['exact',          1, 'Name.Constant'],
  ['rank-profile',   1, 'Keyword.Declaration'],
  ['hybrid',         1, 'Name.Function'],
  ['first-phase',    1, 'Keyword'],
  ['bm25',           2, 'Name.Builtin'],
  ['0.5',            1, 'Literal.Number.Float'],
  ['closeness',      1, 'Name.Builtin'],
  ['match-features', 1, 'Keyword'],
].freeze

YQL_SAMPLE = <<~'YQL'
  select id from music where ({targetHits: 10}nearestNeighbor(embedding, q)) and year >= 2000
  | all(group(time.year(ts)) each(output(count()))) # count per year
  select * from music where text contains text(@query)
  all(group(genre) filter(in(genre, "rock")) each(output(count())))
YQL

YQL_EXPECTATIONS = [
  ['select',          1, 'Keyword'],
  ['music',           1, 'Name'],
  ['10',              1, 'Literal.Number'],
  ['nearestNeighbor', 1, 'Name.Function'],
  ['and',             1, 'Operator.Word'],
  ['>=',              1, 'Operator'],
  ['all',             1, 'Keyword'],
  ['time',            1, 'Name.Class'],
  ['count',           1, 'Name.Function'],
  ['# count',         1, 'Comment.Single'],
  ['@query',          1, 'Name.Variable'],
  ['all',             2, 'Keyword'],                   # grouping on its own, without "|"
  ['in(genre',        1, 'Operator.Word'],
].freeze

CPP_SAMPLE = <<~'CPP'
  ConfigSubscriber subscriber;
  ConfigHandle<FooConfig>::UP fooHandle = subscriber.subscribe<FooConfig>(configId);
  if (fooHandle->isChanged() && config != NULL) {
      std::unique_ptr<FooConfig> foo = fooHandle->getConfig();
  }
CPP

CPP_EXPECTATIONS = [
  ['ConfigSubscriber', 1, 'Name.Class'],
  ['FooConfig',        1, 'Name.Class'],
  ['subscriber',       1, 'Name'],
  ['if',               1, 'Keyword'],
  ['NULL',             1, 'Name.Builtin'],
].freeze

CONSOLE_SAMPLE = <<~'SH'
  $ vespa-sentinel-cmd list
  container state=RUNNING mode=AUTO id="default/container.0"
  # Find DEBUG log messages for component creation, like:
  $ curl -s -H "Content-Type: application/json" \
    --data @feed.json \
    http://localhost:8080/document/v1/
  $ vespa query 'yql=select * from music
    where artist contains "coldplay"'
  [2021-01-07 10:13:37.006] DEBUG : container > a; b
SH

CONSOLE_EXPECTATIONS = [
  ['$',              1, 'Generic.Prompt'],
  ['container state', 1, 'Generic.Output'],
  ['# Find',         1, 'Comment'],
  ['--data',         1, 'Name.Tag'],                   # continues the command after "\"
  ['where artist',   1, 'Literal.String.Single'],      # continues the quoted argument
  ['[2021',          1, 'Generic.Output'],
  ['> a; b',         1, 'Generic.Output'],             # not a prompt
].freeze

def check_lexer(tag, sample, expectations, failures)
  lexer = Rouge::Lexer.find(tag)
  return failures << "#{tag}: no lexer registered" unless lexer

  tokens = []
  lexer.new.lex(sample).each { |token, value| value.each_char { tokens << token } }
  text = sample.chars

  errors = text.each_index.select { |i| tokens[i] == Rouge::Token::Tokens::Error }
  failures << "#{tag}: error tokens at #{errors.map { |i| text[i].inspect }.join(', ')}" unless errors.empty?
  failures << "#{tag}: lexed text differs from the input" unless tokens.size == text.size

  expectations.each do |snippet, occurrence, expected|
    index = -1
    occurrence.times { index = sample.index(snippet, index + 1) or break }
    next failures << "#{tag}: #{snippet.inspect} occurrence #{occurrence} not in sample" unless index

    actual = tokens[index]&.qualname
    failures << "#{tag}: #{snippet.inspect} (#{occurrence}) is #{actual}, expected #{expected}" unless actual == expected
  end
end

# [language, code with markup, [opening tag, text inside it] for each kept tag, outermost first]
MARK_CASES = [
  # A mark around one token
  ['vespa-schema-language', %(field title type string {\n    indexing: summary | <span class="pre-hilite">index</span>\n}\n),
   [['<span class="pre-hilite">', 'index']]],
  # Marks that start and end inside tokens, and a mark across lines
  ['java', %(String na<span class="pre-hilite">me = "Hel</span>lo";\n<span class="pre-hilite">int a;\nint b;</span>\n),
   [['<span class="pre-hilite">', 'me = "Hel'], ['<span class="pre-hilite">', "int a;\nint b;"]]],
  # A link, and a link inside a mark
  ['vespa-schema-language', %(indexing: input myField | <a href="../rag/embedding.html">embed</a> | attribute\n),
   [['<a href="../rag/embedding.html">', 'embed']]],
  ['vespa-schema-language', %(<span class="pre-hilite">field <a href="#title">title</a> type string</span> {\n}\n),
   [['<span class="pre-hilite">', 'field title type string'], ['<a href="#title">', 'title']]],
  # Emphasis inside an XML attribute value
  ['xml', %(<node hostalias="<em>node1</em>"/>\n), [['<em>', 'node1']]],
  # A closing tag without an opening tag is code, and a tag that is not closed leaves the code as it is
  ['java', %(String s = "</b>";\n), []],
  ['java', %(String s = "<em>x";\n), []],
].freeze

# Returns [opening tag, text inside it] for each kept tag in the HTML, outermost first.
def kept_tags(html)
  found = []
  open = []
  html.scan(%r{<(/?)(\w+)[^>]*>|[^<]+}) do
    tag = Regexp.last_match[0]
    if !tag.start_with?('<')
      open.each { |entry| entry[1] << CGI.unescapeHTML(tag) }
    elsif Regexp.last_match[1].empty?
      entry = [tag, +'']
      found << entry if tag.match?(/\A<(a\s|em>|b>|strong>|i>|span class="pre-hilite">)/)
      open << entry
    else
      open.pop
    end
  end
  found
end

def check_marks(lang, code, expected, failures)
  plain, marks = HighlightMarks.extract(code)
  html = HighlightMarks.format(Rouge::Lexer.find(lang).new.lex(plain), marks)
  failures << "marks (#{lang}): highlighted text differs from the code" unless CGI.unescapeHTML(html.gsub(/<[^>]+>/, '')) == plain
  actual = kept_tags(html)
  failures << "marks (#{lang}): kept #{actual.inspect}, expected #{expected.inspect}" unless actual == expected
end

failures = VespaTextMate.unmapped_scopes.map { |tag, scopes| "#{tag}: no token for scopes #{scopes.join(', ')}" }
check_lexer('vespa-schema-language', SCHEMA_SAMPLE, SCHEMA_EXPECTATIONS, failures)
check_lexer('vespa-yql', YQL_SAMPLE, YQL_EXPECTATIONS, failures)
check_lexer('cpp', CPP_SAMPLE, CPP_EXPECTATIONS, failures)
check_lexer('console', CONSOLE_SAMPLE, CONSOLE_EXPECTATIONS, failures)
MARK_CASES.each { |lang, code, marks| check_marks(lang, code, marks, failures) }

if failures.empty?
  puts 'Rouge lexers OK'
else
  puts failures
  exit 1
end
