#!/usr/bin/env python3
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

import json
import sys
from bs4 import BeautifulSoup
import random

def create_text_doc(doc, paragraph, paragraph_id, header):
    id = doc['put']
    #id:open:doc::open/en/access-logging.html#
    _,namespace,doc_type,_,id = id.split(":")
    #print("n={},doc_type={},id={}".format(namespace,doc_type,id))
   
    new_namespace = namespace + "-p"
    id = id.replace(namespace, new_namespace)
    id = "id:{}:{}::{}".format(new_namespace, "paragraph", id)
    fields = doc['fields']
    new_doc = {
        "put": id,
        "fields": {
            "title": fields['title'],
            "path": fields['path'],
            "doc_id": fields['path'],
            "namespace": new_namespace,
            "content": paragraph
        }
    }
    
    if header:
        title = fields['title']
        new_title = title + " - " + header
        new_doc["fields"]["title"] = new_title

    if paragraph_id is None:
        paragraph_id = str(random.randint(0,1000))

    new_doc['fields']['path'] = new_doc['fields']['path'] + "#" + paragraph_id
    new_doc['put'] = new_doc['put'] + "#" + paragraph_id
    
    return new_doc 


with open(sys.argv[1]) as fp:
    random.seed(42)
    docs = json.load(fp)
    operations = []
    for doc in docs:
        #if doc['fields']['path'] != "/en/reference/schema-reference.html":
        #    continue
        html_doc = doc['fields']['html']
        soup = BeautifulSoup(html_doc, 'html5lib')
        texts = []
        current_text = ""
        current_id = None
        current_header = ""
        first = True
        for element in soup.descendants:
            if element.name in ["h1", "h2", "h3", "h4"]:
                if current_text:
                    if first and current_id == None:
                        current_id = ""
                        first = False
                    texts.append((current_text.strip(), current_id, current_header))
                    current_text = element.get_text().strip() + " - "
                    current_id = None
                current_id = element.attrs.get("id")
                current_header = element.get_text()   
                if current_id == None:
                    print("Missing header id {} {}".format(doc['fields']['path'], current_header))
                       
            else:
                if element.get_text() and element.name in ["p", "td", "th"]:
                    current_text = current_text + " " + element.get_text().strip().replace("\n"," ")
                    current_text = current_text.strip()
    
        if current_text:
            texts.append((current_text.strip(), current_id, current_header))
        
        for text, index, header in texts:
            cleaner_text = " ".join(text.split())
            operations.append(create_text_doc(doc, cleaner_text, index, header))
    with open("paragraph_index.json", "w") as fp:    
        json.dump(operations, fp)
