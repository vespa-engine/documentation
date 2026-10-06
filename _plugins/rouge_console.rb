# _plugins/rouge_console.rb
#
# Adapts Rouge's console lexer to how the docs write terminal sessions:
#
#   $ vespa deploy --wait 300 app
#   # Wait for the application to start
#   Deployed app ...
#
# - Only lines starting with "$" are commands. Rouge also treats any line containing #, > or ; as a
#   prompt, which makes output lines into commands. Its prompt option cannot be given in a
#   {% highlight %} tag.
# - Lines starting with "#" are comments.
# - A command continues on the next lines while it ends with "\" or leaves a quote open. Rouge
#   treats those lines as output.

require 'rouge'

module DocsConsole
  def prompt_regex
    /\A[ \t]*\$(?=[ \t]|$)/
  end

  def allow_comments?
    true
  end

  def reset!
    super
    @continued = false
  end

  def process_line(input, &output)
    if @continued
      input.scan(line_regex)
      lang_lexer.continue_lex(input[0], &output)
    else
      super
      return unless prompt_regex.match?(input[0])
    end
    @continued = input[0].rstrip.end_with?('\\') || lang_lexer.stack.length > 1
  end
end

Rouge::Lexers::ConsoleLexer.prepend(DocsConsole)
