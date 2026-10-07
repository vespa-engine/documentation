# _plugins/rouge_json_excerpts.rb
#
# JSON in the documentation is often an excerpt: "..." (or "..") stands for left-out content, and a
# list of objects from a larger response is written with commas between them, without the enclosing
# array. Rouge's JSON lexer marks both as errors. Colour them as punctuation instead. Neither occurs
# in valid JSON outside a string, so valid JSON is not affected.

require 'rouge'

Rouge::Lexers::JSON.prepend :root do
  rule %r/\.{2,}|…/, Rouge::Token::Tokens::Punctuation
  rule %r/,/, Rouge::Token::Tokens::Punctuation
end

[:object, :array].each do |state|
  Rouge::Lexers::JSON.prepend state do
    rule %r/\.{2,}|…/, Rouge::Token::Tokens::Punctuation
  end
end
