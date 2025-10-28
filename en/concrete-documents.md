---
# Copyright Vespa.ai. All rights reserved.
title: "Concrete document types"
---

In [document processing](document-processing.html),
`setFieldValue()` and `getFieldValue()`
is used to access fields in a `Document`.
The data for each of the fields in the document instance is wrapped in field values.
If the documents use structs, they are handled the same way. Example:

```
book.setFieldValue("title", new StringFieldValue("Moby Dick"));
```

Alternatively, use code generation to get a *concrete document type*,
a `Document` subclass that represents the exact document type
(defined for example in the file `book.sd`).
To generate, include it in the build, plugins section in *pom.xml*:

```
<plugin>
    <groupId>com.yahoo.vespa</groupId>
    <artifactId>vespa-documentgen-plugin</artifactId>
    <!-- Find latest version at search.maven.org/search?q=g:com.yahoo.vespa%20a:vespa-documentgen-plugin -->
    <version>{{site.variables.vespa_version}}</version>
    <configuration>
        <schemasDirectory>etc/schemas</schemasDirectory>
    </configuration>
    <executions>
        <execution>
            <id>document-gen</id>
            <goals>
                <goal>document-gen</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

`schemasDirectory` contains the
[schemas](reference/schema-reference.html).
Generated classes will be in *target/generated-sources*.
The document type `book` will be represented as the Java class `Book`,
and it will have native methods for data access, so the code example above becomes:

```
book.setTitle("Moby Dick");
```

| Configuration | Description |
| --- | --- |
| Java package | Specify the Java package of the generated types by using the following configuration:   ``` <configuration>     <packageName>com.yahoo.mypackage</packageName> ``` |
| User provided annotation types | To provide the Java implementation of a given annotation type, yielding *behaviour of annotations* (implementing additional interfaces may be one scenario):   ``` <configuration>     <schemasDirectory>etc/schemas</schemasDirectory>     <provided>         <annotation>             <type>NodeImpl</type>             <clazz>com.yahoo.vespa.document.NodeImpl</clazz>         </annotation>         <annotation>             <type>DocumentImpl</type>             <clazz>com.yahoo.vespa.document.DocumentImpl</clazz>         </annotation>     </provided> ```  Here, the plugin will not generate a type for `NodeImpl` and `DocumentImpl`, but the `ConcreteDocumentFactory` will support them, so that code depending on this will work. |
| Abstract annotation types | Make a generated annotation type abstract:   ``` <configuration>     <abztract>       <annotation>         <type>myabstractannotationtype</type>       </annotation>     </abztract> ``` |

## Inheritance

If input document types use single inheritance, the generated Java types will inherit accordingly.
However, if a document type inherits from more than one type
(example: `document myDoc inherits base1, base2`),
the Java type for `myDoc` will just inherit from `Document`,
since Java has single inheritance.
Refer to [schema inheritance](schemas.html#schema-inheritance) for examples.

## Feeding

Concrete types are often used in a docproc, used for feeding data into stateful clusters.
To make Vespa use the correct type during feeding and serialization,
include in `<container>` in [services.xml](reference/services.html ):

```
<container id="default" version="1.0">
    <document type="book"
              bundle="the name in <artifactId> in your pom.xml"
              class="com.yahoo.mypackage.Book" />
```

Vespa will make the type `Book` and all other concrete
document, annotation and struct types from the bundle available to the docproc(s) in the container.
The specified bundle must be the `Bundle-SymbolicName`.
It will also use the given Java type when feeding through a docproc chain.
If the class is not in the specified bundle,
the container will emit an error message about not being able to load
`ConcreteDocumentFactory` as a component, and not start.
There is no need to `Export-Package` the concrete document types from the bundle,
a `package-info.java` is generated that does that.

## Factory and copy constructor

Along with the actual types, the Maven plugin will also generate a class `ConcreteDocumentFactory`,
which holds information about the actual concrete types present.
It can be used to initialize an object given the document type:

```
Book b = (Book) ConcreteDocumentFactory.getDocument("book", new DocumentId("id:book:book::0"));
```

This can be done for example during deserialization, when a document is created.
The concrete types also have copy constructors that can take a generic
`Document` object of the same type. The contents will be deep-copied:

```
Document bookGeneric;
// …
Book book = new Book(bookGeneric, bookGeneric.getId());
```

All the accessor and mutator methods on `Document` will work as expected on concrete types.
Note that `getFieldValue()` will *generate* an
ad-hoc `FieldValue` *every time*,
since concrete types don't use them to store data.
`setFieldValue()` will pack the data into the native Java field of the type.

## Document processing

In a document processor, cast the incoming document base into the
concrete document type before accessing it. Example:

```
public class ConcreteDocDocProc extends DocumentProcessor {
    public Progress process(Processing processing) {
        DocumentPut put = (DocumentPut) processing.getDocumentOperations().get(0);
        Book b = (Book) (put.getDocument());
        b.setTitle("The Title");
        return Progress.DONE;
    }
}
```

Concrete document types are not supported for document updates or removes.
