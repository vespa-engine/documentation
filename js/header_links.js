// Copyright Vespa.ai. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

function generateHeaderLinks() {
  for (const tag of ["h2", "h3", "h4"]) {
    let headings = document.getElementsByTagName(tag);
    for (const heading of headings) {
      addLink(heading)
    }
  }
}

function addLink(heading) {
  if (heading.id === null || heading.id.trim() === "") {return;}  // Consider auto-generate the id is empty
  let i = document.createElement("i");
  i.classList.add("d-icon", "d-link");
  i.style.color = "#303030";  // same as heading
  let a = document.createElement("a");
  a.setAttribute("href", "#" + heading.id);
  a.classList.add("a-hidden");
  a.appendChild(i);
  heading.appendChild(a);
}

document.addEventListener("DOMContentLoaded", generateHeaderLinks);
