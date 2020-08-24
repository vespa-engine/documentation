<!-- Copyright Verizon Media. Licensed under the terms of the Apache 2.0 license. See LICENSE in the project root. -->

# Documentation testing

This directory contains the Vespa documentation testing code.
The URLs to test are specified in `_test_config.yml`.
Running

    $ ./test.py

without arguments will test each URL in that file in sequence.

To run this locally:

    $ pip3 install -r requirements.txt
    $ ./test.py [URL | FILE]

If you want to run a test that is not in the above file, you can add the file
path or URL as an argument and that test will be run.

Alternatively, run in docker (like the travis tests do):

    $ ./travis/start-docker-container.sh
