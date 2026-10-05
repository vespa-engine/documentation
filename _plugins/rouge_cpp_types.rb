# _plugins/rouge_cpp_types.rb
#
# Rouge's C++ lexer leaves type names as plain names, so C++ examples get much less colour than
# the same code in Java. Colour capitalised names as types, with the rule Rouge's Java lexer uses
# for class names. NULL is left to the C++ lexer.

require 'rouge'

Rouge::Lexers::Cpp.prepend :statements do
  rule %r/\b(?!NULL\b)[[:upper:]][[:alnum:]]*\b/, Rouge::Token::Tokens::Name::Class
end
