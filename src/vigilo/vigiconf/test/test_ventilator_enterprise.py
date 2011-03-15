#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests du Ventilator. Ces tests ne fonctionneront que dans
Vigilo Enterprise Edition.
"""

import string, random, math
import os, unittest, shutil
from pprint import pprint

from vigilo.common.conf import settings

import vigilo.vigiconf.conf as conf

from helpers import setup_tmpdir
from helpers import setup_db, teardown_db

from vigilo.vigiconf.lib.ventilation.remote import VentilatorRemote
from vigilo.vigiconf.loaders.ventilation import VentilationLoader
from vigilo.vigiconf.lib.server.local import ServerLocal
from vigilo.vigiconf.lib import ParsingError
from vigilo.vigiconf.lib.confclasses.host import Host as ConfHost
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.applications.vigimap import VigiMap
from vigilo.vigiconf.applications.connector_metro import ConnectorMetro

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, Ventilation, Application
from vigilo.models.tables import VigiloServer
from vigilo.models.demo import functions as df

class VentilatorTest(unittest.TestCase):
    """Test VentilatorRemote"""

    def setUp(self):
        """Call before every test case."""
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        os.mkdir(os.path.join(self.tmpdir, "db"))
        self.basedir = os.path.join(self.tmpdir, "deploy")
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        # créer le fichier ssh_config
        os.mkdir(os.path.join(self.tmpdir, "ssh"))
        open(os.path.join(self.tmpdir, "ssh", "ssh_config"), "w").close()
        setup_db()
        self.apps = {"nagios": Nagios(), "vigimap": VigiMap(),
                     "connector-metro": ConnectorMetro()}
        for appname in self.apps:
            df.add_application(appname)
        self.ventilator = VentilatorRemote(self.apps.values())

    def tearDown(self):
        """Call after every test case."""
        DBSession.expunge_all()
        teardown_db()
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts
        shutil.rmtree(self.tmpdir)


    def test_export_localventilation_db(self):
        """ test de l'export de la ventilation en mode local.

        le remplacement de la persistance pickle par db n'est pas testée
        ici.
        """
        ventilation = {"testserver1": {}}
        for app in self.apps.values():
            ventilation["testserver1"][app] = "sup.example.com"

        # chargement en base
        df.add_vigiloserver('sup.example.com')
        ConfHost(conf.hostsConf, "dummy.xml", "testserver1",
                 "192.168.1.1", "Servers")
        host_db = df.add_host("testserver1")

        # vérification de sécurité -- peut-être obsolète
        self.assertEquals(DBSession.query(Application).count(), len(self.apps),
                "There should be %d apps in DB" % len(self.apps))


        ventilationloader = VentilationLoader(ventilation, self.apps.values())
        ventilationloader.load()

        print ventilation
        for appname in self.apps:
            links = DBSession.query(Ventilation
                ).filter(Ventilation.application.has(
                    Application.name == unicode(appname))
                ).filter(Ventilation.host==host_db)
            print links.all()
            self.assertEquals(links.count(), 1,
                              "There should be one supervision link")
            self.assertEquals(links.first().vigiloserver.name,
                              u'sup.example.com',
                              "superviser server must be sup.example.com")

    def test_host_ventilation_group(self):
        host = df.add_host("localhost")
        group1 = df.add_supitemgroup("Group1")
        group2 = df.add_supitemgroup("Group2", group1)
        host.groups = [group2, ]
        self.ventilator.make_cache()
        self.assertEquals(self.ventilator.get_host_ventilation_group("localhost", {}), "Group1")

    def test_host_ventilation_group_multiple(self):
        host = df.add_host("localhost")
        group1 = df.add_supitemgroup("Group1")
        group2 = df.add_supitemgroup("Group2", group1)
        group3 = df.add_supitemgroup("Group3", group1)
        host.groups = [group2, group3]
        self.ventilator.make_cache()
        self.assertEquals(self.ventilator.get_host_ventilation_group(
                          "localhost", {}), "Group1")

    def test_host_ventilation_conflicting_groups(self):
        host = df.add_host("localhost")
        group1 = df.add_supitemgroup("Group1")
        group2 = df.add_supitemgroup("Group2", group1)
        group3 = df.add_supitemgroup("Group3")
        group4 = df.add_supitemgroup("Group4", group3)
        host.groups = [group2, group4]
        self.ventilator.make_cache()
        self.assertRaises(ParsingError,
                self.ventilator.get_host_ventilation_group, "localhost", {})

    def test_reventilate(self):
        """Cas où un serveur est supprimé de la conf"""
        # besoin de localhost en base
        host = ConfHost(conf.hostsConf, "hosts/localhost.xml", "localhost",
                             "127.0.0.1", "Servers")
        df.add_host("localhost")
        conf.appsGroupsByServer = {
                "interface": {
                    "P-F":     [u"sup.example.com", u"supserver2.example.com",
                                u"supserver3.example.com"],
                    "Servers": [u"sup.example.com", u"supserver2.example.com",
                                u"supserver3.example.com"],
                },
                "collect": {
                    "P-F":     [u"sup.example.com", u"supserver2.example.com",
                                u"supserver3.example.com"],
                    "Servers": [u"sup.example.com", u"supserver2.example.com",
                                u"supserver3.example.com"],
                },
                "metrology": {
                    "P-F":     [u"sup.example.com", u"supserver2.example.com",
                                u"supserver3.example.com"],
                    "Servers": [u"sup.example.com", u"supserver2.example.com",
                                u"supserver3.example.com"],
                },
        }
        df.add_vigiloserver('sup.example.com')
        df.add_vigiloserver('supserver2.example.com')
        df.add_vigiloserver('supserver3.example.com')
        for i in range(9):
            hostname = "localhost%d" % i
            conf.hostsConf[hostname] = conf.hostsConf["localhost"].copy()
            conf.hostsConf[hostname]["name"] = hostname
            df.add_host(hostname)
        ventilation = self.ventilator.ventilate()
        ventilationloader = VentilationLoader(ventilation, self.apps.values())
        ventilationloader.load()
        # On vérifie que des hôtes ont quand même été affectés à
        # supserver3.example.com
        ss3_hosts = []
        for host in ventilation:
            for app in ventilation[host]:
                if "supserver3.example.com" in ventilation[host][app]:
                    ss3_hosts.append(host)
        assert len(ss3_hosts) > 0
        # Et maintenant, on supprime supserver3.example.com
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                conf.appsGroupsByServer[appGroup][hostGroup].remove(
                        u'supserver3.example.com')
        # On reventile
        ventilation = self.ventilator.ventilate()
        ventilationloader = VentilationLoader(ventilation, self.apps.values())
        ventilationloader.load()

        # Tout doit avoir été reventilé sur les autres serveurs
        for host in ventilation:
            for app in ventilation[host]:
                self.assertNotEquals(ventilation[host][app],
                        "supserver3.example.com",
                        u"L'hote %s est toujours supervise par un "
                            % host +
                        u"serveur qui a ete supprime")

    def test_ventilation_with_backup(self):
        """
        La ventilation donne un nominal et un backup pour chaque
        hôte/fonction.
        """
        conf.appsGroupsByServer = {
            'collect' : {
                'P-F'             : ['localhost'],
                'Servers'         : ['localhost'],
                'Telecom'         : ['localhost'],
            },
            'metrology' : {
                'P-F'             : ['localhost'],
                'Servers'         : ['localhost'],
                'Telecom'         : ['localhost'],
            },
        }
        conf.appsGroupsBackup = {
            'collect' : {
                'P-F'             : ["localhost2"],
                'Servers'         : ["localhost2"],
                'Telecom'         : ["localhost2"],
            },
            'metrology' : {
                'P-F'             : ["localhost2"],
                'Servers'         : ["localhost2"],
                'Telecom'         : ["localhost2"],
            },
        }

        ConfHost(conf.hostsConf, "dummy.xml", "localhost",
                 "127.0.0.1", "Servers")
        df.add_host("localhost")

        # Chargement en base
        df.add_vigiloserver('localhost')
        df.add_vigiloserver('localhost2')
        df.add_supitemgroup("Group1")

        # À l'issue de la ventilation, "localhost" et "localhost2"
        # doivent recevoir la métrologie de "localhost", mais seul
        # "localhost" doit recevoir les changements d'états Nagios.
        ventilation = self.ventilator.ventilate()
        pprint(ventilation)

        # Pour la métrologie et la collecte, on a à chaque fois
        # deux serveurs retenus (un nominal et un backup) par le
        # processus de ventilation.
        conn_metro = self.apps["connector-metro"]
        self.assertEquals(
            ventilation["localhost"][conn_metro],
            ['localhost', 'localhost2']
        )
        nagios = self.apps["nagios"]
        self.assertEquals(
            ventilation["localhost"][nagios],
            ['localhost', 'localhost2']
        )

        # En base, on ne doit retrouver qu'un serveur de supervision (pour le
        # proxy)
        ventilationloader = VentilationLoader(ventilation, self.apps.values())
        ventilationloader.load()
        ventilations = DBSession.query(
                    VigiloServer.name
                ).join(
                    Ventilation,
                    Host,
                    Application,
                ).filter(Host.name == u"localhost"
                ).filter(Application.name == u"connector-metro"
                ).order_by(VigiloServer.name.asc()
                ).all()
        ventilations = sorted([vs.name for vs in ventilations])
        self.assertEquals(
            ventilations,
            [u'localhost', ]
        )

    def test_ventilator_repartition(self):
        """Teste l'homogénéité de l'algorithme de ventilation."""
        # Un seul groupe de supervision, pas de backup.
        conf.appsGroupsByServer = {'collect': {'P-F': []}}
        conf.appsGroupsBackup = {'collect': {'P-F': []}}
        conf.hostfactory.hosts = {}
        conf.hostsConf = conf.hostfactory.hosts

        # Différents paramètres du test, complètement arbitraires,
        # mais suffisamment grands je l'espère pour être représentatifs.
        nb_vigiloservers = random.randint(2, 20)
        nb_hosts = 1000
        max_length = 64
        diff_threshold = 5

        # On génère un certain nombre de serveurs de supervision.
        for i in xrange(nb_vigiloservers):
            conf.appsGroupsByServer['collect']['P-F'].append('test-%d' % i)
            df.add_vigiloserver('test-%d' % i)

        # Alphabet des caractères autorisés dans un nom d'hôte.
        # NON, l'underscore (_) n'est pas autorisé d'après les RFC.
        alphabet = string.letters + string.digits + '.-'

        # On génère un grand nombre d'hôtes.
        for i in xrange(nb_hosts):
            # Génère un nom d'hôte de taille aléatoire.
            hostname = "".join([random.choice(alphabet)
                for j in xrange(random.randint(0, max_length))])

            # On les ajoute dans la base de données
            # et dans le groupe de supervision "P-F".
            df.add_host(hostname)
            conf.hostsConf[hostname] = {'serverGroup': 'P-F'}

        # À l'issue de la ventilation, "localhost" et "localhost2"
        # doivent recevoir la métrologie de "localhost", mais seul
        # "localhost" doit recevoir les changements d'états Nagios.
        ventilation = self.ventilator.ventilate()
        nagios = self.apps["nagios"]

        # On calcule le nombre d'hôtes supervisé par chaque serveur.
        stats = {}
        for i in xrange(nb_vigiloservers):
            stats['test-%d' % i] = 0
        for host, v in ventilation.iteritems():
            stats[v[nagios][0]] += 1

        avg = nb_hosts / float(nb_vigiloservers)

        # Si on observe un écart trop important par rapport à la moyenne,
        # l'algorithme a échoué.
        for i in xrange(nb_vigiloservers):
            delta = math.sqrt(
                (stats['test-%d' % i] - avg) *
                (stats['test-%d' % i] - avg))
            self.failUnless(
                delta < nb_hosts * diff_threshold / 100.,
                "Delta (%f) is > %f10%%" % (delta, diff_threshold)
            )


    def test_orphan_servers(self):
        """
        Si une app n'est plus déployée sur un serveur, il faut l'arrêter
        """
        conf.appsGroupsByServer = {
            'collect' : {
                'P-F'             : ['localhost'],
                'Servers'         : ['localhost'],
                'Telecom'         : ['localhost'],
            },
            'metrology' : {
                'P-F'             : ['localhost'],
                'Servers'         : ['localhost'],
                'Telecom'         : ['localhost'],
            },
        }
        # besoin de localhost en base
        ConfHost(conf.hostsConf, "dummy.xml", "localhost",
                        "127.0.0.1", "P-F")
        df.add_host("localhost")
        # chargement des apps
        nagios = self.apps["nagios"]
        nagios.servers["localhost"] = ServerLocal("localhost")
        nagios.actions["localhost"] = ["stop", "start"]
        df.add_vigiloserver('localhost')
        ventilation = self.ventilator.ventilate()
        assert ventilation["localhost"][nagios] == ["localhost", ]
        ventilationloader = VentilationLoader(ventilation, self.apps.values())
        ventilationloader.load()
        #DBSession.flush()
        # on supprime les serveurs Nagios pour le groupe P-F
        conf.appsGroupsByServer["collect"]["P-F"] = []
        ventilation = self.ventilator.ventilate()
        assert nagios not in ventilation["localhost"]
        #from pprint import pprint; pprint(ventilation)
        ventilationloader = VentilationLoader(ventilation, self.apps.values())
        ventilationloader.load()
        self.assertEqual(nagios.actions["localhost"], ["stop"])

    def test_servers_for_app(self):
        nagios = Nagios()
        ventilation = {
                "dummy1": {nagios: ["vsrv1", "vsrv2"]},
                "dummy2": {nagios: ["vsrv3", "vsrv4"]},
                }
        result = self.ventilator.servers_for_app(ventilation, nagios)
        self.assertEqual(sorted(list(result)), ["vsrv1", "vsrv3"])

if __name__ == '__main__':
    unittest.main()