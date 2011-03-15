
import os
import shutil

from vigilo.common.conf import settings
settings.load_module(__name__)

def teardown():
    opts = ["libdir", "targetconfdir", "lockfile"]
    for d in [ settings["vigiconf"][o] for o in opts ]:
        if os.path.exists(d):
            shutil.rmtree(d)