from test_xsdutil import XSDTest

class HosttemplateXSD(XSDTest):
    """ Test of the hosttemplate.xsd file.
    
    The hosttemplate.xsd file is used to validate host templates xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/hosttemplate.xsd"
    
    xml_ok_files = {
        "src/vigilo/vigiconf/conf.d/hosttemplates": ["*.xml"],
        "tests/testdata/xsd/hosttemplates/ok": [
            "interleaved_tags.xml",
        ],
   }
    
    xml_ko_files = {"tests/testdata/xsd/hosttemplates/ko":[
                                    "linux.xml", ]}
