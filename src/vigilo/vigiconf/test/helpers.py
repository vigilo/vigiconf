# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import os, shutil
import tempfile

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
    settings["vigiconf"]["confdir"] = os.path.join(os.path.dirname(__file__),
                                                   "testdata", subdir)

def reload_conf(hostsdir=None):
    """We changed the paths, reload the factories"""
    from vigilo.vigiconf.loaders.group import GroupLoader
    conf.testfactory.__init__()
    conf.hosttemplatefactory.__init__(conf.testfactory)
    conf.hosttemplatefactory.load_templates()
    if not hostsdir:
        hostsdir = os.path.join(settings["vigiconf"].get("confdir"), "hosts")
    conf.hostfactory.__init__(
            hostsdir,
            conf.hosttemplatefactory,
            conf.testfactory,
      )
    conf.hostsConf = conf.hostfactory.hosts
    GroupLoader().load()
    #conf.loadConf()

def setup_tmpdir():
    """Prepare the temporary directory"""
    tmpdir = tempfile.mkdtemp(prefix="tests-vigiconf-")
    settings["vigiconf"]["libdir"] = tmpdir
    conf.LIBDIR = tmpdir
    return tmpdir

#Create an empty database before we start our tests for this module
def setup_db():
    """Crée toutes les tables du modèle dans la BDD."""
    #tmpdir = tempfile.mkdtemp(prefix="tests-vigiconf-")
    #settings["database"]["sqlalchemy_url"] = "sqlite:///%s/vigilo.db" % tmpdir
    transaction.abort()

    # La vue GroupPath dépend de Group et GroupHierarchy.
    # SQLAlchemy ne peut pas détecter correctement la dépendance.
    # On crée le schéma en 2 fois pour contourner ce problème.
    from vigilo.models.tables.grouppath import GroupPath
    mapped_tables = metadata.tables.copy()
    del mapped_tables[GroupPath.__tablename__]
    metadata.create_all(tables=mapped_tables.itervalues())
    metadata.create_all(tables=[GroupPath.__table__])

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
        self.force = True

    def status(self):
        # On indique qu'aucun changement n'a eu lieu,
        # car le fait de positionner le flag "force"
        # force de toutes façons les opérations.
        return {'toadd': [], 'added': [],
                'toremove': [], 'removed': [], 'modified': []}

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

#from vigilo.vigiconf.lib.dispatchator.base import Dispatchator
#class DummyDispatchator(Dispatchator):
#    def __init__(self):
#        self.force = True
#
#    def get_svn_status(self):
#        # On indique qu'aucun changement n'a eu lieu,
#        # car le fait de positionner le flag "force"
#        # force de toutes façons les opérations.
#        return {'toadd': [], 'added': [],
#                'toremove': [], 'removed': [], 'modified': []}
