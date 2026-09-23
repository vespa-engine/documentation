---
# Copyright Vespa.ai. All rights reserved.
title: "Filter intersections"
---

Filter intersections tell you how many results your query would have if
you narrowed it down with one or more additional filters, without actually
narrowing it down. One query gives you the count for every filter and every
combination of filters, where you would otherwise need one query per combination.

A *filter* here is a named condition written in YQL, the same syntax you use after
`where` in a query. For example `brand contains "nike"` or `stock > 0`. You give
each filter a short name, such as `brand` or `instock`, and that name is how the
filter is identified in the response. A filter is *intersected* with your query
when both must hold: `brand contains "nike"` intersected with "all shoes" is "all
Nike shoes".

Each count is produced by a copy of your query with the filters added, asking for
zero hits. It therefore costs less than a full query while behaving exactly like
one: same rank profile, same operators, same rules for what is counted. Every
Vespa response already carries one such number for the query itself, called
`totalCount`, and the filter intersection counts are computed the same way, so
they are directly comparable to it. The counts are as exact as the operators you
use: exact for ordinary filters, and a lower bound if the query or a filter uses
an operator that stops before it has seen every matching document, see
[which operators give exact counts](#which-operators-give-exact-counts).
This makes them well suited to understanding a data set or a result set, while
[grouping](grouping.html) remains the tool for aggregating over the result your
query returns.

When using filter intersections, you send a normal query, for example "all shoes",
together with a list of named filters, for example "brand is Nike", "in stock" and
"on sale". Vespa runs your
query as usual and returns its hits. In addition, it counts how many of your
query's results also satisfy each filter, and how many satisfy each
combination of filters: every pair by default, and every triple, quadruple and
beyond if you ask for it. All counts are returned in the same response, so a
single query answers both "what are the results" and "how many results would
be left if one filter, or several, were added". The second answer is a set of
counts, not a set of documents: you learn how many, not which.

Every count includes your query. In the shoe example, the count for "in stock"
means "shoes that are in stock", never "everything in stock in the whole data set".
You choose how many filters to combine at once with
one parameter. Two is the default. Higher values give a more complete picture
but add computational cost, since there are more combinations to count, see
[Controlling depth and cost](#controlling-depth-and-cost).

For the shoe example, the counts could look like this:

<table class="table">
  <thead>
    <tr><th class="is-center" style="min-width: 28em">Filters added to the "all shoes" query</th><th class="is-center" style="min-width: 14em">Matching shoes</th></tr>
  </thead>
  <tbody>
    <tr><td class="is-center">Nike</td><td class="is-center">300</td></tr>
    <tr><td class="is-center">In stock</td><td class="is-center">900</td></tr>
    <tr><td class="is-center">On sale</td><td class="is-center">200</td></tr>
    <tr><td class="is-center">Nike <em>and</em> in stock</td><td class="is-center">240</td></tr>
    <tr><td class="is-center">Nike <em>and</em> on sale</td><td class="is-center">60</td></tr>
    <tr><td class="is-center">In stock <em>and</em> on sale</td><td class="is-center">150</td></tr>
  </tbody>
</table>

Without filter intersections you would need seven queries to produce this table:
one for the search results, and one more per row. With filter intersections you
send your query once, with the filters attached. Vespa runs the six counts at the
same time as the query itself and returns everything in one response: the search
results and all the counts.



## How it works

When Vespa receives a query, it passes it through a series of processing steps
before sending it to the nodes that hold your data. Each step is a small component
called a [searcher](../applications/searchers.html), and the ordered series is called
a [search chain](../applications/chaining.html). Filter intersections is one such searcher. It ships with Vespa,
so you write no code: you turn it on by listing it in your application's
configuration, as shown under [Setting it up](#setting-it-up).

Once turned on, the searcher stays passive until you ask for counts. You do that
by sending your list of filters along with the query, as an extra query parameter
named `filterIntersections.filters`. How to write it is shown under
[Querying with filter intersections](#querying-with-filter-intersections). A query that does not include this parameter is not
affected in any way.

When a request contains filters, the searcher:

1. Reads the list of named filters you sent along with your query.
   Each filter is a name plus a condition written in YQL, the same kind of
   condition you write after `where` in a query.
2. Works out which combinations of filters to count. Each combination is called
   a *cell*. First every filter on its own, then every pair of filters, then
   every group of three, and so on up to a limit you control with the
   `filterIntersections.dimensions` parameter. The default limit is 2, so by
   default you get singles and pairs, see
   [Combining more filters at a time](#combining-more-filters-at-a-time).
   In the shoe example, with the three filters
   named `brand`, `instock` and `onsale`, that gives six cells: `brand`, `instock`
   and `onsale` on their own, plus the three pairs `brand&instock`,
   `brand&onsale` and `instock&onsale`. The `&` joins the names of the filters
   in a cell into its key, which is how you find the cell in the response.
   The `&` is the default and can be changed with `filterIntersections.separator`,
   see [Query parameters](#query-parameters).
3. Turns every cell into a query of its own. Each one is a copy of your query
   with the cell's filters added to its `where` condition, so the `brand&instock`
   cell becomes "shoes, and brand is Nike, and in stock". These copies ask for
   nothing but a count: no hits, no document summaries. All of them
   are sent to the nodes that hold your data at the same time as your original
   query, so the counts arrive in parallel rather than one after the other.
4. Collects the counts as they come back and adds them to the response, one
   entry per cell under the name `filterIntersections`, next to the ordinary
   search results. What this looks like is shown under
   [Read the result](#step-4-read-the-result).

Your original query runs unchanged. The hits, grouping and ranking you asked for
are returned exactly as if the searcher was not there. The counts are added
on the side.

<img src="/assets/img/filter-intersections.svg" alt="One request fans out to one count query per filter combination, and the counts are collected into the result" width="810" style="display: block; margin: 1em auto;"/>

A cell is your query plus some filters, nothing else is changed. It uses the same
[rank profile](../ranking/ranking-intro.html), so query inputs the profile
declares, such as the tensor a `nearestNeighbor` filter needs, and
[match-phase](../reference/schemas/schemas.html#match-phase) limits apply to the
cell as well. Because a cell asks for zero hits, Vespa skips scoring for it
whenever it can, which keeps cells cheap. A cell's count is therefore the
`totalCount` you would see if you added those filters to your query yourself,
with one exception: a first-phase
[rank-score-drop-limit](../reference/schemas/schemas.html#rank-score-drop-limit)
removes documents from your query's `totalCount` but not from a cell's count,
since a cell never computes the score the limit would compare against.

### Which operators give exact counts

A cell is a real query, so its count is as accurate as `totalCount` is for a
normal query. That accuracy depends on the operators used in the query and in the
filters. Most [YQL operators](../reference/querying/yql.html) look at every
document that could match, so their counts are exact:
[contains](../reference/querying/yql.html#contains),
[numeric comparisons and range](../reference/querying/yql.html#numeric),
[in](../reference/querying/yql.html#in),
[and](../reference/querying/yql.html#and),
[or](../reference/querying/yql.html#or),
[not](../reference/querying/yql.html#not),
[phrase](../reference/querying/yql.html#phrase),
[near](../reference/querying/yql.html#near),
[sameElement](../reference/querying/yql.html#sameelement),
[geoLocation](../reference/querying/yql.html#geolocation),
[matches](../reference/querying/yql.html#matches),
[fuzzy](../reference/querying/yql.html#fuzzy),
[predicate](../reference/querying/yql.html#predicate),
[dotProduct](../reference/querying/yql.html#dotproduct),
[weightedSet](../reference/querying/yql.html#weightedset),
[rank](../reference/querying/yql.html#rank) and
[equiv](../reference/querying/yql.html#equiv).

A few operators are built to find the *best* documents rather than *all* of them.
They stop once they have enough good candidates, and documents they never looked
at are never counted. With these, the count is a lower bound: the true number of
matches is at least that high, and possibly higher.

<table class="table">
  <thead>
    <tr><th>Operator</th><th>Why the count is a lower bound</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="../reference/querying/yql.html#weakand">weakAnd</a></td>
      <td>
        Keeps only the <a href="../reference/querying/yql.html#targethits">targetHits</a>
        best-scoring documents per content node, 100 by default. Once it has that many, it skips
        every document that cannot score higher than the ones it already holds.
        The count is exact only when fewer documents match than <code>targetHits</code>.
      </td>
    </tr>
    <tr>
      <td><a href="../reference/querying/yql.html#wand">wand</a></td>
      <td>Same mechanism as <code>weakAnd</code>, over a weighted set of tokens.</td>
    </tr>
    <tr>
      <td><a href="../reference/querying/yql.html#nearestneighbor">nearestNeighbor</a></td>
      <td>
        Returns the <a href="../reference/querying/yql.html#targethits">targetHits</a> closest
        documents per content node, however far away they are, whether the search is exact or
        uses an <a href="approximate-nn-hnsw.html">HNSW index</a>. On its own it is therefore not a filter: it always finds
        <code>targetHits</code> documents. To make it one, add the
        <a href="../reference/querying/yql.html#distancethreshold">distanceThreshold</a>
        annotation to exclude documents beyond a distance, and set <code>targetHits</code>
        high enough to cover every document within that distance. The count is still capped
        at <code>targetHits</code> per node.
      </td>
    </tr>
    <tr>
      <td>range with <a href="../reference/querying/yql.html#hitlimit">hitLimit</a></td>
      <td>
        The <code>hitLimit</code> annotation makes a range look at only the first
        <code>hitLimit</code> values in the range. A range without it is exact.
      </td>
    </tr>
  </tbody>
</table>

{% include important.html content='Free text is easy to get wrong here.
<a href="../reference/querying/yql.html#userinput">userInput()</a> turns the text into a
<code>weakAnd</code> by default, and so does the plain
<a href="../reference/api/query.html#query">query</a> request parameter. A base query such as
<code>userInput(@q)</code> therefore gives lower-bound counts. To get exact counts, set the
<a href="../reference/querying/yql.html#grammar">grammar</a> annotation to <code>all</code> or
<code>any</code> on <code>userInput()</code>, or set the
<a href="../reference/api/query.html#model.type">type</a> request parameter accordingly.
Filters that must count exactly should use explicit operators such as <code>contains</code>.' %}



## When to use filter intersections, and when to use grouping

[Grouping](grouping.html) is Vespa's general aggregation feature. It can count too,
but it can also sum, average, find minimum and maximum values, list the top hits
per group, and nest groups inside groups. Filter intersections only count. Since
both can answer "how many", it helps to know which tool fits:

<table class="table">
  <thead>
    <tr><th></th><th>Grouping</th><th>Filter intersections</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Counts what</td>
      <td>Each distinct <em>value</em> of one attribute field, such as every brand</td>
      <td>Each named <em>filter expression</em>, and combinations of them</td>
    </tr>
    <tr>
      <td>Filter can be</td>
      <td>An attribute value</td>
      <td>Any YQL <code>where</code> fragment: ranges, geo, <code>sameElement</code>, boolean logic, and so on</td>
    </tr>
    <tr>
      <td>Combinations</td>
      <td>Nested groups over fixed fields</td>
      <td>Every pair (or triple, and so on) of the filters you name</td>
    </tr>
    <tr>
      <td>Ranking</td>
      <td>Runs inside your query, over the documents your query returns</td>
      <td>Each cell is a copy of your query with the same rank profile, asking for zero hits</td>
    </tr>
    <tr>
      <td>Cost</td>
      <td>One query, aggregation done on the content nodes</td>
      <td>One extra count query per cell</td>
    </tr>
  </tbody>
</table>

Use grouping when you want counts per value of a field, such as "how many products
per brand", or when you want more than a count per bucket, such as sums or averages.
Use filter intersections when your filters are not single field values, or when you
need to know how filters combine, such as "how many Nike shoes are both on sale
and in stock", for example to explore a data set.



## Setting it up

### Step 1: Add the searcher to a search chain

Open [services.xml](../reference/applications/services/search.html) in your
application package. Find your `<container>` element,
and inside it the `<search>` element. If you have no `<search>` element yet, add one
directly inside `<container>`. Then add a chain with the searcher:

```xml
<services version="1.0">

    <container id="default" version="1.0">
        <document-api/>

        <search>
            <chain id="default" inherits="vespa">
                <searcher id="ai.vespa.search.counting.FilterIntersectionsSearcher"/>
            </chain>
        </search>
    </container>

    <content id="products" version="1.0">
        <!-- Your content cluster, unchanged -->
    </content>

</services>
```

`<chain id="default" inherits="vespa">` declares the search chain that handles
requests that do not ask for a specific chain. `inherits="vespa"` pulls in all
the built-in searchers, so the rest of query processing keeps working as before.
If you already have a chain with `id="default"`, add the `<searcher>` line inside
that chain instead of adding a second one. You can also give the searcher a
chain of its own, shown below.

{% include note.html content="The searcher is inactive unless a request contains
<code>filterIntersections.filters</code>, so adding it to the default chain does not
change the behavior or cost of your other queries." %}

If you prefer to keep it out of the default chain, put it in a chain of its own and
select that chain per request with the `searchChain` query parameter:

```xml
<search>
    <chain id="with-counts" inherits="vespa">
        <searcher id="ai.vespa.search.counting.FilterIntersectionsSearcher"/>
    </chain>
</search>
```

Queries then select this chain by adding the
[searchChain](../reference/api/query.html#searchchain) query parameter,
for example `vespa query 'yql=...' searchChain=with-counts`.

### Step 2: Deploy

Deploy the application package to Vespa Cloud as usual, see
[Deploy an application](../basics/deploy-an-application.html):

```
$ vespa deploy --wait 600
```

The same command deploys to a self-managed Vespa when the CLI target points to it.



## Querying with filter intersections

To get filter intersection counts, send your normal query and add one query
parameter, `filterIntersections.filters`, holding the filters. That is all that is
required. Three more parameters adjust how many filters are combined, how many
cells are allowed and how keys are written. They all have defaults and are listed
under [Query parameters](#query-parameters) in the reference at the bottom of this page.

### Step 1: Write your base query

Start with the query you would send anyway. The filters are intersected with this
query, so the counts describe subsets of this result set, not of the whole corpus.
Using the shoe example:

```
select * from sources product where category contains "shoes"
```

### Step 2: Define the filters

The filters parameter is a JSON array. Each element has a `name`, which you choose
and which identifies the filter in the result, and a `where`, which is a YQL
`where` expression written against your [schema](../basics/schemas.html):

```json
[
  { "name": "brand",   "where": "brand contains \"nike\"" },
  { "name": "instock", "where": "stock > 0" },
  { "name": "onsale",  "where": "discount > 0" }
]
```

Rules for filters:

* Names must be unique within a request and must not be empty.
* `where` is any expression that is valid after the `where` keyword in a query.
  Ranges, `in`, `geoLocation`, `sameElement`, `userInput`, boolean operators and
  parentheses all work. See the [YQL reference](../reference/querying/yql.html)
  for the full list.
* You can use `@parameter` substitution inside `where`, just as in the main query.
  A filter `{"name": "brand", "where": "brand contains @wantedBrand"}` reads the
  `wantedBrand` request parameter.
* The order you list filters in does not matter. The searcher sorts them by name
  (case-insensitive) so the output order is stable.

### Step 3: Send the request

Using the [Vespa CLI](../clients/vespa-cli.html):

```
$ vespa query \
    'yql=select * from sources product where category contains "shoes"' \
    'hits=10' \
    'filterIntersections.filters=[{"name":"brand","where":"brand contains \"nike\""},{"name":"instock","where":"stock > 0"},{"name":"onsale","where":"discount > 0"}]'
```

You can also send the same request as an HTTP POST with a JSON body. Two things
change: the filters are written as a normal JSON array instead of a string, and
the parameter name `filterIntersections.filters` is split on the dot into a
`filterIntersections` object with a `filters` field inside it:

```
$ curl --cert data-plane-public-cert.pem --key data-plane-private-key.pem \
    -H "Content-Type: application/json" \
    --data '{
      "yql": "select * from sources product where category contains \"shoes\"",
      "hits": 10,
      "filterIntersections": {
        "filters": [
          { "name": "brand",   "where": "brand contains \"nike\"" },
          { "name": "instock", "where": "stock > 0" },
          { "name": "onsale",  "where": "discount > 0" }
        ]
      }
    }' \
    $ENDPOINT/search/
```

`$ENDPOINT` is your application's endpoint, which `vespa status --format=plain`
prints, and the certificate and key are the data plane credentials you got when
deploying to Vespa Cloud.

Both examples ask for ten hits from the base query, with `hits=10`. If you only
want the counts and no search results at all, set `hits=0` on the base query
instead. The filter intersection counts are the same either way, since cells
always ask for zero hits themselves.

### Step 4: Read the result

The counts are in `root.fields.filterIntersections.buckets`, next to the usual
`totalCount`. The hits are in `root.children` as always:

```json
{
  "root": {
    "id": "toplevel",
    "relevance": 1.0,
    "fields": {
      "totalCount": 1200,
      "filterIntersections": {
        "buckets": [
          { "key": "brand",           "names": ["brand"],            "totalCount": 300 },
          { "key": "instock",         "names": ["instock"],          "totalCount": 900 },
          { "key": "onsale",          "names": ["onsale"],           "totalCount": 200 },
          { "key": "brand&instock",   "names": ["brand", "instock"], "totalCount": 240 },
          { "key": "brand&onsale",    "names": ["brand", "onsale"],  "totalCount": 60  },
          { "key": "instock&onsale",  "names": ["instock", "onsale"],"totalCount": 150 }
        ]
      }
    },
    "coverage": { "coverage": 100, "documents": 48211, "full": true, "nodes": 2, "results": 1, "resultsFull": 1 },
    "children": [
      { "id": "id:product:product::sku-1001", "relevance": 0.87, "fields": { "..." : "..." } }
    ]
  }
}
```

How to read it:

* `fields.totalCount` (1200) is the number of shoes matching the base query alone.
  This is the ordinary `totalCount`, untouched. Each bucket's `totalCount` is
  computed the same way, so the numbers are directly comparable.
* Each bucket is one cell. `names` lists the filters that were combined,
  `key` is the same names joined with the separator (default `&`) for convenient
  lookup, and `totalCount` is the number of documents matching the base query
  *and* every filter in `names`.
* So `brand&instock` = 240 means 240 shoes are Nike and in stock. Since `brand`
  alone is 300, the remaining 60 Nike shoes must be out of stock.
* Buckets are ordered by size first: all singles, then all pairs, then triples and
  so on up to the `filterIntersections.dimensions` you asked for. Within each size
  they are ordered by name.

To find the count for a single filter, look up the bucket whose `key` equals the
filter name. To find the count for a combination, join the filter names in
case-insensitive sorted order with the separator, and look up that key.



## Controlling depth and cost

Each cell is one extra count query against your content nodes, so the number of
cells decides the cost of a request. Two parameters control it:
`filterIntersections.dimensions` sets how many filters are combined per cell, and
`filterIntersections.maxCells` caps how many cells a request may produce.

### Combining more filters at a time

`filterIntersections.dimensions` is the maximum number of filters combined in one
cell. The default is 2, which gives every single filter and every pair. Set it to
1 to get only the single-filter counts, or to 3 to also get every triple. Any
value of 1 or more is allowed. The only limit is the total number of cells it
produces, which must stay within `filterIntersections.maxCells`, see below.

You cannot combine more filters than you have, so a `dimensions` value above the
number of filters simply acts as if it were equal to it. For example, with two
filters and `dimensions=5`, you get the two filters on their own plus the one
pair, three cells in total, the same as `dimensions=2` would give.

### How many cells a request produces

With $$ n $$ filters and $$ d $$ dimensions, the number of cells is the number of
ways to choose 1, 2, and so on up to $$ d $$ of the filters, where the order of
the chosen filters does not matter. That is a sum of binomial coefficients:

$$ \text{cells}(n, d) = \sum_{k=1}^{\min(d, n)} \binom{n}{k} = \sum_{k=1}^{\min(d, n)} \frac{n!}{k!\,(n-k)!} $$

For the shoe example, three filters at two dimensions,
$$ \binom{3}{1} + \binom{3}{2} = 3 + 3 = 6 $$ cells. The sum grows quickly:

<table class="table">
  <thead>
    <tr><th class="is-center">Filters</th><th class="is-center">dimensions=1</th><th class="is-center">dimensions=2</th><th class="is-center">dimensions=3</th></tr>
  </thead>
  <tbody>
    <tr><td class="is-center">3</td><td class="is-center">3</td><td class="is-center">6</td><td class="is-center">7</td></tr>
    <tr><td class="is-center">5</td><td class="is-center">5</td><td class="is-center">15</td><td class="is-center">25</td></tr>
    <tr><td class="is-center">10</td><td class="is-center">10</td><td class="is-center">55</td><td class="is-center">175</td></tr>
    <tr><td class="is-center">14</td><td class="is-center">14</td><td class="is-center">105</td><td class="is-center">469</td></tr>
    <tr><td class="is-center">20</td><td class="is-center">20</td><td class="is-center">210</td><td class="is-center">1350</td></tr>
  </tbody>
</table>

Twenty filters at three dimensions means 1350 count queries per request. Whether
that is acceptable depends on your cluster and your latency budget. The formula
and the table let you work out the number of cells for a request before you send it.

### Limiting the number of cells

`filterIntersections.maxCells` is a safety limit on the number of cells, default 1000.
A request that would produce more cells than this is rejected before anything is
sent to the content nodes, with an error like:

```
14 filters at 4 dimensions give 1470 cells, more than the default limit of 1000 (raise it with filterIntersections.maxCells)
```

The limit is inclusive: exactly `maxCells` cells is allowed. You can lower it to
protect your cluster from expensive requests, or raise it if you have measured
that your cluster handles the load. If your cluster serves clients you do not
control, pin it in a [query profile](query-profiles.html) with
[overridable="false"](../reference/querying/query-profiles.html#overridable),
since otherwise a request parameter overrides the profile value.

### Performance

Keep these points in mind when sizing a cluster that serves filter intersections:

* **Load scales with cells, latency does not.** Cells are submitted concurrently
  to the container's request thread pool, so as long as it has free threads,
  request latency is roughly the slowest single count query. Content node load,
  however, grows linearly with the number of cells, since each is a full match
  over the posting lists of the base query plus its filters. Ten cells is ten times
  the matching work of one query.
* **Cells do the minimum work a count query can.** They request zero hits, fetch no
  document summaries and carry no grouping. With zero hits Vespa skips scoring
  unless the query contains `nearestNeighbor`, `weakAnd` or `wand`, which score
  internally to decide what matches. If it does, every cell pays for scoring,
  second phase included, so a cheap rank profile keeps cells cheap.
* **Cells share the request timeout.** Each cell may use up to the remaining time of
  the request. A request with many cells needs a timeout that accommodates them
  running side by side on the content nodes. Cells run on the container's shared
  thread pool, so on a container that is already saturated some cells may end up
  running one after another and miss the deadline.
* **Fast filters make fast cells.** Filters over attributes with
  [fast-search](../content/attributes.html#fast-search) match far faster than
  filters that must scan attribute values.




## Errors and partial results

Filter intersections never returns a wrong count silently. A count is either exact
or missing, with an error explaining why.

**Invalid input rejects the whole request.** If something is wrong with the
filters or the parameters, for example a filter with invalid YQL, the request
fails with an `INVALID_QUERY_PARAMETER` error before anything is sent to the
content nodes. No counts are returned, and the error names what was wrong:

```json
"errors": [
  {
    "code": 4,
    "summary": "Invalid query parameter",
    "message": "Filter 'broken': invalid YQL: ..."
  }
]
```

The full list of rejected inputs is in the [errors reference](#errors) at the
bottom of this page.

**A failing cell is dropped, not guessed.** If one cell's query fails on the
content nodes, that bucket is omitted from `buckets`, and an error is added to
`root.errors` with the cell's key in its message. The other buckets and your main
result are returned as normal.

**A degraded cell is dropped too.** Every cell runs with soft timeout disabled,
so a cell either searches the full corpus or is reported as degraded. If a cell
times out or hits a node that is down, its count would be too low, so it is omitted
and an error is added instead, with the coverage percentage it reached:

```
Intersection cell 'brand&instock': degraded coverage (50%), count not exact
```

When you see these, the request `timeout` is usually too short for the number of
cells, or a content node is unavailable. See
[graceful degradation](../performance/graceful-degradation.html) for how Vespa
handles timeouts and coverage in general.

**A filter that matches nothing is not an error.** Its cell, and every cell it is
part of, simply gets a count of 0.



## Reference

### Query parameters

All parameters are read by `FilterIntersectionsSearcher` and only have an effect
when the searcher is in the search chain that handles the request.

<table class="table">
  <thead>
    <tr><th>Parameter</th><th>Type</th><th>Default</th><th>Description</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>filterIntersections.filters</code></td>
      <td>String (JSON)</td>
      <td>none</td>
      <td>
        A JSON array of objects, each with a non-empty <code>name</code> and a non-empty
        YQL <code>where</code> expression. Names must be unique.
        When absent or an empty array, the searcher does nothing.
      </td>
    </tr>
    <tr>
      <td><code>filterIntersections.dimensions</code></td>
      <td>Integer</td>
      <td>2</td>
      <td>
        Maximum number of filters combined in one cell. Must be at least 1.
        Values above the number of filters are clamped.
      </td>
    </tr>
    <tr>
      <td><code>filterIntersections.maxCells</code></td>
      <td>Integer</td>
      <td>1000</td>
      <td>
        Maximum number of cells (and hence count queries) per request, inclusive.
        Must be at least 1. Requests exceeding it are rejected before reaching the content nodes.
      </td>
    </tr>
    <tr>
      <td><code>filterIntersections.separator</code></td>
      <td>String</td>
      <td><code>&amp;</code></td>
      <td>String joining filter names into a bucket's <code>key</code>, see <a href="#result-format">Result format</a> below.</td>
    </tr>
  </tbody>
</table>

### Result format

Added to the result as the field `filterIntersections` under `root.fields`,
only when the searcher processed filters:

<table class="table">
  <thead>
    <tr><th>Field</th><th>Type</th><th>Description</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>filterIntersections.buckets</code></td>
      <td>Array of objects</td>
      <td>One entry per cell that produced an exact count, ordered by number of filters, then by key.</td>
    </tr>
    <tr>
      <td><code>buckets[].key</code></td>
      <td>String</td>
      <td>The filter names in this cell, sorted case-insensitively and joined with the separator.</td>
    </tr>
    <tr>
      <td><code>buckets[].names</code></td>
      <td>Array of strings</td>
      <td>The filter names in this cell, sorted case-insensitively.</td>
    </tr>
    <tr>
      <td><code>buckets[].totalCount</code></td>
      <td>Integer</td>
      <td>
        Number of documents matching the base query and all filters in <code>names</code>.
        Same accuracy as <a href="../reference/querying/default-result-format.html#totalcount">totalCount</a>:
        exact, except a lower bound when <code>weakAnd</code>, <code>wand</code> or <code>nearestNeighbor</code> is used.
      </td>
    </tr>
  </tbody>
</table>

### How a cell query is built

A cell is a copy of your query with three changes: the cell's filters are added
with AND, `hits` and `offset` are set to 0, and
[summary](../reference/api/query.html#presentation.summary), grouping and
[soft timeout](../reference/api/query.html#ranking.softtimeout.enable) are turned off. Everything else, including the rank profile, `sources` and any
`@parameter` values, is kept. Filters are parsed separately and combined as query
trees, never pasted into the YQL text, so a filter cannot change the meaning of
your query.

### Errors

<table class="table">
  <thead>
    <tr><th>Situation</th><th>Effect</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Filters JSON invalid, filter without name or <code>where</code>, duplicate name, invalid YQL in a <code>where</code>,
          <code>dimensions</code> or <code>maxCells</code> below 1, or cell count above <code>maxCells</code></td>
      <td>Whole request fails with error code 4, <code>INVALID_QUERY_PARAMETER</code>. Nothing is sent to the content nodes.
          <code>buckets</code> is empty.</td>
    </tr>
    <tr>
      <td>A cell's query returns an error from the content nodes</td>
      <td>That bucket is omitted. The error is added to <code>root.errors</code>, prefixed with <code>Intersection cell '&lt;key&gt;':</code>.
          Other buckets and the main result are unaffected.</td>
    </tr>
    <tr>
      <td>A cell's query has degraded coverage (timeout, node down)</td>
      <td>That bucket is omitted. A timeout or backend communication error is added to <code>root.errors</code>
          with the coverage percentage reached.</td>
    </tr>
    <tr>
      <td>No <code>filterIntersections.filters</code>, or an empty array</td>
      <td>The searcher does nothing. No <code>filterIntersections</code> field in the result.</td>
    </tr>
  </tbody>
</table>
