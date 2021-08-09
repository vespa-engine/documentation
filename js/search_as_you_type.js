import handleResults from "./handle_results.js";

const input = document.getElementById("searchinput");
const result = document.getElementById("result");
const searchForm = document.getElementById("search-form");

const debounce = (func, timeout = 300) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
};

const handleInput = (event) => {
  if (event.target.value.length > 0) {
    result.innerHTML = `Searching for '${event.target.value}' ...`;

    fetch(
      `https://doc-search.vespa.oath.cloud/search/?yql=${escape(
        `select * from doc
        where ([{"defaultIndex": "default"}]userInput(@input))
        or ([{"defaultIndex": "grams"}]userInput(@input));`
      )}&input=${escape(
        event.target.value
      )}&hits=128&ranking=weighted_doc_rank&timeout=5s&locale=en-US`
    )
      .then((res) => res.json())
      .then(handleResults)
      .catch(console.error);
  } else {
    output.innerHTML = "";
  }
};

input.addEventListener("input", debounce(handleInput));
