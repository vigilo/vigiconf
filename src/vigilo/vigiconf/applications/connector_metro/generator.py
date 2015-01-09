# -*- coding: utf-8 -*-
################################################################################
#
# VigiConf
# Copyright (C) 2007-2015 CS-SI
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
import sqlite3

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import Generator, GenerationError
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


class ConnectorMetroGen(Generator):
    """Generator for connector-metro, the RRD db generator"""
    # On doit déployer sur tous les serveurs retournés
    # par la ventilation (nominal + backup).
    deploy_only_on_first = False

    def generate(self):
        # pylint: disable-msg=W0201
        self.connections = {}
        super(ConnectorMetroGen, self).generate()
        self.finalize_databases()

    def generate_host(self, hostname, vserver):
        """Generate files"""
        h = conf.hostsConf[hostname]
        if "dataSources" not in h or not h['dataSources']:
            return
        # Ajout des serveurs de backup
        if vserver not in self.application.servers:
            self.application.add_server(vserver)
        # Initialisation de la base
        db_path = os.path.join(self.baseDir, vserver, "connector-metro.db")
        if vserver not in self.connections:
            self.init_db(db_path, vserver)
            os.chmod(db_path, # chmod 644
                     stat.S_IRUSR | stat.S_IWUSR | \
                     stat.S_IRGRP | stat.S_IROTH )
        cursor = self.connections[vserver]["cursor"]
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
            metro_data = h['metro_services'].get(datasource, {})

            tplvars = {
                'host': hostname,
                'dsType': ds_data['dsType'],
                'dsName': datasource,
                'factor': metro_data.get("factor", 1),
                'nagiosName': metro_data.get("servicename"),
                'vserver': vserver,
                'warningThreshold': metro_data.get('warning'),
                'criticalThreshold': metro_data.get('critical'),
            }

            if ds_data.get("max") is not None:
                # toute valeur supérieure collectée sera ignorée
                tplvars["max"] = float(ds_data["max"]) * 100 # marge de sécurité
            else:
                tplvars["max"] = None
            if ds_data.get("min") is not None:
                # toute valeur inférieure collectée sera ignorée
                tplvars["min"] = float(ds_data["min"])
            else:
                tplvars["min"] = None

            if not datasource in netflow_datasources:
                self.db_add_ds(cursor, tplvars, ds_data.get("rra_template"))
            else:
                # Netflow est un cas un peu à part
                # et nécessite un modèle spécifique
                # de stockage des données dans les RRD.
                self.db_add_ds(cursor, tplvars, "netflow")

    def init_db(self, db_path, vserver):
        try:
            os.makedirs(os.path.dirname(db_path))
        except OSError:
            pass
        db = sqlite3.connect(db_path)
        c = db.cursor()
        self.connections[vserver] = {"db": db, "cursor": c}
        # perfdatasource
        c.execute("""CREATE TABLE perfdatasource (
                         idperfdatasource INTEGER NOT NULL,
                         name TEXT NOT NULL,
                         hostname VARCHAR(255) NOT NULL,
                         type VARCHAR(255) NOT NULL,
                         PDP_step INTEGER NOT NULL,
                         heartbeat INTEGER NOT NULL,
                         min FLOAT,
                         max FLOAT,
                         factor FLOAT NOT NULL,
                         warning_threshold VARCHAR(32),
                         critical_threshold VARCHAR(32),
                         nagiosname VARCHAR(255),
                         ventilation VARCHAR(255),
                         PRIMARY KEY (idperfdatasource)
                     )""")
        #c.execute("CREATE INDEX ix_perfdatasource_name "
        #          "ON perfdatasource (name)")
        #c.execute("CREATE INDEX ix_perfdatasource_hostname "
        #          "ON perfdatasource (hostname)")
        # rra
        c.execute("""CREATE TABLE rra (
                         idrra INTEGER NOT NULL,
                         type VARCHAR(255) NOT NULL,
                         xff FLOAT,
                         RRA_step INTEGER NOT NULL,
                         rows INTEGER NOT NULL,
                         PRIMARY KEY (idrra)
                     )""")
        # liaison
        c.execute("""CREATE TABLE pdsrra (
                         idperfdatasource INTEGER NOT NULL,
                         idrra INTEGER NOT NULL,
                         "order" INTEGER NOT NULL,
                         PRIMARY KEY (idperfdatasource, idrra),
                         UNIQUE (idperfdatasource, "order"),
                         FOREIGN KEY(idperfdatasource)
                             REFERENCES perfdatasource (idperfdatasource)
                             ON DELETE CASCADE ON UPDATE CASCADE,
                         FOREIGN KEY(idrra)
                             REFERENCES rra (idrra)
                             ON DELETE CASCADE ON UPDATE CASCADE
                     )""")
        #db.commit()
        #c.close()
        #db.close()

    def db_add_ds(self, cursor, data, rra_template=None):
        config = self.application.getConfig()
        if rra_template is None:
            rra_template = "basic"
        elif rra_template not in config["rra"]:
            msg = _("Unknown RRA template %s") % rra_template
            raise GenerationError(msg)
        rra_template = config["rra"][rra_template]
        rras = rra_template["rras"]


        PDP_step = rra_template.get("PDP_step", config["PDP_step"])
        heartbeat = rra_template.get("heartbeat", config["heartbeat"])
        cursor.execute("INSERT INTO perfdatasource VALUES ("
                       "NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (data["dsName"], data["host"], data["dsType"],
                        PDP_step, heartbeat,
                        data["min"], data["max"], data["factor"],
                        data["warningThreshold"], data["criticalThreshold"],
                        data["nagiosName"], data['vserver']))
        ds_id = cursor.lastrowid

        for index, rra in enumerate(rras):
            cursor.execute("SELECT idrra FROM rra WHERE type = ? AND xff = ? "
                           "AND RRA_step = ? AND rows = ?",
                           (rra["type"], rra["xff"], rra["RRA_step"], rra["rows"]))
            rra_id = cursor.fetchone()
            if rra_id is None:
                cursor.execute("INSERT INTO rra VALUES (NULL, ?, ?, ?, ?)",
                           (rra["type"], rra["xff"], rra["RRA_step"], rra["rows"]))
                rra_id = cursor.lastrowid
            else:
                rra_id = rra_id[0]
            cursor.execute("INSERT INTO pdsrra VALUES (?, ?, ?)",
                           (ds_id, rra_id, index))

    def finalize_databases(self):
        for vserver in self.connections:
            db = self.connections[vserver]["db"]
            cursor = self.connections[vserver]["cursor"]
            cursor.execute("CREATE INDEX ix_perfdatasource_name "
                           "ON perfdatasource (name)")
            cursor.execute("CREATE INDEX ix_perfdatasource_hostname "
                           "ON perfdatasource (hostname)")
            cursor.execute("CREATE INDEX ix_perfdatasource_warning_threshold "
                           "ON perfdatasource (warning_threshold)")
            cursor.execute("CREATE INDEX ix_perfdatasource_critical_threshold "
                           "ON perfdatasource (critical_threshold)")
            db.commit()
            cursor.close()
            db.close()
