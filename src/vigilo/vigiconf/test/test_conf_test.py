# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2015 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import unittest

from vigilo.vigiconf.lib.confclasses.test import Test

from vigilo.vigiconf.lib import ParsingError

from vigilo.common.gettext import translate
_ = translate(__name__)

class TestTestParamsConversion(unittest.TestCase):
    """
    Tests les méthodes de conversion des paramètres
    des tests de supervision.
    """

    def test_as_bool(self):
        """Conversion d'un paramètre en booléen."""
        # Les valeurs booléennes de Python doivent être acceptées
        # et retournées sans modification.
        self.assertTrue(Test.as_bool(True))
        self.assertFalse(Test.as_bool(False))

        # Les valeurs suivantes doivent être évaluées
        # à True (case-insensitive).
        for value in ('1', 'true', 'on', 'yes', 'True', 'ON'):
            self.assertTrue(Test.as_bool(value))

        # Les valeurs suivantes doivent être évaluées
        # à False (case-insensitive).
        for value in ('0', 'false', 'off', 'no', 'False', 'NO'):
            self.assertFalse(Test.as_bool(value))

        # Toute autre valeur doit lever une erreur d'analyse.
        for value in ('', 'test'):
            self.assertRaises(ParsingError, Test.as_bool, value)

    def test_as_float(self):
        """Conversion d'un paramètre en flottant."""
        # Les floats de Python doivent être acceptés et retournés en l'état.
        self.assertEquals(3.14, Test.as_float(3.14))

        # Les valeurs compatibles doivent être converties sans erreur.
        for value, res in (('3.14', 3.14), ('-4', -4.0)):
            self.assertEquals(res, Test.as_float(value))

        # Toute autre valeur doit lever une erreur d'analyse.
        for value in ('', 'test', '+', '-', '-.'):
            self.assertRaises(ParsingError, Test.as_float, value)

    def test_as_int(self):
        """Conversion d'un paramètre en entier."""
        # Les floats et autres valeurs de Python compatibles
        # doivent être acceptés et retournés en l'état.
        self.assertEquals(3, Test.as_int(3.14))
        self.assertEquals(-2, Test.as_int(-2))

        # Les valeurs compatibles doivent être converties sans erreur.
        for value, res in (('3', 3), ('-4', -4)):
            self.assertEquals(res, Test.as_int(value))

        # Toute autre valeur doit lever une erreur d'analyse.
        for value in ('', 'test', '+', '-', '-.', '3.14'):
            self.assertRaises(ParsingError, Test.as_int, value)
