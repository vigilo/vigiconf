from test_xsdutil import XSDTest

class HostGroupXSD(XSDTest):
    """ Test of the hostgroup.xsd file.
    
    The hostgroup.xsd file is used to validate host groups xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/hostgroup.xsd"
    
    xml_ok_files = {"tests/testdata/xsd/hostgroups/ok":[
                                      "hostgroups.xml",
                                      "hostgroups2.xml",
                                      "hostgroups3.xml",
                                      ],
                    "tests/testdata/xsd/hostgroups/ko/loader_ko/1":[
                                      "hostgroups4.xml",
                                      ]
                   }
    
    xml_ko_files = {"tests/testdata/xsd/hostgroups/ko":[
                                      "hostgroups1.xml",
                                      ]
                   }
