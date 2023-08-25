
function generateQueryExamples () {
    let docsearchQueries = document.getElementsByClassName("yql-x");
    for (let anchor of docsearchQueries) {
        generateYQL(anchor, "https://doc-search.vespa.oath.cloud/search/");
    }
    let queryStringQueries = document.getElementsByClassName("querystring-x");
    for (let anchor of queryStringQueries) {
        generateQuery(anchor, "https://doc-search.vespa.oath.cloud/search/");
    }
}

function generateYQL(anchor, endpoint) {
    let processed = anchor.innerText
        .replaceAll('”', '"')
        .replaceAll('“', '"')
    anchor.setAttribute("href", encodeURI(endpoint + "?yql=" + processed));
}

function generateQuery(anchor, endpoint) {
    let processed = anchor.innerText
        .replaceAll('”', '"')
        .replaceAll('“', '"')
    anchor.setAttribute("href", encodeURI(endpoint + "?" + processed));
}

document.addEventListener("DOMContentLoaded", generateQueryExamples);
