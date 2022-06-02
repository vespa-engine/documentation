
function copyPreContent(button) {
    // Assume a pre after the copy button
    let elem = button;
    button.classList.add("d-tooltip-top");
    button.setAttribute("data-tooltip", "copied!");
    setTimeout(() => button.classList.remove("d-tooltip-top"), 800);
    setTimeout(() => button.removeAttribute("data-tooltip"), 800);
    while (elem = elem.nextSibling) {
        if ( elem.nodeType !== Node.TEXT_NODE) {
            if (elem.nodeName === "PRE") {
                copyToClipboard(removePrompt(elem.innerText).trim());
            }
        }
    }
}

function removePrompt(text) {
    return text.replace(/^\$\s*/gm, "");
}

function copyToClipboard(text) {
    // thanks to https://stackoverflow.com/questions/400212/how-do-i-copy-to-the-clipboard-in-javascript
    if (!navigator.clipboard) {
        alert("Copy button not supported in this browser version")
        return;
    }
    navigator.clipboard.writeText(text).then(function() {
        console.log('Async: Copying to clipboard was successful!');
    }, function(err) {
        console.error('Async: Could not copy text: ', err);
    });
}
