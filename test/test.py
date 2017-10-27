#! /usr/bin/python
# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

# Copyright 2017 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

import os
import re
import sys
import json
import time
import yaml
import shutil
import urllib2
import tempfile
import subprocess

from bs4 import BeautifulSoup

################################################################################
# Execution
################################################################################

project_root = os.getcwd()
work_dir = os.path.join(project_root, "_work")

script = {
    "before" : [],
    "steps" : [],
    "after" : []
}


def print_cmd_header(cmd, extra="", print_header=True):
    if not print_header:
        return
    print("")
    print("*" * 80)
    print("* {0}".format(cmd))
    if len(extra) > 0:
        print("* ({0})".format(extra))
    print("*" * 80)


def stop(msg):
    sys.stderr.write("ERROR: {0}\n".format(msg))
    sys.exit(-1)


def shell_cmd(cmd):
    retcode = subprocess.call(cmd, shell=True)
    return retcode


def shell_cmd_output(cmd, print_output=True):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    retcode = p.returncode
    if print_output:
        print stdout.strip()
        print stderr.strip()
    return retcode, stdout, stderr


def exec_export(cmd):
    command = cmd["$"]
    print_cmd_header(command)

    m = re.match("^export ([_A-Za-z]+)\s*=\s*(.+)$", command)
    if m != None:
        name = m.group(1)
        _,value,_ = shell_cmd_output("echo {0}".format(m.group(2)), print_output=False)
        os.putenv(name, value.strip())
        print("{0}={1}".format(name, value.strip()))
    else:
        stop("Could not parse export command '{0}'".format(command))


def exec_wait(cmd):
    command = cmd["$"]
    expect = cmd["wait-for"]
    max_wait = 300 # todo: max this configurable
    try_interval = 5 # todo: max this configurable too
    print_cmd_header(command, "Waiting for '{0}'".format(expect))

    waited = 0
    while waited < max_wait:
        retcode,stdout,stderr = shell_cmd_output(command, print_output=False)
        if stdout.find(expect) >= 0:
            return
        else:
            time.sleep(try_interval)
            waited += try_interval
            print("Waited for {0}/{1} seconds...".format(waited, max_wait))

    if waited >= max_wait:
        stop("Expected output '{0}' not found in command '{1}'. Waited for {2} seconds.".format(expect, command, max_wait))


def exec_assert(cmd):
    command = cmd["$"]
    expect = cmd["contains"]
    print_cmd_header(command, "Expecting '{0}'".format(expect))

    retcode,stdout,stderr = shell_cmd_output(command, print_output=True)
    if stdout.find(expect) == -1:
        stop("Expected output '{0}' not found in command '{1}'".format(expect, command))


def exec_default(cmd):
    command = cmd["$"]
    print_cmd_header(command)

    retcode = shell_cmd(command)
    if retcode != 0:
        stop("Command '{0}' returned code {1}".format(command, retcode))


def exec_step(cmd):
    globals()["exec_" + cmd["type"]](cmd)


def exec_script():
    tmpdir = tempfile.mkdtemp(dir=work_dir)
    os.chdir(tmpdir)

    try:
        for cmd in script["before"]:
            exec_step(cmd)
        for cmd in script["steps"]:
            exec_step(cmd)
    except Exception as e:
        print(e)
    finally:
        for cmd in script["after"]:
            try:
                exec_step(cmd)
            except:
                pass


################################################################################
# Parsing
################################################################################

def parse_cmd(cmd, attrs):
    cmd = cmd.strip()
    if cmd.startswith("#"):
        return None
    if cmd.startswith("$"):
        cmd = cmd[1:]
    cmd = cmd.strip()
    if len(cmd) == 0:
        return None

    if cmd.startswith("export"):
        return { "$" : cmd, "type":"export" }
    if attrs.has_key("data-test-wait-for"):
        return { "$" : cmd, "type":"wait", "wait-for":attrs["data-test-wait-for"] }
    if attrs.has_key("data-test-assert-contains"):
        return { "$" : cmd, "type":"assert", "contains":attrs["data-test-assert-contains"] }
    return { "$" : cmd, "type":"default" }


def parse_cmds(pre, attrs):
    cmds = []
    line_continuation = ""
    line_continuation_delimiter = "\\"
    for line in pre.split("\n"):
        cmd = "{0} {1}".format(line_continuation, line.strip())
        if cmd.endswith(line_continuation_delimiter):
            line_continuation += cmd[:-len(line_continuation_delimiter)]
        else:
            cmd = parse_cmd(cmd, attrs)
            if cmd != None:
                cmds.append(cmd)
            line_continuation = ""
    return cmds


def parse_file(pre, attrs):
    stop("File fields are not implemented yet")


def process_page(html, source_name = ""):
    global script
    script["before"] = []
    script["steps"]  = []
    script["after"]  = []

    soup = BeautifulSoup(html, "html.parser")

    for pre in soup.find_all(lambda tag: tag.name == "pre" and tag.has_attr("data-test")):
        if pre.attrs["data-test"] == "before":
            script["before"].extend(parse_cmds(pre.string, pre.attrs))

        if pre.attrs["data-test"] == "exec":
            script["steps"].extend(parse_cmds(pre.string, pre.attrs))

        if pre.attrs["data-test"] == "file":
            script["steps"].extend(parse_file(pre.string, pre.attrs))

        if pre.attrs["data-test"] == "after":
            script["after"].extend(parse_cmds(pre.string, pre.attrs))

    print_cmd_header("Script to execute", extra = source_name)
    print(json.dumps(script, indent=2))

    exec_script()


################################################################################
# Running
################################################################################

def create_work_dir():
    os.chdir(project_root)
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)


def run_url(url):
    html = urllib2.urlopen(url).read()
    process_page(html, url)


def run_config():
    config_file = "_test_config.yml"
    if not os.path.isfile(config_file):
        config_file = os.path.join("test",config_file)
    if not os.path.isfile(config_file):
        stop("Could not find configuration file")

    with open(config_file, "r") as f:
        config = yaml.load(f)
        for url in config["urls"]:
            run_url(url)


def run_file(file_name):
    if file_name.startswith("http"):
        run_url(file_name)
    elif file_name == "-":
        process_page(sys.stdin.read(), "stdin")
    else:
        with open(file_name) as f:
            process_page(f.read(), file_name)


def main():
    create_work_dir()

    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        run_config()


if __name__ == "__main__":
    main()
