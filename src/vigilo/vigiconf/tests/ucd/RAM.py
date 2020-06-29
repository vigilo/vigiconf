# vim:set fileencoding=utf-8 expandtab tabstop=4 shiftwidth=4:
# pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2006-2020 CS GROUP – France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, Float
from vigilo.vigiconf.tests.all.RAM import RAM as all_RAM
from vigilo.common.gettext import l_


class RAM(all_RAM):
    """Check the RAM usage of a host"""

    oids = [".1.3.6.1.4.1.2021.4"]

    @arg('warn', Float, l_('WARNING threshold'))
    @arg('crit', Float, l_('CRITICAL threshold'))
    def add_test(self, warn=80, crit=90):
        # Calcul de l'espace réellement utilisé :
        # memTotalReal - memAvailReal - memBuffer - memCached
        rpn_formula = [
            '.1.3.6.1.4.1.2021.4.5.0', '.1.3.6.1.4.1.2021.4.6.0', '-',
            '.1.3.6.1.4.1.2021.4.15.0', '-', '.1.3.6.1.4.1.2021.4.14.0', '-',
            ]
        # Pourcentage de l'espace total :
        # valeur-precedente / memTotalReal * 100
        rpn_percent_formula = rpn_formula + [
                '.1.3.6.1.4.1.2021.4.5.0', '/', '100', '*' ]

        # Service
        self.add_collector_service("RAM", "sup_rpn",
                [ "RAM", warn, crit, "RAM: %2.2f%%" ] + rpn_percent_formula,
                [ "WALK/.1.3.6.1.4.1.2021.4" ])
        # Metro
        self.add_collector_metro("ram-buffer", "directValue", [],
                [ "GET/.1.3.6.1.4.1.2021.4.14.0" ], "GAUGE",
                label="Buffer")
        self.add_collector_metro("ram-cached", "directValue", [],
                [ "GET/.1.3.6.1.4.1.2021.4.15.0" ], "GAUGE",
                label="Cached")
        self.add_collector_metro("Used RAM", "m_rpn", rpn_formula,
                [ "WALK/.1.3.6.1.4.1.2021.4" ], "GAUGE",
                label="Used")
        self.add_collector_metro("Total RAM", "directValue", [],
                [ "GET/.1.3.6.1.4.1.2021.4.5.0" ], "GAUGE",
                label="Total")

        self.add_graph("RAM",
                ["Used RAM", "ram-buffer", "ram-cached", "Total RAM"],
                "stacks", "bytes", group="Performance", last_is_max=True,
                min=0, factors={"Used RAM":   1024,
                                "ram-buffer": 1024,
                                "ram-cached": 1024,
                                "Total RAM":  1024})
