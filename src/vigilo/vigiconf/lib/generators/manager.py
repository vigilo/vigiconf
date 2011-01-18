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

from vigilo.models.tables import LowLevelService

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib import VigiConfError
from vigilo.vigiconf.lib.validator import Validator
from vigilo.vigiconf.lib.loaders import LoaderManager
from vigilo.vigiconf.lib.ventilation import get_ventilator
from .base import Generator


class GenerationError(VigiConfError):
    """
    Exception remontée quand il y a eu une erreur à la génération
    """
    pass


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
            LOGGER.debug("Generating configuration for %s" % app.name)
            generator = app.generator(app, vba, validator)
            generator.generate()
            generator.write_scripts()
        LOGGER.debug("Configuration generated")

    def generate(self, commit_db=False, nosyncdb=False):
        """
        Main method of this class, produces the configuration files.

        @param commit_db: True means that data is commited in the database
               after generation; if False, a rollback is done.
        @type commit_db: C{boolean}
        @raise L{GenerationError}
        """

        loader = LoaderManager(self.dispatchator)
        if not nosyncdb:
            LOGGER.debug("Syncing with database")
            loader.load_apps_db(self.apps)
            loader.load_conf_db()
            loader.load_vigilo_servers_db()
        ventilation = self.ventilator.ventilate()
        LOGGER.debug("Loading ventilation in DB")
        loader.load_ventilation_db(ventilation)

        LOGGER.debug("Validating ventilation")
        validator = Validator(ventilation)
        if not validator.preValidate():
            for errmsg in validator.getSummary(details=True, stats=True):
                LOGGER.error(errmsg)
            raise GenerationError("prevalidation")

        LOGGER.debug("Moving metro services")
        self.move_metro_services(ventilation, validator)
        LOGGER.info(_("Running generators"))
        self.run_all_generators(ventilation, validator)

        if validator.hasErrors():
            for errmsg in validator.getSummary(details=True, stats=True):
                LOGGER.error(errmsg)
            if commit_db:
                transaction.abort()
                LOGGER.debug("Transaction rollbacked")
            raise GenerationError("validation")
        else:
            try:
                if commit_db:
                    transaction.commit()
                    LOGGER.debug("Transaction commited")
                else:
                    transaction.abort()
                    LOGGER.debug("Transaction rollbacked")
            except Exception, v:
                transaction.abort()
                LOGGER.debug("Transaction rollbacked")
                raise GenerationError("db commit")

            for msg in validator.getSummary(details=True, stats=True):
                LOGGER.info(msg)

    def move_metro_services(self, ventilation, validator):
        """
        On transforme les services sur la métrologie en services reroutés sur
        le serveur de métro. On ne peut pas le faire plus tôt parce qu'on a pas
        accès à la ventilation.
        On règle au passage le reRoutedBy sur le service d'origine.
        """
        vba = self.ventilator.ventilation_by_appname(ventilation)
        for hostname in conf.hostsConf.copy():
            if not conf.hostsConf[hostname]["metro_services"]:
                continue
            metro_services = conf.hostsConf[hostname]["metro_services"]
            if "connector-metro" not in vba[hostname]:
                validator.addWarning(hostname, "metro services",
                                        _("Can't find the metro server "
                                          "for the RRD-based services"))
                continue
            metro_server = vba[hostname]["connector-metro"]
            if isinstance(metro_server, list):
                metro_server = self._choose_metro_server(hostname, vba)
            if metro_server not in conf.hostsConf:
                if metro_server.count(".") and \
                        metro_server[:metro_server.find(".")] in conf.hostsConf:
                    metro_server = metro_server[:metro_server.find(".")]
                else:
                    validator.addWarning(hostname, "metro services",
                            _("The metrology server %s must be supervised for "
                              "the RRD-based services to work") % metro_server)
                    continue
            nagios_server = vba[hostname]["nagios"]
            if isinstance(nagios_server, list):
                nagios_server = nagios_server[0]
            metro_nagios_server = vba[metro_server]["nagios"]
            if isinstance(metro_nagios_server, list):
                metro_nagios_server = metro_nagios_server[0]
            if metro_nagios_server == nagios_server:
                # le serveur de metro est supervisé par le même serveur Nagios,
                # pas besoin d'ajouter un hôte fictif
                perf_host = metro_server
            else:
                # on doit créer un pseudo-hôte sur ce serveur Nagios
                perf_host = "_perfservices_"
                if perf_host not in conf.hostsConf:
                    conf.hostsConf[perf_host] = {
                            "name": perf_host,
                            "otherGroups": ["perf-services"],
                            "weight": 1,
                            "checkHostCMD": "check_dummy",
                            "services": {},
                            "SNMPJobs": {},
                            }
                    for attr in ["address", "serverGroup", "hostTPL",
                                 "snmpVersion", "community", "snmpPort",
                                 "snmpOIDsPerPDU"]:
                        conf.hostsConf[perf_host][attr] = \
                                conf.hostsConf[metro_server][attr]
            # Réglage du reRouteFor et du reRoutedBy
            for servicetuple in metro_services:
                servicename = servicetuple[0]
                metro_services[servicetuple]["reRouteFor"] = {
                                "host": hostname,
                                "service": servicename}
                conf.hostsConf[hostname]["services"][
                        servicename]["reRoutedBy"] = {
                                "host": perf_host,
                                "service": servicename,
                                }
                # On ne le fait pas en base parce que c'est compliqué et que ça
                # n'a pas vraiment de sens pour ce genre de services : les RRDs
                # on un step fixe.

                # On met les services Collector sur le serveur de métro
                jobname = "PERFSERVICE:%s:%s" % (hostname, servicename)
                conf.hostsConf[perf_host]["SNMPJobs"] \
                    [(jobname, "service")] = metro_services[servicetuple].copy()
                # Ajout dans la ventilation
                if perf_host not in vba:
                    vba[perf_host] = {}
                vba[perf_host]["nagios"] = nagios_server
                vba[perf_host]["collector"] = nagios_server
                if perf_host not in ventilation:
                    ventilation[perf_host] = {}
                for app, vserver in ventilation[hostname].iteritems():
                    if app.name == "nagios":
                        ventilation[perf_host][app] = vserver
                    if app.name == "collector":
                        ventilation[perf_host][app] = vserver

    def _choose_metro_server(self, hostname, vba):
        """On choisit le même serveur que nagios si possible"""
        nagios_servers = vba[hostname]["nagios"]
        if not isinstance(nagios_servers, list):
            nagios_servers = [nagios_servers, ]
        for metro_server in vba[hostname]["connector-metro"]:
            if metro_server in nagios_servers:
                return metro_server
        return vba[hostname]["connector-metro"][0]

