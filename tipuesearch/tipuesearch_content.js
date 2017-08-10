---
layout: empty
---
var tipuesearch = {"pages": [
{% for page in site.pages %}
  {
    "title": {{ page.title | strip_html | normalize_whitespace | jsonify }},
    "text": {{ page.content | strip_html | normalize_whitespace | jsonify }},
    "tags": "",
    "url": "{{site.github.url}}{{ page.url | relative_url }}"
  }{% unless forloop.last %},{% endunless %}
{% endfor %}
]};
