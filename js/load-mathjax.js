
window.MathJax = {
    //chtml: {
    //    scale: 0.75,
    //    minScale: .5
    //},
    svg: {  // http://docs.mathjax.org/en/latest/options/output/svg.html
        minScale: .5
    }
};

(function () {
    let script = document.createElement('script');
    //script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
    script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-svg.js';
    script.async = true;
    document.head.appendChild(script);
})();
