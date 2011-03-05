#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

import os
import subprocess
import glob

class XSDTest(unittest.TestCase):
    """
    A base class for testing XSD schema.

    Just use it as a base class then redefine:
      - xsd_file
      - xml_ok_files
      - xml_ko_files
    """
    _cmd_verb = "xmllint --noout --schema %s %s"
    _cmd_silent = "xmllint --noout --schema %s %s 2>/dev/null"

    xsd_file = "testdata/xsd/sample.xsd"
    xml_ok_files = {"testdata/xsd":["sample_ok.xml", ]}
    xml_ko_files = {"testdata/xsd":["sample_ko.xml", ]}

    def test_xmllint_present(self):
        result = subprocess.call("xmllint --version 2> /dev/null", shell="True")
        self.assertEquals(0, result, "xmllint must be installed")

    def _run_command(self, filepath, expect):
        here = os.path.dirname(__file__)
        cmd = self._cmd_silent % (os.path.join(here, self.xsd_file), filepath)
        r = subprocess.call(cmd, shell="True")
        if expect == "ko":
            self.assertNotEquals(0, r, "file %s is invalid" % filepath)
        elif expect == "ok" and r != 0:
            print "Failed to validate %s" % filepath
            print cmd
            return False
        return True

    def test_xsd_ko_files(self):
        """ test invalid xml files"""
        here = os.path.dirname(__file__)
        for dir, files in self.xml_ko_files.iteritems():
            for file in files:
                filepath = os.path.join(here, dir, file)
                if "*" in file:
                    for f in glob.glob(filepath):
                        self._run_command(f, "ko")
                else:
                    self._run_command(filepath, "ko")

    def test_xsd_ok_files(self):
        """ test valid xml files"""
        here = os.path.dirname(__file__)
        ko_list = []
        for dir, files in self.xml_ok_files.iteritems():
            for file in files:
                filepath = os.path.join(here, dir, file)
                if "*" in file:
                    for f in glob.glob(filepath):
                        if not self._run_command(f, "ok"):
                            ko_list.append(f)
                else:
                    if not self._run_command(filepath, "ok"):
                        ko_list.append(filepath)
        if len(ko_list) > 0:
            self.fail("files %s should be valid" % ", ".join(ko_list))

