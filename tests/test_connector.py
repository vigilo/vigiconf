# vim: set fileencoding=utf-8 sw=4 ts=4 et ai :

"""
Tests du connecteur VigiConf
"""

import os
import unittest
import time

# ATTENTION: ne pas utiliser twisted.trial, car nose va ignorer les erreurs
# produites par ce module !!!
#from twisted.trial import unittest
from nose.twistedtools import reactor, deferred

from twisted.internet import defer
from wokkel.test.helpers import XmlStreamStub
from wokkel.generic import parseXml

from vigilo.pubsub.xml import NS_COMMAND
from vigilo.vigiconf.connector.xmpptovigiconf import XMPPToVigiConf
from vigilo.vigiconf.connector.command import Command, CommandNotFound, \
        AlreadyCalledError


class CommandTest(unittest.TestCase):

    @deferred(10)
    def test_command_sleep(self):
        """Test de la commande sleep"""
        now = time.time()
        process = Command("sleep", ["3"])
        d = process.run()
        def check_time(r):
            self.assertEqual(process.duration, 3)
        d.addCallback(check_time)
        return d

    def test_command_unknown(self):
        """Une commande introuvable doit provoquer une exception"""
        now = time.time()
        self.assertRaises(CommandNotFound, Command, "nonexistant")

    @deferred(10)
    def test_command_alread_called(self):
        """Une commande ne doit pas pouvoir être lancée deux fois"""
        now = time.time()
        process = Command("true")
        d = process.run()
        def check_time(r):
            return process.run()
            self.assertRaises(AlreadyCalledError, process.run)
        d.addCallback(check_time)
        def fail(r):
            self.fail()
        def check_failure(r):
            self.failUnless(isinstance(r.value, AlreadyCalledError))
        d.addCallbacks(fail, check_failure)
        return d


class XMPPToVigiConfTest(unittest.TestCase):

    def setUp(self):
        # Mocks the behaviour of XMPPClient. No TCP connections made.
        self.stub = XmlStreamStub()
        self.conn = XMPPToVigiConf()
        self.conn.xmlstream = self.stub.xmlstream
        self.conn.send = self.stub.xmlstream.send
        self.conn.connectionInitialized()

    def tearDown(self):
        self.conn.stop()

    @deferred(10)
    def test_echo(self):
        """Test d'une commande simple (echo)"""
        self.conn.vigiconf_cmd = "echo"
        msg = ('<command xmlns="%s">'
               '<cmdname>dummy</cmdname>'
               '<arg>arg1</arg><arg>arg2</arg>'
               '</command>' % NS_COMMAND)
        #self.stub.send(msg)
        d = self.conn.processMessage( (parseXml(msg), {"from": "dummy",
                                                       "to": "dummy"}) )
        def check_output(p):
            self.assertEqual(p.exit_code, 0)
            self.assertEqual(p.stdout, "dummy arg1 arg2\n")
            self.assertEqual(p.stderr, "")
        d.addCallback(check_output)
        return d

    @deferred(10)
    def test_vigiconf_help(self):
        """Test avec 'vigiconf --help'"""
        buildout_bin_dir = os.path.join(os.path.dirname(__file__), "..", "bin")
        os.environ["PATH"] = buildout_bin_dir + ":" + os.environ["PATH"]
        msg = ('<command xmlns="%s">'
               '<cmdname>--help</cmdname>'
               '</command>' % NS_COMMAND)
        d = self.conn.processMessage( (parseXml(msg), {"from": "dummy",
                                                       "to": "dummy"}) )
        def check_result(p):
            self.assertEqual(p.exit_code, 0)
            self.failUnless(p.stdout.count("usage") >= 1)
            self.assertEqual(p.stderr, "")
        d.addCallback(check_result)
        return d

    @deferred(10)
    def test_text_msg(self):
        """Test de l'envoi d'une commande en mode texte"""
        self.conn.vigiconf_cmd = "echo"
        msg = ('<message type="chat" from="dummy_from" to="dummy_to">'
               '<thread>dummy_thread</thread>'
               '<body>dummy_command arg1 arg2</body>'
               '</message>')
        self.stub.send(parseXml(msg))
        d = defer.Deferred()
        def check_output(r):
            self.failIf(len(self.stub.output) < 2)
            self.assertEqual(self.stub.output[-2].toXml(), 
                             "<message to='dummy_from' from='dummy_to' type='chat'>"
                             "<body>Running command: echo dummy_command arg1 arg2</body>"
                             "<thread>dummy_thread</thread></message>")
            self.assertEqual(self.stub.output[-1].toXml(),
                             "<message to='dummy_from' from='dummy_to' type='chat'>"
                             "<body>OK</body><thread>dummy_thread</thread></message>")
        d.addCallback(check_output)
        reactor.callLater(3, d.callback, None) # attendre un peu
        return d

