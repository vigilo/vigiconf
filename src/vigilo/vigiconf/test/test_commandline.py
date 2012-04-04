# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# pylint: disable-msg=C0111,W0212,R0904
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

import unittest
import sys

from mock import Mock

from vigilo.vigiconf import commandline


class CommandLineTest(unittest.TestCase):

    def setUp(self):
        mock_os = Mock(name="os")
        mock_os.getuid.return_value = 0
        mock_os.environ = {}
        sys.modules["os"] = mock_os
        mock_pw_entry = Mock(name="pw_entry")
        mock_pw_entry.pw_name = "vigiconf"
        mock_pw_entry.pw_uid = 142
        mock_pw_entry.pw_gid = 242
        mock_pw_entry.pw_dir = "/home/for/vigiconf"
        mock_pw_entry.pw_shell = "/shell/for/vigiconf"
        mock_pwd = Mock(name="pwd")
        mock_pwd.getpwuid.return_value = mock_pw_entry
        mock_pwd.getpwnam.return_value = mock_pw_entry
        sys.modules["pwd"] = mock_pwd

    def tearDown(self):
        del sys.modules["os"]
        del sys.modules["pwd"]

    def test_change_user(self):
        commandline.change_user()
        self.assertEqual(sys.modules["os"].environ,  {
                'USERNAME': "vigiconf",
                'HOME': "/home/for/vigiconf",
                'SHELL': "/shell/for/vigiconf",
                'LOGNAME': "vigiconf",
                'USER': "vigiconf",
        })
        self.assertEqual(sys.modules["os"].method_calls, [
                ('getuid', (), {}),
                ('setregid', (242, 242), {}),
                ('initgroups', ("vigiconf", 242), {}),
                ('setreuid', (142, 142), {}),
                ('getuid', (), {})
        ])

