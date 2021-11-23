
function replace(encodedText) {
    var body_element = document.getElementsByTagName('body')[0];
    var selection = window.getSelection();
    var newdiv = document.createElement('div');
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
    var elements = document.getElementsByClassName("urlunencode");
    var len = elements.length
    for (var i = 0 ; i < len; i++)
    {
        var original = elements[i].innerHTML;
        elements[i].innerHTML = decodeURIComponent(original);
        elements[i].getAttributeNode("oncopy").nodeValue = "replace(\""+original+"\");";
    }

}

document.addEventListener("DOMContentLoaded", init);
