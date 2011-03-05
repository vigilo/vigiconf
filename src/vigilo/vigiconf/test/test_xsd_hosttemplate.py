from test_xsdutil import XSDTest

class HosttemplateXSD(XSDTest):
    """ Test of the hosttemplate.xsd file.

    The hosttemplate.xsd file is used to validate host templates xml files"""

    xsd_file = "../validation/xsd/hosttemplate.xsd"

    xml_ok_files = {
        "../conf.d/hosttemplates": ["*.xml"],
        "testdata/xsd/hosttemplates/ok": [
            "interleaved_tags.xml",
        ],
   }

    xml_ko_files = {"testdata/xsd/hosttemplates/ko":[
                     "linux.xml", ]}
