define service{
    use                     generic-passive-service
    host_name               %(name)s
    service_description     %(desc)s
    check_command           report_stale
    check_freshness         1
    ; Les connecteurs envoient un message toutes les minutes
    freshness_threshold     330
    %(generic_sdirectives)s
}
