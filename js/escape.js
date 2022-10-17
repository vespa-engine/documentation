

// https://github.com/janl/mustache.js/blob/550d1da9e3f322649d04b4795f5356914f6fd7e8/mustache.js#L71
const escapeHtml = (string) => {
  const escapeMap = Object.freeze({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D;'
  });
  return String(string).replace(/[&<>"'`=\/]/g, (s) => escapeMap[s]);
}


const unescapeHtml = (string) => {
  const unescapeMap = Object.freeze({
    '&amp;' : '&',
    '&lt;'  : '<',
    '&gt;'  : '>',
    '&quot;': '"',
    '&#39;' : "'",
    '&#x2F;': '/',
    '&#x60;': '`',
    '&#x3D;': '='
  });
  return String(string)
    .replace(/&amp;|&lt;|&gt;|&quot;|&#39;|&#x2F;|&#x60;|&#x3D;/g, (s) => unescapeMap[s]);
}

export default escapeHtml;
export default unescapeHtml;
