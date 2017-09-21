---
layout: empty
index: false
---
var tipuesearch = {"pages": [
{% for page in site.pages %}
{% unless page.index == false %}
  {
    "title": {{ page.title | strip_html | normalize_whitespace | jsonify }},
    "text": {{ page.content | strip_html | normalize_whitespace | jsonify }},
    "tags": "",
    "url": "{{site.github.url}}{{ page.url | relative_url }}"
  }{% unless forloop.last %},{% endunless %}
{% endunless %}
{% endfor %}
]};
