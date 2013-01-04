# -*- coding: utf-8 -*-
# Copyright (C) 2011-2013 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

DEFAULTS = {
    "step": 300,
    "heartbeat": 600,
    "rra": {
        "basic": [
            { "type": "AVERAGE", "xff": 0.5, "step": 1, "rows": 600 },
            { "type": "AVERAGE", "xff": 0.5, "step": 6, "rows": 700 },
            { "type": "AVERAGE", "xff": 0.5, "step": 24, "rows": 775 },
            { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 732},
        ],
        "netflow": [
            { "type": "AVERAGE", "xff": 0.5, "step": 1, "rows": 4320 },
            { "type": "AVERAGE", "xff": 0.5, "step": 12, "rows": 744 },
            { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 366},
        ],
        # Cette définition de RRAs est utile
        # pour les jauges à valeurs discrètes,
        # ex: nombre d'utilisateurs/sessions TCP,
        # nombre d'appels en cours, etc.
        "discrete": [
            { "type": "LAST", "xff": 0.5, "step": 1, "rows": 600 },
            { "type": "AVERAGE", "xff": 0.5, "step": 6, "rows": 700 },
            { "type": "AVERAGE", "xff": 0.5, "step": 24, "rows": 775 },
            { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 732},
        ],
    },
}
