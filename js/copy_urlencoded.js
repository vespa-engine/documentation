
function replace(encodedText) {
    let body_element = document.getElementsByTagName('body')[0];
    let selection = window.getSelection();
    let newdiv = document.createElement('div');
    body_element.appendChild(newdiv);
    newdiv.innerHTML = encodedText;
    newdiv.style.position='absolute';
    newdiv.style.left='-99999px';
    selection.selectAllChildren(newdiv);
    window.setTimeout(function() {
        body_element.removeChild(newdiv);
    },0);
}

function init() {
    let elements = document.getElementsByClassName("urlunencode");
    let len = elements.length
    for (let i = 0 ; i < len; i++)
    {
        let original = elements[i].innerHTML;
        elements[i].innerHTML = decodeURIComponent(original);
        elements[i].getAttributeNode("oncopy").nodeValue = "replace(\""+original+"\");";
    }

}

document.addEventListener("DOMContentLoaded", init);
