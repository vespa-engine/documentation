---
# Copyright Vespa.ai. All rights reserved.
title: "Filter intersections reference"
---

This is the reference for `FilterIntersectionsSearcher`, which counts how many
results a query would have with each named filter, and each combination of
filters, added. Refer to the [filter intersections guide](../../querying/filter-intersections.html)
for an introduction, setup and caveats.

Each combination of filters is called a *cell* and is counted by its own query.

## Query parameters

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
      <td>String joining filter names into a bucket's <code>key</code>, see <a href="#result-format">Result format</a>.</td>
    </tr>
  </tbody>
</table>

A filter's `where` accepts anything valid after the `where` keyword in a
[YQL](yql.html) query, including `@parameter` substitution. Some operators give
lower-bound counts, see the [caveats](../../querying/filter-intersections.html#caveats).

## Result format

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
        Same accuracy as <a href="default-result-format.html#totalcount">totalCount</a>:
        exact, except a lower bound when <code>weakAnd</code>, <code>wand</code>,
        <code>nearestNeighbor</code> or a range with <code>hitLimit</code> is used.
      </td>
    </tr>
  </tbody>
</table>

## How a cell query is built

A cell is a copy of the query with these changes:

* The cell's filters are added with AND.
* `hits` and `offset` are set to 0.
* [summary](../api/query.html#presentation.summary), grouping and
  [soft timeout](../api/query.html#ranking.softtimeout.enable) are turned off.

Everything else, including the rank profile, `sources` and any `@parameter` values,
is kept. Filters are parsed separately and combined as query trees, never pasted into
the YQL text, so a filter cannot change the meaning of the query.

In [streaming mode](../../performance/streaming-search.html), content nodes replace
the rank profile with `unranked` for any query with zero hits and no grouping. Cells
therefore run with `unranked` there, not the query's rank profile.

## Number of cells

With $$ n $$ filters and $$ d $$ dimensions, the number of cells is:

$$ \text{cells}(n, d) = \sum_{k=1}^{\min(d, n)} \binom{n}{k} = \sum_{k=1}^{\min(d, n)} \frac{n!}{k!\,(n-k)!} $$

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

A request producing more than `filterIntersections.maxCells` cells is rejected with:

```
14 filters at 4 dimensions give 1470 cells, more than the default limit of 1000 (raise it with filterIntersections.maxCells)
```

## Execution

* All cells are submitted concurrently to the container's shared request thread pool,
  together with the original query. Latency is roughly that of the slowest cell
  while threads are free. On a saturated container, cells may run one after another and
  miss the deadline.
* Each cell may use up to the remaining time of the request's `timeout`.
* Content node load grows linearly with the number of cells.
* Since soft timeout is off, a cell either covers the full corpus or is reported as
  degraded. Degraded cells are omitted, never returned with a partial count.

## Errors

<table class="table">
  <thead>
    <tr><th>Situation</th><th>Effect</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>Filters JSON invalid, filter without name or <code>where</code>, duplicate name, invalid YQL in a <code>where</code>,
          <code>dimensions</code> or <code>maxCells</code> below 1, or cell count above <code>maxCells</code></td>
      <td>Whole request fails with error code 4, <code>INVALID_QUERY_PARAMETER</code>, naming the problem,
          for example <code>Filter 'broken': invalid YQL: ...</code>. Nothing is sent to the content nodes.</td>
    </tr>
    <tr>
      <td>A cell's query returns an error from the content nodes</td>
      <td>That bucket is omitted. The error is added to <code>root.errors</code>, prefixed with <code>Intersection cell '&lt;key&gt;':</code>.
          Other buckets and the main result are unaffected.</td>
    </tr>
    <tr>
      <td>A cell's query has degraded coverage (timeout, node down)</td>
      <td>That bucket is omitted. An error with the coverage reached is added to <code>root.errors</code>, for example
          <code>Intersection cell 'brand&amp;instock': degraded coverage (50%), count not exact</code>.</td>
    </tr>
    <tr>
      <td>A filter matches nothing</td>
      <td>Not an error. Its cells get <code>totalCount</code> 0.</td>
    </tr>
    <tr>
      <td>No <code>filterIntersections.filters</code>, or an empty array</td>
      <td>The searcher does nothing. No <code>filterIntersections</code> field in the result.</td>
    </tr>
  </tbody>
</table>
