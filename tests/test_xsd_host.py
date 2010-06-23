from test_xsdutil import XSDTest

class HostXSD(XSDTest):
    """ Test of the host.xsd file.
    
    The host.xsd file is used to validate hosts xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/host.xsd"
    
    xml_ok_files = {"tests/testdata/conf.d/hosts":[
                                      "localhost.xml",
                                      ],
                    "tests/testdata/xsd/hosts/ok":[
                                    "example_nagios_spec.xml", ]
                   }
    
    xml_ko_files = {"tests/testdata/xsd/hosts/ko":[
                                    "localhost1.xml",
                                    "example_nagios_spec2.xml",
                                    "missing_weight_attribute.xml",
                                    ]}
