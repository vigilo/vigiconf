HOSTS["%(host)s"]["%(dsName)s"] = {
    "step": 300,
    "DS": {
        "name": "DS",
        "type": "%(dsType)s",
        "heartbeat": 600,
        "min": "U",
        "max": "U" },
    "RRA": [
        { "type": "AVERAGE", "xff": 0.5, "step": 1, "rows": 600 },
        { "type": "AVERAGE", "xff": 0.5, "step": 6, "rows": 700 },
        { "type": "AVERAGE", "xff": 0.5, "step": 24, "rows": 775 },
        { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 732}
    ]
}
