# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import os
import tempfile

import vigilo.vigiconf.conf as conf

from vigilo.models.session import DBSession

from vigilo.models.vigilo_bdd_config import metadata

metadata.bind = DBSession.bind

#testdatadir = None

def setUpModule(self):
    """Call once, before loading all the test cases."""
    setup_path()
    self.testdatadir = os.path.join(os.path.dirname(__file__), "testdata")

def setup_path():
    conf.CODEDIR = os.path.join(os.path.dirname(__file__), "..", "src",
            "vigilo", "vigiconf")
    conf.CONFDIR = os.path.join(conf.CODEDIR, "conf.d")

def reload_conf():
    """We changed the paths, reload the factories"""
    conf.testfactory.__init__()
    conf.hosttemplatefactory.__init__(conf.testfactory)
    conf.hosttemplatefactory.load_templates()
    conf.hostfactory.__init__(
            os.path.join(conf.CONFDIR, "hosts"),
            conf.hosttemplatefactory,
            conf.testfactory,
            conf.groupsHierarchy,
      )
    conf.loadConf()

def setup_tmpdir():
    """Prepare the temporary directory"""
    tmpdir = tempfile.mkdtemp(dir="/dev/shm", prefix="tests-vigiconf")
    conf.LIBDIR = tmpdir
    return tmpdir

#Create an empty database before we start our tests for this module
def setup_db():
    """Crée toutes les tables du modèle dans la BDD."""
    metadata.create_all()
    
#Teardown that database 
def teardown_db():
    """Supprime toutes les tables du modèle de la BDD."""
    metadata.drop_all()
