# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
################################################################################
#
# ConfigMgr Data Consistancy validator
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

""" ConfigMgrData Consistancy validation tool
"""

from __future__ import absolute_import

from .. import conf

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.models.session import DBSession
from vigilo.models import tables

class Validator(object):
    """
    Used by the generators to validate the configuration.
    @ivar _mapping: the ventilation mapping
    @type _mapping: C{dict}, see the
        L{vigilo.vigiconf.lib.ventilation.Ventilator.ventilate}() method
    @ivar _warnings: the list of warnings
    @type _warnings: C{list}
    @ivar _errors: the list of errors
    @type _errors: C{list}
    @ivar _stats: some statistics
    @type _stats: C{dict} containing 3 keys: filesWritten, dirsCreated, and
        nbGenerators.
    """

    def __init__(self, mapping):
        """
        @param mapping: the ventilation mapping
        @type  mapping: C{dict}, see the
            L{vigilo.vigiconf.lib.ventilation.Ventilator.ventilate}() method
        """
        self._mapping = mapping
        self._warnings = []
        self._errors = []
        self._stats = {"filesWritten":0, "dirsCreated":0, "nbGenerators":0}

    def addError(self, source, element, message):
        """
        Append an error to the final report
        @param source: the L{Generator<generators>} name
        @type  source: C{str}
        @param element: the element emitting the error.
        @type  element: C{str}
        @param message: the error message
        @type  message: C{str}
        """
        self._errors.append({"source":source, "object":element, "msg":message})

    def addWarning(self, source, element, message):
        """
        Append a warning to the final report
        @param source: the L{Generator<generators>} name
        @type  source: C{str}
        @param element: the element emitting the warning.
        @type  element: C{str}
        @param message: the warning message
        @type  message: C{str}
        """
        self._warnings.append({"source":source, "object":element,
                               "msg":message})

    def addAFile(self):
        """Increase the number of written files (for statistical purpose)"""
        self._stats["filesWritten"] += 1

    def addADir(self):
        """Increase the number of created dirs (for statistical purpose)"""
        self._stats["dirsCreated"] += 1

    def addAGenerator(self):
        """
        Increase the number of involved generators (for statistical purpose)
        """
        self._stats["nbGenerators"] += 1

    def preValidate(self):
        """
        Launches the validation
        @return: The result of validation
        @rtype: C{boolean}
        """
        self._stats["nbHosts"] = len(conf.hostsConf)
        self.apps = set()
        servers = set()
        for hostVentilation in self._mapping.values():
            for (app, vservers) in hostVentilation.iteritems():
                self.apps.add(app)
                servers.update(set(vservers))
        self._stats["nbServers"] = len(servers)
        self._stats["nbApps"] = len(self.apps)
        self.preValidateDB()
        if len(servers) == 0:
            self.addError("Base Config", "servers",
                          _("No server configuration to be generated"))
        if len(self.apps) == 0:
            self.addError("Base Config", "apps",
                          _("No application configuration to be generated"))
        if len(conf.hostsConf) == 0:
            self.addError("Base Config", "hosts",
                          _("No host configuration to be generated"))
        return not self.hasErrors()

    def preValidateDB(self):
        # Hosts
        hosts_db = DBSession.query(tables.Host).count()
        if hosts_db != self._stats["nbHosts"]:
            self.addError("DBLoader", "hosts",
                _("The number of host entries in the database does not match "
                  "the number of hosts in the configuration. "
                  "Database: %(db)d, configuration: %(conf)d")
                % {"db": hosts_db, "conf": self._stats["nbHosts"]})
            hosts_db = set([h.name for h in DBSession.query(tables.Host).all()])
            hosts_conf = set([ unicode(h) for h in conf.hostsConf.keys() ])
            LOGGER.debug("Hosts: difference between conf and DB: %s",
                         " ".join(hosts_db ^ hosts_conf))
        # Services
        svc_db = DBSession.query(tables.LowLevelService).count()
        svc_conf = 0
        svc_conf_detail = []
        for host in conf.hostsConf:
            if "services" in conf.hostsConf[host]:
                svc_conf += len(conf.hostsConf[host]["services"])
                svc_conf_detail.extend(["%s::%s" % (host, s)
                        for s in conf.hostsConf[host]["services"]])
            if "SNMPJobs" in conf.hostsConf[host] and \
                        conf.hostsConf[host]["SNMPJobs"]:
                svc_conf += 1
                svc_conf_detail.append("%s::Collector" % host)
            if "TelnetJobs" in conf.hostsConf[host] and \
                        conf.hostsConf[host]["TelnetJobs"]:
                svc_conf += 1
                svc_conf_detail.append("%s::collector-telnet" % host)
        if svc_db != svc_conf:
            self.addError("DBLoader", "services",
                _("The number of services entries in the database does not "
                  "match the number of services in the configuration. "
                  "Database: %(db)d, configuration: %(conf)d")
                % {"db": svc_db, "conf": svc_conf})
            svc_db_detail = ["%s::%s" % (s.host.name, s.servicename)
                    for s in DBSession.query(tables.LowLevelService).all()]
            svc_conf_detail = [ unicode(s) for s in svc_conf_detail ]
            LOGGER.debug("Services: difference between conf and DB: %s",
                         ", ".join(set(svc_db_detail) ^ set(svc_conf_detail)))
        # Applications
        apps_db = DBSession.query(tables.Application).count()
        if apps_db != self._stats["nbApps"]:
            self.addWarning("DBLoader", "applications",
                _("The number of apps loaded in the database does not match "
                  "the number of apps to deploy. Database: %(db)d, "
                  "to deploy: %(deploy)d. Possible cause: one or more app "
                  "have no Vigilo server to be deployed on.")
                % {"db": apps_db, "deploy": self._stats["nbApps"]})
            apps_db = set([a.name for a in
                           DBSession.query(tables.Application).all()])
            apps_conf = set()
            for host, hostVentilation in self._mapping.iteritems():
                for app in hostVentilation:
                    apps_conf.add(app.name)
            LOGGER.debug("Applications: difference between conf and DB: %s",
                         " ".join(apps_db ^ apps_conf))
        # Ventilation
        ventilation_db = DBSession.query(tables.Ventilation).count()
        if ventilation_db != self._stats["nbHosts"] * self._stats["nbApps"]:
            self.addWarning("DBLoader", "ventilation",
                _("The number of ventilation entries in the database does "
                  "not match the number of host and apps. Database: %(db)d, "
                  "should be: %(conf)d. Possible cause: one or more "
                  "application have no Vigilo server to be deployed on.")
                % {"db": ventilation_db,
                   "conf": self._stats["nbHosts"] * self._stats["nbApps"]})
            ventilation_db = set([ "%s:%s" % (v.host.name, v.application.name)
                         for v in DBSession.query(tables.Ventilation).all() ])
            ventilation_conf = set()
            for a in self.apps:
                for h in conf.hostsConf.keys():
                    ventilation_conf.add("%s:%s" % (h, a))
            LOGGER.debug("Ventilation: difference between conf and DB: %s",
                         " ".join(ventilation_db ^ ventilation_conf))

    def hasErrors(self):
        """
        @return: True if any major error has been found, False otherwise
        @rtype: C{boolean}
        """
        return len(self._errors) != 0

    def getSummary(self, details=False, stats=False):
        """
        Prepare a textual summary of the validation result
        @param details: be very verbose
        @type  details: C{boolean}
        @param stats: print statistics
        @type  stats: C{boolean}
        @return: the summary
        @rtype: C{str}
        """
        if self._stats["nbApps"] != self._stats["nbGenerators"]:
            self.addWarning("Base Config", "generators",
                    _("%(nb_gens)d generators exist whereas %(nb_apps)d "
                      "applications have been configured")
                    % {'nb_gens': self._stats["nbGenerators"],
                       'nb_apps': self._stats["nbApps"]})
        s = []
        if details:
            for i in self._errors:
                s.append(_("########> Error in %(source)s (object "
                            "%(object)s): %(error)s") % {
                    'source': i['source'],
                    'object': i['object'],
                    'error': i['msg'],
                })
            for i in self._warnings:
                s.append(_("====> Warning in %(source)s (object %(object)s): "
                            "%(error)s") % {
                    'source': i['source'],
                    'object': i['object'],
                    'error': i['msg'],
                })
        s.append(_("%d errors") % len(self._errors))
        s.append(_("%d warnings") % len(self._warnings))
        if stats:
            s.append(_("%(nbGenerators)d generators have configured "
                "%(nbHosts)d hosts on %(nbServers)d servers.") % self._stats)
            s.append(_("%(filesWritten)d files have been generated in "
                "%(dirsCreated)d directories") % self._stats)
        return s


