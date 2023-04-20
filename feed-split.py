#!/usr/bin/env python3
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

import json
import sys
from bs4 import BeautifulSoup
from markdownify import markdownify
import random
import re
from xml.sax.saxutils import escape

note_pattern = re.compile(r"\{%\s*include\s*note\.html\s*content='(?:[^']|'[^']*')*'\s*%\}")
note_pattern2 = re.compile(r"\{%\s*include\s*note\.html\s*content='.*?'\s*%\}")
note_pattern3 = re.compile(r"\{%\s*include\s*query\.html\s*content='.*?'\s*%\}")
important_pattern = re.compile(r"\{%\s*include\s*important\.html\s*content='(?:[^']|'[^']*')*'\s*%\}")
important_pattern2 = re.compile(r"\{%\s*include\s*important\.html\s*content='.*?'\s*%\}")

def what_language(el):
    z = re.match("\{\% highlight (\w+) \%\}", el.text)
    if z:
        return z.group(1)
    if el.text.find("curl") > 0:
        return "bash"

    return ""

def remove_jekyll(text):
    text = text.replace("\{\% highlight (\w+) \%\}","")
    text =re.sub("\{\% highlight .* \%\}", "", text)
    text = text.replace("{% endhighlight %}","")
    return text

def xml_fixup(text):
    regex = r"{%\s*highlight xml\s*%}(.*?){%\s*endhighlight\s*%}"
    matches = re.findall(regex, text, re.DOTALL)
    for match in matches:
        escaped_match = escape(match)
        text = text.replace(match,escaped_match)
    return text

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
            "content": paragraph,
            "base_uri": sys.argv[2]
        }
    }
    
    if header:
        title = fields['title']
        new_title = title + " - " + header
        new_doc["fields"]["title"] = new_title

    if paragraph_id is None:
        paragraph_id = str(random.randint(0,1000))

    new_doc['fields']['path'] = new_doc['fields']['path'] + "#" + paragraph_id
    new_doc['put'] = new_doc['put'] + "-" + paragraph_id
    
    return new_doc 


with open(sys.argv[1]) as fp:
    random.seed(42)
    docs = json.load(fp)
    operations = []
    for doc in docs:
        #if doc['fields']['path'] != "/en/reference/schema-reference.html":
        #    continue
        html_doc = doc['fields']['html']
        html_doc = xml_fixup(html_doc)
        soup = BeautifulSoup(html_doc, 'html5lib')
        md = markdownify(html_doc,heading_style='ATX', code_language_callback=what_language)
        lines = md.split("\n")
        headers = []
        header = ""
        text = ""
        id = ""
        data = []
        for line in lines:
            if line.startswith("#"):
                if text:
                    data.append((id,header, text))
                    text = ""
                header = line.lstrip("#")
                id = "-".join(header.split()).lower()
            else:
                text = text + remove_jekyll(line) + "\n"
        data.append((id,header, text))
        for paragraph_id, header, paragraph in data:
            paragraph = note_pattern.sub("", paragraph)
            paragraph = note_pattern2.sub("", paragraph)
            paragraph = note_pattern3.sub("", paragraph)
            paragraph = important_pattern.sub("",paragraph)
            paragraph = important_pattern2.sub("",paragraph)
            paragraph_doc = create_text_doc(doc, paragraph, paragraph_id, header)
            operations.append(paragraph_doc)
            
    with open("paragraph_index.json", "w") as fp:    
        json.dump(operations, fp)
