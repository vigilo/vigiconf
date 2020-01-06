# -*- coding: utf-8 -*-
# Copyright (C) 2007-2020 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Generator for Nagios"""

from vigilo.common.conf import settings

import os.path

import networkx as nx

from vigilo.vigiconf import conf
from vigilo.vigiconf.lib.generators import FileGenerator

from sqlalchemy.orm import aliased
from vigilo.models.session import DBSession
from vigilo.models.tables import Host, Ventilation, VigiloServer, Dependency, \
                                    DependencyGroup, Application

class NagiosGen(FileGenerator):
    """
    This class is in charge of generating a nagios compliant configuration
    file given the internal data model of VigiConf (see conf.py)

    @todo: this really deserves a refactoring, use safety glasses
    """
    #    check_command           check-host-alive
    #<-     23 caracters      ->#
    pad = 23

    def generate(self):
        # pylint: disable-msg=W0201
        self._files = {}
        self._graph = None
        super(NagiosGen, self).generate()

    def generate_host(self, hostname, vserver):
        # pylint: disable-msg=W0201
        self.fileName = os.path.join(self.baseDir, vserver, "nagios",
                                     "nagios.cfg")
        if self.fileName not in self._files:
            self._files[self.fileName] = {}
        # loads the configuration for host
        h = conf.hostsConf[hostname]
        if not os.path.exists(self.fileName):
            # One Nagios server routes all its events to a single
            # connector-nagios instance.
            self.templateCreate(self.fileName, self.templates["header"], {
                    "confid": conf.confid,
                })
        newhash = h.copy()
        # Groups
        self.__fillgroups(hostname, newhash)

        # Dependencies
        parents = self._getdeps(hostname)
        if parents:
            newhash['parents'] = "parents ".ljust(self.pad) + ",".join(parents)
        else:
            newhash['parents'] = ""

        # directives generiques du type host
        newhash['generic_hdirectives'] =  "".join(["%s %s\n    " % \
            (directive.ljust(self.pad), val)
            for directive, val in \
                    newhash['nagiosDirectives']['host'].iteritems()])

        # Add the host definition
        self.templateAppend(self.fileName, self.templates['host'], newhash)

        # directives generiques du type services
        newhash['generic_sdirectives'] = ""
        generic_sdirectives = ""
        if "nagiosDirectives" in newhash:
            if "services" in newhash['nagiosDirectives']:
                for directive, value in \
                       newhash['nagiosDirectives']['services'].iteritems():
                    newhash['generic_sdirectives'] += "%s %s\n    " % \
                            (directive.ljust(self.pad), value)

        # Add the service item into the Nagios configuration file
        self.__fillservices(hostname, newhash)

        ## WARNING: ugly hack to handle routes (GCE based, must disappear)!!
        ## unused unless your host has a '-RT-DC' in its name
        ## TODO: use tags
        #if h['name'].count('-RT-DC'):
        #    if len(h['routeItems']):
        #        for kk in self.mapping.keys():
        #            hh = conf.hostsConf[kk]
        #            if hh['name'].count('-RT-DC'):
        #                if len(hh['routeItems']):
        #                    for (kkk) in hh['routeItems'].keys():
        #                        sname = 'route '+hh['routeItems'][kkk]
        #                        self.templateAppend(self.fileName,
        #                                        self.templates["collector"],
        #                                        {'name': h['name'],
        #                                        'serviceName': sname})

    def __fillgroups(self, hostname, newhash):
        """Fill the groups in the configuration file"""
        h = conf.hostsConf[hostname]
        if h.get("otherGroups", None):
            newhash['hostGroups'] = "%s %s" % \
                    ("hostgroups".ljust(self.pad), ','.join(h['otherGroups']))
            # builds a list of all groups memberships
            for i in h['otherGroups']:
                if i not in self._files[self.fileName]:
                    self._files[self.fileName][i] = 1
                    # @TODO: réfléchir à la gestion des groupes Nagios.
                    # L'ancien code a été conservé ci-dessous.
                    self.templateAppend(self.fileName,
                                    self.templates["hostgroup"],
                                    {'hostgroupName': i,
                                     'hostgroupAlias': i})
#                    self.templateAppend(self.fileName,
#                                    self.templates["hostgroup"],
#                                    {"hostgroupName": i,
#                                     "hostgroupAlias": conf.hostsGroups[i]})
        else:
            newhash['hostGroups'] = "# no hostgroups defined"

    def _build_topology(self):
        """
        Construit la topologie dans un graphe NetworkX, accessible par
        C{self._graph}.
        """
        self._graph = nx.DiGraph()

        # On récupère dans la BDD la liste des dépendances.
        # note: l'argument alias évite la création d'une sous-requête inutile
        host1 = aliased(Host, alias=Host.__table__.alias())
        host2 = aliased(Host, alias=Host.__table__.alias())
        dependencies = DBSession.query(
                            host1.name.label('host1'),
                            host2.name.label('host2'),
                            VigiloServer.name.label('vserver'),
                        ).join(
                            (Dependency, Dependency.idsupitem == host1.idhost),
                            (DependencyGroup, DependencyGroup.idgroup ==
                                Dependency.idgroup),
                            (host2, host2.idhost == DependencyGroup.iddependent),
                            (Ventilation, Ventilation.idhost ==
                                Dependency.idsupitem),
                            (VigiloServer, VigiloServer.idvigiloserver ==
                                Ventilation.idvigiloserver),
                            (Application, Application.idapp ==
                                Ventilation.idapp),
                        ).filter(DependencyGroup.role == u'topology'
                        ).filter(Application.name == u'nagios'
                        ).all()

        # On ajoute ces dépendances dans le graphe en tant qu'arcs.
        for dependency in dependencies:
            self._graph.add_edge(dependency.host1, dependency.host2,
                                 vserver=dependency.vserver)


    def _getdeps(self, hostname):
        """
        @param hostname: hôte à considérer
        @type  hostname: C{str}
        @return: Parents topologiques de l'hôte
        @rtype: C{list}
        """
        if self._graph is None:
            self._build_topology()

        if hostname not in self._graph.node:
            return []

        vserver = self.ventilation[hostname]['nagios']
        if isinstance(vserver, list):
            vserver = vserver[0]

        deps = [ p for p in self._graph.predecessors(hostname)
                 if self._graph.edge[p][hostname]['vserver'] == vserver ]
        return deps

    def __fillservices(self, hostname, newhash):
        """Fill the services section in the configuration file"""
        h = conf.hostsConf[hostname]
        for (srvname, srvdata) in h['services'].iteritems():
            scopy = srvdata.copy()

            # directives generiques du type services
            generic_sdirectives = ""
            if "nagiosDirectives" in newhash:
                if "services" in newhash['nagiosDirectives']:
                    for directive, value in \
                        newhash['nagiosDirectives']['services'].iteritems():
                            generic_sdirectives += "%s %s\n    " % \
                                        (directive.ljust(self.pad), value)
            if newhash['nagiosSrvDirs'].has_key(srvname):
                for directive, value in \
                        newhash['nagiosSrvDirs'][srvname].iteritems():
                            generic_sdirectives += "%s %s\n    " % \
                                    (directive.ljust(self.pad), value)
            # Handle command definition
            if scopy.has_key('command') and scopy['type'] == 'active' and \
                     not h['force-passive']:
                generic_sdirectives += "%s %s\n    " % \
                        ("check_command".ljust(self.pad), scopy['command'])
            # Handle perfdata
            if srvname in h['PDHandlers']:
                generic_sdirectives += "%s 1\n    " % \
                    "process_perf_data".ljust(self.pad)

            if h['force-passive']:
                # forcing passive type of service
                tpltype = "passive"
            else:
                tpltype = scopy['type']
            self.templateAppend(self.fileName, self.templates[tpltype],
                        {'name': h['name'],
                         'serviceName': srvname,
                         'generic_sdirectives': generic_sdirectives.rstrip()})

# vim:set expandtab tabstop=4 shiftwidth=4:
