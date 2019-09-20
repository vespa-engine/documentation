#!/usr/bin/env bash

# Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

set -e

# The vespaengine/vespa-pipeline contains both JDK 8 and 11. For the sample-apps/documentation we
# must use JDK 11:
source /etc/profile.d/jdk-env.sh
/usr/sbin/alternatives --set java "$JAVA_11"
/usr/sbin/alternatives --set javac "$JAVAC_11"
export JAVA_HOME="$JAVA_11_HOME"

yum install -y python36-pip

pip3 install -r test/requirements.txt --user

./test/test.py

