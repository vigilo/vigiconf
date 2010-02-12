from test_xsdutil import XSDTest

class ServiceGroupXSD(XSDTest):
    """ Test of the servicegroup.xsd file.
    
    The servicegroup.xsd file is used to validate service groups xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/servicegroup.xsd"
    
    xml_ok_files = {"tests/testdata/xsd/servicegroups/ok":[
                                      "servicegroups.xml",
                                      "servicegroups1.xml",
                                      "servicegroups2.xml",
                                     ],
                    "src/vigilo/vigiconf/conf.d/servicegroups":[
                                      "servicegroups.xml",
                                      ]
                   }
    
    xml_ko_files = {"tests/testdata/xsd/servicegroups/ko":[
                                       "servicegroups3.xml",
                                      ]
                   }
