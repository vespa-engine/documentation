const input = document.getElementById("searchinput");
const inputParent = input.parentElement;
const dropdown = document.createElement("div");
inputParent.appendChild(dropdown);

// https://www.freecodecamp.org/news/javascript-debounce-example/
const debounce = (func, timeout = 300) => {
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

const handleSuggestClick = (e) => {
  e.preventDefault();
  e.stopPropagation();
  input.value = e.target.innerHTML;
};

const handleUnfocus = (e) => hideDropdown();

const handleResults = (data) => {
	console.log(data);

  if (data.root.children[0].children) {
    const items = data.root.children[0].children[0].children
      .map(child => ({
        value: (child.value)
      }));

    items.map(item => {
      const p = document.createElement("p");
      p.innerHTML = item.value;
      p.addEventListener("mousedown", handleSuggestClick);
      dropdown.appendChild(p)
    });
    
  }
};

const handleInput = (e) => {
  dropdown.innerHTML = "";
  if (e.target.value.length > 0) {
    dropdown.classList.add("show");
    dropdown.classList.remove("hide");

    fetch(
      `https://doc-search.vespa.oath.cloud/search/?yql=select%20*%20from%20sources%20query%20where%20default%20contains%20%28%5B%7B%22prefix%22%3Atrue%7D%5D%22${e.target.value.replaceAll(
        /[^a-zA-Z0-9 ]/g,
        ""
      )}%22%29%20%7C%20all%28group%28input%29%20max%2810%29%20order%28-avg%28relevance%28%29%29%20*%20count%28%29%29%20each%28max%281%29%29%29%3B`,
      {
        mode: "cors",
        referrerPolicy: "origin",
      }
    )
      .then((res) => {
        console.log(res);
        return res.json();
      })
      .then((data) => handleResults(data))
      .catch((e) => console.error(e));
  } else {
    hideDropdown();
  }
};

input.addEventListener("input", debounce(handleInput));
input.addEventListener("focusout", handleUnfocus);
