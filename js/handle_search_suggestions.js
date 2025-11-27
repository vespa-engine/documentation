// Function to create and manage search suggestions for a specific input
const createSearchSuggestionHandler = (input) => {
  const inputParent = input.parentElement;
  const searchForm = input.closest('.search-form');
  const dropdown = document.createElement("div");
  dropdown.className = "dropdown hide";
  inputParent.appendChild(dropdown);
  input.setAttribute("autocomplete", "off");

  const getNextSibling = (node) => {
    let sibling = node.nextSibling;
    // Skip separator elements
    while (sibling && sibling.tagName === 'HR') {
      sibling = sibling.nextSibling;
    }
    return sibling;
  }

  const getPreviousSibling = (node) => {
    let sibling = node.previousSibling;
    // Skip separator elements
    while (sibling && sibling.tagName === 'HR') {
      sibling = sibling.previousSibling;
    }
    return sibling;
  }
  
  const getValueFromElement = (element) => {
    // For term suggestions, use the data-term attribute (without emoji)
    if (element.hasAttribute('data-term')) {
      return element.getAttribute('data-term');
    }
    // For document suggestions, use the title (without emoji)
    if (element.hasAttribute('data-path')) {
      return element.innerHTML.replace('📃 ', '');
    }
    return element.innerHTML;
  }

  //arrow-key logic
  let dropdownShow = false;
  let firstArrow = false;
  const selectedID = `selectedDropdownElement-${input.id}`;
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
          input.value = getValueFromElement(newSelected);
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
          input.value = getValueFromElement(newSelected);
        } else {
          firstArrow = true;
          input.value = writtenInput;
        }
      } else if (event.key === "Enter" && !firstArrow) {
        // If a document suggestion is selected, navigate to it
        selected = document.getElementById(selectedID);
        if (selected && selected.hasAttribute('data-path')) {
          event.preventDefault();
          window.location.href = selected.getAttribute('data-path');
        }
        // Otherwise let the form submit normally for term suggestions
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
    input.value = e.target.getAttribute('data-term') || e.target.innerHTML;
    const submitButton = searchForm.querySelector('.search-submit');
    if (submitButton) {
      submitButton.click();
    }
  };

  const handleUnfocus = (e) => hideDropdown();

  const handleDocClick = (e, path) => {
    e.preventDefault();
    e.stopPropagation();
    window.location.href = path;
  };

  const handleSuggestionResults = (docData, termData) => {
    firstArrow = true;
    dropdown.innerHTML = "";
    
    const hasDocResults = docData && docData.length > 0;
    const hasTermResults = termData && termData.length > 0;
    
    if (hasDocResults || hasTermResults) {
      // Add document results
      if (hasDocResults) {
        docData.forEach((child) => {
          const p = document.createElement("p");
          p.className = "suggestion-doc";
          p.innerHTML = `📃 ${child.fields.title}`;
          p.setAttribute("data-path", child.fields.path);
          p.addEventListener("mousedown", (e) => handleDocClick(e, child.fields.path));
          dropdown.appendChild(p);
        });
      }
      
      // Add separator if both types exist
      if (hasDocResults && hasTermResults) {
        const separator = document.createElement("hr");
        separator.className = "suggestion-separator";
        dropdown.appendChild(separator);
      }
      
      // Add term results
      if (hasTermResults) {
        termData.forEach((child) => {
          const p = document.createElement("p");
          p.className = "suggestion-term";
          p.innerHTML = `🔍 ${child.fields.term}`;
          p.setAttribute("data-term", child.fields.term);
          p.addEventListener("mousedown", handleSuggestClick);
          dropdown.appendChild(p);
        });
      }
      
      showDropdown();
      if (input.value.length <= 0) { hideDropdown();}
    } else {
      hideDropdown();
    }
  };

  return {
    handleSuggestionResults,
    handleUnfocus,
    hideDropdown,
    handleArrowKeys
  };
};

// Initialize handlers for all search inputs
const handlers = new Map();

document.addEventListener("DOMContentLoaded", () => {
  const inputs = document.querySelectorAll('.searchinput');
  inputs.forEach(input => {
    const handler = createSearchSuggestionHandler(input);
    handlers.set(input.id, handler);
  });
});

// Export a function that finds the right handler for the current input
const getHandlerForInput = (inputId) => {
  return handlers.get(inputId);
};

export { getHandlerForInput };
