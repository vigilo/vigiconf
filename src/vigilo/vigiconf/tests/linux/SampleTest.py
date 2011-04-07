# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903

from vigilo.vigiconf.lib.confclasses.test import Test



class SampleTest(Test):

    def add_test(self, host):
        """Adds the test"""
        print("Adding test from linux/SampleTest for %s"%host.name)


# vim:set expandtab tabstop=4 shiftwidth=4:
