DEFAULTS = {
    "step": 300,
    "heartbeat": 600,
    "rra":  [
            { "type": "AVERAGE", "xff": 0.5, "step": 1, "rows": 600 },
            { "type": "AVERAGE", "xff": 0.5, "step": 6, "rows": 700 },
            { "type": "AVERAGE", "xff": 0.5, "step": 24, "rows": 775 },
            { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 732},
        ],
    "rra_netflow": [
            { "type": "AVERAGE", "xff": 0.5, "step": 1, "rows": 4320 },
            { "type": "AVERAGE", "xff": 0.5, "step": 12, "rows": 744 },
            { "type": "AVERAGE", "xff": 0.5, "step": 288, "rows": 366},
        ],
}
