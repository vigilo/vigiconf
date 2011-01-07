host_conf["plugins"].append({
    "name": %(plugin)r,      # Plugin name
    "srv_name": %(srv_name)r, # Nagios service name of this plugin
    "crystals": %(crystals)r,
    "labels": %(labels)r,
    "crit": %(crit)r,
})
