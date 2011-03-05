from test_xsdutil import XSDTest

class HostGroupXSD(XSDTest):
    """ Test of the hostgroup.xsd file.

    The group.xsd file is used to validate host/service groups xml files"""

    xsd_file = "../validation/xsd/group.xsd"

    xml_ok_files = {"testdata/xsd/hostgroups/ok": [
                                      "hostgroups.xml",
                                      "hostgroups2.xml",
                                      "hostgroups3.xml",
                                      "hostgroups4.xml",
                                      ],
                     "../conf.d/groups": ["*.xml"],
                   }

    xml_ko_files = {"testdata/xsd/hostgroups/ko":[
                                      "hostgroups1.xml",
                                      ]
                   }
