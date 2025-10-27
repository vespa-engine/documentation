import handleResults from "./handle_results.js";
import { getHandlerForInput } from "./handle_search_suggestions.js";

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

const encode = (params) => {
  return new URLSearchParams(params)
    .toString()
    .replaceAll('+', '%20'); // CloudFront requires that spaces are encoded as %20
};

// Get the active search input (mobile or desktop)
const getActiveSearchInput = () => {
  const inputs = document.querySelectorAll('.searchinput');
  for (const input of inputs) {
    // Check if input is visible
    if (input.offsetParent !== null) {
      return input;
    }
  }
  // Fallback to first input if none are visible
  return inputs[0];
};

const handleQuery = (query, inputId) => {
  const handler = getHandlerForInput(inputId);
  
  if (query.length > 0) {
    const result = document.getElementById("result");

    document.getElementById("hits").innerHTML = "";
    result.innerHTML = `Searching for '${escapeHtml(query)}' ...`;
    fetch("https://api.search.vespa.ai/search/?" + encode({term: query}))
        .then((res) => res.json())
        .then((res) => { const children = (res.root.children)? res.root.children : [];
          if (handler) {
            handler.handleSuggestionResults(
              children.filter(child => child.fields.sddocname === "doc"),
              children.filter(child => child.fields.sddocname === "term")
            );
          }
          handleResults(children.filter(child => child.fields.sddocname === "doc"), escapeHtml(query))})
        .catch(console.error);
  } else {
    document.getElementById("hits").innerHTML = "";
    result.innerHTML = "";
    if (handler) {
      handler.hideDropdown();
    }
  }
};

const handleLocationQuery = () => {
  const params = new URLSearchParams(window.location.search);

  if (params.has("q")) {
    const query = params.get("q");
    const activeInput = getActiveSearchInput();
    if (activeInput) {
      activeInput.value = query;
    }
    result.innerHTML = `Searching for '${escapeHtml(query)}' ...`;

    const searchParams = {
      yql: 'select * from doc where {grammar: "weakAnd"}userInput(@userinput)',
      hits: 25,
      ranking: 'documentation',
      locale: 'en-US',
      userinput: query,
    };

    fetch("https://api.search.vespa.ai/search/?" + encode(searchParams))
        .then((res) => res.json())
        .then((res) => handleResults(res.root.children, escapeHtml(query)))
  }
};

document.addEventListener("DOMContentLoaded", () => {
  handleLocationQuery();
  
  // Attach event listeners to all search inputs
  const inputs = document.querySelectorAll('.searchinput');
  inputs.forEach(input => {
    input.addEventListener("input", (event) => {
      debounce(handleQuery(event.target.value, event.target.id));
    });

    input.addEventListener("focusout", (event) => {
      const handler = getHandlerForInput(event.target.id);
      if (handler) handler.handleUnfocus(event);
    });

    input.addEventListener("keydown", (event) => {
      const handler = getHandlerForInput(event.target.id);
      if (handler) handler.handleArrowKeys(event);
    });
  });
});
