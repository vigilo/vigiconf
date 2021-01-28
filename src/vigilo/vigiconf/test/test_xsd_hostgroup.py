# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2011-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import

from .test_xsdutil import XSDTest

class HostGroupXSD(XSDTest):
    """
    Test du fichier hostgroup.xsd.
    The group.xsd file is used to validate host/service groups xml files
    """

    xsd_file = "group.xsd"

    xml_ok_files = {"hostgroups/ok": [
                        "hostgroups.xml",
                        "hostgroups2.xml",
                        "hostgroups3.xml",
                        "hostgroups4.xml",
                        ],
                     "../../../conf.d/groups": ["*.xml"],
                   }

    xml_ko_files = {"hostgroups/ko":[
                        "hostgroups1.xml",
                                      ]
                   }
