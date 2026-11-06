---
# Copyright Vespa.ai. All rights reserved.
title: "Agent-ready schemas"
---

Agents will increasingly be the users of search applications. They differ from the typical human
user in two ways:

* they need all the information on how to use a particular application it in their context
* they are able to make use of that information to generate complex high-precision queries to solve tasks

Vespa provides the information agents need as a skill available on container endpoints.
To enable it, add the schemas skill to services.xml in your search container cluster:

```xml
<services>
    <container id="...">
        <search/>
        <skills><schemas/></skills>
    </container>
</services>
```

With this in place, you can point agents using a search application to `[endpoint]/skills/v1/schemas` 
to enable them to search like experts.

## Schema explanations

The skill provides information on what schemas, fields, rank profiles, and inputs are available,
their types, match modes, and how to embed, when done internally. In addition, you can provide
*explanations* that supply additional information that might be useful:

```vespa-schema-language
schema article {

    explanation {
        Scientific articles imported from pdf archives. 
        Individual fields will denote whether the article is peer
        reviewed, when it was published, by whom and so on. Titles,
        abstracts and full text are searchable
        both lexically and as multi-vector representations, 
        see fields for details.
    }

    document {
        field publish_date type long {
            indexing: attribute
            explanation: Published data as an epoch seconds timestamp.
        }
        …
    }

    rank-profile topical {
        explanation {
            Orders articles by broad relevance to the described concept,
            emphasizing semantic matching while ranking exact lexical
            matches higher.

            @input query(embedding) the concept as a single embedding 
            @input query(freshness) the weight (0-1) to give to recency
                                    among topical matches
        }
        …
    }

}
```

Explanations can be added on schemas, fields, and rank profiles, and on rank profiles
they can also contain explanations for the inputs to the profile, see the
[schema reference](../reference/schemas/schemas.html).

Explanations should be used when there is *additional relevant information to provide*, such as
the range and unit of values of a field, what are suitable use cases for a rank profile and similar.
They should not explain what's obvious, or repeat information that is provided automatically, such as the type.
