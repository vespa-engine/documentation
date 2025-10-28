---
# Copyright Vespa.ai. All rights reserved.
title: "Predicate Search Java Library"
---

{% include important.html content="The Predicate Search Java Library is **deprecated** for removal in
[Vespa 9](vespa9-release-notes.html). Use [predicate fields](predicate-fields.html) instead." %}

The rationale for predicate fields is described in the
[predicate fields document](predicate-fields.html).
Vespa also has a standalone Java library for searching predicate fields,
for boolean matching tightly integrated with a Java program, e.g. running on a grid.
The performance is similar to predicate search in Vespa.
Find API documentation in the
[javadoc](https://javadoc.io/doc/com.yahoo.vespa/predicate-search).
Get started - add a dependency in *pom.xml*:

```
<dependency>
  <groupId>com.yahoo.vespa</groupId>
  <artifactId>predicate-search</artifactId>
</dependency>
```

### Indexing documents

Unlike Vespa predicate fields, which have dynamic indexes,
the Java library requires the entire index to be built before any searches are run.
Once built, the index cannot be changed.
Build an index using an instance of `PredicateIndexBuilder`.

Use `indexDocument(id, predicate)` to index documents.
This method takes two arguments, a 32-bit document id and the document itself
(in form of a `Predicate` object).
Once all documents are indexed, create the index by invoking `build()`.
This method returns a `PredicateIndex` object.

Use [Predicate.fromString()](https://javadoc.io/doc/com.yahoo.vespa/predicate-search-core/latest/com/yahoo/document/predicate/Predicate.html) to parse predicate expressions from strings.
The expressions use the [predicate syntax](predicate-fields.html).

### Index configuration

Just as with Vespa predicate fields, specify the [arity](predicate-fields.html#index-size) and
[upper- and lower bounds](predicate-fields.html#upper-and-lower-bounds) for the index,
to make the index more efficient and trade index size for query performance.
This is set when creating a `PredicateIndexBuilder` object,
and cannot be changed without creating a new `PredicateIndexBuilder`.
Check the [Config](https://javadoc.io/doc/com.yahoo.vespa/predicate-search/latest/com/yahoo/search/predicate/Config.html)
class for more information on other configuration parameters.

### Serializing the index

The predicate index supports serialization.
Use the `PredicateIndex.writeToOutputStream(out)` to serialize the index to an output stream,
and the `PredicateIndex.fromInputStream(in)` to deserialize an index from an input stream.
Deserializing an index is significantly faster than creating a new index
through `PredicateIndexBuilder`.

### Creating a searcher

`PredicateIndex` has a method called `searcher()`, which creates a new searcher object.
The searcher exposes one method, `search(query)`, which searches the index.
The index itself is thread-safe, but a searcher is not. When searching from multiple threads,
make sure to create a separate searcher object for each thread.

### Creating a query

A query is represented as a `PredicateQuery` object.
The `PredicateQuery` object contains a set of features with `String` values,
and a set of range features with `long` values.
Each feature in the query may have a 64-bit sub-query bitmap set.

### Executing a query

The `search()` method on `PredicateIndex.Searcher`
returns a stream object which lazily evaluates the query when the results are needed.
Each `Hit` in the result stream contains the document id for the hit,
as well as a sub-query bitmap indicating which sub-queries the hit was a match for.
The hits are returned in the order they were indexed.

## Performance

As with Vespa, the arity and upper- and lower bound configuration impacts on the performance and index size.
E.g, increasing the arity increases QPS at a cost of a larger index.

The library may cache common posting lists to increase performance.
The cache consists of the most expensive posting lists based on size and their prevalence in queries.
The cache is disabled by default and must be build manually using
`PredicateIndex.rebuildPostingListCache()`.
It is recommended to rebuild the cache regularly for optimal performance,
for instance every 1 millionth query or every 30 minutes.
The cache rebuild is thread-safe and can be executed safely during concurrent search operations.

## Sample code

```
package com.yahoo.example;

import com.yahoo.document.predicate.Predicate;
import com.yahoo.search.predicate.Config;
import com.yahoo.search.predicate.Hit;
import com.yahoo.search.predicate.PredicateIndex;
import com.yahoo.search.predicate.PredicateIndexBuilder;
import com.yahoo.search.predicate.PredicateQuery;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.util.List;
import java.util.stream.Stream;

import static com.yahoo.document.predicate.Predicates.and;
import static com.yahoo.document.predicate.Predicates.feature;
import static java.util.stream.Collectors.toList;

public class App {

    public static void main( String[] args ) throws IOException {
        // Create index configuration
        Config config = new Config.Builder()
                .setArity(10)
                .setLowerBound(0) // Minimum value for 'age' range feature
                .setUpperBound(150) // Maximum value for 'age' range feature
                .build();

        // Create index builder
        PredicateIndexBuilder indexBuilder = new PredicateIndexBuilder(config);
        // Pass document id and predicate. 'age' is a range feature, while 'gender' is a normal feature
        indexBuilder.indexDocument(1, Predicate.fromString("age in [20..40] and gender in ['male', 'female']"));
        indexBuilder.indexDocument(2, and(feature("age").inRange(40, 60), feature("gender").inSet("male")));
        // Create index from builder
        PredicateIndex index = indexBuilder.build();

        // Create query1
        PredicateQuery query1 = new PredicateQuery();
        query1.addFeature("gender", "male", 0b01); // Subquery 0
        query1.addFeature("gender", "female", 0b10); // Subquery 1
        query1.addRangeFeature("age", 30, 0b11); // Subquery 0 and 1

        // Run queries using multiple threads
        Runnable searchRunnable = () -> {
            // Create a searcher
            // Note: PredicateIndex.Searcher is not thread safe, so each thread has to use a separate Searcher
            PredicateIndex.Searcher searcher = index.searcher();

            // Search index. A stream of hits is returned
            Stream<Hit> hitStream = searcher.search(query1);
            // Prints document id and subquery bitmap ('[0, 0x3]'). Bitmap is 0b11 as document matches both subqueries
            System.out.println("Hit: " + hitStream.findFirst().get());
        };
        new Thread(searchRunnable).start();
        new Thread(searchRunnable).start();

        // Rebuild posting list cache to improve performance
        index.rebuildPostingListCache();

        new Thread(searchRunnable).start();
        new Thread(searchRunnable).start();

        // Serialized index to a byte array
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        index.writeToOutputStream(new DataOutputStream(baos));
        byte[] serializedIndex = baos.toByteArray();

        // Load the index from byte array
        PredicateIndex deserializedIndex =
                PredicateIndex.fromInputStream(
                        new DataInputStream(
                                new ByteArrayInputStream(serializedIndex)));

        // Create new query (which is not using subqueries this time)
        PredicateQuery query2 = new PredicateQuery();
        query2.addFeature("gender", "male");
        query2.addRangeFeature("age", 40);
        // Search using deserialized index
        List<Hit> hits = deserializedIndex.searcher().search(query2).collect(toList());
        // Prints the id for both documents. No subquery bitmap printed
        System.out.println("Hits from deserialized index: " + hits);
    }
}
```
