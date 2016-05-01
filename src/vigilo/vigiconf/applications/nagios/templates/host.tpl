define host{
    host_name               %(name)s
    alias                   %(name)s
    address                 %(address)s
    %(hostGroups)s
    %(parents)s
    %(generic_hdirectives)s
}

