# _plugins/rouge_schema_placeholders.rb
#
# Syntax overviews in the schema reference write placeholders such as [name] and [type-name]
# where a schema has its own names and values. Rouge's schema lexer colours the words in them as
# schema, e.g. "type" in [type-name] as a keyword. Colour a bracketed placeholder as emphasis
# instead, in every state of the lexer, as a placeholder can stand anywhere.
#
# A placeholder starts with a letter, and does not follow a name, a closing bracket or the type of
# a tensor literal, so that tensor dimensions (x[384]) and tensor values (tensor(x[2]):[a, b]) are
# not affected.

require 'rouge'
require_relative 'rouge_textmate'

Rouge::Lexers::VespaSchema.state_definitions.keys.each do |state|
  Rouge::Lexers::VespaSchema.prepend state do
    rule %r/(?<![\w)\]}])(?<!\):)\[[A-Za-z][^\]\n]*\]/, Rouge::Token::Tokens::Generic::Emph
  end
end
