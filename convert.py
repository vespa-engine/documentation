#!/usr/bin/env python3
# Copyright Vespa.ai. All rights reserved.
#Convert from jsonl to json

import sys
import json

docs = []
for line in open(sys.argv[1]):
	d = json.loads(line)
	docs.append(d)

with open(sys.argv[2],"w") as fp:
	fp.write(json.dumps(docs))

