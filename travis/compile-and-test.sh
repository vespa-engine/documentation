#!/usr/bin/env bash

# Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

set -e

source /etc/profile.d/jdk-env.sh

# Install same docker as in our host on travis
curl -sLOf "https://download.docker.com/linux/centos/7/x86_64/stable/Packages/docker-ce-17.09.1.ce-1.el7.centos.x86_64.rpm"
yum localinstall -y docker-ce-17.09.1.ce-1.el7.centos.x86_64.rpm 

# Install python 3 and requirements for the tests
yum install -y python36-pip
pip3 install -r test/requirements.txt --user

# Some procedures use openssl
yum install -y openssl

# Run all tests
./test/test.py
