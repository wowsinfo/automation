"""Aircraft domain: full squadron and attack parameters.

Target data, mirroring ShipBuilder's CvAircraftDataContainer:
- attack group size, attack count/cooldown/interval
- preparation and aiming times and speed limits
- engine boost (forsage) and JATO params, damage taken multipliers
- hangar settings (max number on deck, restoration time/amount)
- speed coefficients, climb/dive angles, weapon (bomb) reference,
  plane consumables

Raw source: aircraft module fields such as ``maxHealth``,
``numPlanesInSquadron``, ``attackerSize``, ``attackCount``,
``attackCooldown``, ``speedMin``, ``speedMax``, ``maxForsageAmount``,
``forsageRegeneration``, ``hangarSettings``.
"""


_FIELD_MAP = {
    'attackerSize': 'attackerSize',
    'attackCount': 'attackCount',
    'attackCooldown': 'attackCooldown',
    'attackInterval': 'attackInterval',
    'aimingTime': 'aimingTime',
    'aimingSpeedLimits': 'aimingSpeedLimits',
    'aimingAccuracyIncreaseRate': 'aimingAccuracyIncreaseRate',
    'aimingAccuracyDecreaseRate': 'aimingAccuracyDecreaseRate',
    'aimingTurnSpeedLimit': 'aimingTurnSpeedLimit',
    'preparationTime': 'preparationTime',
    'preparationSpeedLimits': 'preparationSpeedLimits',
    'preparationTurnSpeedLimit': 'preparationTurnSpeedLimit',
    'climbSpeedCoef': 'climbSpeedCoef',
    'diveSpeedCoef': 'diveSpeedCoef',
    'angleOfClimb': 'angleOfClimb',
    'angleOfDive': 'angleOfDive',
    'postAttackInvulnerabilityDuration': 'postAttackInvulnerabilityDuration',
    'jatoDuration': 'jatoDuration',
    'jatoSpeedMultiplier': 'jatoSpeedMultiplier',
    'maxForsageAmount': 'maxForsageAmount',
    'forsageRegeneration': 'forsageRegeneration',
    'speedMin': 'speedMin',
    'speedMax': 'speedMax',
    'visibilityFactorByPlane': 'visibilityFactorByPlane',
    'attackerDamageTakenMultiplier': 'attackerDamageTakenMultiplier',
    'damageTakenMultiplier': 'damageTakenMultiplier',
    'bombName': 'bombName',
    'bombFallingTime': 'bombFallingTime',
    'bombingDropPointTime': 'bombingDropPointTime',
    'emptyReturnSpeedMultiplier': 'emptyReturnSpeedMultiplier',
    'maxRotateSpeed': 'maxRotateSpeed',
    'planeSpeedupCoef': 'planeSpeedupCoef',
    'canStop': 'canStop',
}


def unpack_aircraft(aircraft: dict) -> dict:
    """Extract aircraft data from a raw aircraft module."""
    out = {}

    for raw, name in _FIELD_MAP.items():
        if raw in aircraft:
            out[name] = aircraft[raw]

    hangar = aircraft.get('hangarSettings')
    if isinstance(hangar, dict):
        for raw, name in [('maxValue', 'maxNumberOnDeck'),
                          ('timeToRestore', 'restorationTime'),
                          ('restoreAmount', 'restoreAmount'),
                          ('startValue', 'startOnDeck')]:
            if raw in hangar:
                out[name] = hangar[raw]

    abilities = aircraft.get('PlaneAbilities')
    if isinstance(abilities, dict):
        out['planeConsumables'] = abilities

    return out
