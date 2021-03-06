# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Generator for RRD graph generator"""

from __future__ import absolute_import

import os
import stat
import sqlite3

from vigilo.common.gettext import translate
_ = translate(__name__)

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import Generator

class VigiRRDGen(Generator):
    """Generator for RRD graph generator"""

    def generate(self):
        # pylint: disable-msg=W0201
        self._all_ds_graph = set()
        self._all_ds_metro = set()
        self.connections = {}
        super(VigiRRDGen, self).generate()
        self.validate_ds_list()
        self.finalize_databases()

    def generate_host(self, hostname, vserver):
        h = conf.hostsConf[hostname]
        if len(h['graphItems']) == 0:
            return
        db_path = os.path.join(self.baseDir, vserver, "vigirrd.db")
        if vserver not in self.connections:
            self.init_db(db_path, vserver)
            os.chmod(db_path, # chmod 644
                     stat.S_IRUSR | stat.S_IWUSR |
                     stat.S_IRGRP | stat.S_IROTH )
        cursor = self.connections[vserver]["cursor"]

        idhost = self.db_add_host(cursor, hostname)
        for graphname, graphdata in h["graphItems"].iteritems():
            self.db_add_graph(cursor, idhost, graphname, graphdata, h["dataSources"])

        # list all ds for validation
        for graphvalues in h["graphItems"].values():
            self._all_ds_graph.update(set(graphvalues["ds"]))
            # ajout des cdefs utilisés
            for cdef in graphvalues["cdefs"]:
                self._all_ds_graph.update(set(
                        cmd for cmd in cdef["cdef"].split(",")
                        if cmd in h["dataSources"]))
        self._all_ds_metro.update(set(h["dataSources"].iterkeys()))

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
        self.addWarning("VigiRRD", _("Some datasources are not on a graph: %s")
                    % ", ".join([ "%s/%s" % dsr for dsr in missing_ds_report]))

    def init_db(self, db_path, vserver):
        try:
            os.makedirs(os.path.dirname(db_path))
        except OSError:
            pass
        db = sqlite3.connect(db_path)
        c = db.cursor()
        self.connections[vserver] = {"db": db, "cursor": c}
        # host
        c.execute("""CREATE TABLE host (
                         idhost INTEGER NOT NULL,
                         name VARCHAR(255) NOT NULL,
                         grid VARCHAR(64) NOT NULL,
                         height INTEGER NOT NULL,
                         width INTEGER NOT NULL,
                         step INTEGER NOT NULL,
                         PRIMARY KEY (idhost),
                          UNIQUE (name)
                     )""")
        # perfdatasource
        c.execute("""CREATE TABLE perfdatasource (
                         idperfdatasource INTEGER NOT NULL,
                         name TEXT NOT NULL,
                         label TEXT,
                         factor FLOAT NOT NULL,
                         max FLOAT,
                         PRIMARY KEY (idperfdatasource)
                     )""")
        # graph
        c.execute("""CREATE TABLE graph (
                         idgraph INTEGER NOT NULL,
                         idhost INTEGER,
                         name VARCHAR(255) NOT NULL,
                         template VARCHAR(255) NOT NULL,
                         vlabel VARCHAR(255) NOT NULL,
                         lastismax BOOLEAN,
                         min FLOAT,
                         max FLOAT,
                         PRIMARY KEY (idgraph),
                          FOREIGN KEY(idhost) REFERENCES host (idhost)
                     )""")
        # liaison
        c.execute("""CREATE TABLE graphperfdatasource (
                         idperfdatasource INTEGER NOT NULL,
                         idgraph INTEGER NOT NULL,
                         `order` INTEGER NOT NULL,
                         PRIMARY KEY (idperfdatasource, idgraph),
                          FOREIGN KEY(idperfdatasource) REFERENCES perfdatasource (idperfdatasource) ON DELETE CASCADE ON UPDATE CASCADE,
                          FOREIGN KEY(idgraph) REFERENCES graph (idgraph) ON DELETE CASCADE ON UPDATE CASCADE
                     )""")
        # CDEFs
        c.execute("""CREATE TABLE cdef (
                         idcdef INTEGER NOT NULL,
                         idgraph INTEGER NOT NULL,
                         name TEXT,
                         cdef TEXT,
                         PRIMARY KEY (idcdef),
                          FOREIGN KEY(idgraph) REFERENCES graph (idgraph) ON DELETE CASCADE ON UPDATE CASCADE,
                          UNIQUE (idgraph, name)
                     )""")

    def db_add_host(self, cursor, hostname):
        config = self.application.getConfig()
        cursor.execute("INSERT INTO host VALUES (NULL, ?, ?, ?, ?, ?)",
                       (hostname, config["grid"], config["height"],
                        config["width"], config["step"]))
        return cursor.lastrowid

    def db_add_graph(self, cursor, idhost, graphname, graphdata, dses):
        cursor.execute("INSERT INTO graph VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
                   (idhost, graphname, graphdata["template"],
                    graphdata["vlabel"],
                    graphdata.get("last_is_max", False),
                    graphdata["min"], graphdata["max"]))
        idgraph = cursor.lastrowid

        for index, dsname in enumerate(graphdata["ds"]):
            factor = graphdata["factors"].get(dsname, 1)
            self.db_add_pds(cursor, idgraph, dsname, factor, index, dses)

        for cdef in graphdata["cdefs"]:
            self.db_add_cdef(cursor, idgraph, cdef)

        return idgraph

    def db_add_pds(self, cursor, idgraph, name, factor, index, dses): # pylint: disable-msg=R0201
        cursor.execute("INSERT INTO perfdatasource(name, factor, label, max) "
                       "VALUES (?, ?, ?, ?)",
                       (name, factor, dses[name]['label'], dses[name]['max']))
        idpds = cursor.lastrowid
        cursor.execute("INSERT INTO graphperfdatasource "
                       "VALUES (?, ?, ?)", (idpds, idgraph, index))
        return idpds

    def db_add_cdef(self, cursor, idgraph, cdef): # pylint: disable-msg=R0201
        cursor.execute("INSERT INTO cdef (idgraph, name, cdef) "
                       "VALUES (?, ?, ?)",
                       (idgraph, cdef["name"], cdef["cdef"]))
        return cursor.lastrowid

    def finalize_databases(self):
        for vserver in self.connections:
            db = self.connections[vserver]["db"]
            cursor = self.connections[vserver]["cursor"]
            cursor.execute("CREATE INDEX ix_perfdatasource_name "
                           "ON perfdatasource (name)")
            cursor.execute("CREATE INDEX ix_host_name "
                           "ON host (name)")
            cursor.execute("CREATE INDEX ix_graph_name "
                           "ON graph (name)")
            db.commit()
            cursor.close()
            db.close()


# vim:set expandtab tabstop=4 shiftwidth=4:
