import re
import yaml

import requests


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
    response = requests.get(
        "https://raw.githubusercontent.com/vespa-engine/vespa/master/container-core/src/main/java/com/yahoo/metrics/Unit.java")
    content = response.text
    base_unit_dict = parse_base_units(content)
    return parse_units(content, base_unit_dict)


def parse_metrics(content, units):
    metrics = []
    for line in content.split("\n"):
        metric = {}
        # Matches Unit name to base unit and optional per-unit
        matcher = re.search(r".*\(\"(.+)\",\s*Unit\.([A-Z_]+),\s*\"(.*)\"", line)
        if matcher:
            metric["name"] = matcher.group(1)
            metric["unit"] = units[matcher.group(2)]
            metric["description"] = matcher.group(3)
            metrics.append(metric)
    return metrics


def get_metrics(metric_type, units):
    response = requests.get(
        f'https://raw.githubusercontent.com/vespa-engine/vespa/master/container-core/src/main/java/com/yahoo/metrics/{metric_type}.java')
    return parse_metrics(response.text, units)


def generate_metrics_doc():
    units = get_units()
    metrics = {"container_metrics": get_metrics("ContainerMetrics", units),
               "searchnode_metrics": get_metrics("SearchNodeMetrics", units),
               "storage_metrics": get_metrics("StorageMetrics", units),
               "distributor_metrics": get_metrics("DistributorMetrics", units)}

    with open('_data/metrics.yml', 'w') as outfile:
        yaml.dump(metrics, outfile, default_flow_style=False)


generate_metrics_doc()
