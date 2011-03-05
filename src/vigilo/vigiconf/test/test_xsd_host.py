from test_xsdutil import XSDTest

class HostXSD(XSDTest):
    """ Test of the host.xsd file.

    The host.xsd file is used to validate hosts xml files"""

    xsd_file = "../validation/xsd/host.xsd"

    xml_ok_files = {
        "testdata/xsd/hosts/ok": [
            "example_nagios_spec.xml",
            "example_nagios_spec2.xml",
            "no_secondary_groups.xml",
            "interleaved_tags.xml",
            "localhost1.xml",
        ],
        "../conf.d/hosts": [
            "localhost.xml",
        ],
    }

    xml_ko_files = {
        "testdata/xsd/hosts/ko": [
        ],
    }
