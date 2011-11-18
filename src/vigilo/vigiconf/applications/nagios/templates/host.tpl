define host{
    use                     %(hostTPL)s
    host_name               %(name)s
    alias                   %(name)s
    address                 %(address)s
    check_command           %(checkHostCMD)s
    %(hostGroups)s
    %(quietOrNot)s
    %(parents)s
    %(notification_period)s
    %(generic_hdirectives)s
}

