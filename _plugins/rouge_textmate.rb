# _plugins/rouge_textmate.rb
#
# Rouge lexers built from TextMate grammars, so that code blocks tagged with a Vespa language
# (```schema, {% highlight schema %}) are highlighted from the same grammar as the editors use.
# The grammars live in _grammars/ as unmodified copies of the ones in vespa-engine/vespa.
#
# A TextMate pattern list maps onto a Rouge state: at each position the patterns are tried in
# order, and text no pattern matches is emitted one character at a time. A begin/end rule pushes
# a state that tries the end pattern first, then the rule's own patterns. Scopes are mapped to the
# Rouge tokens styled in css/native.css.

require 'json'
require 'rouge'
require 'strscan'

module VespaTextMate
  # Scope prefixes, most specific first. A nil token means "use the token of the enclosing rule",
  # e.g. the quote characters of a string are coloured as the string.
  SCOPE_TOKENS = [
    ['punctuation.definition.comment',     nil],
    ['punctuation.definition.string',      nil],
    ['punctuation.definition.variable',    nil],
    ['meta.',                              nil],
    ['comment',                            Rouge::Token::Tokens::Comment::Single],
    ['string.quoted.double',               Rouge::Token::Tokens::Literal::String::Double],
    ['string.quoted.single',               Rouge::Token::Tokens::Literal::String::Single],
    ['string',                             Rouge::Token::Tokens::Literal::String],
    ['constant.character.escape',          Rouge::Token::Tokens::Literal::String::Escape],
    ['constant.numeric.float',             Rouge::Token::Tokens::Literal::Number::Float],
    ['constant.numeric.integer',           Rouge::Token::Tokens::Literal::Number::Integer],
    ['constant.numeric',                   Rouge::Token::Tokens::Literal::Number],
    ['keyword.declaration',                Rouge::Token::Tokens::Keyword::Declaration],
    ['keyword.operator',                   Rouge::Token::Tokens::Operator],
    ['keyword',                            Rouge::Token::Tokens::Keyword],
    ['storage.type',                       Rouge::Token::Tokens::Keyword::Type],
    ['storage.modifier',                   Rouge::Token::Tokens::Keyword],
    ['support.type',                       Rouge::Token::Tokens::Keyword::Type],
    ['support.variable',                   Rouge::Token::Tokens::Name],
    ['entity.name.type',                   Rouge::Token::Tokens::Name::Class],
    ['entity.other.inherited-class',       Rouge::Token::Tokens::Name::Class],
    ['entity.name.function.rank-feature',  Rouge::Token::Tokens::Name::Builtin],
    ['entity.name.function',               Rouge::Token::Tokens::Name::Function],
    ['variable.other.enummember',          Rouge::Token::Tokens::Name::Constant],
    ['variable.language',                  Rouge::Token::Tokens::Name::Variable],
    ['variable.parameter',                 Rouge::Token::Tokens::Name::Variable],
    ['punctuation',                        Rouge::Token::Tokens::Punctuation],
  ].freeze

  TEXT = Rouge::Token::Tokens::Text
  ANY_CHAR = /./m

  # Scopes in a grammar that SCOPE_TOKENS does not cover. These render as plain text.
  def self.unmapped_scopes
    @unmapped_scopes ||= Hash.new { |h, k| h[k] = [] }
  end

  def self.token_for(scope, lexer_tag)
    return nil if scope.nil?
    SCOPE_TOKENS.each do |prefix, token|
      return token if scope == prefix || scope.start_with?(prefix.end_with?('.') ? prefix : "#{prefix}.")
    end
    unmapped_scopes[lexer_tag] << scope unless unmapped_scopes[lexer_tag].include?(scope)
    nil
  end

  # Instance methods of the generated lexers.
  module LexerMethods
    # Scan the way a TextMate engine does, which the grammar's patterns are written for:
    # - One line at a time, keeping the state stack between lines, so that no match spans a
    #   line break and lookbehinds do not see the previous line.
    # - With fixed_anchor, so that \b and lookbehinds see the text before the scan position on
    #   the same line. Rouge's own scanner does not, so they would also match mid-word.
    # Otherwise the same as RegexLexer#stream_tokens in Rouge 3, without the debug output.
    def stream_tokens(str, &b)
      @output_stream = b
      @states = self.class.states
      @null_steps = 0
      str.each_line do |line|
        stream = @current_stream = StringScanner.new(line, fixed_anchor: true)
        until stream.eos?
          b.call(Rouge::Token::Tokens::Error, stream.getch) unless step(state, stream)
        end
      end
    end

    # Emit a match whose capture groups have their own tokens. Text between the captures gets
    # the token of the whole match. StringScanner does not expose group offsets, so the regex is
    # matched again at the same position of the full string. Regexp#match takes a character
    # offset, while StringScanner#pos is in bytes, hence charpos.
    def emit_captures(stream, regex, whole_token, capture_tokens)
      start = stream.charpos - stream.matched.length
      match = regex.match(stream.string, start)
      whole_token = capture_tokens.fetch(0, whole_token) || whole_token
      return token(whole_token) unless match && match.begin(0) == start
      pos = start
      groups = capture_tokens.keys.reject { |i| i.zero? || match.begin(i).nil? }
      groups.sort_by { |i| [match.begin(i), -match.end(i)] }.each do |i|
        b, e = match.begin(i), match.end(i)
        next if b < pos || b == e
        token(whole_token, match.string[pos...b]) if b > pos
        token(capture_tokens[i] || whole_token, match.string[b...e])
        pos = e
      end
      token(whole_token, match.string[pos...match.end(0)]) if match.end(0) > pos
    end
  end

  # Defines the states of lexer_class from the grammar at grammar_path. Rouge's state DSL methods
  # (rule, mixin) are protected, as they are meant to be called from a literal state block, so
  # they are called with send.
  class Builder
    def initialize(lexer_class, grammar_path)
      @lexer = lexer_class
      @tag = lexer_class.tag
      @grammar = JSON.parse(File.read(grammar_path))
      @inner_states = 0
    end

    def build
      @lexer.include(LexerMethods)
      @grammar.fetch('repository', {}).each do |name, rule|
        define_state(repository_state(name), [rule], TEXT, fallback: false)
      end
      define_state(:root, @grammar.fetch('patterns'), TEXT, fallback: true)
      # Rouge evaluates state definitions on first use. Load them all now, so that an invalid
      # regex or include fails the site build rather than the first page that uses the language.
      @lexer.state_definitions.keys.each { |name| @lexer.get_state(name) }
    end

    private

    def repository_state(name)
      :"repository_#{name}"
    end

    def define_state(name, rules, parent_token, fallback:, end_rule: nil)
      builder = self
      @lexer.state(name) do
        builder.send(:add_end_rule, self, *end_rule) if end_rule
        rules.each { |rule| builder.send(:add_rule, self, rule, parent_token) }
        rule(ANY_CHAR, parent_token) if fallback
      end
    end

    def add_rule(dsl, rule, parent_token)
      if rule['include']
        add_include(dsl, rule['include'])
      elsif rule['match']
        add_match_rule(dsl, rule, parent_token)
      elsif rule['begin']
        add_begin_end_rule(dsl, rule, parent_token)
      elsif rule['patterns']
        rule['patterns'].each { |r| add_rule(dsl, r, parent_token) }
      end
    end

    def add_include(dsl, reference)
      case reference
      when '$self', '$base' then dsl.send(:mixin, :root)
      when /\A#(.+)/        then dsl.send(:mixin, repository_state(Regexp.last_match(1)))
      else raise ArgumentError, "#{@tag}: unsupported include #{reference.inspect}"
      end
    end

    def add_match_rule(dsl, rule, parent_token)
      regex = Regexp.new(rule['match'])
      token = token_for(rule['name']) || parent_token
      captures = capture_tokens(rule['captures'])
      if captures.empty?
        dsl.send(:rule, regex, token)
      else
        dsl.send(:rule, regex) { |stream| emit_captures(stream, regex, token, captures) }
      end
    end

    def add_begin_end_rule(dsl, rule, parent_token)
      begin_regex = Regexp.new(rule['begin'])
      end_regex = Regexp.new(rule['end'])
      token = token_for(rule['name']) || parent_token
      content_token = token_for(rule['contentName']) || token
      begin_captures = capture_tokens(rule['beginCaptures'] || rule['captures'])
      end_captures = capture_tokens(rule['endCaptures'] || rule['captures'])

      inner = :"#{@tag}_inner_#{@inner_states += 1}"
      define_state(inner, rule.fetch('patterns', []), content_token, fallback: true,
                   end_rule: [end_regex, token, end_captures])
      dsl.send(:rule, begin_regex) do |stream|
        emit_captures(stream, begin_regex, token, begin_captures)
        push(inner)
      end
    end

    # The end pattern can match the empty string (e.g. "$"), so it is emitted only when non-empty.
    def add_end_rule(dsl, end_regex, token, captures)
      dsl.send(:rule, end_regex) do |stream|
        emit_captures(stream, end_regex, token, captures) unless stream.matched_size.zero?
        pop!
      end
    end

    def capture_tokens(captures)
      (captures || {}).each_with_object({}) do |(index, capture), tokens|
        tokens[index.to_i] = token_for(capture['name'])
      end
    end

    def token_for(scope)
      VespaTextMate.token_for(scope, @tag)
    end
  end

  def self.define(lexer_class, grammar_path)
    Builder.new(lexer_class, grammar_path).build
  end
end

module Rouge
  module Lexers
    class VespaSchema < RegexLexer
      title 'Vespa schema'
      desc 'Vespa schema language, from the TextMate grammar in vespa-engine/vespa'
      tag 'schema'
      aliases 'sd', 'vespa-schema'
      filenames '*.sd'

      VespaTextMate.define(self, File.expand_path('../_grammars/vespa-schema.tmLanguage.json', __dir__))
    end
  end
end

if defined?(Jekyll)
  VespaTextMate.unmapped_scopes.each do |tag, scopes|
    Jekyll.logger.warn 'Rouge TextMate:', "#{tag}: no token for scopes #{scopes.join(', ')}"
  end
end
