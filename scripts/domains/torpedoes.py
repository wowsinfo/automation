"""Torpedo domain: arming, homing and splash parameters.

Target data, mirroring ShipBuilder's TorpedoDataContainer:
- arming distance (arming time * speed) and reaction time
- depth, splash armor coeff and cube size, underwater splash damage
- raw homing parameters (acoustic detection, damage coefficient per ping,
  time to change angle/speed, torpedo angles, maneuver distance)
- can-hit classes derived from ignore classes

Raw source: torpedo projectile module fields such as ``speed``,
``visibilityFactor``, ``maxDist``, ``uwCritical``, ``alphaDamage``,
``isDeepWater``, ``armingTime``, ``acousticDetection``, ``torpedoAngles``.
"""


SHIP_CLASSES = ['AirCarrier', 'Battleship', 'Cruiser', 'Destroyer',
                'Submarine', 'Auxiliary']


_FIELD_MAP = {
    'armingTime': 'armingTime',
    'depth': 'depth',
    'bulletDiametr': 'diameter',
    'splashArmorCoeff': 'splashArmorCoeff',
    'splashCubeSize': 'splashCubeSize',
    'underwaterSplashBPDamageMultiplier': 'underwaterSplashDamageMultiplier',
    'damageCoeffMaxPing': 'damageCoeffMaxPing',
    'acousticDetection': 'acousticDetection',
    'timeToChangeAngle': 'timeToChangeAngle',
    'timeToChangeSpeed': 'timeToChangeSpeed',
    'torpedoAngles': 'torpedoAngles',
    'maneuverDist': 'maneuverDist',
    'alertDist': 'alertDist',
}


def unpack_torpedo(torpedo: dict) -> dict:
    """Extract torpedo data from a raw torpedo projectile module."""
    out = {}

    speed = torpedo.get('speed')
    arming_time = torpedo.get('armingTime')
    if speed is not None and arming_time is not None:
        out['armingDistance'] = round(speed * arming_time, 1)
        out['reactionTime'] = arming_time

    for raw, name in _FIELD_MAP.items():
        if raw in torpedo:
            out[name] = torpedo[raw]

    if 'SubmarineTorpedoParams' in torpedo:
        # per-ping homing data (turning/vertical speeds, search radius/angle,
        # per-class drop distances) shown by ShipBuilder
        out['submarineParams'] = torpedo['SubmarineTorpedoParams']
    if 'bulletSplashCubesDamage' in torpedo:
        out['splashDamage'] = torpedo['bulletSplashCubesDamage']
    if 'isInvisible' in torpedo:
        out['isInvisible'] = torpedo['isInvisible']

    ignore_classes = torpedo.get('ignoreClasses')
    if isinstance(ignore_classes, list):
        out['canHitClasses'] = [c for c in SHIP_CLASSES
                                if c not in ignore_classes]

    return out
