---
# Copyright Vespa.ai. All rights reserved.
title: "Grouping Information in Results"
---

const DEFAULT_GROUPING = "all( group(customer) each(output(sum(price))) )";
const useLocalHostProxy = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
function setGroupingParam(groupingVal) {
const currentUrl = new URL(window.location.href); // Get the current URL
const urlParams = new URLSearchParams(currentUrl.search);
urlParams.set('grouping', groupingVal); // Set or update the query parameter
currentUrl.search = urlParams.toString();
window.history.pushState({}, '', currentUrl);
}
function flattenFields(node) {
if (!node.fields) return node;
return {
...node,
...node.fields, // spread fields to top level
fields: undefined // optional: remove nested 'fields' key
};
}
function getSearchUrl(yql){
const encodedYql = encodeURIComponent(yql);
const vespaUrl = `https://api.search.vespa.ai/search/?yql=${encodedYql}`
if (useLocalHostProxy){
// use the local proxy to avoid CORS issues
return `https://api.allorigins.win/get?url=${encodeURIComponent(vespaUrl)}`;
}
return vespaUrl;
}
/**
* when developing locally, we use a proxy to avoid CORS issues.
* this proxy return the response in a different format, so we need to parse it.
**/
function handleProxyRequest(request){
if (useLocalHostProxy){
return JSON.parse(request.contents);
}
return request;
}
function executeGroupingFromTheContainer(container) {
const yql = container.querySelector('#grouping-query-input').value;
const resultContainer = container.querySelector('#table-container');
executeGrouping(yql, resultContainer);
}
function onKeyDown(event, elem) {
if (event.key === 'Enter'){
executeGroupingFromTheContainer(elem);
}
if (document.getElementById('grouping-query-input').value !== DEFAULT_GROUPING) {
document.getElementById('refresh-btn').classList.remove('hide');
} else{
document.getElementById('refresh-btn').classList.add('hide');
}
}
function clearGroupingParam() {
const currentUrl = new URL(window.location.href); // Get the current URL
const urlParams = new URLSearchParams(currentUrl.search);
urlParams.delete('grouping'); // Set or update the query parameter
currentUrl.search = urlParams.toString();
window.history.pushState({}, '', currentUrl);
}
function reset(){
document.getElementById('grouping-query-input').value = DEFAULT_GROUPING;
document.getElementById('refresh-btn').classList.add('hide');
clearGroupingParam();
}
function openTab(url) {
const link = document.createElement('a');
link.href = url;
link.target = '_blank';
document.body.appendChild(link);
link.click();
link.remove();
}
function getQueryParam(name) {
const urlParams = new URLSearchParams(window.location.search);
return urlParams.get(name);
}
function addQueryLink(yql, container) {
const existingLinkDiv = container.querySelector('#query-link-container');
const linkDiv = document.createElement('div');
linkDiv.id = 'query-link-container';
const rawYql = 'select * from purchase where true limit 0 |' + yql;
linkDiv.innerHTML = `<a href="${getSearchUrl(rawYql)}" target="_blank">Direct Response</a>`;
if (existingLinkDiv) {
existingLinkDiv.replaceWith(linkDiv);
} else {
container.appendChild(linkDiv);
}
}
function executeGrouping(yql, outputContainer) {
outputContainer.classList.add('loading');
outputContainer.innerHTML = '<div class="loader"></div>';
const rawYql = 'select * from purchase where true limit 0 |' + yql;
fetch(getSearchUrl(rawYql))
.then(response => {
if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
return response.json();
})
// If using the local proxy, we need to parse the response
.then(handleProxyRequest)
.then(jsonData => {
const groupingResponses = jsonData.root.children?.[0]?.children ?? [];
outputContainer.innerHTML = '';
outputContainer.classList.remove('loading');
const excludeKeys = ['id', 'documentid', 'relevance', 'fields', 'source', 'sddocname'];
let anyDataShown = false;
for (const groupResponse of groupingResponses) {
const groups = groupResponse?.children ?? [];
let rows = [];
groups.forEach(group => {
rows = rows.concat(flattenGroupHierarchy(group));
});
const table = generateTable(rows, excludeKeys);
if (table) {
table.classList.add('table');
outputContainer.appendChild(table);
anyDataShown = true;
}
}
addQueryLink(yql, outputContainer.parentNode);
if (!anyDataShown) {
if (jsonData.root.errors) {
jsonData.root.errors.forEach((error) => {
// Output the error
outputContainer.innerHTML += `<p style="color:red;">Error:${error.message}</p>`;
});
} else {
outputContainer.innerHTML = '<p>No data available to display.</p>';
}
}
})
.catch(error => {
outputContainer.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
});
}
function transformPreToExecutableCells() {
document.querySelectorAll('pre:not(.no-transform)').forEach(pre => {
const fullText = pre.textContent.trim();
const splitIndex = fullText.indexOf('|');
if (splitIndex === -1) return;
const yql = fullText.slice(splitIndex + 1).trim();
const container = document.createElement('div');
container.className = 'yql-cell';
const label = document.createElement('div');
label.textContent = 'Executable Grouping Query:';
label.className = 'yql-cell-label';
const textarea = document.createElement('textarea');
textarea.value = yql;
textarea.className = 'yql-cell-textarea';
const runButton = document.createElement('button');
runButton.textContent = 'Run Grouping';
runButton.className = 'button is-small yql-cell-button';
const resultDiv = document.createElement('div');
resultDiv.className = 'grouping-table-container';
runButton.onclick = () => {
executeGrouping(textarea.value, resultDiv);
};
// Replace <pre> with this new interactive container
pre.replaceWith(container);
container.appendChild(label);
container.appendChild(textarea);
container.appendChild(runButton);
container.appendChild(resultDiv);
});
}
document.addEventListener('DOMContentLoaded', function() {
transformPreToExecutableCells();
const yql = document.querySelector('#grouping-query-input').value;
const linkContainer = document.querySelector('#query-link-container');
addQueryLink(yql, linkContainer);
// Get the value of the 'grouping' query parameter
const groupingValue = getQueryParam('grouping');
// If the 'grouping-query-input' element exists, set its value to the query parameter
const groupingInput = document.getElementById('grouping-query-input');
if (groupingValue !== null) {
document.getElementById('refresh-btn').classList.remove('hide');
groupingInput.value = groupingValue;
} else{
document.getElementById('refresh-btn').classList.add('hide');
}
});

