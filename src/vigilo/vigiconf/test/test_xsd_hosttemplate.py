# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2011-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>
from __future__ import absolute_import

from .test_xsdutil import XSDTest

class HosttemplateXSD(XSDTest):
    """
    Test du fichier hosttemplate.xsd.
    The hosttemplate.xsd file is used to validate host templates xml files
    """

    xsd_file = "hosttemplate.xsd"

    xml_ok_files = {
        "hosttemplates/ok": [
            "interleaved_tags.xml",
            "passive_tags.xml",
        ],
        "../../../conf.d/hosttemplates": ["*.xml"],
   }

    xml_ko_files = {"hosttemplates/ko":[
                     "linux.xml", ]}
