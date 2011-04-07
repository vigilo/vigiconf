from test_xsdutil import XSDTest

class HosttemplateXSD(XSDTest):
    """ Test of the hosttemplate.xsd file.

    The hosttemplate.xsd file is used to validate host templates xml files"""

    xsd_file = "hosttemplate.xsd"

    xml_ok_files = {
        "hosttemplates/ok": [
            "interleaved_tags.xml",
        ],
        "../../../conf.d/hosttemplates": ["*.xml"],
   }

    xml_ko_files = {"hosttemplates/ko":[
                     "linux.xml", ]}
