#! /usr/bin/env python3
# Copyright Vespa.ai. All rights reserved.

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
        for anchor in soup.find_all('a', {"class": "yql-x"}):
            sanitized_query = re.sub('\n', '', anchor.text)
            links.add((filename, 'https://api.search.vespa.ai/search/?yql=' + quote(sanitized_query)))
        for anchor in soup.find_all('a', {"class": "querystring-x"}):
            sanitized_query = re.sub('\n', '', anchor.text)
            links.add((filename, 'https://api.search.vespa.ai/search/?' + quote(sanitized_query, safe='&=')))


def get_links(directory):
    print("Scanning files in {}".format(directory))
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.html'):
                extract_links(os.path.join(root, filename))


def check_total_count(querytuple):
    r = requests.get(querytuple[1])
    d = r.json()
    total_count = d["root"]["fields"]["totalCount"]
    print("{0} results: {1}".format(total_count, querytuple))
    return total_count > 0


def main():
    if len(sys.argv) <= 1:
        sys.exit(("Missing directory argument"))
    directory = sys.argv[1]
    if not os.path.exists(directory):
        sys.exit(("{} does not exist".format(directory)))
    get_links(directory)
    print("Checking queries: {}".format(links))
    for querytuple in links:
        if not check_total_count(querytuple):
            sys.exit("Query failed")


if __name__ == "__main__":
    main()
