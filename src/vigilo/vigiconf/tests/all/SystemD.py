# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
#pylint: disable-msg=C0301,C0111,W0232,R0201,R0903,W0221
# Copyright (C) 2020-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

from __future__ import unicode_literals

from vigilo.vigiconf.lib.confclasses.validators import arg, String, Bool, Enum, List
from vigilo.vigiconf.lib.confclasses.test import Test
from vigilo.common.gettext import l_


class SystemD(Test):
    """Check the state of a SystemD unit/system"""

    _states = ('active', 'reloading', 'inactive', 'failed', 'activating',
               'deactivating')
    _file_states = ('', 'enabled', 'enabled-runtime', 'disabled', 'masked',
                    'masked-runtime', 'static', 'indirect', 'generated',
                    'transient', 'bad')

    @arg(
        'service', String,
        l_('Display name'),
        l_("""
            Name to display in the GUI.

            This setting also controls the name of the service
            created in Nagios (service_description).
        """)
    )
    @arg(
        'unit', String,
        l_('Unit name'),
        l_("""
            SystemD unit whose state will be checked.

            If omitted, the overall system health will be checked
            instead.
        """)
    )
    @arg(
        'valid_states', List(min=1, types=Enum(zip(_states, _states))),
        l_('Valid states'),
        l_("""
            Valid states for the unit. An alarm will be raised if the unit
            is in a state that is not part of this list.
            The severity of the alarm depends on the actual unit state:

              *  A WARNING alarm is raised for the 'active', 'reloading'
                 and 'activating' states.
              *  A CRITICAL alarm is raised for the 'inactive', 'failed'
                 and 'deactivating' states.
        """)
    )
    @arg(
        'unit_file_state', Enum(zip(_file_states, _file_states)),
        l_('Expected unit file state'),
        l_("""
            If given, a CRITICAL alarm will be raised if the unit file's state
            does not match the expected state. This can be used for example
            to check that masked/disabled unit files are in the proper state.
            This can also be used to prevent a CRITICAL alarm from being raised
            when the unit file's state is expected to be 'bad'.

            If omitted, a CRITICAL alarm is only raised if the unit file's state
            is 'bad' according to SystemD.
        """)
    )
    def add_test(self, service, unit="", unit_file_state='',
                 valid_states=('active', 'reloading', 'activating')):
        if unit:
            check = "check_systemd_unit"
        else:
            check = "check_systemd_health"

        args = "%s -s %s" % (unit, ','.join(valid_states))
        if unit_file_state:
            args += ' -f %s' % unit_file_state

        self.add_external_sup_service(service, "%s!%s" % (check, args))
        self.add_perfdata_handler(service, '%s-uptime' % service,
                                  'uptime', 'uptime')
        self.add_graph("%s uptime" % service, [ '%s-uptime' % service ],
                       'lines', 's')
