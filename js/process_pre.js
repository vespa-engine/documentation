
function processFilePREs() {
    const tags = document.getElementsByTagName("pre");

    // copy elements, because the list above is mutated by the insert html below
    let elems = [];
    for (let i = 0; i < tags.length; i++) {
        elems.push(tags[i]);
    }

    for (let i = 0; i < elems.length; i++) {
        let elem = elems[i];
        if (elem.getAttribute("data-test") === "file") {
            let html = elem.innerHTML;
            //elem.innerHTML = html.replace(/<!--\?/g, "<?").replace(/\?-->/g, "?>").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            elem.insertAdjacentHTML("afterend", "<div class=\"filepath\">Write to file: " + elem.getAttribute("data-path") + "</div>");
        }
    }
};

document.addEventListener("DOMContentLoaded", processFilePREs);
