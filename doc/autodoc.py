# -*- coding: utf-8 -*-
# Copyright (C) 2011-2018 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import print_function
import sys, os, inspect
from epydoc.markup import epytext
from vigilo.vigiconf.lib.confclasses.test import TestFactory
from logging import getLogger

LOGGER = getLogger(__name__)

def _get_target_file():
    """
    Retourne le nom du fichier dans lequel la documentation
    des tests de supervision supportés par Vigilo sera écrite.
    """
    return os.path.join(os.path.dirname(__file__), 'suptests.rst')


def _prepare_table():
    widths = []
    table = []
    return table


def _to_unicode(line):
    if isinstance(line, unicode):
        return line
    if isinstance(line, str):
        return line.decode('utf-8', 'replace')
    raise NotImplementedError()

# Credit for this function goes to Paul Clinch:
# http://code.activestate.com/recipes/285264-natural-string-sorting/#c6
def keynat(string):
    r'''A natural sort helper function for sort() and sorted()
    without using regular expressions or exceptions.

    >>> items = ('Z', 'a', '10th', '1st', '9')
    >>> sorted(items)
    ['10th', '1st', '9', 'Z', 'a']
    >>> sorted(items, key=keynat)
    ['1st', '9', '10th', 'a', 'Z']
    '''
    it = type(1)
    r = []
    for c in string:
        if c.isdigit():
            d = int(c)
            if r and type( r[-1] ) == it:
                r[-1] = r[-1] * 10 + d
            else:
                r.append(d)
        else:
            r.append(c.lower())
    return r

