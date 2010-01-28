from test_xsdutil import XSDTest

class HosttemplateXSD(XSDTest):
    """ Test of the hosttemplate.xsd file.
    
    The hosttemplate.xsd file is used to validate host templates xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/hosttemplate.xsd"
    
    xml_ok_files = {"src/vigilo/vigiconf/conf.d/hosttemplates":[
                                      #"aix.xml",
                                      "as400.xml",
                                      "cisco.xml",
                                      "default.xml",
                                      "linux.xml",
                                      "netapp.xml",
                                      "netware.xml",
                                      "nokia.xml",
                                      "nortel.xml",
                                      "pfs.xml",
                                      "solaris.xml",
                                      "windows.xml",
                                      ]
                   }
    
    xml_ko_files = {"tests/testdata/xsd/hosttemplates/ko":[
                                    "linux.xml", ]}
