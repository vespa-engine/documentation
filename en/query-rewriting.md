---
# Copyright Vespa.ai. All rights reserved.
title: "Query Rewriting"
---

A search application can improve the quality by interpreting the intended meaning of the user queries.
Once the meaning is guessed,
the query can be rewritten to one that will satisfy the user better than the raw query.
Vespa includes a query rewriting language which makes it easy to use query
rewriting to understand and act upon the query semantics.

These query rewriting techniques can be combined to improve the search experience:
* Query focusing: Decide a field to search for a term
* Query enhancing: Add additional terms which improves the query
* Stopwords: Remove terms which hurts recall or precision -
  [example](https://github.com/vespa-cloud/cord-19-search/blob/main/src/main/java/ai/vespa/example/cord19/searcher/BoldingSearcher.java)
* Synonyms: Replace terms or phrases by others

Query rewriting done by *semantic rules* or *searchers*.
Semantic rules is a simple production rule language that operates on queries.
For more complex query rewriting logic which could not be handled by simple rules,
one could create a rewriting searcher making use of the query rewriting framework.

## EQUIV

EQUIV is a query operator that can be used to add synonyms
for words where the various synonyms should be equivalent - example:
* The user query is `(used AND automobile)`
* *automobile* is a synonym for *car* (from a dictionary)
* Rewrite the query to `(used AND (automobile EQUIV car))`
* *automobile* or *car* are here equivalent -
  the query shall behave as if all occurrences of *car* in the document corpus
  had been replaced by *automobile*

See the [reference](reference/query-language-reference.html#equiv)
for differences between OR and EQUIV.
In many cases it might be better to use OR instead of EQUIV.
Example *Snoop* Dogg:

```
"Snoop" EQUIV "Snoop Doggy Dogg" EQUIV "Snoop Lion" EQUIV "Calvin Broadus" EQUIV "Calvin Cordozar Broadus Junior"
```

However, *Snoop* is used by other people -
so matching that alone is not a sure hit for the correct entity,
and finding more than one of the synonyms in the same text gives better confidence.
This is exactly what OR does:

```
"Snoop"!20 OR "Snoop Doggy Dogg"!90 OR "Snoop Lion"!75 OR "Calvin Broadus"!60 OR "Calvin Cordozar Broadus Junior"!100
```

Use lower weights on the alternatives with less confidence.
If it looks like the many words and phrases inside the OR
overwhelms other words in the query, giving even lower weights may be useful,
for example making the sum of weights 100 - the default weight for just one alternative.

The decision to use EQUIV must be taken by application-specific dictionary or linguistics use.
This can be done using [YQL](reference/query-language-reference.html#equiv)
or from a container plugin (example
[EquivSearcher.java](https://github.com/vespa-engine/sample-apps/blob/master/album-recommendation-java/src/main/java/ai/vespa/example/album/EquivSearcher.java)) where the query object is manipulated as follows:

1. Find a word item in the query
2. Check that an EQUIV can be used in that place
   (see [limitations](reference/query-language-reference.html#equiv))
3. Find the synonyms in the dictionary
4. Make an `EquivItem` with the synonyms (and the original word) as children
5. Replace the original `WordItem` with the new `EquivItem`

## Rules

A simple semantic rule looks like:

```
lotr -> lord of the rings;
```

This means that whenever the term *lotr* is encountered in a query,
replace it by the terms *lord of the rings*.
Rules can also refer to conditions, and the produced terms can be a
modified version of whatever is matched instead of a concrete term:

```
[brand] -> company:[brand];
[brand] :- sony, dell, ibm, hp;
```

This rule says that, whenever the condition named *brand* is matched,
replace the matched term(s) by *the same term(s)* searching the *company* field.
In addition, the *brand* condition is defined to match any of a list of brands.
Note how `->` means a replacing production rule,
`:-` means a condition and `,` separates alternatives.

It is also possible to do grouping using parentheses,
list multiple terms which must be matched in sequence,
and to write *adding* production rules using `+>` instead of `->`.
Terms are by default added using the query default (as if they were written in the search box),
but it is also possible to force them to be AND, OR, NOT or RANK using respectively
`+`, `?`, `-` and `$`.
Here is a more complex rule illustrating this:

```
[destination] (in, by, at, on) [place] +> $name:[destination]
```

This rule boosts matches which has a destination which matches the
*name* field followed by a preposition and a place
(the definition of the *destination* and *place* conditions are not shown).
This is achieved by adding a RANK term -
a term which do not impact whether a document is matched or not,
but which adds a relevancy boost if it is.

The complete syntax of this language is found in the
[semantic rules reference](reference/semantic-rules.html ).

## Rule bases

A collection of rules used together are collected in a *rule base* -
a text file containing rules and conditions, with file suffix `.sr` (for semantic rules).
Example:

```
# Replacements
lotr -> lord of the rings;
colour -> color;
audi -> skoda;

# Stopwords
[stopword] -> ;  # (Replace them by nothing)
[stopword] :- and, or, the, be;

# Focus brands to the brand field. If we think the brand
# field has high quality data, we can replace.  We use the same name
# for the condition and the field, but this is not necessary.
[brand] :- brand:[brand];
[brand] :- sony, dell, ibm, hp;

# Boost recognized categories
[category] +> $category:[category];
[category] :- laptop, digital camera, camera;
```

The rules in a rule base is evaluated in order from the top down.
A rule will be matched as many times as is possible before evaluation moves on to the next query.
So the query *colour colour* will be rewritten to *color color*
before moving on to the next rule.

## Configuration

A rule base file is placed in the `rules/` directory under
the [application package](reference/application-packages-reference.html),
and will be named as the file, excluding the `.sr` suffix.
E.g. if the rules above are saved to `[my-application]/rules/example.sr`,
the rules base available is named `example`.

To make a rule base be used by default in queries,
add `@default` on a separate line to the rule base.
To deactivate the default rules,
add [rules.off](reference/query-api-reference.html#rules.off) to the query.

The rules can safely be updated at any time by running `vespa prepare` again.
If there are errors in the rule bases, they will not be updated,
and the errors will be reported on the command line.

To trace what the rules are doing,
add [tracelevel.rules=[number]](reference/query-api-reference.html#tracelevel.rules) to the query.

## Using multiple rule bases

It is possible to place multiple rule bases in the `[my-application]/rules/`
and choose between them in the query.
Rules may also include each other.
This is useful to organize larger sets of rules,
to experiment with variants of the rule set in new bases which includes the standard base,
or to use different sets of rules for different use cases.

To include one rule base in another,
add `@include(rulebasename)` on a separate line,
where *rulebasename* is the file name (with or without the *.sr*).
The result will be the same as if the included rule base were copied in
to the location of the `include` line.
If a condition is defined in both bases, the one from the *including* base will be used.
It is also possible to refer to the same-named condition in an included rule base
using the `@super` directive as a condition.
For example, this rule base adds some more categories to the *category* definition
in the `example.sr` above:

```
@include(example)

# Category becomes laptop, digital camera, camera, palmtop, phone
[category] :- @super, palmtop, phone;
```

Multiple rule bases can be included, and included rule bases can themselves have included rule bases.
All the rule bases included in the application package will be available when making queries.
One of the rule bases can be made the default by adding `@default` on a separate line in the rule base.
To use another rule base,
add [rules.rulebase=[rulebasename]](reference/query-api-reference.html#rules.rulebase) to the query.

## Using a finite state automaton
*Finite state automata* (FSA) are efficient in storing and making lookups in large string lists.
A rule base can be compiled into an FSA to increase performance.
An automaton is created from a text file which lists the condition terms to match
and the condition names separated by a tab (by default).
The name of the condition can be followed by a semicolon and additional data which will be ignored.

This automaton source file defines the same as the
*stopword* and *brand* conditions in the example rule base:

```
and   stopword
or    stopword
be    stopword
the   stopword
sony  brand
dell  brand
ibm   brand; This text is ignored
hp    brand
```

Use [vespa-makefsa](/en/operations/tools.html#vespa-makefsa) to compile the automaton file:

```
$ vespa-makefsa -t sourcefile.txt targetfile.fsa
```

The target file is used from a rule base by adding *@automata(automatonfile)*
on a separate line in the rule base file (the file path is relative to *$VESPA_HOME*).
Automata-files must be stored on all container nodes.

Note that automata are not included in others,
so a rule base including another which uses an automaton
must also declare to use the same automaton
(or an automaton containing any changes from the automaton of the included base).

## Query phrasing

Users search for phrases like *New York*, *Rolling Stones*,
*The Who*, or *daily horoscopes*.
Considering the latter, most of the time the query string will look like this:

```
/search/?query=daily horoscopes&…
```

This is actually a search for documents where both *daily* and *horoscopes* match,
but not necessarily documents with the exact phrase *"daily horoscopes"*.
PhrasingSearcher is a Searcher that compares queries with a list of common phrases,
and replaces two search terms with a phrase.
If *"daily horoscopes"* is a common phrase, the above query becomes:

```
/search/?query="daily horoscopes"&…
```

The PhrasingSearcher must be configured with a list of common phrases,
compiled into a *finite state automation* (FSA). The phrase list must be:
* all lowercase
* sorted alphabetically

Example:

```
$ perl -ne 'print lc' listofphrasestextfile.unsorted.mixedcase | sort > listofphrasestextfile
```

Note that the Perl command to convert the text file to lowercase does
not handle non-ASCII characters well (this is just an example).
If the list of phrases is e.g. UTF-8 encoded and/or contains non-English characters,
double-check that the resulting file is correct.

Use [vespa-makefsa](/en/operations/tools.html#vespa-makefsa)
to compile the list into an FSA file:

```
$ vespa-makefsa listofphrasestextfile phrasefsa
```

Put the file on all container nodes, configure the location
and [deploy](application-packages.html):

```
<container id="default" version="1.0">
    <config name="container.qr-searchers">
        <com>
            <yahoo>
                <prelude>
                    <querytransform>
                        <PhrasingSearcher>
                            <automatonfile>/path/phrasefsa</automatonfile>
                        </PhrasingSearcher>
                    </querytransform>
                </prelude>
            </yahoo>
        </com>
    </config>
```

## Special tokens

Query tokens are built from *text characters*, as defined by `isTextCharacter` in
[com.yahoo.text.Text](https://github.com/vespa-engine/vespa/blob/master/vespajlib/src/main/java/com/yahoo/text/Text.java).
To query for terms with other characters, like *c++* or *.net*, use *special tokens*.
Unlike query rewriting/phrasing, special tokens modifies data at feeding time,
so changes to configuration should be followed by (automatic) document re-feed.

Add a  [specialtokens config](reference/services.html#generic-config) to *services.xml* to enable.
Specify a token list called *default*, with a list of tokens.
A token can have an optional replacement.
All special tokens must be in lower-case.
There is no need to enable it for particular fields,
or indicate the need for special token handling during query input.
Refer to [specialtokens.def](https://github.com/vespa-engine/vespa/blob/master/configdefinitions/src/vespa/specialtokens.def) for details. Example configuration:

```
<?xml version="1.0" encoding="UTF-8"?>
<services version="1.0">
    <config name="vespa.configdefinition.specialtokens">
        <tokenlist>
            <item>
                <name>default</name>
                <tokens>
                    <item>
                        <token>c++</token>
                    </item>
                    <item>
                        <token>wal-mart</token>
                        <replace>walmart</replace>
                    </item>
                    <item>
                        <token>.net</token>
                    </item>
                </tokens>
            </item>
        </tokenlist>
    </config>
    ...
</services>
```

{% include note.html content='Special tokens is most useful for text search, meaning fields with longer text.
For use cases with full exact matching in small fields, like `where product contains "M&M"`,
consider using [match: exact](reference/schema-reference.html#match), like

```
    field product type string {
        indexing: summary | index
        match: exact
    }
```

'%}

Remember to encode queries when testing with non-textual characters.
The Vespa CLI has a `-v` option to print as YQL:

```
$ vespa query -v 'select * from items where product contains "M&M"'

curl http://127.0.0.1:8080/search/\?timeout=10s\&yql=select+%2A+from+items+where+product+contains+%22M%26M%22
```
