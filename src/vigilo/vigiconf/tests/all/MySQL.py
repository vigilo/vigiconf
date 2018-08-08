# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2017-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, String, Bool
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import translate, l_
_ = translate(__name__)


class MySQL(Test):
    """
    Test a MySQL server's availability and collect statistics
    about its current resource usage and lock conflicts.
    """

    @arg(
        'login', String,
        l_('Login'),
        l_("""
            Login to use during the connection to the server.

            Note: both a login and a password must be defined
            for this setting to have any effect.
        """)
    )
    @arg(
        'password', String,
        l_('Password'),
        l_("""
            Password.to use during the connection.

            Note: both a login and a password must be defined
            for this setting to have any effect.
        """)
    )
    def add_test(self, login=None, password=None):
        if not login or password is None:
            self.add_external_sup_service("MySQL", "check_mysql")
        else:
            self.add_external_sup_service("MySQL", "check_mysql_cmdlinecred!%s!%s" % (login, password))

            self.add_perfdata_handler("MySQL", "MySQL-OpenFiles", "Open files", "Open_files")
            self.add_perfdata_handler("MySQL", "MySQL-OpenTables", "Open tables", "Open_tables")
            self.add_perfdata_handler("MySQL", "MySQL-Connections", "Connections", "Threads_connected")
            self.add_perfdata_handler("MySQL", "MySQL-FailedLock", "Failed table locks", "Table_locks_waited")

            self.add_graph("Used resources", ["MySQL-OpenFiles", "MySQL-OpenTables", "MySQL-Connections"], "lines", "resources")
            self.add_graph("Failed table locks", ["MySQL-failedLock"], "lines", "failures")

