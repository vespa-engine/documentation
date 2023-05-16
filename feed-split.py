#!/usr/bin/env python3
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
import copy
import json
import sys
from bs4 import BeautifulSoup
from markdownify import markdownify
import random
import re
from xml.sax.saxutils import escape
import tiktoken
import urllib.parse

encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
note_pattern = re.compile(r"{%\s*include.*?%}", flags=re.DOTALL)
highlight_pattern = re.compile(r"{%\s*.*?\s%}", flags=re.DOTALL)


def what_language(el):
    z = re.match(r"{%\s*highlight\s*(\w+)\s%}", el.text)
    if z:
        lang =  z.group(1)
        return lang
    if el.text.find("curl") > 0:
        return "bash"
    if el.text.find("import com.yahoo") > 0:
        return "java"
    return ""

def remove_jekyll(text):
    text = note_pattern.sub("", text)
    text = highlight_pattern.sub("", text)
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
    id = "id:{}:{}::{}".format(new_namespace, "paragraph", id)
    fields = doc['fields']
    n_tokens = len(encoding.encode(paragraph))
    new_doc = {
        "put": id,
        "fields": {
            "title": fields['title'],
            "path": fields['path'],
            "doc_id": fields['path'],
            "namespace": new_namespace,
            "content": paragraph,
            "content_tokens": n_tokens,
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
    new_doc['put'] = new_doc['put'] + "-" + urllib.parse.quote(paragraph_id)
    
    return new_doc


def split_text(htmldoc):
    md = markdownify(split_tables(htmldoc), heading_style='ATX', code_language_callback=what_language)
    lines = md.split("\n")
    header = ""
    text = ""
    id = ""
    data = []
    for line in lines:
        if line.startswith("#"):
            if text:
                data.append((id, header, text))
                text = ""
            header = line.lstrip("#")
            id = "-".join(header.split()).lower()
        else:
            text = text + "\n" + line

    data.append((id, header, text)) #Flush any last data
    return data


def split_tables(htmldoc):
    soup = BeautifulSoup(htmldoc, 'html5lib')

    # Only consider tables on top-level - i.e., do not find rows in tables within tables
    top_level_tables = soup.body.find_all('table', recursive=False)
    for table in top_level_tables:
        header_row = None
        thead = table.find_all('thead', recursive=False)
        if len(thead):
            header_rows = thead[0].find_all('tr', recursive=False)
            if len(header_rows):
                header_row = header_rows[0]
        tbody = table.find_all('tbody', recursive=False)
        rows = tbody[0].find_all('tr', recursive=False)
        for row in rows:
            # Use soup as parent, append at end, as there are nested tables and H within table is no good here
            move_row_to_new_table_if_has_id(soup, header_row, row)
    return str(soup)


def move_row_to_new_table_if_has_id(soup, header_row, row):
    id_elem = row.find_all('p', {'id': True})
    if len(id_elem):
        new_h4 = soup.new_tag('h4', id=id_elem[0]['id'])
        new_h4.string = id_elem[0]['id']
        new_table = soup.new_tag('table')
        new_table.insert(0, row)
        if header_row:
            new_table.insert(0, copy.copy(header_row))
        soup.append(new_h4)
        soup.append(new_table)


def main():
    with open(sys.argv[1]) as fp:
        random.seed(42)
        docs = json.load(fp)
        operations = []
        for doc in docs:
            html_doc = doc['fields']['html']
            html_doc = xml_fixup(html_doc)
            data = split_text(html_doc)

            for paragraph_id, header, paragraph in data:

                paragraph = paragraph.lstrip('\n').lstrip(" ")
                paragraph = paragraph.rstrip('\n')

                paragraph = re.sub(r"\n*```", "\n```", paragraph)
                paragraph = re.sub(r"```\n*", "```\n", paragraph)

                paragraph = paragraph.replace("```\njson","```json")
                paragraph = paragraph.replace("```\nxml","```xml")
                paragraph = paragraph.replace("```\nbash","```bash")
                paragraph = paragraph.replace("```\nsh","```sh")
                paragraph = paragraph.replace("```\nraw","```\n")
                paragraph = paragraph.replace("```\njava","```java\n")

                paragraph = remove_jekyll(paragraph)

                if paragraph:
                    paragraph_doc = create_text_doc(doc, paragraph, paragraph_id, header)
                    operations.append(paragraph_doc)

    #Merge question expansion
    questions_expansion = dict()
    with open(sys.argv[3]) as fp:
        for line in fp:
            op = json.loads(line)
            id = op['update']
            fields = op['fields']
            if "questions" in fields:
                questions = fields['questions']['assign']
                questions_expansion[id] = questions
    for op in operations:
        id = op['put']
        if id in questions_expansion:
            op['fields']['questions'] = questions_expansion[id]

    with open("paragraph_index.json", "w") as fp:
        json.dump(operations, fp)


if __name__ == "__main__":
    main()
