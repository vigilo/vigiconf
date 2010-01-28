#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

import os

class XSDTest(unittest.TestCase):
    """A base class for testing XSD schema.
    
    Usage:
    just use it as a base class then redefine:
      * xsd_file
      * xml_ok_files
      * xml_ko_files
    TODO: move to common module, use lxml ?
    """
    _cmd_verb = "xmllint --noout --schema %s %s"
    _cmd_silent = "xmllint --noout --schema %s %s 2> /dev/null"
    
    xsd_file = "tests/testdata/xsd/sample.xsd"
    xml_ok_files = {"tests/testdata/xsd":["sample_ok.xml", ]}
    xml_ko_files = {"tests/testdata/xsd":["sample_ko.xml", ]}
    
    def test_xmllint_present(self):
        self.assertEquals(0, os.system("xmllint --version 2> /dev/null"),
                          "xmllint is installed")
    
    def test_xsd_ko_files(self):
        """ test invalid xml files"""
        for dir, files in self.xml_ko_files.iteritems():
            for file in files:
                cmd = self._cmd_silent % (self.xsd_file, os.path.join(dir, file))
                r = os.system(cmd)
                self.assertNotEquals(0, r, "file %s is invalid" % file)
    
    def test_xsd_ok_files(self):
        """ test valid xml files"""
        ko_list = []
        for dir, files in self.xml_ok_files.iteritems():
            for file in files:
                cmd = self._cmd_verb % (self.xsd_file, os.path.join(dir, file))
                r = os.system(cmd)
                if r != 0:
                    ko_list.append(file)
        if len(ko_list) > 0:
            self.assertFalse(True, "files %s should be valid" % ", ".join(ko_list))
        
