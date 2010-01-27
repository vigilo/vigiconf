from test_xsdutil import XSDTest

class HostXSD(XSDTest):
    """ Test of the host.xsd file.
    
    The host.xsd file is used to validate hosts xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/host.xsd"
    
    xml_ok_files = {"src/vigilo/vigiconf/conf.d/hosts":[
                                      "localhost.xml",
                                      "example.xml.dist",
                                      ]
                   }
    
    xml_ko_files = {"tests/testdata/xsd/hosts/ko":[
                                    "localhost1.xml", ]}
