define host{
	use                     %(hostTPL)s
	host_name               %(name)s
	alias                   %(name)s
	address                 %(mainIP)s
	check_command           %(checkHostCMD)s
    %(hostGroups)s
    %(quietOrNot)s
    %(parents)s
    %(notification_period)s
}

