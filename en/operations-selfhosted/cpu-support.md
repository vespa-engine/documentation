---
# Copyright Vespa.ai. All rights reserved.
title: "CPU Support"
category: oss
redirect_from:
- /en/cpu-support.html
---

For maximum performance, the current version of Vespa for x86_64 is compiled only for [Haswell (2013)](https://en.wikipedia.org/wiki/Haswell_(microarchitecture)) or later CPUs.
If trying to run on an older CPU, you will likely see error messages like the following:

```
Problem running program /opt/vespa/bin/vespa-runserver => died with signal: illegal instruction (you probably have an older CPU than required)
```

or in older versions of Vespa, something like

```
/usr/local/bin/start-container.sh: line 67: 10 Illegal instruction /opt/vespa/bin/vespa-start-configserver
```

If you would like to run Vespa on an older CPU, we provide a [generic x86 container image](https://hub.docker.com/r/vespaengine/vespa-generic-intel-x86_64/).
This image is slower, receives less testing than the regular image, and is less frequently updated.
**To start a Vespa Docker container using this image:**

```
$ docker run --detach --name vespa --hostname vespa-container \
  --publish 8080:8080 --publish 19071:19071 \
  vespaengine/vespa-generic-intel-x86_64
```
