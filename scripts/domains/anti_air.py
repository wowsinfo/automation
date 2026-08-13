"""Anti-air domain: full aura and flak cloud parameters.

Target data, mirroring ShipBuilder's AntiAirDataContainer:
- long/medium/short range auras with range, constant damage, DPS,
  hit chance, explosion count and shot travel time
- flak cloud counts (inner/outer), damage, radius, duration and spawn time

Raw source: air defense module auras (``areaDamage``, ``areaDamagePeriod``,
``hitChance``, ``innerBubbleCount``, ``outerBubbleCount``,
``bubbleDamage``) plus global constants.
"""


def _unpack_aura(aura: dict) -> dict:
    """Unpack a single air defense aura into wiki-friendly values."""
    info = {}
    min_distance = aura.get('minDistance')
    max_distance = aura.get('maxDistance')
    if min_distance is not None:
        info['minRange'] = round(min_distance / 1000, 3)
    if max_distance is not None:
        info['maxRange'] = round(max_distance / 1000, 3)
    for key in ['hitChance', 'areaDamage', 'areaDamagePeriod',
                'explosionCount', 'shotDelay', 'shotTravelTime',
                'bubbleDamage', 'innerBubbleCount', 'outerBubbleCount',
                'bubbleRadius', 'bubbleDuration', 'enableBarrage']:
        if key in aura:
            info[key] = aura[key]
    period = aura.get('areaDamagePeriod')
    if aura.get('areaDamage') is not None and period:
        info['dps'] = round(aura['areaDamage'] / period, 1)
    return info


def unpack_anti_air(module: dict) -> dict:
    """Extract anti-air data from a raw air defense module."""
    auras = {'near': [], 'medium': [], 'far': []}
    flak = None

    for aura in module.values():
        if not isinstance(aura, dict):
            continue
        aura_type = aura.get('type')
        if aura_type not in auras:
            continue

        info = _unpack_aura(aura)
        # flak bubble aura: not a normal AA gun, keep it separate
        if aura.get('areaDamage') == 0:
            flak = {
                'inner': int(aura.get('innerBubbleCount', 0)),
                'outer': int(aura.get('outerBubbleCount', 0)),
                'hitChance': aura.get('hitChance'),
                'spawnTime': aura.get('shotTravelTime'),
                'radius': aura.get('bubbleRadius'),
                'duration': aura.get('bubbleDuration'),
                # value 7 matches the existing bubble damage formula
                'damage': aura.get('bubbleDamage', 0) * 7,
            }
            continue

        auras[aura_type].append(info)

    anti_air = {'auras': auras}
    if flak is not None:
        anti_air['flak'] = flak
    return anti_air
