if (window.location.pathname != "/search.html"){
const input = document.getElementById("searchinput");
const inputParent = input.parentElement;
const searchForm = document.getElementById("search-form");
const dropdown = document.createElement("div");
dropdown.className = "dropdown hide";
inputParent.appendChild(dropdown);
input.setAttribute("autocomplete", "off");

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

const hideDropdown = () => {
  dropdown.classList.remove("show");
  dropdown.classList.add("hide");
};

const showDropdown = () => {
  dropdown.classList.add("show");
  dropdown.classList.remove("hide");
};

const handleSuggestClick = (e) => {
  e.preventDefault();
  e.stopPropagation();
  input.value = e.target.innerHTML;
  searchForm.submit.click();
};

const handleUnfocus = (e) => hideDropdown();

const handleResults = (data) => {
  dropdown.innerHTML = "";
  if (data.root.children) {
    const items = data.root.children.map((child) => ({
      value: child.fields.term,
    }));
    items.forEach((item) => {
      const p = document.createElement("p");
      p.innerHTML = item.value;
      p.addEventListener("mousedown", handleSuggestClick);
      dropdown.appendChild(p);
    });
    showDropdown();
    if (document.getElementById("searchinput").value <= 0) {hideDropdown();}
  } else {
    hideDropdown();
  }
};

const handleInput = (e) => {
  if (e.target.value.length > 0) {
    fetch(
      `https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20sources%20term%20where%20term%20contains%20%28%5B%7B%22prefix%22%3Atrue%7D%5D%22${e.target.value.replaceAll(
        /[^a-zA-Z0-9 ]/g,
        ""
      )}%22%29%20and%20%28corpus_count%20>%201%20or%20query_count%20>%201%29%3B&ranking=term_rank`
    )
      .then((res) => res.json())
      .then(handleResults)
      .catch(console.error);
  } else {
    hideDropdown();
  }
};

input.addEventListener("input", debounce(handleInput));
input.addEventListener("focusout", handleUnfocus);
}
