
function generateQueryExamples () {
    let docsearchQueries = document.getElementsByClassName("docsearch-x");
    for (let anchor of docsearchQueries) {
        generateQuery(anchor, "https://doc-search.vespa.oath.cloud/search/");
    }
    let cord19Queries = document.getElementsByClassName("cord19-x");
    for (let anchor of cord19Queries) {
        generateQuery(anchor, "https://api.cord19.vespa.ai/search/");
    }
}

function generateQuery(anchor, endpoint) {
    //let hr = document.createElement("hr");
    //anchor.parentElement.insertBefore(hr, anchor);
    anchor.setAttribute("href", encodeURI(endpoint + "?yql=" + anchor.innerText));
}

document.addEventListener("DOMContentLoaded", generateQueryExamples);
