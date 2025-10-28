---
# Copyright Vespa.ai. All rights reserved.
title: "Query API Reference"
redirect_from:
- /en/reference/search-api-reference.html
---

Refer to the [Query API guide](../query-api.html) for API examples.

All the request parameters listed below can be set in query profiles.
The first four blocks of properties are also modeled as
[query profile types](../query-profiles.html#query-profile-types).
These types can be referred from query profiles (and inheriting types)
to provide type checking on the parameters.

These parameters often have both a full name -
including the path from the root query profile -
and one or more abbreviated names.
Both names can be used in requests,
while only full names can be used in query profiles.
The full names are case-sensitive, abbreviated names are case-insensitive.

The parameters modeled as query profiles are also available through
get methods as Java objects from the Query to Searcher components.

## Parameters

Query
:   * [yql](#yql)

Native Execution Parameters
:   * [hits](#hits) [*count*]
    * [offset](#offset) [*start*]
    * [queryProfile](#queryprofile)
    * [groupingSessionCache](#groupingsessioncache)
    * [searchChain](#searchchain)
    * [timeout](#timeout)

Query Model
:   * [model.defaultIndex](#model.defaultindex) [*default-index*]
    * [model.encoding](#model.encoding) [*encoding*]
    * [model.filter](#model.filter) [*filter*]
    * [model.locale](#model.locale) [*locale*]
    * [model.language](#model.language) [*lang, language*]
    * [model.queryString](#model.querystring) [*query*]
    * [model.restrict](#model.restrict) [*restrict*]
    * [model.searchPath](#model.searchpath) [*path*]
    * [model.sources](#model.sources) [*search, sources*]
    * [model.type](#model.type) [*type*]
    * [model.type.composite](#model.type.composite)
    * [model.type.tokenization](#model.type.tokenization)
    * [model.type.syntax](#model.type.syntax)
    * [model.type.isYqlDefault](#model.type.isYqlDefault)

Ranking
:   * [ranking.location](#ranking.location) [*location*]
    * [ranking.features](#ranking.features) [*input*, *rankfeature*]
    * [ranking.listFeatures](#ranking.listfeatures) [*rankfeatures*]
    * [ranking.profile](#ranking.profile) [*ranking*]
    * [ranking.properties](#ranking.properties) [*rankproperty*]
    * [ranking.softtimeout.enable](#ranking.softtimeout.enable)
    * [ranking.sorting](#ranking.sorting) [*sorting*]
    * [ranking.freshness](#ranking.freshness)
    * [ranking.queryCache](#ranking.querycache)
    * [ranking.rerankCount](#ranking.rerankcount)
    * [ranking.keepRankCount](#ranking.keeprankcount)
    * [ranking.rankScoreDropLimit](#ranking.rankscoredroplimit)
    * [ranking.secondPhase.rankScoreDropLimit](#ranking.secondphase.rankscoredroplimit)
    * [ranking.globalPhase.rerankCount](#ranking.globalphase.rerankcount)
    * [ranking.globalPhase.rankScoreDropLimit](#ranking.globalphase.rankscoredroplimit)
    * [ranking.matching](#ranking.matching)
    * [ranking.matchPhase](#ranking.matchPhase)
    * [ranking.significance.useModel](#ranking.significance.useModel)

Presentation
:   * [presentation.bolding](#presentation.bolding) [*bolding*]
    * [presentation.format](#presentation.format) [*format*]
    * [presentation.template](#presentation.template)
    * [presentation.summary](#presentation.summary) [*summary*]
    * [presentation.timing](#presentation.timing)

Grouping
:   * [select](#select)
    * [collapse.summary](#collapse.summary)
    * [collapsefield](#collapsefield)
    * [collapsesize](#collapsesize)* [collapsesize](#collapsesize.fieldname) [*fieldname*]
      * [grouping.defaultMaxGroups](#grouping.defaultmaxgroups)
      * [grouping.defaultMaxHits](#grouping.defaultmaxhits)
      * [grouping.globalMaxGroups](#grouping.globalmaxgroups)
      * [grouping.defaultPrecisionFactor](#grouping.defaultprecisionfactor)
      * [timezone](#timezone)

Streaming
:   * [streaming.groupname](#streaming.groupname)
    * [streaming.selection](#streaming.selection)
    * [streaming.maxbucketspervisitor](#streaming.maxbucketspervisitor)

Tracing
:   * [trace.level](#trace.level)
    * [trace.explainLevel](#trace.explainlevel)
    * [trace.profileDepth](#trace.profiledepth)
    * [trace.profiling.matching.depth](#trace.profiling.matching.depth)
    * [trace.profiling.firstPhaseRanking.depth](#trace.profiling.firstPhaseRanking.depth)
    * [trace.profiling.secondPhaseRanking.depth](#trace.profiling.secondPhaseRanking.depth)
    * [trace.timestamps](#trace.timestamps)
    * [trace.query](#trace.query)

Semantic Rules
:   * [rules.off](#rules.off)
    * [rules.rulebase](#rules.rulebase)
    * [tracelevel.rules](#tracelevel.rules)

Dispatch
:   * [dispatch.topKProbability](#dispatch.topkprobability)

Other
:   * [recall](#recall)
    * [user](#user)
    * [hitcountestimate](#hitcountestimate)
    * [metrics.ignore](#metrics.ignore)
    * [weakAnd.replace](#weakand.replace)
    * [wand.hits](#wand.hits)
    * [sorting.degrading](#sorting.degrading)
    * [noCache](#nocache)

## Query

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| yql |  | String |  | See the [YQL query guide](../query-language.html) for examples, and the [reference](query-language-reference.html) for details. |

## Native Execution Parameters

These parameters are defined in the `native` query profile type.

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| hits | count | Number | 10 | A positive integer, including 0. The maximum number of hits to return from the result set.  `hits` is capped at `maxHits`, default 400. `maxHits` can be set in a [query profile](../query-profiles.html).  Number of hits can also be set in [YQL](query-language-reference.html#limit-offset). |
| offset | start | Number | 0 | To implement pagination: The number of hits to skip when returning the result. A positive integer, including 0.  `offset` is capped at `maxOffset`, default 1000. `maxOffset` can be set in a [query profile](../query-profiles.html).  Offset can also be set in [YQL](query-language-reference.html#limit-offset). |
| queryProfile |  | String | `default` | A query profile id with format `name:version`, where version can be omitted or partially specified, e.g. `myprofile:2.1`. A [query profile](../query-profiles.html) has default properties for a query. The default query profile is named *default*. |
| groupingSessionCache |  | Boolean | true | Set to true to enable grouping session cache. See the [grouping reference](grouping-syntax.html#grouping-session-cache) for details. |
| searchChain |  | String | `default` | A search chain id with format `name:version`, where version can be omitted or partially specified, e.g. `mychain:2.1.3`. The [search chain](../components/chained-components.html) initially invoked when processing the query. This search chain may invoke other chains. |
| timeout |  | String | 0.5s | Positive floating point number with an optional unit. Default unit is seconds (s), valid unit strings are e.g. *ms* and *s*. To set a timeout of one minute, the argument could be set to *60 s*. Space between the number and the unit is optional.  It specifies the overall timeout of the query execution and can be defined in a [query profile](../query-profiles.html). Different classes of queries can then easily have a different latency budget/timeout using different profiles.  At timeout, the hits generated thus far are returned, refer to [ranking.softtimeout.enable](#ranking.softtimeout.enable) for details on HTTP status codes and response elements.  Refer to the [Query API guide](../query-api.html#timeout) for more details on timeout handling. |

## Query Model Parameters

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| model.defaultIndex | default-index | String | `default` | An index name. The field which is searched for query terms which doesn't explicitly specify an index. Also see the [defaultIndex](query-language-reference.html#defaultindex) query annotation. |
| model.encoding | encoding | String | `utf-8` | Encoding names or aliases defined in the [IANA character sets](https://www.iana.org/assignments/character-sets/character-sets.xhtml). Sets the encoding to use when returning a result. The query is always encoded as UTF-8, independently of how the result will be encoded.  The encodings `big5`, `euc-jp`, `euc-kr`, `gb2312`, `iso-2022-jp` and `shift-jis` also influences how [tokenization](../linguistics.html#tokenization) is done in the absence of an explicit language setting. |
| model.filter | filter | String |  | A filter string in the [Simple Query Language](simple-query-language-reference.html). Sets a filter to be combined with the [model.queryString](#model.querystring). Typical use of a filter is to add machine generated or preferences based filter terms to the user query.  Terms which are passed in the filter are not [bolded](#presentation.bolding). The filter is parsed the same way as a query of type `any`, the full syntax is available. The positive terms (preceded by +) and phrases act as AND filters, the negative terms (preceded by -) act as NOT filters, while the unprefixed terms will be used to RANK the results. Unless the query has no positive terms, the filter will only restrict and influence ranking of the result set, never cause more matches than the query.  The [model.queryString](#model.querystring) must be present for this to have any effect. To add filters to the YQL string, use query profiles. See [example](/en/query-profiles.html#example). |
| model.locale | locale | String |  | A language tag from [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646). Sets the locale and language to use when parsing queries from a language tag, such as `en-US`. This attribute should always be set when it is known. If this parameter is not set, it will be guessed from the query and encoding, and default to english if it cannot be guessed. |
| model.language | lang, language | String |  | A language tag from [RFC 5646](https://www.rfc-editor.org/rfc/rfc5646), but allowing underscore instead of dash as separator character. A legacy alternative to locale. When this value is accessed, underscores will be replaced by dashes in the returned value. Also see the [language](query-language-reference.html#language) query term annotation. |
| model.queryString | query | String |  | A query string in the [Simple Query Language](simple-query-language-reference.html). It is combined with [model.filter](#model.filter). See the [userQuery](query-language-reference.html#userquery) operator for how to combine with YQL. Can also be used without YQL. |
| model.restrict | restrict | String |  | A comma-delimited list of document type (schema) names, defaulting to all schemas if not set. See [multiple schemas](../schemas.html#multiple-schemas) and [federation](../federation.html).  Use [model.sources](#model.sources) to restrict to content cluster names or other source names. |
| model.searchPath | searchpath | String |  | Specification of which content nodes a query should be sent to. This is useful for debugging/monitoring and when using [Rank phase statistics](../phased-ranking.html#rank-phase-statistics). Note that in a content cluster with flat distribution (i.e. no <group> element in *services.xml*), there is 1 implicit group.  If not set, defaults to all nodes in one group, selected by load balancing.  `searchpath::ELEMENT [';' ELEMENT]*`  `ELEMENT::NODE ['/' GROUP]`  `NODE::EXP [',' EXP]*`  `EXP::NUM | RANGE`  `GROUP::NUM | '*'`  `RANGE::'['NUM ',' NUM ' >'`  Examples:   * `7/3` = node 7, group 3. * `7/` = node 7, any group. * `*/0` = all nodes in group 0 * `7,1,9/0` = nodes 1,7 and 9, group 0. * `1,[3,9>/0` = nodes 1,3,4,5,6,7,8, group 0. |
| model.sources | search, sources | String |  | A comma-separated list of content cluster names or other source names, defaulting to all sources/clusters if not set. The names of the sources to query, e.g. one or more content clusters and/or federated sources - see [content cluster mapping](../schemas.html#content-cluster-mapping). Also see [federation](../federation.html).  Use [model.restrict](#model.restrict) to only search a subset of the schemas in a cluster. |
| model.type | type | String | `weakAnd` | Sets all the model.type parameters (composite, tokenization, and syntax) specifying how to parse a [model.queryString](#model.querystring) parameter at once, according to the given table:   | Value Results in | | | | | --- | --- | --- | --- | | composite tokenization syntax | | | | all and internal simple | | | | | any or internal simple | | | | | linguistics weakAnd linguistics none | | | | | phrase phrase internal none | | | | | tokenize weakAnd internal none | | | | | weakAnd weakAnd internal simple | | | | | web and internal web | | | | | yql and internal yql | | | |   Also see [YQL grammar](query-language-reference.html#userinput). |
| model.type.composite |  | String | `Determined by model.type` | Sets the Vespa query composite type that will collect parsed terms of the query by default.   |  |  | | --- | --- | | and Create an AndItem which only matches if *all* terms are present. | | | near Create a NearItem which matches if all the terms appear near each other (gap of 1 by default). | | | oNear Create an ONearItem which matches if all the terms appear near each other (gap of 1 by default), in the given order. | | | or Create an OrItem which matches if *any* of the terms are present. | | | phrase Create a PhraseItem which matches if all the terms are present in the given order with no gaps. | | | weakAnd Create a [WeakAndItem](https://docs.vespa.ai/en/using-wand-with-vespa.html#weakand) which has the semantics of `or` with performance approaching `and`. | | |
| model.type.tokenization |  | String | `Determined by model.type` | Sets the tokenizer used to split the query string into tokens.   |  |  | | --- | --- | | internal Use the tokenizer built into the query parser. | | | linguistics Pass the full query string as-is to the linguistics component for tokenization, exactly as on the indexing side, and collect any text and numeric token returned as-is, with no further stemming or normalization even when specified in the schema. This is only supported in conjunction with the `none` syntax option. | | |
| model.type.syntax |  | String | `Determined by model.type` | Sets the syntax used to interpret the query string. Options:   |  |  | | --- | --- | | none | No syntax: Disregard any non-searchable terms | | simple | Use the [simple query language](simple-query-language-reference.html) suitable for end users. | | web | Like the [simple query language](simple-query-language-reference.html), but '+' in front of a term means "search for this term as-is", and 'a OR b' (capital OR) means match either a or b. | | yql | Parse as a [YQL query](https://docs.vespa.ai/en/reference/query-language-reference.html). | |
| model.type.isYqlDefault |  | Boolean | `false` | Whether the model.type settings should be used as the default settings for terms in YQL queries. With this parameter turned on, the model.type settings become the default "grammar" settings in userQuery, and with tokenization set to `linguistics` this will also cause "contains" terms to not undergo stemming, normalization and lowercasing as separate operations, as using this mode delegates all token processing to a single pass through the lingustics module. |

## Ranking

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| ranking.location |  | String |  | See [Geo search](../geo-search.html). Point (two-dimensional location) to use as base for location ranking. {% include deprecated.html content=" Deprecated in favor of adding a [geoLocation](query-language-reference.html#geolocation) item to the query tree. Use inside a [rank](query-language-reference.html#rank) operator if it should be used only for ranking)."%} |
| ranking.features .*featurename* | input .*featurename*, rankfeature .*featurename* | String |  | Set a query rank feature input to a value. The key must be a query feature - `query(anyname)`, and the value must be a double, string (to be hashed to a double), or a tensor matching the [declared input type](schema-reference.html#inputs) on [tensor literal form](tensor.html#tensor-literal-form) - see the [tensor user guide](../tensor-user-guide.html#querying-with-tensors). Examples:  `input.query(userageDouble)=42.1`  `input.query(stringToBeHashed)=abcd`  `input.query(myIndexedTensor)=[1.0, 2.0, 3.0]`  `input.query(myMappedTensor)={"Tablet Keyboard Cases": 0.8, "Keyboards":0.3}` |
| ranking.listFeatures | rankfeatures | Boolean | false | Set to true to request *all* [rank-features](schema-reference.html#rank-features) to be calculated and returned. The rank features will be returned in the summary field *rankfeatures*. This option is typically used for MLR training, should not to be used for production. |
| ranking.profile | ranking | String | `default` | Sets [rank profile](schema-reference.html#rank-profile) to use for assigning rank scores for documents. The `default` rank profile will be used for backends which does not have the given rank profile. |
| ranking.properties .*propertyname* | rankproperty .*propertyname* | String |  | Set a [rank property](schema-reference.html#rank-properties) that is passed to, and used by a feature executor for this query. Example: `query=foo&ranking.properties.dotProduct.X={a:1,b:2}` |
| ranking.softtimeout .enable |  | Boolean | true | By default, the hits available are returned on [timeout](#timeout). To return no hits at timeout instead, set `ranking.softtimeout.enable=false`.  Softtimeout uses `ranking.softtimeout.factor` of the [timeout](#timeout), default 70%. The rest of the time budget is spent on later ranking phases.  The factor is adaptive, per rank profile - the factor is adjusted based on remaining time after all ranking phases, unless overridden in the query using `ranking.softtimeout.factor`.  A [timeout](default-result-format.html#timeout) element is returned in the query response at timeout.  Example: query with 500ms timeout, use 300ms in first-phase ranking: `&ranking.softtimeout.enable=true &ranking.softtimeout.factor=0.6 &timeout=0.5`  The `ranking.softtimeout` settings controls what the content nodes should do in the case where the latency budget has almost been used (timeout times a factor). Return the documents recalled and ranked with the [first phase function](../phased-ranking.html) within the time used, or simply don't produce a result:   * With soft timeout disabled, the Vespa container will return a 504 timeout without any results. * When enabled, it will return the documents matched and ranked up until the timeout was reached,   with a 200 OK response along with the reason the result set was degraded.   The container might respond with a timeout error with HTTP response code 504 even with soft timeout enabled if the timeout is set so low that the query does not make it to the content nodes, or the container does not have any time left after input and query processing to dispatch the query to the content nodes.  Read more about soft timeout in [coverage degradation](../graceful-degradation.html). |
| ranking.softtimeout .factor |  | Number | 0.7 | See [ranking.softtimeout.enable](#ranking.softtimeout.enable). |
| ranking.sorting | sorting | String |  | A valid [sort specification](sorting.html). Fields you want to sort on must be stored as document attributes in the index structure by adding [attribute](schema-reference.html#attribute) to the indexing statement. |
| ranking.significance.useModel |  | Boolean | false | Enables or disables the use of significance models specified in [service.xml](services-search.html#significance). Overrides [use-model](schema-reference.html#significance) set in the rank profile. |
| ranking.freshness |  | String |  | Sets the time which will be used as *now* during execution.  `[integer]`, an absolute time in seconds since epoch, or `now-[number]`, to use a time [integer] seconds into the past, or `now` to use the current time. |
| ranking.queryCache |  | Boolean | false | Turns query cache on or off. Query is a two-phase process. If the query cache is on, the query is stored on the content nodes between the first and second phase, saving network bandwidth and also query setup time, at the expense of using more memory. It only affects the protocol phase two, see [caches in Vespa](../performance/caches-in-vespa.html). It does not cache the result, it just saves resources by not forwarding the query twice (one for the first protocol phase which is find the best k documents from all nodes, to the second phase which is to fill summary data and potentially ranking features listed in summary-features in the rank profile).  The [summary-features](schema-reference.html#summary-features) are re-calculated but this setting avoids sending the query down once more. There is little downside of using it, and it can save resources and latency in cases where the query tree and query ranking features (e.g. tensors used in ranking) are large. As this is a protocol optimization, it also works with changing filter, it's not cached cross independent queries, it's just saving having to send the same query twice. |
| ranking.rerankCount |  | Number |  | Specifies the number of hits that should be ranked in the second ranking phase. Overrides the [rerank-count](schema-reference.html#secondphase-rerank-count) set in the rank profile. Setting to 0 disables the second phase reranking. |
| ranking.keepRankCount |  | Number |  | Specifies the number of hits that should keep rank value. Overrides the [keep-rank-count](schema-reference.html#keep-rank-count) set in the rank profile. |
| ranking.rankScoreDropLimit |  | Number |  | Minimum rankscore for a document to be considered a hit. Overrides the [rank-score-drop-limit](schema-reference.html#rank-score-drop-limit) set in the rank profile. |
| ranking.secondphase.rankscoredroplimit |  | Number |  | Minimum rank score for a document to be considered a hit after second phase reranking or rescoring. Overrides the [second phase rank-score-drop-limit](schema-reference.html#secondphase-rank-score-drop-limit) set in the rank profile. |
| ranking.globalPhase.rerankCount |  | Number |  | Specifies the number of hits that should be re-ranked in the global ranking phase. Overrides the [rerank-count](schema-reference.html#globalphase-rerank-count) set in the rank profile. Setting to 0 disables the global phase reranking. |
| ranking.globalphase.rankscoredroplimit |  | Number |  | Minimum rank score for a document to be considered a hit after global phase reranking or rescoring. Overrides the [global phase rank-score-drop-limit](schema-reference.html#globalphase-rank-score-drop-limit) set in the rank profile. |

## ranking.matching

Settings to control behavior during matching of query evaluation.
If these are set in the query, they will override any equivalent settings in the
[rank profile](schema-reference.html#rank-profile).
Detailed descriptions are found in the rank profile documentation.

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| ranking.matching .numThreadsPerSearch |  | integer |  | Rank profile equivalent: [num-threads-per-search](schema-reference.html#num-threads-per-search)  Overrides the global [persearch](services-content.html#requestthreads-persearch) threads to a **lower** value. |
| ranking.matching .minHitsPerThread |  | integer |  | Rank profile equivalent: [min-hits-per-thread](schema-reference.html#min-hits-per-thread)  After estimating the number of hits for a query, this number is used to decide how many search threads to use. |
| ranking.matching .numSearchPartitions |  | integer |  | Rank profile equivalent: [num-search-partitions](schema-reference.html#num-search-partitions)  Number of logical partitions the corpus on a content node is divided in. A partition is the smallest unit a search thread will handle. |
| ranking.matching .termwiseLimit |  | double [0.0, 1.0] |  | Rank profile equivalent: [termwise-limit](schema-reference.html#termwise-limit)  If estimated number of hits > corpus * termwise-limit, document candidates are pruned with a [TAAT](../performance/feature-tuning.html#hybrid-taat-daat) evaluation for query terms not needed for ranking. |
| ranking.matching .postFilterThreshold |  | double [0.0, 1.0] | 1.0 | Rank profile equivalent: [post-filter-threshold](schema-reference.html#post-filter-threshold)  Threshold value deciding if a query with an approximate [nearestNeighbor](query-language-reference.html#nearestneighbor) operator combined with filters is evaluated using post-filtering. |
| ranking.matching .approximateThreshold |  | double [0.0, 1.0] | 0.05 | Rank profile equivalent: [approximate-threshold](schema-reference.html#approximate-threshold)  Threshold value deciding if a query with an approximate [nearestNeighbor](query-language-reference.html#nearestneighbor) operator combined with filters is evaluated by searching for approximate or exact nearest neighbors. |
| ranking.matching .filterFirstThreshold |  | double [0.0, 1.0] | 0.0 | Rank profile equivalent: [filter-first-threshold](schema-reference.html#filter-first-threshold)  Threshold value deciding if the filter is checked before computing a distance (*filter-first heuristic*) while searching the [HNSW](schema-reference.html#index-hnsw) graph for approximate neighbors with filtering. |
| ranking.matching .filterFirstExploration |  | double [0.0, 1.0] | 0.3 | Rank profile equivalent: [filter-first-exploration](schema-reference.html#filter-first-exploration)  Value specifying how aggressively the filter-first heuristic searches the [HNSW](schema-reference.html#index-hnsw) graph for approximate neighbors with filtering. |
| ranking.matching .explorationSlack |  | double [0.0, 1.0] | 0.0 | Rank profile equivalent: [exploration-slack](schema-reference.html#exploration-slack)  Value specifying slack to delay the termination of the search of the [HNSW](schema-reference.html#index-hnsw) graph for nearest neighbors with or without filtering. |
| ranking.matching .targetHitsMaxAdjustmentFactor |  | double [1.0, inf] |  | Rank profile equivalent: [target-hits-max-adjustment-factor](schema-reference.html#target-hits-max-adjustment-factor)  Value used to control the auto-adjustment of [targetHits](query-language-reference.html#targethits) used when evaluating an approximate [nearestNeighbor](query-language-reference.html#nearestneighbor) operator with post-filtering. |
| ranking.matching .filterThreshold |  | double [0.0, 1.0] |  | Rank profile equivalent: [filter-threshold](schema-reference.html#filter-threshold)  Threshold value (in the range [0, 1]) deciding when matching in *index* fields should be treated as filters. This happens for query terms with [estimated hit ratios](../glossary.html#estimated-hit-ratio) that are above the *filterThreshold*. |
| ranking.matching.weakand .stopwordLimit |  | double [0.0, 1.0] |  | Rank profile equivalent: [weakand stopword-limit](schema-reference.html#weakand-stopword-limit)  A number in the range [0, 1] representing the maximum [normalized document frequency](../glossary.html#document-frequency-normalized) a query term can have in the corpus before it's considered a stopword and dropped entirely from being a part of the `weakAnd` evaluation. |
| ranking.matching.weakand .adjustTarget |  | double [0.0, 1.0] |  | Rank profile equivalent: [weakand adjust-target](schema-reference.html#weakand-adjust-target)  A number in the range [0, 1] representing [normalized document frequency](../glossary.html#document-frequency-normalized). Used to derive a per-query document score threshold, where documents scoring lower than the threshold will not be considered as potential hits from the `weakAnd` operator. |
| ranking.matching.weakand .allowDropAll |  | boolean | false | Rank profile equivalent: [weakand allow-drop-all](schema-reference.html#weakand-allow-drop-all)  A boolean value that, if set to `true`, will allow the `weakAnd` operator to drop *all* terms from the query if all terms are considered stopwords (i.e by setting `weakAnd.stopwordLimit`).  Typically used in conjunction with [nearestNeighbor](/en/nearest-neighbor-search.html#querying-using-nearestneighbor-query-operator) or other operators to ensure that the query will return hits even when all terms are considered stopwords. |

## ranking.matchPhase

Settings to control behavior during the match phase of query evaluation.
If these are set in the query, they will override any
[match-phase](schema-reference.html#match-phase) settings in the rank profile.
Detailed descriptions are found in the rank profile documentation.

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| ranking.matchPhase .attribute |  | string |  | Rank profile equivalent: [match-phase: attribute](schema-reference.html#match-phase-attribute)  The attribute used to limit matches by if more than maxHits hits will be produced. |
| ranking.matchPhase .maxHits |  | long |  | Rank profile equivalent: [match-phase: max-hits](schema-reference.html#match-phase-max-hits)  The max number of hits that should be generated on each content node during the match phase.  Setting the value to `0` disables the match phase early termination. |
| ranking.matchPhase .ascending |  | boolean |  | Rank profile equivalent: [match-phase: order](schema-reference.html#match-phase-order)  Whether to keep the documents having the highest (false) or lowest (true) values of the match phase attribute. |
| ranking.matchPhase .diversity.attribute |  | string |  | Rank profile equivalent: [diversity: attribute](schema-reference.html#diversity-attribute)  The attribute to use when deciding diversity. |
| ranking.matchPhase .diversity.minGroups |  | long |  | Rank profile equivalent: [diversity: min-groups](schema-reference.html#diversity-min-groups)  The minimum number of groups that should be returned from the match phase grouped by the diversity attribute. |

## Dispatch

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| dispatch.topKProbability |  | double |  | Probability to use when computing how many hits to fetch from each partition when merging and creating the final result set. See [services](services-content.html#top-k-probability) for details.  Default: [none](services-content.html#top-k-probability). |

## Presentation

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| presentation.bolding | bolding | Boolean | true | Whether to bold query terms in [schema](schema-reference.html) fields defined with [bolding: on](schema-reference.html#bolding) or [summary: dynamic](schema-reference.html#summary). |
| presentation.format | format | String | `default` | | Value | Description | | --- | --- | | *No value* or [default](default-result-format.html) | The default, builtin JSON format | | [json](default-result-format.html) | Builtin JSON format | | `xml` | Builtin XML format. {% include deprecated.html content="See [deprecations](../vespa8-release-notes.html)."%} | | [page](page-result-format.html) | XML format which is suitable for use with [page templates](../page-templates.html). {% include deprecated.html content="See [deprecations](../vespa8-release-notes.html)."%} | | *Any other value* | A custom [result renderer](../result-rendering.html) supplied by the application | |
| presentation.summary | summary | String |  | The name of the [summary class](../document-summaries.html) used to select fields in results.  Default: The default summary class of the schema. |
| presentation.template |  | String |  | The id of a deployed page template to use for this result. This should be used with the [page](page-result-format.html) result format. |
| presentation.timing |  | Boolean | false | Whether a result renderer should try to add optional timing information to the rendered page - see the [result reference](default-result-format.html#timing). |
| presentation.format.tensors |  | String | `short` | Controls how tensors are rendered in the result.   | Value | Description | | --- | --- | | `short` | Render the tensor value in an object having two keys, "type" containing the value, and "cells"/"blocks"/"values" ([depending on the type](document-json-format.html#tensor)) containing the tensor content.  Render the tensor content in the [type-appropriate short form](document-json-format.html#tensor). | | `long` | Render the tensor value in an object having two keys, "type" containing the value, and "cells" containing the tensor content.  Render the tensor content in the [general verbose form](document-json-format.html#tensor). | | `short-value` | Render the tensor content directly.  Render the tensor content in the [type-appropriate short form](document-json-format.html#tensor). | | `long-value` | Render the tensor content directly.  Render the tensor content in the [general verbose form](document-json-format.html#tensor). | | `hex` | Use `short` form, and render dense values [hex encoded](tensor.html#indexed-hex-form). | | `hex-value` | Use `short-value` form, and render dense values [hex encoded](tensor.html#indexed-hex-form). | |

## Grouping and Aggregation

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| select |  | String |  | Requests specific multi-level result set statistics and/or hit groups to be returned in the result. Fields you want to retrieve statistics or hit groups for must be stored as document attributes in the index structure by adding attribute to the indexing statement.  Default is no grouping.  See the [grouping guide](../grouping.html) for examples. |
| collapsefield |  | String |  | Comma-separated list of [field names](schema-reference.html#summary), that should only appear uniquely in a result. Hits with values in these fields which are already present in a higher-ranked hit will be filtered out.  Read more in [result diversity](/en/result-diversity.html) to compare this with other options.  Default is no field collapsing. |
| collapsesize |  | Number | 1 | The number of hits to keep in each collapsed bucket - used for all collapsefields. |
| collapsesize.*fieldname* |  | Number | 1 | The number of hits to keep in each collapsed bucket - used for the specified field. This value takes precedence over the value specified in `collapsesize`. |
| collapse.summary |  | String |  | A valid name of a document summary class. Use this summary class to fetch the fields used for collapsing.  Default: Use default summary or attributes. |
| grouping.defaultMaxGroups |  | Number | 10 | Positive integer or `-1` to disable.  The default number of groups to return when [max](../grouping.html#ordering-and-limiting-groups) is not specified. |
| grouping.defaultMaxHits |  | Number | 10 | Positive integer or `-1` to disable.  The default number of hits to return when [max](../grouping.html#hits-per-group) is not specified. |
| grouping.globalMaxGroups |  | Number | 10000 | Positive integer or `-1` to disable.  A cost limit for grouping queries. Any query that may exceed this threshold will be preemptively failed by the container. The limit is defined as the total number of groups and document summaries a query may produce. A query that does not have an implicit or explicit `max` defined for all levels will always fail if limit is enabled. This parameter can only be overridden in a [query profile](../query-profiles.html).  See the [grouping guide](../grouping.html#global-limit) for practical examples. |
| grouping.defaultPrecisionFactor |  | Decimal number | 2.0 | The default precision scale factor when [precision](../grouping.html#ordering-and-limiting-groups) is not specified. The final precision value is calculated by multiplying the effective `max` value with the scale factor. |
| timezone |  | String | `utc` | Specifies a timezone that will be used to offset all `time` related expressions in grouping. See [Java's definition](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/TimeZone.html#getTimeZone(java.lang.String)) for valid timezones.  See the [grouping guide](../grouping.html#timezone-grouping) for examples. |

## Streaming

Parameters for [streaming search mode](../streaming-search.html).

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| streaming.groupname |  | A string |  | Sets the group (specified by [g=<groupname>](../documents.html#id-scheme)) of the documents to stream through. |
| streaming.selection |  | A [document selection](document-select-language.html) |  | Restricts streaming search using a selection expression instead of a group id.  If the selection is on the form `id.group == "foo" or id.group == "bar" or id.group == ...` this will only stream documents in those groups, which is efficient for a small number of groups.  If any other selection is used, this will stream through *all* groups, which is very costly. |
| streaming.maxbucketspervisitor |  | An integer Positive infinity | If set, limit backend bucket concurrency to the specified number of buckets. Can be used to explicitly control resource usage for extremely large streaming search locations. This is an expert option. | |

## Tracing

Parameters controlling trace information returning with the result for diagnostics.

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| trace.level | tracelevel | Number | 0 | A positive number. Default is no tracing.  Collect trace information for debugging when running a query. Higher numbers give progressively more detail on query transformations, searcher execution and content node(s) query execution. See [query tracing](../query-api.html#query-tracing) for details and examples.  Tracing is subject to change at any time, the below is a guide:   | Level | Description | | --- | --- | | 1 | Basic tracing in container | | 2 | Basic tracing, more details | | 3 | Basic tracing, even more details | | 4 | Include timing info from content nodes | | 5 | Even more timing info from content nodes | | 6 | Include the query execution plan (blueprint) | | 7 | Include the query execution tree | |
| trace.explainLevel | explainlevel | Number | 0 | Set to a positive number to collect query execution information for debugging when running a query. Higher numbers give progressively more detail on content node query execution. Tuning this parameter is useful if we want to get more information from the content nodes without gathering lots of trace information from the container chain.  Explanation is subject to change at any time, the below is a guide:   | Level | Description | | --- | --- | | 1 | Timing and overall query plan (blueprint) from each content node | | 2 | Timing per search thread and execution tree (search iterator tree) |   Note that you might get the same at [trace.level](#trace.level) 5 and above. Default is no explanation.  Tracing with `trace.explainLevel` also requires that [trace.level](#trace.level) is positive. |
| trace.profileDepth |  | Number | 0 | Turns on performance profiling of the content node query execution for [matching](#trace.profiling.matching.depth), [first-phase ranking](#trace.profiling.firstPhaseRanking.depth), and [second-phase ranking](#trace.profiling.secondPhaseRanking.depth). How profiling is performed is based on whether `trace.profileDepth` is positive or negative:   | Type | Description | | --- | --- | | Tree | A positive number specifies the depth used by a tree profiler. A higher number means more profiler data. The output resembles the structure of the search iterator tree or rank expression tree being profiled, with total time and self time tracked per component (node in the tree). | | Flat | A negative number specifies the topn (cut-off) used by a flat profiler. The output returns the topn components that use the most self time. |   The performance profiling output is subject to change at any time. Default is no information.  Tracing with `trace.profileDepth` also requires that [trace.level](#trace.level) is positive. |
| trace.profiling.matching.depth |  | Number | 0 | Turns on profiling of [matching](../performance/sizing-search.html#life-of-a-query-in-vespa) of the content node query execution. This exposes information about how time spent on matching is distributed between individual search iterators. The profiling output is tagged *match_profiling* and is subject to change at any time. Default is no information. See [trace.profileDepth](#trace.profiledepth) for semantics of this parameter.  Tracing with `trace.profiling.matching.depth` requires that [trace.level](#trace.level) is positive. |
| trace.profiling.firstPhaseRanking.depth |  | Number | 0 | Turns on profiling of the [first-phase ranking](../ranking.html) of the content node query execution. This exposes information about how time spent on first-phase ranking is distributed between individual [rank features](rank-features.html). The profiling output is tagged *first_phase_profiling* and is subject to change at any time. Default is no information. See [trace.profileDepth](#trace.profiledepth) for semantics of this parameter.  Tracing with `trace.profiling.firstPhaseRanking.depth` also requires that [trace.level](#trace.level) is positive. |
| trace.profiling.secondPhaseRanking.depth |  | Number | 0 | Turns on profiling of the [second-phase ranking](../ranking.html) of the content node query execution. This exposes information about how time spent on second-phase ranking is distributed between individual [rank features](rank-features.html). The profiling output is tagged *second_phase_profiling* and is subject to change at any time. Default is no information. See [trace.profileDepth](#trace.profiledepth) for semantics of this parameter.  Tracing with `trace.profiling.secondphaseRanking.depth` also requires that [trace.level](#trace.level) is positive. |
| trace.timestamps |  | Boolean | false | Enable to get timing information already at [trace.level=1](#trace.level). This is useful for debugging latency spent at different components in the container search chain without rendering a lot of string data which is associated with higher trace levels. |
| trace.query |  | Boolean | true | Whether to include the query in any trace messages. This is useful for avoiding query serialization with very large queries to avoid impact from it on performance and excessively large traces. |

## Semantic Rules

Refer to [semantic rules](semantic-rules.html).

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| rules.off |  | Boolean | true | Turn rule evaluation off for this query. |
| rules.rulebase |  | String |  | A rule base name - the name of the rule base to use for these queries. |
| tracelevel.rules |  | Number |  | The amount of rule evaluation trace output to show, higher number means more details. This is useful to see a trace from rule evaluation without having to see trace from all other searchers at the same time. |

## Other

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| recall |  | String |  | Any allowed collection of recall terms. Sets a recall parameter to be combined with the query. This is identical to [filter](#model.filter), except that recall terms are not exposed to the ranking framework and thus not ranked. As such, one can not use unprefixed terms; they must either be positive or negative. |
| user |  | String |  | The id of the user making the query. The content of the argument is made available to the search chain, but it triggers no features in Vespa apart from being propagated to the access log. |
| hitcountestimate |  | Boolean | false | Make this an estimation query. No hits will be returned, and total hit count will be set to an estimate of what executing the query as a normal query would give. |
| metrics.ignore |  | Boolean | false | Ignore metric collection for this query request, useful for [warm-up queries](../performance/container-tuning.html#container-warmup). |
| weakAnd.replace |  | Boolean | false | Replace all instances of OR in the query tree with weakAnd. |
| wand.hits |  | Number | 100 | Used in combination with [weakAnd.replace](#weakand.replace). Sets the targetHits of the new weakAnds to the specified value. |
| sorting.degrading |  | Boolean | true | When sorting on a [single-value numeric attribute with fast-search](../attributes.html) an optimization is activated to return early, with an inaccurate total-hits count. Set `sorting.degrading` to false to disable this optimization.  This optimization sets the primary sorting attribute as the [match phase attribute](#ranking.matchphase.attribute), and [match phase maxHits](#ranking.matchphase.maxhits) equal to `max(10000, maxHits+maxOffset)`. [maxHits](#hits) and [maxOffset](#offset) can be set in a query profile. |
| noCache | nocache | Boolean | false | Sets whether this query should never be served from a cache. Vespa has [few caches](../performance/caches-in-vespa.html), and this parameter does not control any of them. Therefore, this parameter has no effect |

## HTTP status codes

The following rules determine which HTTP status code is returned:
* If the Result contains no errors (Result.hits().getError()==null): 200 OK is returned.
* If the Result contains errors and no regular hits:
  + If the error code of any ErrorMessage in the Result
    (Result.hits().getErrorHit().errorIterator()) is a "WEB SERVICE ERROR CODE",
    the first of those is returned.
  + Otherwise, if it is an "HTTP COMPATIBLE ERROR CODE", the mapping of it is returned.
  + Otherwise 500 INTERNAL_SERVER_ERROR is returned.
* If the Result contains errors and also contains valid hits:
  The same as above, but 200 OK is returned by default instead of 500.

List of possible HTTP status codes and their descriptions.

| Code | Description |
| --- | --- |
| 200 | OK |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 405 | Method Not Allowed |
| 408 | Request Timeout |
| 428 | Precondition Required |
| 431 | Request Header Fields Too Large |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable; no available search handler threads in the jdisc container to serve the request. See [Container Tuning](../performance/container-tuning.html#container-worker-threads) on sizing thread pools. |
| 504 | Gateway Timeout |
| 507 | Insufficient Storage |

### Error code to status code mapping

Mapping of internal error codes to HTTP status codes.

| Error Code | HTTP Code |
| --- | --- |
| com.yahoo.container.protect.Error.BAD_REQUEST | 400 |
| com.yahoo.container.protect.Error.UNAUTHORIZED | 401 |
| com.yahoo.container.protect.Error.FORBIDDEN | 403 |
| com.yahoo.container.protect.Error.NOT_FOUND | 404 |
| com.yahoo.container.protect.Error.INTERNAL_SERVER_ERROR | 500 |
| com.yahoo.container.protect.Error.INSUFFICIENT_STORAGE | 507 |
---

## select

A `select` query is equivalent in structure to YQL, written in JSON.
Contains subparameters `where` and `grouping`.

| Parameter | Alias | Type | Default | Description |
| --- | --- | --- | --- | --- |
| where |  | String |  | A string with JSON. Refer to the [select reference](select-reference.html) for details. |
| grouping |  | String |  | A string with JSON. Refer to the [select reference](select-reference.html) for details. |
