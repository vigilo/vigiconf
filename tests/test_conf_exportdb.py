#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
sample test
"""


import unittest

import vigilo.vigiconf.conf as conf
from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.vigiconf.dbexportator import export_conf_db

from confutil import setup_db, teardown_db, reload_conf

from vigilo.models import Host, HostGroup
from vigilo.models.configure import DBSession

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
        self.assertEquals(len(conf.hostsConf.items()), 1,
                          "one host in conf (%d)"%len(conf.hostsConf.items()))
        
        export_conf_db()
        # check host groups
        nb = len(conf.hostsGroups.keys())
        # 2 groups created for new hosts and services (see settings)
        nb = nb + 2
        nbdb = DBSession.query(HostGroup).count()
        self.assertEquals(nb, nbdb, "nb hostgroups conf:%d db:%d" % (nb, nbdb))
        
        # check if localhost exists in db
        h = Host.by_host_name(u'localhost')
        self.assertEquals(h.name, u'localhost')
    

if __name__ == '__main__':
    unittest.main()
