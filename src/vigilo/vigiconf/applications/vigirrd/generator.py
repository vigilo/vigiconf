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

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

class VigiRRDGen(FileGenerator):
    """Generator for RRD graph generator"""

    def generate(self):
        """Generate files"""
        all_ds_graph = set()
        all_ds_metro = set()
        for host, ventilation in self.mapping.iteritems():
            if not 'vigirrd' in ventilation.keys():
                continue
            h = conf.hostsConf[host]
            if len(h['graphItems']) == 0:
                continue
            fileName = "%s/%s/vigirrd.conf.py" \
                       % (self.baseDir, ventilation['vigirrd'])
            # fill the template
            if not os.path.exists(fileName):
                self.templateCreate(fileName, self.templates["header_host"],
                                    {"confid": conf.confid})
                self.templateAppend(fileName, self.templates["header_label"], {})
            self.templateAppend(fileName, self.templates["host"],
                                {'host': host, 'graphes': h["graphItems"]})
            # list all ds for validation
            for graphvalues in h["graphItems"].values():
                all_ds_graph.update(set(graphvalues["ds"]))
            if conf.mode != "onedir":
                # add human-readable labels
                for dsid in h["dataSources"]:
                    self.templateAppend(fileName, self.templates["label"],
                                    {'label': dsid,
                                     'value': h["dataSources"][dsid]["label"]})
                    all_ds_metro.add(dsid)
            for dsid in h["dataSources"]:
                all_ds_metro.add(dsid)
        # compare the DS lists for validation
        if all_ds_graph != all_ds_metro:
            missing_ds = all_ds_metro - all_ds_graph
            # Convert to human-readable
            missing_ds_human = []
            for ds in missing_ds:
                for host in conf.hostsConf.keys():
                    h = conf.hostsConf[host]
                    if h["dataSources"].has_key(ds):
                        missing_ds_human.append(h["dataSources"][ds]["label"])
            self.addWarning("RRDGraph", "All the defined DSs are not graphed: "
                                       +"%s" % ", ".join(missing_ds_human))


# vim:set expandtab tabstop=4 shiftwidth=4:
