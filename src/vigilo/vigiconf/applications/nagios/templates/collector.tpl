define service{
    use                     generic-passive-service
    host_name               %(name)s
    service_description     %(serviceName)s
    %(quietOrNot)s
    %(notification_period)s
    %(generic_sdirectives)s
}

