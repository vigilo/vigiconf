################################################################################
#
# ConfigMgr RRD Grapher configuration file generator
# Copyright (C) 2007 CS-SI
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

"""Generator for RRD graph generator"""

from __future__ import absolute_import

import os.path

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

class VigiRRDGen(FileGenerator):
    """Generator for RRD graph generator"""

    def generate(self):
        self._all_ds_graph = set()
        self._all_ds_metro = set()
        super(VigiRRDGen, self).generate()
        self.validate_ds_list()

    def generate_host(self, hostname, vserver):
        h = conf.hostsConf[hostname]
        if len(h['graphItems']) == 0:
            return
        fileName = os.path.join(self.baseDir, vserver, "vigirrd.conf.py")
        # fill the template
        if not os.path.exists(fileName):
            self.templateCreate(fileName, self.templates["header_host"],
                                {"confid": conf.confid})
            self.templateAppend(fileName, self.templates["header_label"], {})
        self.templateAppend(fileName, self.templates["host"],
                            {'host': hostname, 'graphes': h["graphItems"]})
        # list all ds for validation
        for graphvalues in h["graphItems"].values():
            self._all_ds_graph.update(set(graphvalues["ds"]))
        # add human-readable labels
        for dsid in h["dataSources"]:
            self.templateAppend(fileName, self.templates["label"],
                            {'label': dsid,
                             'value': h["dataSources"][dsid]["label"]})
        for dsid in h["dataSources"]:
            self._all_ds_metro.add(dsid)

    def validate_ds_list(self):
        # compare the DS lists for validation
        if self._all_ds_graph == self._all_ds_metro:
            return
        missing_ds = self._all_ds_metro - self._all_ds_graph
        # Convert to human-readable
        missing_ds_report = []
        for ds in missing_ds:
            for host in conf.hostsConf.keys():
                h = conf.hostsConf[host]
                if "dataSources" not in h:
                    continue
                if ds in h["dataSources"]:
                    missing_ds_report.append( (host, ds) )
        self.addWarning("VigiRRD", _("All the defined DSes are not graphed: %s")
                    % ", ".join([ "%s/%s" % dsr for dsr in missing_ds_report]))


# vim:set expandtab tabstop=4 shiftwidth=4:
