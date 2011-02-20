#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ventilator test
"""

import string, random, math
import os, unittest, shutil
from pprint import pprint

import vigilo.vigiconf.conf as conf

from helpers import reload_conf, setup_tmpdir
from helpers import setup_db, teardown_db

from sqlalchemy.sql.functions import count

from vigilo.vigiconf.lib import dispatchmodes
from vigilo.vigiconf.lib.ventilation.local import VentilatorLocal
from vigilo.vigiconf.lib.ventilation.remote import VentilatorRemote
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.vigiconf.lib.loaders import LoaderManager
from vigilo.vigiconf.lib import ParsingError
from vigilo.vigiconf.lib.confclasses.host import Host as ConfHost
from vigilo.vigiconf.applications.nagios import Nagios
from vigilo.vigiconf.applications.vigimap import VigiMap
from vigilo.vigiconf.applications.connector_metro import ConnectorMetro

from vigilo.models.session import DBSession

from vigilo.models.tables import Host, Ventilation, Application, \
                                    SupItemGroup, VigiloServer
from vigilo.models.demo.functions import add_host, add_vigiloserver, \
                                            add_supitemgroup

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
        #conf.load_general_conf()
        #dispatchator = dispatchmodes.getinstance()
        #self.generator = GeneratorManager(dispatchator.applications, dispatchator)
        host = ConfHost(conf.hostsConf, "dummy.xml", "testserver1",
                        "192.168.1.1", "Servers")
        host = add_host("testserver1")
        self.apps = [Nagios(), VigiMap(), ConnectorMetro()]
        self.ventilator = VentilatorRemote(self.apps)
        self.ventilator_local = VentilatorLocal(self.apps)

    def tearDown(self):
        """Call after every test case."""
        teardown_db()
        DBSession.expunge_all()
        shutil.rmtree(self.tmpdir)


    def test_export_localventilation_db(self):
        """ test de l'export de la ventilation en mode local.

        le remplacement de la persistance pickle par db n'est pas testée
        ici.
        """
        ventilation = self.ventilator_local.ventilate()
        num_apps = len(ventilation['testserver1'])

        # need localhost as VigiloServer
        add_vigiloserver(u'localhost')

        #need apps in DB
        dispatchator = dispatchmodes.getinstance()
        loader = LoaderManager(dispatchator)
        loader.load_apps_db(self.apps)
        DBSession.flush()
        self.assertEquals(DBSession.query(Application).count(), num_apps,
                "There should be %d apps in DB" % num_apps)

        loader.load_vigilo_servers_db()
        loader.load_ventilation_db(ventilation, self.apps)

        # check that for each app, localhost is supervised by itself
        print ventilation
        host = add_host("testserver1")
        for app in self.apps:
            print host, app
            links = DBSession.query(Ventilation
                ).filter(Ventilation.application.has(
                    Application.name == unicode(app))
                ).filter(Ventilation.host==host)
            print links.all()
            self.assertEquals(links.count(), 1,
                              "There should be one supervision link")
            self.assertEquals(links.first().vigiloserver.name, u'localhost',
                              "superviser server must be localhost")

    def test_host_ventilation_group(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        host.groups = [group2,]
        self.ventilator.make_cache()
        self.assertEquals(self.ventilator.get_host_ventilation_group("localhost", {}), "Group1")

    def test_host_ventilation_group_multiple(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        group3 = add_supitemgroup("Group3", group1)
        host.groups = [group2, group3]
        self.ventilator.make_cache()
        self.assertEquals(self.ventilator.get_host_ventilation_group("localhost", {}), "Group1")

    def test_host_ventilation_conflicting_groups(self):
        host = add_host("localhost")
        group1 = add_supitemgroup("Group1")
        group2 = add_supitemgroup("Group2", group1)
        group3 = add_supitemgroup("Group3")
        group4 = add_supitemgroup("Group4", group3)
        host.groups = [group2, group4]
        self.ventilator.make_cache()
        self.assertRaises(ParsingError, self.ventilator.get_host_ventilation_group, "localhost", {})

    def test_reventilate(self):
        """Cas où un serveur est supprimé de la conf"""
        # besoin de localhost en base
        self.host = ConfHost(conf.hostsConf, "hosts/localhost.xml", "localhost",
                             "127.0.0.1", "Servers")
        host = add_host("localhost")
        # chargement des apps
        dispatchator = dispatchmodes.getinstance()
        loader = LoaderManager(dispatchator)
        loader.load_apps_db(self.apps)
        DBSession.flush()
        conf.appsGroupsByServer = {
                "interface": {
                    "P-F":     [u"sup.example.com", u"supserver2.example.com", u"supserver3.example.com"],
                    "Servers": [u"sup.example.com", u"supserver2.example.com", u"supserver3.example.com"],
                },
                "collect": {
                    "P-F":     [u"sup.example.com", u"supserver2.example.com", u"supserver3.example.com"],
                    "Servers": [u"sup.example.com", u"supserver2.example.com", u"supserver3.example.com"],
                },
                "metrology": {
                    "P-F":     [u"sup.example.com", u"supserver2.example.com", u"supserver3.example.com"],
                    "Servers": [u"sup.example.com", u"supserver2.example.com", u"supserver3.example.com"],
                },
        }
        #for appGroup in conf.appsGroupsByServer:
        #    for hostGroup in conf.appsGroupsByServer[appGroup]:
        #        conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver2.example.com')
        #        conf.appsGroupsByServer[appGroup][hostGroup].append(u'supserver3.example.com')
        loader.load_vigilo_servers_db()
        for i in range(9):
            hostname = "localhost%d" % i
            conf.hostsConf[hostname] = conf.hostsConf["localhost"].copy()
            conf.hostsConf[hostname]["name"] = hostname
            add_host(hostname)
        ventilation = self.ventilator.ventilate()
        loader.load_ventilation_db(ventilation, self.apps)
        # On vérifie que des hôtes ont quand même été affectés à supserver3.example.com
        ss3_hosts = []
        for host in ventilation:
            for app in ventilation[host]:
                if "supserver3.example.com" in ventilation[host][app]:
                    ss3_hosts.append(host)
        assert len(ss3_hosts) > 0
        # Et maintenant, on supprime supserver3.example.com
        for appGroup in conf.appsGroupsByServer:
            for hostGroup in conf.appsGroupsByServer[appGroup]:
                conf.appsGroupsByServer[appGroup][hostGroup].remove(u'supserver3.example.com')
        # On reventile
        ventilation = self.ventilator.ventilate()
        loader.load_ventilation_db(ventilation, self.apps)

        # Tout doit avoir été reventilé sur les autres serveurs
        for host in ventilation:
            for app in ventilation[host]:
                self.assertNotEquals(ventilation[host][app],
                        "supserver3.example.com",
                        u"L'hote %s est toujours supervise par un "
                            % host +
                        u"serveur qui a ete supprime")

    def test_ventilation_with_backup(self):
        """La ventilation donne un nominal et un backup pour chaque hôte/fonction."""
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

        host = ConfHost(conf.hostsConf, "dummy.xml", "localhost",
                        "127.0.0.1", "Servers")
        host = add_host("localhost")

        # Chargement des applications et des serveurs de supervision.
        dispatchator = dispatchmodes.getinstance()
        loader = LoaderManager(dispatchator)
        loader.load_apps_db(self.apps)
        loader.load_vigilo_servers_db()
        group1 = add_supitemgroup("Group1")

        # À l'issue de la ventilation, "localhost" et "localhost2"
        # doivent recevoir la métrologie de "localhost", mais seul
        # "localhost" doit recevoir les changements d'états Nagios.
        ventilation = self.ventilator.ventilate()
        conn_metro = [a for a in self.apps if a.name == "connector-metro"][0]
        nagios = [a for a in self.apps if a.name == "nagios"][0]
        pprint(ventilation)

        # Pour la métrologie et la collecte, on a à chaque fois
        # deux serveurs retenus (un nominal et un backup) par le
        # processus de ventilation.
        self.assertEquals(
            ventilation["localhost"][conn_metro],
            ['localhost', 'localhost2']
        )
        self.assertEquals(
            ventilation["localhost"][nagios],
            ['localhost', 'localhost2']
        )

        # En base, on ne doit retrouver qu'un serveur de supervision (pour le proxy)
        loader.load_ventilation_db(ventilation, self.apps)
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
        conf.hostsConf = {}

        # Différents paramètres du test, complètement arbitraires,
        # mais suffisamment grands je l'espère pour être représentatifs.
        nb_vigiloservers = random.randint(2, 20)
        nb_hosts = 1000
        max_length = 64
        diff_threshold = 5

        # On génère un certain nombre de serveurs de supervision.
        for i in xrange(nb_vigiloservers):
            conf.appsGroupsByServer['collect']['P-F'].append('test-%d' % i)

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
            add_host(hostname)
            conf.hostsConf[hostname] = {'serverGroup': 'P-F'}

        # Chargement des applications et des serveurs de supervision.
        dispatchator = dispatchmodes.getinstance()
        loader = LoaderManager(dispatchator)
        loader.load_apps_db(self.apps)
        loader.load_vigilo_servers_db()

        # À l'issue de la ventilation, "localhost" et "localhost2"
        # doivent recevoir la métrologie de "localhost", mais seul
        # "localhost" doit recevoir les changements d'états Nagios.
        ventilation = self.ventilator.ventilate()
        nagios = [a for a in self.apps if a.name == "nagios"][0]

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
        host = ConfHost(conf.hostsConf, "dummy.xml", "localhost",
                        "127.0.0.1", "P-F")
        host = add_host("localhost")
        conf.load_general_conf()
        # chargement des apps
        dispatchator = dispatchmodes.getinstance()
        apps = dict([(app.name, app) for app in self.apps])
        apps["nagios"].servers["localhost"] = ["stop", "start"]
        loader = LoaderManager(dispatchator)
        loader.load_apps_db(self.apps)
        loader.load_vigilo_servers_db()
        ventilation = self.ventilator.ventilate()
        assert ventilation["localhost"][apps["nagios"]] == ["localhost", ]
        loader.load_ventilation_db(ventilation, self.apps)
        DBSession.flush()
        # on supprime les serveurs Nagios pour le groupe P-F
        conf.appsGroupsByServer["collect"]["P-F"] = []
        ventilation = self.ventilator.ventilate()
        assert apps["nagios"] not in ventilation["localhost"]
        #from pprint import pprint; pprint(ventilation)
        loader.load_ventilation_db(ventilation, self.apps)
        self.assertEqual(apps["nagios"].servers["localhost"], ["stop"])


if __name__ == '__main__':
    unittest.main()
