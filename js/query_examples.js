
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
    anchor.setAttribute("href", encodeURI(endpoint + "?yql=" + anchor.innerText));
}

function generateQuery(anchor, endpoint) {
    anchor.setAttribute("href", encodeURI(endpoint + "?" + anchor.innerText));
}

document.addEventListener("DOMContentLoaded", generateQueryExamples);
