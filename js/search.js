import handleResults from "./handle_results.js";
import handleSuggestionResults, {handleUnfocus, hideDropdown, handleArrowKeys} from "./handle_search_suggestions.js";

const escapeMap = Object.freeze({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
  '/': '&#x2F;',
  '`': '&#x60;',
  '=': '&#x3D;'
});
// https://github.com/janl/mustache.js/blob/550d1da9e3f322649d04b4795f5356914f6fd7e8/mustache.js#L71
const escapeHtml = (string) => String(string).replace(/[&<>"'`=\/]/g, (s) => escapeMap[s]);


// https://www.freecodecamp.org/news/javascript-debounce-example/
const debounce = (func, timeout = 200) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
};


const handleQuery = (query) => {
  if (query.length > 0) {
    const result = document.getElementById("result");
    
    document.getElementById("hits").innerHTML = "";
    result.innerHTML = `Searching for '${escapeHtml(query)}' ...`;
    const searchParams = new URLSearchParams({term: query});
    fetch("https://doc-search.vespa.oath.cloud/search/?" + searchParams.toString())
        .then((res) => res.json())
        .then((res) => { const children = (res.root.children)? res.root.children : [];
          handleSuggestionResults(children.filter(child => child.fields.sddocname === "term"));
          handleResults(children.filter(child => child.fields.sddocname === "doc"))})
        .catch(console.error);
  } else {
    document.getElementById("hits").innerHTML = "";
    result.innerHTML = "";
    hideDropdown();
  }
};

const handleLocationQuery = () => {
  const params = new URLSearchParams(window.location.search);

  if (params.has("q")) {
    const query = params.get("q");
    document.getElementById("searchinput").value = query;
    result.innerHTML = `Searching for '${escapeHtml(query)}' ...`;

    const searchParams = new URLSearchParams({
      yql: 'select * from doc where {grammar: "weakAnd"}userInput(@userinput)',
      hits: 25,
      ranking: 'documentation',
      locale: 'en-US',
      userinput: query,
    });

    fetch("https://doc-search.vespa.oath.cloud/search/?" + searchParams.toString())
        .then((res) => res.json())
        .then((res) => handleResults(res.root.children))
  }
};

document.addEventListener("DOMContentLoaded", handleLocationQuery);
document.getElementById("searchinput").addEventListener(
  "input",
  (event) => {
    debounce(handleQuery(event.target.value));
  }
);

document.getElementById("searchinput").addEventListener("focusout", handleUnfocus);
document.getElementById("searchinput").addEventListener("keydown", handleArrowKeys)
