# -*- coding: utf-8 -*-
# Copyright (C) 2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import absolute_import, print_function

import textwrap

from vigilo.common.gettext import translate
_ = translate(__name__)

def dump(testfactory, hclasses, available_hclasses):
    """
    Affiche la liste des tests et classes de tests disponibles
    sous forme textuelle sur la sortie standard.
    """

    wrapper = textwrap.TextWrapper(
        initial_indent=' ' * 4,
        subsequent_indent=' ' * 4,
        break_long_words=False,
    )
    print(_("Available host classes:"))
    for line in wrapper.wrap(", ".join(available_hclasses) + "."):
        print(line)

    if not hclasses:
        return

    for hclass in hclasses:
        testnames = sorted(testfactory.get_testnames([hclass]))
        print("")
        print(_("Tests for host class '%s':") % hclass)
        for line in wrapper.wrap(", ".join(testnames) + "."):
            print(line)

