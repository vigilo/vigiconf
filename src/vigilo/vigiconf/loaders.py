# -*- coding: utf-8 -*-
################################################################################
#
# ConfigMgr configuration files generation wrapper
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
Data loaders for models like HostGroup, ServiceGroup, Dependency.

File format: XML
Notice: some other models like Host have their own loader (confclasses)
TODO: confclasses refactoring needed ?
"""
import os
import subprocess

from xml.etree import ElementTree as ET # Python 2.5

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

#from vigilo.models.session import DBSession
from vigilo.models.configure import DBSession

from vigilo.models import HostGroup, ServiceGroup
from vigilo.models import Host, LowLevelService, HighLevelService, Dependency

from . import conf

from .lib import ParsingError

__docformat__ = "epytext"

# VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
#   configurations de la supervision en mode CLI
#
#   configuration des groupes d'hôtes : ajout/modification/suppression d'un
#   groupe d'hôte
def load_hostgroups(basedir):
    """ Loads Host groups from xml files.
    
        @param basedir: a directory containing hostgroups definitions files
        @type  basedir: C{str}
    """
    _load_from_xmlfiles(basedir, "hostgroup.xsd", _load_hostgroups_from_xml)


# VIGILO_EXIG_VIGILO_CONFIGURATION_0010 : Fonctions de préparation des
#   configurations de la supervision en mode CLI
#
#   configuration d'un groupe de service : ajout/modification/suppression d'un
#     groupe de service
#   configuration des services de haut niveau : ajout/modification/suppression
#     d'un service
#   configuration des règles de corrélations associé à un service de haut
#     niveau : ajout/modification/suppression d'une règle de corrélation
def load_servicegroups(basedir):
    """ Loads Service groups from xml files.
    
        @param basedir: a directory containing servicegroups definitions files
        @type  basedir: C{str}
    """
    _load_from_xmlfiles(basedir, "servicegroup.xsd",
                        _load_servicegroups_from_xml)

def load_dependencies(basedir):
    """ Loads dependencies from xml files.
    
        @param basedir: a directory containing dependency definitions files
        @type  basedir: C{str}
    """
    _load_from_xmlfiles(basedir, "dependency.xsd", _load_dependencies_from_xml)

def load_hlservices(basedir):
    """ Loads dependencies from xml files.
    
        @param basedir: a directory containing dependency definitions files
        @type  basedir: C{str}
    """
    _load_from_xmlfiles(basedir, "hlservice.xsd", _load_hlservices_from_xml)


def _load_from_xmlfiles(basedir, xsd_file, handler):
    """ Generic loader of data from xml files.
    
        @param basedir: a directory containing xml files
        @type  basedir: C{str}
        @param xsd_file: a xsd file for validation
        @type  xsd_file: C{str}
        @param handler:  a processing function for a xml file with one argument (path)
        @type  handler: C{function}
    """
    for root, dirs, files in os.walk(basedir):
        for f in files:
            if not f.endswith(".xml"):
                continue
            path = os.path.join(root, f)
            _validate(path, xsd_file)
            # load data
            handler(path)
        
            LOGGER.debug("Sucessfully parsed %s" % path)
        for d in dirs: # Don't visit subversion/CVS directories
            if d.startswith("."):
                dirs.remove(d)
            if d == "CVS":
                dirs.remove("CVS")


def _validate(xmlfile, xsdfilename):
    """
    Validate the XML against the DTD using xmllint
    
    @note: this could take time.
    @todo: use lxml for python-based validation
    @param xmlfile: an XML file
    @type  xmlfile: C{str}
    @param  xsdfilename: an XSD file name (present in the validation/xsd dir)
    @type  xsdfilename: C{str}
    """
    xsd = os.path.join(os.path.dirname(__file__),
                       "validation", "xsd", xsdfilename)
    result = subprocess.call(["xmllint", "--noout", "--schema", xsd, xmlfile])
    if result != 0:
        raise ParsingError("XML validation failed")


def _load_hostgroups_from_xml(path):
    """ Loads Host groups from a xml file.
    
        @param path: an XML file
        @type  path: C{str}
    """
    _load_groups_from_xml(path, HostGroup, "hostgroup")

def _load_servicegroups_from_xml(path):
    """ Loads Service groups from a xml file.
    
        @param path: an XML file
        @type  path: C{str}
    """
    _load_groups_from_xml(path, ServiceGroup, "servicegroup")

def _load_groups_from_xml(filepath, classgroup, tag_group):
    """ Loads Host or service groups from a xml file.
    
        @param filepath: an XML file
        @type  filepath: C{str}
        @param classgroup HostGroup or ServiceGroup
        @type  filepath: C{class}
        @param tag_group "hostgroup" or "servicegroup"
        @type  filepath: C{str}
    """
    parent_stack = []
    current_parent = None
    
    try:
        for event, elem in ET.iterparse(filepath, events=("start", "end")):
            if event == "start":
                if elem.tag == tag_group:
                    name = unicode(elem.attrib["name"].strip())
                    group = classgroup.by_group_name(groupname=name)
                    if not group:
                        group = classgroup(name=name)
                        DBSession.add(group)
                    else:
                        group.children = []
                    
                    if current_parent:
                        if group.parent:
                            if group.parent.name != current_parent.name:
                                raise Exception(
                "%s %s should have one parent (%s, %s)" %
                (tag_group, group.name, group.parent.name,
                 current_parent.name)
                                    )
                        group.parent = current_parent
                    # update parent stack
                    parent_stack.append(group)
                elif elem.tag == "children":
                    current_parent = parent_stack[-1]
            else:
                if elem.tag == tag_group:
                    if len(parent_stack) > 0:
                        parent_stack.pop()
                elif elem.tag == "children":
                    current_parent = None
        DBSession.flush()
    except:
        DBSession.rollback()
        raise


def _load_dependencies_from_xml(filepath):
    """ Loads dependencies from a xml file.
    
        @param xmlfile: an XML file
        @type  xmlfile: C{str}
    """
    subitems = False
    levelservices1 = {}
    levelservices2 = {}
    
    try:
        for event, elem in ET.iterparse(filepath, events=("start", "end")):
            if event == "start":
                if elem.tag == "dependency":
                    dependency = True
                    hostnames = []
                    servicenames = []
                elif elem.tag == "host":
                    if subitems:
                        subhosts.append(elem.attrib["name"].strip())
                    else:
                        hostnames.append(elem.attrib["name"].strip())
                elif elem.tag == "service":
                    name = elem.attrib["name"].strip()
                    if elem.attrib.has_key("level"):
                        level = elem.attrib["level"].strip()
                    else:
                        level = None
                    if subitems:
                        if not level: level = "low"
                        subservices.append(name)
                        levelservices2[name] = level
                    else:
                        if not level: level = "high"
                        servicenames.append(name)
                        levelservices1[name] = level
                elif elem.tag == "subitems":
                    subitems = True
                    subhosts = []
                    subservices = []
            else:
                if elem.tag == "dependency":
                    
                    # verifier si au moins 1 dependant (host ou service)
                    if len(hostnames) == 0 and len(servicenames) == 0:
                        raise Exception(
                                    "No dependant supitem (host or service)"
                              )
                    
                    dependency = False
                    # retrieve hosts and services from db
                    supitems2 = []
                    for hname in subhosts:
                        supitems2.append(Host.by_host_name(hname))
                        for sname in subservices:
                            supitems2.append(
                             LowLevelService.by_host_service_name(hname, sname)
                            )
                    
                    # recueil des low level services dépendants
                    llservicesnames = []
                    for sname in servicenames:
                        if levelservices1[sname] == "low":
                            llservicesnames.append(sname)
                    
                    # erreur si low level service sans host
                    if len(hostnames) == 0 and len(llservicesnames) > 0:
                        raise Exception(
                            "low level services without a host declaration"
                            % ", ".join(llservices))
            
                    # create dependency links
                    for hname in hostnames:
                        supitem1 = Host.by_host_name(hname)
                        if not supitem1:
                            raise Exception("host %s does not exist" % hname)
                        
                        supitems1 = []
                        for sname in llservicesnames:
                            lls = LowLevelService.by_host_service_name(
                                                                hname, sname
                                                                )
                            if not lls:
                                raise Exception(
                                       "low level service %s/%s does not exist"
                                       % (hname, sname))
                            supitems1.append(lls)
                            
                        if len(supitems1) == 0:
                            supitems1 = [supitem1, ]
                        
                        for supitem1 in supitems1:
                            for supitem2 in supitems2:
                                if not supitem2:
                                    continue
                                    
                                dep = Dependency(supitem1=supitem1,
                                                 supitem2=supitem2)
                                DBSession.add(dep)
                    
                    for sname in servicenames:
                        if levelservices1[sname] == "low": continue
                        
                        hls = HighLevelService.by_service_name(sname)
                        if not hls:
                            raise Exception("HLS %s does not exist" % sname)
                        for supitem2 in supitems2:
                            if not supitem2:
                                continue
                            dep = Dependency(supitem1=hls, supitem2=supitem2)
                            DBSession.add(dep)
                        
                        
                        
                elif elem.tag == "host":
                    pass
                elif elem.tag == "service":
                    level = None
                elif elem.tag == "subitems":
                    subitems=False
        DBSession.flush()
    except:
        DBSession.rollback()
        raise

def _load_hlservices_from_xml(filepath):
    """ Loads high level services from a xml file.
    
        @param filepath: an XML file
        @type  filepath: C{str}
    """
    
    try:
        for event, elem in ET.iterparse(filepath, events=("start", "end")):
            if event == "start":
                if elem.tag == "hlservice":
                    name = elem.attrib["name"].strip()
                    groups = []
                    message = None
                elif elem.tag == "message":
                    message = elem.text
                elif elem.tag == "warning_threshold":
                    warning_threshold = int(elem.attrib["value"].strip())
                elif elem.tag == "critical_threshold":
                    critical_threshold = int(elem.attrib["value"].strip())
                elif elem.tag == "priority":
                    priority = int(elem.attrib["value"].strip())
                elif elem.tag == "op_dep":
                    op_dep = elem.attrib["value"].strip()
                elif elem.tag == "group":
                    group = elem.attrib["name"].strip()
                    groups.append(group)
            else:
                if elem.tag == "hlservice":
                    # on instancie ou on récupère le HLS
                    hls = HighLevelService.by_service_name(name)
                    if hls:
                        hls.servicename = unicode(name)
                        hls.op_dep = unicode(op_dep)
                        hls.message = unicode(message)
                        hls.priority = priority
                        hls.warning_threshold = warning_threshold
                        hls.critical_threshold = critical_threshold
                    else:
                        hls = HighLevelService(servicename=unicode(name),
                                       op_dep=unicode(op_dep),
                                       message=unicode(message),
                                       priority=priority,
                                       warning_threshold=warning_threshold,
                                       critical_threshold=critical_threshold
                                               )
                        DBSession.add(hls)
                    # ajout des groupes
                    hls.groups = []
                    for gname in groups:
                        sg = ServiceGroup.by_group_name(gname)
                        if not sg:
                            raise Exception("Service group %s does not exist."
                                            % gname)
                        hls.groups.append(sg)
                    
                    # ajout des impacts
                    # les impacts sont ajoutés après le traitement de
                    # l'ensemble des fichiers
                    
        DBSession.flush()
    except:
        DBSession.rollback()
        raise

