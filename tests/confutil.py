# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import os
import tempfile

from vigilo.common.conf import settings
settings.load_module(__name__)
from vigilo.models.configure import metadata, DBSession, configure_db

import vigilo.vigiconf.conf as conf



def setUpModule(self):
    """Call once, before loading all the test cases."""
    setup_path()
    self.testdatadir = os.path.join(os.path.dirname(__file__), "testdata")

def setup_path():
    conf.CODEDIR = os.path.join(os.path.dirname(__file__), "..", "src",
            "vigilo", "vigiconf")
    settings["vigiconf"]["confdir"] = os.path.join(conf.CODEDIR, "conf.d")

def reload_conf():
    """We changed the paths, reload the factories"""
    conf.testfactory.__init__()
    conf.hosttemplatefactory.__init__(conf.testfactory)
    conf.hosttemplatefactory.load_templates()
    conf.hostfactory.__init__(
            os.path.join(settings["vigiconf"].get("confdir"), "hosts"),
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
    from ConfigParser import SafeConfigParser
    parser = SafeConfigParser()
    parser.read('settings_tests.ini')

    settings = dict(parser.items('database'))

    configure_db(settings, 'sqlalchemy.')
#    db_basename = settings['db_basename']
    metadata.create_all()
    
#Teardown that database 
def teardown_db():
    """Supprime toutes les tables du modèle de la BDD."""
    metadata.drop_all()
