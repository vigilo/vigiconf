VigiConf
========

VigiConf is part of the Vigilo project <http://vigilo-project.org>.

VigiConf acts as a configuration generator, validator and dispatcher for
several software components, some of them being Vigilo modules (in parethesis),
that all share a common data referential:

  * Nagios
  * Collector (a highly optimized SNMP Nagios plugin)
  * Connector-Metro (an XMPP-to-RRD metrology store)
  * VigiRRD (a web-based RRD graph generator)
  * VigiMap (a map-sytle interface for Vigilo)
  * Nagios-HLS (a nagios instance dedicated to High Level Services)
  * CorrTrap (an SNMP Trap receiver and translator)
  * PerfData (a PerfData-to-XMPP router)

All data definition comes from a single model, described as a tree of
XML files contained in a directory. Data definition decribes the
assets to supervise:

  * hosts
  * host groups
  * supervision servers in charge of hosts groups
  * services associated with hosts
  * the way the services are collected (passively, directly…)
  * SNMP jobs that are to be scheduled for a give host
  * data sources related to data collected from SNMP Jobs or Nagios' perfdata
  * graphes that contain several data sources on a single image
  * and more…

VigiConf uses SVN as a configuration versionning system and rely on SSH
and sudo to copy configuration files, and launch commands (to validate a
configuration file validity, stop/start/restart deamons). The actions on the
(possibly remote) Vigilo server are handled by the VigiConf-local component.

After installing this package, you need to extract the configuration and
templates directories from the subversion repository. See
/etc/vigilo/vigiconf/conf.d/README.source for the subversion repository
address.

All actions are done using the "vigiconf" command, under the the "vigiconf"
system user.

