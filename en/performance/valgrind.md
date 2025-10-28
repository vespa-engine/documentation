---
# Copyright Vespa.ai. All rights reserved.
title: "Using Valgrind with Vespa"
---

Valgrind is a useful tool to investigate bugs,
and to get a detailed performance profile of an application
after [profiling](profiling.html) to get the higher level picture.
This documents how to run Vespa processes with valgrind.

## Valgrind with callgrind

Install valgrind.
One might need to enable world writeable `$VESPA_HOME`:

```
$ sudo chmod 777 $VESPA_HOME
```

Keep in mind to reset that after profiling session is completed.
General use of valgrind - show memory errors:

```
$ valgrind 'application'
```

Show call graph:

```
$ valgrind --tool=callgrind 'application'
```

Show a detailed profiling graph - use this to optimize the application:

```
$ valgrind --tool=callgrind --simulate-hwpref=yes --simulate-cache=yes \
  --dump-instr=yes --collect-jumps=yes 'application'
```

After running valgrind, copy *callgrind.out.** to a host that has *kcachegrind* installed.
Also copy the binary to the same path as it had while running.
It might also be nice to have access to the code - path to code can be specified in kcachegrind.

## Start Vespa using valgrind

Start Vespa with the following environment variables set:

```
$ VESPA_USE_VALGRIND="vespa-proton"
```

Run Vespa under valgrind and check for memory errors (logs in `$VESPA_HOME/tmp/`):

```
$ VESPA_USE_VALGRIND="vespa-proton" VESPA_VALGRIND_OPT="--tool=callgrind --simulate-hwpref=yes \
  --simulate-cache=yes --dump-instr=yes --collect-jumps=yes"
```

Profile the application:

```
$ VESPA_USE_VALGRIND="vespa-proton" VESPA_VALGRIND_OPT="--tool=callgrind --simulate-hwpref=yes \
  --simulate-wb=yes --dump-instr=yes --collect-jumps=yes --collect-bus=yes --branch-sim=yes"
```

Remember to stop Vespa - the callgrind.* files are not generated until the program stops.
