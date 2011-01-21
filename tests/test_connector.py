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
from vigilo.vigiconf.connector.xmpptovigiconf import XMPPToVigiConf, \
        VigiConfMessageProtocol
from vigilo.vigiconf.connector.command import Command, CommandNotFound, \
        AlreadyCalledError


class CommandTest(unittest.TestCase):

#    @deferred(10)
#    def test_command_sleep(self):
#        """Test de la commande sleep"""
#        now = time.time()
#        process = Command("sleep", ["3"])
#        d = process.run()
#        def check_time(r):
#            self.assertEqual(process.duration, 3)
#        d.addCallback(check_time)
#        return d

    def test_command_unknown(self):
        """Une commande introuvable doit provoquer une exception"""
        now = time.time()
        self.assertRaises(CommandNotFound, Command, "nonexistant")

    @deferred(10)
    def test_command_alread_called(self):
        """Une commande ne doit pas pouvoir être lancée deux fois"""
        process = Command("true")
        process.dry_run = True
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


class CommandDryRun(Command):
    def __init__(self, command, arguments=[]):
        Command.__init__(self, command, arguments)
        self.dry_run = True

class XMPPToVigiConfTest(unittest.TestCase):

    def setUp(self):
        # Mocks the behaviour of XMPPClient. No TCP connections made.
        self.stub = XmlStreamStub()
        self.conn = XMPPToVigiConf()
        self.conn.xmlstream = self.stub.xmlstream
        self.conn.send = self.stub.xmlstream.send
        self.conn.connectionInitialized()
        message_protocol = VigiConfMessageProtocol(self.conn)
        message_protocol.xmlstream = self.stub.xmlstream
        message_protocol.connectionInitialized()

    def tearDown(self):
        self.conn.stop()

    @deferred(10)
    def test_simple(self):
        """Test d'une commande simple"""
        self.conn.vigiconf_cmd = "echo"
        self.conn._command_class = CommandDryRun
        msg = ('<command xmlns="%s">'
               '<cmdname>dummy</cmdname>'
               '<arg>arg1</arg><arg>arg2</arg>'
               '</command>' % NS_COMMAND)
        #self.stub.send(msg)
        d = self.conn.processMessage( (parseXml(msg), {"from": "dummy",
                                                       "to": "dummy"}) )
        def check_output(p):
            self.assertEqual(p.exit_code, 0)
            self.assertEqual(p.command, "echo")
            self.assertEqual(p.executable, "/bin/echo")
            self.assertEqual(p.arguments, ["dummy", "arg1", "arg2"])
        d.addCallback(check_output)
        return d

    @deferred(10)
    def test_text_msg(self):
        """Test de l'envoi d'une commande en mode texte (message)"""
        self.conn.vigiconf_cmd = "echo"
        self.conn._command_class = CommandDryRun
        msg = ('<message from="dummy_from" to="dummy_to">'
               '<thread>dummy_thread</thread>'
               '<body>dummy_command arg1 arg2</body>'
               '</message>')
        self.stub.send(parseXml(msg))
        d = defer.Deferred()
        def check_output(r):
            #print [e.toXml() for e in self.stub.output]
            self.failIf(len(self.stub.output) < 2)
            msg = self.stub.output[-1]
            print msg.toXml()
            self.assertEqual(str(msg["to"]), "dummy_from")
            self.assertEqual(str(msg["from"]), "dummy_to")
            self.assertEqual(str(msg["type"]), "normal")
            self.assertEqual(str(msg.thread), "dummy_thread")
            self.failUnless(unicode(msg.subject).startswith("OK."))
            self.assertEqual(str(msg.body), "")
        d.addCallback(check_output)
        reactor.callLater(2, d.callback, None) # attendre un peu
        return d

    @deferred(10)
    def test_text_msg_chat(self):
        """Test de l'envoi d'une commande en mode texte (chat)"""
        self.conn.vigiconf_cmd = "echo"
        self.conn._command_class = CommandDryRun
        msg = ('<message type="chat" from="dummy_from" to="dummy_to">'
               '<thread>dummy_thread</thread>'
               '<body>dummy_command arg1 arg2</body>'
               '</message>')
        self.stub.send(parseXml(msg))
        d = defer.Deferred()
        def check_output(r):
            #print [e.toXml() for e in self.stub.output]
            self.failIf(len(self.stub.output) < 3)
            msg_exec = self.stub.output[-3]
            msg_summary = self.stub.output[-2]
            msg_output = self.stub.output[-1]
            for msg in self.stub.output[-3:-1]:
                self.assertEqual(str(msg["to"]), "dummy_from")
                self.assertEqual(str(msg["from"]), "dummy_to")
                self.assertEqual(str(msg["type"]), "chat")
                self.assertEqual(str(msg.thread), "dummy_thread")
            self.failIf("echo dummy_command arg1 arg2" not in
                        unicode(msg_exec.body))
            self.failUnless(unicode(msg_summary.body).startswith("OK."))
            self.assertEqual(str(msg_output.body), "")
        d.addCallback(check_output)
        reactor.callLater(2, d.callback, None) # attendre un peu
        return d

#    @deferred(10)
#    def test_cmd_failed(self):
#        """Test de l'envoi d'une commande qui échoue"""
#        self.conn.vigiconf_cmd = "false"
#        msg = ('<message type="chat" from="dummy_from" to="dummy_to">'
#               '<body>dummy</body></message>')
#        self.stub.send(parseXml(msg))
#        d = defer.Deferred()
#        def check_output(r):
#            #print [e.toXml() for e in self.stub.output]
#            self.failIf(len(self.stub.output) < 3)
#            msg_exec = self.stub.output[-3]
#            msg_summary = self.stub.output[-2]
#            msg_output = self.stub.output[-1]
#            for msg in self.stub.output[-3:-1]:
#                self.assertEqual(str(msg["to"]), "dummy_from")
#                self.assertEqual(str(msg["from"]), "dummy_to")
#                self.assertEqual(str(msg["type"]), "chat")
#            self.failIf("false dummy" not in unicode(msg_exec.body))
#            self.failIf("!" not in unicode(msg_summary.body))
#            self.assertEqual(str(msg_output.body), "")
#        d.addCallback(check_output)
#        reactor.callLater(1, d.callback, None) # attendre un peu
#        return d