## Grouping Interface

Try running requests on the
[grouping example data](https://github.com/vespa-engine/sample-apps/blob/master/examples/part-purchases-demo/ext/feed.jsonl):

all( group(customer) each(output(sum(price))) )

Run Grouping

The Vespa grouping language is a list-processing language
which describes how the query hits should be grouped, aggregated, and presented in result sets.
A grouping statement takes the list of all matches to a query as input and groups/aggregates
it, possibly in multiple nested and parallel ways to produce the output.
This is a logical specification and does not indicate how it is executed,
as instantiating the list of all matches to the query somewhere would be too expensive,
and execution is distributed instead.

Refer to the [Query API reference](reference/query-api-reference.html#select)
for how to set the *select* parameter,
and the [Grouping reference](reference/grouping-syntax.html) for details.
Fields used in grouping must be defined as [attribute](attributes.html) in the document schema.
Grouping supports continuation objects for [pagination](#pagination).

The [Grouping Results](https://github.com/vespa-engine/sample-apps/tree/master/examples/part-purchases-demo)
sample application is a practical example.

## The grouping language structure

The operations defining the structure of a grouping are:
* `all(statement)`: Execute the nested statement once on the input list as a whole.
* `each(statement)`: Execute the nested statement on each element of the input list.
* `group(specification)`:
  Turn the input list into a list of lists according to the grouping specification.
* `output`: Output some value(s) at the current location in the structure.

The parallel and nested collection of these operations defines both the structure of the computation
and of the result it produces.
For example, `all(group(customer) each(output(count())))`
will take all matches, group them by customer id, and for each group, output the count of hits in the group.

Vespa distributes and executes the grouping program on content nodes and merges results on container nodes -
in multiple phases, as needed.
As realizing such programs over a distributed data set requires more network round-trips than a regular search query,
these queries may be more expensive than regular queries -
see [defaultMaxGroups](reference/query-api-reference.html#grouping.defaultmaxgroups) and the likes
for how to control resource usage.

## Grouping by example

For the entirety of this document, assume an index of engine part purchases:

| Date | Price | Tax | Item | Customer |
| --- | --- | --- | --- | --- |
| 2006-09-06 09:00:00 | $1 000 | 0.24 | Intake valve | Smith |
| 2006-09-07 10:00:00 | $1 000 | 0.12 | Rocker arm | Smith |
| 2006-09-07 11:00:00 | $2 000 | 0.24 | Spring | Smith |
| 2006-09-08 12:00:00 | $3 000 | 0.12 | Valve cover | Jones |
| 2006-09-08 10:00:00 | $5 000 | 0.24 | Intake port | Jones |
| 2006-09-08 11:00:00 | $8 000 | 0.12 | Head | Brown |
| 2006-09-09 12:00:00 | $1 300 | 0.24 | Coolant | Smith |
| 2006-09-09 10:00:00 | $2 100 | 0.12 | Engine block | Jones |
| 2006-09-09 11:00:00 | $3 400 | 0.24 | Oil pan | Brown |
| 2006-09-09 12:00:00 | $5 500 | 0.12 | Oil sump | Smith |
| 2006-09-10 10:00:00 | $8 900 | 0.24 | Camshaft | Jones |
| 2006-09-10 11:00:00 | $1 440 | 0.12 | Exhaust valve | Brown |
| 2006-09-10 12:00:00 | $2 330 | 0.24 | Rocker arm | Brown |
| 2006-09-10 10:00:00 | $3 770 | 0.12 | Spring | Brown |
| 2006-09-10 11:00:00 | $6 100 | 0.24 | Spark plug | Smith |
| 2006-09-11 12:00:00 | $9 870 | 0.12 | Exhaust port | Jones |
| 2006-09-11 10:00:00 | $1 597 | 0.24 | Piston | Brown |
| 2006-09-11 11:00:00 | $2 584 | 0.12 | Connection rod | Smith |
| 2006-09-11 12:00:00 | $4 181 | 0.24 | Rod bearing | Jones |
| 2006-09-11 13:00:00 | $6 765 | 0.12 | Crankshaft | Jones |

## Basic Grouping

Example: *Return the total sum of purchases per customer* - steps:

1. Select all documents:

   ```
   /search/?yql=select * from sources * where true
   ```
2. Take the list of all hits:

   ```
   all(...)
   ```
3. Turn it into a list of lists of all hits having the same customer id:

   ```
   group(customer)
   ```
4. For each of those lists of same-customer hits:
   each(...)
5. Output the sum (an aggregator) of the price over all items in that list of hits:

   ```
   output(sum(price))
   ```

Final query, producing the sum of the price of all purchases for each customer:

```
/search/?yql=select * from sources * where true limit 0 |
  all( group(customer) each(output(sum(price))) )
```

Here, limit is set to zero to get the grouping output only.
URL encoded equivalent:

```
/search/?yql=select%20%2A%20from%20sources%20%2A%20where%20true%20limit%200%20%7C%20
  all%28%20group%28customer%29%20each%28output%28sum%28price%29%29%29%20%29
```

Result:

| GroupId | Sum(price) |
| --- | --- |
| Brown | $20 537 |
| Jones | $39 816 |
| Smith | $19 484 |

Example: *Sum price of purchases [per date](#time-and-date):*

```
select (…) | all(group(time.date(date)) each(output(sum(price))))
```

Note: in examples above, *all* documents are evaluated.
Modify the query to add filters (and thus cut latency), like (remember to URL encode):

```
/search/?yql=select * from sources * where customer contains "smith"
```

## Ordering and Limiting Groups

In many scenarios, a large collection of groups is produced, possibly too large to display or process.
This is handled by ordering groups, then limiting the number of groups to return.

The `order` clause accepts a list of one or more expressions.
Each of the arguments to `order` is prefixed by either a plus/minus for ascending/descending order.

Limit the number of groups using `max` and `precision` -
the latter is the number of groups returned per content node to be merged to the global result.
Larger document distribution skews hence require a higher `precision` for accurate results.

An implicit limit can be specified through the
[grouping.defaultMaxGroups](reference/query-api-reference.html#grouping.defaultmaxgroups) query parameter.
This value will always be overridden if `max` is explicitly specified in the query.
Use `max(inf)` to retrieve all groups when the query parameter is set.

If `precision` is not specified, it will default to a factor times `max`.
This factor can be overridden through the
[grouping.defaultPrecisionFactor](reference/query-api-reference.html#grouping.defaultprecisionfactor)
query parameter.

Example: To find the 2 globally best groups, make an educated guess on how
many samples are needed to fetch from each node in order to get the right groups.
This is the `precision`.
An initial factor of 3 has proven to be quite good in most use cases.
If however, the data for customer 'Jones' was spread on 3 different content nodes,
'Jones' might be among the 2 best on only one node.
But based on the distribution of the data,
we have concluded by earlier tests that if we fetch 5.67 as many groups as we need to,
we will have a correct answer with at least 99.999% confidence.
So then we just use 6 times as many groups when doing the merge.

However, there is one exception.
Without an `order` constraint, `precision` is not required.
Then, local ordering will be the same as global ordering.
Ordering will not change after a merge operation.

### Example

Example: *The two customers with most purchases, returning the sum for each:*

```
select (…) | all(group(customer) max(2) precision(12) order(-count())
    each(output(sum(price))))
```

## Hits per Group

Use `summary` to print the fields for a hit,
and `max` to limit the number of hits per group.

An implicit limit can be specified through the
[grouping.defaultMaxHits](reference/query-api-reference.html#grouping.defaultmaxhits) query parameter.
This value will always be overridden if `max` is explicitly specified in the query.
Use `max(inf)` to retrieve all hits when the query parameter is set.

### Example

Example: Return the three most expensive parts per customer:

```
/search/?yql=select * from sources * where true |
             all(group(customer) each(max(3) each(output(summary()))))
```

Notes on ordering in the example above:
* The `order` clause is a directive for *group* ordering, not *hit* ordering.
  Here, there is no order clause on the groups, so default ordering `-max(relevance())` is used. The *-*
  denotes the sorting order, *-* means descending (higher score first).
  In this case, the query is "all documents", so all groups are equally relevant and the group order is random.
* To order hits inside groups, use ranking. Add `ranking=pricerank` to the query
  to use the pricerank [rank profile](ranking.html) to rank by price:

  ```
  rank-profile pricerank inherits default {
      first-phase {
          expression: attribute(price)
      }
  }
  ```

## Filter within a group

Use the `filter` clause to select which values to keep in a group. See the [reference](reference/grouping-syntax.html#filtering-groups) for details.

### Example

Example: Sum the price per customer of `Bonn.*` where price was over 1000.

```
/search/?yql=select * from sources * where true |
             all(group(customer) filter(regex("Bonn.*", attributes{"sales_rep"}) and not range(0, 1000, price)) each(output(sum(price)) each(output(summary()))))
```

## Global limit for grouping queries
- [add](reference/document-json-format.html#add)
  Use the [grouping.globalMaxGroups](reference/query-api-reference.html#grouping.globalmaxgroups) query parameter
  to restrict execution of queries that are potentially too expensive in terms of compute and bandwidth.
  Queries that may return a result exceeding this threshold are failed preemptively.
  This limit is compared against the total number of groups and hits that query could return at worst-case.

  ### Examples

  The following query may return 5 groups and 0 hits.
  It will be rejected when `grouping.globalMaxGroups < 5`

  ```
    select (…) | all(group(item) max(5) each(output(count())))
  ```

  The following query may return 5 groups and 35 hits.
  It will be rejected when `grouping.globalMaxGroups < 5+5*7`.

  ```
    select (…) | all(
      group(customer) max(5)
        each(
          output(count()) max(7)
            each(output(summary()))
        )
    )
  ```

  The following query may return 6 groups and 30 hits.
  It will be rejected when `grouping.globalMaxGroups < 2*(3+3*5)`.

  ```
  select (…) |
  all(
      all(group(item) max(3)
        each(output(count()) max(5)
          each(output(summary()))))
      all(group(customer) max(3)
        each(output(count()) max(5)
          each(output(summary())))))
  ```

  ### Combining with default limits for groups/hits

  The `grouping.globalMaxGroups` restriction will utilize the
  [grouping.defaultMaxGroups](reference/query-api-reference.html#grouping.defaultmaxgroups)/
  [grouping.defaultMaxHits](reference/query-api-reference.html#grouping.defaultmaxhits)
  values for grouping statements without a `max`. The two queries below are identical, assuming
  `defaultMaxGroups=5` and `defaultMaxHits=7`, and both will be rejected when
  `globalMaxGroups < 5+5*7`.

  ```
  select (…) |
  all(
    group(customer) max(5)
      each(
        output(count()) max(7)
          each(output(summary()))
      )
  )
  ```
```
  select (…) |
  all(
    group(customer)
      each(
        output(count())
          each(output(summary()))
      )
  )
  ```

  A grouping without `max` combined with `defaultMaxGroups=-1`/`defaultMaxHits=-1`
  will be rejected unless `globalMaxGroups=-1`. This is because the query produces an unbounded result,
  an infinite number of groups if `defaultMaxGroups=-1` or an infinite number of summaries if
  `defaultMaxHits=-1`.
  An unintentional DoS (Denial of Service) could be the utter consequence if a query returns thousands of groups and summaries.
  This is why setting `globalMaxGroups=-1` is risky.

  ### Recommended settings

  The best practice is to always specify `max` in groupings,
  making it easy to reason about the worst-case cardinality of the query results. The performance will also benefit.
  Set `globalMaxGroups` to the overall worst-case result cardinality with some margin.
  The `defaultMaxGroups`/`defaultMaxHits`
  should be overridden in a query profile if some groupings do not use `max` and the default values are too low.

  ```
    <query-profile id="default">
      <field name="grouping.defaultMaxGroups">20</field>
      <field name="grouping.defaultMaxHits">100</field>
      <field name="grouping.globalMaxGroups">8000</field>
    </query-profile>
  ```

  ## Performance and Correctness

  Grouping is, by default, tuned to favor performance over correctness.
  Perfect correctness may not be achievable; result of queries using [non-default ordering](#ordering-and-limiting-groups)
  can be approximate, and correctness can only be partially achieved by a larger `precision` value that sacrifices performance.

  The [grouping session cache](reference/grouping-syntax.html#grouping-session-cache) is enabled by default.
  Disabling it will improve correctness, especially for queries using `order` and `max`.
  The cost of multi-level grouping expressions will increase, though.

  Consider increasing the [precision](#ordering-and-limiting-groups) value when using `max` in combination with `order`.
  The default precision may not achieve the required correctness for your use case.

  ## Nested Groups

  Groups can be nested. This offers great drilling capabilities,
  as there are no limits to nesting depth or presented information on any level.
  Example: How much each customer has spent per day by grouping on customer, then date:

  ```
  select (…) | all(group(customer) each(group(time.date(date)) each(output(sum(price)))))
  ```

  Use this to query for all items on a per-customer basis, displaying the most expensive hit for each customer,
  with subgroups of purchases on a per-date basis.
  Use the [summary](#hits-per-group) clause
  to show hits inside any group at any nesting level.
  Include the sum price for each customer, both as a grand total and broken down on a per-day basis:

  ```
  /search/?yql=select * from sources * where true limit 0|
               all(group(customer)
                   each(max(1) output(sum(price)) each(output(summary())))
                        each(group(time.date(date))
                        each(max(10) output(sum(price)) each(output(summary())))))
          &ranking=pricerank
  ```

  | GroupId | sum(price) |  |  |  |  |  |
  | --- | --- | --- | --- | --- | --- | --- |
  | Brown | $20 537 |  |  |  |  |  |
  |  | Date | Price | Tax | Item | Customer |  |
  |  | 2006-09-08 11:00 | $8 000 | 0.12 | Head | Brown |  |
  |  | GroupId | Sum(price) |  |  |  |  |
  |  | 2006-09-08 | $8 000 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-08 11:00 | $8 000 | 0.12 | Head | Brown |
  |  | 2006-09-09 | $3 400 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-09 11:00 | $3 400 | 0.12 | Oil pan | Brown |
  |  | 2006-09-10 | $7 540 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-10 10:00 | $3 770 | 0.12 | Spring | Brown |
  |  |  | 2006-09-10 12:00 | $2 330 | 0.24 | Rocker arm | Brown |
  |  |  | 2006-09-10 11:00 | $1 440 | 0.12 | Exhaust valve | Brown |
  |  | 2006-09-11 | $1 597 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-11 10:00 | $1 597 | 0.24 | Piston | Brown |
  | Jones | $39 816 |  |  |  |  |  |
  |  | Date | Price | Tax | Item | Customer |  |
  |  | 2006-09-11 12:00 | $9 870 | 0.12 | Exhaust port | Jones |  |
  |  | GroupId | Sum(price) |  |  |  |  |
  |  | 2006-09-08 | $8 000 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-08 10:00 | $5 000 | 0.24 | Intake port | Jones |
  |  |  | 2006-09-08 12:00 | $3 000 | 0.12 | Valve cover | Jones |
  |  | 2006-09-09 | $2 100 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-09 10:00 | $2 100 | 0,12 | Engine block | Jones |
  |  | 2006-09-10 | $8 900 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-10 10:00 | $8 900 | 0.24 | Camshaft | Jones |
  |  | 2006-09-11 | $20 816 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-11 12:00 | $9 870 | 0.12 | Exhaust port | Jones |
  |  |  | 2006-09-11 13:00 | $6 765 | 0.12 | Crankshaft | Jones |
  |  |  | 2006-09-11 12:00 | $4 181 | 0.24 | Rod bearing | Jones |
  | Smith | $19 484 |  |  |  |  |  |
  |  | Date | Price | Tax | Item | Customer |  |
  |  | 2006-09-10 11:00 | $6 100 | 0.24 | Spark plug | Smith |  |
  |  | GroupId | Sum(price) |  |  |  |  |
  |  | 2006-09-06 | $1 000 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-06 09:00 | $1 000 | 0.24 | Intake valve | Smith |
  |  | 2006-09-07 | $3 000 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-07 11:00 | $2 000 | 0.24 | Spring | Smith |
  |  |  | 2006-09-07 10:00 | $1 000 | 0.12 | Rocker arm | Smith |
  |  | 2006-09-09 | $6 800 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-09 12:00 | $5 500 | 0.12 | Oil sump | Smith |
  |  |  | 2006-09-09 12:00 | $1 300 | 0.24 | Coolant | Smith |
  |  | 2006-09-10 | $6 100 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-10 11:00 | $6 100 | 0.24 | Spark plug | Smith |
  |  | 2006-09-11 | $2 584 |  |  |  |  |
  |  |  | Date | Price | Tax | Item | Customer |
  |  |  | 2006-09-11 11:00 | $2 584 | 0.12 | Connection rod | Smith |

  ## Structured grouping

  Structured grouping is nested grouping over an array of structs or maps.
  In this case, each array element is treated as a sub-document and may
  be grouped separately. See the reference for grouping on
  [multivalue attributes](reference/grouping-syntax.html#multivalue-attributes)
  for details. It is also possible to
  [filter the groups](reference/grouping-syntax.html#filtering-groups)
  so only matching elements are considered. An example could be:

  ```
    select (…) | all(group(attributes.value) filter(regex("delivery_method",attributes.key)) each(output(sum(price)) each(output(summary()))))
  ```

  ## Range grouping

  In the examples above, results are grouped on distinct values, like customer or date.
  To group on price:

  ```
  select (…) | all(group(price) each(each(output(summary()))))
  ```

  This gives one group per price. To group on price *ranges*, one could compress the price range.
  This gives prices in $0 - $999 in bucket 0, $1 000 - $2 000 in bucket 1 and so on:

  ```
  select (…) | all(group(price/1000) each(each(output(summary()))))
  ```

  An alternative is using [bucket expressions](reference/grouping-syntax.html#bucket-expressions) -
  think of a bucket as the range per group.
  Group on price, make groups have a width of 1000:

  ```
  select (…) | all(group(fixedwidth(price,1000)) each(each(output(summary()))))
  ```

  Use `predefined` to configure group sizes individually (the two below are equivalent):

  ```
  select (…) |
  all(
    group(predefined(price,
      bucket(0,1000),
      bucket(1000,2000),
      bucket(2000,5000),
      bucket(5000,inf)))
    each(each(output(summary())))
  )
  ```

  This works with strings as well - put Jones and Smith in the second group:

  ```
  select (…) | all(group(predefined(customer, bucket(-inf,"Jones"), bucket("Jones", inf))) each(each(output(summary()))))
  ```

  ... or have Jones in his own group:

  ```
  select (…) | all(group(predefined(customer, bucket<-inf,"Jones">, bucket["Jones"], bucket<"Jones", inf>)) each(each(output(summary()))))
  ```

  Use decimal numbers in bucket definitions if the expression evaluates to a double or float:

  ```
  select (…)
  | all(
    group(predefined(tax,
        bucket(0.0, 0.2),
        bucket(0.2, 0.5),
        bucket(0.5, inf)))
      each(
        each(output(summary()))
      )
  )
  ```

  ## Pagination

  Grouping supports [continuation](reference/grouping-syntax.html#continuations) objects
  that are passed as annotations to the grouping statement.
  The `continuations` annotation is a list of zero or more continuation strings,
  returned in the grouping result.
  For example, given the result:

  ```
  {% highlight json %}
  {
      "root": {
          "children": [
              {
                  "children": [
                      {
                          "children": [
                              {
                                  "fields": {
                                      "count()": 7
                                  },
                                  "value": "Jones",
                                  "id": "group:string:Jones",
                                  "relevance": 1.0
                              }
                          ],
                          "continuation": {
                              "next": "BGAAABEBEBC",
                              "prev": "BGAAABEABC"
                          },
                          "id": "grouplist:customer",
                          "label": "customer",
                          "relevance": 1.0
                      }
                  ],
                  "continuation": {
                      "this": "BGAAABEBCA"
                  },
                  "id": "group:root:0",
                  "relevance": 1.0
              }
          ],
          "fields": {
              "totalCount": 20
          },
          "id": "toplevel",
          "relevance": 1.0
      }
  }
  {% endhighlight %}
  ```

  reproduce the same result by passing the *this*-continuation along the original select:

  ```
  select (…) | { 'continuations':['BGAAABEBCA'] }all(…)
  ```

  To display the next page of customers, pass the *this*-continuation of the root
  group, and the *next* continuation of the customer list:

  ```
  select (…) | { 'continuations':['BGAAABEBCA', 'BGAAABEBEBC'] }all(…)
  ```

  To display the previous page of customers, pass the *this*-continuation of the root group,
  and the *prev* continuation of the customer list:

  ```
  select (…) | { 'continuations':['BGAAABEBCA', 'BGAAABEABC'] }all(…)
  ```

  The `continuations` annotation is an ordered list of continuation strings.
  These are combined by replacement
  so that a continuation given later will replace any shared state with a continuation given before.
  Also, when using the `continuations` annotation,
  always pass the *this*-continuation as its first element.

  {% include note.html content="Continuations work best when the ordering of hits is stable -
  which can be achieved by using [ranking](ranking.html) or
  [ordering](reference/grouping-syntax.html#order).
  Adding a tie-breaker might be needed - like [random.match](reference/rank-features.html#random)
  or a random double value stored in each document -
  to keep the ordering stable in case of multiple documents that would otherwise get the same rank score
  or the same value used for ordering."%}

  ## Expressions

  Instead of just grouping on some attribute value,
  the `group` clause may contain arbitrarily complex expressions -
  see `group` in the
  [grouping reference](reference/grouping-syntax.html) for an exhaustive list.
  Examples:
  * Select the minimum or maximum of sub-expressions
  * Addition, subtraction, multiplication, division, and even modulo of sub-expressions
  * Bitwise operations on sub-expressions
  * Concatenation of the results of sub-expressions

  Sum the prices of purchases on a per-hour-of-day basis:

  ```
  select (…) | all(group(mod(div(date,mul(60,60)),24)) each(output(sum(price))))
  ```

  These types of expressions may also be used inside `output` operations,
  so instead of simply calculating the sum price of the grouped purchases,
  calculate the sum income after taxes per customer:

  ```
  select (…) | all(group(customer) each(output(sum(mul(price,sub(1,tax))))))
  ```

  Note that the validity of an expression depends on the current nesting level.
  For, while `sum(price)` would be a valid expression for a group of hits, `price` would not.
  As a general rule, each operator within an expression either applies to a single hit or aggregates values across a group.

  ## Search Container API

  As an alternative to a textual representation,
  one can use the programmatic API to execute grouping requests.
  This allows multiple grouping requests to run in parallel,
  and does not collide with the `yql` parameter - example:

  ```
  {% highlight java %}
  @Override
  public Result search(Query query, Execution execution) {
      // Create grouping request.
      GroupingRequest request = GroupingRequest.newInstance(query);
      request.setRootOperation(new AllOperation()
              .setGroupBy(new AttributeValue("foo"))
              .addChild(new EachOperation()
                  .addOutput(new CountAggregator().setLabel("count"))));

      // Perform grouping request.
      Result result = execution.search(query);

      // Process grouping result.
      Group root = request.getResultGroup(result);
      GroupList foo = root.getGroupList("foo");
      for (Hit hit : foo) {
          Group group = (Group)hit;
          Long count = (Long)group.getField("count");
          // TODO: Process group and count.
      }

      // Pass results back to calling searcher.
      return result;
  }
  {% endhighlight %}
  ```

  Refer to the
  [API documentation](https://javadoc.io/doc/com.yahoo.vespa/container-search/latest/com/yahoo/search/grouping/package-summary.html) for the complete reference.

  ## TopN / Full corpus

  Simple grouping: count the number of documents in each group:

  ```
  select * from purchase where true | all( group(customer) each(output(count())) )
  ```

  Two parallel groupings:

  ```
  select * from purchase where true | all(
    all(
        group(customer) each(output(count()))
    )
    all(
        group(item) each(output(count()))
    )
  )
  ```

  Only the 1000 best hits will be grouped at each content node. Lower accuracy, but higher speed:

  ```
  select * from purchase where true limit 0 |
    all(
      max(1000)
      all(
        group(customer)
        each(output(count()))
      )
    )
  ```

  ## Selecting groups

  Do a modulo 3 operation before selecting the group:

  ```
  select * from purchase where true limit 0 |
    all(
      group(price % 3)
      each(output(count()))
    )
  ```

  Do `price + tax * price` before selecting the group:

  ```
  select * from purchase where true limit 0 | all(
    group(price + tax * price)
    each(output(count()))
  )
  ```

  ## Ordering groups

  Do a modulo 5 operation before selecting the group -
  the groups are then ordered by their aggregated sum of attribute "tax":

  ```
  select * from purchase where true limit 0 | all(
    group(price % 5)
    order(sum(tax))
    each(output(count()))
  )
  ```

  Do `price + tax * price` before selecting the group.
  Ordering is given by the maximum value of attribute "price" in each group:

  ```
  select * from purchase where true limit 0 |
    all(
      group(price + tax * price)
      order(max(price))
      each(output(count()))
    )
  ```

  Take the average relevance of the groups and multiply it with
  the number of groups to get a cumulative count:

  ```
   select * from purchase where true limit 0 |
    all(
    group(customer)
    order(avg(relevance()) * count())
    each(output(count()))
  )
  ```

  One can not directly reference an attribute in the order clause, as this:

  ```
  select * from purchase where true limit 0 |
    all(
    group(customer)
    order(price * count())
    each(output(count()))
  )
  ```

  However, one can do this:

  ```
  select * from purchase where true limit 0 | all(
    group(customer)
    order(max(price) * count())
    each(output(count()))
  )
  ```

  ## Collecting aggregates

  Simple grouping to count the number of documents in each group and return the best hit in each group:

  ```
  select * from purchase where true limit 0 |
    all(
    group(customer)
    each(
      max(1)
      each(output(summary()))
    )
  )
  ```

  Also return the sum of attribute "price":

  ```
  select * from purchase where true limit 0 |
    all( group(customer) each(max(1) output(count(), sum(price)) each(output(summary()))) )
  ```

  Also, return an XOR of the 64 most significant bits of an MD5
  over the concatenation of attributes "customer", "price" and "tax":

  ```
  select * from purchase where true limit 0 |
    all(group(customer) each(max(1) output(count(), sum(price), xor(md5(cat(customer, price, tax), 64))) each(output(summary()))))
  ```

  It is also possible to return quantiles, for instance, the p50 and p90 of the price.

  ```
  select * from purchase where true limit 0 |
    all(group(customer) each(output(quantiles([0.5,0.9], price))))
  ```

  ## Grouping

  Single-level grouping on "customer" attribute, returning at most 5 groups with full hit count as well as the 69 best hits.

  ```
  select * from purchase where true limit 0 | all(group(customer) max(5) each(max(69) output(count()) each(output(summary()))))
  ```

  Two level grouping on "customer" and "item" attribute:

  ```
  select * from purchase where true limit 0 | all(group(customer) max(5) each(output(count()) all(group(item) max(5) each(max(69) output(count()) each(output(summary()))))))
  ```

  Three-level grouping on "customer", "item" and "attributes.key(coupon)" attribute:

  ```
  select * from purchase where true limit 0 | all(group(customer) max(1) each(output(count()) all(group(item) max(1) each(output(count()) max(1) all(group(attributes.key) max(1) each(output(count()) each(output(summary()))))))))
  ```

  As above, but also collect best hit in level 2:

  ```
  select * from purchase where true limit 0 | all(group(customer) max(5) each(output(count()) all(group(item) max(5) each(output(count()) all(max(1) each(output(summary()))) all(group(attributes.key) max(5) each(max(69) output(count()) each(output(summary()))))))))
  ```

  As above, but also collect best hit in level 1:

  ```
  select * from purchase where true limit 0 | all(group(customer) max(5) each(output(count()) all(max(1) each(output(summary()))) all(group(item) max(5) each(output(count()) all(max(1) each(output(summary()))) all(group(attributes.key) max(5) each(max(69) output(count()) each(output(summary()))))))))
  ```

  As above, but using different document summaries on each level:

  ```
   select * from purchase where true limit 0 |
    all( group(customer) max(5) each(output(count())
       all(max(1) each(output(summary(complexsummary))))
       all(group(item) max(5) each(output(count())
           all(max(1) each(output(summary(simplesummary))))
           all(group(price) max(5) each(max(69) output(count())
               each(output(summary(fastsummary)))))) )
  ```

  Deep grouping with counting and hit collection on all levels:

  ```
   select * from purchase where true limit 0 |
    all( group(customer) max(5) each(output(count())
       all(max(1) each(output(summary())))
       all(group(item) each(output(count())
           all(max(1) each(output(summary())))
           all(group(price) each(output(count())
               all(max(1) each(output(summary())))))))) )
  ```

  ## Time and date

  The field (`time` below, but can have any name)
  must be a [long](reference/schema-reference.html#long), with second resolution (unix timestamp/epoch).
  See the [reference](reference/grouping-syntax.html#time-expressions) for all time-functions.

  Group by year:

  ```
  select * from purchase where true limit 0 | all(group(time.year(date)) each(output(count())))
  ```

  Group by year, then by month:

  ```
  select * from purchase where true limit 0 |
    all( group(time.year(date)) each(output(count())
       all(group(time.monthofyear(date)) each(output(count())))) )
  ```

  Groups *today*, *yesterday*, *lastweek*, and *lastmonth*
  using `predefined` aggregator, and groups each day within each of these separately:

  ```
   select * from purchase where true limit 0 |
    all(
      group(
        predefined((now() - date) / (60 * 60 * 24),
        bucket(0,1),
        bucket(1,2),
        bucket(3,7),
        bucket(8,31))
        )
      each(output(count())
        all(max(2) each(output(summary())))
        all(group((now() - date) / (60 * 60 * 24))
          each(output(count())
            all(max(2) each(output(summary())))
          )
        )
      )
    )
  ```

  ### Timezones in grouping

  The `timezone` query parameter can be used to rewrite each time-function with a timezone offset.
  See the [reference](reference/query-api-reference.html#timezone). Example:

  ```
  $ vespa query "select * from purchase where true | \
                 all( group(time.hourofday(date)) each(output(count()))" \
                "timezone=America/Los_Angeles"
  ```

  This query selects all documents from `purchase`, groups them by the
  hour they were made (adjusted to the local time
  in `America/Los_Angeles`), and counts how many purchases fall into
  each hour.

  ## Counting unique groups

  The `count` aggregator can be applied on a list of groups to determine the number of unique groups
  without having to explicitly retrieve all groups.
  Note that this count is an estimate using HyperLogLog++ which is an algorithm for the count-distinct problem.
  To get an accurate count, one needs to explicitly retrieve all groups
  and count them in a custom component or in the middle tier calling out to Vespa.
  This is network intensive and might not be feasible in cases with many unique groups.

  Another use case for this aggregator is counting the number of unique instances matching a given expression.

  Output an estimate of the number of groups, which is equivalent to the number of unique values for attribute "customer":

  ```
  select * from purchase where true limit 0 | all( group(customer) each(output(count())) )
  ```

  Output an estimate of the number of unique string lengths for the attribute "item":

  ```
  select * from purchase where true limit 0 | all(group(strlen(item)) each(output(count())))
  ```

  Output the sum of the "price" attribute for each group
  in addition to the accurate count of the overall number of unique groups
  as the inner each causes all groups to be returned.

  ```
  select * from purchase where true limit 0 | all(group(customer) output(count()) each(output(sum(price))))
  ```

  The `max` clause is used to restrict the number of groups returned.
  The query outputs the sum for the 3 best groups.
  The `count` clause outputs the estimated number of groups (potentially >3).
  The `count` becomes an estimate here as the number of groups is limited by max,
  while in the above example, it's not limited by max:

  ```
  select * from purchase where true limit 0 | all(group(customer) max(3) output(count()) each(output(sum(price))))
  ```

  Output the number of top-level groups, and for the 10 best groups,
  output the number of unique values for attribute "item":

  ```
  select * from purchase where true limit 0 | all(group(customer) max(10) output(count()) each(group(item) output(count())))
  ```

  ## Counting unique groups - multivalue fields

  A [multivalue](/en/schemas.html#multivalue-field) attribute is a
  [weighted set](/en/reference/schema-reference.html#weightedset),
  [array](/en/reference/schema-reference.html#array) or
  [map](/en/reference/schema-reference.html#map).
  Most grouping functions will just handle the elements of multivalued attributes separately,
  as if they were all individual values in separate documents.
  If you are grouping over array of struct or maps, scoping will be used to preserve structure.
  Each entry in the array/map will be treated as a separate sub-document,
  so documents can be counted twice or more - see
  [#33646](https://github.com/vespa-engine/vespa/issues/33646) for details.

  This could be solved by performing adding an additional level grouping,
  where you group on a field that is unique for each document (grouping on document id is not supported).
  You may then count the unique groups to determine the unique document count:

  ```
  select * from purchase where true limit 0 | all(group(customer) each(group(item) output(count())))
  ```

  ## Impression forecasting

  Using impression logs for a given user,
  one can make a function that maps from rank score to the number of impressions an advertisement would get - example:

  ```
  Score   Integer (# impressions for this user)
  0.200   0
  0.210   1
  0.220   2
  0.240   3
  0.320   4
  0.420   5
  0.560   6
  0.700   7
  0.800   8
  0.880   9
  0.920  10
  0.940  11
  0.950  12
  ```

  Storing just the first column (the rank scores, including a rank score for 0 impressions)
  in an array attribute named *impressions*, the grouping operation
  [interpolatedlookup(impressions, relevance())](reference/grouping-syntax.html#interpolatedlookup)
  can be used to figure out how many times a given advertisement would have been shown to this particular user.

  So if the rank score is 0.420 for a specific user/ad/bid combination,
  then `interpolatedlookup(impressions, relevance())` would return 5.0.
  If the bid is increased so the rank score gets to 0.490,
  it would get 5.5 as the return value instead.

  In this context, a count of 5.5 isn't meaningful for the past of a single user,
  but it gives more information that may be used as a forecast.
  Summing this across more, different users may then be used to forecast
  the total of future impressions for the advertisement.

  ## Aggregating over all documents

  Grouping is useful for analyzing data.
  To aggregate over the full document set, create *one* group (which will have *all* documents)
  by using a constant (here 1) - example:

  ```
  select rating from restaurant where true | all(group(1) each(output(avg(price))))
  ```

  Make sure all documents have a value for the given field, if not, NaN is used, and the final result is also NaN:

  ```
  {% highlight json %}
  {
      "id": "group:long:1",
      "relevance": 0.0,
      "value": "1",
      "fields": {
          "avg(rating)": "NaN"
      }
  }
  {% endhighlight %}
  ```

  ## Count fields with NaN

  Count number of documents missing a value for an [attribute](/en/attributes.html) field
  (actually, in this example, unset or less than 0, see the bucket expression below).
  Set a higher query timeout, just in case.
  Example, analyzing a field called *price*:

  ```
  select rating from restaurant where true | all( group(predefined(price, bucket[-inf, 0>, bucket[0, inf>)) each(output(count())) )
  ```

  Example output, counting 2 documents with `-inf` in *rating*:

  ```
  {% highlight json %}
  "children": [
      {
          "id": "group:long_bucket:-9223372036854775808:0",
          "relevance": 0.0,
          "limits": {
              "from": "-9223372036854775808",
              "to": "0"
          },
          "fields": {
              "count()": 2
          }
      },
      {
          "id": "group:long_bucket:0:9223372036854775807",
          "relevance": 0.0,
          "limits": {
              "from": "0",
              "to": "9223372036854775807"
          },
          "fields": {
              "count()": 8
          }
      }
  ]
  {% endhighlight %}
  ```

  See [analyzing field values](visiting.html#analyzing-field-values)
  for how to export ids of documents meeting given criteria from the full corpus.

  ## List fields with NaN

  This is similar to the counting of NaN above,
  but instead of aggregating the count, for each hit,
  print a [document summary](/en/reference/schema-reference.html#document-summary):

  ```
  select rating from restaurant where true |
      all( group(predefined(price, bucket[-inf, 0>, bucket[0, inf>))
      order(max(price))
      max(1)
      each( max(100) each(output(summary()))) )
  ```

  Notes:
  * We are only interested in the first group,
    so order by `max(price)` and use `max(1)` to get only the first
  * Uses `max(100)` in order to limit result set sizes.
    Read more about [grouping.defaultmaxhits](/en/reference/query-api-reference.html#grouping.defaultmaxhits).
  * Use the [continuation token](#pagination) to iterate over the result set.

  ## Grouping over a Map field

  In the example data, a record looks like:

  ```
  {% highlight json %}
  {
    "fields": {
      "attributes": {
        "delivery_method": "Curbside Pickup",
        "sales_rep": "Bonnie",
        "coupon": "SAVE10"
      },
      "customer": "Smith",
      "date": 1157526000,
      "item": "Intake valve",
      "price": "1000",
      "tax": "0.24"
    }
  }
  {% endhighlight %}
  ```

  The map field [schema definition](/en/reference/schema-reference.html#map) is:

  ```
  field attributes type map<string, string> {
      indexing: summary
      struct-field key   { indexing: attribute }
      struct-field value { indexing: attribute }
  }
  ```

  With this, one can group on both key (`delivery_method`, `sales_rep`, and `coupon`)
  and values (here counting each value).
  Try the link to see the output:

  ```
  select * from purchase where true limit 0 |
      all(
        group(attributes.key)
        each( group(attributes.value) each(output(count())))
      )
  ```

  A more interesting example is to see the sum per sales rep:

  ```
  select * from purchase where true limit 0 |
      all(
        group(attributes.key)
        each( group(attributes.value) each(output(sum(price))))
      )
  ```

  const checkboxes = document.querySelectorAll('input[type="checkbox"][data-col]');
  const table = document.getElementById('table-container').children;
  checkboxes.forEach(checkbox => {
  checkbox.addEventListener('change', () => {
  const colIndex = parseInt(checkbox.getAttribute('data-col'));
  const cells = table.querySelectorAll(`tr > *:nth-child(${colIndex + 1})`);
  cells.forEach(cell => {
  if (checkbox.checked) {
  cell.classList.remove('hidden');
  } else {
  cell.classList.add('hidden');
  }
  });
  });
  });
  function flattenGroupHierarchy(node, path = {}, rows = []) {
  if (!node) return rows;
  // If it's a group, store its value
  if (node.value) {
  const key = node.id.split(':')[1]; // e.g., 'string' or 'time.date(date)'
  path[key] = node.value;
  }
  // If it has fields (e.g., sum(price)), create a row
  if (node.fields) {
  const row = { ...path, ...node.fields };
  rows.push(row);
  }
  // Recursively process children
  if (node.children) {
  node?.children?.forEach(child => flattenGroupHierarchy(child, { ...path }, rows));
  }
  return rows;
  }
  function generateTable(data, excludeKeys = []) {
  if (!data || data.length === 0) return null;
  const isFlat = data.every(item =>
  Object.values(item).every(value => typeof value !== 'object' || value === null)
  );
  const shouldIncludeKey = key => !excludeKeys.includes(key);
  const getAllKeys = () => {
  const keys = new Set();
  data.forEach(item => {
  Object.keys(item).forEach(k => {
  if (shouldIncludeKey(k)) keys.add(k);
  });
  });
  return Array.from(keys);
  };
  const allKeys = getAllKeys();
  const table = document.createElement('table');
  const thead = table.createTHead();
  const headerRow = thead.insertRow();
  allKeys.forEach(key => {
  const th = document.createElement('th');
  th.textContent = key;
  headerRow.appendChild(th);
  });
  const tbody = table.createTBody();
  data.forEach(item => {
  const row = tbody.insertRow();
  allKeys.forEach(key => {
  const td = row.insertCell();
  const value = item[key];
  if (Array.isArray(value)) {
  const subTable = generateTable(value, excludeKeys);
  if (subTable) td.appendChild(subTable);
  } else if (typeof value === 'object' && value !== null) {
  const subTable = generateTable([value], excludeKeys);
  if (subTable) td.appendChild(subTable);
  } else {
  td.textContent = value !== undefined ? value : '';
  }
  });
  });
  return table;
  }
