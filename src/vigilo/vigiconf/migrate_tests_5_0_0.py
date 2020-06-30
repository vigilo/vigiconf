# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2017-2020 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals, print_function
import sys
import inspect
from copy import deepcopy
from lxml import etree

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.models.configure import configure_db
configure_db(settings['database'], 'sqlalchemy_')

import vigilo.vigiconf.conf as conf
from vigilo.vigiconf.lib.confclasses.test import TestFactory



def _convert_classes(tree):
    # La classe "all" est systématiquement/automatiquement inclue.
    hclasses = set(['all'])
    xpath_classes = etree.XPath("class")

    # Construction de la liste des classes d'hôtes appliquées,
    # et suppression des balises "classes".
    for cls in xpath_classes(tree):
        hclasses.add(cls.text)
        cls.getparent().remove(cls)
    return hclasses


def _convert_tests(tree, hclasses):
    xpath_tests = etree.XPath("test")
    xpath_args = etree.XPath("arg")
    factory = TestFactory(confdir=settings["vigiconf"]["confdir"])

    for xml_test in xpath_tests(tree):
        testname = xml_test.get('name')
        if not testname:
            raise ValueError("Missing test name for: %s" % xml_test.getpath())

        added = 0
        tail = xml_test.tail or ''
        for cls in sorted(hclasses, reverse=True):
            test = factory.get_test("%s.%s" % (cls, testname))
            if not test:
                continue

            if not hasattr(test.add_test, 'wrapped_func'):
                func = test.add_test
            else:
                func = test.add_test.wrapped_func

            # Récupère la liste des arguments connus pour ce test
            # (et cette classe) à partir de la signature de add_test().
            known_args = list(inspect.getargspec(func))[0][1:]
            new_elem = deepcopy(xml_test)
            new_elem.set('name', "%s.%s" % (cls, testname))

            if added == 0:
                new_elem.tail = ''
            else:
                new_elem.tail = tail

            for arg in new_elem.findall('arg'):
                if arg.get('name') not in known_args:
                    new_elem.remove(arg)

            # Ajoute le nouveau test obtenu après migration.
            xml_test.addnext(new_elem)
            added += 1

        # Supprime l'ancien test.
        tree.remove(xml_test)

def _main(args):
    if len(args) < 1:
        print("Usage: %s <input file> [output file]" % sys.argv[0])
        sys.exit(1)

    print("Migrating '%s'" % (args[0], ))
    tree = etree.parse(args[0])
    xpath_hosts = etree.XPath("(//host|//template)")
    for host in xpath_hosts(tree):
        hclasses = _convert_classes(host)
        _convert_tests(host, hclasses)

    if len(args) < 2:
        output = sys.stdout
    else:
        output = open(args[1], 'w')

    output.write(etree.tostring(tree))
    sys.exit(0)

def main():
    return _main(sys.argv[1:])
