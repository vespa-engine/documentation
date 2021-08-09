import handleResults from "./handle_results.js";

const debounce = (func, timeout = 300) => {
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

 //   fetch(
 //     `https://doc-search.vespa.oath.cloud/search/?yql=${escape(
 //       `select * from doc
 //       where ([{"defaultIndex": "default"}]userInput(@input))
 //       or ([{"defaultIndex": "grams"}]userInput(@input));`
 //     )}&input=${escape(
 //       query
 //     )}&hits=128&ranking=weighted_doc_rank&timeout=5s&locale=en-US`
 //   )
    fetch(
      `https://doc-search.vespa.oath.cloud/search/?yql=${escape(
        `select * from doc
        where ([{"defaultIndex": "grams"}]userInput(@input));`
      )}&input=${escape(
        query
      )}&hits=128&ranking=weighted_doc_rank&timeout=5s&locale=en-US`
    )
      .then((res) => res.json())
      .then(handleResults)
      .catch(console.error);
  } else {
    document.getElementById("hits").innerHTML = "";
    result.innerHTML = "";
  }
};

const handleLocationQuery = (event) => {
  const params = Object.fromEntries(
    decodeURIComponent(window.location.search.substring(1))
      .split("&")
      .map((item) => item.split("="))
  );

  if (params["q"]) {
    const query = decodeURI(params["q"]).replace(/\+/g, " ");
    document.getElementById("searchinput").value = query;
    handleQuery(query);
  }
};

window.addEventListener("load", handleLocationQuery);
document.getElementById("searchinput").addEventListener(
  "input",
  debounce((event) => handleQuery(event.target.value))
);
