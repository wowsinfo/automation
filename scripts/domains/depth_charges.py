"""Depth charge domain: launcher and projectile parameters.

Target data, mirroring ShipBuilder's DepthChargesLauncherDataContainer and
DepthChargeDataContainer:
- launcher pack settings (shots in pack, max packs) and per-thrower data
  (bombs, shoot angle/distance, fall speed, sectors)
- projectile data: damage, sink speed, detonation depth, splash radius,
  fire chance, flood generation, points of damage, hit classes

Raw source: depth charge launcher module fields and depth charge projectile
module fields such as ``damage``, ``sinkSpeed``, ``detonationTimer``,
``detonationDepth``, ``splashRadius``, ``fireChance``, ``floodChance``.
"""


_PACK_FIELDS = [
    'numShots', 'shotsInPack', 'maxPacks', 'shotDelay',
    'gunsSequenceType', 'centerZoneWidthPart', 'useShotNodesForSequence',
]

_LAUNCHER_FIELDS = [
    'numBombs', 'shootAngle', 'shootDist', 'startFallSpeed', 'horizSector',
    'vertSector', 'fallRollAcceleration', 'rollSpeed', 'rotationSpeed',
]

_PROJECTILE_FIELDS = {
    'alphaDamage': 'damage',
    'bulletSpeed': 'sinkSpeed',
    'maxDepth': 'detonationDepth',
    'depthSplashRadius': 'splashRadius',
    'burnProb': 'fireChance',
    'floodGeneration': 'floodGeneration',
    'pointsOfDamage': 'pointsOfDamage',
    'ignoreClasses': 'ignoreClasses',
    'alertDist': 'alertDist',
    'explosivePower': 'explosivePower',
    'integralPower': 'integralPower',
    'fallDistance': 'fallDistance',
    'fallTime': 'fallTime',
    'buoyancyToDamageCoeff': 'buoyancyToDamageCoeff',
}


def unpack_depth_charge(projectile: dict) -> dict:
    """Extract depth charge projectile data from a raw projectile module."""
    out = {}
    for raw, name in _PROJECTILE_FIELDS.items():
        if raw in projectile:
            out[name] = projectile[raw]
    return out


def unpack_depth_charges(module: dict, params: dict) -> dict:
    """Extract depth charge data from a raw launcher module."""
    out = {}

    packs = {}
    for key in _PACK_FIELDS:
        if key in module:
            packs[key] = module[key]
    if len(packs) > 0:
        out['packs'] = packs

    launchers = []
    ammo_names = []
    for key, entry in module.items():
        if not isinstance(entry, dict):
            continue
        if 'HP' not in key or 'numBombs' not in entry:
            continue
        launcher = {'name': key}
        for field in _LAUNCHER_FIELDS:
            if field in entry:
                launcher[field] = entry[field]
        launchers.append(launcher)
        ammo_list = entry.get('ammoList')
        if isinstance(ammo_list, list):
            ammo_names.extend(ammo_list)
    if len(launchers) > 0:
        out['launchers'] = launchers

    for ammo_name in ammo_names:
        if isinstance(params, dict) and ammo_name in params:
            out['ammo'] = unpack_depth_charge(params[ammo_name])
            break

    return out
