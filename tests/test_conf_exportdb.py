#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sample test
"""


import unittest

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.dbexportator import export_conf_db

from confutil import reload_conf, setup_tmpdir, setup_db, teardown_db

from vigilo.models import Host, HostGroup
from vigilo.models.session import DBSession

class ExportDBTest(unittest.TestCase):
    """Test Sample"""

    def setUp(self):
        """Call before every test case."""
        reload_conf()
        setup_db()
        
    
    def tearDown(self):
        """Call after every test case."""
        teardown_db()
    
    def test_export_hosts_db(self):
        print 'hostsconf', conf.hostsConf
        
        export_conf_db()
        # check host groups
        nb = len(conf.hostsGroups.keys())
        nbdb = DBSession.query(HostGroup).count()
        self.assertEquals(nb, nbdb, "nb hostgroups conf:%d db:%d" % (nb, nbdb))
        
        # check if localhost exists in db
        h = Host.by_host_name(u'localhost')
        self.assertEquals(h.name, u'localhost')
    

if __name__ == '__main__':
    unittest.main()
