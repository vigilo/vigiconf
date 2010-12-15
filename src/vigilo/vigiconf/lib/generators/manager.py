# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2011 CS-SI
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
Generators for the Vigilo Config Manager
"""

from __future__ import absolute_import

import glob
import os, sys
import os.path
import types

import transaction

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.validator import Validator
from vigilo.vigiconf.lib.loaders import LoaderManager
from vigilo.vigiconf.lib.ventilation import get_ventilator
from .base import Generator


class GeneratorManager(object):
    """
    Handles the generator library.
    @cvar apps: the list of available applications.
    @type apps: C{list}
    """

    genshi_enabled = False

    def __init__(self, apps, dispatchator):
        self.apps = apps
        self.dispatchator = dispatchator
        self.ventilator = get_ventilator(self.apps)
        try:
            self.genshi_enabled = settings['vigiconf'].as_bool(
                                    'enable_genshi_generation')
        except KeyError:
            self.genshi_enabled = False

    def run_all_generators(self, ventilation, validator):
        """
        Execute la méthode I{generate()} de la classe pointée par l'attribut
        I{generate} de chaque application
        """
        vba = self.ventilator.ventilation_by_appname(ventilation)
        LOGGER.debug("Generating configuration")
        for app in self.apps:
            if not app.generator:
                continue
            generator = app.generator(app, vba, validator)
            generator.generate()
            generator.write_scripts()

    def generate(self, commit_db=False):
        """
        Main method of this class, produces the configuration files.

        @param commit_db: True means that data is commited in the database
               after generation; if False, a rollback is done.
        @type commit_db: C{boolean}
        @return: True if sucessful, False otherwise
        @rtype: C{boolean}
        @TODO: lever des exceptions plutôt que de retourner False
        """

        LOGGER.debug("Syncing with database")
        loader = LoaderManager(self.dispatchator)
        loader.load_apps_db(self.apps)
        loader.load_conf_db()
        loader.load_vigilo_servers_db()
        ventilation = self.ventilator.ventilate()
        loader.load_ventilation_db(ventilation)

        validator = Validator(ventilation)
        if not validator.preValidate():
            # TODO: exception
            for errmsg in validator.getSummary(details=True, stats=True):
                LOGGER.error(errmsg)
            LOGGER.error(_("Generation failed!"))
            return False

        self.run_all_generators(ventilation, validator)

        if validator.hasErrors():
            # TODO: exception
            for errmsg in validator.getSummary(details=True, stats=True):
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
                # TODO: exception
                transaction.abort()
                LOGGER.debug(_("Transaction rollbacked"))
                return False

            for msg in validator.getSummary(details=True, stats=True):
                LOGGER.info(msg)
            LOGGER.info(_("Generation successful"))
            return True
