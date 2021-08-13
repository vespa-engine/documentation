const input = document.getElementById("searchinput");
const inputParent = input.parentElement;
const searchForm = document.getElementById("search-form");
const dropdown = document.createElement("div");
dropdown.className = "dropdown hide";
inputParent.appendChild(dropdown);
input.setAttribute("autocomplete", "off");


//predictive shadow text
const suggestText = document.createElement("div");
suggestText.className = "suggestText";
suggestText.id = "textSuggest"
inputParent.appendChild(suggestText);
suggestText.innerHTML="";
//

// https://www.freecodecamp.org/news/javascript-debounce-example/

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

const handleSuggestionResults = (data) => {
  console.log(data);
  suggestText.innerHTML = "";
  dropdown.innerHTML = "";
  if (data.length > 0) {
    const items = data.map((child) => ({
      value: child.fields.term,
    }));
    items.map((item) => {
      const p = document.createElement("p");
      p.innerHTML = item.value;
      p.addEventListener("mousedown", handleSuggestClick);
      dropdown.appendChild(p);
      showDropdown();
    });
    suggestText.innerHTML = items[0].value;
    document.getElementById("searchinput").placeholder = "";
    if (document.getElementById("searchinput").value <= 0) {suggestText.innerHTML = ""; hideDropdown(); document.getElementById("searchinput").placeholder = "Search Documentation";}
  } else {
    hideDropdown();
    suggestText.innerHTML= "";
    document.getElementById("searchinput").placeholder = "Search Documentation";
  }
};


export default handleSuggestionResults;
export {handleUnfocus, hideDropdown};