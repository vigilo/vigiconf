# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import os, shutil
import tempfile

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_',
    settings['database']['db_basename'])

from vigilo.models.session import metadata, DBSession
from vigilo.models.tables import VigiloServer, StateName
from vigilo.vigiconf.loaders.group import GroupLoader
from vigilo.vigiconf.lib.dispatchator import Dispatchator

import vigilo.vigiconf.conf as conf

# test postgres: appeler abort() avant teardown
import transaction


def setUpModule(self):
    """Call once, before loading all the test cases."""
    setup_path()
    self.testdatadir = os.path.join(os.path.dirname(__file__), "testdata")

def setup_path():
    conf.CODEDIR = os.path.join(os.path.dirname(__file__), "..", "src",
            "vigilo", "vigiconf")
    settings["vigiconf"]["confdir"] = os.path.join(os.path.dirname(__file__),
                                                   "testdata", "conf.d")

def reload_conf(hostsdir=None):
    """We changed the paths, reload the factories"""
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
    GroupLoader().load()
    conf.loadConf()

def setup_tmpdir(dirpath=None):
    """Prepare the temporary directory"""
    #if not dirpath:
    #    dirpath = tempfile.mkdtemp(dir="/dev/shm", prefix="tests-vigiconf")
    #tmpdir = dirpath
    tmpdir = settings["vigiconf"].get("libdir")
    conf.LIBDIR = tmpdir
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)
    return tmpdir

#Create an empty database before we start our tests for this module
def setup_db():
    """Crée toutes les tables du modèle dans la BDD."""
    metadata.create_all()
    DBSession.add(StateName(statename=u'OK', order=1))
    DBSession.add(StateName(statename=u'UNKNOWN', order=2))
    DBSession.add(StateName(statename=u'WARNING', order=3))
    DBSession.add(StateName(statename=u'CRITICAL', order=4))
    DBSession.add(StateName(statename=u'UP', order=1))
    DBSession.add(StateName(statename=u'UNREACHABLE', order=2))
    DBSession.add(StateName(statename=u'DOWN', order=4))
    DBSession.flush()

#Teardown that database
def teardown_db():
    """Supprime toutes les tables du modèle de la BDD."""
    # pour postgres, sinon ça bloque
    transaction.abort()

    metadata.drop_all()


def setup_deploy_dir():
    """ setup des tests dispatchator
    """
    # Prepare necessary directories
    # TODO: commenter les divers repertoires
    gendir = settings["vigiconf"].get("libdir")
    shutil.rmtree(gendir, ignore_errors=True)
    os.mkdir(gendir)

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
    reload_conf()

def teardown_deploy_dir():
    """ teardown des tests dispatchator
    """
    shutil.rmtree(settings["vigiconf"].get("libdir"))

class DummyDispatchator(Dispatchator):
    def __init__(self, added=None, removed=None, modified=None):
        if added is None:
            added = []
        if removed is None:
            removed = []
        if modified is None:
            modified = []
        self._svn_status = {
            'add': added,
            'remove': removed,
            'modified': modified,
        }

    def get_svn_status(self):
        return self._svn_status
