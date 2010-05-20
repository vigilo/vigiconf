#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test that 
"""
import unittest
from vigilo.vigiconf.lib.revisionmanager import RevisionManager
from vigilo.vigiconf.lib.systemcommand import SystemCommand

class ServerTest:
    def createCommand(self, iCommand):
        """
        @note: To be implemented by subclasses
        @param iCommand: command to execute
        @type  iCommand: C{str}
        @return: the command instance
        @rtype: L{SystemCommand<lib.systemcommand.SystemCommand>}
        """
        c = SystemCommand(iCommand)
        return c
    

class RevisionManagerTest(unittest.TestCase):
    
    def test_nosuchfile_exception(self):
        rm = RevisionManager()
        
        server = ServerTest()
        cr = rm.getRevision(server, "file_not_exists.txt")
        self.assertEquals(0, cr)
        
