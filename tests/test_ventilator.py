#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ventilator test
"""


import unittest

import vigilo.vigiconf.conf as conf

from confutil import reload_conf, setup_tmpdir


class VentilatorTest(unittest.TestCase):
    """Test Sample"""

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        #self.tmpdir = setup_tmpdir()
    
    def tearDown(self):
        """Call after every test case."""
        #shutil.rmtree(self.tmpdir)
    
    def test_sample(self):
        pass

if __name__ == '__main__':
    unittest.main()
