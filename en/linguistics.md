---
# Copyright Vespa.ai. All rights reserved.
title: "Linguistics in Vespa"
---

Vespa uses a *linguistics* module to process text in queries and documents during indexing and searching.
The goal of linguistic processing is to increase *recall* (how many documents are matched)
without hurting *precision* (the relevance of the documents matched) too much.
It consists of such operations as:
* tokenizing text into chunks of known types such as words and punctuation.
* normalizing accents.
* finding the base form of words (stemming or lemmatization).

Linguistic processing is run when writing documents, and when querying:

![Overview: linguistic processing in Vespa](/assets/img/vespa-overview-linguistics.svg)

The processing is run on [string](reference/schema-reference.html#string) fields
with `index` indexing mode. Overview:

1. When writing documents, string fields with `indexing: index` are by default processed.
   A field's language will configure this processing.
   A document/fields can have the language set explicitly,
   if not, it is [detected](#field-language-detection).
2. The field's content is tokenized, normalized and stemmed,
   and the resulting terms are added to the index.
   {% include note.html content='The language for the field is not persisted on the content node,
   just the processed terms themselves' %}
3. A query is also processed the same way - this is symmetric with the schema.
   The language of the strings is [detected](#query-language-detection) unless specified using
   [model.locale](reference/query-api-reference.html#model.locale)
   or [annotations](reference/query-language-reference.html#annotations) like `language`.
   {% include note.html content='This is a very common query problem -
   it is hard to detect language precisely from short strings.' %}
4. The processed query is evaluated on the content nodes,
   and will only work as expected if both documents and queries are processed using identical settings
   (like same language).

These operations can be turned on or off per field in the [schema](schemas.html).
See [implicitTransforms](reference/query-language-reference.html#implicittransforms)
for how to enable/disable transforms per query term.

### Default languages

The default Vespa linguistics implementation uses [OpenNLP](https://opennlp.apache.org/). Apache OpenNLP
language detection has support for 103 languages, and OpenNLP tokenization and stemming supports these languages:
* Arabic (ar)
* Catalan (ca)
* Danish (da)
* Dutch (nl)
* English (en)
* Finnish (fi)
* French (fr)
* German (de)
* Greek (el)
* Hungarian (hu)
* Indonesian (id)
* Irish (ga)
* Italian (it)
* Norwegian (no)
* Portuguese (pt)
* Romanian (ro)
* Russian (ru)
* Spanish (es)
* Swedish (sv)
* Turkish (tr)

Other languages that will use a fallback to English *en*.

The OpenNLP language detector gives a prediction with a
confidence; with confidence typically increasing with more
input. The threshold for using the prediction can be configured
with a number typically from 1.0 (wild guess) to 6.0 (confident
guess), with 2.0 as the default:

```
  <container id="..." version="1.0">
    ...
    <config name="ai.vespa.opennlp.open-nlp">
      <detectConfidenceThreshold>4.2</detectConfidenceThreshold>
    </config>
```

English uses a simpler stemmer (kStem) by default, which produces fewer stems and therefore lower recall.
To use OpenNlp stemming (Snowball) also for English add this config to your <container> element(s):

```
  <container id="..." version="1.0">
    ...
    <config name="ai.vespa.opennlp.open-nlp">
      <snowballStemmingForEnglish>true</snowballStemmingForEnglish>
    </config>
```

See *Tokens* [OpenNLP models](https://opennlp.apache.org/models.html) and [text matching](text-matching.html)
for examples and how to experiment with linguistics.

If you need support for more languages, you can consider replacing the default OpenNLP based linguistic integration
with the [Lucene Linguistics](lucene-linguistics.html) implementation which supports more languages.

### Chinese

The default linguistics implementation does not segment Chinese into tokens, but this can be turned on by config:

```
  <container id="..." version="1.0">
    ...
    <config name="ai.vespa.opennlp.open-nlp">
      <cjk>true</cjk>
      <createCjkGrams>true</createCjkGrams>
    </config>
```

The createCjkGrams adds substrings of segments longer than 2 characters, which may increase recall.

## Language handling

Vespa does *not* know the language of a document - this applies:

1. The indexing processor is instructed on a per-field level what language to
   use when calling the underlying linguistics library
2. The query processor is instructed on a per-query level what language to use

If no language is explicitly set in a document or a query,
Vespa will run its configured language detector on the available text
(the full content of a document field, or the full `query=` parameter value).

A document that contains the exact same word as a query might not be recall-able
if the language of the document field is detected differently from the query.
Unless the query has explicitly declared a [language](reference/query-api-reference.html#model.language),
this can occur.

### Indexing with language

The indexing process run by Vespa is a sequential execution
of the indexing scripts of each field in the schema, in the declared order.
At any point, the script may set the language that will be used for indexing statements for subsequent fields,
using [set_language](reference/indexing-language-reference.html#set_language).
Example:

```
schema doc {
    document doc {
        field language type string {
            indexing: set_language
        }
        field title type string {
            indexing: index
        }
    }
}
```

If a language has not been set when tokenization of a field is run, the language is determined by
[language detection](#field-language-detection).

If all documents have the same language, the language can be hardcoded it the schema in this way:

```
schema doc {

    field language type string {
        indexing: "en" | set_language
    }

    document doc {
    ...
```

If the same document contains fields in multiple languages, set_language can be invoked multiple times, e.g.:

```
schema doc {
    document doc {
        field language_title1 type string {
            indexing: set_language
        }
        field title1 type string {
            indexing: index
        }
        field language_title2 type string {
            indexing: set_language
        }
        field title2 type string {
            indexing: index
        }
    }
}
```

Or, if fixed per field, use multiple indexing statements in each field:

```
schema doc {
    document doc {
        field my_english_field type string {
            indexing {
                "en" | set_language;
                index;
            }
        }
        field my_spanish_field type string {
            indexing {
                "es" | set_language;
                index;
            }
        }
    }
}
```

### Field language detection

When indexing a document, if a field has unknown language (i.e. not set using `set_language`),
language detection is run on the field's content.
This means, language detection is per field, not per document.

See [query language detection](#query-language-detection) for detection confidence,
fields with little text will default to English.

### Querying with language

The content of an indexed string field is language-agnostic.
One must therefore apply a symmetric tokenization on the query terms in order to match the content of that field.

The query parser subscribes to configuration that tells it what fields are indexed strings,
and every query term that targets such a field are run through appropriate tokenization.
The [language](reference/query-api-reference.html#model.language) query parameter
controls the language state of these calls.

Because an index may simultaneously contain terms in any number of languages,
one can have stemmed variants of one language match the stemmed variants of another.
To work around this, store the language of a document in a separate attribute,
and apply a filter against that attribute at query-time.

By default, there is no knowledge anywhere that captures what
languages are used to generate the content of an index.
The language parameter only affects the transformation of query terms that hit tokenized indexes.

### Query language detection

If no [language](reference/query-api-reference.html#model.language) parameter is used,
or the query terms are [annotated](reference/query-language-reference.html#annotations),
the language detector is called to process the query string.

Queries are normally short, as a consequence, the detection confidence is low. Example:

```
$ vespa query "select * from music where userInput(@text)" \
  tracelevel=3 text='Eine kleine Nachtmusik' | grep 'Stemming with language'
    "message": "Stemming with language=ENGLISH"

$ vespa query "select * from music where userInput(@text)" \
  tracelevel=3 text='Eine kleine Nachtmusik schnell' | grep 'Stemming with language'
    "message": "Stemming with language=GERMAN"
```

See [#24265](https://github.com/vespa-engine/vespa/issues/24265) for details -
in short, with the current 0.02 confidence cutoff, queries with 3 terms or fewer will default to English.

### Multiple languages

Vespa supports having documents in multiple languages in the same schema, but does not out-of-the-box
support cross-lingual retrieval (e.g., search using English and retrieve relevant documents written in German).
This is because the language of a query is determined
by the language of the query string and only one transformation can take place.

Approaches to overcome this limitation include:

1. Use semantic retrieval using a multilingual text embedding model (see [blog post](https://blog.vespa.ai/simplify-search-with-multilingual-embeddings/))
   which has been trained on multilingual corpus and can be used to retrieve documents in multiple languages.
2. Stem and tokenize the query using the relevant languages,
   build a query tree using [weakAnd](reference/query-language-reference.html#weakand) /
   [or](reference/query-language-reference.html#or)
   and using [equiv](reference/query-language-reference.html#equiv) per stem variant.
   This is easiest done in a custom [Searcher](searcher-development.html) as mentioned in
   [#12154](https://github.com/vespa-engine/vespa/issues/12154).

Example:
**language=fr:** machine learning => machin learn
**language=en:** machine learning => machine learn

Using *weakAnd* here as example as that technique is already mentioned in #12154:

```
select * from sources * where rank(
    default contains "machine",
    default contains "learning",
    weakAnd(
      default contains equiv("machin", "machine"),
      default contains "learn"
    )
)
```

We now retrieve using all possible stems/base forms with *weakAnd*,
and use the [rank](reference/query-language-reference.html#rank) operator
to pass in the original query form, so that ranking can rank literal matches (original) higher.
Benefit of *equiv* is that it allows multiple term variants to share the same position,
so that proximity ranking does not become broken by this approach.

## Tokenization

Tokenization removes any non-word characters,
and splits the string into *tokens* on each word boundary.
In addition, CJK tokens are split using a *segmentation* algorithm.
The resulting tokens are then searchable in the index.

Also see [N-gram matching](reference/schema-reference.html#gram).

## Normalization

An example normalization is à ⇒ a.
Normalizing will cause accents and similar decorations which are often misspelled
to be normalized the same way both in documents and queries.

Vespa uses [java.text.Normalizer](https://docs.oracle.com/javase/7/docs/api/java/text/Normalizer.html)
to normalize text, see
[SimpleTransformer.java](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/simple/SimpleTransformer.java).
Normalization preserves case.

Refer to the [nfkc](reference/query-language-reference.html#nfkc) query term annotation.
Also see the YQL [accentDrop](reference/query-language-reference.html#accentdrop) annotation.

## Stemming

Stemming means *translate a word to its base form*
(singular forms for nouns, infinitive for verbs),
using a [stemmer](https://en.wikipedia.org/wiki/Stemming).
Use of stemming increases search recall,
because the searcher is usually interested in documents containing query words
regardless of the word form used.
Stemming in Vespa is symmetric,
i.e. words are converted to stems both when indexing and searching.

Examples of this is when text is indexed,
the stemmer will convert the noun *reports* (plural) to *report*,
and the latter will be stored in the index.
Likewise, before searching, *reports* will be stemmed to *report*.
Another example is that *am*, *are* and *was*
will be stemmed to *be* both in queries and indexes.

When [bolding](reference/schema-reference.html#bolding) is enabled,
all forms of the query term will be bolded.
I.e. when searching for *reports*,
both *report*, *reported* and *reports* will be bolded.

See the [stem](reference/query-language-reference.html#stem) query term annotation.

### Theory

From a matching point of view,
stemming takes all possible token strings and maps them into equivalence classes.
So in the example above, the set of tokens
{ *report*, *reports*, *reported* } are in an equivalence class.
To represent the class,
the linguistics library should pick the best element in the class.
At query time, the text typed by a user will be tokenized,
and then each token should be mapped to the most likely equivalence class,
again represented by the shortest element that belongs to the class.

While the theory sounds pretty simple,
in practice it is not always possible to figure out which equivalence class a token should belong to.
A typical example is the string *number*.
In most cases we would guess this to mean a numerical entity of some kind,
and the equivalence class would be { *number*, *numbers* } - but it could also be a verb,
with a different equivalence class { *number*, *numbered*, *numbering* }.
These are of course closely related, and in practice they will be merged,
so we'll have a slightly larger equivalence class
{ *number*, *numbers*, *numbered*, *numbering* }
and be happy with that.
However, in a sentence such as *my legs keep getting number every day*,
the *number* token clearly does not have the semantics of a numerical entity,
but should be in the equivalence class
{ *numb*, *number*, *numbest*, *numbness* } instead.
But blindly assigning *number* to the equivalence class *numb* is clearly not right,
since the *more numb* meaning is much less likely than the *numerical entity* meaning.

The approach currently taken by the low-level linguistics library
will often lead to problems in the *number*-like cases as described above.
To give better recall, Vespa has implemented a *multiple* stemming option.

### Configuration

By default, all words are stemmed to their *best* form.
Refer to the [stemming reference](reference/schema-reference.html#stemming) for other stemming types. To change type, add:

```
stemming: [stemming-type]
```

Stemming can be set either for a field, a fieldset or as a default for all fields.
Example: Disable stemming for the field *title*:

```
field title type string {
    indexing: summary | index
    stemming: none
}
```

See [andSegmenting](reference/query-language-reference.html#andsegmenting)
for how to control re-segmenting when stemming.

## Creating a custom linguistics implementation

A linguistics component is an implementation of
[com.yahoo.language.Linguistics](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/Linguistics.java). Refer to the
[com.yahoo.language.simple.SimpleLinguistics](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/simple/SimpleLinguistics.java) implementation (which can be subclassed for convenience).

SimpleLinguistics provides support for english stemming only.
Try loading the `com.yahoo.language.simple.SimpleLinguistics` module,
or providing another linguistics module.

The linguistics implementation must be configured as a component
in container clusters doing linguistics processing,
see [injecting components](jdisc/injecting-components.html).

As document processing for indexing is by default done by an autogenerated container cluster
which cannot be configured, specify a container cluster for indexing explicitly.

This example shows how to configure SimpleLinguistics for linguistics using the same cluster for both query and indexing processing
(if using different clusters, add the same linguistics component to all of them):

```
<services>

    <container version="1.0" id="mycontainer">
        <component id="com.yahoo.language.simple.SimpleLinguistics"/>
        <document-processing/>
        <search/>
        <nodes ...>
    </container>

    <content version="1.0">
        <redundancy>1</redundancy>
        <documents>
            <document type="mydocument" mode="index"/>
            <document-processing cluster="mycontainer"/>
        </documents>
        <nodes ...>
    </content>

</services>
```

If changing the linguistics component of a live system,
recall can be reduced until all documents are re-written.
This because documents will still be stored with tokens generated by the previous linguistics module.
