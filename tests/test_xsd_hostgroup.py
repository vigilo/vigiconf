from test_xsdutil import XSDTest

class HostGroupXSD(XSDTest):
    """ Test of the host.xsd file.
    
    The host.xsd file is used to validate hosts xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/hostgroup.xsd"
    
    xml_ok_files = {"tests/testdata/":[
                                      "hostgroups.xml",
                                      ]
                   }
    
    xml_ko_files = {"tests/testdata/xsd/hostgroups/ko":[]}
