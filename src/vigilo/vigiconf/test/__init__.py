# vim: fileencoding=utf-8 sw=4 ts=4 et ai
# Copyright (C) 2011-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import os
import shutil

os.environ['VIGILO_SETTINGS'] = 'settings_tests.ini'
from vigilo.common.conf import settings
settings.load_module(__name__)

def teardown():
    opts = ["libdir", "targetconfdir", "lockfile"]
    for d in [ settings["vigiconf"][o] for o in opts ]:
        if os.path.isdir(d):
            shutil.rmtree(d)
        elif os.path.exists(d):
            os.remove(d)
