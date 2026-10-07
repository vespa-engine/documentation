# _plugins/rouge_xml_placeholders.rb
#
# Syntax overviews in the reference write placeholders such as [optional attributes] where a tag's
# attributes go. That is not XML, so Rouge's XML lexer marks it as an error. Colour a bracketed
# placeholder inside a tag as emphasis instead. Valid XML has no "[" there, so it is not affected.

require 'rouge'

Rouge::Lexers::XML.prepend :tag do
  rule %r/\[[^\]\n]*\]/, Rouge::Token::Tokens::Generic::Emph
end
