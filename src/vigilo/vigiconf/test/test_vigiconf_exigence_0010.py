#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test des exigences vigiconf
"""

import os
import unittest

import vigilo.vigiconf.conf as conf
from vigilo.common.conf import settings
settings.load_module(__name__)

from helpers import setup_db, teardown_db, DummyRevMan, TESTDATADIR

from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.loaders.hlservice import HLServiceLoader

from vigilo.models.tables import SupItemGroup, HighLevelService
from vigilo.models.session import DBSession
from vigilo.models.demo.functions import add_host, add_lowlevelservice

from vigilo.vigiconf.lib.confclasses.host import HostFactory
from vigilo.vigiconf.lib.confclasses.hosttemplate import HostTemplate
from vigilo.models.tables.grouphierarchy import GroupHierarchy


class ExigConfiguration0010Test(unittest.TestCase):
    """
    Test de l'exigence VIGILO_EXIG_VIGILO_CONFIGURATION_0010::

        Fonctions de préparation des configurations de la supervision
        en mode CLI.

        La fonction de configuration de la supervision doit permettre à un
        utilisateur au travers d'une IHM de type CLI (Command Line Interface)
        de réaliser les fonctions de gestion de configurations suivantes :

        configuration des groupes d'hôtes :
          ajout/modification/suppression d'un groupe d'hôte
        configuration des hôtes à superviser :
          ajout/modification/suppression d'un hôte ou d'une liste d'hôtes;
        configuration des paramètres d'authentification SNMP pour chaque hôte
          à superviser ( version V1,V2c,V3) et adresse IP pour l'interface SNMP
        configuration d'un groupe de service : ajout/modification/suppression
          d'un groupe de service
        configuration des services et seuils d'alarmes :
          ajout/modification/suppression d'un service et positionnement des
            seuils d'alarme Warning/Critical/OK;
        configuration des services de haut niveau :
          ajout/modification/suppression d'un service
        configuration des règles de corrélations associé à un service de haut
        niveau :
          ajout/modification/suppression d'une règle de corrélation
        configuration des valeurs de performances à collecter :
          ajout/modification/suppression d'une valeur de performance
        configuration des cartes automatiques
    """

    def setUp(self):
        """Call before every test case."""
        setup_db()
        #reload_conf()


    def tearDown(self):
        """Call after every test case."""
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        teardown_db()

    def test_hostgroup(self):
        DBSession.query(SupItemGroup).delete()
        DBSession.query(GroupHierarchy).delete()
        DBSession.flush()
        grouploader1 = GroupLoader()
        grouploader1.load_dir(os.path.join(TESTDATADIR, 'xsd/hostgroups/ok'))

        nb = DBSession.query(SupItemGroup).count()
        self.assertEquals(22, nb, "Host groups not loaded")

    def test_host(self):
        # ces templates sont utilisés dans les fichiers
        for tplname in ["default", "linux"]:
            conf.hosttemplatefactory.register(HostTemplate(tplname))
        f = HostFactory(
                os.path.join(TESTDATADIR, 'xsd/hosts/todelete'),
                conf.hosttemplatefactory,
                conf.testfactory,
            )
        hosts = f.load()
        self.assertFalse(hosts.has_key('localhost'),
                         "localhost has been deleted in conf")
        self.assertTrue(hosts.has_key('testhost2'), "testhost2 is in conf")

    # @TODO: il faudrait rédiger ces tests unitaires.
#    def test_snmp_v1(self):
#        pass
#
#    def test_snmp_v2c(self):
#        pass
#
#    def test_snmp_v3(self):
#        pass
#
#    def test_service_seuilalarm_ajout(self):
#        pass
#
#    def test_service_seuilalarm_modif(self):
#        pass
#
#    def test_service_seuilalarm_suppr(self):
#        pass
#
#    def test_service_hls_ajout(self):
#        pass
#
#    def test_service_hls_modif(self):
#        pass

    def test_service_hls_suppr(self):
        # création de groupes de services
        host1 = add_host("host11")
        add_host("host12")
        add_lowlevelservice(host1, "llservice1")
        add_lowlevelservice(host1, "llservice2")
        grouploader = GroupLoader()
        grouploader.insert({"name": u"hlsgroup1", "parent": None})
        grouploader.insert({"name": u"hlsgroup2", "parent": None})
        hlserviceloader1 = HLServiceLoader(grouploader, DummyRevMan())
        hlserviceloader1.load_dir(os.path.join(TESTDATADIR,
                                  'xsd/hlservices/ok'))

        nb = DBSession.query(HighLevelService).count()
        self.assertEquals(nb, 4, "4 hlservices created")
        hls = HighLevelService.by_service_name(u'hlservice11')
        self.assertTrue(hls, "hlservice11 created.")

        # on charge un dossier avec un seul hls
        grouploader = GroupLoader()
        hlserviceloader2 = HLServiceLoader(grouploader, DummyRevMan())
        hlserviceloader2.has_changed = True
        hlserviceloader2.load_dir(os.path.join(TESTDATADIR,
                                  'xsd/hlservices/todelete'))
        hlserviceloader2.cleanup()

        nb2 = DBSession.query(HighLevelService).count()
        print [ hls.servicename for hls in
                DBSession.query(HighLevelService).all() ]
        self.assertEquals(nb2, 1, "1 hlservice")

        hls = HighLevelService.by_service_name(u'hlservice1')
        self.assertTrue(hls, "hlservice1 re-created.")


    # @TODO: il faudrait rédiger ces tests unitaires.
#    def test_reglecorr_hls_ajout(self):
#        pass
#
#    def test_reglecorr_hls_modif(self):
#        pass
#
#    def test_reglecorr_hls_suppr(self):
#        pass
#
#    def test_valeurperf_ajout(self):
#        pass
#
#    def test_valeurperf_modif(self):
#        pass
#
#    def test_valeurperf_suppr(self):
#        pass
#
#    def test_conf_carte_auto(self):
#        """ Test configuration des cartes automatiques.
#        """
#        #self.assertTrue(False, "Not yet implemented.")


if __name__ == '__main__':
    unittest.main()
