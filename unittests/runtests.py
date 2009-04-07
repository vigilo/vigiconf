#!/usr/bin/python2.5

"""
Run all the unit tests.

Python >= 2.5 required for the dispatchator

"""

import os
import unittest

curdir = os.path.abspath(os.path.dirname(__file__))
os.chdir(curdir)
os.environ["VIGICONF_MAINCONF"] = "../src/confmgr-test.conf"

import sys
sys.path.insert(0, "../src")

# Load available suites
for file in os.listdir(curdir):
    if not file.endswith(".py"):
        continue
    if file == os.path.basename(__file__):
        continue
    execfile(os.path.join(curdir, file))

# Run all the tests
unittest.main()
