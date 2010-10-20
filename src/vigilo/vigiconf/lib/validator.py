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

from vigilo.common.gettext import translate
_ = translate(__name__)

class Validator(object):
    """
    Used by the generators to validate the configuration.
    @ivar _mapping: the ventilation mapping
    @type _mapping: C{dict}, see the
        L{vigilo.vigiconf.lib.ventilator.Ventilator.ventilate}() method
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
            L{vigilo.vigiconf.lib.ventilator.Ventilator.ventilate}() method
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
        apps = set()
        servers = set()
        for hostVentilation in self._mapping.values():
            for (app, vservers) in hostVentilation.iteritems():
                apps.add(app)
                servers.update(set(vservers))
        self._stats["nbServers"] = len(servers)
        self._stats["nbApps"] = len(apps)
        returnCode = True
        if len(servers) == 0:
            self.addError("Base Config", "servers",
                          _("No server configuration to be generated"))
            returnCode = False
        if len(apps) == 0:
            self.addError("Base Config", "apps",
                          _("No application configuration to be generated"))
            returnCode = False
        if len(conf.hostsConf) == 0:
            self.addError("Base Config", "hosts",
                          _("No host configuration to be generated"))
            returnCode = False
        return returnCode

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
                                "applications have been configured") % {
                                'nb_gens': self._stats["nbGenerators"],
                                'nb_apps': self._stats["nbApps"],
                            })
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


if __name__ == "__main__":
    import generator
    conf.loadConf()
    _ventilation = generator.getventilation()
    v = Validator(_ventilation)
    v.preValidate()
    print "\n".join(v.getSummary(stats = True) + [''])

# vim:set expandtab tabstop=4 shiftwidth=4:
