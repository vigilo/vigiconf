#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test de la validation des applications
"""
import unittest
import os

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib import dispatchmodes
from vigilo.vigiconf.lib.application import ApplicationError
from vigilo.vigiconf.lib.systemcommand import SystemCommandError

from vigilo.common.conf import settings
settings.load_module(__name__)

from confutil import reload_conf


class AppsValidationTest(unittest.TestCase):

    def setUp(self):
        """Call before every test case."""
        reload_conf()
    
    def test_saveToConfig(self):
        """ test partiel de la validation des applis dans la méthode
            saveToConfig
        """
        # Deploy on the localhost only -> switch to Community Edition
        delattr(conf, "appsGroupsByServer")
        dispatchator = dispatchmodes.getinstance()
        
        for _App in dispatchator.getApplications():
            try:
                _App.validate(os.path.join(settings["vigiconf"].get("libdir"), "deploy"))
            except ApplicationError, e:
                if e.cause is not None \
                        and isinstance(e.cause, SystemCommandError) \
                        and e.cause.returncode == 255:
                    # a system command is missing, no big deal
                    print "Missing command to validate %s" % _App.getName()
                else:
                    raise
