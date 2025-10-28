---
# Copyright Vespa.ai. All rights reserved.
title: "Query Profile Reference"
---

This is a reference to the full format of [Query Profile](#query-profiles) and
[Query Profile Type](#query-profile-types) configuration files.
For an introduction to query profiles, please see [query profiles](../query-profiles.html).

## Query Profiles

A query profile defines a named set of search request parameters with values - structure:

```
<query-profile id="[id]" [optional attributes]>

    <description></description> ?

    <dimensions></dimensions> ?

    <field name="[name]" [optional attributes]>[value]</field> *

    <query-profile for="[dimension values] [optional attributes]>
        <field name="[name]">[value]</field> *
    </query-profile> *

</query-profile>
```

where `?` means optional and `*` means repeatable tag.
These items are described in the following sections.

### id

The id has the format:

```
id        ::= name(:major(.minor(.micro(.qualifier)?)?)?)?
name      ::= identifier
major     ::= integer
minor     ::= integer
micro     ::= integer
qualifier ::= identifier
```

Any omitted numeric version component missing is taken to mean 0,
while a missing qualifier is taken to mean the empty string.
If the name is exactly `default`, this profile will be the default.
If there are multiple profiles named `default`, the newest version is the default.

### Optional `query-profile` attributes

| Name | Default | Description |
| --- | --- | --- |
| type | *No type checking* | The id of a query profile type which defines the possible content of this query profile |
| inherits | *No inclusion* | A space-separated list of id's of the query profiles whose fields should be included in this profile. The fields are included exactly as if they were present in this profile. Order matters: If a field is present in multiple inherited profiles, the first one found in a depth first, left to right search will be used. Fields present in this profile always overrides the same field name in an inherited profile. |

### Description

A textual description of the purpose of this. Used for documentation.

### Query profile `field`

A field in a query profile defines a key-value pair.

If the value is a primitive (string, number), then this key value will
be available from the Query exactly as if it was submitted with the search request as a parameter
(if it is set both ways, the search request takes priority).

If the value is a reference to another query profile,
the key-values of the referenced profile will be available from the Query exactly as
if they were submitted with the search request as a parameter,
with the key of this value and a dot prepended to each key in the nested profile, i.e
`keyNameInReferringProfile.keyNameInReferencedProfile=value`.

### `field` name

The name of the field, must be a valid [identifier](#identifiers).

### Optional `field` attributes

| Name | Default | Description |
| --- | --- | --- |
| overridable | `true` | `true` or `false`. If this is `true`, this field can be overridden by a parameter of the same name in the search request. If it is `false`, it can not be overridden in the request. This attribute overrides the overridable setting in the field definition for this field (if any). If a non overridable value is attempted assigned a value later, the assignment will *not* cause an error, but will simply be ignored. |

### `field` value

This value of the field, may be either:
* a primitive, encoded as any (XML escaped) string, or
* a reference to another query profile encoded as <ref>[query-profile-id]</ref>

If this field is defined in the query profile type referenced by this query profile,
then the value must be the valid value type defined by that query type field definition.

### Dimensions

A comma-separated list of dimensions over which variants of this profile may be created as
[nested query profiles](#query-profile-nested).
The names of the dimensions are the names of request parameters which,
when received in the request, will trigger the matching profile variants.

### Query profile (nested)

A nested query profile defines variants of values returned from the enclosing query profile,
which are returned for variable requests where this variant is the most specific match to the request properties
named by the [dimensions](#dimensions)
as defined by its [for attribute](#query-profile-nested-for-attribute).
No other attributes may be set in nested query profiles.

### Query profile (nested) `for` attribute

This attribute defines the values of the [dimensions](#dimensions) of the enclosing profile
for which this nested profile defined alternative values, as a comma-separated list.
The values are defined in the same order as the dimensions are defined.
Dimensions for which this should match any value may be denoted by a "*".
One or more trailing "*" may be omitted - example:

```
for="a,b,*,c,*,*"
for="a,b,*,c"      // equivalent to the above
```

## Query Profile Types

A query profile type defines a set of valid, typed values for a query profile - structure:

```
<query-profile-type id="[id]" [optional attributes]>

    <description></description> ?

    <match path="true"/> ?

    <strict/> ?

    <field name="[name]" type="[type]" [optional attributes]/> *

</query-profile-type>
```

where `?` means optional tag and `*` means repeatable tag.
These items are described in the following sections.

### Optional `query-profile-type` attributes

| Name | Default | Description |
| --- | --- | --- |
| inherits | *No inclusion* | A space-separated list of id's of the query profile types whose field definitions should be included in this profile. The fields are included exactly as if they were present in this profile type. Order matters: If a field definition is present in multiple inherited profiles, the first one found in a depth first, left to right search will be used. A field definition in this type always overrides inherited ones. The same rules apply to other elements than fields. |

### `match`

If <match path="true"> is added to the query profile type,
the name of the profile will be understood as a slash separated path name
during matching of a query profile name to an actual profile.
If the query profile name is a *path component prefix* of the query profile name reference,
the profile matches the reference.
The profile having the most specific match is used as the target of the reference.

If `match` is not specified in the profile type, exact name matching is used.
The syntax is as specified for future extensions.

The match setting is inherited from supertypes to subtypes.

### `strict`

If this element is added to a query profile type,
then that profile can only contain values explicitly defined in the profile,
whether that value is provided by a query profile,
the search request or programmatically.

It is possible to add strict sub-profiles to a non-strict profile and vice-versa,
making it possible to create respectively "structs in maps" and "maps in structs".

A profile which inherits a strict profile will also be strict,
i.e `strict` is inherited.

Some rules to note when using a top-level profile type which is declared as strict:
* If the top-level profile is of a strict type,
  that type should usually inherit the `native` type to allow the built-in parameters to be passed in.
  This profile type and the subtypes it references are always available -
  refer to the [Query API reference](query-api-reference.html).
* Non-primitive model objects are permitted to be added to the query profiles
  even if the top level profile is strict, but primitives (strings, numbers, booleans)
  are *not* permitted but must either be declared in the strict profile type,
  or wrapped in a proper model object
* Feature specific properties like `select` are not automatically permitted,
  the parameters of the features which should be exposed must be declared explicitly in a strict top level type.

### Query profile type `field`

This defines the name and type of a field of query profiles of this type.

### `field` type

This defines the type of this field. The type is one of:

| Type name | Description |
| --- | --- |
| string | Any string |
| integer | A signed 32-bit whole number |
| long | A signed 64-bit whole number |
| float | A signed 32-bit float |
| double | A signed 64-bit float |
| boolean | A boolean value, `true` or `false` |
| [[tensor-type-spec]](tensor.html#tensor-type-spec) | A tensor type spec |
| query-profile | A reference to a query profile of any type |
| query-profile:[query-profile-type-id] | A reference to a query profile of the given type |

### Optional `field` definition attributes

| Name | Default | Description |
| --- | --- | --- |
| mandatory | `false` | `true` or `false`. If this is `true`, this field *must* be present in either the query profile of this type or explicitly in the request referencing it |
| overridable | `true` | `true` or `false`. If this is `true`, instances of this field can be overridden by a parameter of the same name in the search request. If it is `false`, it can not be overridden in the request |
| alias | *None* | One or more space-separated aliases of the field name. Unlike field names, aliases are case-insensitive |
| description | *None* | A textual description of the purpose of this field. Used for documentation |

### Identifiers

An identifier is a string matches the pattern `[a-zA-Z_/][a-zA-Z0-9_/]*`.
