# Grammars for syntax highlighting

TextMate grammars used to highlight Vespa languages in code blocks. `_plugins/rouge_textmate.rb`
turns each grammar into a Rouge lexer when the site is built.

| File | Language tags | Source |
|------|---------------|--------|
| `vespa-schema.tmLanguage.json` | `schema`, `sd`, `vespa-schema` | [vespa-engine/vespa: integration/tmgrammar/grammars/vespa-schema.tmLanguage.json](https://github.com/vespa-engine/vespa/blob/master/integration/tmgrammar/grammars/vespa-schema.tmLanguage.json) |

The grammars are unmodified copies. Do not edit them here: change the grammar in vespa-engine/vespa
and copy the new version to this directory.

`test/test_rouge_lexers.rb` checks that each grammar loads, that all its scopes map to a token, and
that a sample of each language is highlighted as expected.
