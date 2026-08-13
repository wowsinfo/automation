"""Airstrike domain: ASW / aircraft strike parameters.

Target data, mirroring ShipBuilder's AirstrikeDataContainer:
- auto usage, charges, minimum/maximum distance, maximum flight distance
- fly-away time, drop time, time between shots, time from heaven
- the aircraft used by the strike (HP, squadron size, speeds, weapon)

Raw source: air support module fields such as ``planeName``,
``reloadTime``, ``maxDist``, ``chargesNum`` plus aircraft module fields.
"""


_MODULE_FIELDS = [
    'autoUsage', 'chargesNum', 'climbAngle', 'flyAwayTime', 'maxDist',
    'maxPlaneFlightDist', 'minDist', 'reloadTime', 'timeBetweenShots',
    'timeFromHeaven',
]

_PLANE_FIELDS = [
    'maxHealth', 'numPlanesInSquadron', 'visibilityFactor',
    'visibilityFactorByPlane', 'speedMoveWithBomb', 'speedMin', 'speedMax',
    'attackerSize', 'attackCount', 'attackCooldown', 'attackInterval',
    'aimingTime', 'bombName', 'maxForsageAmount', 'forsageRegeneration',
    'jatoDuration', 'jatoSpeedMultiplier',
]


def unpack_airstrike(module: dict, params: dict) -> dict:
    """Extract airstrike data from a raw air support module."""
    airstrike = {}

    for key in _MODULE_FIELDS:
        if key in module:
            airstrike[key] = module[key]

    plane_name = module.get('planeName')
    if plane_name and isinstance(params, dict) and plane_name in params:
        plane = params[plane_name]
        details = {}
        for key in _PLANE_FIELDS:
            if key in plane:
                details[key] = plane[key]
        airstrike['plane'] = details

    return airstrike
