define service{
    use                     generic-active-service
    host_name               %(name)s
    service_description     %(serviceName)s
    %(generic_sdirectives)s
}

