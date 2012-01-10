# -*- coding: utf-8 -*-
################################################################################
#
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
Generator for connector-nagios
"""


import os.path
import stat
import sqlite3

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import Generator


class ConnectorNagiosGen(Generator):
    """Generator for connector-nagios"""
    # On doit déployer sur tous les serveurs retournés
    # par la ventilation (nominal + backup).
    deploy_only_on_first = False

    def generate(self):
        # pylint: disable-msg=W0201
        self.connections = {}
        super(ConnectorNagiosGen, self).generate()
        self.finalize_databases()

    def generate_host(self, hostname, vserver):
        """Generate files"""
        h = conf.hostsConf[hostname]
        # Ajout des serveurs de backup
        if vserver not in self.application.servers:
            self.application.add_server(vserver)
        # Initialisation de la base
        db_path = os.path.join(self.baseDir, vserver, "connector-nagios.db")
        if vserver not in self.connections:
            self.init_db(db_path, vserver)
            os.chmod(db_path, # chmod 644
                     stat.S_IRUSR | stat.S_IWUSR | \
                     stat.S_IRGRP | stat.S_IROTH )
        cursor = self.connections[vserver]["cursor"]
        cursor.execute("UPDATE hosts SET ventilation = ?, local = 1 "
                       "WHERE name = ?", (vserver, hostname))


    def init_db(self, db_path, vserver):
        try:
            os.makedirs(os.path.dirname(db_path))
        except OSError:
            pass
        db = sqlite3.connect(db_path)
        c = db.cursor()
        self.connections[vserver] = {"db": db, "cursor": c}
        c.execute("""CREATE TABLE hosts (
                         name VARCHAR(255) NOT NULL,
                         ventilation VARCHAR(255),
                         local BOOL NOT NULL,
                         PRIMARY KEY (name)
                     )""")
        for hostname in conf.hostsConf.keys():
            try:
                vserver = self.ventilation[hostname]["connector-nagios"]
                if isinstance(vserver, list):
                    vserver = vserver[0]
            except KeyError:
                vserver = None
            c.execute("INSERT INTO hosts VALUES (?, ?, 0)",
                      (hostname, vserver))


    def finalize_databases(self):
        for vserver in self.connections:
            db = self.connections[vserver]["db"]
            cursor = self.connections[vserver]["cursor"]
            cursor.execute("CREATE INDEX ix_hosts_ventilation "
                           "ON hosts (ventilation)")
            cursor.execute("CREATE INDEX ix_hosts_local "
                           "ON hosts (local)")
            db.commit()
            cursor.close()
            db.close()
