# vim: set fileencoding=utf-8 sw=4 ts=4 et :
"""
Connecteur VigiConf - XMPP
"""

import sys, os

from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.application import service


from vigilo.common.gettext import translate
from vigilo.connector import client, options

_ = translate('vigilo.vigiconf')

class VigiConfConnectorServiceMaker(object):
    """
    Creates a service that wraps everything the connector needs.
    """
    implements(service.IServiceMaker, IPlugin)
    tapname = "vigilo-vigiconf"
    description = "Vigilo connector for VigiConf"
    options = options.Options

    def makeService(self, options):
        """ the service that wraps everything the connector needs. """
        from vigilo.common.conf import settings
        if options["config"] is not None:
            settings.load_file(options["config"])
        else:
            settings.load_module('vigilo.vigiconf')

        from vigilo.common.logging import get_logger
        LOGGER = get_logger('vigilo.vigiconf.connector')

        from vigilo.vigiconf.connector.xmpptovigiconf import XMPPToVigiConf, \
                    VigiConfMessageProtocol, AutoSubscribeProtocol

        xmpp_client = client.client_factory(settings)
        forwarder = XMPPToVigiConf()
        forwarder.setHandlerParent(xmpp_client)
        messageprotocol = VigiConfMessageProtocol(forwarder)
        messageprotocol.setHandlerParent(xmpp_client)
        autosub = AutoSubscribeProtocol()
        autosub.setHandlerParent(xmpp_client)

        # Présence
        from vigilo.connector.presence import PresenceManager
        presence_manager = PresenceManager()
        presence_manager.setHandlerParent(xmpp_client)

        # Statistiques
        from vigilo.connector.status import StatusPublisher
        servicename = options.get("name", "vigilo-connector-vigiconf")
        stats_publisher = StatusPublisher(forwarder,
                            settings["connector"].get("hostname", None),
                            servicename=servicename)
        stats_publisher.setHandlerParent(xmpp_client)

        root_service = service.MultiService()
        xmpp_client.setServiceParent(root_service)
        return root_service

vigiconf_connector = VigiConfConnectorServiceMaker()
