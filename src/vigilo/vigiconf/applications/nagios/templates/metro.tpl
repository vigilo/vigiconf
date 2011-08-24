define service{
    use                     generic-passive-service
    host_name               %(name)s
    service_description     %(desc)s
    check_command           report_stale_data
    check_freshness         1
    ; On laisse 30s de marge pour que la collecte arrive. Ca a l'air peu mais
    ; il y a les soft states pour eviter le flapping (3 par defaut).
    freshness_threshold     330
    max_check_attempts      3 ; evite le flapping
    %(generic_sdirectives)s
}

