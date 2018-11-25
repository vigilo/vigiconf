# confid:%(confid)s

use strict;
use warnings;
package host;
our %%Host = (
	sup => {services => { },},
	IPAddress     => '%(address)s',
	hostname      => '%(name)s',
	timeout       => %(collectorTimeout)s,
	snmp          => { port => %(snmpPort)s, snmpOIDsPerPDU => %(snmpOIDsPerPDU)s, version => %(snmpVersion)s, transport => '%(snmpTransport)s', %(snmpAuth)s },
	metro         => { DS => [ ] }
);

