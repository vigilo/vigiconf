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

from vigilo.common.conf import settings
from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.models.session import DBSession

from vigilo.models import HostGroup, ServiceGroup
from vigilo.models import Host, LowLevelService, HighLevelService, Dependency

from . import conf

from .lib import ParsingError

def load_hostgroups(basedir):
    """ Loads Host groups from xml files.
    
        @param basedir: a directory containing hostgroups definitions files
        @type  basedir: C{str}
    """
    for root, dirs, files in os.walk(basedir):
        for f in files:
            if not f.endswith(".xml"):
                continue
            path = os.path.join(root, f)
            validate(path, "hostgroup.xsd")
            # load hostgroups
            _load_hostgroups_from_xml(path)
            pass
        
            LOGGER.debug("Sucessfully parsed %s" % path)
        for d in dirs: # Don't visit subversion/CVS directories
            if d.startswith("."):
                dirs.remove(d)
            if d == "CVS":
                dirs.remove("CVS")

def load_servicegroups(basedir):
    """ Loads Service groups from xml files.
    
        @param basedir: a directory containing servicegroups definitions files
        @type  basedir: C{str}
    """
    for root, dirs, files in os.walk(basedir):
        for f in files:
            if not f.endswith(".xml"):
                continue
            path = os.path.join(root, f)
            validate(path, "servicegroup.xsd")
            # load servicegroups
            _load_servicegroups_from_xml(path)
            pass
        
            LOGGER.debug("Sucessfully parsed %s" % path)
        for d in dirs: # Don't visit subversion/CVS directories
            if d.startswith("."):
                dirs.remove(d)
            if d == "CVS":
                dirs.remove("CVS")

def load_dependencies(basedir):
    """ Loads dependencies from xml files.
    
        @param basedir: a directory containing dependency definitions files
        @type  basedir: C{str}
    """
    for root, dirs, files in os.walk(basedir):
        for f in files:
            if not f.endswith(".xml"):
                continue
            path = os.path.join(root, f)
            validate(path, "dependency.xsd")
            # load dependencies
            _load_dependencies_from_xml(path)
            pass
        
            LOGGER.debug("Sucessfully parsed %s" % path)
        for d in dirs: # Don't visit subversion/CVS directories
            if d.startswith("."):
                dirs.remove(d)
            if d == "CVS":
                dirs.remove("CVS")

def validate(xmlfile, xsdfilename):
        """
        Validate the XML against the DTD using xmllint

        @note: this could take time.
        @todo: use lxml for python-based validation
        @param xmlfile: an XML file
        @type  xmlfile: C{str}
        @param  xsdfilename: an XSD file name (present in the validation/xsd directory)
        @type  xsdfilename: C{str}
        """
        xsd = os.path.join(os.path.dirname(__file__),
                           "validation", "xsd", xsdfilename)
        result = subprocess.call(["xmllint", "--noout", "--schema", xsd, xmlfile])
        if result != 0:
            raise ParsingError("XML validation failed")

def _load_hostgroups_from_xml(filepath):
    """ Loads Host groups from a xml file.
    
        @param xmlfile: an XML file
        @type  xmlfile: C{str}
    """
    parent_stack = []
    current_parent = None
    
    try:
        for event, elem in ET.iterparse(filepath, events=("start", "end")):
            if event == "start":
                if elem.tag == "hostgroup":
                    name = elem.attrib["name"].strip()
                    hostgroup = HostGroup.by_group_name(groupname=name)
                    if not hostgroup:
                        hostgroup = HostGroup(name=name)
                        DBSession.add(hostgroup)
                    else:
                        hostgroup.children = []
                    
                    if current_parent:
                        hostgroup.parent = current_parent
                    # update parent stack
                    parent_stack.append(hostgroup)
                elif elem.tag == "children":
                    current_parent = parent_stack[-1]
            else:
                if elem.tag == "hostgroup":
                    if len(parent_stack) > 0:
                        parent_stack.pop()
                elif elem.tag == "children":
                    current_parent = None
        DBSession.flush()
    except:
        DBSession.rollback()
        raise

def _load_servicegroups_from_xml(filepath):
    """ Loads Host groups from a xml file.
    
        @param xmlfile: an XML file
        @type  xmlfile: C{str}
    """
    parent_stack = []
    current_parent = None
    
    try:
        for event, elem in ET.iterparse(filepath, events=("start", "end")):
            if event == "start":
                if elem.tag == "servicegroup":
                    name = elem.attrib["name"].strip()
                    hostgroup = HostGroup.by_group_name(groupname=name)
                    if not hostgroup:
                        hostgroup = HostGroup(name=name)
                        DBSession.add(hostgroup)
                    else:
                        hostgroup.children = []
                    
                    if current_parent:
                        hostgroup.parent = current_parent
                    # update parent stack
                    parent_stack.append(hostgroup)
                elif elem.tag == "children":
                    current_parent = parent_stack[-1]
            else:
                if elem.tag == "servicegroup":
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
    dependency = False
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
                        raise Exception("No dependant supitem (host or service)")
                    
                    dependency = False
                    # retrieve hosts and services from db
                    supitems2 = []
                    for hname in subhosts:
                        supitems2.append(Host.by_host_name(hname))
                        for sname in subservices:
                            supitems2.append(
                             LowLevelService.by_host_service_name(hname, sname)
                            )
                    # create dependency links
                    for hname in hostnames:
                        host = Host.by_host_name(hname)
                        if not host:
                            raise Exception("host %s does not exist" % hname)
                        
                        for supitem2 in supitems2:
                            if not supitem2:
                                continue
                            dep = Dependency(supitem1=host, supitem2=supitem2)
                            DBSession.add(dep)
                    for sname in servicenames:
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
