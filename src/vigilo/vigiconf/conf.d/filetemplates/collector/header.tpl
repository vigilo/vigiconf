# confid:%(confid)s

use strict;
use warnings;
package host;
our %%Host = (
	sup => {services => { },},
	IPAddress     => "%(mainIP)s",
	hostname      => "%(name)s",
	snmp          => { port => %(port)s, snmpOIDsPerPDU => %(snmpOIDsPerPDU)s, version => %(snmpVersion)s, %(snmpAuth)s},
	metro         => { DS => [ ] }
);

