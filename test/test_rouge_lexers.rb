# Checks the Rouge lexers that _plugins/rouge_textmate.rb builds from the grammars in _grammars/,
# and the C++ lexer extension in _plugins/rouge_cpp_types.rb.
#
# Run from the repository root:
#   bundle exec ruby test/test_rouge_lexers.rb

require 'rouge'
require_relative '../_plugins/rouge_textmate'
require_relative '../_plugins/rouge_cpp_types'

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

failures = VespaTextMate.unmapped_scopes.map { |tag, scopes| "#{tag}: no token for scopes #{scopes.join(', ')}" }
check_lexer('vespa-schema-language', SCHEMA_SAMPLE, SCHEMA_EXPECTATIONS, failures)
check_lexer('cpp', CPP_SAMPLE, CPP_EXPECTATIONS, failures)

if failures.empty?
  puts 'Rouge lexers OK'
else
  puts failures
  exit 1
end
