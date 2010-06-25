from test_xsdutil import XSDTest

class HostGroupXSD(XSDTest):
    """ Test of the hostgroup.xsd file.
    
    The group.xsd file is used to validate host/service groups xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/group.xsd"
    
    xml_ok_files = {"tests/testdata/xsd/hostgroups/ok":[
                                      "hostgroups.xml",
                                      "hostgroups2.xml",
                                      "hostgroups3.xml",
                                      "hostgroups4.xml",
                                      ],
                    "tests/testdata/conf.d/groups":[
                                      "hostgroups.xml",
                                      "servicegroups.xml",
                                      ],
                   }
    
    xml_ko_files = {"tests/testdata/xsd/hostgroups/ko":[
                                      "hostgroups1.xml",
                                      ]
                   }
