---
# Copyright Vespa.ai. All rights reserved.
title: "Query Profiles"
---

A Query Profile is a named collection of search request parameters given in the configuration.
The search request can specify a query profile
whose parameters will be used as parameters of that request.
This frees the client from having to manage and send a large number of parameters,
and enables the request parameters to use for a use case to be changed
without having to change the client.
Query profiles enables [bucket tests](testing.html#feature-switches-and-bucket-tests),
where a part of the query stream is given some experimental treatment,
as well as differentiating behavior based on (OEM) customer, user type, region, frontend type etc.
This document explains how to create and use query profiles.
See also the [query profile reference](reference/query-profile-reference.html) for the full syntax.

## Using a Query Profile

A Query Profile is an XML file containing the request parameter names and their values, e.g.:

```
<query-profile id="MyProfile">
    <field name="hits">20</field>
    <field name="maxHits">2000</field>
    <field name="unique">merchantid</field>
</query-profile>
```

See the [query profile reference](reference/query-profile-reference.html) for the full syntax.
{% include important.html content='Note that full property names must be used, aliases like
`input.query(...)` are only supported in requests and programmatic lookup.'%}
See the [Query API reference](reference/query-api-reference.html)
for a list of the built-in query properties.

To deploy a query profile:

1. Create a file for the profile, using the format above,
   having the name *[my-profile-name].xml*,
   e.g. *MyProfile.xml* (replace any `/` in the name by `_`)
2. Put this in the directory *search/query-profiles* in
   the [application package](application-packages.html) root
3. [Redeploy](application-packages.html#deploy) the application package

Any number of query profile files may be added to this directory.
If the query profiles contains errors, like incorrect syntax and/or infinite reference loops, deployment will fail.

To use a query profile in a query request, send the name of the profile as the parameter `queryProfile`:

```
queryProfile=MyProfile
```

If the request does not specify a query profile,
the profile named `default` will be used.
If no `default` profile is configured, no profile will be used.
If the queryProfile parameter is set but does not resolve to an existing profile,
an error message is returned.
Example, set default query timeout to 200ms for all queries not using a query profile:

```
$ cat search/query-profiles/default.xml

<query-profile id="default">
    <field name="timeout">0.2</field>
</query-profile>
```

The query profile values (whether set from a configured query profile or by the request)
is available as *query properties*.
To look up a value from a [Searcher component](searcher-development.html), use:

```
query.properties().get("myVariable")
```

Note that property names are case-sensitive.

### Example

Use a query profile to modify the YQL query string
using an [IN](/en/reference/query-language-reference.html#in) operator
and [local substitution](#local-substitution) of *cities*:

```
{% highlight xml %}

    select * from restaurant where userQuery() and city in (%{cities})
    ""

{% endhighlight %}
```

Use [match: word](/en/reference/schema-reference.html#match) for the IN operator:

```
field city type string {
    indexing: summary | index
    match:    word
}
```

An example query passing the values for the IN operator to be substituted into the YQL string:

```
$ vespa query \
  queryProfile=city-filter \
  cities='"berlin","paris"' \
  query='what the user typed'
```

With this, the application can use the *city-filter* query profile if there are cities in the filter,
if empty, use a *no-filter* query profile:

```
{% highlight xml %}

    select * from restaurant where userQuery()

{% endhighlight %}
```
```
$ vespa query \
  queryProfile=no-filter \
  query='what the user typed'
```

### Overrides

The parameter values set in *MyProfile.xml* will be used
as if they were present directly in the request.
If a parameter is present both directly in the request and in a profile,
the request value takes precedence by default.
Individual query profile field can be made to take priority by setting
the [overridable](reference/query-profile-reference.html#overridable) attribute to `false`.
Example:

```
<query-profile id="default">
    <field name="timeout" overridable="false">0.2</field>
</query-profile>
```

## Nested Structure

To support structure in the set of request variables, a query profile
value may not be a string but a reference to another query profile.
In this case, the referenced query profile functions as a map
(or struct, if types are used, see below) in the referencing query profile.
The parameter names of the nested profile gets preceded by the name of the
reference variable and a dot. For example:

```
<query-profile id="MyProfile">
    <field name="hits">10</field>
    <field name="unique">merchantid</field>
    <field name="user"><ref>MyUserProfile</ref></field>
</query-profile>
```

Where the referenced profile might look like:

```
<query-profile id="MyUserProfile">
    <field name="age">20</field>
    <field name="profession">student</field>
</query-profile>
```

If `MyProfile` is referenced in a query now, it will contain the variables

```
hits=10
unique=merchantid
user.age=20
user.profession=student
```

References can be nested to provide a deeper structure,
producing variables having multiple dots.
The dotted variables can be overridden directly in the search request
(using the dotted name) just as other parameters.

Note that the id value of a profile reference can also be set in the request,
making it possible to choose not just the top level profile
but also any number of specific subprofiles in the request.
For example, the request can contain

```
queryProfile=MyUserProfile&user=ref:MyOtherUserprofile
```

to change the reference in the above example to some other subprofile.
Note the `ref:` prefix which is required to identify this
as setting user to a query profile referenced by id rather than setting it to a string.

## Inheritance

A query profile may inherit one or more other query profiles.
This is useful when there is some common set of parameters applicable to
multiple use cases, and a smaller set of parameters which varies between them.
To inherit another query profile, reference it as follows:

```
<query-profile id="MyProfile" inherits="MyBaseProfile">
    …
</query-profile>
```

The parameters of `MyBaseProfile` will be present when this
profile is used exactly as if they were explicitly written in this profile.

Multiple inheritance is supported by specifying multiple
space-separated profile ids in the inheritance attribute.
Order matters in this list - if a parameter is set in more than one of the inherited profiles,
the first one encountered in the depth first, left to right search order is used.

Parameters specified in the child query profile will always override the same parameters in an inherited one.

## Value Substitution

Query profile values may contain substitution strings on the form
`%{property-name}`. Example:

```
<query-profile id="MyProfile">
    <field name="message">Hello %{world}!</field>
    <field name="world">Earth</field>
</query-profile>
```

The value returned by looking up `message` will be *Hello Earth!*.

### Global resolution

Values are normally replaced by the value returned
from `query.properties().get("property-name")` *at the time of the lookup*.
Therefore, substituted values may be looked up in variants, in inherited profiles,
in values set at run time and by following query profile references. Details:
* No substitution will be performed *in* values set at run time
* If the value referenced in a substitution returns null,
  the reference is substituted by the empty string
* Unclosed substitutions cause an error at deploy time, but unknown values do not
  (they may exist at run time and will be replaced by an empty string if not)
* Recursive substitution works as expected. However, there is no loop detection

### Local substitution

To substitute by a value in the same query profile (or variant),
prefix the property by a dot, as in

```
<query-profile id="MyProfile">
    <field name="message">Hello %{.world}!</field>
    <field name="world">Earth</field>
</query-profile>
```

Local substitutions can be verified at deploy time and will cause an error if not found.

## Query Profile Variants

In some cases, it is convenient to allow the values returned from a
query profile to vary depending on the values of some properties input in the request.
For example, a query profile may contain values which depend on both the market
in which the request originated (`market`), the kind of device (`model`)
*and* the bucket in question (`bucket`).

Such variants over a set of request parameters may be represented in a single query profile,
by defining nested variants of the query profile for the relevant combinations of request values.
A complete example:

```
<query-profile id="multiprofile1"> <!-- A regular profile may define "virtual" children within itself -->

    <!-- Names of the request parameters defining the variant profiles of this. Order matters as described below.
         Each individual value looked up in this profile is resolved from the most specific matching virtual
         variant profile -->
    <dimensions>region,model,bucket</dimensions>

    <!-- Values may be set in the profile itself as usual, this becomes the default values given no matching
         virtual variant provides a value for the property -->
    <field name="a">My general a value</field>

    <!-- The "for" attribute in a child profile supplies values in order for each of the dimensions -->
    <query-profile for="us,nokia,test1">
        <field name="a">My value of the combination us-nokia-test1-a</field>
    </query-profile>

    <!-- Same as [us,*,*]  - trailing "*"'s may be omitted -->
    <query-profile for="us">
        <field name="a">My value of the combination us-a</field>
        <field name="b">My value of the combination us-b</field>
    </query-profile>

    <!-- Given a request which matches both the below, the one which specifies concrete values to the left
         gets precedence over those specifying concrete values to the right
         (i.e the first one gets precedence here) -->
    <query-profile for="us,nokia,*">
        <field name="a">My value of the combination us-nokia-a</field>
        <field name="b">My value of the combination us-nokia-b</field>
    </query-profile>
    <query-profile for="us,*,test1">
        <field name="a">My value of the combination us-test1-a</field>
        <field name="b">My value of the combination us-test1-b</field>
    </query-profile>

</query-profile>
```

### Variants and Inheritance

It is possible to define variants across several levels in an inheritance hierarchy.
The variant dimensions are inherited from parent to child,
with the usual precedence rules (depth first left to right),
so a parent profile may define the dimensions and the child the values over which it should vary.

Variant resolution within a profile has precedence over resolution in parents.
This means e.g. that a default value for a given property in a sub-profile will be chosen
over a perfect variant match in an inherited profile.

Variants may specify their own inherited profiles, as in:

```
<query-profile id="multiprofile1">
    …
    <query-profile for="us,nokia,test1" inherits="parent1 parent2">
        …
    </query-profile>
</query-profile>
```

Values are resolved in this profile and inherited profiles "interleaved" by the variant resolution order
(which is specificity by default). E.g. by decreasing priority:

```
1.   Highest prioritized variant value
2.   Value in inherited from highest prioritized variant
3.   Next highest prioritized variant value
4.   Value in inherited from next highest prioritized variant
…
n.   Value defined at top level in profile
n+1. Value in inherited from query profile
```

## Query Profile Types

The query profiles may optionally be *type checked*.
Type checking is turned on by referencing a *Query Profile Type* from the query profile.
The type lists the legal set of parameters of the query profile,
whether additional parameters are allowed, and so on.

A query profile type is referenced by:

```
<query-profile id="MyProfile" type="MyProfileType">
    …
</query-profile>
```

And the type is defined as:

```
<query-profile-type id="MyProfileType">
    <field name="age" type="integer"/>
    <field name="profession" type="string"/>
    <field name="user" type="query-profile:MyUserProfile">
</query-profile-type>
```

This specifies that these three parameters may be present in profiles using this type,
as well as the query profile type of the `user` parameter.

It is also possible to specify that parameters are mandatory,
that no additional parameters are allowed (strict),
to inherit other types and so on, refer to the full syntax in
[the query profile reference](reference/query-profile-reference.html#query-profile-types).
If the base profile type is strict, it *must* extend a built-in query profile type,
see the [strict reference documentation](reference/query-profile-reference.html#strict).

A query profile type is deployed by adding a file named *[query-profile-type-name].xml*
in the *search/query-profiles/types* directory in the application package.

Query profile types may be useful even if query profiles are not used to set values.
As they define the names, types and structure of the parameters which can be accepted in the search request,
they can also be used to define, restrict and check the content of search requests.
For example, as the built-in search api parameters are also type checked if a typed query profile is used,
types can be used to restrict the parameters that can be set in a request,
or to mandate that some are always set.
The built-in parameters are defined in a set of query profile types which are always present
and which can be inherited and referenced in application-defined types.
These built-in types are defined in the [Query API](reference/query-api-reference.html).

## Path Matching

By adding `<match path="true">` to a profile type,
*path* name matching is used rather than the default exact matching
when a profile is looked up from a name.
Path matching interprets the profile name as a slash separated path
and matches references which are subpaths (more specific paths) to super-paths.
The most specific match becomes the target of the reference. For example:

```
Given the query profile names:
  a1
  a1/b1

Then:
  a1/b1/c1/d1  resolves to a1/b1
  a1/b         resolves to a1
  a            does not resolve
```

This is useful to assign specific query profile id's to every client or bucket
without having to create a different configuration item for each of these cases.
If there is a need to provide a differentiated configuration for any such client or bucket in the future,
this can be done without having the client change its request parameter because a specific id is already used.

## Versioning

Query profiles (and types) may exist in multiple versions at the same time.
Wherever a name of a query profile (or type) is referenced,
the name may also append a version string, separated by a colon, e.g `MyProfile:1.2.3`.
The version number is *resolved* - if no version is given the highest version known is used.
If the version number is only partially specified, as in `my-version:1`,
the highest version starting by 1 is used.

Where a query profile (or type) is defined, the id may specify the version, followed by a colon:

```
<query-profile id="MyProfile:1.2.3">
  …
</query-profile>
```

Any sub-number omitted is taken to mean 0 where a version is defined,
so `id="MyProfile:1"` is the same as `"id=MyProfile:1.0.0"`.

Query profiles (and types) which specifies a version in their id
must use a file name which includes the same version string after the name,
separated by a dash, e.g. *MyProfile-1.2.3.xml*.

For more information on versions,
see [component versioning](reference/component-reference.html#component-versioning).

## Dump Tool

It can sometimes be handy to be able to dump resolved query profiles offline.
Run without arguments to get usage:

```
$ vespa-query-profile-dump-tool
```
