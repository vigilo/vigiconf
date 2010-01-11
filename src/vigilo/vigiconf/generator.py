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
        if not settings.get("SILENT", False):
            sys.stdout.write("\n".join(v.getSummary(details=True, stats=True)
                                      +['']))
            sys.stdout.write("Generation Successful\n")
        return True

if __name__ == "__main__":
    #from pprint import pprint; pprint(globals())
    conf.loadConf()
    _gendir = os.path.join(conf.LIBDIR, "deploy")
    os.system("rm -rf %s/*" % _gendir)
    if 0:
        import hotshot, hotshot.stats
        _prof = hotshot.Profile("/tmp/generator.prof")
        _prof.runcall(generate, _gendir)
        _prof.close()
        _stats = hotshot.stats.load("/tmp/generator.prof")
        _stats.strip_dirs()
        _stats.sort_stats('time', 'calls')
        _stats.print_stats(20)
    else:
        if not generate(_gendir):
            sys.exit(1)


# vim:set expandtab tabstop=4 shiftwidth=4: