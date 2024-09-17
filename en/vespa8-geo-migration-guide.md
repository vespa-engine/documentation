---
# Copyright Vespa.ai. All rights reserved.
title: "Position fields - Vespa 8 migration"
---

Refer to [Vespa 8 release notes](vespa8-release-notes.html) -
this is a guide on how to migrate from Vespa 7 to Vespa 8 when using position fields.
The guide is relevant for applications having a `position` field in a schema.

For the rest of this document, we assume a schema containing:
```
field myfield type position {...}
```


## Step 1: Upgrade to Vespa 8 in geo legacy mode
Add to _services.xml_, see [legacy-v7-json-rendering](reference/default-result-format.html#geo-position-rendering),
add under the root `services` tag:
```xml
<services>
    <legacy>
        <v7-geo-positions>true</v7-geo-positions>
    </legacy>
```



## Step 2: Result rendering
If the position field is only used as a filter, and not returned in result sets, skip this section. 
In Vespa 7, a position filed could be rendered as:
```json
"myfield.position": {
    "y": 63453700,
    "x": 10460800,
    "latlong": "N63.453700;E10.460800"
}
```
and optionally:
```json
"myfield": {
    "y": 63453700,
    "x": 10460800
}
```
With Vespa 8, the result format is changed to:
```json
"myfield": {
    "lat": 63.4537,
    "lng": 10.4608
}
```
Note that this is also the Vespa 8 feeding format. 

{% include important.html content="Change all code that parses query results to expect the new format.
This includes programs that parses the result JSON and [Searchers](searcher-development.html)." %}

On Vespa 7, the `distance` rank feature is output as:
```
"myfield.distance": 14352,
```
On Vespa 8, use the summary feature instead:
```
distance(myfield).km
```


## Step 3: Query API
Change from using the `pos.ll` / `pos.radius` / `pos.bb` / `pos.attribute` parameters, e.g.:
```
pos.ll=63.4225N+10.3637E&pos.radius=5km
```
to using [YQL](query-language.html):
```
where geoLocation(myfieldname, 63.5, 10.5, "5 km")
```


## Step 4: Feeding format and /document/v1/ API

The Vespa 7 feeding format can be used on Vespa 8,
it is however recommended changing to:
```json
"myfield": {
    "lat": 63.4537,
    "lng": 10.4608
}
```
This is the same format as in query results.

The result format when using GET / VISIT in [document/v1/](reference/document-v1-api-reference.html) is changed from:
```json
"myfield": {
    "y": 63453700,
    "x": 10460800
}
```
to:
```json
"myfield": {
    "lat": 63.4537,
    "lng": 10.4608
}
```
