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

from . import conf

from .lib import ParsingError

def load_hostgroups(basedir):
    """ Loads Host groups from xml files.
    TODO: NYI
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

def load_servicegroups():
    """ Loads Service groups from xml files.
    TODO: NYI
    """
    pass

def load_dependencies():
    """ Loads dependencies from xml files.
    TODO: NYI
    """
    pass

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

