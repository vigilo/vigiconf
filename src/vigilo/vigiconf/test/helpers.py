# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import print_function
import os
import sys
import shutil
import tempfile
import stat

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_')

from vigilo.models.session import metadata, DBSession
from vigilo.models.tables import StateName, MapGroup

import vigilo.vigiconf.conf as conf

# test postgres: appeler abort() avant teardown
import transaction

TESTDATADIR = os.path.join(os.path.dirname(__file__), "testdata")

def setUpModule(self):
    """Call once, before loading all the test cases."""
    setup_path()
    self.testdatadir = os.path.join(os.path.dirname(__file__), "testdata")

def setup_path(subdir=None):
    conf.CODEDIR = os.path.join(os.path.dirname(__file__), "..", "src",
            "vigilo", "vigiconf")
    if subdir is None:
        subdir = "conf.d"
    old_path = settings["vigiconf"]["confdir"]
    settings["vigiconf"]["confdir"] = os.path.join(os.path.dirname(__file__),
                                                   "testdata", subdir)
    return old_path

def setup_tmpdir():
    """Prepare the temporary directory"""
    tmpdir = tempfile.mkdtemp(prefix="tests-vigiconf-")
    mode755 = (stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
               stat.S_IRGRP | stat.S_IXGRP |
               stat.S_IROTH | stat.S_IXOTH)
    os.chmod(tmpdir, mode755) # accès utilisateur nagios
    settings["vigiconf"]["libdir"] = tmpdir
    conf.LIBDIR = tmpdir
    return tmpdir

#Create an empty database before we start our tests for this module
def setup_db():
    """Crée toutes les tables du modèle dans la BDD."""
    #tmpdir = tempfile.mkdtemp(prefix="tests-vigiconf-")
    #settings["database"]["sqlalchemy_url"] = "sqlite:///%s/vigilo.db" % tmpdir
    transaction.abort()

    # On crée les tables, puis les vues.
    mapped_tables = metadata.tables.copy()
    views = {}
    for tablename in mapped_tables:
        info = mapped_tables[tablename].info or {}
        if info.get('vigilo_view'):
            views[tablename] = mapped_tables[tablename]
    for view in views:
        del mapped_tables[view]

    metadata.create_all(tables=mapped_tables.itervalues())
    metadata.create_all(tables=views.values())

    DBSession.add(StateName(statename=u'OK', order=1))
    DBSession.add(StateName(statename=u'UNKNOWN', order=2))
    DBSession.add(StateName(statename=u'WARNING', order=3))
    DBSession.add(StateName(statename=u'CRITICAL', order=4))
    DBSession.add(StateName(statename=u'UP', order=1))
    DBSession.add(StateName(statename=u'UNREACHABLE', order=2))
    DBSession.add(StateName(statename=u'DOWN', order=4))
    MapGroup(name=u'Root')
    DBSession.flush()

#Teardown that database
def teardown_db():
    """Supprime toutes les tables du modèle de la BDD."""
    # pour postgres, sinon ça bloque
    transaction.abort()
    metadata.drop_all()
    #tmpdir = settings["database"]["sqlalchemy_url"].split("/")[3:-1]
    #shutil.rmtree("/".join(tmpdir))


def setup_deploy_dir():
    """ setup des tests dispatchator
    """
    # Prepare necessary directories
    # TODO: commenter les divers repertoires
    gendir = settings["vigiconf"].get("libdir")
    #shutil.rmtree(gendir, ignore_errors=True)
    #os.mkdir(gendir)

    basedir = os.path.join(gendir, "deploy")
    os.mkdir(basedir)
    conf.baseConfDir = os.path.join(gendir, "vigiconf-conf")
    os.mkdir(conf.baseConfDir)
    for dir in [ "new", "old", "prod" ]:
        os.mkdir( os.path.join(conf.baseConfDir, dir) )
    # Create necessary files
    os.mkdir( os.path.join(gendir, "revisions") )
    revs = open( os.path.join(gendir, "revisions", "localhost.revisions"), "w")
    revs.close()
    os.mkdir( os.path.join(basedir, "localhost") )
    revs = open( os.path.join(basedir, "localhost", "revisions.txt"), "w")
    revs.close()
    # We changed the paths, reload the factories
    #reload_conf()

def teardown_deploy_dir():
    """ teardown des tests dispatchator
    """
    #shutil.rmtree(settings["vigiconf"].get("libdir"))
    opts = ["libdir", "targetconfdir", "lockfile"]
    for d in [ settings["vigiconf"][o] for o in opts ]:
        if os.path.exists(d):
            shutil.rmtree(d)

