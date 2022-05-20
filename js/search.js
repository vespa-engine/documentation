import handleResults from "./handle_results.js";
import handleSuggestionResults, {handleUnfocus, hideDropdown, handleArrowKeys} from "./handle_search_suggestions.js";

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
    result.innerHTML = `Searching for '${query}' ...`;
  fetch(
      encodeURI("https://doc-search.vespa.oath.cloud/search/?term=" + query)
  )
      .then((res) => res.json())
      .then((res) => { const children = (res.root.children)? res.root.children : [];
        handleSuggestionResults(children.filter(child => child.fields.sddocname == "term"));
        handleResults(children.filter(child => child.fields.sddocname == "doc"))})
      .catch(console.error);
  } else {
    document.getElementById("hits").innerHTML = "";
    result.innerHTML = "";
    hideDropdown();
  }
};

const handleLocationQuery = () => {
  const params = Object.fromEntries(
    decodeURIComponent(window.location.search.substring(1))
      .split("&")
      .map((item) => item.split("="))
  );

  if (params["q"]) {
    const query = decodeURI(params["q"]).replace(/\+/g, " ");
    document.getElementById("searchinput").value = query;
    result.innerHTML = `Searching for '${query}' ...`;
    fetch(
        encodeURI("https://doc-search.vespa.oath.cloud/search/?yql=" +
            "select * from doc where {grammar: \"weakAnd\"}userInput(@userinput)" +
            "&hits=25&ranking=documentation&locale=en-US&userinput=" + query)
    )
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
