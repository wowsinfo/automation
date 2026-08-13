"""Main battery domain: dispersion, firing arcs and turret-level data.

Target data, mirroring ShipBuilder's MainBatteryDataContainer:
- caliber, barrel count, rate of fire, traverse, ammo switch time
- horizontal/vertical dispersion values and formulas (delimiter/taper,
  ellipse radius at zero/delimiter/max range, ranging coefficients)
- turret firing arcs (``horizSector``/``vertSector``) for firing-angle
  diagrams

Raw source: artillery module fields such as ``maxDist``, ``sigmaCount``,
``normalDistribution``, ``delim``, ``taperDist``, ``horizSector``,
``rotationSpeed``, ``ammoSwitchCoeff``, ``shotDelay``, ``numBarrels``,
``barrelDiameter``.
"""


def _find_guns(module: dict) -> list:
    """Return the gun entries of an artillery/secondary module."""
    guns = []
    for key, entry in module.items():
        if not isinstance(entry, dict):
            continue
        if 'HP' not in key:
            continue
        if 'barrelDiameter' not in entry:
            continue
        guns.append(entry)
    return guns


def unpack_main_battery(module: dict) -> dict:
    """Extract main battery data from a raw artillery module."""
    battery = {}
    guns = _find_guns(module)
    if len(guns) == 0:
        return battery

    first = guns[0]
    if 'barrelDiameter' in first:
        battery['caliber'] = first['barrelDiameter']
    battery['barrels'] = sum(int(g.get('numBarrels', 0)) for g in guns)

    reload = first.get('shotDelay')
    if reload:
        battery['rof'] = round(60.0 / reload, 2)
    if 'rotationSpeed' in first:
        battery['traverse'] = first['rotationSpeed']
    if 'ammoSwitchCoeff' in first:
        battery['ammoSwitchCoeff'] = first['ammoSwitchCoeff']

    dispersion = {}
    # module level dispersion settings
    for key in ['normalDistribution', 'taperDist']:
        if key in module:
            dispersion[key] = module[key]
    # per-gun dispersion values
    for key in ['delim', 'ellipseRangeMin', 'ellipseRangeMax',
                'radiusOnZero', 'radiusOnDelim', 'radiusOnMax',
                'idealDistance', 'idealRadius', 'minRadius',
                'maxEllipseRanging', 'medEllipseRanging',
                'minEllipseRanging', 'smokePenalty',
                'onMoveTarPosCoeffZero', 'onMoveTarPosCoeffDelim',
                'onMoveTarPosCoeffMaxDist', 'onMoveTarPosDelim']:
        if key in first:
            dispersion[key] = first[key]
    if len(dispersion) > 0:
        battery['dispersion'] = dispersion

    firing_arcs = {}
    for key, entry in module.items():
        if not isinstance(entry, dict) or 'HP' not in key:
            continue
        if 'horizSector' not in entry:
            continue
        turret = {'horizSector': entry['horizSector']}
        if 'vertSector' in entry:
            turret['vertSector'] = entry['vertSector']
        firing_arcs[key] = turret
    if len(firing_arcs) > 0:
        battery['firingArcs'] = firing_arcs

    return battery
