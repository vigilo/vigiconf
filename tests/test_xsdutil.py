#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

import os
import subprocess

class XSDTest(unittest.TestCase):
    """A base class for testing XSD schema.

    Usage:
    just use it as a base class then redefine:
      * xsd_file
      * xml_ok_files
      * xml_ko_files
    """
    _cmd_verb = "xmllint --noout --schema %s %s"
    _cmd_silent = "xmllint --noout --schema %s %s 2>/dev/null"

    xsd_file = "tests/testdata/xsd/sample.xsd"
    xml_ok_files = {"tests/testdata/xsd":["sample_ok.xml", ]}
    xml_ko_files = {"tests/testdata/xsd":["sample_ko.xml", ]}

    def test_xmllint_present(self):
        self.assertEquals(0, subprocess.call("xmllint --version 2> /dev/null", shell="True"),
                          "xmllint is installed")

    def test_xsd_ko_files(self):
        """ test invalid xml files"""
        for dir, files in self.xml_ko_files.iteritems():
            for file in files:
                cmd = self._cmd_silent % (self.xsd_file, os.path.join(dir, file))
                r = subprocess.call(cmd, shell="True")
                self.assertNotEquals(0, r, "file %s is invalid" % file)

    def test_xsd_ok_files(self):
        """ test valid xml files"""
        ko_list = []
        for dir, files in self.xml_ok_files.iteritems():
            for file in files:
                cmd = self._cmd_silent % (self.xsd_file, os.path.join(dir, file))
                r = subprocess.call(cmd, shell="True")
                if r != 0:
                    print "Failed to validate %s" % file
                    print cmd
                    ko_list.append(file)
        if len(ko_list) > 0:
            self.fail("files %s should be valid" % ", ".join(ko_list))

