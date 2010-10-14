#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ventilator test
"""


import os, unittest, shutil
from pprint import pprint

import vigilo.vigiconf.conf as conf

from confutil import reload_conf, setup_tmpdir
from confutil import setup_db, teardown_db

from vigilo.vigiconf.lib import dispatchmodes
from vigilo.vigiconf.lib.ventilation.local import VentilatorLocal
from vigilo.vigiconf.lib.ventilation.remote import VentilatorRemote
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.lib.loaders import LoaderManager
from vigilo.vigiconf.lib import ParsingError

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, Ventilation, Application, SupItemGroup
from vigilo.models.demo.functions import add_host, add_vigiloserver, add_supitemgroup

class VentilatorTest(unittest.TestCase):
    """Test VentilatorRemote"""

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "db"))
        self.basedir = os.path.join(self.tmpdir, "deploy")
        conf.hosttemplatefactory.load_templates()
        setup_db()
        reload_conf()
        dispatchator = dispatchmodes.getinstance()
        self.generator = GeneratorManager(dispatchator.applications)
        self.ventilator = VentilatorRemote(dispatchator.applications)
        self.ventilator_local = VentilatorLocal(dispatchator.applications)

    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        shutil.rmtree(self.tmpdir)


    def test_export_localventilation_db(self):
        """ test de l'export de la ventilation en mode local.

        le remplacement de la persistance pickle par db n'est pas testée
        ici.
        """
        ventilation = self.ventilator_local.ventilate()
        num_apps = len(ventilation['localhost'])

        # need locahost in db
        host = add_host("localhost")
        # need localhost as VigiloServer
        add_vigiloserver(u'localhost')

        #need apps in DB
        loader = LoaderManager()
        loader.load_apps_db(self.generator.apps)
        DBSession.flush()
        self.assertEquals(DBSession.query(Application).count(), num_apps,
                "There should be %d apps in DB" % num_apps)

        loader.load_vigilo_servers_db()
        loader.load_ventilation_db(ventilation)

        # check that for each app, localhost is supervised by itself
        for app in conf.apps:
            links = DBSession.query(Ventilation).filter(Ventilation.application.has(Application.name==unicode(app))).filter(Ventilation.host==host)
            self.assertEquals(links.count(), 1, "One supervision link (%d)" % links.count())
            self.assertEquals(links.first().vigiloserver.name, u'localhost', "superviser server is localhost")

    def test_getservertouse(self, one_server=True):
        """ Test de la nouvelle persistance db remplaçant la persistance pickle.
        """
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                conf.appsGroupsByServer[appGroup][hostGroup].remove(u'localhost2')

        # need locahost in db
        host = add_host("localhost")

        # need server
        add_vigiloserver(u'localhost')

        # need applications from the collect group
        appGroup = "collect"
        for app in ["nagios", "perfdata", "collector"]:
            DBSession.add(Application(name=unicode(app)))
        DBSession.flush()

        for hostGroup in conf.appsGroupsByServer[appGroup]:
            l = conf.appsGroupsByServer[appGroup][hostGroup]
            server = self.ventilator.getServerToUse(l, host.name, appGroup)
            if one_server:
                self.assertEquals(server, u'localhost')

    def test_getservertouse_multi(self):
        """ Test de la ventilation sur plusieurs serveurs vigilo.
        """
        # add 2 others servers in conf
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver2.example.com')
                conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver3.example.com')

        # add the 2 servers in DB
        add_vigiloserver(u'supserver2.example.com')
        add_vigiloserver(u'supserver3.example.com')

        self.test_getservertouse(one_server=False)

    def test_host_ventilation_group(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        host.groups = [group2,]
        self.assertEquals(self.ventilator.get_host_ventilation_group("localhost", {}), "Group1")

    def test_host_ventilation_group_multiple(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        group3 = add_supitemgroup("Group3", group1)
        host.groups = [group2, group3]
        self.assertEquals(self.ventilator.get_host_ventilation_group("localhost", {}), "Group1")

    def test_host_ventilation_conflicting_groups(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        group3 = add_supitemgroup("Group3")
        group4 = add_supitemgroup("Group4", group3)
        host.groups = [group2, group4]
        self.assertRaises(ParsingError, self.ventilator.get_host_ventilation_group, "localhost", {})

    def test_reventilate(self):
        """Cas où un serveur est supprimé de la conf"""
        # besoin de localhost en base
        host = add_host("localhost")
        # chargement des apps
        loader = LoaderManager()
        loader.load_apps_db(self.generator.apps)
        DBSession.flush()
        # On ajoute 2 autres serveurs de supervision
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver2.example.com')
                conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver3.example.com')
        loader.load_vigilo_servers_db()
        for i in range(9):
            hostname = "localhost%d" % i
            conf.hostsConf[hostname] = conf.hostsConf["localhost"].copy()
            conf.hostsConf[hostname]["name"] = hostname
            add_host(hostname)
        ventilation = self.ventilator.ventilate()
        loader.load_ventilation_db(ventilation)
        # On vérifie que des hôtes ont quand même été affectés à supserver3.example.com
        ss3_hosts = []
        for host in ventilation:
            for app in ventilation[host]:
                if ventilation[host][app] == "supserver3.example.com":
                    ss3_hosts.append(host)
        assert len(ss3_hosts) > 0
        # Et maintenant, on supprime supserver3.example.com
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                conf.appsGroupsByServer[appGroup][hostGroup].remove(u'supserver3.example.com')
        # On reventile
        ventilation = self.ventilator.ventilate()
        loader.load_ventilation_db(ventilation)

        # Tout doit avoir été reventilé sur les autres serveurs
        for host in ventilation:
            for app in ventilation[host]:
                self.assertNotEquals(ventilation[host][app],
                        "supserver3.example.com",
                        u"L'hote %s est toujours supervise par un "
                            % host +
                        u"serveur qui a ete supprime")


if __name__ == '__main__':
    unittest.main()
