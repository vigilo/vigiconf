#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from . import conf
from .lib.validator import Validator
from . import generators

# module d'export base de données
from .dbexportator import update_apps_db, export_conf_db, export_ventilation_DB

import transaction

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

def generate(commit_db=False):
    """ Main routine of this module, produces the configuration files.
    
    TODO: implementer l'option commit db.
    
    @param gendir generation directory
    @type gendir C{str}
    @param commit_db True means that data is commited in the database
           after generation; if False, a rollback is done.
    @type commit_db C{boolean}
    @return: True if sucessful, False otherwise
    @rtype: C{boolean}
    """
    
    # mise à jour de la liste des application en base
    update_apps_db()

    # mise à jour de la base de données
    export_conf_db()

    h = getventilation()

    # export de la ventilation en base de données
    export_ventilation_DB(h)

    v = Validator(h)
    if not v.preValidate():
        for errmsg in v.getSummary(details=True, stats=True):
            LOGGER.error(errmsg)
        LOGGER.error(_("Generation failed!"))
        return False
    genmanager = generators.GeneratorManager()
    genmanager.generate(h, v)
            
    if v.hasErrors():
        for errmsg in v.getSummary(details=True, stats=True):
            LOGGER.error(errmsg)
        LOGGER.error(_("Generation failed!"))
        if commit_db:
            transaction.abort()
            LOGGER.debug(_("Transaction rollbacked"))
        return False
    else:
        try:
            if commit_db:
                transaction.commit()
                LOGGER.debug(_("Transaction commited"))
            else:
                transaction.abort()
                LOGGER.debug(_("Transaction rollbacked"))
        except Exception, v:
            transaction.abort()
            LOGGER.debug(_("Transaction rollbacked"))
            return False

        for msg in v.getSummary(details=True, stats=True):
            LOGGER.info(msg)
        LOGGER.info(_("Generation successful"))
        return True

if __name__ == "__main__":
    #from pprint import pprint; pprint(globals())
    conf.loadConf()
    _gendir = os.path.join(settings["vigiconf"].get("libdir"), "deploy")
    os.system("rm -rf %s/*" % _gendir)
    if 0:
        import hotshot, hotshot.stats
        _prof = hotshot.Profile("/tmp/generator.prof")
        _prof.runcall(generate)
        _prof.close()
        _stats = hotshot.stats.load("/tmp/generator.prof")
        _stats.strip_dirs()
        _stats.sort_stats('time', 'calls')
        _stats.print__stats(20)
    else:
        if not generate():
            sys.exit(1)


# vim:set expandtab tabstop=4 shiftwidth=4:
