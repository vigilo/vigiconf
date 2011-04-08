# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904

from test_xsdutil import XSDTest

class HostXSD(XSDTest):
    """
    Test du fichier host.xsd.
    The host.xsd file is used to validate hosts xml files
    """

    xsd_file = "host.xsd"

    xml_ok_files = {
        "hosts/ok": [
            "example_nagios_spec.xml",
            "example_nagios_spec2.xml",
            "no_secondary_groups.xml",
            "interleaved_tags.xml",
            "localhost1.xml",
        ],
        "../../../conf.d/hosts": [
            "localhost.xml",
        ],
    }

    xml_ko_files = {
        "hosts/ko": [
        ],
    }