def write_autodoc():
    """
    Génère automatiquement une documentation des tests de supervision
    supportés par Vigilo au format reStructuredText et l'enregistre
    dans le fichier retourné par L{_get_target_file}.

    Cf. ticket #932.
    """

    widths = []
    handle = open(_get_target_file(), 'w')
    handle.write(".. table:: Liste des tests de supervision "
                 "           disponibles dans Vigilo\n\n")

    test_factory = TestFactory('/')
    tests = test_factory.get_testnames()

    # PHASE 1 : récupération de la documentation des tests.
    tests_doc = {}
    for test in tests:
        # On ignore la classe de test générique.
        if test == 'Test':
            continue

        tests_doc[test] = {
            'params': {},
            'doc': '',
            'hclasses': [],
        }

        for test_cls in test_factory.get_test(test):
            # Recopie la documentation de la classe,
            # qui devient celle du test représenté.
            hclass = test_factory.get_hclass(test_cls)
            test_doc = test_cls.__doc__ or ""
            if not test_doc:
                print("WARNING: aucune description pour le test '%(test)s' "
                      "de la classe d'hôtes '%(hclass)s'" % {
                        'test': test,
                        'hclass': hclass,
                      }, file=sys.stderr)

            errors = []
            test_doc = epytext.parse_docstring(test_doc, errors)
            if errors:
                print("WARNING: impossible de lire la documentation du "
                      "test '%(test)s' de la classe d'hôtes '%(hclass)s'" % {
                        'test': test,
                        'hclass': hclass,
                      }, file=sys.stderr)

                tests_doc[test]['doc'] = ""
            else:
                tests_doc[test]['doc'] = \
                    test_doc.to_plaintext(None).strip().replace('\n', ' ')

            # Détermine les noms des paramètres
            # obligatoires et optionnels du test
            # pour cette classe d'équipements.
            specs = list(inspect.getargspec(test_cls.add_test))
            specs[0] = specs[0][1:] # "self" est toujours présent.
            optional = isinstance(specs[3], tuple) and len(specs[3]) or 0
            optional = specs[0][:-optional]
            required = specs[0][: len(specs[0]) - len(optional)]

            # Prépare un espace pour stocker la documentation
            # sur les paramètres obligatoires et optionnels
            # de ce test.
            #
            # @XXX: Ce code suppose que la documentation d'un argument donné
            #       ne varie pas en fonction de la classe (ie: est constante).
            tests_doc[test]['hclasses'].append(hclass)
            for param in required:
                tests_doc[test]['params'].setdefault(param, {
                    'doc': '',
                    'hclasses': {},
                })
                tests_doc[test]['params'][param]['hclasses'][hclass] = True
            for param in optional:
                tests_doc[test]['params'].setdefault(param, {
                    'doc': '',
                    'hclasses': {},
                })
                tests_doc[test]['params'][param]['hclasses'][hclass] = False

            errors = []
            if not test_cls.add_test.__doc__:
                print("WARNING: les paramètres du test '%(test)s' de la "
                      "classe d'hôtes '%(hclass)s' ne sont pas documentés" % {
                        'test': test,
                        'hclass': hclass,
                      }, file=sys.stderr)

                continue

            doc = epytext.parse_docstring(test_cls.add_test.__doc__, errors)
            if errors:
                print("WARNING: impossible de lire la documentation des "
                      "paramètres du test '%(test)s' de la classe "
                      "d'hôtes '%(hclass)s'" % {
                        'test': test,
                        'hclass': hclass,
                      }, file=sys.stderr)

                continue

            fields = doc.split_fields()
            for field in fields[1]:
                # Si un paramètre inconnu est documenté...
                if field.arg() not in tests_doc[test]['params']:
                    print("WARNING: paramètre '%(param)s' inconnu "
                          "(mais documenté !) dans le test '%(test)s' "
                          "de la classe d'hôtes '%(hclass)s'" % {
                            'param': field.arg(),
                            'test': test,
                            'hclass': hclass,
                          }, file=sys.stderr)
                    continue
                tests_doc[test]['params'][field.arg()]['doc'] = \
                    field.body().to_plaintext(None).strip().replace('\n', ' ')

            for param in tests_doc[test]['params']:
                if tests_doc[test]['params'][param]['doc']:
                    continue
                print("WARNING: le paramètre '%(param)s' n'est pas "
                      "documenté dans le test '%(test)s' de la classe "
                      "d'hôtes '%(hclass)s'" % {
                        'param': param,
                        'test': test,
                        'hclass': hclass,
                      }, file=sys.stderr)

    # PHASE 2 : transformation de la documentation en tableau
    #           avec les données formatées en reStructuredText.
    cells = [[], [], []]
    tests = sorted(tests_doc.iterkeys(), key=keynat)
    for test in tests:
        # Nom du test (colonne 1).
        cells[0].append('**%s**' % test)

        # Classes d'équipements (colonne 2).
        hclasses = sorted(tests_doc[test]['hclasses'], key=keynat)
        for hclass in hclasses:
            if hclass == 'all':
                cells[1].append('* %s' % '*Toutes*')
            else:
                cells[1].append('* %s' % hclass)

        # Description du test (colonne 3).
        cells[2].append(tests_doc[test]['doc'])
        # Description des paramètres du test (colonne 3).
        params = sorted(tests_doc[test]['params'].iterkeys(), key=keynat)
        if params:
            cells[2].append("")
            cells[2].append("Paramètres acceptés par le test :")
        for param in params:
            cells[2].append("")
            param_doc = "``%s``: %s" % (
                    param,
                    tests_doc[test]['params'][param]['doc']
                )
            param_hclasses = sorted(
                                tests_doc[test]['params'][param]['hclasses'],
                                key=keynat)
            if set(param_hclasses) != set(hclasses):
                param_doc += " (uniquement pour les classes suivantes: %s)" % \
                    ", ".join(param_hclasses)
            cells[2].append(param_doc)

        padding = max(len(cells[0]), len(cells[1]), len(cells[2]))
        for i in xrange(3):
            if len(cells[i]) != padding:
                cells[i].extend([""] * (padding - len(cells[i])))

        # Marque la fin de la documentation de ce test.
        cells[0].append(None)
        cells[1].append(None)
        cells[2].append(None)

    # PHASE 3 : représentation du tableau dans le fichier final.
    widths = []
    header = (
        "Nom du test",
        "Classes disponibles",
        "Détails",
    )

    for i in xrange(3):
        # Détermine la largeur à utiliser pour chacune des colonnes.
        # Il s'agit du max des largeurs des différentes entrées
        # de la colonne, y compris l'en-tête, plus deux (+2).
        # Le +2 permet d'ajouter un espace avant et après le texte,
        # ce qui évite des problèmes de délimitation du contenu des cases.
        widths.append(
            max(
                len(max(cells[i], key=lambda x: x is not None and len(x) or 0)),
                len(header[i])
            ) + 2
        )
    new_line = "+%s+" % "+".join(["-" * width for width in widths])
    header_line = new_line.replace('-', '=')

    data = [
        # En-tête.
        new_line,
        header,
        header_line,
    ]

    # Convertit les cellules du tableau en lignes de données.
    for i in xrange(len(cells[0])):
        # Si les cellules d'une ligne ne contiennent que des None,
        # on insère le délimiteur d'entrées à la place
        # (cf. formatage des tableaux en reStructuredText).
        if cells[0][i] is None and cells[1][i] is None and cells[2][i] is None:
            data.append(new_line)
            continue
        data.append( (cells[0][i], cells[1][i], cells[2][i]) )

    # Écrit le contenu du tableau ligne par ligne.
    for line in data:
        if isinstance(line, basestring):
            real_line = _to_unicode(line)
        else:
            # Il s'agit d'un itérable avec le contenu de chacune des cellules
            # de la ligne. On effectue le bourrage nécessaire pour aligner
            # les cellules
            real_line = [u""]
            for index, part in enumerate(line):
                real_line.append(u" " + _to_unicode(part).ljust(widths[index] - 1))
            real_line.append(u"")
            real_line = u"|".join(real_line)
        handle.write(" " * 4 + real_line.encode('utf-8') + "\n")

    handle.write("\n.. vim: set tw=79 :\n")
    handle.close()
    return 0


if __name__ == "__main__":
    sys.exit(write_autodoc())
else:
    write_autodoc()
