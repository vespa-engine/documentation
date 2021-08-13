import handleResults from "./handle_results.js";
import handleSuggestionResults from "./handle_search_suggestions.js";
import handleSuggestionResult, {handleUnfocus, hideDropdown} from "./handle_search_suggestions.js";

const debounce = (func, timeout = 500) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
};

const handleShadow = (event) => {
  const suggestText = document.getElementById("textSuggest");
  if (!suggestText.innerHTML.startsWith(event.target.value)) {suggestText.innerHTML = ""; document.getElementById("searchinput").placeholder = "Search Documentation";}
}

const handleQuery = (query) => {

  if (query.length > 0) {

    const result = document.getElementById("result");
    
    document.getElementById("hits").innerHTML = "";
    result.innerHTML = `Searching for '${query}' ...`;
    console.log(window.location.pathname)
 fetch(
  `https://doc-search.vespa.oath.cloud/search/?term=${escape(query)}`
)
      .then((res) => res.json())
      .then((res) => {const children = (res.root.children)? res.root.children : [];
        handleSuggestionResults(children.filter(child => child.fields.sddocname == "term"));
        handleResults(children.filter(child => child.fields.sddocname == "doc"))})
      .catch(console.error);
  } else {
    document.getElementById("hits").innerHTML = "";
    result.innerHTML = "";
    const suggestText = document.getElementById("textSuggest");
    suggestText.innerHTML = "";
    document.getElementById("searchinput").placeholder = "Search Documentation";
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
    console.log(query)
    //handleQuery(query);
    result.innerHTML = `Searching for '${query}' ...`;
    fetch(
      `https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20doc%20where%20userInput(@input)%3B&hits=400&ranking=documentation&locale=en-US&input=${escape(query)}`
    )
          .then((res) => res.json())
          .then((res) => handleResults(res.root.children))
  }
};

window.addEventListener("load", handleLocationQuery);
document.getElementById("searchinput").addEventListener(
  "input",
  (event) => {
    handleShadow(event);
    debounce((event) => handleQuery(event.target.value))(event);
  }
);

document.getElementById("searchinput").addEventListener("focusout", handleUnfocus);
