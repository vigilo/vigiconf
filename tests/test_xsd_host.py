from test_xsdutil import XSDTest

class HostXSD(XSDTest):
    """ Test of the host.xsd file.
    
    The host.xsd file is used to validate hosts xml files"""
    
    xsd_file = "src/vigilo/vigiconf/validation/xsd/host.xsd"
    
    xml_ok_files = {
        "tests/testdata/conf.d/hosts": [
            "localhost.xml",
        ],
        "tests/testdata/xsd/hosts/ok": [
            "example_nagios_spec.xml",
            "no_secondary_groups.xml",
            "interleaved_tags.xml",
            "localhost1.xml",
        ],
    }
    
    xml_ko_files = {"tests/testdata/xsd/hosts/ko":[
                                    "example_nagios_spec2.xml",
                                    ]}
