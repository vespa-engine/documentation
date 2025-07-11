#!/usr/bin/env python3
# Copyright Vespa.ai. All rights reserved.
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

encoding = tiktoken.encoding_for_model("gpt-4o-mini")
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


def is_selfhosted_doc(doc):
    path = doc['fields']['path']
    if "/en/operations-selfhosted" in path:
        return True
    return False

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
            "base_uri": sys.argv[2],
            "selfhosted": is_selfhosted_doc(doc)
        }
    }

    if header:
        title = fields['title']
        new_title = title + " - " + header
        new_doc["fields"]["title"] = new_title

    if paragraph_id is None:
        paragraph_id = str(random.randint(0,1000))

    new_doc['fields']['path'] = new_doc['fields']['path'] + \
        "#" + paragraph_id.replace("?", "")
    new_doc['put'] = new_doc['put'] + "-" + urllib.parse.quote(paragraph_id)

    return new_doc


def split_text(soup):
    split_tables(soup)
    split_lists(soup)
    md = markdownify(str(soup), heading_style='ATX', code_language_callback=what_language)
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
            header = line.lstrip("#").replace("\\", "")
            id = "-".join(header.replace(',', '').split()).lower()
        else:
            text = text + "\n" + line

    data.append((id, header, text)) #Flush any last data
    return data


def remove_notext_tags(soup):
    for remove_tag in soup.find_all(['style', 'script']):
        remove_tag.decompose()


def split_lists(soup):
    for list in soup.body.find_all(['ul', 'ol']):
        for list_item in list.find_all('li'):
            move_linkable_item_to_single_entity(soup, list_item)


def split_tables(soup):
    top_level_tables = soup.body.find_all('table', recursive=False)  # i.e., do not find rows in tables within tables
    for table in top_level_tables:
        tbody = table.find('tbody')  # tbody is implicit and always there
        for row in tbody.find_all('tr', recursive=False):
            move_linkable_item_to_single_entity(soup, row)


def table_header_row(row):
    thead = row.find_parent('table').find('thead')
    if thead is not None:
        return thead.find('tr')
    return None


def max_cols(tbody):
    max_cols = 0
    if tbody is None:
        return max_cols
    for row in tbody.find_all('tr'):
        cols = len(row.find_all(['th', 'td']))
        if cols > max_cols:
            max_cols = cols
    return max_cols


def add_header_to_tables_if_missing(soup):
    for table in soup.body.find_all('table'):
        thead = table.find('thead')
        if thead is None:
            thead = soup.new_tag('thead')
            table.insert(0, thead)
        header_row = thead.find('tr')
        if header_row is None:
            tr = soup.new_tag('tr')
            thead.append(tr)
            for _ in range(max_cols(table.tbody)):
                tr.append(soup.new_tag('th'))


def move_linkable_item_to_single_entity(soup, item):
    id_elem = item.find('p', {'id': True})
    if id_elem is not None:
        new_h4 = soup.new_tag('h4', id=id_elem['id'])
        new_h4.string = id_elem['id']
        if item.name == 'tr':
            new_container = soup.new_tag('table')
            new_thead = soup.new_tag('thead')
            new_tbody = soup.new_tag('tbody')
            new_container.append(new_thead)
            new_container.append(new_tbody)
            header_row = table_header_row(item)
            if header_row is not None:
                new_thead.append(copy.copy(header_row))
            else:
                dummy_tr = soup.new_tag('tr')
                for _ in item.find_all(['th', 'td']):
                    dummy_tr.append(soup.new_tag('th'))
                new_thead.append(dummy_tr)
            new_tbody.append(item)
            soup.append(new_h4)
            soup.append(new_container)
        else:
            item.name = 'div'  # change <li> to <div> for nicer display
            soup.append(new_h4)
            new_h4.insert_after(item)


def fix_pre_content(soup):
    # Workaround: ensure no faux headings from pre content
    for pre in soup.body.find_all('pre'):
        pre_text = pre.get_text()
        pre.string = re.sub(r'^#', ' #', pre_text, flags=re.MULTILINE)


def main():
    with open(sys.argv[1]) as fp:
        random.seed(42)
        docs = json.load(fp)
        operations = []
        for doc in docs:
            html_doc = doc['fields']['html']
            html_doc = xml_fixup(html_doc)
            soup = BeautifulSoup(html_doc, 'html5lib')
            remove_notext_tags(soup)
            fix_pre_content(soup)
            add_header_to_tables_if_missing(soup)
            data = split_text(soup)

            for paragraph_id, header, paragraph in data:

                paragraph = paragraph.lstrip('\n').lstrip(" ")
                paragraph = paragraph.rstrip('\n')

                paragraph = re.sub(r"\n{2,}", "\n\n", paragraph)

                paragraph = re.sub(r"\n*```", "\n```", paragraph)
                paragraph = re.sub(r"```\n*", "```\n", paragraph)

                paragraph = paragraph.replace("```\njson","```json")
                paragraph = paragraph.replace("```\nxml","```xml")
                paragraph = paragraph.replace("```\nbash","```bash")
                paragraph = paragraph.replace("```\nsh","```sh")
                paragraph = paragraph.replace("```\nraw","```\n")
                paragraph = paragraph.replace("```\njava","```java\n")

                # Necessary backslashes and quotes will be added when json-serialized.
                paragraph = paragraph.replace("\\", "")

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
        else:
            op['fields']['questions'] = [op['fields']['title']]

    with open("paragraph_index.json", "w") as fp:
        json.dump(operations, fp)


if __name__ == "__main__":
    main()
