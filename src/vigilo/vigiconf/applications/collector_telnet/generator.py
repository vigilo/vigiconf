# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2011 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
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

"""Generator for Nagios"""

import os.path

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator


class CollectorTelnetGen(FileGenerator):
    """
    This class is in charge of generating a collectorTelnet compliant
    configuration file given the internal data model of VigiConf
    (see conf.py)
    """

    def generate(self):
        # pylint: disable-msg=W0201
        self._files = {}
        super(CollectorTelnetGen, self).generate()

    def generate_host(self, hostname, vserver):
        h = conf.hostsConf[hostname]
        _ip = h["address"]
        _fileName = os.path.join(
                self.baseDir,
                vserver,
                "collector-telnet",
                "%s.py" % hostname
                )
        if h.has_key("telnetJobs") and h["telnetJobs"]:
            if h["telnetJobs"].has_key("General"):
                _conf = h["telnetJobs"]["General"]
                self.templateCreate(
                        _fileName,
                        self.templates["host"],
                        {
                            "host": hostname,
                            "ip": _ip,
                            "login": _conf["login"],
                            "pass": _conf["pass"],
                            "timeout": _conf["timeout"],
                        }
                    )
            for _plugin in h["telnetJobs"].keys():
                if _plugin == "General" or _plugin == "NagiosTimePeriod":
                    continue
                _conf = h["telnetJobs"][_plugin]
                if not _conf.has_key("crit"):
                    _crit = None
                else:
                    _crit = _conf["crit"]
                self.templateAppend(
                        _fileName,
                        self.templates["plugins"],
                        {
                            "plugin": _conf["name"],
                            "srv_name": _conf["srv_name"],
                            "crystals": _conf["crystals"],
                            "domain": _conf["domain"],
                            "labels": _conf["labels"],
                            "crit": _crit,
                        }
                    )

# vim:set expandtab tabstop=4 shiftwidth=4:
