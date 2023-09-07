# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
import re

import requests
from collections import namedtuple
from itertools import groupby


class MetricSetReference:
    def __init__(self, filename, title, metric_list):
        self.filename = filename
        self.title = title
        self.metric_list = metric_list
        self.is_metric_set_reference = any('suffixes' in metric for metric in self.metric_list)

    def suffix_column(self, metric):
        return f'\t  <td>{metric["suffixes"]}</td>\n' if self.is_metric_set_reference else ''

    def metric_html_rows(self, metrics):
        return "\n".join([f'\t<tr>\n'
                          f'\t  <td><p id="{metric["name"].replace(".", "_")}">{metric["name"]}</p></td>\n'
                          f'\t  <td>{metric["description"]}</td>\n'
                          f'\t  <td>{metric["unit"]}</td>\n'
                          f'\t  <td>{metric["suffixes"]}</td>\n'
                          f'\t</tr>' for metric in metrics])

    def metric_html_columns(self):
        optional_suffix_column = "<th>Suffixes</th>" if self.is_metric_set_reference else ""
        return "<th>Name</th><th>Description</th><th>Unit</th>" + optional_suffix_column

    def metric_tables(self):
        key = lambda x: x["metric_type"]
        sorted_metrics = sorted(self.metric_list, key=key)
        return "\n".join([f'<h2 id="{metric_type.lower()}-metrics">{metric_type.title()} Metrics</h2>\n'
                          f'<table class="table">\n'
                          f'    <thead>\n'
                          f'        <tr><th>Name</th><th>Description</th><th>Unit</th><th>Suffixes</th></tr>\n'
                          f'    </thead>\n'
                          f'    <tbody>\n'
                          f'{self.metric_html_rows(metrics)}\n'
                          f'    </tbody>\n'
                          f'</table>\n' for metric_type, metrics in groupby(sorted_metrics, key=key)])

    def as_html(self):
        return (f'---\n'
                f'# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.\n'
                f'title: "{self.title}"\n'
                f'---\n\n\n'
                f'{self.metric_tables()}')


class MetricReference:
    def __init__(self, filename, title, metric_list):
        self.filename = filename
        self.title = title
        self.metric_list = metric_list

    def metric_html_rows(self):
        return "\n".join([f'\t<tr>\n'
                          f'\t  <td><p id="{metric["name"].replace(".", "_")}">{metric["name"]}</p></td>\n'
                          f'\t  <td>{metric["description"]}</td>\n'
                          f'\t  <td>{metric["unit"]}</td>\n'
                          f'\t</tr>' for metric in self.metric_list])

    def as_html(self):
        return (f'---\n'
                f'# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.\n'
                f'title: "{self.title}"\n'
                f'---\n\n\n'
                f'<table class="table">\n'
                f'    <thead>\n'
                f'        <tr><th>Name</th><th>Description</th><th>Unit</th></tr>\n'
                f'    </thead>\n'
                f'    <tbody>\n'
                f'{self.metric_html_rows()}\n'
                f'    </tbody>\n'
                f'</table>\n')


class UnitReference:
    def __init__(self, filename, title, units):
        self.filename = filename
        self.title = title
        self.units = units

    def unit_html_rows(self):
        return "\n".join([f'\t<tr>\n'
                          f'\t  <td>{unit.name}</td>\n'
                          f'\t  <td>{unit.description}</td>\n'
                          f'\t</tr>' for unit in self.units])

    def as_html(self):
        return (f'---\n'
                f'# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.\n'
                f'title: "{self.title}"\n'
                f'---\n\n\n'
                f'<table class="table">\n'
                f'    <thead>\n'
                f'        <tr><th>Unit</th><th>Description</th></tr>\n'
                f'    </thead>\n'
                f'    <tbody>\n'
                f'{self.unit_html_rows()}\n'
                f'    </tbody>\n'
                f'</table>\n')


def parse_base_units(content):
    base_unit_dict = {}
    for line in content.split("\n"):
        matcher = re.search(r"\s*([a-zA-Z_]+)\(\"([a-z0-9 ]+)\"", line)
        if matcher:
            base_unit_dict[matcher.group(1)] = matcher.group(2)
    return base_unit_dict


# Maps unit enum to wanted string representation
def parse_units(content, base_units):
    units = {}
    Unit = namedtuple("Unit", "name description")
    for line in content.split("\n"):
        # Matches Unit name to base unit and optional per-unit
        matcher = re.search(r"\s*([A-Z_]+)\(BaseUnit\.([A-Z_]+)(, BaseUnit\.([A-Z_]+))?,\s*\"(.*)\"\)[,;]", line)
        if not matcher:
            continue
        description = matcher.group(5).replace('\\', '')
        if matcher.group(4):
            name = base_units[matcher.group(2)] + "/" + base_units[matcher.group(4)]
        else:
            name = base_units[matcher.group(2)]
        units[matcher.group(1)] = Unit(name, description)
    return units


def get_units():
    response = requests.get(
        "https://raw.githubusercontent.com/vespa-engine/vespa/master/metrics/src/main/java/ai/vespa/metrics/Unit.java")
    content = response.text
    base_unit_dict = parse_base_units(content)
    return parse_units(content, base_unit_dict)


def get_suffix_names():
    response = requests.get(
        "https://raw.githubusercontent.com/vespa-engine/vespa/master/metrics/src/main/java/ai/vespa/metrics/Suffix.java")
    return parse_base_units(response.text)


def parse_metrics(content, units, metric_type):
    metrics = []
    for line in content.split("\n"):
        metric = {}
        # Matches metric name, unit and description
        matcher = re.search(r"\s*([A-Z0-9_]+)\(\"(.+)\",\s*Unit\.([A-Z_]+),\s*\"(.*)\"", line)
        if matcher:
            metric["enum"] = matcher.group(1)
            metric["name"] = matcher.group(2)
            metric["unit"] = units[matcher.group(3)].name
            metric["description"] = matcher.group(4).replace('\\', '')
            metric["metric_type"] = metric_type
            metrics.append(metric)
    return metrics


def get_suffixes(optional_suffix, suffix_set, suffix_names):
    suffix_regex = lambda x: re.sub("[^a-zA-Z0-9_]+", '', x)
    if optional_suffix:
        suffix = suffix_regex(optional_suffix)
        return "N/A" if suffix == 'baseName' else suffix_names[suffix]
    return ", ".join([suffix_names[suffix_regex(suf)] for suf in suffix_set.split(",")])


def parse_metric_set(content, all_metrics, suffix_names):
    metrics = []
    for line in content.split("\n"):
        matcher = re.search(
            r".*\(.*Metrics\.(?P<name>[A-Z0-9_]+)(\.(?P<optional_suffix>[a-zA-Z_]+))?,*.(EnumSet.of\(("
            r"?P<suffix_set>.*)\)\))?",
            line)

        if not matcher:
            continue
        name = matcher.group("name")
        suffix_set = matcher.group("suffix_set")
        optional_suffix = matcher.group("optional_suffix")
        m = next((m1 for m1 in all_metrics if m1["enum"] == name), None)
        # Skip if no match, we probably haven't documented the metric - I.e. an internal metric
        if not m:
            continue
        metric = {"name": m["name"], "suffixes": get_suffixes(optional_suffix, suffix_set, suffix_names),
                  "unit": m["unit"], 'description': m['description'], 'metric_type': m['metric_type']}
        metrics.append(metric)

    return metrics


def get_metrics(metric_type, units):
    response = requests.get(
        f'https://raw.githubusercontent.com/vespa-engine/vespa/master/metrics/src/main/java/ai/vespa/metrics/{metric_type}Metrics.java')
    return parse_metrics(response.text, units, metric_type)


def write_reference_doc(metric_reference):
    file = open("en/reference/%s" % metric_reference.filename, "w")
    file.write(metric_reference.as_html())


def generate_doc(metric_type, units):
    filename = metric_type.lower() + "-metrics-reference.html"
    title = metric_type.title() + " Metrics"
    metrics = get_metrics(metric_type, units)
    return MetricReference(filename, title, metrics)


def generate_docs(metric_types, units):
    metrics_super_set = []
    for metric_type in metric_types:
        filename = metric_type.lower() + "-metrics-reference.html"
        title = metric_type.title() + " Metrics"
        metrics = get_metrics(metric_type, units)
        write_reference_doc(MetricReference(filename, title, metrics))
        metrics_super_set.extend(metrics)
    return metrics_super_set


def get_metric_set(metric_set, metrics_superset, suffixes):
    response = requests.get(
        f'https://raw.githubusercontent.com/vespa-engine/vespa/master/metrics/src/main/java/ai/vespa/metrics/set/{metric_set.enum_filename}')
    return parse_metric_set(response.text, metrics_superset, suffixes)


def generate_metric_set_doc(metric_sets, metrics_superset):
    suffix_names = get_suffix_names()
    for metric_set in metric_sets:
        filename = metric_set.name.lower() + "-set-metrics-reference.html"
        title = metric_set.name.title() + " Metric Set"
        metrics = get_metric_set(metric_set, metrics_superset, suffix_names)
        write_reference_doc(MetricSetReference(filename, title, metrics))


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
        "Slobrok",
        "Sentinel",
        "ClusterController"
    ]
    metrics_super_set = generate_docs(metric_types, units)

    MetricSet = namedtuple("MetricSet", "name enum_filename")
    metric_sets = [
        MetricSet("Default", "DefaultMetrics.java"),
        MetricSet("Vespa", "VespaMetricSet.java")
    ]
    generate_metric_set_doc(metric_sets, metrics_super_set)
    write_reference_doc(UnitReference("unit-metrics-reference.html", "Metric Units Reference", units.values()))


generate_metrics_doc()
