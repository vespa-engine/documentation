# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
import re

import requests


class MetricReference:
    def __init__(self, filename, title, metric_list):
        self.filename = filename
        self.title = title
        self.metric_list = metric_list

    def metric_html_rows(self):
        return "\n".join([f'\t<tr>\n'
                          f'\t  <td>{metric["name"]}</td>\n'
                          f'\t  <td>{metric["description"]}</td>\n'
                          f'\t  <td>{metric["unit"]}</td>\n'
                          f'\t</tr>' for metric in self.metric_list])

    def as_html(self):
        return f"""---
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
title: "{self.title}"
---


<table class="table">
    <thead>
        <tr><th>Name</th><th>Description</th><th>Unit</th></tr>
    </thead>
    <tbody>
{self.metric_html_rows()}
    </tbody>
</table>
"""


def parse_base_units(content):
    base_unit_dict = {}
    for line in content.split("\n"):
        matcher = re.search(r"\s*([A-Z_]+)\(\"([a-z]+)\"", line)
        if matcher:
            base_unit_dict[matcher.group(1)] = matcher.group(2)
    return base_unit_dict


# Maps unit enum to wanted string representation
def parse_units(content, base_units):
    units = {}
    for line in content.split("\n"):
        # Matches Unit name to base unit and optional per-unit
        matcher = re.search(r"\s*([A-Z_]+)\(BaseUnit\.([A-Z_]+)(, BaseUnit\.([A-Z_]+))?", line)
        if not matcher:
            continue
        if matcher.group(4):
            units[matcher.group(1)] = base_units[matcher.group(2)] + "/" + base_units[matcher.group(4)]
        else:
            units[matcher.group(1)] = base_units[matcher.group(2)]
    return units


def get_units():
    response = requests.get("https://raw.githubusercontent.com/vespa-engine/vespa/master/container-core/src/main/java/com/yahoo/metrics/Unit.java")
    content = response.text
    base_unit_dict = parse_base_units(content)
    return parse_units(content, base_unit_dict)


def parse_metrics(content, units):
    metrics = []
    for line in content.split("\n"):
        metric = {}
        # Matches metric name, unit and description
        matcher = re.search(r".*\(\"(.+)\",\s*Unit\.([A-Z_]+),\s*\"(.*)\"", line)
        if matcher:
            metric["name"] = matcher.group(1)
            metric["unit"] = units[matcher.group(2)]
            metric["description"] = matcher.group(3)
            # No need to document internal metrics
            if "Yahoo! Internal" not in metric["description"]:
                metrics.append(metric)
    return metrics


def get_metrics(metric_type, units):
    response = requests.get(f'https://raw.githubusercontent.com/vespa-engine/vespa/master/container-core/src/main/java/com/yahoo/metrics/{metric_type}Metrics.java')
    return parse_metrics(response.text, units)


def write_reference_doc(metric_reference):
    file = open("en/reference/%s" % metric_reference.filename, "w")
    file.write(metric_reference.as_html())


def generate_doc(metric_type, units):
    filename = metric_type.lower() + "-metrics-reference.html"
    title = metric_type.title() + " Metrics"
    metrics = get_metrics(metric_type, units)
    return MetricReference(filename, title, metrics)

def generate_metrics_doc():
    units = get_units()
    metric_types = [
        "Container",
        "SearchNode",
        "Storage",
        "Distributor",
        "ConfigServer",
        "Logd",
        "NodeAdmin",
        "Slobrok"
    ]
    for metric_type in metric_types:
        reference_doc = generate_doc(metric_type, units)
        write_reference_doc(reference_doc)


generate_metrics_doc()
