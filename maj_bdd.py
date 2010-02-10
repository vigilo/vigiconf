# -*- coding: utf-8 -*-
from sqlalchemy import and_

#from vigiconf import model
#from vigiconf.model import DBSession
from vigilo.models.configure import DBSession
#from vigilo.models.session import DBSession
from vigilo.models import VigiloServer, AppGroup, Host, \
        Host_VigiloServer_AppGroup


from datetime import datetime

import transaction

#DBSession.autocommit = True

# VigiloServer (VigiloServer)
def add_srv(fqdn):
    s = DBSession.query(VigiloServer).filter(VigiloServer.fqdn == fqdn).first()
    if not s:
        s = VigiloServer(fqdn=fqdn)
        print "Ajout du Serveur Vigilo: ", fqdn
        DBSession.add(s)
    return s

# Groupe d'Application Vigilo (AppGroup)
def add_appgroup(name):
    ag = DBSession.query(AppGroup) \
         .filter(AppGroup.name == name) \
         .first()
    if not ag:
        ag = AppGroup(name=name)
        print "Ajout du groupe d'application: ", name
        DBSession.add(ag)
    return ag

# Hôte (Host)
def add_host(name, checkhostcmd, hosttpl, snmpcommunity, mainip, snmpport):
    h = DBSession.query(Host).filter(Host.name == name).first()
    if not h:
        h = Host(name=name, checkhostcmd=checkhostcmd,
                       hosttpl=hosttpl, snmpcommunity=snmpcommunity, mainip=mainip, snmpport=snmpport)
        print "Ajout de l'hôte: ", name
        DBSession.add(h)
    return h

# table de liaison (Host_VigiloServer_AppGroup)
def add_liaison(fqdn, idappgroup, idsrv):
    l = DBSession.query(Host_VigiloServer_AppGroup) \
            .filter(Host_VigiloServer_AppGroup.fqdn == fqdn) \
            .filter(Host_VigiloServer_AppGroup.idappgroup == idappgroup) \
            .filter(Host_VigiloServer_AppGroup.idsrv == idsrv) \
            .first()
    if not l:
        l = Host_VigiloServer_AppGroup(fqdn=fqdn, 
                                             idappgroup=idappgroup, 
                                             idsrv=idsrv)
        print "ajout de la liaison: ", (fqdn, idappgroup, idsrv)
        DBSession.add(l)
    return l


s1 = add_srv(u'srv1')
s2 = add_srv(u'srv2')
s3 = add_srv(u'srv3')
s4 = add_srv(u'srv1') # test de l'ajout de deux fois le même serveur

ag1 = add_appgroup(u'collect')
ag2 = add_appgroup(u'metro')
ag3 = add_appgroup(u'trap')
ag4 = add_appgroup(u'dns')

h1 = add_host(u'proto4.si.c-s.fr', u'dummy', u'linuxserver', u'public', u'127.0.0.1', u'12')
h2 = add_host(u'messagerie.si.c-s.fr', u'dummy', u'linuxserver', u'public', u'127.0.0.1', u'12')
h3 = add_host(u'testnortel.si.c-s.fr', u'dummy', u'switch', u'public', u'127.0.0.1', u'12')
h4 = add_host(u'proto6.si.c-s.fr', u'dummy', u'ciscorouter', u'public', u'127.0.0.1', u'12')

h_s_ag =  add_liaison(h1.name, ag1.idappgroup, s1.idsrv)
h_s_ag =  add_liaison(h1.name, ag2.idappgroup, s1.idsrv)
h_s_ag =  add_liaison(h2.name, ag1.idappgroup, s2.idsrv)
h_s_ag =  add_liaison(h2.name, ag1.idappgroup, s3.idsrv)
h_s_ag =  add_liaison(h3.name, ag1.idappgroup, s4.idsrv)
h_s_ag =  add_liaison(h3.name, ag1.idappgroup, s4.idsrv)

transaction.commit()
