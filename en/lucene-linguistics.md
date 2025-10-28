---
# Copyright Vespa.ai. All rights reserved.
title: "Lucene Linguistics"
---

Lucene Linguistics is a custom [linguistics](linguistics.html) implementation of the
[Apache Lucene](https://lucene.apache.org) library.
It provides a Lucene analyzer to handle text processing for a language
with an optional variation per [stemming mode](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/process/StemMode.java).

Check [sample apps](https://github.com/vespa-engine/sample-apps/tree/master/examples/lucene-linguistics) to
get started.

## Crash course to Lucene text analysis

Lucene [text
analysis](https://lucene.apache.org/core/9_8_0/core/org/apache/lucene/analysis/package-summary.html)
is a process of converting text into searchable tokens.
This text analysis consists of a series of components applied to the text in order:
* [CharFilters](https://lucene.apache.org/core/9_8_0/core/org/apache/lucene/analysis/CharFilter.html):
  transform the text before it is tokenized, while providing corrected character offsets to account for these
  modifications.
* [Tokenizers](https://lucene.apache.org/core/9_8_0/core/org/apache/lucene/analysis/Tokenizer.html):
  responsible for breaking up incoming text into tokens.
* [TokenFilters](https://lucene.apache.org/core/9_8_0/core/org/apache/lucene/analysis/TokenFilter.html):
  responsible for modifying tokens that have been created by the Tokenizer.

A specific configuration of the above components is wrapped into an
[Analyzer](https://lucene.apache.org/core/9_8_0/core/org/apache/lucene/analysis/Analyzer.html) object.

The text analysis works as follows:

1. All char filters are applied in the specified order on the entire text string
2. Token filters in the specified order are applied on each token.

## Defaults language analysis

Lucene Linguistics out-of-the-box exposes the analysis components provided
by the [lucene-core](https://lucene.apache.org/core/9_8_0/core/index.html)
and the
[lucene-analysis-common](https://lucene.apache.org/core/9_8_0/analysis/common/index.html)
libraries.
Other libraries with Lucene text analysis components
(e.g. [analysis-kuromoji](https://lucene.apache.org/core/9_8_0/analysis/kuromoji/index.html))
can be added to the application package as a Maven dependency.

Lucene Linguistics out-of-the-box provides analyzers for 40 languages:
* Arabic
* Armenian
* Basque
* Bengali
* Bulgarian
* Catalan
* Chinese
* Czech
* Danish
* Dutch
* English
* Estonian
* Finnish
* French
* Galician
* German
* Greek
* Hindi
* Hungarian
* Indonesian
* Irish
* Italian
* Japanese
* Korean
* Kurdish
* Latvian
* Lithuanian
* Nepali
* Norwegian
* Persian
* Portuguese
* Romanian
* Russian
* Serbian
* Spanish
* Swedish
* Tamil
* Telugu
* Thai
* Turkish

The Lucene
[StandardAnalyzer](https://lucene.apache.org/core/9_8_0/core/org/apache/lucene/analysis/standard/StandardAnalyzer.html)
is used for the languages that doesn't have a custom nor a default analyzer.

## Linguistics key

Linguistics keys identify a configuration of text analysis.
A key has 2 parts: a mandatory [language code](https://github.com/vespa-engine/vespa/blob/master/linguistics/src/main/java/com/yahoo/language/Language.java) and an optional stemming mode.
The format is `LANGUAGE_CODE[/STEM_MODE]`.
There are 5 stemming modes: `NONE, DEFAULT, ALL, SHORTEST, BEST` (they can be specified in the [field schema](reference/schema-reference.html#stemming)).

Examples of linguistics key:
* `en`: English language.
* `en/BEST`: English language with the `BEST` stemming mode.

## Customizing text analysis

Lucene linguistics provides multiple ways to customize text analysis per language:
* `LuceneLinguistics` component configuration in the `services.xml`
* `ComponentsRegistry`

### LuceneLinguistics component configuration

In `services.xml` it is possible to construct an analyzer by providing
[configuration for the](https://github.com/vespa-engine/vespa/blob/master/lucene-linguistics/src/main/resources/configdefinitions/lucene-analysis.def)
`LuceneLinguistics` component (from all text analysis components that are available on the classpath).
Example for the English language:

```
  <component id="linguistics"
             class="com.yahoo.language.lucene.LuceneLinguistics"
             bundle="your-bundle-name">
    <config name="com.yahoo.language.lucene.lucene-analysis"/>
      <configDir>lucene-linguistics</configDir>
      <analysis>
        <item key="en">
          <tokenizer>
            <name>standard</name>
          </tokenizer>
          <tokenFilters>
            <item>
              <name>stop</name>
              <conf>
                <item key="words">en/stopwords.txt</item>
                <item key="ignoreCase">true</item>
              </conf>
            </item>
            <item>
              <name>englishMinimalStem</name>
            </item>
          </tokenFilters>
        </item>
      </analysis>
  </component>
```

Notes:
* `item key="en"` value is a [linguistics key](#linguistics-key).
* the `en/stopwords.txt` file must be placed in your application package under
  the `lucene-linguistics` directory.
* If the `configDir` is not provided the files must be on the classpath.

### Components registry

The [ComponentsRegistry](jdisc/injecting-components.html#depending-on-all-components-of-a-specific-type)
mechanism can be used to set a Lucene Analyzer for a language.

```
<component
    id="en"
    class="org.apache.lucene.analysis.core.SimpleAnalyzer"
    bundle="your-bundle-name" />
```

Where:
* `id` must be a [linguistics key](#linguistics-key);
* `class` is the implementation class that extends the `Analyzer` class;
* `bundle` is a name of the application package as specified in the `pom.xml`
  (or can be any bundle added to your `components` dir that contains the class).

For this to work, the class must provide **only** a constructor without arguments.

In case your analyzer class needs some initialization you must wrap the analyzer into a class
that implements the `Provider<Analyzer>` class.

### Custom text analysis components

The text analysis components are loaded via Java Service provider interface ([SPI](https://www.baeldung.com/java-spi)).

To use an external library that is properly prepared it is enough to add the
library to the application package as a Maven dependency.

In case you need to create a custom component the steps are:

1. Implement a component in a Java class
2. Register the component class in the (e.g. a custom token filter) `META-INF/services/org.apache.lucene.analysis.TokenFilterFactory`
   file that is on the classpath.

## Language Detection

Lucene Linguistics doesn't provide language detection.
This means that for both feeding and searching you should provide a
[language parameter](reference/query-api-reference.html#model.language).
