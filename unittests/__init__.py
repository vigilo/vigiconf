# vim: set fileencoding=utf-8 sw=4 ts=4 et :

import os
import tempfile

import conf

#testdatadir = None

def setUpModule(self):
    """Call once, before loading all the test cases."""
    setup_path()
    conf.simulate = True
    conf.silent = True
    self.testdatadir = os.path.join(os.path.dirname(__file__), "testdata")

def setup_path():
    conf.confDir = os.path.join(os.path.dirname(__file__), "..", "src", "conf.d")
    conf.templatesDir = os.path.join(conf.confDir,"filetemplates")
    conf.dataDir = os.path.join(os.path.dirname(__file__), "..", "src")

def reload_conf():
    """We changed the paths, reload the factories"""
    conf.hosttemplatefactory.__init__()
    conf.hosttemplatefactory.load_templates()
    conf.testfactory.__init__()
    conf.loadConf()

def setup_tmpdir():
    """Prepare the temporary directory"""
    tmpdir = tempfile.mkdtemp(dir="/dev/shm")
    conf.libDir = tmpdir
    return tmpdir

