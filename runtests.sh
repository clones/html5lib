#!/bin/sh
#
# A simple script to run both the python and ruby tests back to back
#
(cd python; python tests/runtests.py) && (cd ruby; rake test)
