# confid:%(confid)s

use strict;
use warnings;
package host;
our %%Host = (
	sup => {services => { },},
	IPAddress     => "%(mainIP)s",
	hostname      => "%(name)s",
	snmp          => { port => %(port)d, snmpOIDsPerPDU => %(snmpOIDsPerPDU)d, version => %(snmpVersion)s, %(snmpAuth)s},
	storeMe       => { IPAddress => "%(storemeServer)s", port => 50001, },
	spoolMe       => { IPAddress => "%(spoolmeServer)s", port => 50000, },
	metro         => { DS => [ ] }
);

