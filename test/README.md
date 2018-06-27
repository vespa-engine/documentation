<!-- Copyright 2018 Yahoo Holdings. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root. -->

# Documentation testing

This directory contains the Vespa documentation testing code. The URLs to test
are specified in the `_test_config.yml` file. Running

    $ python test.py

without arguments will test each URL in that file in sequence.

To run this locally:

    $ pip install -r requirements.txt
    $ python test.py [URL | FILE]

If you want to run a test that is not in the above file, you can add the file
path or URL as an argument and that test will be run.

