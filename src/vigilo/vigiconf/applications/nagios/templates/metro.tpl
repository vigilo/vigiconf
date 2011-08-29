define service{
    use                     generic-passive-service
    host_name               %(name)s
    service_description     %(desc)s
    %(generic_sdirectives)s
}

