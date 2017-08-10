#! /usr/bin/python

import os
import sys
import json
import yaml
import urllib
import subprocess


def find(json, path, separator = "."):
    if len(path) == 0: return json
    head, _, rest = path.partition(separator)
    return find(json[head], rest) if head in json else None


def call(args):
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    return out


def vespa_get(endpoint, operation, options):
    url = "{0}/{1}/?{2}".format(endpoint, operation, "&".join(options))
    return call(["curl", "-gk", url])


def vespa_post(endpoint, operation, file):
    url = "{0}/{1}/".format(endpoint, operation)
    return call([
        "curl",
        "-k",
        "-H", "Content-Type:application/json",
        "-X", "POST",
        "--data-binary", "@{0}".format(file),
        url
    ])


def vespa_visit(endpoint, document_type, continuation = None):
    options = [
        "visit.selection={0}".format(urllib.quote("doc.doctype=\"{0}\"".format(document_type))),
        "format=json",
        "populatehitfields=false",
        "visit.approxMaxDocs=100"
    ]
    if continuation is not None and len(continuation) > 0:
        options.append("visit.continuation={0}".format(continuation))
    response = vespa_get(endpoint, "visit", options)
    return json.loads(response)


def vespa_remove(endpoint, doc_ids):
    options = [ "id[{0}]={1}".format(i, id) for i,id in enumerate(doc_ids) ]
    return vespa_get(endpoint, "remove", options)


def vespa_feed(endpoint, feed):
    return vespa_post(endpoint, "document", feed)


def get_indexed_docids(endpoint, document_type):
    docids = set()
    continuation = ""
    while continuation is not None:
        json = vespa_visit(endpoint, document_type, continuation)
        children = find(json, "root.children")
        if children is not None:
            docids.update([find(child, "id") for child in children])
        continuation = find(json, "root.fields.visitorContinuationToken")
    return docids


def get_feed_docids(feed):
    with open(feed, "r") as f:
        feed_json = json.load(f)
    return set([ find(doc, "put") for doc in feed_json ])


def print_header(msg):
    print("")
    print("*" * 80)
    print("* {0}".format(msg))
    print("*" * 80)


def read_config():
    with open("_config.yml", "r") as f:
        return yaml.load(f)


def main():
    config = read_config()["search"]
    feed = config["feed"]
    endpoint = config["endpoint"]
    doctype = config["doctype"]
    do_remove_index = config["do_index_removal_before_feed"]
    do_feed = config["do_feed"]

    print_header("Retrieving already indexed document ids")
    docids_in_index = get_indexed_docids(endpoint, doctype)
    print("{0} documents found.".format(len(docids_in_index)))

    if do_remove_index:
        print_header("Removing all indexed documents")
        print(vespa_remove(endpoint, docids_in_index))
        print("{0} documents removed.".format(len(docids_in_index)))

    if do_feed:
        print_header("Building feed")
        print call(["jekyll", "build"])
        assert os.path.exists(feed)

        print_header("Parsing feed file for document ids")
        docids_in_feed = get_feed_docids(feed)
        print("{0} documents found.".format(len(docids_in_feed)))

        if len(docids_in_feed) == 0:
            return

        docids_to_remove = docids_in_index.difference(docids_in_feed)
        if len(docids_to_remove) > 0:
            print_header("Removing indexed documents not in feed")
            for id in docids_to_remove:
                print("Removing {0}".format(id))
            print(vespa_remove(endpoint, docids_to_remove))
            print("{0} documents removed.".format(len(docids_to_remove)))

        print_header("Feeding documents")
        print(vespa_feed(endpoint, feed))
        print("{0} documents fed.".format(len(docids_in_feed)))


if __name__ == "__main__":
    main()
