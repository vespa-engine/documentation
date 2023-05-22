#!/usr/bin/env python3
# Copyright Yahoo. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root.
#Convert from jsonl to json

import sys
import json

docs = []
for line in open(sys.argv[1]):
	d = json.loads(line)
	docs.append(d)

with open(sys.argv[2],"w") as fp:
	fp.write(json.dumps(docs))

