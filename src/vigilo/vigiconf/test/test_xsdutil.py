# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2014 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import

import unittest

import os
import subprocess
import glob

from .helpers import TESTDATADIR


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
    _xsd_basedir = os.path.join(os.path.dirname(__file__), "..",
                                "validation", "xsd")
    _basedir = os.path.join(TESTDATADIR, "xsd")

    xsd_file = "../../test/testdata/xsd/sample.xsd"
    xml_ok_files = {"":["sample_ok.xml", ]}
    xml_ko_files = {"":["sample_ko.xml", ]}

    def test_xmllint_present(self):
        result = subprocess.call("xmllint --version 2> /dev/null", shell="True")
        self.assertEquals(0, result, "xmllint must be installed")

    def _run_command(self, filepath, expect):
        xsd_path = os.path.join(self._xsd_basedir, self.xsd_file)
        cmd = self._cmd_silent % (xsd_path, filepath)
        #cmd = self._cmd_verb % (xsd_path, filepath)
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
        for subdir, files in self.xml_ko_files.iteritems():
            for filename in files:
                filepath = os.path.join(self._basedir, subdir, filename)
                if "*" in filename:
                    for f in glob.glob(filepath):
                        self._run_command(f, "ko")
                else:
                    self._run_command(filepath, "ko")

    def test_xsd_ok_files(self):
        """ test valid xml files"""
        ko_list = []
        for subdir, files in self.xml_ok_files.iteritems():
            for filename in files:
                filepath = os.path.join(self._basedir, subdir, filename)
                if "*" in filename:
                    for f in glob.glob(filepath):
                        if not self._run_command(f, "ok"):
                            ko_list.append(f)
                else:
                    if not self._run_command(filepath, "ok"):
                        ko_list.append(filepath)
        if len(ko_list) > 0:
            self.fail("files %s should be valid" % ", ".join(ko_list))
