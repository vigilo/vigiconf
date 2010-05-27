define service{
	use                     generic-active-service
	host_name               %(name)s
	service_description     %(desc)s
	check_command           %(command)s
	max_check_attempts      %(maxchecks)s
    %(quietOrNot)s
    %(perfDataOrNot)s
    %(notification_period)s
    %(generic_sdirectives)s
}

