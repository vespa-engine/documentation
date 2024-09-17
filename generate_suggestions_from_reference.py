#!/usr/bin/env python3
# Copyright Vespa.ai. All rights reserved.

from bs4 import BeautifulSoup
import sys
import json
import mmh3

def extract_links_from_html(html_file):
    with open(html_file, 'r') as file:
        soup = BeautifulSoup(file, 'html.parser')

    links = []
    pre_tags = soup.find_all('pre', class_='pre-config')
    for pre_tag in pre_tags:
        a_tags = pre_tag.find_all('a')
        for a_tag in a_tags:
            link_text = a_tag.get_text()
            link = a_tag['href']
            links.append((link_text, link))

    return links

# Example usage:
html_file = sys.argv[1]
url_prefix = sys.argv[2]
namespace = sys.argv[3]
part = html_file.split("/")[-1]
part = part.replace(".html","")
prefix = "/".join(html_file.split("/")[:-1])

result = extract_links_from_html(html_file)
for link_text, link in result:
    if not link_text:
        continue
    if link_text.find("DEPRECATED") > 0:
        continue
    if link.startswith("#"):
        url = url_prefix + html_file + link 
    else: 
        url = url_prefix + prefix + '/' + link 
    id = id = mmh3.hash(url)
    term = {
        'put': 'id:term-reference:term::%i' % id,
            'fields': {
                'term': link_text,
                'namespace': namespace,
                'hash': id,
                'type': "reference:" + part,
                'url': url,
                "corpus_count": 2,
                "document_count": 2
            }
    }
    print(json.dumps(term))

