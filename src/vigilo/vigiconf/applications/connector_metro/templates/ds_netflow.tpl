HOSTS["%(host)s"]["%(dsName)s"] = {
    "step": 300,
    "DS": {
        "name": "DS",
        "type": "%(dsType)s",
        "heartbeat": 600,
        "min": "U",
        "max": "U" },
    "RRA": [
        { "type": "AVERAGE", "xff": 0.5, "step": 1, "rows": 4320 },
        { "type": "AVERAGE", "xff": 0.5, "step": 12, "rows": 744 },
        { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 366}
    ]
}
