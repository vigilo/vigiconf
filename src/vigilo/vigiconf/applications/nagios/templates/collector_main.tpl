define service{
    use                     generic-active-service
    host_name               %(name)s
    service_description     Collector
    check_command           Collector
    max_check_attempts      2
    %(generic_sdirectives)s
}

