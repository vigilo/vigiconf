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

"""
Generator for connector-metro, the RRD db generator
"""


import os.path
import stat
import urllib
import sqlite3

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import Generator


class ConnectorMetroGen(Generator):
    """Generator for connector-metro, the RRD db generator"""

    def generate_host(self, hostname, vserver):
        """Generate files"""
        h = conf.hostsConf[hostname]
        if "dataSources" not in h or not h['dataSources']:
            return
        db_path = os.path.join(self.baseDir, vserver, "connector-metro.db") 
        if not os.path.exists(db_path):
            self.init_db(db_path)
            os.chmod(db_path, # chmod 644
                     stat.S_IRUSR | stat.S_IWUSR | \
                     stat.S_IRGRP | stat.S_IROTH )
        db = sqlite3.connect(db_path)
        cursor = db.cursor()
        datasources = h['dataSources'].keys()
        datasources.sort()
        netflow_datasources = []
        for ip in h['netflow'].get('IPs', {}):
            netflow_datasources.append("in_bytes_" + ip)
            netflow_datasources.append("out_bytes_" + ip)
            netflow_datasources.append("in_packets_" + ip)
            netflow_datasources.append("out_packets_" + ip)
        for datasource in datasources:
            ds_data = h['dataSources'][datasource]
            if datasource in netflow_datasources:
                datasource = "/".join(i for i in datasource.split("/")[:-1])
            tplvars = {
                'host': hostname,
                'dsType': ds_data['dsType'],
                'dsName': datasource,
            }
            if "max" in ds_data and ds_data["max"] is not None:
                # toute valeur supérieure collectée sera ignorée
                tplvars["max"] = float(ds_data["max"]) * 100 # marge de sécurité
            else:
                tplvars["max"] = None
            if "min" in ds_data and ds_data["min"] is not None:
                # toute valeur inférieure collectée sera ignorée
                tplvars["min"] = float(ds_data["min"])
            else:
                tplvars["min"] = None
            if not datasource in netflow_datasources:
                self.db_add_ds(cursor, tplvars, is_netflow=False)
            else:
                self.db_add_ds(cursor, tplvars, is_netflow=True)
        db.commit()
        cursor.close()
        db.close()

    def init_db(self, db_path):
        db = sqlite3.connect(db_path)
        c = db.cursor()
        # perfdatasource
        c.execute("""CREATE TABLE perfdatasource (
                         idperfdatasource INTEGER NOT NULL, 
                         name TEXT NOT NULL, 
                         hostname VARCHAR(255) NOT NULL, 
                         type VARCHAR(255) NOT NULL, 
                         step INTEGER NOT NULL, 
                         heartbeat INTEGER NOT NULL, 
                         min FLOAT, 
                         max FLOAT, 
                         PRIMARY KEY (idperfdatasource)
                     )""")
        c.execute("CREATE INDEX ix_perfdatasource_name "
                  "ON perfdatasource (name)")
        c.execute("CREATE INDEX ix_perfdatasource_hostname "
                  "ON perfdatasource (hostname)")
        # rra
        c.execute("""CREATE TABLE rra (
                         idrra INTEGER NOT NULL, 
                         type VARCHAR(255) NOT NULL, 
                         xff FLOAT, 
                         step INTEGER NOT NULL, 
                         rows INTEGER NOT NULL, 
                         PRIMARY KEY (idrra)
                     )""")
        # liaison
        c.execute("""CREATE TABLE pdsrra (
                         idperfdatasource INTEGER NOT NULL, 
                         idrra INTEGER NOT NULL, 
                         PRIMARY KEY (idperfdatasource, idrra), 
                         FOREIGN KEY(idperfdatasource)
                             REFERENCES perfdatasource (idperfdatasource)
                             ON DELETE CASCADE ON UPDATE CASCADE, 
                         FOREIGN KEY(idrra)
                             REFERENCES rra (idrra)
                             ON DELETE CASCADE ON UPDATE CASCADE
                     )""")
        db.commit()
        c.close()
        db.close()

    def db_add_ds(self, cursor, data, is_netflow=False):
        config = self.application.getConfig()
        cursor.execute("INSERT INTO perfdatasource VALUES ("
                       "NULL, ?, ?, ?, ?, ?, ?, ?)",
                       (data["dsName"], data["host"], data["dsType"],
                        config["step"], config["heartbeat"],
                        data["min"], data["max"]))
        ds_id = cursor.lastrowid
        if is_netflow:
            rras = config["rra_netflow"]
        else:
            rras = config["rra"]
        for rra in rras:
            cursor.execute("SELECT idrra FROM rra WHERE type = ? AND xff = ? "
                           "AND step = ? AND rows = ?",
                           (rra["type"], rra["xff"], rra["step"], rra["rows"]))
            rra_id = cursor.fetchone()
            if rra_id is None:
                cursor.execute("INSERT INTO rra VALUES (NULL, ?, ?, ?, ?)",
                           (rra["type"], rra["xff"], rra["step"], rra["rows"]))
                rra_id = cursor.lastrowid
            else:
                rra_id = rra_id[0]
            cursor.execute("INSERT INTO pdsrra VALUES (?, ?)", (ds_id, rra_id))


