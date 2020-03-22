#!/usr/bin/env bash

# Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

set -e

source /etc/profile.d/jdk-env.sh

# Install same docker as in our host on travis
curl -sLOf "https://download.docker.com/linux/centos/7/x86_64/stable/Packages/docker-ce-18.06.0.ce-3.el7.x86_64.rpm"
yum localinstall -y docker-ce-18.06.0.ce-3.el7.x86_64.rpm

# Install python 3 and requirements for the tests
yum install -y python36-pip
pip3 install -r test/requirements.txt --user

# Some procedures use openssl
yum install -y openssl

export VESPA_TEAM_ALBUM_REC_JAVA_API_KEY

# Run all tests
./test/test.py
