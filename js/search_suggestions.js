import handleSuggestionResults, {handleUnfocus, hideDropdown, handleArrowKeys} from "./handle_search_suggestions.js"; 

if (window.location.pathname != "/search.html"){
const input = document.getElementById("searchinput");

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

const handleInput = (e) => {
  if (e.target.value.length > 0) {
    fetch(
      `https://api.search.vespa.ai/search/?yql=select%20*%20from%20sources%20term%20where%20default%20contains%20%28%5B%7B%22prefix%22%3Atrue%7D%5D%22${e.target.value.replaceAll(
        /[^a-zA-Z0-9 ]/g,
        ""
      )}%22%29%3B&ranking=term_rank`
    )
      .then((res) => res.json())
      .then((res) => {const children = (res.root.children)? res.root.children : [];
      handleSuggestionResults(children)})
      .catch(console.error);
  } else {
    hideDropdown();
  }
};

input.addEventListener("input", debounce(handleInput));
input.addEventListener("focusout", handleUnfocus);
input.addEventListener("keydown", handleArrowKeys);
}
