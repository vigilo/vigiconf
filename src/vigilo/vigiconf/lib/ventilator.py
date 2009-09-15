################################################################################
#
# ConfigMgr host/server repartition balancer
# Copyright (C) 2007-2009 CS-SI
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
################################################################################

# pylint: disable-msg=E1101

"""
Module in charge of finding the good server to handle a given application 
for a given host defined in the configuration.

This file is part of the Enterprise Edition
"""

from __future__ import absolute_import

import os.path
import pickle

from .. import conf

__docformat__ = "epytext"

def saveToFile(o, fileName):
    """
    Save the state to a pickle file
    @param fileName: the filename to save to
    @type  fileName: C{str}
    """
    pickle.dump(o, open(fileName, 'wb'))

def getFromFile(fileName):
    """
    Get the state from a pickle file
    @param fileName: the filename to load from
    @type  fileName: C{str}
    """
    if os.path.exists(fileName):
        return pickle.load(open(fileName, 'rb'))
    else:
        return None

def getSize(serverName):
    """
    @param serverName: a server name
    @type  serverName: C{str}
    @return: the number of hosts held by a server
    @rtype: C{int}
    """
    o = getFromFile(getFileNameFromServerName(serverName))
    if o == None:
        return 0
    else:
        return len(o)

def getFileNameFromServerName(serverName):
    """
    @param serverName: server name
    @type  serverName: C{str}
    @return: path to the pickle file
    """
    return "%s/%s.pkl" % (os.path.join(conf.LIBDIR, "db"), serverName)

def appendHost(serverName, host):
    """
    Append a host to a pickle database
    @param serverName: server name
    @type  serverName: C{str}
    @param host: the host to append
    @type  host: C{str}
    """
    fileName = getFileNameFromServerName(serverName)
    o = getFromFile(fileName)
    if o == None:
        o = []
    o.append(host)
    saveToFile(o, fileName)


def getNextServerToUse(serverList):
    """
    @param serverList: the list of servers
    @type serverList: list of strings
    @return: the less busy server
    """
    n = 9999999999
    server = None
    for i in serverList:
        nn = getSize(i)
        if nn <= n :
            server = i
            n = nn
    return server

def getServerToUse(serverList, host):
    """
    Find the server to use for a given host.
    If the host is already handled by a server, return it.
    Choose the less busy otherwise.
    @param serverList: the list of servers
    @type serverList: list of strings
    @param host: the host name to handle
    @type  host: C{str}
    @return: the server to use
    @rtype:  C{str}
    """
    for i in serverList:
        o = getFromFile(getFileNameFromServerName(i))
        if o and host in o:
            return i
    # not found yet, choose next server
    s = getNextServerToUse(serverList)
    appendHost(s, host)
    return s

def findAServerForEachHost():
    """
    Try to find the best server where to monitor the hosts contained in the I{conf}.

    @return: a dict of the ventilation result. The dict content is:
      - B{Key}: name of a host 
      - B{value}: a dict in the form:
        - B{Key}: the name of an application for which we have to deploy a configuration for this host
          (Nagios, CorrSup, Collector...)
        - B{Value}: the hostname of the server where to deploy the conf for this host and this application

    I{Example}:

      >>> findAServerForEachHost()
      {
      ...
      "my_host_name":
        {
          'apacheRP': 'presentation_server.domain.name',
          'collector': 'collect_server_pool1.domain.name',
          'corrsup': 'correlation_server.domain.name',
          'corrtrap': 'correlation_server.domain.name',
          'dns': 'infra_server.domain.name',
          'nagios': 'collect_server_pool1.domain.name',
          'nagvis': 'presentation_server.domain.name',
          'perfdata': 'collect_server_pool1.domain.name',
          'rrdgraph': 'store_server_pool2.domain.name',
          'storeme': 'store_server_pool2.domain.name',
          'supnav': 'presentation_server.domain.name'
        }
      ...
      }

    """
    r = {}
    for (host, v) in conf.hostsConf.iteritems():
        hostGroup = v['serverGroup']
        hm = {}
        for appGroup in conf.appsGroupsByServer:
            l = conf.appsGroupsByServer[appGroup][hostGroup]
            if len(l) != 0 :
                if len(l) == 1:
                    server = l[0]
                else:
                    # choose wisely
                    server = getServerToUse(l, host)
                for app in conf.appsByAppGroups[appGroup]:
                    hm[app] = server
        r[host] = hm
    return r

if __name__ == "__main__":
    import pprint
    conf.loadConf()
    pprint.pprint(findAServerForEachHost())

# vim:set expandtab tabstop=4 shiftwidth=4:
