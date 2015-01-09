# -*- coding: utf-8 -*-
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2011-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.vigiconf.lib import VigiConfError

from vigilo.common.gettext import translate
_ = translate(__name__)



class UpTime(Test):
    """Check the SNMP server's uptime"""

    oids = [".1.3.6.1.2.1.1.3.0"]

    def add_test(self, warn=900, crit=400):
        """
        Teste la disponibilité de l'équipement (durée depuis son dernier
        redémarrage, ou en réalité, depuis le dernier redémarrage de
        son agent SNMP).

        @param warn: Durée en secondes pendant laquelle une alerte
            de niveau WARNING est émise après le redémarrage
            de l'équipement ou de l'agent SNMP.
        @type  warn: C{int}
        @param crit: Durée en secondes pendant laquelle une alerte
            de niveau CRITICAL est émise après le redémarrage
            de l'équipement ou de l'agent SNMP.
            Cette valeur doit être strictement inférieure à celle
            du paramètre L{warn}.
        @type  crit: C{int}
        """
        warn = self.as_int(warn)
        crit = self.as_int(crit)

        if warn < 0 or crit < 0 or warn < crit:
            raise VigiConfError(_('Invalid thresholds. Expected 0 < crit < warn'))

        self.add_collector_service("UpTime", "sysUpTime", [crit, warn],
                            ["GET/.1.3.6.1.2.1.1.3.0"])
        self.add_collector_metro("sysUpTime", "m_sysUpTime", [],
                            ["GET/.1.3.6.1.2.1.1.3.0"], 'GAUGE', label="UpTime")
        self.add_graph("UpTime", [ "sysUpTime" ], "lines", "jours",
                            factors={"sysUpTime": round(1.0/86400, 10)})


# vim:set expandtab tabstop=4 shiftwidth=4:
