#!/usr/bin/env bash

# Copyright 2019 Oath Inc. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.

set -e

echo "Docker version: $(docker --version)"

docker run --rm --net=host -v/var/run/docker.sock:/var/run/docker.sock -v $(pwd):$(pwd) -w $(pwd) --entrypoint $(pwd)/travis/compile-and-test.sh vespaengine/vespa-pipeline