from vigilo.vigiconf.lib.dispatchator.revisionmanager import RevisionManager
class DummyRevMan(RevisionManager):
    def __init__(self):
        self.force = ("deploy", "db-sync")
        # On indique qu'aucun changement n'a eu lieu,
        # car le fait de positionner le flag "force"
        # force de toutes façons les opérations.
        self.dummy_status = {'added': [], 'removed': [], 'modified': []}

    def status(self):
        return self.dummy_status

from vigilo.vigiconf.lib.systemcommand import SystemCommand
class DummyCommand(SystemCommand):
    def execute(self):
        return self.getCommand()

class LoggingCommand(SystemCommand):
    def __init__(self, command, logger, result=None):
        super(LoggingCommand, self).__init__(command)
        self.logger = logger
        self.result = result

    def execute(self):
        self.logger.append(self.getCommand())
        if self.result is None:
            return super(LoggingCommand, self).execute()
        else:
            self.mResult = [ self.result, "" ] # stdout, stderr
            return self.mResult

class LoggingCommandFactory(object):
    def __init__(self, simulate=False):
        self.executed = []
        self.simulate = simulate
    def __call__(self, command):
        if self.simulate:
            result = ""
        else:
            result = None
        return LoggingCommand(command, self.executed, result)



from unittest import TestCase
from subprocess import Popen, PIPE, STDOUT
from vigilo.models.tables import ConfFile
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from vigilo.vigiconf.lib.confclasses.host import Host
from vigilo.vigiconf.lib.generators import GeneratorManager
from vigilo.models.demo.functions import add_host

class GeneratorBaseTestCase(TestCase):
    """Classe de base pour les tests de génération"""

    def setUp(self):
        setup_db()
        conf.hostsConf = {}
        # Prepare temporary directory
        self.tmpdir = setup_tmpdir()
        self.basedir = os.path.join(self.tmpdir, "deploy")
        self.old_conf_path = settings["vigiconf"]["confdir"]
        settings["vigiconf"]["confdir"] = os.path.join(self.tmpdir, "conf.d")
        os.mkdir(settings["vigiconf"]["confdir"])
        self.testfactory = TestFactory(confdir=settings["vigiconf"]["confdir"])
        self.host = Host(conf.hostsConf, "dummy.xml", "testserver1",
                         "192.168.1.1", "Servers")
        self.host.set_attribute("collectorTimeout", "3")
        # attention, le fichier dummy.xml doit exister ou l'hôte sera supprimé
        # juste après avoir été inséré
        open(os.path.join(self.tmpdir, "conf.d", "dummy.xml"), "w").close()
        conffile = ConfFile.get_or_create("dummy.xml")
        add_host("testserver1", conffile)
        self.apps = self._get_apps()
        self.genmanager = GeneratorManager(self.apps.values())
        self.substitutions = {
            'nagios_bin': 'nagios',
            'nagios_svc': 'nagios',
            'targetconfdir': '/etc/vigilo/vigiconf/',
            'nagios_cfg': '/etc/nagios/nagios.cfg',
        }

    def tearDown(self):
        DBSession.expunge_all()
        teardown_db()
        shutil.rmtree(self.tmpdir)
        settings["vigiconf"]["confdir"] = self.old_conf_path
        conf.hostsConf = {}

    def _get_apps(self):
        """
        Dictionnaire des instances d'applications à tester.
        Exemple: {"nagios": Nagios(), "vigimap": VigiMap()}
        """
        return {}

    def _generate(self):
        self.genmanager.generate(DummyRevMan())

    def _validate(self):
        deploydir = os.path.join(self.basedir, "localhost")
        for appname, app in self.apps.iteritems():
            __import__(app.__module__)
            module = sys.modules[app.__module__]
            validation_script = os.path.join(
                    os.path.dirname(module.__file__),
                    "validate.sh")
            fh = open(validation_script, 'r')
            contents = fh.read()
            fh.close()
            contents = contents % {
            }
            validation_script = os.path.join(self.tmpdir, "validate.sh")
            fh = open(validation_script, 'w')
            fh.write(contents % self.substitutions)
            fh.close()
            print(appname)
            proc = Popen(["sh", validation_script, deploydir],
                        stdout=PIPE, stderr=STDOUT)
            print(proc.communicate()[0])
            self.assertEqual(proc.returncode, 0)
