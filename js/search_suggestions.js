import { getHandlerForInput } from "./handle_search_suggestions.js"; 

if (window.location.pathname != "/search.html"){

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
    .replaceAll('+', '%20'); // seems like CloudFront requires that spaces are encoded as %20 
};

const handleInput = (e) => {
  const handler = getHandlerForInput(e.target.id);
  if (!handler) return;

  if (e.target.value.length > 0) {
    // Sanitize input for search (remove special characters)
    const sanitizedInput = e.target.value.replaceAll(/[^a-zA-Z0-9 ]/g, "");
    
    // First fetch: Document suggestions using YQL
    const docSearchParams = {
      yql: 'select * from doc where grams contains (@userinput)',
      hits: 5,
      ranking: 'weighted_doc_rank',
      locale: 'en-US',
      userinput: sanitizedInput,
    };
    
    const docFetch = fetch(
      `https://api.search.vespa.ai/search/?${encode(docSearchParams)}`
    ).then((res) => res.json());

    // Second fetch: Term suggestions (prefix matching)
    const termSearchParams = {
      yql: `select * from sources term where default contains ([{"prefix":true}]"${sanitizedInput}")`,
      ranking: 'term_rank',
      hits: 5,
    };
    
    const termFetch = fetch(
      `https://api.search.vespa.ai/search/?${encode(termSearchParams)}`
    ).then((res) => res.json());

    // Wait for both fetches
    Promise.all([docFetch, termFetch])
      .then(([docRes, termRes]) => {
        const docChildren = (docRes.root.children) ? docRes.root.children : [];
        const termChildren = (termRes.root.children) ? termRes.root.children : [];
        handler.handleSuggestionResults(docChildren, termChildren);
      })
      .catch(console.error);
  } else {
    handler.hideDropdown();
  }
};

// Initialize all search inputs
document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll('.searchinput');
  inputs.forEach(input => {
    input.addEventListener("input", debounce(handleInput));
    input.addEventListener("focusout", (e) => {
      const handler = getHandlerForInput(e.target.id);
      if (handler) handler.handleUnfocus(e);
    });
    input.addEventListener("keydown", (e) => {
      const handler = getHandlerForInput(e.target.id);
      if (handler) handler.handleArrowKeys(e);
    });
  });
});

}
