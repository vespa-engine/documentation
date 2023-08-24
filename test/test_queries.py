#! /usr/bin/env python3
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

import os
import sys
import re
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

links = set()


def extract_links(filename):
    with open(filename) as fp:
        soup = BeautifulSoup(fp, 'html.parser')
        for anchor in soup.find_all('a', {"class": "docsearch-x"}):
            sanitized_query = re.sub('\n', '', anchor.text)
            links.add('https://api.search.vespa.ai/search/?yql=' + quote(sanitized_query))
        for anchor in soup.find_all('a', {"class": "cord19-x"}):
            sanitized_query = re.sub('\n', '', anchor.text)
            links.add('https://api.cord19.vespa.ai/search/?yql=' + quote(sanitized_query))


def get_links(directory):
    print("Scanning files in {}".format(directory))
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.html'):
                extract_links(os.path.join(root, filename))


def check_total_count(query):
    r = requests.get(query)
    d = r.json()
    total_count = d["root"]["fields"]["totalCount"]
    print("{0} results for {1}".format(total_count, query))
    return total_count > 0


def main():
    if len(sys.argv) <= 1:
        sys.exit(("Missing directory argument"))
    directory = sys.argv[1]
    if not os.path.exists(directory):
        sys.exit(("{} does not exist".format(directory)))
    get_links(directory)
    print("Checking queries: {}".format(links))
    for query in links:
        if not check_total_count(query):
            sys.exit("Query failed")


if __name__ == "__main__":
    main()
