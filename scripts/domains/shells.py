"""Shells / ballistics domain: full ballistic and splash parameters.

Target data, mirroring ShipBuilder's ShellDataContainer and the ballistics
notes in wows-toolkit:
- air drag and krupp for every shell type (AP only had these before)
- arming threshold and fuse timer, shell cap and cap normalization angle
- underwater drag and penetration factors, explosion and splash radius
- dispersion distance params used for trajectory/penetration simulations

Raw source: projectile module fields such as ``bulletSpeed``, ``bulletMass``,
``bulletDiametr``, ``bulletAirDrag``, ``bulletKrupp``, ``bulletDetonator``,
``bulletRicochetAt``, ``bulletAlwaysRicochetAt``, ``alphaDamage``,
``alphaPiercingHE``, ``alphaPiercingCS``, ``burnProb``, ``explosionRadius``.
"""


_FIELD_MAP = {
    'bulletAirDrag': 'airDrag',
    'bulletKrupp': 'krupp',
    'bulletDetonator': 'fuseTime',
    'bulletDetonatorThreshold': 'armingThreshold',
    'bulletCap': 'shellCap',
    'bulletCapNormalizeMaxAngle': 'capNormalizeMaxAngle',
    'bulletWaterDrag': 'waterDrag',
    'bulletUnderwaterDistFactor': 'underwaterDistFactor',
    'bulletUnderwaterPenetrationFactor': 'underwaterPenetrationFactor',
    'explosionRadius': 'explosionRadius',
    'depthSplashRadius': 'splashRadius',
    'distParams': 'distParams',
    'distTile': 'distTile',
}


def unpack_shell(projectile: dict) -> dict:
    """Extract shell data from a raw projectile module."""
    shell = {}
    for raw, name in _FIELD_MAP.items():
        if raw in projectile:
            shell[name] = projectile[raw]
    return shell
