################################################################################
#
# ConfigMgr configuration files generation wrapper
# Copyright (C) 2007-2009 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
################################################################################
"""
This is the generator of ConfMgr.

It reads a configuration as Python dicts by invoking the conf module (see its
doc), dynamically sources the generators available (as Python files available
in the generators directory) make sure every host of the configuration is
handled by a monitoring server, by invoking the ventilator module (see its
documentation), and launches all generators with both pieces of data.
"""

from __future__ import absolute_import

import os
import sys

from vigilo.common.conf import settings
settings.load_module(__name__)

from . import conf
from .lib.validator import Validator
from . import generators

__docformat__ = "epytext"


def getventilation():
    """Wrapper for the ventilator"""
    if hasattr(conf, "appsGroupsByServer"):
        try:
            from .lib import ventilator
        except ImportError:
            # Community Edition, ventilator is not available.
            return get_local_ventilation()
        return ventilator.findAServerForEachHost()
    else:
        return get_local_ventilation()

def get_local_ventilation():
    """Map every app to localhost (Community Edition)"""
    mapping = {}
    for host in conf.hostsConf.keys():
        mapping[host] = {}
        for app in conf.apps:
            mapping[host][app] = "localhost"
    return mapping

def generate(gendir):
    """
    Main routine of this module, produces the configuration files.
    @return: True if sucessful, False otherwise.
    """
    h = getventilation()
    v = Validator(h)
    if not v.preValidate():
        sys.stderr.write("\n".join(v.getSummary(details=True, stats=True)))
        sys.stderr.write("Generation Failed!!\n")
        return False
    genmanager = generators.GeneratorManager()
    genmanager.generate(gendir, h, v)
    if v.hasErrors():
        sys.stderr.write("\n".join(v.getSummary(details=True, stats=True)+['']))
        sys.stderr.write("Generation Failed!!\n")
        return False
    else:
        if not settings["vigiconf"].get("silent", False):
            sys.stdout.write("\n".join(v.getSummary(details=True, stats=True)
                                      +['']))
            sys.stdout.write("Generation Successful\n")
        return True

if __name__ == "__main__":
    #from pprint import pprint; pprint(globals())
    conf.loadConf()
    __gendir = os.path.join(settings["vigiconf"].get("libdir"), "deploy")
    os.system("rm -rf %s/*" % __gendir)
    if 0:
        import hotshot, hotshot.stats
        __prof = hotshot.Profile("/tmp/generator.prof")
        __prof.runcall(generate, __gendir)
        __prof.close()
        __stats = hotshot.stats.load("/tmp/generator.prof")
        __stats.strip_dirs()
        __stats.sort_stats('time', 'calls')
        __stats.print__stats(20)
    else:
        if not generate(__gendir):
            sys.exit(1)


# vim:set expandtab tabstop=4 shiftwidth=4:
