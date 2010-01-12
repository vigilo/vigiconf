#!/usr/bin/env python
################################################################################
#
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

"""
This module contains the DBExportator, a tool to export
hosts and services configuration into the vigilo database.
"""

from __future__ import absolute_import

import sys
import syslog

from vigilo.models.session import DBSession
from vigilo.models import Host, HostGroup, ServiceLowLevel, ServiceGroup

from . import conf


def export_conf_db():
    """
    Update database with hostConf data.
    @returns: None
    """
    hostsConf = conf.hostsConf
    hostsGroups = conf.hostsGroups
    
    # hosts groups
    try:
        for name, desc in hostsGroups.iteritems():
            hg = HostGroup.by_group_name(name)
            if not hg:
                hg = HostGroup(name=name)
            DBSession.add(hg)
    except:
        DBSession.rollback()
        raise
    
    # hosts
    try:
        for hostname, host in hostsConf.iteritems():
            h = Host.by_host_name(hostname)
            if h:
                # update host object
                h.checkhostcmd=host['checkHostCMD']
                h.hosttpl=host['hostTPL']
                h.snmpcommunity=host['community']
                h.mainip=host['mainIP']
                h.snmpport=host['port']
            else:
                # create host object
                h = Host(name=hostname, checkhostcmd=host['checkHostCMD'],
                               hosttpl=host['hostTPL'], snmpcommunity=host['community'],
                               mainip=host['mainIP'], snmpport=host['port'],
                               weight=1)
                DBSession.add(h)
    except:
        DBSession.rollback()
        raise
    
    # hosts
    try:
        for hostname, host in hostsConf.iteritems():
            for srvname, srv in host['services'].iteritems():
                s = ServiceLowLevel.by_host_service_name(hostname, srvname)
                if s:
                    s.command = srv['command']
                else:
                    # create service object
                    cmd = 'none'
                    if srv.has_key('command'):
                        cmd = srv['command']
                    s = ServiceLowLevel(servicename=srvname, op_dep='-',
                                        host=Host.by_host_name(hostname),
                                        command=cmd, weight=1)
                    DBSession.add(s)
    except:
        DBSession.rollback()
        raise
    
    DBSession.flush()


if __name__ == "__main__":
    syslog.openlog('DBExportator' , syslog.LOG_PERROR)
    syslog.syslog(syslog.LOG_INFO, "DBExportator Begin")

    try:
        conf.loadConf()
    except Exception,e :
        syslog.syslog(syslog.LOG_ERR, "Cannot load the conf.")
        syslog.syslog(syslog.LOG_ERR, str(e) )
        sys.exit(-1)

    export_conf_db()
    
    syslog.syslog(syslog.LOG_INFO, "DBExportator End")
