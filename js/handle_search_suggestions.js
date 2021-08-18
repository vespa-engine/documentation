const input = document.getElementById("searchinput");
const inputParent = input.parentElement;
const searchForm = document.getElementById("search-form");
const dropdown = document.createElement("div");
dropdown.className = "dropdown hide";
inputParent.appendChild(dropdown);
input.setAttribute("autocomplete", "off");

const getNextSibling = (node) => {
  if (node.nextSibling) {
    return node.nextSibling;
  }
  return null;
}

const getPreviousSibling = (node) => {
  if (node.previousSibling) {
    return node.previousSibling
  }
  return null;
}

//arrow-key logic
let dropdownShow = false;
let firstArrow = false;
const selectedID = "selectedDropdownElement";
let writtenInput = "";

const handleArrowKeys = (event) => {
  if (dropdownShow){ 
    let newSelected;
    let selected;
    if (event.key === "ArrowDown" && event.target.value) {
      event.preventDefault();
      if (firstArrow) {
        writtenInput = input.value;
        newSelected = dropdown.firstChild;
        firstArrow = false;
      } else {
        selected = document.getElementById(selectedID);
        selected.id = "";
        newSelected = getNextSibling(selected);
      }
      if (newSelected) {
        newSelected.id = selectedID;
        input.value = newSelected.innerHTML;
      } else {
        firstArrow = true;
        input.value = writtenInput;
      }
    } else if (event.key === "ArrowUp" && event.target.value){
      event.preventDefault();
      if (firstArrow) {
        writtenInput = input.value;
        newSelected = dropdown.lastChild;
        firstArrow = false;
      } else {
        selected = document.getElementById(selectedID);
        selected.id = "";
        newSelected = getPreviousSibling(selected);
      }
      if (newSelected) {
        newSelected.id = selectedID;
        input.value = newSelected.innerHTML;
      } else {
        firstArrow = true;
        input.value = writtenInput;
      }
    }
  }
}


const hideDropdown = () => {
  dropdown.classList.remove("show");
  dropdown.classList.add("hide");
  dropdownShow = false;
};

const showDropdown = () => {
  dropdown.classList.add("show");
  dropdown.classList.remove("hide");
  dropdownShow = true;
};

const handleSuggestClick = (e) => {
  e.preventDefault();
  e.stopPropagation();
  input.value = e.target.innerHTML;
  searchForm.submit.click();
};

const handleUnfocus = (e) => hideDropdown();

const handleSuggestionResults = (data) => {
  firstArrow = true;
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
    });
    showDropdown();
    if (document.getElementById("searchinput").value <= 0) { hideDropdown();}
  } else {
    hideDropdown();
  }
};

export default handleSuggestionResults;
export {handleUnfocus, hideDropdown, handleArrowKeys};